"""bao-CR-649 — bộ thu sự kiện giao diện trên app cũ thumua: trường `app` cấp lô, quy route về v2, cột
`tab_ui_event.app`, màn tách theo app, và mã của tệp `frontend/src/telemetry/ui-event-codes.ts` khớp Python.

Bài đối chiếu mã đọc mã NGOÀI `backend/`: trong container `api` qua mount chỉ-đọc `/app/thumua-src`
(docker-compose.yml), ở máy thật / CI thì dò ngược lên tìm `frontend/src` (cùng khuôn `test_dong_bo_giao_dien_v2.py`).
"""
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import app_settings
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.usage_codes import UiApp, UiEventType, UiForm
from app.main import app
from app.modules.usage_profile import app_split_service
from app.modules.usage_profile.model import UiEvent
from app.modules.usage_profile.route_pattern import _THUMUA_TO_V2, canonical_route, normalize_route
from app.modules.usage_profile.telemetry_schema import UiEventBatch
from app.modules.usage_profile.telemetry_service import build_rows, store_batch

from ho_so_lam_viec_factory import add_ui, make_person

URL = "/api/telemetry/ui-events"


def ev(**kw):
    base = {"type": 1, "route": "/purchase-requests/:id", "form": 0, "duration_ms": 0,
            "result_count": None, "age_ms": 0, "tab_key": 7, "error": None}
    return {**base, **kw}


@pytest.fixture
def client_as(db):
    limiter.reset()

    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


# ── schema: trường `app` cấp lô ────────────────────────────────────────────────

def test_lo_khong_khai_app_la_erp_v2():
    assert UiEventBatch.model_validate({"events": [ev()]}).app == int(UiApp.ERP_V2)


def test_lo_thumua_khai_app_2():
    assert UiEventBatch.model_validate({"app": 2, "events": [ev()]}).app == int(UiApp.THUMUA)


@pytest.mark.parametrize("bad", [0, 3, 99, -1])
def test_app_la_tu_choi(bad):
    with pytest.raises(ValidationError):
        UiEventBatch.model_validate({"app": bad, "events": [ev()]})


def test_app_khong_duoc_nam_trong_tung_su_kien():
    #  `extra="forbid"` ở từng sự kiện: thumua gửi nhầm `app` vào event là 422 — hợp đồng là CẤP LÔ
    with pytest.raises(ValidationError):
        UiEventBatch.model_validate({"events": [ev(app=2)]})


# ── quy route thumua về v2 ──────────────────────────────────────────────────────

#  MỖI DÒNG của bảng `_THUMUA_TO_V2` có một dòng ở đây (route danh sách của thumua → route v2); bài dưới canh bảng
#  và danh sách này phủ nhau đủ — thêm màn mà quên một bên là đỏ.
_LIST_ROUTES = {
    "/purchase-requests": "/procurement/purchase-requests",
    "/survey-requests": "/procurement/survey-requests",
    "/purchase-orders": "/procurement/purchase-orders",
    "/surveys": "/procurement/surveys",
    "/surveys-supplier": "/procurement/surveys",
    "/surveys-product": "/procurement/surveys",
    "/survey-progress": "/procurement/survey-progress",
    "/purchase-progress": "/procurement/purchase-progress",
    "/category-assignees": "/procurement/category-assignees",
    "/customs-prices": "/procurement/customs-prices",
    "/po-cost-types": "/procurement/po-cost-types",
    "/pr-lines-report": "/procurement/pr-lines-report",
    "/survey-report": "/procurement/survey-report",
    "/documents": "/procurement/purchase-orders/:id/documents",
    "/suppliers": "/production/suppliers",
    "/products": "/production/products",
    "/units": "/production/units",
    "/item-groups": "/production/item-groups",
    "/contracts": "/production/contracts",
    "/payables": "/finance/payables",
    "/payment-requests": "/finance/payment-requests",
    "/companies": "/hr/companies",
    "/departments": "/hr/departments",
    "/employees": "/hr/employees",
    "/inventory": "/inventory/stock",
    "/warehouses": "/inventory/warehouses",
    "/backups": "/system/backups",
    "/settings": "/system/settings",
    "/roles": "/system/permissions",
    "/users": "/system/permissions/users",
    "/reports": "/report",
    "/tickets": "/support",
}


@pytest.mark.parametrize("raw, expected", list(_LIST_ROUTES.items()))
def test_canonical_route_tung_man_thumua(raw, expected):
    assert canonical_route(raw, int(UiApp.THUMUA)) == expected


def test_bang_quy_route_va_bai_kiem_phu_nhau_du():
    assert {"/" + k for k in _THUMUA_TO_V2} == set(_LIST_ROUTES)


@pytest.mark.parametrize("raw, expected", [
    ("/purchase-requests/:id", "/procurement/purchase-requests/:id"),
    ("/purchase-requests/new", "/procurement/purchase-requests/new"),
    ("/survey-requests/:id/process", "/procurement/survey-requests/:id/process"),
    ("/surveys-supplier/:id", "/procurement/surveys/:id"),
    ("/customs-prices/pesticides/:id", "/procurement/customs-prices/pesticides/:id"),
    ("/users/:id", "/system/permissions/users/:id"),
    ("/tickets/:id", "/support/tickets/:id"),            # danh sách là `/support`, chi tiết giữ đoạn `tickets`
    ("/print/purchase-order/:id", "/print/purchase-order/:id"),   # hai app đã giống nhau
    ("/me", "/me"), ("/notifications", "/notifications"),         # cùng route ở hai app
    ("/import-batches/:id", "/import-batches/:id"),               # thumua không có bản v2: giữ
    ("/customs-regulations", "/customs-regulations"),
    ("/", "/"),
])
def test_canonical_route_thumua(raw, expected):
    assert canonical_route(raw, int(UiApp.THUMUA)) == expected


def test_canonical_route_v2_giu_nguyen():
    assert canonical_route("/purchase-requests/:id", int(UiApp.ERP_V2)) == "/purchase-requests/:id"


def test_canonical_route_sau_normalize_khong_lot_id():
    route = canonical_route(normalize_route("/purchase-orders/129?q=abc"), int(UiApp.THUMUA))
    assert route == "/procurement/purchase-orders/:id"


def test_canonical_route_khong_vuot_120():
    long = "/purchase-requests/" + "a" * 110
    assert len(canonical_route(long, int(UiApp.THUMUA))) <= 120


# ── build_rows / store_batch ghi cột app + route đã quy ─────────────────────────

def test_build_rows_thumua():
    batch = UiEventBatch.model_validate({"app": 2, "events": [ev(route="/purchase-orders/55")]})
    rows = build_rows(batch, user_id=9, session_id=None, now=datetime(2026, 10, 20, 3, 0, 0))
    assert rows[0]["app"] == 2
    assert rows[0]["route_pattern"] == "/procurement/purchase-orders/:id"


def test_build_rows_v2_mac_dinh_app_1():
    rows = build_rows(UiEventBatch.model_validate({"events": [ev(route="/procurement/purchase-orders/5")]}),
                      user_id=9, session_id=None)
    assert rows[0]["app"] == 1
    assert rows[0]["route_pattern"] == "/procurement/purchase-orders/:id"


def test_store_batch_luu_cot_app(db):
    u, _ = make_person(db,"T1")
    store_batch(db, UiEventBatch.model_validate({"app": 2, "events": [ev(), ev(type=3, form=1)]}), u.id, None)
    rows = db.query(UiEvent).order_by(UiEvent.id).all()
    assert [r.app for r in rows] == [2, 2]
    assert rows[1].form_key == int(UiForm.PURCHASE_REQUEST)


def test_api_nhan_lo_thumua(db, client_as):
    u, _ = make_person(db,"T2")
    app_settings._cache["usage_tracking_enabled"] = "true"
    r = client_as(u).post(URL, json={"app": 2, "events": [ev(route="/survey-requests/new", type=3, form=2)]})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["accepted"] == 1
    row = db.query(UiEvent).one()
    assert (row.app, row.route_pattern, row.form_key) == (2, "/procurement/survey-requests/new", 2)


def test_api_app_la_422(db, client_as):
    u, _ = make_person(db,"T3")
    r = client_as(u).post(URL, json={"app": 5, "events": [ev()]})
    assert r.status_code == 422
    assert db.query(UiEvent).count() == 0


# ── tách theo app ───────────────────────────────────────────────────────────────

def test_split_by_app_dem_dung(db):
    (u1, _), (u2, _) = make_person(db, "S1"), make_person(db, "S2")
    at = datetime(2026, 10, 19, 2, 0, 0)   # 09:00 VN ngày 19/10
    for e in (add_ui(db, u1, at, int(UiEventType.PAGE_VIEW), "/procurement/purchase-orders/:id"),
              add_ui(db, u1, at, int(UiEventType.FORM_OPEN), "/procurement/purchase-orders/new", form=3)):
        e.app = 1
    for e in (add_ui(db, u1, at, int(UiEventType.PAGE_VIEW), "/procurement/purchase-requests/:id"),
              add_ui(db, u2, at, int(UiEventType.FORM_SUBMIT), "/procurement/purchase-requests/new", form=1),
              add_ui(db, u2, at, int(UiEventType.CLIENT_ERROR), "/procurement/purchase-requests/:id")):
        e.app = 2
    #  ngoài kỳ: không tính
    add_ui(db, u2, at - timedelta(days=5), int(UiEventType.PAGE_VIEW), "/x").app = 2
    db.commit()
    out = app_split_service.split_by_app(db, date(2026, 10, 19), date(2026, 10, 19))
    by = {i["app"]: i for i in out["items"]}
    assert set(by) == {1, 2}
    assert (by[1]["events"], by[1]["users"], by[1]["page_views"], by[1]["form_open"]) == (2, 1, 1, 1)
    assert (by[2]["events"], by[2]["users"], by[2]["page_views"], by[2]["form_submit"], by[2]["client_errors"]) == (3, 2, 1, 1, 1)
    assert by[2]["label"] == "Thu mua (app cũ)"


def test_split_by_app_rong_van_du_hai_dong(db):
    out = app_split_service.split_by_app(db, date(2026, 1, 1), date(2026, 1, 7))
    assert [i["app"] for i in out["items"]] == [1, 2]
    assert all(i["events"] == 0 for i in out["items"])


def test_api_by_app_co_gac_va_nam_truoc_user_id(db, client_as):
    u, _ = make_person(db, "S3")
    r = client_as(u).get("/api/usage-profiles/by-app?preset=this_month")
    #  người thường: gác kép (báo cáo + setting.read) chặn → 401/403; KHÔNG được rơi vào `/{user_id}`
    #  (422 vì "by-app" không phải số) — nghĩa là đường khai đúng chỗ, trước đường tham số
    assert r.status_code in (401, 403), r.text


# ── mã ở frontend/src/telemetry/ui-event-codes.ts khớp Python ───────────────────

_MOUNT = Path("/app/thumua-src")


def _thumua_codes() -> Path | None:
    rel = Path("telemetry") / "ui-event-codes.ts"
    if (_MOUNT / rel).is_file():
        return _MOUNT / rel
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "frontend" / "src" / rel
        if candidate.is_file():
            return candidate
    return None


def _const_block(text: str, name: str) -> dict[str, int]:
    m = re.search(rf"export const {name} = \{{(.*?)\}} as const", text, re.S)
    assert m, f"không thấy {name}"
    return {k: int(v) for k, v in re.findall(r"(\w+):\s*(\d+)", m.group(1))}


def test_ma_thumua_khop_python():
    path = _thumua_codes()
    if path is None:
        pytest.skip("Không thấy frontend/src/telemetry — trong container cần mount /app/thumua-src (docker-compose.yml)")
    text = path.read_text(encoding="utf-8")
    assert _const_block(text, "UI_EVENT") == {t.name: int(t) for t in UiEventType}
    forms = _const_block(text, "UI_FORM_CODE")
    assert forms == {f.name: int(f) for f in UiForm if f.name in forms}
    assert {"PURCHASE_REQUEST", "QUOTE_REQUEST", "PURCHASE_ORDER"} <= set(forms)
    m = re.search(r"export const UI_APP_THUMUA = (\d+)", text)
    assert m and int(m.group(1)) == int(UiApp.THUMUA)
