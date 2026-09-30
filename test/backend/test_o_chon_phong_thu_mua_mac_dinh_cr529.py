"""bao-CR-529 — ô «Phòng thu mua mặc định» (`central_purchasing_dept_code`) CHỌN từ danh mục Phòng ban.

Đại ca: «sao chỗ này để mã PBA017, sao không cho chọn từ danh sách phòng ban». Giao diện nay vẽ ô
chọn theo cờ `type: "department"`; dưới DB vẫn lưu MÃ phòng như bao-CR-524. Điều mới ở backend là
CỬA LƯU: mã không có trong danh mục hoặc phòng đã ngừng dùng → 400 (trước CR này gõ sai mã là
`core/central_purchasing` lặng lẽ quay về «phòng xử lý để trống»).
"""
import time

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.core.central_purchasing import get_central_dept_id
from app.modules.department.model import Department
from app.modules.setting import service
from app.modules.setting.model import Setting

KEY = "central_purchasing_dept_code"


@pytest.fixture(autouse=True)
def _settings_read_test_db(db, monkeypatch):
    """`app_settings` đọc từ DB của bài kiểm (bản thật mở `SessionLocal` MySQL), dọn đệm mỗi bài."""
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    app_settings.refresh()
    yield
    app_settings.refresh()


@pytest.fixture
def depts(db, seed):
    central = Department(code="PBA017", name="Sản xuất -Thu mua", company_id=seed.company_id, is_active=True)
    factory = Department(code="NM01", name="Nhà máy Dego Organic", company_id=seed.company_id, is_active=True)
    retired = Department(code="CU01", name="Phòng cũ", company_id=seed.company_id, is_active=False)
    db.add_all([central, factory, retired])
    db.commit()
    return central, factory, retired


def _stored(db) -> str | None:
    row = db.query(Setting).filter(Setting.skey == KEY).first()
    return row.svalue if row else None


def _save_error(db, value) -> str:
    with pytest.raises(HTTPException) as e:
        service.save(db, {KEY: value}, user_id=7)
    assert e.value.status_code == 400
    return str(e.value.detail)


def test_field_is_flagged_as_department_picker_but_stored_as_string():
    field = next(f for f in service.get_all()["fields"] if f["key"] == KEY)
    assert field["type"] == "department"
    assert app_settings.REGISTRY[KEY][0] == "str"


def test_saving_existing_department_code_switches_central_dept(db, depts):
    _, factory, _ = depts
    service.save(db, {KEY: " NM01 "}, user_id=7)
    assert _stored(db) == "NM01"
    db.info.pop("central_purchasing_dept", None)
    assert get_central_dept_id(db) == factory.id


def test_blank_means_default_pba017(db, depts):
    central, _, _ = depts
    service.save(db, {KEY: "NM01"}, user_id=7)
    service.save(db, {KEY: ""}, user_id=7)
    assert _stored(db) == ""
    db.info.pop("central_purchasing_dept", None)
    assert get_central_dept_id(db) == central.id


def test_unknown_code_is_rejected_and_old_value_kept(db, depts):
    service.save(db, {KEY: "NM01"}, user_id=7)
    detail = _save_error(db, "KHONGCO")
    assert "không có phòng ban mã «KHONGCO»" in detail
    db.rollback()
    assert _stored(db) == "NM01"


def test_retired_department_is_rejected(db, depts):
    assert "đã ngừng dùng" in _save_error(db, "CU01")


def test_unchanged_broken_value_does_not_block_saving_other_fields(db, depts):
    """Mã hỏng khai từ trước CR này: người chỉ sửa ô khác vẫn lưu được (màn hình gửi lại mọi ô)."""
    db.add(Setting(skey=KEY, svalue="MACU"))
    db.commit()
    app_settings.refresh()
    service.save(db, {KEY: "MACU", "pr_dispatch_enabled": False}, user_id=7)
    assert _stored(db) == "MACU"
