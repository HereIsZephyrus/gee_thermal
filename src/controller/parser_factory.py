from .parser import Parser
from .lst_parser import LstParser
from .era5_parser import Era5Parser
from .thermal_parser import ThermalParser

@staticmethod
def construct_parser(parser_type: str, quality_file_path: str) -> Parser:
    """
    Parser factory method
    """
    parser_map = {
        'lst': LstParser,
        'era5': Era5Parser,
        'thermal': ThermalParser,
    }
    if parser_type not in parser_map:
        raise ValueError(f"Invalid parser type: {parser_type}")
    return parser_map[parser_type](quality_file_path)