from docx import Document
from typing import Iterator
from app.schemas.document import DocumentElementCreate
from app.services.extraction.base import BaseExtractor

class DOCXExtractor(BaseExtractor):
    def extract(self, file_path: str, original_filename: str) -> Iterator[DocumentElementCreate]:
        doc = Document(file_path)
        
        for child in doc.element.body:
            if child.tag.endswith('p'):
                from docx.text.paragraph import Paragraph
                para = Paragraph(child, doc)
                if para.text.strip():
                    yield DocumentElementCreate(
                        element_type="text",
                        content=para.text.strip(),
                        metadata_={
                            "original_filename": original_filename,
                            "type": "paragraph"
                        }
                    )
            elif child.tag.endswith('tbl'):
                from docx.table import Table
                table = Table(child, doc)
                markdown = ""
                for row_idx, row in enumerate(table.rows):
                    row_data = [cell.text.replace('\\n', ' ').strip() for cell in row.cells]
                    markdown += "| " + " | ".join(row_data) + " |\\n"
                    if row_idx == 0:
                        markdown += "|" + "|".join(["---"] * len(row.cells)) + "|\\n"
                
                if markdown.strip():
                    yield DocumentElementCreate(
                        element_type="table",
                        content=markdown.strip(),
                        metadata_={
                            "original_filename": original_filename,
                            "type": "table"
                        }
                    )
