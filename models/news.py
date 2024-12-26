from pydantic import BaseModel

class NewsRequest(BaseModel):
    topic_id: int
    limit: int = 5  # Количество возвращаемых записей по умолчанию

class NewsResponse(BaseModel):
    topic_id: int
    title: str
    publication_date: str
    link: str
    summarized_text: str
    source: str
