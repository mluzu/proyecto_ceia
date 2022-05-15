import xml.etree.ElementTree as xml
import re
from .apis import SentinelApi
from .data import Data
from rasterio.io import MemoryFile
from rasterio.crs import CRS
from rasterio.transform import Affine

def _get_xml_namespace(element):
    m = re.match(r'\{.*\}', element.tag)
    return m.group(0) if m else None


class SentinelData(Data):

    def __init__(self, platformname, producttype, processinglevel):
        self.sentinelApi = SentinelApi('mluzu', 'aufklarung', platformname, producttype, processinglevel)
        self.product_list = list()
        self._ns = None
        self.pre_filters = {
            "platformname": platformname,
            "producttype": producttype,
            "processinglevel": processinglevel
        }
        self.post_filters = dict()

    def set_bonds_filter(self, rect):
        """
        Prefilter that can be applied by query. The region of interest is calculated from a rectangle diagonal
        :param rect: Only sequence type is with four elements supported
        """
        if len(rect) != 4:
            raise ValueError("Only supports AOI of polygons")

        roi = '({} {}, {} {}, {} {}, {} {}, {} {})'.format(rect[0], rect[1], rect[2], rect[1], rect[2],
                                                           rect[3], rect[0], rect[3], rect[0], rect[1])
        footprint = '"Intersects(POLYGON({}))"'.format(roi)
        self.pre_filters.update({'footprint': footprint})

    def set_date_filter(self, begintime, endtime):
        """
        Prefilter that can be applied by query.
        Supported formats are:
        - yyyyMMdd
        - yyyy-MM-ddThh:mm:ss.SSSZ (ISO-8601)
        - yyyy-MM-ddThh:mm:ssZ
        - NOW
        - NOW-<n>DAY(S) (or HOUR(S), MONTH(S), etc.)
        - NOW+<n>DAY(S)
        - yyyy-MM-ddThh:mm:ssZ-<n>DAY(S)
        - NOW/DAY (or HOUR, MONTH etc.) - rounds the value to the given unit
        :param begintime:
        :param endtime:
        """
        if begintime is None and endtime is None:
            raise ValueError("Provide a begin date and end date")

        interval = f'[{begintime} TO {endtime}]'

        self.pre_filters.update({'beginposition': interval})
        self.pre_filters.update({'endposition': interval})

    def set_cloudcoverage_filter(self, minpercentage, maxpercentage):
        """
        Prefilter that can be applied by query.
        :param min:
        :param max:
        """
        min_max = f'[{minpercentage} TO {maxpercentage}]'

        self.pre_filters.update({'cloudcoverpercentage': min_max})

    def set_bands_filter(self, *bands):
        """
        Postfilter that can be applied by nodes properties
        :params: bands
        """
        if len(bands) == 0:
            raise ValueError("Choose at least one band")

        if not isinstance(bands, list):
            raise ValueError("Provide a list of bands")

        self.pre_filters.update({'bands': bands})

    def get(self, count):
        if len(self.product_list) == 0:
            self.fetch_products()
        return self.product_list[0:count]

    def fetch_products(self):
        pass

    def create_product_list(self):
        """
        First step in retrieving products from Sentinel is searching the products available with the specified filters
        """
        search_url = self.sentinelApi.build_search_query(self.pre_filters)
        search_result = self.sentinelApi.do_query(search_url)
        root = self.parse(search_result)
        product_list = []
        for product_node in self.get_list_in_node(root, "entry"):
            product_path = f"/Products('{self.get_node_value(product_node, 'id')}')/Nodes('{self.get_node_value(product_node, 'title')}.SAFE')"
            product_list.append({
                "product_path": product_path,
            })
        return product_list

    def get_node_value(self, element, key):
        if self._ns is not None:
            node = element.find(f'{self._ns}{key}')
        else:
            node = element.find(key)

        if node is not None:
            return node.text
        else:
            return None

    def get_node_element(self, element, key):
        if self._ns is not None:
            node = element.find(f'{self._ns}{key}')
        else:
            node = element.find(key)

        return node

    def get_list_in_node(self, element, key):
        if self._ns is not None:
            return element.iter(f'{self._ns}{key}')
        else:
            return element.find(key)

    def parse(self, xmlcontent):
        tree = xml.fromstring(xmlcontent)
        ns = _get_xml_namespace(tree)
        if ns is not None:
            self._ns = ns
        return tree


class Sentinel2MSIData(SentinelData):

    def __int__(self, platformname, producttype, processinglevel):
        super().__init__(self, platformname, producttype, processinglevel)

    def fetch_products(self):
        product_list = super().create_product_list()
        for product in product_list:
            product_node = product.get('product_path')
            granule = self._get_product_granule(product_node)
            query = '{}/{}'.format(product_node, "Nodes('GRANULE')/Nodes('{}')/Nodes('MTD_TL.xml')/$value".format(granule))
            url = self.sentinelApi.build_odata_url(query)
            response = self.sentinelApi.do_query(url)
            root = self.parse(response)
            metadata = self._read_metadata(root)
            image = self._get_image(image_node, metadata, self.post_filters)
            product.update({"metadata": metadata, "image": image})

    def _get_product_granule(self, product_node):
        node_path = '{}/{}'.format(product_node, "Nodes('GRANULE')/Nodes")
        url = self.sentinelApi.build_odata_url(node_path)
        response = self.sentinelApi.do_query(url)
        root = self.parse(response)
        granule_node = self.get_node_element(root, 'entry')
        return self.get_node_value(granule_node, 'title')

    def _read_metadata(self, element):
        geometric_info = self.get_node_element(element, 'Geometric_Info')
        tile_geocoding = geometric_info.find('Tile_Geocoding')
        cs_name = tile_geocoding.find('HORIZONTAL_CS_NAME')
        cs_code = tile_geocoding.find('HORIZONTAL_CS_CODE')
        size_node = tile_geocoding.find('Size')
        height = size_node.find('NROWS')
        width = size_node.find('NCOLS')

        metadata = {
            "crs": {"code": cs_code.text, "name": cs_name.text },
            "height": int(height.text),
            "width": int(width.text),
            "resolution": int(size_node.attrib.get('resolution'))
        }
        return metadata

    def _get_images(self, image_node, metadata):

        profile = {
            'driver': 'JP2OpenJPEG',
            'dtype': 'uint16',
            'nodata': None,
            'width': metadata.get('width'),
            'height': metadata.get('height'),
            'count': 1,
            'crs':CRS.from_epsg(32617),
            'transform': Affine(10.0, 0.0, 399960.0, 0.0, -10.0, 5600040.0)
        }
        image_node.find()
        image_bytes = self.sentinelApi.do_query(url, stream=True)
        with MemoryFile(image_bytes) as memfile:
            with memfile.open(**profile) as dataset:
                return dataset.read()




