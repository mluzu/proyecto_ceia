import xml.etree.ElementTree as xml
from .data import Data
from rasterio.io import MemoryFile
from rasterio.crs import CRS
from rasterio.transform import Affine
from requests import Session
from requests.exceptions import HTTPError
from src.imagery.exceptions import SentinelAPIError
import numpy as np
import re
import fnmatch


def namespace(element):
    m = re.match(r'\{.*\}', element.tag)
    return m.group(0) if m else ''


class SentinelData(Data):

    def __init__(self, platformname, producttype, processinglevel):
        self.session = Session()
        self.credentials = ('mluzu', 'aufklarung')
        self.odata_base_url = "https://apihub.copernicus.eu/apihub"
        self.odata_path = "/odata/v1"
        self.products = None
        self.pre_filters = {
            "platformname": platformname,
            "producttype": producttype,
            "processinglevel": processinglevel
        }
        self.post_filters = {
            'resolution': '10'
        }

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
        :param minpercentage:
        :param maxpercentage:
        """
        min_max = f'[{minpercentage} TO {maxpercentage}]'

        self.pre_filters.update({'cloudcoverpercentage': min_max})

    def set_bands_filter(self, *bands):
        """
        Postfilter that can be applied by nodes properties
        :params: bands
        """
        if len(bands) == 0:
            raise ValueError("Provide a list of bands")

        self.post_filters.update({'bands': bands})

    def read(self, count):
        if self.products is None:
            self.fetch_products()
        return self.products[0:count]

    def create_product_list(self):
        """
        First step in retrieving products from Sentinel is searching the products available with the specified filters
        """
        def select_by_vg(items):
            max_veg_perc = 0
            product = None
            for item in items:
                prop = item.find(".//*[@name='vegetationpercentage']")
                if prop is not None:
                    vp = float(prop.text)
                    if vp > max_veg_perc:
                        max_veg_perc = vp
                        product = item
            return product

        query = self.build_search_query()
        response = self.do_query(query)
        root = xml.fromstring(response)
        ns = namespace(root)

        product_list = root.iter(f'{ns}entry')
        product_node = select_by_vg(product_list)

        p = f"/Products('{product_node.find(f'{ns}id').text}')/Nodes('{product_node.find(f'{ns}title').text}.SAFE')"

        return [p]

    def build_search_query(self):
        if self.pre_filters is None:
            raise ValueError

        filters = ' AND '.join(
            [
                f'{key}:{value}'
                for key, value in sorted(self.pre_filters.items())
            ]
        )

        return f'/search?q={filters}'

    def do_query(self, query, stream=False):
        url = '{}{}'.format(self.odata_base_url, query)
        try:
            with self.session.get(url, auth=self.credentials, stream=stream) as response:
                if response.status_code == 200:
                    return response.content
                response.raise_for_status()
        except HTTPError:
            raise SentinelAPIError("Failed request to SentinelApi", response)

    def fetch_products(self):
        pass


class Sentinel2MSIData(SentinelData):

    def __int__(self, platformname, producttype, processinglevel):
        super().__init__(self, platformname, producttype, processinglevel)

    def fetch_products(self):
        product_list = self.create_product_list()
        # choose product by vegetation coverage percentage or
        # random choice. We want only one image to fetch.
        products = []
        for product_path in product_list:
            image_files, granule_identifier = self._get_image_files(product_path)
            metadata = self._get_metadata(product_path, granule_identifier)
            bands = self._get_bands(product_path, image_files, metadata)
            products.append(bands)
        self.products = products

    def _get_image_files(self, product_path):
        query = "{}{}/Nodes('MTD_MSIL2A.xml')/$value".format(self.odata_path, product_path)
        response = self.do_query(query)
        root = xml.fromstring(response)
        image_files = [item.text for item in root.findall('.//IMAGE_FILE')]
        _, identifier, _, _, _ = image_files[0].split('/')
        return image_files, identifier

    def _get_metadata(self, product_path, granule_identifier):
        query = "{}{}/Nodes('GRANULE')/Nodes('{}')/Nodes('MTD_TL.xml')/$value"\
            .format(self.odata_path, product_path, granule_identifier)
        response = self.do_query(query)
        root = xml.fromstring(response)
        ns = namespace(root)
        tile_info = root.find(f'./{ns}Geometric_Info/Tile_Geocoding')
        cs_name = tile_info.find('HORIZONTAL_CS_NAME')
        cs_code = tile_info.find('HORIZONTAL_CS_CODE')
        size = tile_info.iter('Size')
        resolution = self.post_filters.get('resolution')
        for item in size:
            r = item.attrib.get('resolution')
            if r == resolution:
                height = item.find('NROWS')
                width = item.find('NCOLS')
                break

        return {
            "crs": {"code": cs_code.text, "name": cs_name.text},
            "height": int(height.text),
            "width": int(width.text),
            "resolution": int(resolution)
        }

    def _get_bands(self, product_path, image_files, metadata):
        height = metadata.get('height')
        width = metadata.get('width')
        bands = self.post_filters.get('bands')

        profile = {
            'driver': 'JP2OpenJPEG',
            'dtype': 'uint16',
            'nodata': None,
            'width': height,
            'height': width,
            'count': 1,
            'crs': CRS.from_epsg(32617),
            'transform': Affine(10.0, 0.0, 399960.0, 0.0, -10.0, 5600040.0)
        }

        num_bands = len(bands)
        image = np.zeros((num_bands, height, width))
        filtered_image_files = self._image_files_by_post_filters(image_files)

        for i, file_path in enumerate(filtered_image_files):
            granule, identifier, img_folder, res_folder, file_name = file_path.split('/')
            query = "{}{}/Nodes('{}')/Nodes('{}')/Nodes('{}')/Nodes('{}')/Nodes('{}.jp2')/$value"\
                .format(self.odata_path, product_path, granule, identifier, img_folder, res_folder, file_name)
            image_bytes = self.do_query(query, stream=True)
            with MemoryFile(image_bytes) as memfile:
                with memfile.open(**profile) as dataset:
                    img = dataset.read()
                    image[i::] = img
            return image

    def _image_files_by_post_filters(self, image_files):
        files = []
        res = self.post_filters.get('resolution')
        pattern = f'*_{res}m'
        files_by_resolution = fnmatch.filter(image_files, pattern)
        for band in self.post_filters.get('bands'):
            pattern = f'*_{band}_*'
            for file in files_by_resolution:
                if fnmatch.fnmatch(file, pattern):
                    files.append(file)
        return files

