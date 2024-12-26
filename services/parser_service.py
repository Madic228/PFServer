# ФАЙЛ parser_service.py
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_driver():
    """Создает и возвращает новый экземпляр WebDriver."""
    options = Options()
    options.add_argument('--headless')  # Запуск без интерфейса браузера
    options.add_argument('--no-sandbox')  # Отключить sandbox для работы под root
    logger.info("Инициализация WebDriver...")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_article_content(link):
    """Извлекает содержимое статьи по ссылке."""
    try:
        logger.info(f"Извлечение содержимого статьи: {link}")
        local_driver = create_driver()
        local_driver.get(link)
        time.sleep(2)

        # Находим контейнер с текстом статьи
        article_body = local_driver.find_element(By.CSS_SELECTOR, 'div.article__text.article__text_free')

        # Извлекаем текст всех параграфов
        paragraphs = article_body.find_elements(By.TAG_NAME, 'p')
        content = []

        for paragraph in paragraphs:
            text = paragraph.text.strip()
            if not any(phrase in text for phrase in ["Будьте в курсе", "Подкаст", "телеграм-канал"]):
                content.append(text)

        local_driver.quit()
        return "\n".join(content)
    except Exception as e:
        logger.error(f"Ошибка при извлечении содержимого статьи {link}: {e}")
        print(f"Ошибка при извлечении содержимого статьи {link}: {e}")
        return ""

def scroll_and_collect(url, max_articles):
    """Собирает статьи с прокруткой страницы, ограничивая количество статей."""
    logger.info(f"Парсинг URL: {url}, Лимит: {max_articles} статей")
    driver = create_driver()
    driver.get(url)
    time.sleep(2)

    articles = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(articles) < max_articles:
        # Прокрутка вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Обновляем контейнер после прокрутки
        try:
            container = driver.find_element(By.CLASS_NAME, 'js-load-container')
            items = container.find_elements(By.CLASS_NAME, 'item')
        except Exception as e:
            logger.error(f"Ошибка при обновлении контейнера: {e}")
            print(f"Ошибка при обновлении контейнера: {e}")
            break

        for item in items:
            if len(articles) >= max_articles:
                break
            try:
                title = item.find_element(By.CLASS_NAME, 'item__title').text
                date = item.find_element(By.CLASS_NAME, 'item__category').text
                link = item.find_element(By.CLASS_NAME, 'item__link').get_attribute('href')

                # Извлекаем содержимое статьи
                content = extract_article_content(link)

                # Добавляем статью
                articles.append({
                    'title': title,
                    'date': date,
                    'link': link,
                    'content': content,
                })
            except Exception as e:
                logger.error(f"Ошибка при обработке статьи: {e}")
                print(f"Ошибка при обработке статьи: {e}")

        # Проверяем, достигли ли конца страницы
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            logger.info("Достигнут конец страницы.")
            print("Достигнут конец страницы.")
            break
        last_height = new_height

    driver.quit()
    logger.info(f"Парсинг завершен. Собрано {len(articles)} статей.")
    return articles
