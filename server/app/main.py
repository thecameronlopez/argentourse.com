from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.db import engine

from app.services.auth_service import (
    EmailAlreadyInUseError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError
)

app = FastAPI(title="Argentourse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.exception_handler(EmailAlreadyInUseError)
async def handle_email_in_use(_: Request, exc: EmailAlreadyInUseError):
    return JSONResponse(status_code=409, content={"detail": "Email already in use"})

@app.exception_handler(InvalidCredentialsError)
async def handle_invalid_credntials(_: Request, exc: InvalidCredentialsError):
    return JSONResponse(status_code=401, content={"detail": "Invalid crednetials"})

@app.exception_handler(UserNotFoundError)
async def handle_user_not_found_error(_: Request, exc: UserNotFoundError):
    return JSONResponse(status_code=404, content={"detail": "User not found"})

@app.exception_handler(InvalidTokenError)
async def handle_invalid_token(_: Request, exc: InvalidTokenError):
    return JSONResponse(status_code=400, content={"detail": "Invalid or expired token"})

@app.get("/")
def read_root():
    return {"status": "ok"}


@app.get("/health/db")
def db_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": "ok", "result": result.scalar()}
    
app.include_router(api_router, prefix="/api/v1")