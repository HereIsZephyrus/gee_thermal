import os
import logging
from abc import ABC, abstractmethod
from ..monitor import Monitor

logger = logging.getLogger(__name__)

class Controller(ABC):
    def __init__(self, project_manager):
        self.project_manager = project_manager
        self.monitor = Monitor(project_manager.tracker_folder_path, project_manager.drive_manager, project_manager.collection_path)
        self.missing_file_path = os.path.join(project_manager.collection_path, "missing.txt")
        self.exclude_list = self._create_exclude_list(project_manager.collection_path)

    def _create_exclude_list(self, collection_path: str):
        """
        Create the exclude list
        """
        # find all the files in the collection_path, record year-month pair
        exclude_list = []
        os.makedirs(collection_path, exist_ok=True)
        if os.path.exists(self.missing_file_path):
            with open(self.missing_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    year, month = line.strip().split('-')
                    exclude_list.append(f"{int(year)}-{int(month):02}")
        else:
            with open(self.missing_file_path, 'w', encoding='utf-8') as f:
                pass

        for file in os.listdir(collection_path):
            if file.endswith('.tif'):
                elements = file.split('.')[0].split('-')
                year = int(elements[1])
                month = int(elements[2])
                exclude_list.append(f"{year}-{month:02}")
        return exclude_list

    @abstractmethod
    def create_image_series(self, calculator):
        """
        Create the image series
        """
        if not self.project_manager.initialized:
            if not self.project_manager.initialize():
                logger.error("Failed to initialize project manager")
                return

    def post_process(self):
        """
        Post process the data
        """
        pass
