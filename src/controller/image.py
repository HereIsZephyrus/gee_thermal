import logging
import ee
import traceback
from ..communicator.drive_manager import DriveManager

logger = logging.getLogger(__name__)

class Image:
    """
    The ee image class for exporting image to the drive
    """
    def __init__(self, drive_manager: DriveManager, save_path: str, image_name: str, geometry: ee.Geometry):
        self.drive_manager = drive_manager
        self.save_path = save_path
        self.image_name = image_name
        self.geometry = geometry
        self.bands = None

    def add_band(self, sub_image: ee.Image):
        if sub_image is None:
            logger.error("sub_image is None")
            return
        if self.bands is None:
            self.bands = sub_image
            logger.info("create image with band: %s", self.image_name)
        else:
            self.bands = self.bands.addBands(sub_image)
            logger.info("add band to image: %s", self.image_name)

    def create_export_task(self):
        """
        Create the Landsat LST image
        """
        # Define parameters
        try:
            task = ee.batch.Export.image.toDrive(image=self.bands,
                                    description=self.image_name,
                                    folder=f'{self.save_path}',
                                    scale=30,
                                    crs='EPSG:4326',
                                    region=self.geometry,
                                    fileFormat='GeoTIFF',
                                    maxPixels=1e13)
            task.start()
            return task
        except Exception as e:
            logger.error("error to export: %s\n traceback: %s", e, traceback.format_exc())
            return None
