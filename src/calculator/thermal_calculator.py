import ee
import logging
from .calculator import Calculator

logger = logging.getLogger(__name__)

class ThermalCalculator(Calculator):
    def calculate(self, year: int, month: int) -> ee.ImageCollection:
        pass