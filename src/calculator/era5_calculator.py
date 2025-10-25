import traceback
import logging
import ee
from .calculator import Calculator
from ..communicator.ee_manager import CityAsset
from ..era_algorithm import fetch_era5_image

logger = logging.getLogger(__name__)

class Era5Calculator(Calculator):
    def __init__(self, city_asset: CityAsset, quality_file_path: str, missing_file_path: str, check_days_file_path: str):
        super().__init__(city_asset, quality_file_path, missing_file_path, 11132, check_days_file_path)

    def calculate(self, year: int, month: int) -> ee.ImageCollection:
        """ 
        Calculate the LST image series
        """
        date = ee.Date.fromYMD(year, month, self.map_days.get(f"{year}-{month:02}", 1))
        try:
            era_image = fetch_era5_image(
                date=date,
                geometry=self.city_asset.urban_geometry
            )
        except ValueError as ve:
            logger.error("%s", ve)
            return None
        except Exception as e:
            logger.error("fetch error: %s\n traceback: %s", e, traceback.format_exc())
            return None

        return era_image
