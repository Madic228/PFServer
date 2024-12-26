from fastapi import APIRouter, HTTPException
from typing import List
from models.news import NewsRequest, NewsResponse
from services.news_service import get_news_by_topic

router = APIRouter()

@router.post("/news/", response_model=List[NewsResponse])
def fetch_news(request: NewsRequest):
    """Возвращает новости по указанной тематике и количеству."""
    return get_news_by_topic(request.topic_id, request.limit)
