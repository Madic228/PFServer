from typing import List
from db.database import get_db_connection
from models.news import NewsResponse
from fastapi import HTTPException

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
