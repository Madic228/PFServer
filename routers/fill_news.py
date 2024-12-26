# Файл fill_news.py
from fastapi import APIRouter, HTTPException
from services.parser_service import scroll_and_collect
from db.database import get_db_connection
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/")
async def fill_news_database(theme: str, max_articles: int):
    """
    Заполняет таблицу `parsed_news` новостями по указанной теме.
    Принимает:
    - theme: Название темы
    - max_articles: Максимальное количество новостей для парсинга
    """

    logger.info(f"Запрос на парсинг. Тема: {theme}, Количество статей: {max_articles}")

    # Проверяем тему и выполняем соответствующий парсинг
    if theme == "Новости рынка недвижимости":
        logger.info("Начало парсинга новостей рынка недвижимости...")
        news = scroll_and_collect("https://realty.rbc.ru/industry/", max_articles)
    elif theme == "Изменения в законодательстве":
        logger.warning(f"Заглушка для темы: {theme}")
        # Заглушка: логика для парсинга этой темы будет добавлена в будущем
        news = [{"title": "Заглушка: статья по изменениям в законодательстве",
                 "date": "2024-01-01",
                 "link": "https://example.com",
                 "content": "Тестовый контент для темы изменений в законодательстве"}]
    elif theme == "Финансы":
        logger.warning(f"Заглушка для темы: {theme}")
        # Заглушка: логика для парсинга этой темы будет добавлена в будущем
        news = [{"title": "Заглушка: статья по теме финансы",
                 "date": "2024-01-01",
                 "link": "https://example.com",
                 "content": "Тестовый контент для темы финансы"}]
    elif theme == "Строительные проекты и застройщики":
        logger.warning(f"Заглушка для темы: {theme}")
        # Заглушка: логика для парсинга этой темы будет добавлена в будущем
        news = [{"title": "Заглушка: статья по теме строительные проекты",
                 "date": "2024-01-01",
                 "link": "https://example.com",
                 "content": "Тестовый контент для темы строительные проекты"}]
    elif theme == "Общие тенденции рынка":
        logger.warning(f"Заглушка для темы: {theme}")
        # Заглушка: логика для парсинга этой темы будет добавлена в будущем
        news = [{"title": "Заглушка: статья по общей тенденции рынка",
                 "date": "2024-01-01",
                 "link": "https://example.com",
                 "content": "Тестовый контент для темы общие тенденции рынка"}]
    elif theme == "Ремонт и DIY":
        logger.warning(f"Заглушка для темы: {theme}")
        # Заглушка: логика для парсинга этой темы будет добавлена в будущем
        news = [{"title": "Заглушка: статья по теме ремонт и DIY",
                 "date": "2024-01-01",
                 "link": "https://example.com",
                 "content": "Тестовый контент для темы ремонт и DIY"}]
    elif theme == "Дизайн":
        logger.warning(f"Заглушка для темы: {theme}")
        # Заглушка: логика для парсинга этой темы будет добавлена в будущем
        news = [{"title": "Заглушка: статья по теме дизайн",
                 "date": "2024-01-01",
                 "link": "https://example.com",
                 "content": "Тестовый контент для темы дизайн"}]
    else:
        logger.error(f"Тема '{theme}' не поддерживается.")
        raise HTTPException(status_code=400, detail=f"Тема '{theme}' не поддерживается.")

    if not news:
        logger.error(f"Ошибка при парсинге: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить новости.")

    # Сохраняем новости в базу данных
    try:
        logger.info(f"Сохранение {len(news)} статей в базу данных...")
        connection = get_db_connection()
        cursor = connection.cursor()
        for article in news:
            cursor.execute(
                """
                INSERT INTO parsed_news (topic_id, title, publication_date, link, content)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (1, article["title"], article["date"], article["link"], article["content"])
            )
        connection.commit()
        cursor.close()
        connection.close()
        logger.info(f"{len(news)} статей успешно сохранено.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в базу данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении в базу данных: {str(e)}")

    return {"message": f"{len(news)} новостей успешно добавлено в базу данных."}
