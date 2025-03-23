from fastapi import APIRouter, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler

from db.database import get_db_connection
from services.parser_service.theme1_parser import Theme1NewsParser
from services.parser_service.theme2_parser import Theme2NewsParser
from services.parser_service.theme3_parser import Theme3NewsParser
from services.parser_service.theme4_parser import Theme4NewsParser

router = APIRouter()
scheduler = BackgroundScheduler()


# Функция парсинга всех тем сразу
def run_all_parsers(max_articles: int = 10):
    """Запускает парсинг всех тем по указанному количеству статей."""
    parsers = [
        Theme1NewsParser("https://realty.rbc.ru/industry/", topic_id=1),
        Theme2NewsParser("https://realty.ria.ru/tag_thematic_category_Zakonodatelstvo/", topic_id=2),
        Theme3NewsParser("https://www.e1.ru/text/theme/37211/", topic_id=3),
        Theme4NewsParser("https://www.e1.ru/text/tags/zastroyschik/", topic_id=4),
    ]

    for parser in parsers:
        try:
            parser.run(max_articles=max_articles)
            print(f"✅ Парсинг для topic_id={parser.topic_id} завершен. Собрано {max_articles} статей.")
        except Exception as e:
            print(f"❌ Ошибка при парсинге topic_id={parser.topic_id}: {str(e)}")

# Функция для установки таймера парсинга
def schedule_all_parsers(interval_hours: int, max_articles: int = 10):
    """
    Записывает расписание в БД и добавляет задачу в планировщик.

    :param interval_hours: Интервал времени в часах.
    :param max_articles: Количество статей для парсинга в каждой теме.
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO parser_schedule (topic_id, interval_hours, max_articles)
            VALUES (0, %s, %s)
            ON DUPLICATE KEY UPDATE interval_hours=%s, max_articles=%s
        """, (interval_hours, max_articles, interval_hours, max_articles))
    conn.commit()
    conn.close()

    # Удаляем старую задачу, если была
    if scheduler.get_job("all_parsers"):
        scheduler.remove_job("all_parsers")

    # Добавляем новую задачу в планировщик
    scheduler.add_job(run_all_parsers, 'interval', hours=interval_hours, args=[max_articles], id="all_parsers")
    print(f"⏳ Парсинг ВСЕХ тем теперь выполняется каждые {interval_hours} часов.")

# Эндпоинт для запуска парсинга всех тем и добавления в расписание
@router.post("/parse_all/")
def parse_all_news(interval_hours: int, max_articles: int = 10):
    """
    **Запускает парсинг всех тем и устанавливает таймер.**

    **Параметры:**
    - `interval_hours` (int): Интервал в часах (например, `6` для парсинга раз в 6 часов).
    - `max_articles` (int, по умолчанию 10): Количество новостей для каждой темы.

    **Пример запроса:**
    ```json
    {
        "interval_hours": 6,
        "max_articles": 10
    }
    ```
    **Ответ:**
    ```json
    {
        "message": "Парсинг ВСЕХ тем установлен на каждые 6 часов."
    }
    ```
    """
    try:
        schedule_all_parsers(interval_hours, max_articles)

        # Сразу запускаем парсер после добавления расписания
        run_all_parsers(max_articles)

        return {"message": f"Парсинг ВСЕХ тем запущен сразу и установлен на каждые {interval_hours} часов."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при установке таймера: {str(e)}")

# Эндпоинт для обновления расписания парсинга
@router.put("/update_schedule/")
def update_schedule(interval_hours: int, max_articles: int = 10):
    """
    **Обновляет интервал и количество статей в расписании.**

    **Параметры:**
    - `interval_hours` (int): Новый интервал в часах.
    - `max_articles` (int): Новое количество статей для каждой темы.

    **Пример запроса:**
    ```json
    {
        "interval_hours": 12,
        "max_articles": 15
    }
    ```
    **Ответ:**
    ```json
    {
        "message": "Интервал обновлен на 12 часов. Количество статей: 15."
    }
    ```
    """
    try:
        # Обновляем расписание парсинга
        schedule_all_parsers(interval_hours, max_articles)

        # Сразу запускаем парсинг всех тем после обновления расписания
        run_all_parsers(max_articles)
        return {"message": f"Интервал обновлен на {interval_hours} часов. Количество статей: {max_articles}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении расписания: {str(e)}")

# Эндпоинт для удаления задачи парсинга
@router.delete("/delete_schedule/")
def delete_schedule():
    """
    **Удаляет расписание парсинга всех тем.**

    **Пример запроса:**
    ```
    DELETE /delete_schedule/
    ```
    **Ответ:**
    ```json
    {
        "message": "Парсинг всех тем удален из расписания."
    }
    ```
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM parser_schedule WHERE topic_id = 0")
    conn.commit()
    conn.close()

    if scheduler.get_job("all_parsers"):
        scheduler.remove_job("all_parsers")

    return {"message": "Парсинг всех тем удален из расписания."}

# Функция загрузки расписания при запуске сервера
def load_scheduled_jobs():
    """
    Загружает сохраненные настройки таймера из БД и запускает планировщик.
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT interval_hours, max_articles FROM parser_schedule WHERE topic_id = 0")
        schedule = cursor.fetchone()
    conn.close()

    if schedule:
        # Преобразуем кортеж в словарь
        schedule_dict = {
            "interval_hours": schedule[0],
            "max_articles": schedule[1]
        }
        scheduler.add_job(run_all_parsers, 'interval', hours=schedule_dict["interval_hours"], args=[schedule_dict["max_articles"]], id="all_parsers")
        print(f"🔄 Загружена задача парсинга всех тем (каждые {schedule_dict['interval_hours']} часов, {schedule_dict['max_articles']} статей на тему).")


# Запуск планировщика при старте сервера
scheduler.start()
load_scheduled_jobs()
