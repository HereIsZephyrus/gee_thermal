import csv
import traceback
import logging
import ee
from .calculator import Calculator
from ..communicator import CityAsset
from ..lst_algorithm import fetch_best_landsat_image

logger = logging.getLogger(__name__)

class LstCalculator(Calculator):

    def calculate(self):
        """ 
        Calculate the LST image series
        """
        satellite_list = ['L8', 'L5', 'L7', 'L4']
        date_start = ee.Date.fromYMD(self.year, self.month, 1)
        date_end = ee.Date.fromYMD(self.year, self.month, self.month_length).advance(1, 'day')
        use_ndvi = True
        cloud_threshold = 25
        quality_file_path = self.quality_file_path

        landsat_coll = None
        for satellite in satellite_list:
            try:
                landsat_coll, toa_porpotion, sr_porpotion, toa_cloud, sr_cloud , day = fetch_best_landsat_image(
                    landsat=satellite,
                    date_start=date_start,
                    date_end=date_end,
                    geometry=self.city_asset.city_geometry,
                    cloud_theshold=cloud_threshold,
                    cloud_cover_geometry=self.city_asset.urban_geometry,
                    use_ndvi=use_ndvi)
                with open(quality_file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([self.city_asset.name, self.year, self.month, toa_porpotion, sr_porpotion, toa_cloud, sr_cloud, day])
                logging.info("success: %s", satellite)
                break
            except ValueError as ve:
                logging.info("no data for %s(%s)", satellite, ve)
                continue
            except Exception as e:
                logging.error("fetch error: %s\n traceback: %s", e, traceback.format_exc())
                continue
        
        self.image = landsat_coll
