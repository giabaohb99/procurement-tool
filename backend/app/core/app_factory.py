"""Phần chung của hai ứng dụng FastAPI (ai-CR-119): ERP (`app.main`) và dịch vụ AI (`app.agent_main`).

Bốn bộ xử lý lỗi dưới đây chép NGUYÊN từ `app/main.py` (bao-CR-538, 25/08/2026) để hai ứng dụng trả cùng một phong bì
lỗi; sửa ở đây là sửa cho cả hai.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DataError

from app.core.config import settings
from app.core.response import error
from app.core.text_limits import body_models_of, describe_data_error, describe_validation_errors


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error(str(exc.detail), code=str(exc.status_code), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """bao-CR-538: `message` là câu tiếng Việt chỉ đúng ô sai; `details` giữ nguyên danh sách lỗi Pydantic."""
        errors = exc.errors()
        models = body_models_of(request.scope.get("route"))
        return error(describe_validation_errors(errors, models), code="validation_error", status_code=422,
                     details=errors)

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError):
        """bao-CR-538 — lưới cuối: chuỗi lọt xuống MySQL mới bị từ chối (1406) → 422 câu tiếng Việt."""
        import logging

        message, column = describe_data_error(exc)
        logging.getLogger("app.error").warning(
            "DataError lọt xuống DB: %s %s cột=%s — %s", request.method, request.url.path,
            column or "?", getattr(exc, "orig", exc))
        return error(message, code="validation_error", status_code=422,
                     details={"column": column} if column else None)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Lỗi không lường trước: phong bì + MÃ SỰ CỐ tra được trong log; không bày ruột gan ra màn hình."""
        import logging
        import uuid

        ma_su_co = uuid.uuid4().hex[:8].upper()
        logging.getLogger("app.error").exception(
            "[%s] %s %s — %s", ma_su_co, request.method, request.url.path, exc)
        return error(
            f"Hệ thống gặp lỗi không lường trước. Gửi mã sự cố {ma_su_co} cho quản trị "
            "để tra nguyên nhân.",
            code="internal_error", status_code=500, details={"ma_su_co": ma_su_co},
        )


def install_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
