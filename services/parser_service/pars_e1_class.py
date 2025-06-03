import json
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import dateparser
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_date(date_string: str) -> str:
    #logger.info(f"Входная дата для нормализации: {date_string}")
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
        #logger.warning("Не найден блок с содержимым статьи.")
        return ""
    for figcaption in article_body.find_all('figcaption'):
        figcaption.decompose()
    paragraphs = article_body.find_all('p')
    content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
    return content


class E1RealtyRequestParser:
    def __init__(self,
                 parsing_mode: str = "custom_period",
                 start_date: str = "03.05.2025",
                 end_date: str = "10.05.2025",
                 total_pages: int = 2,
                 test_articles_count: int = 0):
        self.parsing_mode = parsing_mode
        self.start_date = start_date
        self.end_date = end_date
        self.total_pages = total_pages
        self.test_articles_count = test_articles_count
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def collect_articles(self) -> List[Dict]:
        if self.parsing_mode == "all_time":
            base_url = "https://www.e1.ru/text/realty/page-{}/"
        else:
            base_url = f"https://www.e1.ru/text/realty/?dateFrom={self.start_date}&dateTo={self.end_date}&page={{}}/"

        results = []
        seen_links = set()
        article_id = 1

        # Определяем режим обхода страниц
        if self.total_pages > 0:
            max_pages = self.total_pages
        elif self.total_pages == 0 and self.test_articles_count > 0:
            max_pages = float('inf')
        else:
            max_pages = 3

        page = 1
        while page <= max_pages:
            #logger.info(f"Обрабатывается страница {page} из {max_pages if max_pages != float('inf') else '?'}")

            try:
                response = requests.get(base_url.format(page), headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                news_blocks = soup.find_all('div', class_='wrap_RL97A')
                if not news_blocks:
                    #logger.warning(f"Не найдено ни одного новостного блока на странице {page}. Прекращаем парсинг.")
                    break

                #logger.info(f"Найдено новостных блоков: {len(news_blocks)}")

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

                        if full_link in seen_links:
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
                            'topic': 'Недвижимость'
                        })

                        article_id += 1

                        if self.test_articles_count > 0 and len(results) >= self.test_articles_count:
                            return results

                    except Exception as e:
                        logger.error(f"Ошибка при обработке новости: {e}")
                        continue

                if len(results) == article_id - 1:
                    logger.warning(f"Новых статей на странице {page} не найдено. Завершаем парсинг.")
                    break

                page += 1

            except Exception as e:
                logger.error(f"Ошибка при обработке страницы {page}: {e}")
                break

        return results

    def fill_articles_content(self, articles: List[Dict]) -> List[Dict]:
        if self.test_articles_count > 0:
            articles = articles[:self.test_articles_count]

        total_articles = len(articles)
        #logger.info(f"\nЗагружено {total_articles} статей для обработки контента")

        for index, article in enumerate(articles, 1):
            #logger.info(f"\nОбработка статьи {index} из {total_articles}: {article['title']}")
            #logger.info(f"URL: {article['link']}")

            try:
                response = requests.get(article['link'], headers=self.headers)
                response.encoding = 'utf-8'
                response.raise_for_status()
                article['content'] = parse_article_content(response.text)
                #logger.info(f"✅ Получен контент длиной {len(article['content'])} символов")
                #logger.info("Первые 200 символов контента:")
                #logger.info(article['content'][:200] + "...")
            except Exception as e:
                #logger.error(f"⚠️ Ошибка при обработке статьи: {e}")
                article['content'] = ""

        return articles

    def parse(self) -> List[Dict]:
        articles = self.collect_articles()
        articles = self.fill_articles_content(articles)
        return articles


if __name__ == "__main__":
    # =====================
    # Инструкция по параметрам:
    # parsing_mode — режим парсинга:
    #     "all_time" — парсить все страницы (игнорирует даты)
    #     "custom_period" — парсить только за указанный период (start_date, end_date)
    # start_date, end_date — даты в формате ДД.ММ.ГГГГ (используются только при custom_period)
    # total_pages — сколько страниц парсить:
    #     > 0 — парсить ровно столько страниц
    #     = 0 и test_articles_count > 0 — парсить до тех пор, пока не наберётся нужное число статей (или не закончатся новости)
    #     = 0 и test_articles_count = 0 — парсить только 3 страницы (защита от бесконечного цикла)
    # test_articles_count — сколько статей собрать (0 — без ограничения, иначе ограничение по количеству)
    # =====================
    parser = E1RealtyRequestParser(
        parsing_mode="custom_period",
        start_date="03.05.2025",
        end_date="10.05.2025",
        total_pages=0,
        test_articles_count=20
    )
    result = parser.parse()
    with open("all_news_data_full2.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("\n✅ Обработка завершена. Результаты сохранены в all_news_data_full.json") 