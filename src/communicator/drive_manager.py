"""
Google Drive Manager
"""
import logging
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

logger = logging.getLogger(__name__)

class DriveManager:
    """
    Manage the drive
    """
    def __init__(self, credentials_file_path: str, folder_id: str, cloud_folder_name: str):
        self.credentials_file_path = credentials_file_path
        self.gauth = self._init_gauth(credentials_file_path)
        self.drive = GoogleDrive(self.gauth)
        self.cloud_folder_name = cloud_folder_name
        self.folder_id = folder_id

    def get_fileobj(self, cloud_file_name):
        """
        Get the file object from the drive
        """
        file_list = self.drive.ListFile({
            'q': f"'{self.folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder'",
            'maxResults': 1000
        }).GetList()
        for file_obj in file_list:
            if (file_obj['title'].startswith(cloud_file_name)):
                return file_obj
        return None

    def _init_gauth(self, credentials_file_path: str):
        """
        Initialize the google authentication
        """
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(credentials_file_path)
        if (gauth.credentials is None):
            gauth.LocalWebserverAuth()
        if gauth.credentials.refresh_token is None:
            logger.warning("refresh token is None")
        return gauth

    def get_folder_id_by_name(self, folder_name, parent_id='root'):
        """
        Get the folder id by the folder name

        Args:
            folder_name: folder name
            parent_id: parent folder id
        """
        query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()
        if file_list:
            return file_list[0]['id']
        return None
