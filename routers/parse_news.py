from fastapi import APIRouter, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from db.database import get_db_connection
from services.parser_service.period_parser import PeriodNewsParser
from services.parser_service.pars_e1_class import E1RealtyRequestParser

router = APIRouter()
scheduler = BackgroundScheduler()

# Функция парсинга за период
def run_period_parser(period_days: int = 7, check_previous_days: int = 2):
    """Запускает парсинг за указанный период."""
    parser = PeriodNewsParser(
        period_days=period_days,
        check_previous_days=check_previous_days
    )
    
    try:
        articles = parser.parse()
        print(f"✅ Парсинг завершен. Собрано {len(articles)} новых статей.")
        return articles
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {str(e)}")
        return []

# Функция для установки таймера парсинга
def schedule_period_parser(interval_hours: int, period_days: int = 7, check_previous_days: int = 2):
    """
    Записывает расписание в БД и добавляет задачу в планировщик.

    :param interval_hours: Интервал времени в часах.
    :param period_days: Количество дней для парсинга от текущей даты.
    :param check_previous_days: Количество предыдущих дней для проверки.
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO parser_schedule (topic_id, interval_hours, period_days, check_previous_days)
            VALUES (0, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                interval_hours=%s, 
                period_days=%s, 
                check_previous_days=%s
        """, (interval_hours, period_days, check_previous_days,
              interval_hours, period_days, check_previous_days))
    conn.commit()
    conn.close()

    # Удаляем старую задачу, если была
    if scheduler.get_job("period_parser"):
        scheduler.remove_job("period_parser")

    # Добавляем новую задачу в планировщик
    scheduler.add_job(
        run_period_parser, 
        'interval', 
        hours=interval_hours, 
        args=[period_days, check_previous_days], 
        id="period_parser"
    )
    print(f"⏳ Парсинг установлен на каждые {interval_hours} часов.")

# Эндпоинт для запуска парсинга за период и добавления в расписание
@router.post("/parse_period/")
def parse_period_news(interval_hours: int, period_days: int = 7, check_previous_days: int = 2):
    """
    **Запускает парсинг за указанный период и устанавливает таймер.**

    **Параметры:**
    - `interval_hours` (int): Интервал в часах (например, `6` для парсинга раз в 6 часов).
    - `period_days` (int, по умолчанию 7): Количество дней для парсинга от текущей даты.
    - `check_previous_days` (int, по умолчанию 2): Количество предыдущих дней для проверки.

    **Пример запроса:**
    ```json
    {
        "interval_hours": 6,
        "period_days": 7,
        "check_previous_days": 2
    }
    ```
    **Ответ:**
    ```json
    {
        "message": "Парсинг установлен на каждые 6 часов."
    }
    ```
    """
    try:
        schedule_period_parser(interval_hours, period_days, check_previous_days)

        # Сразу запускаем парсер после добавления расписания
        run_period_parser(period_days, check_previous_days)

        return {"message": f"Парсинг запущен сразу и установлен на каждые {interval_hours} часов."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при установке таймера: {str(e)}")

# Эндпоинт для обновления расписания парсинга
@router.put("/update_schedule/")
def update_schedule(interval_hours: int, period_days: int = 7, check_previous_days: int = 2):
    """
    **Обновляет интервал и параметры в расписании.**

    **Параметры:**
    - `interval_hours` (int): Новый интервал в часах.
    - `period_days` (int, по умолчанию 7): Количество дней для парсинга от текущей даты.
    - `check_previous_days` (int, по умолчанию 2): Количество предыдущих дней для проверки.

    **Пример запроса:**
    ```json
    {
        "interval_hours": 12,
        "period_days": 7,
        "check_previous_days": 2
    }
    ```
    **Ответ:**
    ```json
    {
        "message": "Интервал обновлен на 12 часов. Период парсинга: 7 дней."
    }
    ```
    """
    try:
        # Обновляем расписание парсинга
        schedule_period_parser(interval_hours, period_days, check_previous_days)

        # Сразу запускаем парсинг после обновления расписания
        run_period_parser(period_days, check_previous_days)
        return {"message": f"Интервал обновлен на {interval_hours} часов. Период парсинга: {period_days} дней."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении расписания: {str(e)}")

# Эндпоинт для удаления задачи парсинга
@router.delete("/delete_schedule/")
def delete_schedule():
    """
    **Удаляет расписание парсинга.**

    **Пример запроса:**
    ```
    DELETE /delete_schedule/
    ```
    **Ответ:**
    ```json
    {
        "message": "Парсинг удален из расписания."
    }
    ```
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM parser_schedule WHERE topic_id = 0")
    conn.commit()
    conn.close()

    if scheduler.get_job("period_parser"):
        scheduler.remove_job("period_parser")

    return {"message": "Парсинг удален из расписания."}

# Функция загрузки расписания при запуске сервера
def load_scheduled_jobs():
    """
    Загружает сохраненные настройки таймера из БД и запускает планировщик.
    """
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT interval_hours, period_days, check_previous_days FROM parser_schedule WHERE topic_id = 0")
        schedule = cursor.fetchone()
    conn.close()

    if schedule:
        # Преобразуем кортеж в словарь
        schedule_dict = {
            "interval_hours": schedule[0],
            "period_days": schedule[1],
            "check_previous_days": schedule[2]
        }
        scheduler.add_job(
            run_period_parser, 
            'interval', 
            hours=schedule_dict["interval_hours"], 
            args=[schedule_dict["period_days"], schedule_dict["check_previous_days"]], 
            id="period_parser"
        )
        print(f"🔄 Загружена задача парсинга (каждые {schedule_dict['interval_hours']} часов, {schedule_dict['period_days']} дней).")

# Эндпоинт для разового парсинга без добавления в расписание
@router.post("/parse_once/")
def parse_once(start_date: str, end_date: str):
    """
    **Выполняет разовый парсинг за указанный период без добавления в расписание.**

    **Параметры:**
    - `start_date` (str): Начальная дата в формате ДД.ММ.ГГГГ
    - `end_date` (str): Конечная дата в формате ДД.ММ.ГГГГ

    **Пример запроса:**
    ```json
    {
        "start_date": "03.05.2025",
        "end_date": "10.05.2025"
    }
    ```
    **Ответ:**
    ```json
    {
        "message": "Парсинг выполнен успешно. Собрано 15 статей.",
        "articles_count": 15
    }
    ```
    """
    try:
        # Преобразуем даты в формат datetime для вычисления периода
        start = datetime.strptime(start_date, "%d.%m.%Y")
        end = datetime.strptime(end_date, "%d.%m.%Y")

        # Вычисляем количество дней между датами
        period_days = (end - start).days + 1

        parser = PeriodNewsParser(
            period_days=period_days,
            check_previous_days=0  # Для разового парсинга не проверяем предыдущие дни
        )

        articles = parser.parse()
        return {
            "message": f"Парсинг выполнен успешно. Собрано {len(articles)} статей.",
            "articles_count": len(articles)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении парсинга: {str(e)}")

# Запуск планировщика при старте сервера
scheduler.start()
load_scheduled_jobs()
