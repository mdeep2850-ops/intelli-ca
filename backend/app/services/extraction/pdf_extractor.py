from pypdf import PdfReader
from typing import Iterator
from app.schemas.document import DocumentElementCreate
from app.services.extraction.base import BaseExtractor

class PDFExtractor(BaseExtractor):
    def extract(self, file_path: str, original_filename: str) -> Iterator[DocumentElementCreate]:
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                yield DocumentElementCreate(
                    element_type="text",
                    content=text.strip(),
                    metadata_={
                        "page_number": i + 1,
                        "original_filename": original_filename
                    }
                )
