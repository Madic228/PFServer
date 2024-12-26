from pydantic import BaseModel

class NewsRequest(BaseModel):
    topic_id: int

class NewsResponse(BaseModel):
    topic_id: int
    title: str
    publication_date: str
    link: str
    content: str
    summarized_text: str
    source: str
