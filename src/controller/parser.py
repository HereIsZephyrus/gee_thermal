from abc import ABC, abstractmethod

class Parser(ABC):
    """
    Parser for the record file
    """
    def __init__(self, quality_file_path: str):
        self.file_path = quality_file_path

    @abstractmethod
    def parse_record(self, start_year: int, end_year: int):
        pass
