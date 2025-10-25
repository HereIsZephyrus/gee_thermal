import csv
from abc import ABC, abstractmethod
import ee
from ..communicator import CityAsset

class Calculator(ABC):
    def __init__(self, city_asset: CityAsset, quality_file_path: str, missing_file_path: str, pixel_resolution: int, check_days_file_path = None):
        self.city_asset = city_asset
        self.quality_file_path = quality_file_path
        self.missing_file_path = missing_file_path
        self.pixel_resolution = pixel_resolution
        self.map_days = None
        if check_days_file_path is not None:
            self.map_days = self._create_map_days(check_days_file_path)

    def _create_map_days(self, check_days_file_path: str) -> dict:
        """
        Create the map days
        """
        map_days = {}
        with open(check_days_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # exclude the first row
            next(reader)
            for row in reader:
                year, month, day = row
                map_days[f"{int(year)}-{int(month):02}"] = int(day)
        return map_days

    @abstractmethod
    def calculate(self, year: int, month: int) -> ee.ImageCollection:
        pass

    def get_month_length(self, year: int, month: int) -> int:
        """
        Get the month length
        """
        month_length = [31,28,31,30,31,30,31,31,30,31,30,31]
        length = month_length[month-1]
        if month != 2:
            return length
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return length+1
        return length
