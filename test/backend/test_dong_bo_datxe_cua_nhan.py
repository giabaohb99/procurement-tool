"""Cửa nhận sự kiện của app đặt xe cũ: `POST /api/sync/datxe/events`.

Cửa này không có người đăng nhập, chỉ có chữ ký HMAC — nên phần đáng kiểm nhất
là những cú gọi bị TỪ CHỐI, và từ chối mà KHÔNG để lại rác dưới DB.
"""
import json
import time

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.core.sync_signature import (
    HEADER_SIGNATURE,
    HEADER_SOURCE,
    HEADER_TIMESTAMP,
    build_signature,
)
from app.main import app
from app.modules.legacy_datxe.controller import PATH_EVENTS
from app.modules.sync_log.constants import SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE
from app.modules.vehicle_booking.model import VehicleBooking

SECRET = "khoa-thu-cho-bai-kiem-khong-phai-khoa-that"


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(settings, "SYNC_DATXE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "SYNC_SHARED_SECRET", SECRET, raising=False)
    #  Bộ tra danh mục không được đi hỏi Firebase trong bài kiểm.
    monkeypatch.setattr("app.modules.legacy_datxe.resolver.read_node",
                        lambda path: None)
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def sample_event(**over) -> dict:
    event = {
        "event_id": "evt_001",
        "occurred_at": "2026-09-17T10:00:00+07:00",
        "entity": "vehicle_booking",
        "action": "update",
        "legacy_id": "req_web_001",
        "erp_id": 0,
        "data": {
            "type": "CAR_BOOKING",
            "createdAt": 1_757_000_000_000,
            "createdBy": "uid_bat_ky",
            "approval": {"overallStatus": "pending_approval"},
            "details": {"purpose": "Đi họp", "startLocation": "Văn phòng",
                        "endLocation": "Nhà khách"},
        },
    }
    event.update(over)
    return event


def post(client, event: dict, *, secret: str = SECRET, source: str = SOURCE_DATXE,
         timestamp: str = "", signature: str = ""):
    body = json.dumps(event, ensure_ascii=False)
    stamp = timestamp or str(int(time.time()))
    return client.post(
        PATH_EVENTS,
        content=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            HEADER_SOURCE: source,
            HEADER_TIMESTAMP: stamp,
            HEADER_SIGNATURE: signature or build_signature(secret, stamp, PATH_EVENTS, body),
        },
    )


# ---------------------------------------------------------------------------
# Chốt chữ ký
# ---------------------------------------------------------------------------

def test_ky_dung_thi_nhan_phieu(client, db):
    resp = post(client, sample_event())

    assert resp.status_code == 200
    data = resp.json()["data"]
    phieu = db.query(VehicleBooking).one()
    assert data["erp_id"] == phieu.id
    assert data["status"] == int(SyncStatus.SUCCESS)
    assert data["sync_log_id"]


def test_ky_bang_khoa_khac_thi_401_va_khong_ghi_gi(client, db):
    resp = post(client, sample_event(), secret="khoa-sai")

    assert resp.status_code == 401
    #  Quan trọng hơn mã lỗi: người ngoài KHÔNG bơm được dòng nào vào sổ.
    assert db.query(SyncLog).count() == 0
    assert db.query(VehicleBooking).count() == 0


def test_thieu_header_chu_ky_thi_401(client):
    body = json.dumps(sample_event())
    resp = client.post(PATH_EVENTS, content=body.encode("utf-8"),
                       headers={"Content-Type": "application/json"})
    assert resp.status_code == 401


def test_dau_thoi_gian_cu_thi_401(client, db):
    cu = str(int(time.time()) - 3600)
    resp = post(client, sample_event(), timestamp=cu)

    assert resp.status_code == 401
    assert db.query(SyncLog).count() == 0


def test_khai_nham_he_nguon_thi_401(client):
    assert post(client, sample_event(), source="pos365").status_code == 401


def test_tat_dong_bo_thi_401(client, monkeypatch, db):
    monkeypatch.setattr(settings, "SYNC_DATXE_ENABLED", False, raising=False)
    resp = post(client, sample_event())

    assert resp.status_code == 401
    assert db.query(SyncLog).count() == 0


def test_chu_ky_chua_ky_tu_ngoai_ascii_thi_tu_choi_chu_khong_no(client):
    """`hmac.compare_digest` ném TypeError với chuỗi ngoài ASCII — phải trả về
    "không khớp" chứ không nổ.

    Kiểm thẳng ở `verify_signature` vì `httpx` chặn header ngoài ASCII ngay từ
    phía gửi; kẻ gọi thật thì gửi byte thô, Starlette giải sang chuỗi và hàm này
    là chỗ đầu tiên đụng vào nó.
    """
    from app.core.sync_signature import verify_signature

    ok, reason = verify_signature(SOURCE_DATXE, PATH_EVENTS, "{}",
                                  str(int(time.time())), "chữ ký bậy")
    assert ok is False and reason


# ---------------------------------------------------------------------------
# Thân yêu cầu
# ---------------------------------------------------------------------------

def test_thieu_legacy_id_thi_400(client):
    resp = post(client, sample_event(legacy_id=""))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "sync_bad_body"


def test_loai_du_lieu_chua_ho_tro_thi_400(client):
    resp = post(client, sample_event(entity="file"))
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "sync_bad_entity"


def test_gui_lai_cung_event_id_thi_bo_qua(client, db):
    post(client, sample_event())
    resp = post(client, sample_event())

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == int(SyncStatus.SKIPPED)
    assert db.query(VehicleBooking).count() == 1


def test_bo_qua_van_phai_tra_ve_erp_id_that(client, db):
    """App cũ ghi `erp_id` nhận được vào `erpId` — trả `0` là xóa mối nối."""
    post(client, sample_event())
    phieu = db.query(VehicleBooking).one()

    #  (1) Trùng `event_id`: nhánh KHÔNG sinh dòng sổ nào.
    trung_su_kien = post(client, sample_event())
    #  (2) Sự kiện khác nhưng nội dung không đổi ô nào của ERP: nhánh có dòng
    #      sổ *bỏ qua*. Hai nhánh khác nhau, cùng một nghĩa vụ.
    khong_doi = post(client, sample_event(event_id="evt_003"))

    for resp in (trung_su_kien, khong_doi):
        data = resp.json()["data"]
        assert data["status"] == int(SyncStatus.SKIPPED)
        assert data["erp_id"] == phieu.id


def test_app_cu_bao_xoa_thi_erp_giu_nguyen_phieu(client, db):
    post(client, sample_event())
    resp = post(client, sample_event(event_id="evt_002", action="delete"))

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == int(SyncStatus.SKIPPED)
    assert db.query(VehicleBooking).count() == 1
