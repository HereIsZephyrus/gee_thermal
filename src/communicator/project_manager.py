"""
Project manager
"""
import logging
import os
import csv
from .drive_manager import DriveManager
from .ee_manager import EEManager

logger = logging.getLogger(__name__)

class ProjectManager:
    """
    Total project manager
    """
    def __init__(self, project_name: str, credentials_file_path: str, collection_path: str, drive_folder_id: str, cloud_folder_name: str, quality_file_path: str, monitor_file_path: str):
        self.project_name = project_name
        self.credentials_file_path = credentials_file_path
        self.collection_path = collection_path
        self.cloud_folder_name = cloud_folder_name
        self.drive_folder_id = drive_folder_id
        self.drive_manager = None
        self.ee_manager = None
        self.initialized = False
        self.quality_file_path = quality_file_path
        self.monitor_file_path = monitor_file_path

    def initialize(self) -> bool:
        """
        Initialize the project
        """
        if not self._init_cloud():
            logger.error("Failed to initialize cloud")
            return False
        if not self._init_local():
            logger.error("Failed to initialize local")
            return False
        self.initialized = True
        return True

    def _init_cloud(self) -> bool:
        """
        Initialize the cloud connection parameters
        """
        self.ee_manager = EEManager(self.project_name)
        logger.info("Initialized ee manager")
        self.drive_manager = DriveManager(self.credentials_file_path, folder_id=self.drive_folder_id, cloud_folder_name=self.cloud_folder_name)
        logger.info("Initialized drive manager")
        return True

    def _init_local(self) -> bool:
        """
        Initialize the local connection parameters
        """
        os.makedirs(os.path.dirname(self.monitor_file_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.quality_file_path), exist_ok=True)
        header = ['city', 'year', 'month', 'toa_image_porpotion', 'sr_image_porpotion', 'toa_cloud_ratio', 'sr_cloud_ratio', 'day']
        if not os.path.exists(self.monitor_file_path):
            with open(self.monitor_file_path, 'w', newline='', encoding='utf-8') as f:
                pass
        if not os.path.exists(self.quality_file_path):
            with open(self.quality_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
        return True

    def getCityAsset(self, city_name: str):
        """
        Get the city asset
        """
        return self.ee_manager.getCityAsset(city_name)
