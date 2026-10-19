"""duoc-CR-641 phase 03 — nhận lô sự kiện giao diện: schema, chuẩn hóa, công tắc, 1 câu INSERT, 413, 401, không vào request_log."""
import json
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import app_settings
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.logging_policy import should_log_request
from app.main import app
from app.modules.usage_profile.model import UiEvent
from app.modules.usage_profile.telemetry_schema import MAX_EVENTS_PER_BATCH, UiEventBatch
from app.modules.usage_profile.telemetry_service import build_rows, store_batch

from ho_so_lam_viec_factory import make_person
from lich_lam_viec_factory import count_queries

URL = "/api/telemetry/ui-events"


def ev(**kw):
    base = {"type": 1, "route": "/procurement/purchase-orders/:id", "form": 0, "duration_ms": 0,
            "result_count": None, "age_ms": 1200, "tab_key": 81723, "error": None}
    return {**base, **kw}


def batch(*events):
    return UiEventBatch.model_validate({"events": list(events)})


@pytest.fixture
def client_as(db):
    limiter.reset()

    def make(user=None, token=True):
        app.dependency_overrides[get_db] = lambda: db
        if user is not None:
            app.dependency_overrides[get_current_user] = lambda: user
        headers = {"Authorization": f"Bearer test-{uuid.uuid4().hex}"} if token else {}
        return TestClient(app, headers=headers)

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


# ── schema (SQLite không ép VARCHAR nên kiểm ở tầng schema) ──────────────────

@pytest.mark.parametrize("bad", [
    ev(type=99), ev(form=99), ev(route="/" + "a" * 120), ev(route="no-slash"), ev(route="/a b"),
    ev(duration_ms=86_400_001), ev(duration_ms=-1), ev(result_count=1_000_001), ev(age_ms=-1),
    ev(tab_key=2**31), ev(type=7, error={"name": "x" * 61, "message": "m"}),
    ev(type=7, error={"name": "n", "message": "m" * 201}), ev(error={"name": "n", "message": "m"}),
    ev(user_id=5), ev(keyword="nguyen van a"),
])
def test_schema_tu_choi_su_kien_xau(bad):
    with pytest.raises(ValidationError):
        batch(bad)


def test_schema_tran_so_su_kien_moi_lo():
    batch(*[ev()] * MAX_EVENTS_PER_BATCH)
    with pytest.raises(ValidationError):
        batch(*[ev()] * (MAX_EVENTS_PER_BATCH + 1))
    with pytest.raises(ValidationError):
        UiEventBatch.model_validate({"events": []})


def test_schema_khong_nhan_user_id_hay_gio_tu_client():
    with pytest.raises(ValidationError):
        UiEventBatch.model_validate({"events": [ev()], "user_id": 9})


# ── chuẩn hóa ở server ────────────────────────────────────────────────────────

def test_route_duoc_chuan_hoa_lai_o_server():
    rows = build_rows(batch(ev(route="/x/123/y/550e8400-e29b-41d4-a716-446655440000")), 1, None)
    assert rows[0]["route_pattern"] == "/x/:id/y/:id"


def test_age_ms_bi_kep_toi_da_24_gio():
    #  L7 (CR-641 review): lô giữ qua đêm do 401 phải giữ được giờ gốc — trần cũ 10 phút làm nó rơi nhầm ngày.
    now = datetime(2026, 1, 5, 12, 0, 0)
    rows = build_rows(batch(ev(age_ms=100_000_000), ev(age_ms=0), ev(age_ms=2000), ev(age_ms=8 * 3_600_000)), 1, None, now=now)
    assert rows[0]["occurred_at"] == now - timedelta(hours=24)
    assert rows[3]["occurred_at"] == now - timedelta(hours=8)
    assert rows[1]["occurred_at"] == now
    assert rows[2]["occurred_at"] == now - timedelta(seconds=2)


def test_search_chi_giu_so_ket_qua_khong_giu_tu_khoa_va_meta_chi_cho_loi():
    rows = build_rows(batch(ev(type=6, route="/search", result_count=0), ev(type=1, result_count=7),
                            ev(type=7, error={"name": "TypeError", "message": "x is undefined"})), 1, None)
    assert rows[0]["result_count"] == 0 and rows[0]["meta"] is None
    assert rows[1]["result_count"] is None          # chỉ SEARCH mới giữ result_count
    assert rows[2]["meta"] == {"n": "TypeError", "m": "x is undefined"}
    assert all("q" not in r and "keyword" not in r for r in rows)


def test_50_su_kien_chi_mot_cau_insert(db):
    user, _ = make_person(db, "T1")
    b = batch(*[ev(tab_key=i) for i in range(50)])
    n, sql = count_queries(db, lambda: store_batch(db, b, user.id, 7))
    assert n == 50
    assert sum(1 for s in sql if s.lstrip().upper().startswith("INSERT")) == 1
    assert db.query(UiEvent).count() == 50
    assert {e.user_id for e in db.query(UiEvent)} == {user.id}
    assert {e.session_id for e in db.query(UiEvent)} == {7}


# ── qua HTTP ──────────────────────────────────────────────────────────────────

def test_chua_dang_nhap_401(client_as):
    resp = client_as(token=False).post(URL, json={"events": [ev()]})
    assert resp.status_code == 401


def test_ghi_lo_user_id_lay_tu_token(db, client_as):
    user, _ = make_person(db, "T2")
    resp = client_as(user).post(URL, json={"events": [ev(), ev(type=2, duration_ms=5000)]})
    assert resp.status_code == 200 and resp.json()["data"] == {"accepted": 2}
    assert [e.user_id for e in db.query(UiEvent)] == [user.id, user.id]


def test_cong_tac_tat_nhan_roi_bo_204_bang_rong(db, client_as):
    user, _ = make_person(db, "T3")
    app_settings._cache["usage_tracking_enabled"] = "false"
    resp = client_as(user).post(URL, json={"events": [ev()]})
    assert resp.status_code == 204 and resp.content == b""
    assert db.query(UiEvent).count() == 0


def test_lo_xau_422(db, client_as):
    user, _ = make_person(db, "T4")
    assert client_as(user).post(URL, json={"events": [ev(type=99)]}).status_code == 422
    assert client_as(user).post(URL, json={"events": []}).status_code == 422


def test_than_qua_64kb_tra_413_truoc_khi_kiem_schema(db, client_as):
    user, _ = make_person(db, "T5")
    big = {"events": [ev(route="/" + "a" * 100)] * 100, "pad": "x" * 70_000}
    resp = client_as(user).post(URL, json=big)
    assert resp.status_code == 413


def test_gioi_han_30_lo_moi_phut(db, client_as):
    user, _ = make_person(db, "T6")
    c = client_as(user)
    codes = [c.post(URL, json={"events": [ev()]}).status_code for _ in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429


def test_duong_telemetry_khong_vao_request_log_nhung_duong_khac_van_ghi():
    assert should_log_request("POST", URL) is False
    assert should_log_request("POST", "/api/telemetry/anything") is False
    assert should_log_request("POST", "/api/notifications/1") is True


def test_than_chunked_khong_content_length_van_bi_chan_413(db, client_as):
    """Bug M2 (CR-641 review): chặn 64 KB chỉ nhìn header Content-Length nên thân chunked đi lọt hết vào RAM."""
    user, _ = make_person(db, "T7")

    def chunks():
        for _ in range(20):
            yield b"x" * 8192   # 160 KB, không có Content-Length (generator → Transfer-Encoding: chunked)

    resp = client_as(user).post(URL, content=chunks(), headers={"content-type": "application/json"})
    assert resp.status_code == 413
    assert db.query(UiEvent).count() == 0


def test_than_nho_khong_content_length_van_nhan_va_van_bi_gioi_han_tan_suat(db, client_as):
    user, _ = make_person(db, "T8")
    c = client_as(user)
    body = json.dumps({"events": [ev()]}).encode()

    def chunked():
        yield body

    assert c.post(URL, content=chunked(), headers={"content-type": "application/json"}).status_code == 200
    codes = [c.post(URL, content=chunked(), headers={"content-type": "application/json"}).status_code for _ in range(30)]
    assert codes[-1] == 429     # trần 30 lô/phút vẫn áp dụng sau khi đọc thân có trần
    assert c.post(URL, content=b"{khong phai json", headers={"content-type": "application/json"}).status_code in (422, 429)
