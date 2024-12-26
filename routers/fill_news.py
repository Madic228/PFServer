from fastapi import APIRouter, HTTPException
from typing import List
from models.news import NewsRequest, NewsResponse
from services.news_service import get_news_by_topic

router = APIRouter()

@router.post("/news/", response_model=List[NewsResponse])
def fetch_news(request: NewsRequest):
    """Возвращает первые 3 новости по указанной тематике."""
    return get_news_by_topic(request.topic_id)
