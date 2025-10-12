import os
import logging
from functools import partial
from .export import export_image
from ..communicator.ee_manager import CityAsset
from ..monitor import Monitor

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, project_manager, year_range: tuple):
        self.project_manager = project_manager
        self.year_range = year_range
        self.monitor = Monitor(project_manager.monitor_file_path, project_manager.drive_manager, project_manager.collection_path)
        self.exclude_list = self._create_exclude_list(project_manager.collection_path)

    def _create_exclude_list(self, collection_path: str):
        """
        Create the exclude list
        """
        # find all the files in the collection_path, record year-month pair
        exclude_list = []
        for file in os.listdir(collection_path):
            if file.endswith('.tif'):
                elements = file.split('.')[0].split('-')
                year = int(elements[1])
                month = int(elements[2])
                exclude_list.append(f"{year}-{month:02}")
        return exclude_list

    def create_image_series(self):
        """
        Create the image series
        """
        if not self.project_manager.initialized:
            if not self.project_manager.initialize():
                logger.error("Failed to initialize project manager")
                return
        self.monitor.start()
        city_asset: CityAsset = self.project_manager.getCityAsset(city_name = "武汉市")
        export_func = partial(export_image,
            drive_manager=self.project_manager.drive_manager,
            city_asset=city_asset,
            cloud_path=self.project_manager.cloud_folder_name,
            monitor=self.monitor,
            quality_file_path=self.project_manager.quality_file_path
        )
        for year in range(self.year_range[0], self.year_range[1]+1):
            for month in range(1,13):
                if self.monitor.create_new_session(year = year, month = month, exclude_list = self.exclude_list):
                    export_func(year = year, month = month)
        logger.info("All done. >_<")
