from fastapi import FastAPI
from routers import fill_news, auth, parse_news, summarize_news
import uvicorn

app = FastAPI()

app.include_router(fill_news.router, prefix="/api/fill_news", tags=["Fill News"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(parse_news.router, prefix="/api/parse", tags=["Parse News"])
#app.include_router(summarize_news.router, prefix="/api/summarize", tags=["Summarize News"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
