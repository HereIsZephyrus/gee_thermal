import ee
import logging

logger = logging.getLogger(__name__)

def calc_cloud_cover(image, whole_geometry, mask_method):
    counting_image = image.clip(whole_geometry)
    first_band_name = counting_image.bandNames().get(0)
    total_counting_pixel = counting_image.reduceRegion(
        reducer = ee.Reducer.count(),
        geometry = whole_geometry,
        scale = 30,
        maxPixels = 1e13
    ).get(first_band_name).getInfo()
    if (total_counting_pixel == 0):
        raise ValueError("the image is not cover the urban area")
    # the invalid value pixels are cloud coverd pixels
    cloud_cover_pixel = mask_method(counting_image).reduceRegion(
        reducer = ee.Reducer.count(),
        geometry = whole_geometry,
        scale = 30,
        maxPixels = 1e13
    ).get(first_band_name).getInfo()
    result = (1 - float(cloud_cover_pixel / total_counting_pixel)) * 100
    logger.debug("cloud cover ratio is 1 - %s/%s = %s%%", cloud_cover_pixel, total_counting_pixel, result)
    return result

def mask_sr(image):
    """
    Apply cloud mask to surface reflectance Landsat image.

    Parameters:
    - image (ee.Image): Input Landsat image.

    Returns:
    - ee.Image: Cloud-masked Landsat image.
    """

    cloud_mask = (
        image.select("QA_PIXEL")
        .bitwiseAnd(1 << 3)
        .Or(image.select("QA_PIXEL").bitwiseAnd(1 << 4))
        .eq(0)
    )
    return image.updateMask(cloud_mask)


def mask_toa(image):
    """
    Apply cloud mask to top-of-atmosphere reflectance Landsat image.

    Parameters:
    - image (ee.Image): Input Landsat image.

    Returns:
    - ee.Image: Cloud-masked Landsat image.
    """

    cloud_mask = image.select("QA_PIXEL").bitwiseAnd(1 << 3).eq(0)
    return image.updateMask(cloud_mask)
