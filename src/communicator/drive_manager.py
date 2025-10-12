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
    def __init__(self, credentials_file_path: str, parent_folder_id: str, cloud_folder_name: str):
        self.gauth = self._init_gauth(credentials_file_path)
        self.drive = GoogleDrive(self.gauth)
        self.cloud_folder_name = cloud_folder_name
        self.folder_id = self._create_folder(parent_folder_id, cloud_folder_name)

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
        gauth.Refresh()
        if gauth.credentials.refresh_token is None:
            logger.warning("refresh token is None")
        return gauth

    def _create_folder(self, parent_folder_id, folder_name):
        """
        Create a folder in the drive

        Args:
            parent_folder_id: parent folder id
            folder_name: folder name

        Returns:
            folder id
        """
        folder_metadata = {
            'title': folder_name,
            'parents': [{'id': parent_folder_id}],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        all_files = self.drive.ListFile({'q': "trashed=false"}).GetList()
        logger.info("current drive all files: %s", len(all_files))
        logger.info("token current expires in: %s", self.gauth.credentials.token_expiry)
        try:
            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
            logger.info("Created folder: %s, folder id: %s", folder_name, folder['id'])
            return folder['id']
        except Exception as e:
            logger.error("Failed to create folder: %s", str(e))
            return None

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
