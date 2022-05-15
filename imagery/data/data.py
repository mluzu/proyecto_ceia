from abc import ABC, abstractmethod


class Data(ABC):

    @abstractmethod
    def set_bonds_filter(self, bonds):
        pass

    @abstractmethod
    def set_date_filter(self, begin, end):
        pass

    @abstractmethod
    def set_bands_filter(self, bands):
        pass

    @abstractmethod
    def set_cloudcoverage_filter(self, minpercentage, maxpercentage):
        pass

    @abstractmethod
    def fetch_products(self):
        pass

    @abstractmethod
    def get(self, count):
        pass


def get():
    pass
