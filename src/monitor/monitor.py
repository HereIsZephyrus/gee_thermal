import logging
import os
import threading
import time
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
        if not os.path.exists(self.monitor_file_path):
            logger.info("Monitor file does not exist, starting with empty trackers list")
            self.trackers = []
            return
        
        try:
            with open(self.monitor_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out None values from failed recoveries
            self.trackers = []
            for line in lines:
                line = line.strip()
                if line:  # Skip empty lines
                    tracker = recover_task_tracker(line)
                    if tracker is not None:
                        self.trackers.append(tracker)
                    else:
                        # Remove the invalid tracker file path from monitor file
                        self._remove_tracker_from_monitor_file(line)
            
            logger.info("Loaded %d valid trackers from monitor file", len(self.trackers))
        except (IOError, OSError) as e:
            logger.error("Error loading monitor file: %s", e)
            self.trackers = []

    def _remove_tracker_from_monitor_file(self, tracker_file_path):
        """
        Remove a tracker file path from the monitor file
        """
        try:
            with open(self.monitor_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out the invalid tracker file path
            filtered_lines = [line for line in lines if line.strip() != tracker_file_path]
            
            with open(self.monitor_file_path, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            logger.info("Removed invalid tracker from monitor file: %s", tracker_file_path)
        except (IOError, OSError) as e:
            logger.error("Error removing tracker from monitor file: %s", e)

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
        try:
            if self.drive_manager.gauth.credentials.refresh_token is None:
                logger.error('refresh token is None')
                return
            
            # Add retry mechanism for network issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.drive_manager.gauth.Refresh()
                    self.drive_manager.gauth.SaveCredentialsFile(self.drive_manager.credentials_file_path)
                    logger.info("token refreshed successfully, expires in: %s", self.drive_manager.gauth.credentials.token_expiry)
                    break
                except (BrokenPipeError, ConnectionError, OSError) as e:
                    logger.warning("Network error during token refresh (attempt %d/%d): %s", attempt + 1, max_retries, e)
                    if attempt == max_retries - 1:
                        logger.error("Failed to refresh token after %d attempts", max_retries)
                        return
                    time.sleep(2 ** attempt)  # Exponential backoff
                except (ValueError, RuntimeError) as e:
                    logger.error("Unexpected error during token refresh: %s", e)
                    return

        except Exception as e:
            logger.error("Error in token refresh process: %s", e)
        finally:
            # Schedule next refresh regardless of success/failure
            threading.Timer(self.refresh_interval * 5, self._check_and_refresh_token).start()
