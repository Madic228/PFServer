import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.INFO)

    # Создание обработчика для записи в файл
    handler = RotatingFileHandler("uvicorn.log", maxBytes=10**6, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Добавление обработчика
    logger.addHandler(handler)

    # Для логирования ошибок и предупреждений
    error_handler = logging.StreamHandler()
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
