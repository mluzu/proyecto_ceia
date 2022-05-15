from .data import Sentinel2MSIData


class Collection:
    def __init__(self, platformname, producttype, processinglevel) -> None:
        self.data = Sentinel2MSIData(platformname, producttype, processinglevel)

    def filter_bonds(self, rectangle):
        self.data.set_bonds_filter(rectangle)
        return self

    def filter_date(self, begin, end):
        self.data.set_date_filter(begin, end)
        return self

    def filter_bands(self, bands):
        self.data.set_bands_filter(bands)
        return self

    def filter_cloudcoverage(self,  minpercentage, maxpercentage):
        self.data.set_cloudcoverage_filter(minpercentage, maxpercentage)
        return self
    
    def size(self):
        pass

    def mean(self):
        pass

    def read(self, count=1):
        image = self.data.get(count)
        return image


  