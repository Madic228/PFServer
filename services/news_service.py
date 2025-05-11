from typing import List, Dict
from db.database import get_db_connection
from models.news import NewsResponse
from fastapi import HTTPException
from datetime import datetime

def get_news_by_topic(topic_id: int, limit: int) -> List[NewsResponse]:
    """Получает новости из базы данных по topic_id и ограничению количества."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT topic_id, title, publication_date, link, summarized_text, source
            FROM articles
            WHERE topic_id = %s
            ORDER BY publication_date DESC
            LIMIT %s
        """
        cursor.execute(query, (topic_id, limit))
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Новости не найдены для указанной тематики.")

        return [NewsResponse(**row) for row in rows]
    finally:
        cursor.close()
        connection.close()

def get_news_by_date(start_date: str, end_date: str) -> List[NewsResponse]:
    """
    Получает все новости за указанный период.
    
    Args:
        start_date (str): Начальная дата в формате YYYY-MM-DD
        end_date (str): Конечная дата в формате YYYY-MM-DD
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT topic_id, title, publication_date, link, summarized_text, source
            FROM articles
            WHERE DATE(publication_date) BETWEEN %s AND %s
            ORDER BY publication_date DESC
        """
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404, 
                detail=f"Новости не найдены за период с {start_date} по {end_date}"
            )

        return [NewsResponse(**row) for row in rows]
    finally:
        cursor.close()
        connection.close()

def get_topics_statistics(start_date: str, end_date: str) -> Dict:
    """
    Получает статистику по всем темам за указанный период.
    
    Args:
        start_date (str): Начальная дата в формате YYYY-MM-DD
        end_date (str): Конечная дата в формате YYYY-MM-DD
        
    Returns:
        Dict: Статистика в формате:
        {
            "period": {
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD"
            },
            "total_articles": 100,
            "topics": [
                {
                    "topic_id": 1,
                    "topic_name": "Название темы",
                    "count": 25,
                    "percentage": 25.0
                },
                ...
            ]
        }
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Получаем общее количество статей
        total_query = """
            SELECT COUNT(*) as total
            FROM articles
            WHERE DATE(publication_date) BETWEEN %s AND %s
        """
        cursor.execute(total_query, (start_date, end_date))
        total = cursor.fetchone()['total']

        # Получаем статистику по темам с названиями из таблицы topics
        topics_query = """
            SELECT 
                t.id as topic_id,
                t.name as topic_name,
                COUNT(a.id) as count
            FROM topics t
            LEFT JOIN articles a ON t.id = a.topic_id 
                AND DATE(a.publication_date) BETWEEN %s AND %s
            GROUP BY t.id, t.name
            ORDER BY t.id
        """
        cursor.execute(topics_query, (start_date, end_date))
        topics_data = cursor.fetchall()

        # Формируем результат для всех тем
        topics = []
        for row in topics_data:
            count = row['count']
            percentage = round((count / total) * 100, 2) if total > 0 else 0.0
            
            topics.append({
                "topic_id": row['topic_id'],
                "topic_name": row['topic_name'],
                "count": count,
                "percentage": percentage
            })

        # Формируем итоговый результат
        result = {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "total_articles": total,
            "topics": topics
        }

        return result
    finally:
        cursor.close()
        connection.close()
