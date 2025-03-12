import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
from db.database import get_db_connection

class Theme3NewsParser:
    def __init__(self, base_url, topic_id, max_articles=10):
        self.base_url = base_url
        self.topic_id = topic_id
        self.max_articles = max_articles

    def fetch_page(self, url: str):
        """Загружает содержимое веб-страницы."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            # Установка правильной кодировки
            response.encoding = response.apparent_encoding
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return None

    def parse_finance_articles(self, html: str):
        """Парсит список новостей из темы 'Финансы'."""
        soup = BeautifulSoup(html, 'html.parser')
        news_list = []

        # Находим контейнер с новостями
        news_container = soup.find('div', class_='hkxta', attrs={'page-type': 'theme'})
        if not news_container:
            print("Не найден контейнер с новостями.")
            return news_list

        # Ищем новости внутри контейнера
        news_items = news_container.find_all('a', attrs={'data-test': 'archive-record-header'})
        for item in news_items[:self.max_articles]:  # Ограничение на количество статей
            try:
                title = item.text.strip()
                link = "https://www.e1.ru" + item['href']  # Полная ссылка

                # Извлекаем дату публикации
                date_container = item.find_next('div', class_='Hiu4B vx3Rq')  # Находим блок с датой
                if date_container:
                    time_tag = date_container.find('time')
                    if time_tag:
                        publication_date_str = time_tag['datetime']  # Получаем строку datetime
                        publication_date = datetime.fromisoformat(publication_date_str)  # Преобразуем в datetime
                    else:
                        publication_date = "Дата отсутствует"
                else:
                    publication_date = "Дата отсутствует"

                news_list.append({
                    "topic_id": self.topic_id,
                    "title": title,
                    "publication_date": publication_date,
                    "link": link,
                    "content": "",
                    "summarized_text": "",
                    "source": "E1.RU"
                })
            except Exception as e:
                print(f"Ошибка при обработке новости: {e}")

        return news_list

    def parse_article_content(self, html: str):
        """Извлекает содержимое статьи из блока <div id='articleBody'>."""
        soup = BeautifulSoup(html, 'html.parser')
        article_body = soup.find('div', id='articleBody', class_='articleContent_fefJj')
        if not article_body:
            print("Не найден блок с содержимым статьи.")
            return ""

        paragraphs = article_body.find_all('p')
        content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        return content

    def update_content_from_links(self, articles):
        """Обновляет поле 'content' у новостей, парся статьи по ссылкам."""
        for article in articles:
            if "link" in article and article["link"]:
                print(f"Парсинг статьи: {article['title']}")
                html = self.fetch_page(article["link"])
                if html:
                    content = self.parse_article_content(html)
                    article["content"] = content if content else "Текст отсутствует"
                else:
                    article["content"] = "Ошибка загрузки страницы"

    def save_to_db(self, articles):
        """Записывает статьи в БД."""
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
                article["publication_date"],  # Здесь уже datetime объект
                article["link"],
                article["content"],
                article["summarized_text"],
                article["source"]
            ))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ {len(articles)} статей записано в БД!")

    def run(self):
        """Запускает парсер для получения и сохранения новостей с содержимым."""
        html = self.fetch_page(self.base_url)
        if html:
            articles = self.parse_finance_articles(html)
            if articles:
                self.update_content_from_links(articles)
                self.save_to_db(articles)

if __name__ == "__main__":
    # URL темы 'Финансы'
    base_url = "https://www.e1.ru/text/theme/37211/"
    parser = Theme3NewsParser(base_url, topic_id=3, max_articles=10)
    parser.run()
