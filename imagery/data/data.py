from abc import ABC, abstractmethod


class Data(ABC):
    """
    Every class in this module should drive from this abstract class
    in order to enforce the interface expected in Collection class
    """

    @abstractmethod
    def set_bonds_filter(self, bonds):
        pass

    @abstractmethod
    def set_date_filter(self, begin, end):
        pass

    @abstractmethod
    def set_bands_filter(self, *bands):
        pass

    @abstractmethod
    def set_cloudcoverage_filter(self, minpercentage, maxpercentage):
        pass

    @abstractmethod
    def fetch_products(self):
        pass

    @abstractmethod
    def read(self, count):
        pass
