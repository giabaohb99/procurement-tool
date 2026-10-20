"""duoc-CR-654 (D0a/D0b) — sự kiện UI_ACTION: mã cố định, validator chéo, trần 60/lô, không chữ gõ; 13 form."""
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import app_settings, code_sets, status_catalog  # noqa: F401
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.ui_action_codes import UI_ACTION_LABELS, UiAction
from app.core.usage_codes import UI_FORM_LABELS, UiEventType, UiForm
from app.main import app
from app.modules.usage_profile.model import UiEvent
from app.modules.usage_profile.telemetry_schema import MAX_UI_ACTIONS_PER_BATCH, UiEventBatch
from app.modules.usage_profile.telemetry_service import build_rows

from ho_so_lam_viec_factory import make_person

URL = "/api/telemetry/ui-events"


def ev(**kw):
    base = {"type": 8, "route": "/procurement/purchase-orders", "action": 1, "age_ms": 100, "tab_key": 5}
    return {**base, **kw}


def batch(*events):
    return UiEventBatch.model_validate({"events": list(events)})


@pytest.fixture
def client_as(db):
    limiter.reset()
    app_settings._cache["usage_tracking_enabled"] = "true"

    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    app_settings._cache.pop("usage_tracking_enabled", None)


def test_ma_cong_bang_so_co_dinh_va_nhan_du():
    assert int(UiEventType.UI_ACTION) == 8
    assert [int(x) for x in UiAction] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 21, 22, 23, 100, 101, 102, 200, 201, 202, 203]
    assert set(UI_ACTION_LABELS) == set(UiAction) and all(UI_ACTION_LABELS.values())
    assert "ui_action" in status_catalog.all_sets()
    assert len({int(x) for x in UiAction}) == len(list(UiAction))   # duy nhất


def test_13_form_so_cu_khong_doi_va_nhan_du():
    assert [int(x) for x in UiForm][:6] == [1, 2, 3, 4, 5, 6]
    assert [int(x) for x in UiForm] == list(range(1, 14))
    assert UiForm.PAYMENT_REQUEST == 7 and UiForm.WORK_TASK == 13
    assert set(UI_FORM_LABELS) == set(UiForm)


@pytest.mark.parametrize("form", range(7, 14))
def test_nhan_form_open_cho_form_moi(form):
    rows = build_rows(batch({"type": 3, "route": "/finance/payment-requests/new", "form": form}), 1, None)
    assert rows[0]["form_key"] == form and rows[0]["action_key"] == 0


@pytest.mark.parametrize("bad", [
    ev(action=0), ev(action=999), ev(action=10),                    # UI_ACTION phải có mã hợp lệ
    {"type": 1, "route": "/a", "action": 1},                        # loại khác không được mang action
    ev(label="Xuất file của anh A"), ev(text="abc"),               # không chữ tự do
])
def test_schema_tu_choi(bad):
    with pytest.raises(ValidationError):
        batch(bad)


def test_ghi_action_key_dung():
    rows = build_rows(batch(ev(action=int(UiAction.EXPORT_EXCEL)), {"type": 1, "route": "/a"}), 1, None)
    assert rows[0]["action_key"] == 100 and rows[0]["event_type"] == 8
    assert rows[1]["action_key"] == 0
    assert all(set(r) >= {"action_key"} and "label" not in r and "text" not in r for r in rows)


def test_tran_60_ui_action_moi_lo_khong_422_va_giu_su_kien_khac():
    events = [ev(tab_key=i) for i in range(100)]
    events[0] = {"type": 1, "route": "/a"}
    rows = build_rows(batch(*events), 1, None)
    assert sum(1 for r in rows if r["event_type"] == 8) == MAX_UI_ACTIONS_PER_BATCH == 60
    assert sum(1 for r in rows if r["event_type"] == 1) == 1


def test_http_ghi_action_va_meta_rong(db, client_as):
    user, _ = make_person(db, "A1")
    resp = client_as(user).post(URL, json={"events": [ev(action=int(UiAction.PRINT)), ev(action=int(UiAction.SORT_CHANGE))]})
    assert resp.status_code in (200, 201), resp.text
    rows = db.query(UiEvent).order_by(UiEvent.id).all()
    assert [(r.event_type, r.action_key, r.user_id) for r in rows] == [(8, 101, user.id), (8, 5, user.id)]
    assert all(r.meta is None and r.result_count is None for r in rows)


def test_http_ma_la_422_khong_ghi(db, client_as):
    user, _ = make_person(db, "A2")
    assert client_as(user).post(URL, json={"events": [ev(action=77)]}).status_code == 422
    assert db.query(UiEvent).count() == 0


def test_cong_tac_tat_204_khong_ghi(db, client_as):
    user, _ = make_person(db, "A3")
    c = client_as(user)
    app_settings._cache["usage_tracking_enabled"] = "false"
    assert c.post(URL, json={"events": [ev()]}).status_code == 204
    assert db.query(UiEvent).count() == 0


def test_than_lo_100_ui_action_nho_hon_64kb():
    body = json.dumps({"events": [ev() for _ in range(100)]})
    assert len(body.encode()) < 64 * 1024
