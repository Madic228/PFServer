from fastapi import APIRouter, HTTPException
from typing import List, Dict
from models.news import NewsRequest, NewsResponse
from services.news_service import get_news_by_topic, get_news_by_date, get_topics_statistics
from pydantic import BaseModel

router = APIRouter()

class DateRangeRequest(BaseModel):
    start_date: str
    end_date: str

@router.post("/news/", response_model=List[NewsResponse])
def fetch_news(request: NewsRequest):
    """Возвращает новости по указанной тематике и количеству."""
    return get_news_by_topic(request.topic_id, request.limit)

@router.post("/news/by-date/", response_model=List[NewsResponse])
def fetch_news_by_date(request: DateRangeRequest):
    """
    **Возвращает все новости за указанный период.**
    
    **Параметры:**
    - `start_date` (str): Начальная дата в формате YYYY-MM-DD
    - `end_date` (str): Конечная дата в формате YYYY-MM-DD
    
    **Пример запроса:**
    ```json
    {
        "start_date": "2025-05-03",
        "end_date": "2025-05-10"
    }
    ```
    """
    return get_news_by_date(request.start_date, request.end_date)

@router.post("/news/statistics/")
def get_news_statistics(request: DateRangeRequest):
    """
    **Возвращает статистику по всем темам за указанный период.**
    
    **Параметры:**
    - `start_date` (str): Начальная дата в формате YYYY-MM-DD
    - `end_date` (str): Конечная дата в формате YYYY-MM-DD
    
    **Пример запроса:**
    ```json
    {
        "start_date": "2025-05-03",
        "end_date": "2025-05-10"
    }
    ```
    
    **Пример ответа:**
    ```json
    {
        "period": {
            "start_date": "2025-05-03",
            "end_date": "2025-05-10"
        },
        "total_articles": 100,
        "topics": [
            {
                "topic_id": 1,
                "topic_name": "РБК Недвижимость",
                "count": 25,
                "percentage": 25.0
            },
            {
                "topic_id": 2,
                "topic_name": "RIA Realty",
                "count": 15,
                "percentage": 15.0
            },
            {
                "topic_id": 3,
                "topic_name": "E1.RU Финансы",
                "count": 0,
                "percentage": 0.0
            },
            {
                "topic_id": 4,
                "topic_name": "E1.RU Строительство",
                "count": 30,
                "percentage": 30.0
            },
            {
                "topic_id": 5,
                "topic_name": "E1.RU Недвижимость",
                "count": 20,
                "percentage": 20.0
            },
            {
                "topic_id": 6,
                "topic_name": "E1.RU Общие новости",
                "count": 10,
                "percentage": 10.0
            }
        ]
    }
    ```
    """
    return get_topics_statistics(request.start_date, request.end_date)
