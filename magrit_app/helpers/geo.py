#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
import numpy as np
from functools import partial
from osgeo.ogr import GetDriverByName, Feature as OgrFeature
from osgeo.osr import SpatialReference, CoordinateTransformation
from pyproj import transform as pyproj_transform, Proj as pyproj_Proj
from shapely.geometry import shape, mapping, MultiPolygon
from shapely.ops import transform
from shapely.affinity import scale
from pandas import read_json as pd_read_json
from geopandas import GeoDataFrame
from subprocess import Popen, PIPE

def _compute_centroids(geometries):
	res = []
	for geom in geometries:
		if hasattr(geom, '__len__'):
			ix_biggest = np.argmax([g.area for g in geom])
			res.append(geom[ix_biggest].centroid)
		else:
			res.append(geom.centroid)
	return res


def make_geojson_links(ref_layer_geojson, csv_table, field_i, field_j, field_fij, join_field):
    gdf = GeoDataFrame.from_features(ref_layer_geojson["features"])
    gdf.set_index(join_field, inplace=True, drop=False)
    gdf.geometry = _compute_centroids(gdf.geometry)
    csv_table = pd_read_json(csv_table)
    csv_table = csv_table[csv_table["i"].isin(gdf.index) & csv_table["j"].isin(gdf.index)]
    geoms_loc = gdf.geometry.loc
    ft_template_start = \
        '''{"type":"Feature","geometry":{"type":"LineString","coordinates":['''
    geojson_features = []
    for n, id_i, id_j, fij in csv_table[[field_i, field_j, field_fij]].itertuples():
#        pt1, pt2 = \
#            list(geoms_loc[id_i].coords)[0], list(geoms_loc[id_j].coords)[0]
        pts = \
            list(geoms_loc[id_i].coords)[0] + list(geoms_loc[id_j].coords)[0]
        geojson_features.append(''.join([
                ft_template_start,
                '''[{0},{1}],[{2},{3}]'''.format(*pts),
                ''']},"properties":{"''',
                '''i":"{0}","j":"{1}","fij":"{2}"'''.format(id_i, id_j, fij),
                '''}}'''
                ])
            )

    return ''.join([
        '''{"type":"FeatureCollection","crs":{"type":"name","properties":'''
        '''{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[''',
        ','.join(geojson_features),
        ''']}'''
        ]).encode()


def olson_transform(geojson, scale_values):
	"""
	Inplace scaling transformation of each polygon of the geojson provided
	according to the "scale values" also provided.

	Args:
	    geojson, dict:
	        The geojson of polygon to transform
	        (it might be useful to have choosen an appropriate projection as we
	        want to deal with the area)
	    scale_values:
	        The pre-computed scale values for olson transformation
	        (1 = no transformation)
	Return:
	    Nothing
	"""
	if len(geojson["features"]) != len(scale_values):
		raise ValueError("Inconsistent number of features/values")
	for ix, feature in enumerate(geojson["features"]):
		geom = shape(feature["geometry"])
		feature['properties']['ref_area'] = geom.area
		val = scale_values[ix]
		try:
			# mpoly = [scale(g, xfact=val, yfact=val) for g in geom]
			feature["geometry"] = mapping(
				MultiPolygon([scale(g, xfact=val, yfact=val) for g in geom]))
		except Exception as err:
			feature["geometry"] = mapping(
				scale(geom, xfact=val, yfact=val))
	geojson['features'].sort(key=lambda x: x['properties']['ref_area'], reverse=True)


def reproj_convert_layer_kml(geojson_path):
	process = Popen(["ogr2ogr", "-f", "KML",
					 "-preserve_fid",
					 "-t_srs", "EPSG:4326",
					 "/dev/stdout", geojson_path], stdout=PIPE)
	stdout, _ = process.communicate()
	return stdout


def reproj_convert_layer(geojson_path, output_path,
                         file_format, output_crs, input_crs="epsg:4326"):
    layer_name = output_path.split('/')
    layer_name = layer_name[len(layer_name) - 1].split('.')[0]

    in_driver = GetDriverByName("GeoJSON")
    out_driver = GetDriverByName(file_format)

    inSpRef = SpatialReference()
    inSpRef.ImportFromEPSG(int(input_crs.split("epsg:")[1]))

    outSpRef = SpatialReference()
    ret_val = outSpRef.ImportFromProj4(output_crs)
    if not ret_val == 0:
        raise ValueError("Error when importing the output crs")

    coords_transform = CoordinateTransformation(inSpRef, outSpRef)

    f_in = in_driver.Open(geojson_path)
    input_layer = f_in.GetLayer()
    f_out = out_driver.CreateDataSource(output_path)
    output_layer = f_out.CreateLayer(layer_name, outSpRef)

    input_lyr_defn = input_layer.GetLayerDefn()
    for i in range(input_lyr_defn.GetFieldCount()):
        fieldDefn = input_lyr_defn.GetFieldDefn(i)
        output_layer.CreateField(fieldDefn)

    output_lyr_defn = output_layer.GetLayerDefn()

    for inFeature in input_layer:
        geom = inFeature.GetGeometryRef()
        geom.Transform(coords_transform)
        outFeature = OgrFeature(output_lyr_defn)
        outFeature.SetGeometry(geom)
        for i in range(output_lyr_defn.GetFieldCount()):
            outFeature.SetField(output_lyr_defn.GetFieldDefn(i).GetNameRef(),
                                inFeature.GetField(i))
        output_layer.CreateFeature(outFeature)
        outFeature.Destroy()
        inFeature.Destroy()
    f_in.Destroy()
    f_out.Destroy()

    if "Shapefile" in file_format:
        outSpRef.MorphToESRI()
        with open(output_path.replace(".shp", ".prj"), 'w') as file_proj:
            file_proj.write(outSpRef.ExportToWkt())
        with open(output_path.replace(".shp", ".cpg"), "w") as encoding_file:
            encoding_file.write("UTF-8")
    return 0


def reproj_layer(geojson, output_crs, input_crs="epsg:4326"):
    reproj = partial(pyproj_transform,
                     pyproj_Proj(init=input_crs),
                     pyproj_Proj(output_crs))
    for feature in geojson["features"]:
        feature["geometry"] = mapping(transform(
            reproj, shape(feature["geometry"])))


def check_projection(proj4string):
    if not isinstance(proj4string, str):
        return False
    if proj4string[0] == '"' and proj4string[len(proj4string) - 1] == '"':
        proj4string = proj4string[1:len(proj4string) - 1]
    if "epsg:" in proj4string[:5]:
        proj4string = "".join(["+init=", proj4string])
    try:
        pyproj_Proj(proj4string)
        outSpRef = SpatialReference()
        ret_val = outSpRef.ImportFromProj4(proj4string)
        if not ret_val == 0:
            return False
        return proj4string
    except:
        return False

def on_geom(geom):
    for pts in geom:
        for pt in pts:
            if pt[0] > 179.9999:
                pt[0] = 179.9999
            elif pt[0] < -179.9999:
                pt[0] =  -179.9999
            if pt[1] > 89.9999:
                pt[1] = 89.9999
            elif pt[1] < -89.9999:
                pt[1] = -89.9999

def repairCoordsPole(geojson):
    for ft in geojson['features']:
        geom = ft["geometry"]
        if "MultiPolygon" in geom["type"]:
            for poly in geom['coordinates']:
                # exterior = poly[:1]
                on_geom(poly[:1])
                if(len(poly) > 2):
                    # interiors  = poly[1:]
                    on_geom(poly[1:])
        elif "Polygon" in geom["type"]:
            # poly = geom['coordinates']
            # exterior = poly[:1]
            on_geom(geom['coordinates'][:1])
            if(len(geom['coordinates']) > 2):
                # interiors  = poly[1:]
                on_geom(geom['coordinates'][1:])
