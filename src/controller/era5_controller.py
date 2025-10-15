import logging
import csv
from .controller import Controller
from functools import partial
from .export import export_image

logger = logging.getLogger(__name__)

class Era5Controller(Controller):
    def __init__(self, project_manager, check_days_file_path):
        super().__init__(project_manager)
        self.check_days_file_path = check_days_file_path

    def create_image_series(self, calculator):
        super().create_image_series(calculator)
        self.monitor.start()
        export_func = partial(export_image,
            drive_manager=self.project_manager.drive_manager,
            city_asset=calculator.city_asset,
            cloud_path=self.project_manager.cloud_folder_name,
            monitor=self.monitor,
            missing_file_path="self.missing_file_path",
            calculator=calculator
        )
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

        logger.info("All done. >_<")
        self.monitor.stop()

    def post_process(self):
        return
