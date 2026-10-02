"""Phase 03 — soi `app.routes` + gác HTTP của 26 đường `/summary`+`/summary/export`.

Khác test cũ gọi thẳng hàm controller: ở đây BẮT BUỘC đi qua `TestClient` vì
`require_report` gắn ở `dependencies=[...]` của route — gọi hàm Python trực
tiếp sẽ KHÔNG chạy qua gác này.
"""
import uuid

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.subject_match import SUBJECT_EMPLOYEE, SUBJECT_ROLE
from app.main import app
from app.modules.employee.model import Employee
from app.modules.user.model import User

#  26 đường — khóa mong đợi + entity giữ nguyên gác quyền (bảng của phase-02).
GATED: dict[str, ReportKey] = {
    "/api/reports/procurement/summary": ReportKey.PURCHASE_REPORT,
    "/api/reports/procurement/summary/export": ReportKey.PURCHASE_REPORT,
    "/api/reports/pr-lines/summary": ReportKey.PR_LINES,
    "/api/reports/pr-lines/summary/export": ReportKey.PR_LINES,
    "/api/survey-progress/summary": ReportKey.SURVEY_PROGRESS,
    "/api/survey-progress/summary/export": ReportKey.SURVEY_PROGRESS,
    "/api/purchase-progress/summary": ReportKey.PURCHASE_PROGRESS,
    "/api/purchase-progress/summary/export": ReportKey.PURCHASE_PROGRESS,
    "/api/survey-report/summary": ReportKey.SURVEY_REPORT,
    "/api/survey-report/summary/export": ReportKey.SURVEY_REPORT,
    "/api/employees/summary": ReportKey.HR_HEADCOUNT,
    "/api/employees/summary/export": ReportKey.HR_HEADCOUNT,
    "/api/leave-requests/summary": ReportKey.LEAVE_USAGE,
    "/api/leave-requests/summary/export": ReportKey.LEAVE_USAGE,
    "/api/leave-balances/summary": ReportKey.LEAVE_BALANCE,
    "/api/leave-balances/summary/export": ReportKey.LEAVE_BALANCE,
    "/api/vehicle-bookings/summary": ReportKey.VEHICLE_BOOKING,
    "/api/vehicle-bookings/summary/export": ReportKey.VEHICLE_BOOKING,
    "/api/seal-requests/summary": ReportKey.SEAL_REQUEST,
    "/api/seal-requests/summary/export": ReportKey.SEAL_REQUEST,
    "/api/documents/summary": ReportKey.DOCUMENT,
    "/api/documents/summary/export": ReportKey.DOCUMENT,
    "/api/approvals/summary": ReportKey.APPROVAL,
    "/api/approvals/summary/export": ReportKey.APPROVAL,
    "/api/work/summary": ReportKey.WORK,
    "/api/work/summary/export": ReportKey.WORK,
}

#  KHÔNG thuộc phân hệ Báo cáo — đã grep, không gán khóa nào (bảng phase-02).
NOT_REPORT = {
    "/api/payables/summary",
    "/api/system-logs/summary",
    "/api/customs/imports/{bid}/rows/summary",
    "/api/leave-balances/tools/summary",
}

#  (khóa, entity giữ nguyên gác quyền, đường summary, đường export).
ROUTE_SPECS = [
    (ReportKey.PURCHASE_REPORT, "report",
     "/api/reports/procurement/summary", "/api/reports/procurement/summary/export"),
    (ReportKey.PR_LINES, "report",
     "/api/reports/pr-lines/summary", "/api/reports/pr-lines/summary/export"),
    (ReportKey.SURVEY_PROGRESS, "survey_request",
     "/api/survey-progress/summary", "/api/survey-progress/summary/export"),
    (ReportKey.PURCHASE_PROGRESS, "purchase_request",
     "/api/purchase-progress/summary", "/api/purchase-progress/summary/export"),
    (ReportKey.SURVEY_REPORT, "survey",
     "/api/survey-report/summary", "/api/survey-report/summary/export"),
    (ReportKey.HR_HEADCOUNT, "employee",
     "/api/employees/summary", "/api/employees/summary/export"),
    (ReportKey.LEAVE_USAGE, "leave_request",
     "/api/leave-requests/summary", "/api/leave-requests/summary/export"),
    (ReportKey.LEAVE_BALANCE, "leave_balance",
     "/api/leave-balances/summary", "/api/leave-balances/summary/export"),
    (ReportKey.VEHICLE_BOOKING, "vehicle_booking",
     "/api/vehicle-bookings/summary", "/api/vehicle-bookings/summary/export"),
    (ReportKey.SEAL_REQUEST, "seal_request",
     "/api/seal-requests/summary", "/api/seal-requests/summary/export"),
    (ReportKey.DOCUMENT, "document",
     "/api/documents/summary", "/api/documents/summary/export"),
    (ReportKey.APPROVAL, "approval_flow",
     "/api/approvals/summary", "/api/approvals/summary/export"),
    (ReportKey.WORK, "work_task",
     "/api/work/summary", "/api/work/summary/export"),
]

PRESET_QS = {"preset": "this_month", "compare": "none"}


def _summary_routes() -> list[APIRoute]:
    return [r for r in app.routes if isinstance(r, APIRoute)
            and (r.path.endswith("/summary") or r.path.endswith("/summary/export"))]


def _route_report_key(path: str):
    for r in _summary_routes():
        if r.path != path:
            continue
        for dep in r.dependencies:
            if hasattr(dep.dependency, "report_key"):
                return dep.dependency.report_key
    return None


# ── Soi app.routes: mọi /summary phải được phân loại ────────────────────────

def test_moi_duong_summary_duoc_phan_loai_gated_hoac_not_report():
    found = {r.path for r in _summary_routes()}
    classified = set(GATED) | NOT_REPORT
    missing = found - classified
    assert missing == set(), (
        f"Đường /summary mới chưa phân loại vào GATED hoặc NOT_REPORT: {sorted(missing)}")
    stale = classified - found
    assert stale == set(), f"Khai trong danh sách nhưng route không còn tồn tại: {sorted(stale)}"


def test_moi_report_key_gac_dung_hai_duong():
    from collections import Counter
    counts = Counter(GATED.values())
    assert counts == {k: 2 for k in ReportKey}, counts


def test_khoa_gac_tren_route_khop_bang_khai():
    for path, expected_key in GATED.items():
        assert _route_report_key(path) == expected_key, (
            f"{path}: route gác khóa {_route_report_key(path)!r}, bảng khai {expected_key!r}")


def test_duong_khong_thuoc_bao_cao_khong_gac_khoa_nao():
    for path in NOT_REPORT:
        assert _route_report_key(path) is None, path


# ── Gọi thật qua TestClient — gác kép + cách ly khóa ─────────────────────────

@pytest.fixture
def client_as(db):
    """⚠️ `core/report_cache.ReportSummaryCacheMiddleware` (gói A2) cache GET
    `/summary` theo khóa `(path, query, sha256(Bearer token))` — một HIT bỏ
    qua HẲN mọi dependency của route, kể cả `require_report` mới thêm.
    `dependency_overrides` giả `get_current_user` KHÔNG đổi header thật, nên
    nếu không gắn token GIẢ NHƯNG DUY NHẤT ở đây, mọi test (và mọi tệp test
    khác gọi 13 đường `/summary` này) sẽ CHIA SẺ cùng một khóa cache (token
    rỗng) qua Redis thật (`REPORT_CACHE_TTL=60s`) — một bài trả 200 sẽ làm
    bài kế tiếp (đứng vòi 403) ăn lại đúng response cũ, SAI mà không ai thấy
    lỗi gì (guard thậm chí không được gọi). Giá trị token không ảnh hưởng xác
    thực (đã giả `get_current_user`), chỉ cần DUY NHẤT mỗi lượt build client.
    """
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        token = f"test-{uuid.uuid4().hex}"
        return TestClient(app, headers={"Authorization": f"Bearer {token}"})

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _new_user(db, code: str) -> User:
    emp = Employee(code=code, full_name=f"Người {code}", is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code}@test.vn", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return user


@pytest.mark.parametrize("key,entity,summary_path,export_path", ROUTE_SPECS)
def test_chua_gan_403_gan_qua_vai_tro_200(db, cap_quyen, gan_bao_cao, client_as,
                                         key, entity, summary_path, export_path):
    user = _new_user(db, f"U{int(key)}")
    role = cap_quyen(user.id, entity, scope="all", read=True, export=True)
    client = client_as(user)

    resp = client.get(summary_path, params=PRESET_QS)
    assert resp.status_code == 403, (summary_path, resp.text)

    gan_bao_cao(SUBJECT_ROLE, role.id, key)
    resp = client.get(summary_path, params=PRESET_QS)
    assert resp.status_code == 200, (summary_path, resp.text)

    resp = client.get(export_path, params=PRESET_QS)
    assert resp.status_code == 200, (export_path, resp.text)


@pytest.mark.parametrize("key,entity,summary_path,export_path", ROUTE_SPECS)
def test_gan_bao_cao_nhung_thieu_quyen_entity_van_403(db, gan_bao_cao, client_as,
                                                      key, entity, summary_path, export_path):
    """Gác KÉP: được GÁN xem báo cáo nhưng KHÔNG có quyền `entity` nào cả (không
    gọi `cap_quyen`) -> vẫn 403 ở cửa quyền phân hệ gốc."""
    user = _new_user(db, f"NOENT{int(key)}")
    gan_bao_cao(SUBJECT_EMPLOYEE, user.employee_id, key)
    resp = client_as(user).get(summary_path, params=PRESET_QS)
    assert resp.status_code == 403, (summary_path, resp.text)


@pytest.mark.parametrize("key,entity,summary_path,export_path", ROUTE_SPECS)
def test_co_read_thieu_export_van_403_tren_export(db, cap_quyen, gan_bao_cao, client_as,
                                                  key, entity, summary_path, export_path):
    user = _new_user(db, f"RDONLY{int(key)}")
    role = cap_quyen(user.id, entity, scope="all", read=True, export=False)
    gan_bao_cao(SUBJECT_ROLE, role.id, key)
    client = client_as(user)

    assert client.get(summary_path, params=PRESET_QS).status_code == 200
    assert client.get(export_path, params=PRESET_QS).status_code == 403


def test_gan_khoa_nay_khong_mo_khoa_khac(db, cap_quyen, gan_bao_cao, client_as):
    """Gán `WORK` không mở `DOCUMENT` — kể cả khi tài khoản thừa quyền `document`."""
    user = _new_user(db, "CROSSKEY")
    role_doc = cap_quyen(user.id, "document", scope="all", read=True, export=True)
    gan_bao_cao(SUBJECT_ROLE, role_doc.id, ReportKey.WORK)

    resp = client_as(user).get("/api/documents/summary", params=PRESET_QS)
    assert resp.status_code == 403, resp.text
