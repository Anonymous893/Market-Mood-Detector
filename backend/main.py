"""Application entry point for the Market Mood Detector."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router
from config import CORS_ORIGINS
from db.history import init as init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized. CORS origins: %s", CORS_ORIGINS)
    yield


app = FastAPI(
    title="Market Mood Detector",
    lifespan=lifespan,
    description=(
        "Market sentiment analysis using Yahoo Finance ticker-specific RSS feeds "
        "and FinBERT. Includes fuzzy deduplication, TTL caching, SQLite history, "
        "trend analytics, and confidence scoring."
    ),
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
}


@app.exception_handler(HTTPException)
async def _http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", _STATUS_CODES.get(exc.status_code, "ERROR"))
        message = detail.get("message", str(exc.detail))
        details = detail.get("details")
    else:
        code = _STATUS_CODES.get(exc.status_code, "ERROR")
        message = str(detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message, "details": details},
        },
    )


@app.exception_handler(RequestValidationError)
async def _validation_exc_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        },
    )


app.include_router(router)
