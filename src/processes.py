import logging
from .controller import Controller, LstParser
from .calculator import LstCalculator

logger = logging.getLogger(__name__)

def process_lst(project_manager, city_asset, year_range):
    """
    Process the LST image series
    """
    controller = Controller(
        project_manager=project_manager,
        year_range=year_range,
        parser=LstParser(project_manager.quality_file_path)
    )
    calculator = LstCalculator(
        city_asset=city_asset,
        quality_file_path=project_manager.quality_file_path,
        missing_file_path=controller.missing_file_path
    )
    try:
        controller.create_image_series(calculator)
    except Exception as e:
        logger.error("Failed to create image series: %s", e)
        return

    try:
        controller.post_process()
    except Exception as e:
        logger.error("Failed to post process: %s", e)
        return

def process_era5(project_manager, city_asset, year_range):
    """
    Process the ERA5 image series
    """
    pass