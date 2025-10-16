"""
The main entry point for the workflow image
"""
import logging
import os
import time
import sys
from dotenv import load_dotenv
from .communicator import ProjectManager
from .communicator.ee_manager import CityAsset
from .processes import process_lst, process_era5, process_thermal

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename=f'logs/image_generator_{time.strftime("%Y%m%d_%H%M%S", time.localtime())}.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger('ee').setLevel(logging.WARNING)

def main(args):
    load_dotenv()
    credentials_file_path = os.getenv('CREDENTIALS_FILE_PATH')
    collection_path = os.getenv('IMAGE_COLLECTION_PATH')
    project_name = os.getenv('PROJECT_NAME')
    quality_file_path = os.getenv('QUALITY_FILE_PATH')
    tracker_folder_path = os.getenv('TRACKER_FOLDER_PATH')
    drive_folder_id = os.getenv('DRIVE_FOLDER_ID')
    cloud_folder_name = os.getenv('DRIVE_FOLDER_NAME')
    calculator_type = args[0]
    project_manager = ProjectManager(
        project_name=project_name,
        credentials_file_path=credentials_file_path,
        collection_path=collection_path,
        drive_folder_id=drive_folder_id,
        cloud_folder_name=cloud_folder_name,
        quality_file_path=quality_file_path,
        tracker_folder_path=tracker_folder_path,
    )
    if not project_manager.initialize():
        logger.error("Failed to initialize project manager")
        return
    city_asset: CityAsset = project_manager.get_city_asset(city_name = "武汉市")
    if calculator_type == "lst":
        if len(args) != 3:
            logger.error("Usage: python -m src lst <start_year> <end_year>")
            sys.exit(1)
        year_range = (int(args[1]), int(args[2]))
        process_lst(project_manager, city_asset, year_range)
    elif calculator_type == "era5":
        if len(args) != 2:
            logger.error("Usage: python -m src era5 <check_days_file_path>")
            sys.exit(1)
        check_days_file_path = args[1]
        process_era5(project_manager, city_asset, check_days_file_path)
    elif calculator_type == "thermal":
        if len(args) != 2:
            logger.error("Usage: python -m src thermal <check_days_file_path>")
            sys.exit(1)
        check_days_file_path = args[1]
        process_thermal(project_manager, city_asset, check_days_file_path)
    else:
        logger.error("Invalid calculator type: %s", calculator_type)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        logger.error("Usage: python -m src <calculator_type> <args>")
        sys.exit(1)
    main(sys.argv[1:])
