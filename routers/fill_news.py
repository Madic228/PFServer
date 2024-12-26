from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.news_service import get_news_by_topic

router = APIRouter()

# Модель для запроса
class NewsRequest(BaseModel):
    topic_id: int

# Модель для ответа
class NewsResponse(BaseModel):
    topic_id: int
    title: str
    publication_date: str
    link: str
    content: str
    summarized_text: str
    source: str

@router.post("/news/", response_model=List[NewsResponse])
def fetch_news(request: NewsRequest):
    """Возвращает первые 3 новости по указанной тематике."""
    return get_news_by_topic(request.topic_id)
