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
    def __init__(self, monitor_folder_path: str, drive_manager: DriveManager, collection_path, refresh_interval: int = 15):
        self.monitor_folder_path = monitor_folder_path
        self.collection_path = collection_path
        self.monitor_file = os.path.join(monitor_folder_path, 'monitor.txt')
        self.trackers = []
        self.drive_manager = drive_manager
        self.refresh_interval = refresh_interval

    def export(self, image):
        """
        Export the image to the drive
        """
        tracker = TaskTracker(
            image=image,
            get_fileobj=self.drive_manager.get_fileobj,
            monitor_folder_path=self.monitor_folder_path,
            collection_path=self.collection_path,
            monitor_file = self.monitor_file
        )
        tracker.start()
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

    def _load_monitor_file(self):
        """
        Load the monitor file
        """
        with open(self.monitor_file, 'r', encoding='utf-8') as f:
            self.trackers = [recover_task_tracker(line) for line in f.readlines()]

    def _check_trackers(self):
        """
        Check the trackers
        """
        for tracker in self.trackers:
            try:
                if not tracker.check_task_status(): # failed or finished
                    self.trackers.remove(tracker)
                    with open(self.monitor_file, 'w', encoding='utf-8') as f:
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
