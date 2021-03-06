## Magrit - Thematic cartography

![png](magrit_app/static/img/logo_magrit2.png)  
[![Build Status](https://travis-ci.org/mthh/magrit.svg?branch=master)](https://travis-ci.org/mthh/magrit)

"Magrit" is an online mapping application developped by UMS RIATE (http://www.ums-riate.fr).  
This tool allows to produce **high quality thematic maps**.   
All usual cartographic representations as well as many cartographic methods often difficult to implement (*smoothing*, *grids*, *discontinuities*, *cartograms*) are available.      Magrit intends to cover the entire processing chain in a single environment, from geographical data to graphic editing.

#### Result examples :

<p><img src="https://magrit.hypotheses.org/files/2017/02/worldpop.png" height="250"/><img src="https://magrit.hypotheses.org/files/2017/02/smoothed2.png" height="250"/></p>


More examples are available in the [gallery](http://magrit.hypotheses.org/galerie).

#### Usage

Most users should go on :
- the [application page](http://magrit.cnrs.fr)
- the [user documentation](http://magrit.cnrs.fr/docs/)


#### Instruction for developpers
>> NOTE : The only targeted/tested OS is currently GNU/Linux.
However it is very likely that it can work with little change on other UNIX-like (xBSD, MacOS?).
In addition, an explanation is provided below for an installation via Docker, which can make a deployement possible for other OS users (notably [Windows](https://docs.docker.com/docker-for-windows/), [FreeBSD](https://wiki.freebsd.org/Docker) or [MacOSX](https://docs.docker.com/docker-for-mac/))

Installation of the required libraries :
(Ubuntu 16.04)
```
# apt-get install -y gcc libpython3.5-dev libopenblas-dev libopenblas-base python3.5 python3.5-dev nodejs python3-pip \
  gdal-bin libgdal-dev libfreetype6-dev libfreetype6 libproj-dev libspatialindex-dev libv8-3.14-dev libffi-dev \
        nodejs nodejs-dev node-gyp npm redis-server libuv1-dev git wget libxslt1-dev libxml2 libxml2-dev
```

Using a python virtual environnement:

```bash
$ git clone https://github.com/riatelab/magrit
$ cd magrit
$ virtualenv venv -p /usr/bin/python3.5
$ source venv/bin/activate
(venv)$ pip install -r requirements-dev.txt
(venv)$ python setup.py install
```
#### Running the test suite :
##### Basic tests without web browser (same than those runned on Travis) :
```
(venv)$ py.test tests/test.py
```

##### Tests using selenium webdriver API (require [chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) available) :
(its actually 3 steps in one : launching the application, waiting for its start to be complete, then actually launching the test suite)
```
(venv)$ magrit & sleep 3 && py.test tests/tests_web.py
```

#### Launching the application:
```bash
(venv)$ magrit -p 9999
INFO:magrit.main:serving on('0.0.0.0', 9999)
....
```

#### Deployement with docker :
##### Using the latest version of the application (+ nginx for static files)

The application to deploy may consist of two Docker containers:
- one used to serve the `aiohttp` application with `Gunicorn` and to host the Redis service used;
- the second is composed only of nginx, used in front-end of Gunicorn (i.g to buffer long requests, etc.) and to serve the static content.
For now you have to build them, but we can releases them on *Docker Hub* if any interest.
This scenario is shown below, exposing publicly `Magrit` on the port 80 :

```` bash
cd /tmp/
mkdir magritapp
# Clone the developpement version :
git clone http://github.com/riatelab/magrit
# Copy the two Dockerfile :
cp -r magrit/misc/Docker/ magritapp/
# Copy the static files :
cp -r magrit/magrit_app/static/ magritapp/Docker/nginx/
# Make some clean up :
rm -rf magrit
# Setting up the magrit image:
cd magritapp/Docker
cd app/
docker build -t "magrit_app:latest" --build-arg CACHEBUST=$(date +%s) .
# Setting up the nginx image:
cd ..
cd nginx/
docker build -t "nginx:latest" .
cd ..
# Starting the application (will be accessible on port 80) :
docker run -dP --name magritapp "magrit_app:latest"
docker run --publish "80:80" -dP --name nginx --link magritapp:magritapp nginx
````

It is also possible to build only the 'Magrit' image, containing the `aiohttp` application; static files are then directly served by `aiohttp`.  

Using the flexibility offered by Docker, one may be able to compose it's deployement in a different way to better balance the load of users (i.g. 1 container for Redis, 1 container for Nginx and 2 or 3 others containers, each one running an instance of the `aiohttp` application via `Gunicorn`).

#### Contributing to Magrit :
Contributions are welcome! There are various way to contribute to the project:
- Feedback and bug reports
- Translation (only French and English languages are currently available)
- Code contribution (you're one the right place! Clone the repo, fix what you want to be fixed and submit a pull request)
- Contribute to the [gallery](http://magrit.hypotheses.org/galerie)
