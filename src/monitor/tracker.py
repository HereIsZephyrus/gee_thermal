import os
import logging
from abc import ABC, abstractmethod
import pickle
from .writer import ThreadSafeFileWriter as FileWriter

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
    max_task_num = 10
    def handle(self, tracker):
        monitor_record_file = os.path.join(tracker.monitor_folder_path,"monitor.txt")
        with open(monitor_record_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) >= self.max_task_num:
            return HoldState()
        self.file_writer.write(content = tracker.monitor_file_path, mode='a')
        tracker.task = tracker.image.create_export_task()
        return ExportState()

class ExportState(TaskState):
    """
    State when the task is exporting
    """
    def handle(self, tracker):
        status = tracker.task.status()
        state = status['state']
        if (state != 'READY'):
            if state == 'COMPLETED':
                logger.info("Success to export %s", tracker.image.image_name)
                return DownloadState()
            if state in ['FAILED', 'CANCELLED']:
                return CompeletedState()
        return ExportState()

class DownloadState(TaskState):
    """
    State when the task is downloading
    """
    def handle(self, tracker):
        cloud_file_name = tracker.image.image_name
        file_obj = tracker.get_file_obj(cloud_file_name)
        local_file_name = os.path.join(tracker.collection_path, cloud_file_name)
        logger.info("downloading to %s", local_file_name)
        file_obj.GetContentFile(local_file_name)

class CompeletedState(TaskState):
    """
    State when the task is finished
    """
    def handle(self, tracker):
        cloud_file_name = tracker.image.image_name
        file_obj = tracker.get_file_obj(cloud_file_name)
        file_obj.Delete()
        logger.info("delete %s", cloud_file_name)
        with open(os.path.join(self.monitor_folder_path,"monitor.txt"), 'r', encoding='utf-8') as f:
            lines = f.readlines()
        lines = [line for line in lines if line.strip() != self.monitor_file_path]
        self.file_writer.write(content = "\n".join(lines), mode='w')
        return None

class TaskTracker:
    """
    Track the status of a task
    """
    def __init__(self, image, get_fileobj, monitor_folder_path, collection_path, monitor_file):
        self.image = image
        self.get_fileobj = get_fileobj
        self.monitor_folder_path = monitor_folder_path
        self.monitor_file_path = os.path.join(self.monitor_folder_path, f"{self.image.image_name}.pkl")
        self.task = None
        self.state = None
        self.collection_path = collection_path
        self.file_writer = FileWriter(monitor_file)

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
        return (self.state is not None)

    def dump(self):
        """
        Dump the tracker to file
        """
        with open(self.monitor_file_path, 'wb') as f:
            pickle.dump(self, f)
        logger.info("Dump tracker to %s", self.monitor_file_path)

def recover_task_tracker(file_path) -> TaskTracker:
    with open(file_path, 'rb') as f:
        tracker = pickle.load(f)
    return tracker
