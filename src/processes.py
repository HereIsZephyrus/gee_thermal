import logging
from typing import Optional
from .controller import LstController, LstParser, Era5Controller, ModisController
from .calculator import LstCalculator, Era5Calculator, MoodisCalculator

logger = logging.getLogger(__name__)

def process_lst(project_manager, city_asset, year_range, check_days_file_path: Optional[str] = None):
    """
    Process the LST image series
    """
    controller = LstController(
        project_manager=project_manager,
        year_range=year_range,
        parser=LstParser(project_manager.quality_file_path),
        check_days_file_path=check_days_file_path
    )
    calculator = LstCalculator(
        city_asset=city_asset,
        quality_file_path=project_manager.quality_file_path,
        missing_file_path=controller.missing_file_path,
        check_days_file_path=check_days_file_path
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

def process_era5(project_manager, city_asset, check_days_file_path):
    """
    Process the ERA5 image series
    """
    controller = Era5Controller(
        project_manager=project_manager,
        check_days_file_path=check_days_file_path
    )
    calculator = Era5Calculator(
        city_asset=city_asset,
        quality_file_path=project_manager.quality_file_path,
        missing_file_path=controller.missing_file_path,
        check_days_file_path=check_days_file_path
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

def process_thermal(project_manager, city_asset, check_days_file_path):
    """
    Process the thermal image series
    """
    controller = ModisController(
        project_manager=project_manager,
        check_days_file_path=check_days_file_path
    )
    calculator = MoodisCalculator(
        city_asset=city_asset,
        quality_file_path=project_manager.quality_file_path,
        missing_file_path=controller.missing_file_path,
        check_days_file_path=check_days_file_path
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
