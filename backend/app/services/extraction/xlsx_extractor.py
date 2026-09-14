import pandas as pd
from typing import Iterator
from app.schemas.document import DocumentElementCreate
from app.services.extraction.base import BaseExtractor

class XLSXExtractor(BaseExtractor):
    def extract(self, file_path: str, original_filename: str) -> Iterator[DocumentElementCreate]:
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            if not df.empty:
                # Fill na so markdown doesn't have NaN
                df = df.fillna("")
                markdown = df.to_markdown(index=False)
                yield DocumentElementCreate(
                    element_type="table",
                    content=markdown,
                    metadata_={
                        "original_filename": original_filename,
                        "sheet_name": sheet_name
                    }
                )
