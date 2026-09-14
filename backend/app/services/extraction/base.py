from abc import ABC, abstractmethod
from typing import Iterator
from app.schemas.document import DocumentElementCreate

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str, original_filename: str) -> Iterator[DocumentElementCreate]:
        pass
