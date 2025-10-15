import ee
import os
import logging
from .ncep_tpw import add_tpw_band
from .cloudmask import mask_sr, mask_toa, calc_cloud_cover
from .compute_metadata import add_index_func, add_timestamp
from .compute_ndvi import add_ndvi_band
from .compute_fvc import add_fvc_band
from .compute_emissivity import add_emissivity_band
from .smw_algorithm import add_lst_band
from .compute_ndbi import add_ndbi_band
from .compute_evi import add_evi_band
from .compute_green import add_green_band
from .constants import LANDSAT_BANDS

logger = logging.getLogger(__name__)
logging.getLogger('ee').setLevel(logging.WARNING)

# Set the path to the service account key file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../.gee-sa-priv-key.json"

def minimum_cloud_cover(image_collection, geometry, cloud_cover_geometry, mask_method, date_start):
    """
    Returns the mosaiced image with the minimum cloud cover in the cloud_cover_geometry
    """
    total_area = geometry.area().getInfo()
    add_index = add_index_func(date_start)
    image_collection = image_collection.map(add_index)
    index_list = list(set(image_collection.aggregate_array('INDEX').getInfo()))
    best_image = None
    best_cloud_cover = 100
    porpotion = 0
    for index in index_list:
        image_condidate_list = image_collection.filter(ee.Filter.eq('INDEX',index))
        image_num = image_condidate_list.size().getInfo()
        if image_num == 0:
            continue
        geometries_feature = image_condidate_list.map(
            lambda image: ee.Feature(image.geometry())
        )
        geometries_feature = ee.FeatureCollection(geometries_feature)
        raw_geometry = geometries_feature.union().geometry()
        intersect = raw_geometry.intersection(geometry)
        image_area = intersect.area().getInfo()
        porpotion = image_area / total_area
        logger.debug('index %s has %s images, the proportion is %s / %s = %s', index, image_num, image_area, total_area, porpotion)
        if (porpotion < 0.8):
            continue
        mosaiced_image = image_condidate_list.mosaic().clip(geometry)
        try:
            couning_area_cloud_cover = calc_cloud_cover(mosaiced_image, cloud_cover_geometry, mask_method)
        except ValueError as e:
            logger.warning("%s", e)
            continue
        if couning_area_cloud_cover < best_cloud_cover:
            best_cloud_cover = couning_area_cloud_cover
            construct_date = ee.Date(date_start).advance(index, 'day').millis()
            best_image = mask_method(mosaiced_image).set('system:time_start', construct_date)

    if best_image is None:
        raise ValueError("No image found for the specified date range.")
    return best_image, porpotion, best_cloud_cover, index + 1

def fetch_best_landsat_image(landsat,date_start,date_end,geometry,cloud_theshold,cloud_cover_geometry,use_ndvi = False):
    """
    Fetches the best Landsat image(mimum cloud cover in cloud_cover_geometry)

    Parameters:
    - landsat: Name of the Landsat collection (e.g., 'L8')
    - date_start: Start date for the collection
    - date_end: End date for the collection
    - geometry: Area of interest
    - cloud_theshold: Cloud cover threshold
    - cloud_cover_geometry: Area of interest for cloud cover
    - use_ndvi: Boolean indicating whether to use NDVI

    Returns:
    - landsatLST: Processed Landsat collection with LST
    """
    # Check if the provided Landsat collection is valid
    if landsat not in LANDSAT_BANDS.keys():
        raise ValueError(
            f"Invalid Landsat constellation: {landsat}. \
            Valid options are: {list(LANDSAT_BANDS.keys())}"
        )

    collection_dict = LANDSAT_BANDS[landsat]

    # Load TOA Radiance/Reflectance
    landsat_toa = (
        ee.ImageCollection(collection_dict["TOA"])
        .filterDate(date_start, date_end)
        .filterBounds(geometry)
        .filter(ee.Filter.lessThan('CLOUD_COVER', cloud_theshold))
    )
    if landsat_toa is None:
        raise ValueError("No toa images found for the specified date range.")

    landsat_sr = (
        ee.ImageCollection(collection_dict["SR"])
        .filterDate(date_start, date_end)
        .filterBounds(geometry)
        .filter(ee.Filter.lessThan('CLOUD_COVER', cloud_theshold))
    )
    if landsat_sr is None:
        raise ValueError("No sr images found for the specified date range.")

    try:
        best_landsat_toa, toa_porpotion, toa_cloud_cover, toa_date = minimum_cloud_cover(landsat_toa, geometry, cloud_cover_geometry, mask_toa, date_start)
    except ValueError as ve:
        raise ValueError(f"TOA: {ve}") from ve
    except Exception as e:
        logger.error("Error finding toa minimum cloud cover: %s", e)
        raise e

    # Load Surface Reflectance collection for NDVI  and apply transformations
    try:
        best_landsat_sr, sr_porpotion, sr_cloud_cover, sr_date = minimum_cloud_cover(landsat_sr, geometry, cloud_cover_geometry, mask_sr, date_start)
    except ValueError as ve:
        raise ValueError(f"SR: {ve}") from ve
    except Exception as e:
        logger.error("Error finding sr minimum cloud cover: %s", e)
        raise e

    if toa_date != sr_date:
        logger.warning("TOA and SR timestamps do not match. TOA: %s, SR: %s", toa_date, sr_date)

    try:
        best_landsat_sr = add_ndvi_band(landsat, best_landsat_sr)
        best_landsat_sr = add_fvc_band(landsat, best_landsat_sr)
    except Exception as e:  
        logger.error("Error adding NDVI, FVC bands: %s", e)
        raise e

    try:
        best_landsat_sr = add_ndbi_band(landsat, best_landsat_sr)
    except Exception as e:
        logger.error("Error adding NDBI band: %s", e)
        raise e

    try:
        best_landsat_sr = add_evi_band(landsat, best_landsat_sr)
    except Exception as e:
        logger.error("Error adding EVI band: %s", e)
        raise e

    try:
        best_landsat_sr = add_green_band(landsat, best_landsat_sr)
    except Exception as e:
        logger.error("Error adding Green band: %s", e)
        raise e

    try:
        best_landsat_sr = add_tpw_band(best_landsat_sr)
    except Exception as e:
        logger.error("Error adding TPW band: %s", e)
        raise e

    try:
        best_landsat_sr = add_emissivity_band(landsat, use_ndvi, best_landsat_sr)
    except Exception as e:
        logger.error("Error adding emissivity band: %s", e)
        raise e

    # Combine collections
    tir = collection_dict["TIR"]
    visw = collection_dict["VISW"] + ["NDVI", "FVC", "NDBI", "EVI", "Green", "EM", "TPW", "TPWpos"]
    try:
        best_landsat = best_landsat_sr.select(visw).addBands(best_landsat_toa.select(tir))
    except Exception as e:
        logger.error("Error adding bands: %s", e)
        raise e

    # Compute the LST
    #landsat_lst = landsat_all.map(lambda image: add_lst_band(landsat, image))
    try:
        best_landsat_lst = add_lst_band(landsat, best_landsat)
    except Exception as e:
        logger.error("Error adding LST band: %s", e)
        raise e
    # best_landsat_lst = add_timestamp(best_landsat_lst)
    if best_landsat_lst is None:
        logger.error("No processed LST images found for the specified date range.")
        raise ValueError("No processed LST images found for the specified date range.")

    # align all bands to the same value type
    best_landsat_lst = best_landsat_lst.select(best_landsat_lst.bandNames()).toFloat()
    return best_landsat_lst, toa_porpotion, sr_porpotion, toa_cloud_cover, sr_cloud_cover, toa_date

def fetch_landsat_collection(landsat, date_start, date_end, geometry, cloud_theshold, use_ndvi = False):
    """
    Fetches a Landsat collection based on the provided parameters
    and applies several transformations.

    Parameters:
    - landsat: Name of the Landsat collection (e.g., 'L8')
    - date_start: Start date for the collection
    - date_end: End date for the collection
    - geometry: Area of interest
    - cloud_theshold: Cloud cover threshold
    - use_ndvi: Boolean indicating whether to use NDVI

    Returns:
    - landsatLST: Processed Landsat collection with LST
    """
    # Check if the provided Landsat collection is valid
    if landsat not in LANDSAT_BANDS.keys():
        raise ValueError(
            f"Invalid Landsat constellation: {landsat}. \
            Valid options are: {list(LANDSAT_BANDS.keys())}"
        )

    collection_dict = LANDSAT_BANDS[landsat]

    # Load TOA Radiance/Reflectance
    landsat_toa = (
        ee.ImageCollection(collection_dict["TOA"])
        .filterDate(date_start, date_end)
        .filterBounds(geometry)
        .filter(ee.Filter.lessThan('CLOUD_COVER', cloud_theshold))
    )

    if landsat_toa is None:
        raise ValueError("No toa images found for the specified date range.")

    # Load Surface Reflectance collection for NDVI  and apply transformations
    landsat_sr = (
        ee.ImageCollection(collection_dict["SR"])
        .filterDate(date_start, date_end)
        .filterBounds(geometry)
        .filter(ee.Filter.lessThan('CLOUD_COVER', cloud_theshold))
        .map(mask_sr)
        .map(lambda image: add_ndvi_band(landsat, image))
        .map(lambda image: add_fvc_band(landsat, image))
        .map(lambda image: add_ndbi_band(landsat, image))
        .map(lambda image: add_evi_band(landsat, image))
        .map(lambda image: add_green_band(landsat, image))
        .map(add_tpw_band)
        .map(lambda image: add_emissivity_band(landsat, use_ndvi, image))
    )

    if landsat_sr is None:
        raise ValueError("No sr images found for the specified date range.")

    # Combine collections
    tir = collection_dict["TIR"]
    visw = collection_dict["VISW"] + ["NDVI", "FVC", "NDBI", "EVI", "Green", "TPW", "TPWpos", "EM"]
    landsat_all = landsat_sr.select(visw).combine(landsat_toa.select(tir), True)

    # Compute the LST
    landsat_lst = landsat_all.map(lambda image: add_lst_band(landsat, image))

    # Add timestamp to each image in the collection
    landsat_lst = landsat_lst.map(add_timestamp)
    return landsat_lst
