from abc import ABC, abstractmethod
from typing import Optional
import ee
from ..communicator import CityAsset

class Calculator(ABC):
    def __init__(self, city_asset: CityAsset, year: int, month: int, quality_file_path: str):
        self.city_asset = city_asset
        self.year = year
        self.month = month
        self.month_length = self._get_month_length()
        self.quality_file_path = quality_file_path
        self.image: Optional[ee.Image] = None

    @abstractmethod
    def calculate(self):
        pass

    def _get_month_length(self) -> int:
        """
        Get the month length
        """
        month_length = [31,28,31,30,31,30,31,31,30,31,30,31]
        length = month_length[self.month-1]
        if self.month != 2:
            return length
        if (self.year % 4 == 0 and self.year % 100 != 0) or (self.year % 400 == 0):
            return length+1
        return length
