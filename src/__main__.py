"""
The main entry point for the workflow image
"""
import logging
import os
from dotenv import load_dotenv
from .controller import Parser, Controller
from .communicator import ProjectManager

logging.basicConfig(
    filename='workflow_image.log',
    filemode='w',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger('ee').setLevel(logging.WARNING)

def main():
    load_dotenv()
    credentials_file_path = os.getenv('CREDENTIALS_FILE_PATH')
    collection_path = os.getenv('IMAGE_COLLECTION_PATH')
    project_name = os.getenv('PROJECT_NAME')
    quality_file_path = os.getenv('QUALITY_FILE_PATH')
    monitor_file_path = os.getenv('MONITOR_FILE_PATH')
    drive_folder_id = os.getenv('DRIVE_FOLDER_ID')
    cloud_folder_name = os.getenv('DRIVE_FOLDER_NAME')
    year_range = (2015, 2025)
    project_manager = ProjectManager(
        project_name=project_name,
        credentials_file_path=credentials_file_path,
        collection_path=collection_path,
        drive_folder_id=drive_folder_id,
        cloud_folder_name=cloud_folder_name,
        quality_file_path=quality_file_path,
        monitor_file_path=monitor_file_path,
    )
    if not project_manager.initialize():
        logger.error("Failed to initialize project manager")
        return
    controller = Controller(
        project_manager=project_manager,
        year_range=year_range
    )
    try:
        controller.create_image_series()
    except Exception as e:
        logger.error("Failed to create image series: %s", e)
        return
    parser = Parser(quality_file_path, year_range=year_range)
    parser.parse_record()

if __name__ == '__main__':
    main()
