### MAPOLOGIC

What does it do for you ?

*MAPOLOGIC* lets you :
 - import your geometries (and an other dataset of values to be joined if necessary)
 - prepare your data (make a jointure, use basic operands to create a new field, show your values distribution and discretize them with some relevant methods or with your custom break values)
 - make a nice map (according to a selected method (see below), using nice on-the-fly-computed colorramps)
 - fully custom it (legend, title, other text block(s), colors, fonts, export size, etc..)
 - export the map you painfully have done! (and the layer(s) which may have been produced in GeoJSON or TopoJSON formats)

Currently allowed geometry input :

 - **shapefile** (.shp .dbf and .prj are requested, provided in a .zip archive or together as multiple files)
 - **geojson** (with "crs" information, otherwise crs is assumed to be EPSG:4326 / OGC:1.3:CRS84)
 - **kml** (specs. only seems to allow spherical coordinates to be stored in this file format)
 - **topojson** (converted from sherical coordinates only)
 - **csv file** (with "x"/"y" or "latitude"/"longitude" fields for points)
 - To be done (?): read GML format, mapinfo TAB/MID and csv file with a "geometry" / "geom" / "wkb" field containing the geom encoded in WKB)

Currently allowed external dataset :
 - **csv file**
(- To be done : read xls, xlsx and ods formats)

Currently available mapping methods :
 - choropleth map
 - proportional symbol map
 - links map
 - choroplethized proportional symbol
 - gridded map
 - compute a gravitational interaction model (Stewart potential) to produce a smoothed map
 - cartograms
 - compute and render the result of statistical comparison between territorial units (based on HyperCarte* methods)
 - In progress : render cartograms according to other algorythms, render "label map" with optimal label positioning

#### Instalation
Following dependencies are needed :

Ubuntu:
```
sudo apt-get install libgdal-dev libproj-dev libv8-dev libffi-dev
libpython3.5-dev r-base redis-server nodejs npm libfftw3-dev libzmq-dev
```