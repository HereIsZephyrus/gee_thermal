import logging
from functools import partial
from .export import export_image
from ..communicator.ee_manager import CityAsset
from ..monitor import Monitor

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, project_manager, year_range: tuple, monitor_folder_path: str):
        self.project_manager = project_manager
        self.year_range = year_range
        self.monitor = Monitor(monitor_folder_path, project_manager.drive_manager, project_manager.collection_path)

    def create_image_series(self):
        """
        Create the image series
        """
        if not self.project_manager.initialized:
            if not self.project_manager.initialize():
                logger.error("Failed to initialize project manager")
                return
        city_asset: CityAsset = self.project_manager.getCityAsset(city_name = "武汉市")
        export_func = partial(export_image,
            drive_manager=self.project_manager.drive_manager,
            city_asset=city_asset,
            save_path=self.project_manager.save_path,
            monitor=self.monitor
        )
        for year in range(self.year_range[0], self.year_range[1]+1):
            for month in range(1,13):
                export_func(year = year, month = month)
        logger.info("All done. >_<")
