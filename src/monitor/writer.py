import threading
import time
import logging

logger = logging.getLogger(__name__)

class ThreadSafeFileWriter:
    def __init__(self, file_path):
        self.file_path = file_path
        self.write_lock = threading.Lock()

    def is_locked(self):
        """
        Check if the file is locked by other process
        """
        return self.write_lock.locked()

    def write(self, content, mode):
        """
        Write content to file in thread safe way
        """
        acquired = self.write_lock.acquire(blocking=False)
        while not acquired:
            time.sleep(0.1)
            acquired = self.write_lock.acquire(blocking=False)

        try:
            with open(self.file_path, mode, encoding='utf-8') as f:
                f.write(content + '\n')
            logger.info("Thread %s write %s to file %s", threading.current_thread().name, content, self.file_path)
            return True
        finally:
            self.write_lock.release()