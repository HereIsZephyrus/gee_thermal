import logging
import csv
import os
import glob
from functools import partial
import numpy as np
from osgeo import gdal, ogr, osr
from .controller import Controller
from .export import export_image

logger = logging.getLogger(__name__)

class Era5Controller(Controller):
    def __init__(self, project_manager, check_days_file_path):
        super().__init__(project_manager)
        self.check_days_file_path = check_days_file_path

    def create_image_series(self, calculator):
        super().create_image_series(calculator)
        self.monitor.start()
        export_func = partial(export_image,
            drive_manager=self.project_manager.drive_manager,
            city_asset=calculator.city_asset,
            cloud_path=self.project_manager.cloud_folder_name,
            monitor=self.monitor,
            missing_file_path=self.missing_file_path,
            calculator=calculator
        )
        with open(self.check_days_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip the header row
            next(reader)
            for row in reader:
                year, month, _ = row
                year_int = int(year)
                month_int = int(month)
                if self.monitor.create_new_session(year = year_int, month = month_int, exclude_list = self.exclude_list):
                    logger.info("Creating new session for %s-%s", year_int, month_int)
                    export_func(year = year_int, month = month_int)
                else:
                    logger.info("Skipping %s-%s", year_int, month_int)

        logger.info("All done. >_<")
        self.monitor.stop()

    def post_process(self):
        """
        Post-process ERA5 TIF files: read all TIF files, calculate wind speed and direction, 
        generate point features for wind visualization
        """
        logger.info("Starting ERA5 data post-processing...")
        output_dir = self.project_manager.collection_path
        if not os.path.exists(output_dir):
            logger.error("Output directory does not exist: %s", output_dir)
            return

        # Find all TIF files
        tif_pattern = os.path.join(output_dir, "*.tif")
        tif_files = glob.glob(tif_pattern)

        if not tif_files:
            logger.warning("No TIF files found: %s", tif_pattern)
            return

        logger.info("Found %d TIF files", len(tif_files))

        # Initialize statistics collection
        statistics_data = []

        # Process each TIF file
        for tif_file in tif_files:
            try:
                file_stats = self._process_single_tif(tif_file)
                if file_stats:
                    statistics_data.extend(file_stats)
            except (IOError, OSError, ValueError) as e:
                logger.error("Error processing file %s: %s", tif_file, e)

        # Save statistics to CSV
        if statistics_data:
            self._save_statistics_to_csv(statistics_data, output_dir)

        logger.info("ERA5 data post-processing completed")

    def _process_single_tif(self, tif_file):
        """
        Process single TIF file, extract wind components and generate point features
        Returns statistics data for this file
        """
        base_name = os.path.splitext(os.path.basename(tif_file))[0]
        logger.info("Processing file: %s", base_name)

        # Open TIF file using GDAL
        dataset = gdal.Open(tif_file, gdal.GA_ReadOnly)
        if dataset is None:
            logger.error("Cannot open file: %s", tif_file)
            return None

        geotransform = dataset.GetGeoTransform()
        projection = dataset.GetProjection()

        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        logger.info("Raster dimensions: %d x %d", cols, rows)

        # Extract wind component data
        wind_data = self._extract_wind_components(dataset)

        if wind_data is None:
            logger.warning("No wind data found: %s", base_name)
            dataset = None
            return None

        # Calculate statistics for each time point
        file_statistics = self._calculate_wind_statistics(wind_data, base_name)

        # Generate point features for each time point as separate GPKG files
        self._create_wind_vector_points_by_time(wind_data, geotransform, projection, tif_file, base_name)

        dataset = None
        logger.info("Completed processing: %s", base_name)

        return file_statistics

    def _extract_wind_components(self, dataset):
        """
        Extract wind components from GDAL dataset
        """
        band_names = []
        for i in range(1, dataset.RasterCount + 1):
            band = dataset.GetRasterBand(i)
            band_name = band.GetDescription()
            band_names.append(band_name)

        logger.info("Band names: %s", band_names)

        # Find u and v component bands for each time point
        u_bands = []
        v_bands = []

        for i, name in enumerate(band_names):
            if 'u_component_of_wind_10m' in name:
                u_bands.append((i + 1, name))  # GDAL band index starts from 1
            elif 'v_component_of_wind_10m' in name:
                v_bands.append((i + 1, name))

        if not u_bands or not v_bands:
            logger.warning("No wind component bands found")
            return None

        logger.info("Found %d U-component bands, %d V-component bands", len(u_bands), len(v_bands))

        # Read wind data for all time points
        wind_data = []

        for (u_idx, u_name), (v_idx, _) in zip(u_bands, v_bands):
            time_str = u_name.split('_h')[-1] if '_h' in u_name else '00'

            u_band = dataset.GetRasterBand(u_idx)
            v_band = dataset.GetRasterBand(v_idx)

            u_array = u_band.ReadAsArray()
            v_array = v_band.ReadAsArray()

            # Calculate wind speed and direction
            wind_speed = np.sqrt(u_array**2 + v_array**2)
            wind_direction = np.arctan2(v_array, u_array) * 180 / np.pi

            # Convert to meteorological standard (from north, clockwise)
            wind_direction = (90 - wind_direction) % 360

            wind_data.append({
                'time': time_str,
                'u_component': u_array,
                'v_component': v_array,
                'wind_speed': wind_speed,
                'wind_direction': wind_direction
            })

        return wind_data

    def _create_wind_vector_points_by_time(self, wind_data, geotransform, projection, tif_file, base_name):
        """
        Create separate GPKG files for each time point using OGR
        """
        output_dir = os.path.dirname(tif_file)

        # Get dimensions from first time point data
        first_data = wind_data[0]
        rows, cols = first_data['wind_speed'].shape

        logger.info("Processing all %d x %d pixels (no resampling)", rows, cols)

        # Process each time point separately
        for time_data in wind_data:
            time_str = time_data['time']
            output_gpkg = os.path.join(output_dir, f"{base_name}_wind_vectors_h{time_str}.gpkg")

            # Create GPKG output using OGR driver
            driver = ogr.GetDriverByName('GPKG')

            # Remove existing file if it exists
            if os.path.exists(output_gpkg):
                driver.DeleteDataSource(output_gpkg)

            # Create data source
            data_source = driver.CreateDataSource(output_gpkg)

            # Create spatial reference system from projection
            srs = osr.SpatialReference()
            srs.ImportFromWkt(projection)

            # Create layer with point geometry
            layer = data_source.CreateLayer('wind_vectors', srs, ogr.wkbPoint)

            # Create attribute fields
            layer.CreateField(ogr.FieldDefn('x', ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn('y', ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn('time', ogr.OFTString))
            layer.CreateField(ogr.FieldDefn('wind_speed', ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn('wind_dir', ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn('u_comp', ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn('v_comp', ogr.OFTReal))

            # Create features for all pixels in this time point
            point_count = 0
            for row in range(rows):
                for col in range(cols):
                    # Calculate geographic coordinates using geotransform
                    x = geotransform[0] + col * geotransform[1] + row * geotransform[2]
                    y = geotransform[3] + col * geotransform[4] + row * geotransform[5]

                    # Extract wind data at this location
                    wind_speed = float(time_data['wind_speed'][row, col])
                    wind_dir = float(time_data['wind_direction'][row, col])
                    u_comp = float(time_data['u_component'][row, col])
                    v_comp = float(time_data['v_component'][row, col])

                    # Skip invalid data (NaN values)
                    if np.isnan(wind_speed) or np.isnan(wind_dir):
                        continue

                    # Create point feature using OGR
                    feature = ogr.Feature(layer.GetLayerDefn())

                    # Set point geometry
                    point = ogr.Geometry(ogr.wkbPoint)
                    point.AddPoint(x, y)
                    feature.SetGeometry(point)

                    # Set attribute values
                    feature.SetField('x', x)
                    feature.SetField('y', y)
                    feature.SetField('time', time_str)
                    feature.SetField('wind_speed', wind_speed)
                    feature.SetField('wind_dir', wind_dir)
                    feature.SetField('u_comp', u_comp)
                    feature.SetField('v_comp', v_comp)

                    # Add feature to layer
                    layer.CreateFeature(feature)
                    feature = None
                    point_count += 1

            # Clean up resources
            data_source = None

            logger.info("Created %d wind vector points for time %s: %s", point_count, time_str, output_gpkg)

    def _calculate_wind_statistics(self, wind_data, base_name):
        """
        Calculate wind speed statistics for each time point
        """
        statistics = []

        for time_data in wind_data:
            time_str = time_data['time']
            wind_speed = time_data['wind_speed']

            # Remove NaN values for statistics calculation
            valid_wind_speed = wind_speed[~np.isnan(wind_speed)]

            if len(valid_wind_speed) == 0:
                logger.warning("No valid wind speed data for %s at time %s", base_name, time_str)
                continue

            # Calculate statistics
            mean_speed = np.mean(valid_wind_speed)
            min_speed = np.min(valid_wind_speed)
            max_speed = np.max(valid_wind_speed)
            std_speed = np.std(valid_wind_speed)

            statistics.append({
                'filename': base_name,
                'time': time_str,
                'mean_wind_speed': mean_speed,
                'min_wind_speed': min_speed,
                'max_wind_speed': max_speed,
                'std_wind_speed': std_speed,
                'valid_pixels': len(valid_wind_speed),
                'total_pixels': wind_speed.size
            })

            logger.info("Statistics for %s time %s: mean=%.2f, min=%.2f, max=%.2f, std=%.2f", 
                       base_name, time_str, mean_speed, min_speed, max_speed, std_speed)

        return statistics

    def _save_statistics_to_csv(self, statistics_data, output_dir):
        """
        Save wind speed statistics to CSV file
        """
        csv_file = os.path.join(output_dir, "era5_wind_statistics.csv")

        # Define CSV headers
        headers = [
            'filename',
            'time',
            'mean_wind_speed',
            'min_wind_speed', 
            'max_wind_speed',
            'std_wind_speed',
            'valid_pixels',
            'total_pixels'
        ]

        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(statistics_data)

            logger.info("Wind speed statistics saved to: %s", csv_file)
            logger.info("Total statistics records: %d", len(statistics_data))

        except (IOError, OSError) as e:
            logger.error("Error saving statistics to CSV: %s", e)
