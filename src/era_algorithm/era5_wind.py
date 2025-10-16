import logging
import ee

logger = logging.getLogger(__name__)

def fetch_era5_image(date: ee.Date, geometry: ee.Geometry) -> ee.Image:
    """
    Fetch ERA5-Land hourly data for specified date with wind and temperature bands

    Parameters:
    - date: Target date (ee.Date)
    - geometry: Clipping geometry (ee.Geometry)

    Returns:
    - ee.Image: ERA5-Land image with wind and temperature bands

    Selected bands:
    - u_component_of_wind_10m: 10m wind speed U component (m/s)
    - v_component_of_wind_10m: 10m wind speed V component (m/s)
    - temperature_2m: 2m air temperature (K)
    - skin_temperature: Surface skin temperature (K)
    - dewpoint_temperature_2m: 2m dewpoint temperature (K)
    - surface_latent_heat_flux_hourly: Surface latent heat flux (W/m2)
    - surface_net_solar_radiation_hourly: Surface net solar radiation (W/m2)
    - surface_net_thermal_radiation_hourly: Surface net thermal radiation (W/m2)
    - surface_sensible_heat_flux_hourly: Surface sensible heat flux (W/m2)
    - surface_solar_radiation_downwards_hourly: Surface solar radiation downwards (W/m2)
    - surface_thermal_radiation_downwards_hourly: Surface thermal radiation downwards (W/m2)
    - evaporation_from_bare_soil_hourly: Evaporation from bare soil (mm/h)
    """
    try:
        date_start = ee.Date(date).update(hour=0, minute=0, second=0)
        date_end = date_start.advance(1, 'day')

        # Load ERA5-Land hourly dataset
        era5_collection = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY') \
            .filterDate(date_start, date_end) \
            .filterBounds(geometry)

        # Select wind and temperature related bands
        selected_bands = [
            'u_component_of_wind_10m',
            'v_component_of_wind_10m',
            'temperature_2m',
            'skin_temperature',
            'dewpoint_temperature_2m',
            'surface_latent_heat_flux_hourly',
            'surface_net_solar_radiation_hourly',
            'surface_net_thermal_radiation_hourly',
            'surface_sensible_heat_flux_hourly',
            'surface_solar_radiation_downwards_hourly',
            'surface_thermal_radiation_downwards_hourly',
            'evaporation_from_bare_soil_hourly'
        ]

        # Sample every 3 hours (0, 3, 6, 9, 12, 15, 18, 21)
        three_hourly_images = []
        for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
            hour_start = date_start.advance(hour, 'hour')
            hour_end = hour_start.advance(1, 'hour')

            # Get single image for this hour and clip to geometry
            hour_image = era5_collection.filterDate(hour_start, hour_end).first()
            clipped_image = hour_image.select(selected_bands).clip(geometry)

            # Add suffix to bands for each time period
            renamed_image = clipped_image.select(
                selected_bands,
                [f'{band}_h{hour:02d}' for band in selected_bands]
            )
            three_hourly_images.append(renamed_image)

        # Combine all time period bands into one image
        result_image = three_hourly_images[0]
        for img in three_hourly_images[1:]:
            result_image = result_image.addBands(img)

        # Set timestamp
        result_image = result_image.set('system:time_start', date_start.millis())
        logger.info("Successfully fetched ERA5-Land data")

        return result_image

    except Exception as e:
        logger.error("Error fetching ERA5-Land wind image: %s", e)
        raise e
