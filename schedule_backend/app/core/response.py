from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None


class AppException(Exception):
    def __init__(self, message: str, code: int = 4000, status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def success_response(data: T | None = None, message: str = "success") -> ApiResponse[T]:
    return ApiResponse(code=0, message=message, data=data)


def error_response(message: str, code: int = 4000, status_code: int = 400) -> JSONResponse:
    payload = ApiResponse[None](code=code, message=message, data=None)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        return error_response(exc.message, code=exc.code, status_code=exc.status_code)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        detail = str(exc.detail) if exc.detail else "request failed"
        return error_response(detail, code=exc.status_code, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
        message = "; ".join(error["msg"] for error in exc.errors())
        return error_response(message or "validation error", code=4220, status_code=422)

    @app.exception_handler(Exception)
    async def handle_unknown_exception(_: Request, exc: Exception) -> JSONResponse:
        return error_response(str(exc) or "internal server error", code=5000, status_code=500)
