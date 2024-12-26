from fastapi import FastAPI
from routers import fill_news
import uvicorn

app = FastAPI()

app.include_router(fill_news.router, prefix="/api/fill_news", tags=["Fill News"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
