import logging
from abc import ABC, abstractmethod
from ..monitor import Monitor

logger = logging.getLogger(__name__)

class Controller(ABC):
    def __init__(self, project_manager):
        self.project_manager = project_manager
        self.monitor = Monitor(project_manager.tracker_folder_path, project_manager.drive_manager, project_manager.collection_path)

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
