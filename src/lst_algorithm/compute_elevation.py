import ee
def add_elevation_band(image):
    """
    Add elevation band to the image.
    """
    elevation = ee.Image("USGS/SRTMGL1_003").select("elevation").clip(image.geometry())
    return image.addBands(elevation.rename("ELEVATION"))
