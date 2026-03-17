from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.db import engine

app = FastAPI(title="Argentourse API")

@app.get("/")
def read_root():
    return {"status": "ok"}


@app.get("/health/db")
def db_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": "ok", "result": result.scalar()}
    
app.include_router(api_router, prefix="/api/v1")