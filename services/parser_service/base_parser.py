import requests
from bs4 import BeautifulSoup
from test.myPars2.database.database import get_db_connection


class BaseNewsParser:
    def __init__(self, base_url, topic_id):
        self.base_url = base_url
        self.topic_id = topic_id

    def fetch_page(self, url: str):
        """Загружает содержимое веб-страницы."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return None

    def save_to_db(self, articles):
        """Записывает статьи в БД"""
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO articles (topic_id, title, publication_date, link, content, summarized_text, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for article in articles:
            cursor.execute(query, (
                article["topic_id"],
                article["title"],
                article["publication_date"],
                article["link"],
                article["content"],
                article["summarized_text"],
                article["source"]
            ))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ {len(articles)} статей записано в БД!")

    def parse_news(self, html: str):
        """Парсит новости из HTML содержимого. Метод должен быть переопределён в дочернем классе."""
        raise NotImplementedError

    def run(self, max_articles=10):
        """Запускает парсер для получения и сохранения новостей."""
        html = self.fetch_page(self.base_url)
        if html:
            articles = self.parse_news(html)
            if articles:
                self.save_to_db(articles)
