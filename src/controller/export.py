"""
Export image
"""
import logging
from pypinyin import lazy_pinyin as pinyin
from .image import Image
from ..communicator.drive_manager import DriveManager
from ..communicator.ee_manager import CityAsset
from ..calculator import LstCalculator
from ..monitor import Monitor

logger = logging.getLogger(__name__)

def export_image(drive_manager: DriveManager, city_asset: CityAsset, save_path: str, monitor: Monitor, year: int, month: int):
    """
    export the lst image to the drive
    """
    e_city_name = ''.join(pinyin(city_asset.name))
    image_name = f"{e_city_name}-{year}-{month:02}"
    image = Image(drive_manager, save_path, image_name, city_asset.city_geometry)
    lst_calculator = LstCalculator(city_asset, year, month)
    lst_calculator.calculate()
    image.add_band(lst_calculator.image)
    try:
        monitor.export(image)
    except Exception as e:
        logger.error("error to create export task: %s", e)
        return False
    return True
