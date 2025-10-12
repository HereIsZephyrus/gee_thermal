import logging
import os
import threading
from datetime import datetime, timedelta
from .tracker import TaskTracker, recover_task_tracker
from ..communicator.drive_manager import DriveManager

logger = logging.getLogger(__name__)

class Monitor:
    """
    Monitor for the system, to trace export task and network status
    """
    def __init__(self, monitor_file_path: str, drive_manager: DriveManager, collection_path, refresh_interval: int = 15):
        self.collection_path = collection_path
        self.monitor_file_path = monitor_file_path
        self.trackers = []
        self.drive_manager = drive_manager
        self.refresh_interval = refresh_interval
        self.tracker_folder_path = self._create_tracker_folder()

    def _create_tracker_folder(self):
        """
        Create the tracker folder
        """
        base_path = os.path.dirname(self.monitor_file_path)
        tracker_folder_path = os.path.join(base_path, "tracker")
        os.makedirs(tracker_folder_path, exist_ok=True)
        return tracker_folder_path

    def export(self, image):
        """
        Export the image to the drive
        """
        tracker = TaskTracker(
            image=image,
            get_fileobj=self.drive_manager.get_fileobj,
            tracker_folder_path=self.tracker_folder_path,
            monitor_file_path=self.monitor_file_path,
            collection_path=self.collection_path
        )
        tracker.start()
        logger.info("start tracker: %s", tracker.tracker_file_path)
        self.trackers.append(tracker)

    def start(self):
        """
        Start the monitor
        """
        try:
            self._load_monitor_file()
        except Exception as e:
            logger.error("error to load monitor file: %s", e)
            raise e

        try:
            self._check_trackers()
        except Exception as e:
            logger.error("error to check trackers: %s", e)

        try:
            self._check_and_refresh_token()
        except Exception as e:
            logger.error("error to check and refresh token: %s", e)

    def create_new_session(self, year: int, month: int, exclude_list: list) -> bool:
        """
        Check if the year-month pair is not recorded in the monitor file
        """
        session_key = f"{year}-{month:02}"
        if session_key in exclude_list:
            return False
        with open(self.monitor_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            if session_key in line:
                return False
        return True

    def _load_monitor_file(self):
        """
        Load the monitor file
        """
        with open(self.monitor_file_path, 'r', encoding='utf-8') as f:
            self.trackers = [recover_task_tracker(line.strip()) for line in f.readlines()]

    def _check_trackers(self):
        """
        Check the trackers
        """
        for tracker in self.trackers:
            try:
                if not tracker.ckeck_status(): # failed or finished
                    self.trackers.remove(tracker)
                    with open(self.monitor_file_path, 'w', encoding='utf-8') as f:
                        f.writelines([line for line in f.readlines() if line.strip() != tracker.tracker_file_path])
            except Exception as e:
                logger.error("error to check tracker: %s", e)

        threading.Timer(self.refresh_interval, self._check_trackers).start()

    def _check_and_refresh_token(self):
        if self.drive_manager.gauth.credentials.refresh_token is None:
            raise Exception('refresh token is None')
        delta_time = (self.drive_manager.gauth.credentials.token_expiry + timedelta(hours=8) - datetime.now()).total_seconds() # adjust for UTC+8
        if delta_time < 300:
            self.drive_manager.gauth.Refresh()
            self.drive_manager.gauth.SaveCredentialsFile(self.drive_manager.credentials_file_path)
            logger.info("token current expires in: %s", self.drive_manager.gauth.credentials.token_expiry)

        threading.Timer(self.refresh_interval, self._check_and_refresh_token).start()
