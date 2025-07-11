from fastapi import FastAPI
from routers import fill_news, auth, parse_news, summarize_news, generations
import uvicorn

import logging_config
logging_config.setup_logging()


app = FastAPI()

app.include_router(fill_news.router, prefix="/api/fill_news", tags=["Fill News"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(parse_news.router, prefix="/api/parse", tags=["Parse News"])
app.include_router(generations.router, prefix="/api/generations", tags=["Generations"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
