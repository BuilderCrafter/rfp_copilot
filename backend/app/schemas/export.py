from pydantic import BaseModel


class ExportResponse(BaseModel):
    download_url: str
    exported_answer_count: int
