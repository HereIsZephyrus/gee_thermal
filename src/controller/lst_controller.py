import os
import logging
from functools import partial
from .export import export_image
from .controller import Controller

logger = logging.getLogger(__name__)

class LstController(Controller):
    def __init__(self, project_manager, year_range: tuple, parser):
        super().__init__(project_manager)
        self.year_range = year_range
        self.parser = parser

    def create_image_series(self, calculator):
        """
        Create the image series
        """
        super().create_image_series(calculator)
        self.monitor.start()
        export_func = partial(export_image,
            drive_manager=self.project_manager.drive_manager,
            city_asset=calculator.city_asset,
            cloud_path=self.project_manager.cloud_folder_name,
            monitor=self.monitor,
            missing_file_path=self.missing_file_path,
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
