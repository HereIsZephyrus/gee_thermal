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
        self.missing_file_path = os.path.join(project_manager.collection_path, "missing.txt")
        self.exclude_list = self._create_exclude_list(project_manager.collection_path)

    def _create_exclude_list(self, collection_path: str):
        """
        Create the exclude list
        """
        # find all the files in the collection_path, record year-month pair
        exclude_list = []
        os.makedirs(collection_path, exist_ok=True)
        if os.path.exists(self.missing_file_path):
            with open(self.missing_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    year, month = line.strip().split('-')
                    exclude_list.append(f"{int(year)}-{int(month):02}")
        else:
            with open(self.missing_file_path, 'w', encoding='utf-8') as f:
                pass

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
            quality_file_path=self.project_manager.quality_file_path,
            missing_file_path=self.missing_file_path
        )
        for year in range(self.year_range[0], self.year_range[1]+1):
            for month in range(1,13):
                if self.monitor.create_new_session(year = year, month = month, exclude_list = self.exclude_list):
                    logger.info("Creating new session for %s-%s", year, month)
                    export_func(year = year, month = month)
        logger.info("All done. >_<")
