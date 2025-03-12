# routers/summarize_news.py
from fastapi import APIRouter, HTTPException
from services.summarizer_service import SummarizerDB

router = APIRouter()

@router.post("/summarize/{topic_id}")
def summarize_news(topic_id: int):
    """Запускает суммаризацию для указанного topic_id."""
    try:
        summarizer = SummarizerDB(topic_id=topic_id)
        summarizer.run()
        return {"message": f"Суммаризация для topic_id={topic_id} завершена."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при суммаризации: {str(e)}")