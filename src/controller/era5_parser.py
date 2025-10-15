import logging
from .parser import Parser

logger = logging.getLogger(__name__)

class Era5Parser(Parser):
    """
    Parser for the record file
    """
    def parse_record(self, start_year: int, end_year: int):
        """
        Parse the record file
        """
        pass