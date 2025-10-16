"""
Export image
"""
import logging
from pypinyin import lazy_pinyin as pinyin
from .image import Image
from ..communicator.drive_manager import DriveManager
from ..communicator.ee_manager import CityAsset
from ..monitor import Monitor

logger = logging.getLogger(__name__)

def export_image(
    drive_manager: DriveManager, city_asset: CityAsset, cloud_path: str,
    monitor: Monitor, year: int, month: int, missing_file_path: str,
    calculator):
    """
    export the lst image to the drive
    """
    e_city_name = ''.join(pinyin(city_asset.name))
    image_name = f"{e_city_name}-{year}-{month:02}"
    bands = calculator.calculate(year, month)
    if bands is None:
        logger.info("no bands for %s", image_name)
        with open(missing_file_path, 'a', encoding='utf-8') as f:
            f.write(f"{year}-{month:02}\n")
        return False
    image = Image(drive_manager, cloud_path, image_name, city_asset.city_geometry, calculator.pixel_resolution)
    image.add_band(bands)
    try:
        monitor.export(image)
    except Exception as e:
        logger.error("error to create export task: %s", e)
        return False
    return True
