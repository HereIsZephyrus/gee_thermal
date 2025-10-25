import logging
import csv
from typing import Optional
from functools import partial
from .export import export_image
from .controller import Controller

logger = logging.getLogger(__name__)

class LstController(Controller):
    def __init__(self, project_manager, year_range: tuple, parser, check_days_file_path: Optional[str] = None):
        super().__init__(project_manager)
        self.year_range = year_range
        self.parser = parser
        self.check_days_file_path = check_days_file_path

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
        if self.check_days_file_path is not None:
            with open(self.check_days_file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # Skip the header row
                next(reader)
                for row in reader:
                    year, month, _ = row
                    year_int = int(year)
                    month_int = int(month)
                    if self.monitor.create_new_session(year = year_int, month = month_int, exclude_list = self.exclude_list):
                        logger.info("Creating new session for %s-%s", year_int, month_int)
                        export_func(year = year_int, month = month_int)
                    else:
                        logger.info("Skipping %s-%s", year_int, month_int)
        else:
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
