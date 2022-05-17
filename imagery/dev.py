import fiona

def bounds():
    root_dir = "/home/mluzu/proyecto_ceia"
    shapefile_dir = "/shapefile"
    shapefilePath = root_dir + shapefile_dir


    gral_lopez_collection = fiona.open(shapefilePath)
    record = next(iter(gral_lopez_collection))

    query_dict = {
        "platformname": None,
        "beginposition": None,
        "endposition": None,
        "ingestiondate": None,
        "collection": None,
        "filename": None,
        "footprint": None,
        "orbitnumber": None,
        "lastorbitnumber": None,
        "relativeorbitnumber": None,
        "lastrelativeorbitnumber": None,
        "orbitdirection": None,
        "polarisationmode": None,
        "producttype": None,
        "sensoroperationalmode": None,
        "swathidentifier": None,
        "cloudcoverpercentage": None,
        "timeliness": None,
        "processinglevel": None
    }

    return gral_lopez_collection.bounds

"""
  for product_node in root.iter(f'{ns}entry'):
        for link in product_node.iter(f'{ns}link'):
            if isinstance(link.attrib, dict):
                if link.attrib.get('rel') == 'alternative':
                    print(link.get('href'))
                    

    profile = {
        'driver': 'JP2OpenJPEG',
        'dtype': 'uint16',
        'nodata': None,
        'width': 10980,
        'height': 10980,
        'count': 1,
        'crs': rasterio.crs.CRS.from_epsg(32617),
        'transform': rasterio.transform.Affine(10.0, 0.0, 399960.0, 0.0, -10.0, 5600040.0)
    }

    with session.get(url, auth=(user, password), stream=True) as responseImage:
        with rasterio.MemoryFile(responseImage.content) as memfile:
            with memfile.open(**profile) as dataset:
                data_array = dataset.read()

    plot.show(data_array)
"""