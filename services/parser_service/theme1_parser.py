import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from db.database import get_db_connection

class Theme1NewsParser:
    def __init__(self, base_url, topic_id):
        self.base_url = base_url
        self.topic_id = topic_id
        self.source = "РБК Недвижимость"

    def fetch_page(self, url: str):
        """Загружает страницу и возвращает объект BeautifulSoup."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return None

    def parse_news(self, soup, max_articles=10):
        """Парсит список новостей, ограничиваясь max_articles."""
        articles = []
        items = soup.find_all('a', class_='item__link rm-cm-item-link js-rm-central-column-item-link')

        for item in items[:max_articles]:  # Ограничение по количеству статей
            try:
                title_tag = item.find('span', class_='item__title rm-cm-item-text js-rm-central-column-item-text')
                title = title_tag.get_text(strip=True) if title_tag else "Без заголовка"

                link = item['href'] if item.has_attr('href') else None
                if not link:
                    continue  # Пропускаем, если нет ссылки

                date_tag = item.find_next('span', class_='item__category')
                publication_date = self.normalize_date(date_tag.get_text(strip=True)) if date_tag else None

                # Парсим контент статьи
                content = self.parse_article_content(link)

                articles.append({
                    'topic_id': self.topic_id,
                    'title': title,
                    'link': link,
                    'publication_date': publication_date,
                    'content': content,
                    'summarized_text': "",
                    'source': self.source
                })
            except Exception as e:
                print(f"Ошибка при обработке новости: {e}")

        return articles

    def parse_article_content(self, url: str):
        """Парсит содержимое новости (только <p>)."""
        try:
            soup = self.fetch_page(url)
            if not soup:
                return None

            article_body = soup.find('div', class_='article__text article__text_free')
            if not article_body:
                return None

            paragraphs = [p.get_text(strip=True) for p in article_body.find_all('p')]
            return "\n".join(paragraphs) if paragraphs else None
        except requests.RequestException as e:
            print(f"Ошибка при загрузке статьи: {e}")
            return None

    def normalize_date(self, date_str):
        """Нормализует дату в формат datetime."""
        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5,
            "июня": 6, "июля": 7, "августа": 8, "сентября": 9, "октября": 10,
            "ноября": 11, "декабря": 12
        }

        try:
            if "Сегодня" in date_str:
                return datetime.now()

            elif "Вчера" in date_str:
                return datetime.now() - timedelta(days=1)

            date_parts = date_str.split(",")
            day_month = date_parts[0].strip().split(" ")

            day = int(day_month[0])
            month = months.get(day_month[1], 1)
            current_year = datetime.now().year

            time_str = date_parts[1].strip() if len(date_parts) > 1 else "00:00"
            date_str = f"{current_year}-{month:02d}-{day:02d} {time_str}"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print(f"Ошибка при разборе даты: {date_str}")
            return None

    def save_to_db(self, articles):
        """Записывает статьи в БД, избегая дубликатов и удаляя старые записи, если их более 20."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем, какие ссылки уже есть в базе
        existing_links_query = "SELECT link FROM articles WHERE topic_id = %s"
        cursor.execute(existing_links_query, (self.topic_id,))
        existing_links = {row[0] for row in cursor.fetchall()}  # Собираем существующие ссылки

        query = """
            INSERT INTO articles (topic_id, title, publication_date, link, content, summarized_text, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        new_articles = [article for article in articles if article["link"] not in existing_links]

        if new_articles:
            for article in new_articles:
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
            print(f"✅ {len(new_articles)} новых статей записано в БД!")

            # Удаляем старые статьи, если их больше 20
            self.cleanup_old_articles(cursor)

        cursor.close()
        conn.close()

    def cleanup_old_articles(self, cursor):
        """Удаляет старые записи, если в БД больше 20 статей по данной теме."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Узнаем количество статей по данной теме
        count_query = "SELECT COUNT(*) FROM articles WHERE topic_id = %s"
        cursor.execute(count_query, (self.topic_id,))
        count = cursor.fetchone()[0]

        if count > 20:
            # Удаляем старые статьи, оставляя только 20 самых свежих
            delete_query = """
                   DELETE FROM articles 
                   WHERE topic_id = %s 
                   AND id IN (
                       SELECT id FROM (
                           SELECT id FROM articles 
                           WHERE topic_id = %s 
                           ORDER BY publication_date ASC 
                           LIMIT %s
                       ) AS subquery
                   )
               """
            articles_to_delete = count - 20  # Сколько лишних статей нужно удалить
            cursor.execute(delete_query, (self.topic_id, self.topic_id, articles_to_delete))
            conn.commit()

        cursor.close()
        conn.close()

    def run(self, max_articles=10):
        """Запускает парсер."""
        soup = self.fetch_page(self.base_url)
        if soup:
            articles = self.parse_news(soup, max_articles=max_articles)
            if articles:
                self.save_to_db(articles)

if __name__ == "__main__":
    parser = Theme1NewsParser("https://realty.rbc.ru/industry/", topic_id=1)
    parser.run(max_articles=10)  # Укажите желаемое количество статей
