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
    def __init__(self, tracker_folder_path: str, drive_manager: DriveManager, collection_path, refresh_interval: int = 15):
        self.collection_path = collection_path
        self.trackers = []
        self.drive_manager = drive_manager
        self.refresh_interval = refresh_interval
        self.tracker_folder_path = tracker_folder_path
        self._create_tracker_folder()
        self._finished = False

    def _create_tracker_folder(self):
        """
        Create the tracker folder
        """
        os.makedirs(self.tracker_folder_path, exist_ok=True)

    def export(self, image):
        """
        Export the image to the drive
        """
        tracker = TaskTracker(
            image=image,
            get_fileobj=self.drive_manager.get_fileobj,
            tracker_folder_path=self.tracker_folder_path,
            collection_path=self.collection_path
        )
        tracker.start()
        logger.info("start tracker: %s", tracker.tracker_file_path)
        self.trackers.append(tracker)

    def stop(self):
        """
        Stop the monitor
        """
        self._finished = True

    def is_finished(self) -> bool:
        """
        Check if the monitor is finished
        """
        return self._finished and len(self.trackers) == 0

    def start(self):
        """
        Start the monitor
        """
        try:
            self._load_trackers()
        except Exception as e:
            logger.error("error to load trackers: %s", e)
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
        Check if the year-month pair is not recorded in the tracker folder
        """
        session_key = f"{year}-{month:02}"
        if session_key in exclude_list:
            return False

        # Check existing tracker files
        if not os.path.exists(self.tracker_folder_path):
            return True

        for filename in os.listdir(self.tracker_folder_path):
            if filename.endswith('.pkl') and session_key in filename:
                return False
        return True

    def _load_trackers(self):
        """
        Load tracker files from the tracker folder
        """
        if not os.path.exists(self.tracker_folder_path):
            logger.info("Tracker folder does not exist, starting with empty trackers list")
            self.trackers = []
            return

        try:
            # Scan the tracker folder for .pkl files
            self.trackers = []
            for filename in os.listdir(self.tracker_folder_path):
                if filename.endswith('.pkl'):
                    file_path = os.path.join(self.tracker_folder_path, filename)
                    tracker = recover_task_tracker(file_path)
                    if tracker is not None:
                        self.trackers.append(tracker)
                    else:
                        # Remove invalid tracker file
                        try:
                            os.remove(file_path)
                            logger.info("Removed invalid tracker file: %s", file_path)
                        except OSError as e:
                            logger.error("Failed to remove invalid tracker file %s: %s", file_path, e)

            logger.info("Loaded %d valid trackers from tracker folder", len(self.trackers))
        except (IOError, OSError) as e:
            logger.error("Error loading tracker files: %s", e)
            self.trackers = []

    def _check_trackers(self):
        """
        Check the trackers
        """
        try:
            for tracker in self.trackers:
                if not tracker.ckeck_status(): # failed or finished
                    self.trackers.remove(tracker)
        except Exception as e:
            logger.error("error to check trackers: %s", e)
        finally:
            if not self.is_finished():
                threading.Timer(self.refresh_interval, self._check_trackers).start()

    def _check_and_refresh_token(self):
        """
        Check and refresh the token
        """
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
            if not self.is_finished():
                threading.Timer(self.refresh_interval * 5, self._check_and_refresh_token).start()
