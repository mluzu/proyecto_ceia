## Configuración del entorno
-pyenv install 3.8.8
-pyenv global 3.8.8
-pip install pipenv
-pipenv --python 3.8.8 install
-pipenv --rm (ejecutar antes en caso de que al a primera arroje el error ERROR:: --system is intended to be used for pre-existing Pipfile installation, not installation of specific packages. Aborting.)
-pipenv shell (activa entorno)

## Instalación de GDAL y rasterio
La versión actual de rasterio (1.2) es compatible con Python 3.6 a 3.9, numpy >= 1.15 y con GDAL 2.3 a 3.2.

-sudo apt-get install libgdal-dev
-export CPLUS_INCLUDE_PATH=/usr/include/gdal
-export C_INCLUDE_PATH=/usr/include/gdal
-pipenv install gdal~=3.2
-pipenv install rasterio~=1.2
-pipenv install fiona
-pipenv install numpy