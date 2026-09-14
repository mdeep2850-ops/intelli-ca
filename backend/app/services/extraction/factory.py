from app.services.extraction.base import BaseExtractor
from app.services.extraction.pdf_extractor import PDFExtractor
from app.services.extraction.docx_extractor import DOCXExtractor
from app.services.extraction.xlsx_extractor import XLSXExtractor

def get_extractor(file_type: str, filename: str) -> BaseExtractor:
    if file_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return PDFExtractor()
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.lower().endswith(".docx"):
        return DOCXExtractor()
    elif file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or filename.lower().endswith(".xlsx"):
        return XLSXExtractor()
    else:
        raise ValueError(f"Unsupported file type for extraction: {file_type} / {filename}")
