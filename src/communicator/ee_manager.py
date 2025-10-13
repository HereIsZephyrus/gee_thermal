"""
Google Earth Engine Manager
"""
import logging
import ee

logger = logging.getLogger(__name__)

class CityAsset:
    """
    Google Earth Engine City asset
    """
    def __init__(self, asset: ee.FeatureCollection, assets_path: str):
        self.asset = asset
        self.name = asset.getInfo()['features'][0]['properties']['市名']
        self.code = asset.getInfo()['features'][0]['properties']['市代码']
        self.city_geometry = ee.Geometry(asset.getInfo()['features'][0]['geometry'])
        urban_boundary = ee.FeatureCollection(f'{assets_path}/urban_{self.code}')
        self.urban_geometry = self._filter_city_bound(urban_boundary.geometry())

    def _filter_city_bound(self, city_geometry: ee.Geometry):
        """
        city geometry buffer has many scatters. select the largest polygon as the main urban area
        """
        if city_geometry.type().getInfo() == 'Polygon':
            return city_geometry
        geometry_num = city_geometry.geometries().length().getInfo()
        logger.debug("geometry_num: %s", geometry_num)
        largest = None
        max_area = 0
        for i in range(0,geometry_num):
            polygon = ee.Geometry.Polygon(city_geometry.coordinates().get(i))
            area = polygon.area().getInfo()
            if area > max_area:
                max_area = area
                largest = ee.Geometry(polygon)
        logger.debug("max area is %s", max_area)
        return largest

class EEManager:
    """
    Manager for Google Earth Engine
    """
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.assets_path = f'projects/{self.project_name}/assets'
        ee.Initialize(project=self.project_name)

    def get_city_asset(self, city_name: str) -> CityAsset:
        """
        Get the city asset
        """
        total_boundary = ee.FeatureCollection(f'{self.assets_path}/YZBboundary')
        city_boundary = total_boundary.filter(ee.Filter.eq('市名', city_name))
        return CityAsset(city_boundary, self.assets_path)
