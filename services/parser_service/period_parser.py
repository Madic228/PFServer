import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from typing import List, Dict
import dateparser
import re
from db.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_date(date_string: str) -> str:
    if not date_string:
        return datetime.now().strftime("%Y-%m-%d")
    if re.match(r'^\d{1,2}:\d{2}$', date_string.strip()):
        return datetime.now().strftime("%Y-%m-%d")
    if not re.search(r'\d{4}', date_string):
        current_year = datetime.now().year
        date_without_time = date_string.split(',')[0].strip()
        date_string = f"{date_without_time} {current_year}"
    parsed_date = dateparser.parse(
        date_string,
        languages=['ru'],
        settings={
            'DATE_ORDER': 'DMY',
            'PREFER_DATES_FROM': 'current_period'
        }
    )
    if parsed_date:
        result = parsed_date.strftime("%Y-%m-%d")
        return result
    return datetime.now().strftime("%Y-%m-%d")

def parse_article_content(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    article_body = soup.find('div', id='articleBody', class_='articleContent_0DdLJ')
    if not article_body:
        return ""
    for figcaption in article_body.find_all('figcaption'):
        figcaption.decompose()
    paragraphs = article_body.find_all('p')
    content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    return content

class PeriodNewsParser:
    def __init__(self,
                 period_days: int = 7,
                 check_previous_days: int = 2):
        self.period_days = period_days
        self.check_previous_days = check_previous_days
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def get_date_range(self):
        """Вычисляет диапазон дат для парсинга."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.period_days)
        return start_date.strftime("%d.%m.%Y"), end_date.strftime("%d.%m.%Y")

    def get_existing_links(self) -> set:
        """Получает список существующих ссылок из БД."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT link FROM articles")
            return {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()

    def collect_articles(self) -> List[Dict]:
        start_date, end_date = self.get_date_range()
        base_url = f"https://www.e1.ru/text/realty/?dateFrom={start_date}&dateTo={end_date}&page={{}}/"

        results = []
        seen_links = set()
        article_id = 1
        existing_links = self.get_existing_links()

        page = 1
        while True:
            try:
                response = requests.get(base_url.format(page), headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                news_blocks = soup.find_all('div', class_='wrap_RL97A')
                if not news_blocks:
                    break

                for block in news_blocks:
                    try:
                        content_div = block.find('div', class_='content_RL97A')
                        if not content_div:
                            continue

                        a_tag = content_div.find('a')
                        if not a_tag:
                            continue

                        title = a_tag.get('title', '').strip()
                        link = a_tag.get('href', '').strip()
                        full_link = link if link.startswith('http') else f'https://www.e1.ru{link}'

                        # Пропускаем если ссылка уже существует в БД или в текущей сессии
                        if full_link in existing_links or full_link in seen_links:
                            continue

                        seen_links.add(full_link)

                        date_wrap = block.find('div', class_='wrap_eiDCU dark_eiDCU statistic_RL97A')
                        date_span = date_wrap.find('span', class_='text_eiDCU') if date_wrap else None
                        date_raw = date_span.text.strip() if date_span else ''
                        date_formatted = normalize_date(date_raw)

                        results.append({
                            'id': article_id,
                            'title': title,
                            'date': date_formatted,
                            'link': full_link,
                            'content': '',
                            'source': 'E1.RU'
                        })

                        article_id += 1

                    except Exception as e:
                        logger.error(f"Ошибка при обработке новости: {e}")
                        continue

                if len(results) == article_id - 1:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Ошибка при обработке страницы {page}: {e}")
                break

        return results

    def fill_articles_content(self, articles: List[Dict]) -> List[Dict]:
        total_articles = len(articles)

        for index, article in enumerate(articles, 1):
            try:
                response = requests.get(article['link'], headers=self.headers)
                response.encoding = 'utf-8'
                response.raise_for_status()
                article['content'] = parse_article_content(response.text)
            except Exception as e:
                logger.error(f"Ошибка при обработке статьи: {e}")
                article['content'] = ""

        return articles

    def save_to_db(self, articles: List[Dict]) -> None:
        """Сохраняет статьи в базу данных."""
        if not articles:
            logger.warning("Нет статей для сохранения в БД")
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Проверяем существующие ссылки
            cursor.execute("SELECT link FROM articles")
            existing_links = {row[0] for row in cursor.fetchall()}

            # Подготавливаем запрос для вставки
            insert_query = """
                INSERT INTO articles (title, publication_date, link, content, source)
                VALUES (%s, %s, %s, %s, %s)
            """

            new_articles = 0
            for article in articles:
                if article['link'] not in existing_links:
                    cursor.execute(insert_query, (
                        article['title'],
                        article['date'],
                        article['link'],
                        article['content'],
                        article['source']
                    ))
                    new_articles += 1

            conn.commit()
            logger.info(f"✅ {new_articles} новых статей сохранено в БД")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка при сохранении в БД: {e}")
        finally:
            cursor.close()
            conn.close()

    def parse(self) -> List[Dict]:
        articles = self.collect_articles()
        articles = self.fill_articles_content(articles)
        self.save_to_db(articles)
        return articles

if __name__ == "__main__":
    parser = PeriodNewsParser(
        period_days=7,
        check_previous_days=2
    )
    result = parser.parse()
    print(f"\n✅ Обработка завершена. Собрано {len(result)} статей.") 