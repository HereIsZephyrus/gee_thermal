import logging
import ee

logger = logging.getLogger(__name__)

def fetch_moodis_image(date: ee.Date, geometry: ee.Geometry) -> ee.Image:
    """
    Fetch MODIS MOD11A1 daily LST data for specified date

    Parameters:
    - date: Target date (ee.Date)
    - geometry: Clipping geometry (ee.Geometry)

    Returns:
    - ee.Image: MODIS MOD11A1 image with LST related bands

    Selected bands:
    - LST_Day_1km: Daytime Land Surface Temperature (K) - scaled by 0.02 and cast to float
    - LST_Night_1km: Nighttime Land Surface Temperature (K) - scaled by 0.02 and cast to float
    - QC_Day: Daytime LST Quality Indicators - cast to float for data type consistency
    - QC_Night: Nighttime LST Quality Indicators - cast to float for data type consistency
    """
    try:
        date_start = ee.Date(date).update(hour=0, minute=0, second=0)
        date_end = date_start.advance(1, 'day')

        # Load MODIS MOD11A1 daily dataset
        modis_collection = ee.ImageCollection('MODIS/061/MOD11A1') \
            .filterDate(date_start, date_end) \
            .filterBounds(geometry)

        # Process LST related bands with proper scale and offset

        # Get the daily image and clip to geometry
        daily_image = modis_collection.first()
        if daily_image is None:
            raise ValueError(f"No MODIS data available for date: {date_start.format('YYYY-MM-dd')}")

        # Apply scale and offset transformations for LST bands
        # LST bands: scale = 0.02, offset = 0
        # QC bands: keep as original type for consistency
        # Use cast() to ensure all bands have the same data type
        lst_day_scaled = daily_image.select('LST_Day_1km').toFloat().multiply(0.02)
        lst_night_scaled = daily_image.select('LST_Night_1km').toFloat().multiply(0.02)
        qc_day = daily_image.select('QC_Day')
        qc_night = daily_image.select('QC_Night')
        
        # Cast all bands to the same data type (float) to avoid export errors
        result_image = ee.Image.cat([
            lst_day_scaled.cast({'LST_Day_1km': 'float'}),
            lst_night_scaled.cast({'LST_Night_1km': 'float'}),
            qc_day.cast({'QC_Day': 'float'}),
            qc_night.cast({'QC_Night': 'float'})
        ]).clip(geometry)

        # Set timestamp
        result_image = result_image.set('system:time_start', date_start.millis())
        logger.info("Successfully fetched MODIS LST data")

        return result_image

    except Exception as e:
        logger.error("Error fetching MODIS LST image: %s", e)
        raise e
