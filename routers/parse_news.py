# routers/parse_news.py
from fastapi import APIRouter, HTTPException
from services.parser_service.theme1_parser import Theme1NewsParser
from services.parser_service.theme2_parser import Theme2NewsParser
from services.parser_service.theme3_parser import Theme3NewsParser
from services.parser_service.theme4_parser import Theme4NewsParser

router = APIRouter()

@router.post("/parse/{topic_id}")
def parse_news(topic_id: int, max_articles: int = 10):
    """Запускает парсер для указанного topic_id."""
    try:
        if topic_id == 1:
            parser = Theme1NewsParser("https://realty.rbc.ru/industry/", topic_id=topic_id)
        elif topic_id == 2:
            parser = Theme2NewsParser("https://realty.ria.ru/tag_thematic_category_Zakonodatelstvo/", topic_id=topic_id)
        elif topic_id == 3:
            parser = Theme3NewsParser("https://www.e1.ru/text/theme/37211/", topic_id=topic_id)
        elif topic_id == 4:
            parser = Theme4NewsParser("https://www.e1.ru/text/tags/zastroyschik/", topic_id=topic_id)
        else:
            raise HTTPException(status_code=400, detail="Некорректный topic_id")

        parser.run(max_articles=max_articles)
        return {"message": f"Парсинг для topic_id={topic_id} завершен. Собрано {max_articles} статей."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге: {str(e)}")