import requests
from bs4 import BeautifulSoup
from datetime import datetime
from db.database import get_db_connection

from datetime import datetime

class Theme4NewsParser:
    def __init__(self, base_url, topic_id):
        self.base_url = base_url
        self.topic_id = topic_id

    def fetch_page(self, url: str):
        """Загружает содержимое веб-страницы."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return None

    def parse_construction_articles(self, html: str, max_articles):
        """Парсит список новостей из темы 'Строительные проекты и застройщики'."""
        soup = BeautifulSoup(html, 'html.parser')
        news_list = []

        # Находим контейнер с новостями
        news_container = soup.find('div', class_='announcementList_zwnJ9')
        if not news_container:
            print("Не найден контейнер с новостями.")
            return news_list

        # Ищем новости внутри контейнера
        news_items = news_container.find_all('div', class_='wrap_fgrum')
        for item in news_items[:max_articles]:  # Ограничение на количество статей
            try:
                # Заголовок и ссылка
                title_tag = item.find('a', class_='header_fgrum')
                title = title_tag.text.strip()
                link = title_tag['href']

                # Дата публикации
                date_tag = item.find('span', class_='text_0UNFI')
                if date_tag:
                    date_str = date_tag.text.strip()
                    # Преобразуем строку даты в объект datetime
                    publication_date = self.normalize_date(date_str)
                else:
                    publication_date = None

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

    def normalize_date(self, date_str: str):
        """Преобразует строку даты в формат datetime."""
        try:
            # Пример строки: "20 февраля, 2025, 08:40"
            months = {
                "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
                "мая": "05", "июня": "06", "июля": "07", "августа": "08",
                "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12"
            }

            # Разделяем строку на части
            parts = date_str.split()
            day = parts[0]
            month = months.get(parts[1].rstrip(','))
            year = parts[2].rstrip(',')
            time = parts[3]

            # Формируем строку в формате, который понимает datetime
            normalized_date_str = f"{year}-{month}-{day} {time}"
            return datetime.strptime(normalized_date_str, "%Y-%m-%d %H:%M")
        except Exception as e:
            print(f"Ошибка при нормализации даты: {e}")
            return None

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

    def run(self, max_articles=10):
        """Запускает парсер для получения и сохранения новостей с содержимым."""
        html = self.fetch_page(self.base_url)
        if html:
            articles = self.parse_finance_articles(html, max_articles)
            if articles:
                self.update_content_from_links(articles)
                self.save_to_db(articles)

if __name__ == "__main__":
    # URL темы 'Строительные проекты и застройщики'
    base_url = "https://www.e1.ru/text/tags/zastroyschik/"
    parser = Theme4NewsParser(base_url, topic_id=4)
    parser.run(max_articles=10)