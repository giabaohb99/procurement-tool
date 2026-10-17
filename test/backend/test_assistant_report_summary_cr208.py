"""ai-CR-208 — tool `report_summary` (K11 của doc/erp/21 §T1): một cửa 13 báo cáo gom sẵn cho Trợ lý / bot / cổng MCP.

Canh:
  - chưa được giao xem báo cáo → từ chối, KHÔNG chạm hàm route;
  - được giao mà thiếu quyền vai trò ở phân hệ gốc → từ chối, nói rõ thiếu gì;
  - số của tool KHỚP đúng phần `data` của đường `/summary` gọi qua HTTP thật (mua hàng, nghỉ phép, công việc);
  - report_key lạ → lỗi kèm danh sách mã hợp lệ;
  - cổng MCP: có trong danh sách chỉ đọc, `link` tuyệt đối, kèm `structuredContent`.
"""
import uuid
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.subject_match import SUBJECT_ROLE
from app.main import app
from app.modules.assistant import tools as T
from app.modules.assistant.tools import report_summary_tool as rs
from app.modules.employee.model import Employee
from app.modules.user.model import User

SEPT = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "previous"}


@pytest.fixture
def client_as(db):
    """Token GIẢ nhưng DUY NHẤT mỗi lần build — `ReportSummaryCacheMiddleware` cache `/summary` theo token
    (xem `test_phan_quyen_bao_cao_gac_duong.py`), dùng chung token là ăn lại response của bài khác."""
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _user(db, code: str, company_id: int = 0, department_id: int = 0) -> User:
    emp = Employee(code=code, full_name=f"Người {code}", company_id=company_id or None,
                   department_id=department_id or None, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@test.vn", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    return user


def _grant(cap_quyen, gan_bao_cao, user, entity: str, key: ReportKey):
    role = cap_quyen(user.id, entity, scope="all", read=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, key)
    return role


def _same_as_http(db, client_as, user, report_key: str, http_path: str, filters: dict) -> dict:
    out = T.run_tool(db, user, "report_summary", {"report_key": report_key, "filters": filters})
    assert "error" not in out, out
    res = client_as(user).get(http_path, params=filters)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    for k in ("period", "totals", "trend", "breakdowns", "notes"):
        assert out[k] == data[k], k
    assert out["meta"]["dimensions"] == data["meta"]["dimensions"]
    return out


# ── Lớp gác ───────────────────────────────────────────────────────────────────

def test_report_key_la_bao_loi_ro(db, seed):
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "report_summary", {"report_key": "bao_cao_ma"})
    assert "không hợp lệ" in out["error"] and "leave_usage (Tình hình nghỉ phép)" in out["error"]
    assert "work (Công việc & Dự án)" in out["error"]


def test_chua_duoc_giao_bao_cao_bi_tu_choi_khong_cham_route(db, cap_quyen, monkeypatch):
    user = _user(db, "RS01")
    cap_quyen(user.id, "leave_request", scope="all", read=True)          # có quyền vai trò, CHƯA được giao báo cáo
    monkeypatch.setitem(rs.REPORTS, "leave_usage", rs.ReportRoute(
        ReportKey.LEAVE_USAGE, lambda: pytest.fail("không được gọi route"), "/report/leave-usage"))
    out = T.run_tool(db, user, "report_summary", {"report_key": "leave_usage"})
    assert out["denied"] and "Tình hình nghỉ phép" in out["error"] and "tab Báo cáo" in out["error"]


def test_duoc_giao_bao_cao_nhung_thieu_quyen_vai_tro(db, gan_bao_cao):
    user = _user(db, "RS02")
    from app.core.subject_match import SUBJECT_EMPLOYEE

    gan_bao_cao(SUBJECT_EMPLOYEE, user.employee_id, ReportKey.LEAVE_USAGE)
    out = T.run_tool(db, user, "report_summary", {"report_key": "leave_usage"})
    assert out["denied"] and "leave_request" in out["error"] and "quyền vai trò" in out["error"]


def test_cong_or_cua_tien_do_mua_hang_chay_dung_dependency_cua_route(db, cap_quyen, gan_bao_cao):
    """Tiến độ mua hàng gác OR (purchase_order.read HOẶC purchase_request.read) — tool chạy lại đúng cổng đó."""
    user = _user(db, "RS03")
    _grant(cap_quyen, gan_bao_cao, user, "purchase_request", ReportKey.PURCHASE_PROGRESS)
    out = T.run_tool(db, user, "report_summary", {"report_key": "purchase_progress", "filters": SEPT})
    assert "error" not in out, out
    assert out["label"] == "Tiến độ mua hàng" and out["link"] == "/report/purchase-progress"


# ── Số khớp đường /summary ────────────────────────────────────────────────────

def test_mua_hang_khop_summary(db, seed, cap_quyen, gan_bao_cao, client_as, monkeypatch):
    from app.modules.payable.model import Payable
    from app.modules.purchase_order.model import POItem, PurchaseOrder
    from app.modules.report import service as report_service

    monkeypatch.setattr(report_service, "report_dept_scope", lambda db_, u: None)
    cid = seed.company_id
    for d, qty in (("2026-09-10", 10), ("2026-08-15", 5)):
        po = PurchaseOrder(code=f"PO-{d}", company_id=cid, order_date=d, status="approved", supplier_code="NCC A",
                           supplier_name="NCC A", nspt="NV A", department="Kho")
        db.add(po)
        db.flush()
        db.add(POItem(po_id=po.id, product_code="SP1", item_group="Nhãn", qty_order=qty, price=100, vat=10,
                      exchange_rate=1))
    db.add(Payable(company_id=cid, incur_date="2026-09-05", total=300, remaining=300, status="unpaid", due_date="",
                   supplier_code="NCC A", supplier_name="NCC A", po_id=0))
    db.commit()
    user = _user(db, "RS10")
    _grant(cap_quyen, gan_bao_cao, user, "report", ReportKey.PURCHASE_REPORT)

    out = _same_as_http(db, client_as, user, "purchase_report", "/api/reports/procurement/summary", SEPT)
    assert out["totals"]["current"]["order_value"] == pytest.approx(1100.0)       # 10 × 100 × 1,1
    assert out["currency"] == "VND" and out["link"] == "/report/purchase"
    vat = {m["key"]: m.get("vat") for m in out["meta"]["metrics"]}
    assert vat["order_value"] == "sau VAT"


def test_nghi_phep_khop_summary(db, seed, cap_quyen, gan_bao_cao, client_as):
    from app.modules.leave.catalog_model import LeaveType
    from app.modules.leave.constants import LR_APPROVED
    from app.modules.leave.request_model import LeaveRequest

    user = _user(db, "RS20", seed.company_id, seed.dept_id)
    lt = LeaveType(code="PN", name="Phép năm")
    db.add(lt)
    db.flush()
    for i, day in enumerate((5, 12)):
        db.add(LeaveRequest(code=f"NP-RS-{i}", company_id=seed.company_id, department_id=seed.dept_id,
                            employee_id=user.employee_id, created_by=user.id, leave_type_id=lt.id,
                            from_date=date(2026, 9, day), to_date=date(2026, 9, day), status=LR_APPROVED,
                            is_deleted=False))
    db.commit()
    _grant(cap_quyen, gan_bao_cao, user, "leave_request", ReportKey.LEAVE_USAGE)

    out = _same_as_http(db, client_as, user, "leave_usage", "/api/leave-requests/summary", SEPT)
    assert out["totals"]["current"]["requests"] == 2


def test_cong_viec_khop_summary_va_nhan_so_khoa(db, cap_quyen, gan_bao_cao, client_as):
    from app.modules.work import list_service, schema, task_service
    from app.modules.work.membership_service import Actor
    from app.modules.work.task_model import WorkTask

    user = _user(db, "RS30")
    _grant(cap_quyen, gan_bao_cao, user, "work_task", ReportKey.WORK)
    owner = Actor(user_id=user.id, employee_id=user.employee_id, company_id=0)
    lid = list_service.create_list(db, owner, schema.ListCreate(name="Dự án RS"))["id"]
    for _ in range(3):
        tid = task_service.create_task(db, owner, schema.TaskCreate(list_id=lid, title="Việc"))["id"]
        db.get(WorkTask, tid).created_at = datetime(2026, 9, 10, 3, 0)
    db.commit()

    filters = dict(SEPT, group_by="list")
    out = _same_as_http(db, client_as, user, "work", "/api/work/summary", filters)
    assert out["totals"]["current"]["created"] == 3
    assert out["total"] == 1 and out["has_more"] is False and out["groups"][0]["label"] == "Dự án RS"
    #  Nhận cả số khóa (13), bộ lọc ngoài danh sách thì báo lại, không lặng lẽ nuốt.
    by_number = T.run_tool(db, user, "report_summary", {"report_key": 13, "filters": dict(SEPT, ma_la="x")})
    assert by_number["report_key"] == "work" and by_number["ignored_filters"] == ["ma_la"]
    assert by_number["totals"] == out["totals"]


def test_tran_so_nhom(db, cap_quyen, gan_bao_cao, monkeypatch):
    user = _user(db, "RS40")
    _grant(cap_quyen, gan_bao_cao, user, "work_task", ReportKey.WORK)
    monkeypatch.setattr(rs, "call_summary_route", lambda fn, db_, u, p: {
        "period": {}, "meta": {}, "totals": {}, "trend": [], "breakdowns": {}, "notes": [],
        "groups": [{"key": i} for i in range(rs.GROUP_CAP + 7)]})
    out = T.run_tool(db, user, "report_summary", {"report_key": "work"})
    assert len(out["groups"]) == rs.GROUP_CAP and out["total"] == rs.GROUP_CAP + 7 and out["has_more"] is True


def test_moi_khoa_bao_cao_deu_co_route_va_dung_khoa_gac():
    """13 ReportKey đều mở; hàm route nạp được và chính là hàm đang gác đúng khóa đó trên app."""
    assert {r.key for r in rs.REPORTS.values()} == set(ReportKey)
    gated = {}
    for route in app.routes:
        for dep in getattr(route, "dependencies", []) or []:
            key = getattr(dep.dependency, "report_key", None)
            if key is not None and route.path.endswith("/summary"):
                gated[route.endpoint] = key
    for name, r in rs.REPORTS.items():
        assert gated.get(r.load()) == r.key, name


# ── Cổng MCP ──────────────────────────────────────────────────────────────────

def test_mcp_mo_cho_khoa_doc_link_tuyet_doi_va_structured(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import erp, mcp, mcp_keys

    assert "report_summary" in mcp.READ_TOOLS and not mcp.is_write_tool("report_summary")
    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    monkeypatch.setattr(erp, "run_tool", lambda db_, u, name, args: {
        "report_key": "work", "link": "/report/work", "totals": {"current": {"created": 3}}})
    owner = SimpleNamespace(id=1, is_active=True)
    key = SimpleNamespace(scope=mcp_keys.SCOPE_READ)
    resp = mcp.handle(db, owner, key, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                       "params": {"name": "report_summary", "arguments": {"report_key": "work"}}})
    result = resp["result"]
    assert result["structuredContent"]["link"] == "https://deverp.degoholding.vn/report/work"
    assert result["structuredContent"]["totals"]["current"]["created"] == 3
    assert '"https://deverp.degoholding.vn/report/work"' in result["content"][0]["text"]
