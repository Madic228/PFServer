import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from db.database import get_db_connection


class Theme2NewsParser:
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

    def parse_news(self, html: str, max_articles):
        """Парсит новости из HTML содержимого и возвращает список новостей с контентом."""
        soup = BeautifulSoup(html, 'html.parser')
        news_list = []

        # Находим контейнер с новостями
        news_container = soup.find('div', class_='list list-tags', attrs={'data-view': 'tags'})
        if not news_container:
            print("Не найден контейнер с новостями.")
            return news_list

        # Парсим каждую новость
        news_items = news_container.find_all('div', class_='list-item', attrs={'data-type': 'article'})
        count = 0  # Счётчик обработанных новостей
        for item in news_items:
            if count >= max_articles:
                break  # Прерываем цикл, если достигли максимального количества статей
            try:
                title_tag = item.find('a', class_='list-item__title')
                title = title_tag.text.strip()
                link = title_tag['href']

                date_tag = item.find('div', class_='list-item__info-item', attrs={'data-type': 'date'})
                date_str = date_tag.text.strip() if date_tag else "Дата отсутствует"

                # Нормализуем дату
                date = self.normalize_date(date_str)

                # Сразу парсим содержимое новости
                article_content = self.parse_article_content(link)

                news_list.append({
                    'topic_id': self.topic_id,
                    'title': title,
                    'link': link,
                    'publication_date': date,
                    'content': article_content,
                    'summarized_text': "",  # Позже можно добавить суммаризацию
                    'source': 'RIA Realty'
                })
                count += 1
            except Exception as e:
                print(f"Ошибка при обработке новости: {e}")

        return news_list

    def parse_article_content(self, url: str):
        """Парсит содержимое новости из HTML."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            article_body = soup.find('div', class_='article__body')

            if not article_body:
                return "Текст статьи отсутствует"

            content = []
            for block in article_body.find_all('div', class_='article__block', attrs={'data-type': 'text'}):
                text_div = block.find('div', class_='article__text')
                if text_div:
                    content.append(text_div.text.strip())

            return "\n".join(content)

        except requests.RequestException as e:
            print(f"Ошибка при загрузке статьи: {e}")
            return "Ошибка при загрузке статьи"

    def normalize_date(self, date_str):
        """Нормализует строку с датой в формат datetime, учитывая 'Сегодня' и 'Вчера'."""

        months = {
            "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5,
            "июня": 6, "июля": 7, "августа": 8, "сентября": 9, "октября": 10,
            "ноября": 11, "декабря": 12
        }

        try:
            # Проверяем на "Сегодня"
            if "Сегодня" in date_str:
                return datetime.now()

            # Проверяем на "Вчера"
            elif "Вчера" in date_str:
                return datetime.now() - timedelta(days=1)

            # Разделяем дату и время
            date_parts = date_str.split(",")
            date_part = date_parts[0].strip()

            # Извлекаем день и месяц
            day_month = date_part.split(" ")
            day = int(day_month[0])
            month_name = day_month[1]

            # Получаем текущий год
            current_year = datetime.now().year

            # Преобразуем месяц в число
            if month_name in months:
                month = months[month_name]
            else:
                print(f"Не удалось распознать месяц: {month_name}")
                return None

            # Преобразуем дату в datetime
            time_str = date_parts[1].strip() if len(date_parts) > 1 else "00:00"
            date_str = f"{current_year}-{month:02d}-{day:02d} {time_str}"
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

            return date
        except ValueError:
            print(f"Не удалось нормализовать дату: {date_str}")
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
        """Удаляет самые старые статьи, если их больше 20."""
        delete_query = """
            DELETE FROM articles 
            WHERE id IN (
                SELECT id FROM articles 
                WHERE topic_id = %s 
                ORDER BY publication_date ASC 
                LIMIT (SELECT COUNT(*) FROM articles WHERE topic_id = %s) - 20
            )
        """
        cursor.execute(delete_query, (self.topic_id, self.topic_id))
        print("♻️ Удалены старые новости, чтобы оставить ровно 20!")

    def run(self, max_articles=10):
        """Запускает парсер для получения и сохранения новостей."""
        html = self.fetch_page(self.base_url)
        if html:
            articles = self.parse_news(html, max_articles)
            if articles:
                self.save_to_db(articles)


if __name__ == "__main__":
    parser = Theme2NewsParser("https://realty.ria.ru/tag_thematic_category_Zakonodatelstvo/", topic_id=2)
    parser.run(max_articles=10)
