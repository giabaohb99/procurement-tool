"""bao-CR-414 GĐ4 — CÔNG NỢ theo phòng: cột ẩn `department_id` trên khoản nợ + phiếu YCTT.

Luật đã chốt:
  · Khoản nợ sinh ra mang phòng ĐANG XỬ LÝ đơn (`handling_dept_of(po)`): phòng được nhờ nếu có,
    không thì phòng lập đơn. Nợ cũ giữ 0, KHÔNG backfill.
  · Bậc `dept_proc` / loại trừ phòng bắt được nợ của phòng nhờ khai `dept_id` ở SCOPE_FIELDS.
  · Thẻ tổng hợp trả HAI bộ số: bốn khóa gốc = "Phần của tôi", `all` = "Tổng nợ NCC", `partial`.
  · YCTT: nợ của HAI phòng khác nhau không đi chung một phiếu; nợ cũ (0) đi với phòng nào cũng
    được; phiếu gõ tay lấy phòng của người lập.
  · Tiền treo cấn vào nợ của phòng nào thì chỉ lấy treo do phòng đó (hoặc phiếu cũ) lập.
  · Tool trợ lý: `summary_all` chỉ xuất hiện khi người hỏi thấy một phần.
"""
import json

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import apply_scope
from app.modules.assistant import tools as T
from app.modules.category_assignee.service import handling_dept_of
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.payable import controller as pay_ctl
from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable
from app.modules.payment_request import service as prq_service
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole, UserScope


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


@pytest.fixture
def two_departments(db, seed):
    factory = Department(code="NM4", name="Nhà máy", company_id=seed.company_id, is_active=True)
    purchasing = Department(code="TM4", name="Thu mua", company_id=seed.company_id, is_active=True)
    db.add_all([factory, purchasing])
    db.flush()
    return factory.id, purchasing.id


_counter = {"n": 0}


def _viewer(db, seed, entity: str, scope: str, dept_id: int | None, *,
            exclude_dept_ids: tuple[int, ...] = ()):
    """Người xem có `entity.read` bậc `scope`, ở phòng `dept_id`, không dính khoản nợ nào."""
    _counter["n"] += 1
    n = _counter["n"]
    emp = Employee(code=f"C414{n:02d}", full_name=f"Người xem {n}", company_id=seed.company_id,
                   department_id=dept_id or 0, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"C414{n:02d}", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    role = Role(code=f"RC414{n:02d}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope, can_read=True))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    for did in exclude_dept_ids:
        db.add(UserScope(user_id=user.id, role_id=role.id, entity="", dim="department",
                         value=str(did), is_exclude=True))
    db.flush()
    perm_cache_clear()
    return user


def _add_payable(db, seed, po_code: str, dept_id: int, total: float = 1000, paid: float = 0,
                 supplier_code: str = "NCCA") -> Payable:
    p = Payable(company_id=seed.company_id, department_id=dept_id, supplier_code=supplier_code,
                supplier_name="NCC Anpha", source_type="goods", po_code=po_code,
                incur_date="2026-08-05", period="2026", due_date="2026-08-20",
                total=total, paid_amount=paid, remaining=total - paid,
                status="paid" if paid >= total else ("partial" if paid else "unpaid"),
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.flush()
    return p


def _seed_three_payables(db, seed, factory_id, purchasing_id):
    """Ba khoản nợ cùng NCC: của nhà máy (1000) · của thu mua (500) · nợ cũ chưa gắn phòng (200)."""
    _add_payable(db, seed, "PO-NM", factory_id, total=1000)
    _add_payable(db, seed, "PO-TM", purchasing_id, total=500)
    _add_payable(db, seed, "PO-CU", 0, total=200)
    db.commit()


def _visible_po_codes(db, user, model=Payable, entity="payable") -> set[str]:
    profile = get_perm_profile(db, user)
    rows = apply_scope(db.query(model), model, entity, user, profile).all()
    return {r.po_code if model is Payable else r.code for r in rows}


def _request(qs: str = "year=all") -> Request:
    return Request({"type": "http", "method": "GET", "path": "/api/payables/summary",
                    "query_string": qs.encode(), "headers": []})


def _summary(db, user, qs: str = "year=all") -> dict:
    """Gọi thẳng route /summary; `success()` trả JSONResponse nên bóc phong bì lấy `data`."""
    return json.loads(pay_ctl.summary(_request(qs), db, user).body)["data"]


# ── Khoản nợ mang phòng đang xử lý đơn ──────────────────────────────────────────────────

def test_payable_upsert_stores_department_of_the_order(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    po = PurchaseOrder(code="PO-NHO", company_id=seed.company_id, department_id=purchasing_id,
                       handler_dept_id=factory_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                       order_date="2026-08-05", status="approved", created_by=seed.u_nstm_id)
    db.add(po)
    db.flush()
    assert handling_dept_of(po) == factory_id      # phòng được nhờ thắng phòng lập đơn

    p = pay_service.upsert(db, source_type="goods", ref_id=77, company_id=seed.company_id,
                           supplier_code="NCCA", supplier_name="NCC Anpha", po_id=po.id,
                           po_code=po.code, invoice_no="", incur_date="2026-08-05", amount=100,
                           vat=8, due_days=30, user_id=seed.u_nstm_id,
                           department_id=handling_dept_of(po))
    assert p.department_id == factory_id

    # Đổi phòng xử lý rồi lưu lại đơn -> khoản nợ đi theo (upsert cùng ref).
    p2 = pay_service.upsert(db, source_type="goods", ref_id=77, company_id=seed.company_id,
                            supplier_code="NCCA", supplier_name="NCC Anpha", po_id=po.id,
                            po_code=po.code, invoice_no="", incur_date="2026-08-05", amount=100,
                            vat=8, due_days=30, user_id=seed.u_nstm_id, department_id=0)
    assert p2.id == p.id and p2.department_id == 0


def test_payable_upsert_without_department_keeps_zero(db, seed):
    """Người gọi cũ không truyền phòng -> 0, đúng hành vi trước GĐ4."""
    p = pay_service.upsert(db, source_type="goods", ref_id=78, company_id=seed.company_id,
                           supplier_code="NCCA", supplier_name="NCC Anpha", po_id=0,
                           po_code="PO-X", invoice_no="", incur_date="2026-08-05", amount=100,
                           vat=0, due_days=30, user_id=seed.u_nstm_id)
    assert p.department_id == 0


# ── Phạm vi trên công nợ + YCTT ───────────────────────────────────────────────────────

def test_dept_proc_viewer_sees_only_own_department_payables(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "payable", "dept_proc", factory_id)
    assert _visible_po_codes(db, user) == {"PO-NM"}


def test_old_untagged_payables_hidden_from_department_tier_but_visible_to_all(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    dept_user = _viewer(db, seed, "payable", "dept", purchasing_id)
    assert _visible_po_codes(db, dept_user) == {"PO-TM"}
    full_user = _viewer(db, seed, "payable", "all", None)
    assert _visible_po_codes(db, full_user) == {"PO-NM", "PO-TM", "PO-CU"}


def test_excluded_department_payables_are_hidden(db, seed, two_departments):
    """Thu mua trừ nhà máy: bậc `all` + loại trừ phòng Nhà máy -> không thấy nợ của nhà máy."""
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "payable", "all", purchasing_id, exclude_dept_ids=(factory_id,))
    assert _visible_po_codes(db, user) == {"PO-TM", "PO-CU"}


def test_dept_proc_viewer_sees_only_own_department_payment_requests(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    for code, dept in (("YCTT-NM", factory_id), ("YCTT-TM", purchasing_id), ("YCTT-CU", 0)):
        db.add(PaymentRequest(code=code, supplier_code="NCCA", supplier_name="NCC Anpha",
                              company_id=seed.company_id, department_id=dept, source_type="goods",
                              request_date="2026-08-25", status="draft", total=100,
                              created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    user = _viewer(db, seed, "payment_request", "dept_proc", factory_id)
    assert _visible_po_codes(db, user, PaymentRequest, "payment_request") == {"YCTT-NM"}


# ── Thẻ tổng hợp: hai bộ số ────────────────────────────────────────────────────────────

def test_summary_returns_my_part_and_supplier_total_when_scoped(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "payable", "dept_proc", factory_id)
    out = _summary(db, user)
    assert out["total"] == 1000.0 and out["remaining"] == 1000.0     # phần của tôi
    assert out["all"]["total"] == 1700.0 and out["all"]["remaining"] == 1700.0
    assert out["partial"] is True


def test_summary_is_not_partial_for_full_scope(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "payable", "all", None)
    out = _summary(db, user)
    assert out["total"] == 1700.0 and out["all"]["total"] == 1700.0
    assert out["partial"] is False


def test_summary_total_respects_screen_filters(db, seed, two_departments):
    """`all` đi cùng bộ lọc màn hình (NCC, kỳ...), chỉ bỏ lớp phạm vi."""
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    _add_payable(db, seed, "PO-B", purchasing_id, total=9999, supplier_code="NCCB")
    db.commit()
    user = _viewer(db, seed, "payable", "dept_proc", factory_id)
    out = _summary(db, user, "year=all&supplier_code=NCCA")
    assert out["all"]["total"] == 1700.0


# ── YCTT: gom nợ theo phòng ────────────────────────────────────────────────────────────

def _create_from(db, seed, payables):
    data = PRequestCreate(request_date="2026-08-20",
                          lines=[LineIn(payable_id=p.id, amount=float(p.remaining)) for p in payables])
    return prq_service.create_requests(db, data, seed.u_req_id)


def test_payment_request_takes_department_from_its_payables(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    a = _add_payable(db, seed, "PO-NM1", factory_id, total=300)
    old = _add_payable(db, seed, "PO-CU1", 0, total=200)       # nợ cũ đi chung được
    db.commit()
    reqs = _create_from(db, seed, [a, old])
    assert len(reqs) == 1 and reqs[0].department_id == factory_id


def test_payment_request_blocks_payables_of_two_departments(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    a = _add_payable(db, seed, "PO-NM2", factory_id, total=300)
    b = _add_payable(db, seed, "PO-TM2", purchasing_id, total=300)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        _create_from(db, seed, [a, b])
    assert exc.value.status_code == 400 and "HAI phòng" in exc.value.detail


def test_manual_payment_request_uses_creator_department(db, seed):
    """Phiếu gõ tay không gắn khoản nợ -> phòng của người lập (seed.emp_req thuộc seed.dept_id)."""
    data = PRequestCreate(request_date="2026-08-20", supplier_code="NX",
                          lines=[LineIn(po_code="PO-TAY", invoice_no="HD1", amount=100)])
    req = prq_service.create_requests(db, data, seed.u_req_id)[0]
    assert req.department_id == seed.dept_id


# ── Tiền treo theo phòng ───────────────────────────────────────────────────────────────

def _add_prepaid(db, seed, code: str, dept_id: int, amount: float = 800):
    req = PaymentRequest(code=code, supplier_code="NCCA", supplier_name="NCC Anpha",
                         company_id=seed.company_id, department_id=dept_id, source_type="goods",
                         request_date="2026-08-25", prepay=1, total=amount, status="paid",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, po_code="", amount=amount,
                              created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()
    return req


def test_hanging_lines_filtered_by_department(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _add_prepaid(db, seed, "TREO-NM", factory_id)
    _add_prepaid(db, seed, "TREO-TM", purchasing_id)
    _add_prepaid(db, seed, "TREO-CU", 0)
    db.commit()
    codes = {req.code for req, _ in prq_service.get_hanging_lines(db, "NCCA", "goods", "",
                                                                    department_id=factory_id)}
    assert codes == {"TREO-NM", "TREO-CU"}          # treo cũ chưa gắn phòng vẫn dùng được
    everything = {req.code for req, _ in prq_service.get_hanging_lines(db, "NCCA", "goods", "")}
    assert everything == {"TREO-NM", "TREO-TM", "TREO-CU"}


def test_offset_supplier_hanging_only_uses_own_department_prepayment(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _add_prepaid(db, seed, "TREO-TM-ONLY", purchasing_id, amount=800)
    debt = _add_payable(db, seed, "PO-NM3", factory_id, total=500)
    db.commit()
    # Treo của Thu mua không cấn vào nợ Nhà máy -> với Nhà máy, NCC này "không còn tiền treo".
    with pytest.raises(HTTPException) as exc:
        prq_service.offset_supplier_hanging(db, debt, 0, seed.u_req_id)
    assert exc.value.status_code == 400 and "không còn tiền treo" in exc.value.detail


# ── Trợ lý AI ───────────────────────────────────────────────────────────────────────────

def test_payable_tool_reports_supplier_total_when_viewer_sees_a_part(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "payable", "dept_proc", factory_id)
    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out["summary"]["remaining"] == 1000.0
    assert out["summary_all"]["remaining"] == 1700.0 and out["summary_all"]["count"] == 3
    assert "scope_note" in out
    assert {i["po_code"] for i in out["items"]} == {"PO-NM"}   # không lộ khoản ngoài phạm vi


def test_payable_tool_omits_supplier_total_for_full_scope(db, seed, two_departments, cap_quyen):
    factory_id, purchasing_id = two_departments
    _seed_three_payables(db, seed, factory_id, purchasing_id)
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out["summary"]["remaining"] == 1700.0
    assert "summary_all" not in out and "scope_note" not in out


def test_doc_tool_reports_handler_department(db, seed, two_departments, cap_quyen):
    factory_id, purchasing_id = two_departments
    po = PurchaseOrder(code="PO-NHO-2", company_id=seed.company_id, department_id=purchasing_id,
                       handler_dept_id=factory_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                       order_date="2026-08-05", status="approved", created_by=seed.u_nstm_id)
    db.add(po)
    db.commit()
    cap_quyen(seed.u_req_id, "purchase_order", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "procurement_doc_read", {"entity": "purchase_order", "code": "PO-NHO-2"})
    assert out["header"]["handler_dept_id"] == factory_id
    assert out["header"]["handler_dept"] == "Nhà máy"
