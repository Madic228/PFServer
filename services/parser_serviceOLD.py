import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from db.database import get_db_connection

class BaseNewsParser:
    def __init__(self, base_url, topic_id):
        self.base_url = base_url
        self.topic_id = topic_id

    def fetch_page(self, url: str):
        """Загружает страницу и возвращает объект BeautifulSoup."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы: {e}")
            return None

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

    def run(self, max_articles=10):
        """Запускает парсер."""
        soup = self.fetch_page(self.base_url)
        if soup:
            articles = self.parse_news(soup, max_articles=max_articles)
            if articles:
                self.save_to_db(articles)

class Theme1NewsParser(BaseNewsParser):
    def __init__(self, base_url, topic_id):
        super().__init__(base_url, topic_id)
        self.source = "РБК Недвижимость"

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
                    'summarized_text': None,
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
        """Запускает парсер для получения и сохранения новостей."""
        html = self.fetch_page(self.base_url)
        if html:
            articles = self.parse_news(html, max_articles)
            if articles:
                self.save_to_db(articles)

