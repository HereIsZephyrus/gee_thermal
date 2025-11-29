import csv
from typing import Optional
import traceback
import logging
import ee
from .calculator import Calculator
from ..communicator.ee_manager import CityAsset
from ..lst_algorithm import fetch_best_landsat_image

logger = logging.getLogger(__name__)

class LstCalculator(Calculator):
    def __init__(self, city_asset: CityAsset, quality_file_path: str, missing_file_path: str, check_days_file_path: Optional[str] = None):
        super().__init__(
            city_asset=city_asset,
            quality_file_path=quality_file_path,
            missing_file_path=missing_file_path,
            pixel_resolution=30,
            check_days_file_path=check_days_file_path
        )

    def calculate(self, year: int, month: int) -> ee.ImageCollection:
        """ 
        Calculate the LST image series
        """
        satellite_list = ['L8', 'L5', 'L7', 'L4']
        date_start = ee.Date.fromYMD(year, month, 1)
        date_end = ee.Date.fromYMD(year, month, self.get_month_length(year, month)).advance(1, 'day')
        use_ndvi = True
        cloud_threshold = 25
        quality_file_path = self.quality_file_path
        landsat_coll = None
        latitude = self.city_asset.latitude
        for satellite in satellite_list:
            try:
                landsat_coll, toa_porpotion, sr_porpotion, toa_cloud, sr_cloud , day = fetch_best_landsat_image(
                    landsat=satellite,
                    date_start=date_start,
                    date_end=date_end,
                    geometry=self.city_asset.city_geometry,
                    cloud_theshold=cloud_threshold,
                    cloud_cover_geometry=self.city_asset.urban_geometry,
                    use_ndvi=use_ndvi,
                    month=month,
                    latitude=latitude)
                with open(quality_file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.city_asset.name, year, month, toa_porpotion, sr_porpotion, toa_cloud, sr_cloud, day])
                logger.info("success: %s", satellite)
                break
            except ValueError as ve:
                logger.info("no data for %s(%s)", satellite, ve)
                continue
            except Exception as e:
                logger.error("fetch error: %s\n traceback: %s", e, traceback.format_exc())
                continue

        return landsat_coll
