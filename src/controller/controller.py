import os
import logging
from functools import partial
from .export import export_image
from ..monitor import Monitor

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, project_manager, year_range: tuple, parser):
        self.project_manager = project_manager
        self.year_range = year_range
        self.monitor = Monitor(project_manager.tracker_folder_path, project_manager.drive_manager, project_manager.collection_path)
        self.missing_file_path = os.path.join(project_manager.collection_path, "missing.txt")
        self.exclude_list = self._create_exclude_list(project_manager.collection_path)
        self.parser = parser

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

    def create_image_series(self, calculator):
        """
        Create the image series
        """
        if not self.project_manager.initialized:
            if not self.project_manager.initialize():
                logger.error("Failed to initialize project manager")
                return
        self.monitor.start()
        export_func = partial(export_image,
            drive_manager=self.project_manager.drive_manager,
            city_asset=calculator.city_asset,
            cloud_path=self.project_manager.cloud_folder_name,
            monitor=self.monitor,
            calculator=calculator
        )
        for year in range(self.year_range[0], self.year_range[1]+1):
            for month in range(1,13):
                if self.monitor.create_new_session(year = year, month = month, exclude_list = self.exclude_list):
                    logger.info("Creating new session for %s-%s", year, month)
                    export_func(year = year, month = month)
                else:
                    logger.info("Skipping %s-%s", year, month)
        logger.info("All done. >_<")
        self.monitor.stop()

    def post_process(self):
        """
        Post process the data
        """
        self.parser.parse_record(self.year_range[0], self.year_range[1])
