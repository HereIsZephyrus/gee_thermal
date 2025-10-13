import os
import logging
import time
from abc import ABC, abstractmethod
import pickle

logger = logging.getLogger(__name__)

def check_file_occupied(file_path):
    """
    Check if the file is occupied by other process
    """
    try:
        os.rename(file_path, file_path)
        return False
    except OSError:
        return True

class TaskState(ABC):
    """
    Abstract task state
    """
    @abstractmethod
    def handle(self, tracker):
        pass

class HoldState(TaskState):
    """
    State when the task is hold to wait network or parallel limit
    """
    max_task_num = 5
    def handle(self, tracker):
        # Count the number of .pkl files in tracker folder
        tracker_folder = os.path.dirname(tracker.tracker_file_path)
        pkl_files = [f for f in os.listdir(tracker_folder) if f.endswith('.pkl')]
        if len(pkl_files) >= self.max_task_num:
            return HoldState()
        tracker.task = tracker.image.create_export_task()
        logger.info("ready to export : %s", tracker.task)
        return ExportState()

class ExportState(TaskState):
    """
    State when the task is exporting
    """
    def handle(self, tracker):
        status = tracker.task.status()
        state = status['state']
        if state != 'READY':
            if state == 'COMPLETED':
                logger.info("Success to export %s", tracker.image.image_name)
                return DownloadState()
            if state in ['FAILED', 'CANCELLED']:
                logger.info("Failed to export %s", tracker.image.image_name)
                return CompeletedState()
            logger.info("exporting %s", tracker.image.image_name)
        return ExportState()

class DownloadState(TaskState):
    """
    State when the task is downloading
    """
    def handle(self, tracker):
        cloud_file_name = tracker.image.image_name
        file_obj = tracker.get_fileobj(cloud_file_name)
        logger.info("get fileobj: %s", file_obj)
        local_file_name = os.path.join(tracker.collection_path, cloud_file_name)
        local_file_name = f"{local_file_name}.tif"
        logger.info("downloading to %s", local_file_name)

        # Add retry mechanism for SSL/network errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                file_obj.GetContentFile(local_file_name)
                logger.info("download completed: %s", cloud_file_name)
                return CompeletedState()
            except (OSError, IOError, ConnectionError, Exception) as e:
                error_msg = str(e)
                # Handle various network and download errors
                if any(keyword in error_msg for keyword in ["SSL", "EOF", "Connection", "IncompleteRead", "Broken pipe"]):
                    logger.warning("Network error during download (attempt %d/%d): %s", attempt + 1, max_retries, error_msg)
                    if attempt == max_retries - 1:
                        logger.error("Failed to download %s after %d attempts", cloud_file_name, max_retries)
                        return CompeletedState()  # Still return CompletedState to avoid infinite retry
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Unexpected error during download: %s", error_msg)
                    return CompeletedState()

class CompeletedState(TaskState):
    """
    State when the task is finished
    """
    def handle(self, tracker):
        cloud_file_name = tracker.image.image_name
        file_obj = tracker.get_fileobj(cloud_file_name)
        file_obj.Delete()
        logger.info("Delete cloud file: %s", cloud_file_name)
        return None

class TaskTracker:
    """
    Track the status of a task
    """
    def __init__(self, image, get_fileobj, tracker_folder_path, collection_path):
        self.image = image
        self.get_fileobj = get_fileobj
        self.tracker_file_path = os.path.join(tracker_folder_path, f"{self.image.image_name}.pkl")
        self.task = None
        self.state = None
        self.collection_path = collection_path

    def start(self):
        """
        Start the tracker
        """
        self.state = HoldState()
        self.state = self.state.handle(self)

    def ckeck_status(self) -> bool:
        """
        Monitor task status until it is completed or failed
        """
        self.state = self.state.handle(self)
        self.dump()
        return self.state is not None

    def dump(self):
        """
        Dump the tracker to file
        """
        if self.state is None:
            return
        # Create a copy for serialization
        tracker_data = {
            'image': self.image,
            'get_fileobj': self.get_fileobj,
            'tracker_file_path': self.tracker_file_path,
            'task': self.task,
            'state': self.state,
            'collection_path': self.collection_path
        }

        with open(self.tracker_file_path, 'wb') as f:
            pickle.dump(tracker_data, f)
        logger.debug("Dump tracker to %s", self.tracker_file_path)

    def __del__(self):
        """
        Delete the tracker file when the tracker is completed
        """
        if self.state is None:
            try:
                if os.path.exists(self.tracker_file_path):
                    os.remove(self.tracker_file_path)
                    logger.info("Successfully deleted tracker file: %s", self.tracker_file_path)
                else:
                    logger.warning("Tracker file does not exist: %s", self.tracker_file_path)
            except OSError as e:
                logger.error("Failed to delete tracker file %s: %s", self.tracker_file_path, e)

def recover_task_tracker(file_path) -> TaskTracker:
    """
    Recover the task tracker from the file
    """
    if not os.path.exists(file_path):
        logger.warning("Tracker file does not exist: %s", file_path)
        return None

    try:
        logger.info("recover task tracker from %s", file_path)
        with open(file_path, 'rb') as f:
            tracker_data = pickle.load(f)
        tracker = TaskTracker(
            image=tracker_data['image'],
            get_fileobj=tracker_data['get_fileobj'],
            tracker_folder_path=os.path.dirname(tracker_data['tracker_file_path']),
            collection_path=tracker_data['collection_path']
        )

        tracker.task = tracker_data['task']
        tracker.state = tracker_data['state']

        return tracker
    except (IOError, OSError, pickle.PickleError) as e:
        logger.error("Failed to recover tracker from %s: %s", file_path, e)
        return None
