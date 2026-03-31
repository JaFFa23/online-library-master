from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # exc.errors() -> список ошибок вида:
        # [{"loc": [...], "msg": "...", "type": "...", ...}, ...]
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        # exc.detail может быть строкой, dict или list — возвращаем как есть
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "details": exc.detail,
            },
        )
