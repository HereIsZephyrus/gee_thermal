from ..communicator import CityAsset
from .calculator import Calculator
from .lst_calculator import LstCalculator
from .era5_calculator import Era5Calculator
from .thermal_calculator import ThermalCalculator

@staticmethod
def construct_calculator(calculator_type: str, city_asset: CityAsset, quality_file_path: str, missing_file_path: str) -> Calculator:
    """
    Calculator factory method
    """
    calculator_map = {
        'lst': LstCalculator,
        'era5': Era5Calculator,
        'thermal': ThermalCalculator,
    }
    if calculator_type not in calculator_map:
        raise ValueError(f"Invalid calculator type: {calculator_type}")
    return calculator_map.get(calculator_type)(city_asset, quality_file_path, missing_file_path)
