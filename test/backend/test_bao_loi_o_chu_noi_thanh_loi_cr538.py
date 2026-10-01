"""bao-CR-538 (phần 2, 3, 4) — LỖI Ô CHỮ PHẢI NÓI THÀNH LỜI, KHÔNG RA 500.

Sự cố D30D24DF (30/09/2026): lưu phiếu khảo sát, ô «Ghi chú NSPT» dài hơn cột, MySQL từ chối
«Data too long for column 'nspt_note'» → người dùng thấy «Hệ thống gặp lỗi không lường trước».
Đại ca: «để dưới model trả lỗi lên sql trả lên thì không ổn, phải bắt validate kỹ».

Ba lớp được kiểm ở đây:
  - Phần 3: lỗi Pydantic 422 trả câu tiếng Việt chỉ đúng ô («Ô "Mục đích" tối đa 355 ký tự
    (đang nhập 412)»), `details` giữ nguyên cho máy đọc.
  - Phần 2: đường ghi không qua schema (Body `dict`, gán thẳng trong service) chặn bằng
    `ensure_max_length` / `ensure_model_fits` TRƯỚC khi gán.
  - Phần 4: lọt hết mà MySQL vẫn báo 1406 thì lưới cuối đổi thành 422 + rollback phiên.

Gọi thẳng hàm xử lý thay vì dựng `TestClient` (container kiểm không có `httpx`), cùng cách
`test_loi_khong_luong_truoc_co_ma_su_co.py`.
"""
import asyncio
import json
import logging

import pytest
from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import DataError

from app.core import database
from app.core.text_limits import (column_limit, describe_data_error, describe_validation_errors,
                                  ensure_max_length, ensure_model_fits)
from app.main import data_error_handler, validation_exception_handler
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.survey.model import SurveySupplierLine
from app.modules.survey_request.model import SurveyRequestOption


# ── Schema mẫu cho phần 3 ────────────────────────────────────────────────

class LineIn(BaseModel):
    note: str = Field(default="", max_length=10)
    qty: float = 0


class TicketIn(BaseModel):
    purpose: str = Field(default="", max_length=355)
    code: str = Field(default="", max_length=20, title="Mã phiếu nội bộ")
    need_date: str = ""
    lines: list[LineIn] = []


def _validation_errors(model: type[BaseModel], payload: dict) -> list[dict]:
    """Lỗi y như FastAPI đưa vào `RequestValidationError`: `loc` mở đầu bằng "body"."""
    with pytest.raises(ValidationError) as caught:
        model.model_validate(payload)
    return [{**e, "loc": ("body", *e["loc"])} for e in caught.value.errors()]


def _route_for(model: type[BaseModel]):
    router = APIRouter()

    @router.post("/tickets")
    def create_ticket(data: model):  # type: ignore[valid-type]
        return data

    return router.routes[0]


def _call_validation_handler(errors: list[dict], route=None) -> tuple[int, dict]:
    scope = {"type": "http", "method": "POST", "path": "/api/tickets", "headers": [], "query_string": b""}
    if route is not None:
        scope["route"] = route
    res = asyncio.run(validation_exception_handler(Request(scope), RequestValidationError(errors)))
    return res.status_code, json.loads(res.body)


# ── Phần 3: câu báo lỗi ──────────────────────────────────────────────────

def test_string_too_long_says_field_limit_and_typed_length():
    errors = _validation_errors(TicketIn, {"purpose": "x" * 412})
    status, body = _call_validation_handler(errors)
    assert status == 422
    assert body["success"] is False and body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == 'Ô "Mục đích" tối đa 355 ký tự (đang nhập 412)'


def test_details_stay_untouched_for_machines():
    errors = _validation_errors(TicketIn, {"purpose": "x" * 412})
    _status, body = _call_validation_handler(errors)
    details = body["error"]["details"]
    assert len(details) == 1
    assert details[0]["type"] == "string_too_long"
    assert details[0]["loc"] == ["body", "purpose"]
    assert details[0]["ctx"] == {"max_length": 355}


def test_child_row_error_names_row_number():
    errors = _validation_errors(TicketIn, {"lines": [{"note": "ok"}, {"note": "y" * 11}]})
    assert describe_validation_errors(errors) == 'Ô "Ghi chú" ở dòng thứ 2 tối đa 10 ký tự (đang nhập 11)'


def test_many_errors_show_first_and_count_the_rest():
    errors = _validation_errors(TicketIn, {"purpose": "x" * 400, "lines": [{"qty": "abc"}, {"note": "z" * 20}]})
    message = describe_validation_errors(errors)
    assert message.startswith('Ô "Mục đích" tối đa 355 ký tự (đang nhập 400)')
    assert message.endswith("và 2 lỗi khác")


def test_field_title_on_schema_wins_over_label_table():
    errors = _validation_errors(TicketIn, {"code": "c" * 21})
    _status, body = _call_validation_handler(errors, _route_for(TicketIn))
    assert body["error"]["message"] == 'Ô "Mã phiếu nội bộ" tối đa 20 ký tự (đang nhập 21)'


def test_unknown_field_falls_back_to_field_name():
    class OddIn(BaseModel):
        zz_custom: str = Field(default="", max_length=3)

    errors = _validation_errors(OddIn, {"zz_custom": "abcd"})
    assert describe_validation_errors(errors) == 'Ô "zz_custom" tối đa 3 ký tự (đang nhập 4)'


def test_missing_number_and_date_errors_are_vietnamese():
    from datetime import date

    class StrictIn(BaseModel):
        purpose: str
        qty: float = 0
        need_date: date | None = None

    assert describe_validation_errors(_validation_errors(StrictIn, {})) == 'Ô "Mục đích" bắt buộc nhập'
    assert (describe_validation_errors(_validation_errors(StrictIn, {"purpose": "a", "qty": "mười"}))
            == 'Ô "qty" phải là số')
    assert (describe_validation_errors(_validation_errors(StrictIn, {"purpose": "a", "need_date": "32/13"}))
            == 'Ô "Ngày cần hàng" không phải ngày hợp lệ (định dạng NĂM-THÁNG-NGÀY)')


def test_custom_validator_message_is_kept():
    from pydantic import model_validator

    class RangeIn(BaseModel):
        start: int = 0
        end: int = 0

        @model_validator(mode="after")
        def check_range(self):
            if self.end < self.start:
                raise ValueError("Ngày hết hạn đăng ký phải sau ngày cấp")
            return self

    errors = _validation_errors(RangeIn, {"start": 5, "end": 1})
    assert describe_validation_errors(errors) == "Ngày hết hạn đăng ký phải sau ngày cấp"


# ── Phần 2: helper chặn trước khi gán ────────────────────────────────────

def test_ensure_max_length_passes_short_and_non_text_values():
    assert ensure_max_length("abc", 3, "Mã") == "abc"
    assert ensure_max_length(None, 3, "Mã") is None
    assert ensure_max_length(12345, 3, "Mã") == 12345


def test_ensure_max_length_raises_422_with_same_sentence():
    with pytest.raises(HTTPException) as caught:
        ensure_max_length("x" * 501, 500, "Lý do tạm ngưng / hủy")
    assert caught.value.status_code == 422
    assert caught.value.detail == 'Ô "Lý do tạm ngưng / hủy" tối đa 500 ký tự (đang nhập 501)'


def test_ensure_model_fits_reads_column_length_from_model():
    limit = column_limit(SurveyRequestOption, "system_product_code")
    assert limit and limit > 0
    ensure_model_fits(SurveyRequestOption, {"system_product_code": "a" * limit, "nstm_note": "n" * 100000})
    with pytest.raises(HTTPException) as caught:
        ensure_model_fits(SurveyRequestOption, {"system_product_code": "a" * (limit + 1)})
    assert caught.value.status_code == 422
    assert "Mã sản phẩm hệ thống" in caught.value.detail


def test_survey_request_option_dict_body_is_blocked_before_db(db):
    from app.modules.survey_request import service

    option = SurveyRequestOption(survey_request_line_id=1)
    db.add(option)
    db.commit()
    limit = column_limit(SurveyRequestOption, "system_product_code")
    with pytest.raises(HTTPException) as caught:
        service.set_option_fields(db, 1, option.id, 1, system_product_code="m" * (limit + 1))
    assert caught.value.status_code == 422
    db.refresh(option)
    assert option.system_product_code == ""


def test_survey_fill_line_dict_body_is_blocked_before_db(db):
    from app.modules.survey import service

    line = SurveySupplierLine(survey_id=1, line_approve=service.MISSING)
    db.add(line)
    db.commit()
    limit = column_limit(SurveySupplierLine, "supplier_name")
    with pytest.raises(HTTPException) as caught:
        service.fill_missing_line(db, 1, "supplier", line.id, {"supplier_name": "s" * (limit + 1)}, 1)
    assert caught.value.status_code == 422
    assert "Tên NCC" in caught.value.detail


def test_po_item_pause_reason_is_blocked_before_db(db):
    from app.modules.purchase_order import service

    po = PurchaseOrder(status="approved")
    db.add(po)
    db.flush()
    item = POItem(po_id=po.id)
    db.add(item)
    db.commit()
    limit = column_limit(POItem, "pause_reason")
    with pytest.raises(HTTPException) as caught:
        service.set_item_progress(db, po.id, item.id, service.PROG_PAUSED, "r" * (limit + 1), 1)
    assert caught.value.status_code == 422
    assert caught.value.detail == f'Ô "Lý do tạm ngưng / hủy" tối đa {limit} ký tự (đang nhập {limit + 1})'


# ── Phần 4: lưới cuối cho MySQL 1406 ─────────────────────────────────────

def _data_error(column: str = "pause_reason", table: str = "tab_po_item") -> DataError:
    orig = Exception(1406, f"Data too long for column '{column}' at row 1")
    return DataError(f"UPDATE {table} SET {column}=%(p)s WHERE {table}.id = %(id)s", {}, orig)


def test_data_error_turns_into_422_with_column_limit(caplog):
    scope = {"type": "http", "method": "PUT", "path": "/api/purchase-orders/7", "headers": [], "query_string": b""}
    with caplog.at_level(logging.WARNING, logger="app.error"):
        res = asyncio.run(data_error_handler(Request(scope), _data_error()))
    body = json.loads(res.body)
    assert res.status_code == 422
    limit = column_limit(POItem, "pause_reason")
    assert body["error"]["message"] == f'Ô "Lý do tạm ngưng / hủy" dài quá, tối đa {limit} ký tự'
    assert body["error"]["details"] == {"column": "pause_reason"}
    #  WARNING phải có đường API + tên cột để đi vá chỗ thiếu chặn.
    logged = " ".join(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "/api/purchase-orders/7" in logged and "pause_reason" in logged


def test_data_error_without_known_table_still_names_column():
    message, column = describe_data_error(_data_error(column="zz_unknown_col", table="tab_khong_co"))
    assert column == "zz_unknown_col"
    assert message == 'Ô "zz_unknown_col" dài quá'


def test_get_db_rolls_back_when_error_passes_through(monkeypatch):
    calls = []

    class FakeSession:
        def rollback(self):
            calls.append("rollback")

        def close(self):
            calls.append("close")

    monkeypatch.setattr(database, "SessionLocal", FakeSession)
    gen = database.get_db()
    next(gen)
    with pytest.raises(DataError):
        gen.throw(_data_error())
    assert calls == ["rollback", "close"]
