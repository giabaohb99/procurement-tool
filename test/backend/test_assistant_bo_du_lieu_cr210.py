"""ai-CR-210 — sổ bộ dữ liệu cho AI (K12, tầng T2 doc/erp/21 §5.5): khuôn `assistant/datasets/` + tool `dataset_query`.

Canh:
  - phạm vi TỪNG bộ: người phòng A không ra số phòng B (công nợ, yêu cầu thanh toán); phiếu đã xóa mềm không tính;
  - cổng quyền: thiếu entity → denied nói rõ; chiều NCC của bộ mua hàng đòi supplier.read; bộ mua hàng đòi quyền xem
    Báo cáo mua hàng;
  - trần nhóm: vượt `limit` → truncated + has_more + note; limit kẹp ở 500;
  - không có đường sinh SQL: chỉ số / chiều / bộ lọc ngoài danh mục bị từ chối, bộ lọc lạ báo `ignored_filters`;
  - `analytics_query` cũ chạy qua khuôn mới mà vẫn ra đúng số (bài cũ ở test_assistant_tools.py giữ nguyên).
"""
from datetime import timedelta

import pytest

from app.core.vn_time import vn_today
from app.modules.assistant import datasets
from app.modules.assistant import tools as T
from app.modules.department.model import Department
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.user.model import User


@pytest.fixture
def report_ok(monkeypatch):
    from app.modules.report_access import service as ra

    monkeypatch.setattr(ra, "can_view_report", lambda db_, u, key, profile=None: True)


@pytest.fixture
def other_dept(db, seed):
    d = Department(code="DEPT02", name="Phòng Khác", company_id=seed.company_id, is_active=True)
    db.add(d)
    db.commit()
    return d


def _user(db, seed):
    return db.get(User, seed.u_req_id)


def _q(db, user, dataset, **args):
    return T.run_tool(db, user, "dataset_query", {"dataset": dataset, **args})


def _payables(db, seed, other_dept):
    past = (vn_today() - timedelta(days=5)).isoformat()
    future = (vn_today() + timedelta(days=30)).isoformat()
    rows = [
        Payable(company_id=seed.company_id, department_id=seed.dept_id, supplier_code="A", supplier_name="NCC A",
                incur_date="2026-09-05", due_date=past, amount=1000, vat=100, total=1100, paid_amount=0, remaining=1100,
                status="unpaid"),
        Payable(company_id=seed.company_id, department_id=seed.dept_id, supplier_code="A", supplier_name="NCC A",
                incur_date="2026-10-02", due_date=future, amount=500, vat=50, total=550, paid_amount=550, remaining=0,
                status="paid"),
        Payable(company_id=seed.company_id, department_id=seed.dept_id, supplier_code="B", supplier_name="NCC B",
                incur_date="2026-10-03", due_date=future, amount=2000, vat=200, total=2200, paid_amount=200,
                remaining=2000, status="partial"),
        #  Phòng KHÁC — người phạm vi «phòng ban» không được thấy.
        Payable(company_id=seed.company_id, department_id=other_dept.id, supplier_code="C", supplier_name="NCC C",
                incur_date="2026-10-04", due_date=past, amount=9000, vat=900, total=9900, paid_amount=0, remaining=9900,
                status="unpaid"),
    ]
    db.add_all(rows)
    db.commit()
    return rows


# ── Công nợ phải trả ──────────────────────────────────────────────────────────

def test_cong_no_pham_vi_phong_ban_khong_ra_so_phong_khac(db, seed, cap_quyen, other_dept):
    _payables(db, seed, other_dept)
    user = _user(db, seed)
    out = _q(db, user, "payable")
    assert out["denied"] and "payable" in out["error"]                                   # chưa có quyền

    cap_quyen(seed.u_req_id, "payable", scope="dept", read=True)
    out = _q(db, user, "payable", measures=["remaining", "total", "overdue", "count"])
    assert out["totals"] == {"remaining": 3100.0, "total": 3850.0, "overdue": 1100.0, "count": 3}
    assert out["currency"] == "VND" and out["link"] == "/finance/payables"
    assert {m["key"]: m.get("vat") for m in out["measures"]}["remaining"] == "sau VAT"

    by_dept = _q(db, user, "payable", measures=["remaining"], dimensions=["department"])
    assert [(r["department"], r["department_label"]) for r in by_dept["rows"]] == [(seed.dept_id, "Phòng Test")]


def test_cong_no_toan_cong_ty_chia_hai_chieu_nhan_trang_thai(db, seed, cap_quyen, other_dept):
    _payables(db, seed, other_dept)
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = _user(db, seed)
    out = _q(db, user, "payable", measures=["remaining", "count"], dimensions=["supplier", "status"])
    assert out["total"] == 4 and out["has_more"] is False
    top = out["rows"][0]
    assert (top["supplier"], top["supplier_label"], top["status"], top["status_label"], top["remaining"]) == \
        ("C", "NCC C", "unpaid", "Chờ thanh toán", 9900.0)
    #  Bộ lọc: chỉ khoản quá hạn, theo tháng phát sinh.
    od = _q(db, user, "payable", measures=["overdue"], dimensions=["month"], filters={"overdue": True}, sort="dimension")
    assert [(r["month"], r["overdue"]) for r in od["rows"]] == [("2026-09", 1100.0), ("2026-10", 9900.0)]
    comp = _q(db, user, "payable", dimensions=["company"])
    assert comp["rows"][0]["company_label"] != str(seed.company_id)                     # nhãn tên pháp nhân thật


# ── Yêu cầu thanh toán ────────────────────────────────────────────────────────

def test_yctt_pham_vi_phong_ban_bo_phieu_da_xoa_nhan_trang_thai(db, seed, cap_quyen, other_dept):
    db.add_all([
        PaymentRequest(code="YCTT01", company_id=seed.company_id, department_id=seed.dept_id, supplier_code="A",
                       supplier_name="NCC A", request_date="2026-10-01", total=1000, status="submitted"),
        PaymentRequest(code="YCTT02", company_id=seed.company_id, department_id=seed.dept_id, supplier_code="A",
                       supplier_name="NCC A", request_date="2026-10-05", total=500, status="paid", prepay=1),
        PaymentRequest(code="YCTT03", company_id=seed.company_id, department_id=seed.dept_id, supplier_code="A",
                       supplier_name="NCC A", request_date="2026-10-06", total=7777, status="draft", is_deleted=1),
        PaymentRequest(code="YCTT04", company_id=seed.company_id, department_id=other_dept.id, supplier_code="C",
                       supplier_name="NCC C", request_date="2026-10-07", total=9000, status="approved"),
    ])
    db.commit()
    cap_quyen(seed.u_req_id, "payment_request", scope="dept", read=True)
    user = _user(db, seed)
    out = _q(db, user, "payment_request", measures=["total", "count"], dimensions=["status"])
    assert out["totals"] == {"total": 1500.0, "count": 2}
    assert {(r["status"], r["status_label"]) for r in out["rows"]} == {("submitted", "Chờ duyệt"), ("paid", "Đã chi")}
    pre = _q(db, user, "payment_request", dimensions=["prepay"], filters={"prepay": True})
    assert [(r["prepay"], r["prepay_label"]) for r in pre["rows"]] == [(1, "Trả trước")]
    bad = _q(db, user, "payment_request", filters={"status": "xoa_het"})
    assert "status chỉ nhận" in bad["error"]


# ── Mua hàng ──────────────────────────────────────────────────────────────────

def _history(db):
    db.add_all([
        PurchaseHistory(product_code="P1", product_name="Hàng 1", supplier_code="A", supplier_name="NCC A",
                        order_date="2026-01-10", qty_order=10, price=1000, amount=11000),
        PurchaseHistory(product_code="P2", product_name="Hàng 2", supplier_code="A", supplier_name="NCC A",
                        order_date="2026-02-20", qty_order=5, price=2000, amount=0),
        PurchaseHistory(product_code="P1", product_name="Hàng 1", supplier_code="B", supplier_name="NCC B",
                        order_date="2026-03-05", qty_order=2, price=500, amount=1000),
    ])
    db.commit()


def test_mua_hang_quyen_san_pham_ncc_va_bao_cao(db, seed, cap_quyen, monkeypatch):
    from app.modules.report_access import service as ra

    _history(db)
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = _user(db, seed)
    monkeypatch.setattr(ra, "can_view_report", lambda db_, u, key, profile=None: False)
    out = _q(db, user, "purchase")
    assert out["denied"] and "Báo cáo mua hàng" in out["error"]
    monkeypatch.setattr(ra, "can_view_report", lambda db_, u, key, profile=None: True)
    out = _q(db, user, "purchase", measures=["total_amount", "count", "qty", "product_count"], dimensions=["product"])
    assert out["totals"] == {"total_amount": 22000.0, "count": 3, "qty": 17.0, "product_count": 2}
    assert [(r["product"], r["product_label"], r["total_amount"]) for r in out["rows"]] == [
        ("P1", "Hàng 1", 12000.0), ("P2", "Hàng 2", 10000.0)]
    denied = _q(db, user, "purchase", dimensions=["supplier"])
    assert denied["denied"] and "supplier" in denied["error"]
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    ok = _q(db, user, "purchase", dimensions=["supplier"], filters={"date_from": "2026-02-01"})
    assert [(r["supplier"], r["total_amount"]) for r in ok["rows"]] == [("A", 10000.0), ("B", 1000.0)]


def test_analytics_query_cu_qua_khuon_moi_van_dung_so(db, seed, cap_quyen, report_ok):
    _history(db)
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = _user(db, seed)
    month = T.run_tool(db, user, "analytics_query", {"metric": "total_amount", "dimension": "month", "sort": "dimension"})
    assert month["metric_label"] == "Tổng chi tiêu (đã gồm VAT)" and month["count"] == 3
    assert [(i["group"], i["group_name"], i["value"]) for i in month["items"]] == [
        ("2026-01", None, 11000.0), ("2026-02", None, 10000.0), ("2026-03", None, 1000.0)]
    avg = T.run_tool(db, user, "analytics_query", {"metric": "avg_price", "dimension": "product", "product_code": "P1"})
    assert avg["items"] == [{"group": "P1", "group_name": "Hàng 1", "value": 750.0}]
    assert "không hợp lệ" in T.run_tool(db, user, "analytics_query", {"metric": "drop table"})["error"]


# ── Trần + kiểm tham số ───────────────────────────────────────────────────────

def test_tran_nhom_truncated_va_gioi_han(db, seed, cap_quyen, other_dept):
    _payables(db, seed, other_dept)
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = _user(db, seed)
    out = _q(db, user, "payable", dimensions=["supplier"], limit=2)
    assert out["total"] == 3 and out["returned"] == 2 and out["truncated"] and out["has_more"]
    assert "Thêm bộ lọc" in out["note"]
    assert _q(db, user, "payable", dimensions=["supplier"], limit=99999)["returned"] == 3      # kẹp ở 500, không lỗi


def test_khong_co_duong_sinh_sql_va_bao_loi_ro(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = _user(db, seed)
    assert "Không có bộ dữ liệu" in _q(db, user, "tab_user")["error"]
    out = _q(db, user, "payable", measures=["sum(total); drop table tab_payable"])
    assert "chỉ số" in out["error"] and "remaining" in out["error"]
    out = _q(db, user, "payable", dimensions=["created_by"])
    assert "chiều" in out["error"] and "supplier" in out["error"]
    assert "YYYY-MM-DD" in _q(db, user, "payable", filters={"date_from": "1=1"})["error"]
    assert "Tối đa 4 chỉ số" in _q(db, user, "payable", measures=["remaining", "total", "amount", "vat", "count"])["error"]
    out = _q(db, user, "payable", filters={"created_by": 1})
    assert out["ignored_filters"] == ["created_by"] and "supplier" in out["allowed_filters"]
    desc = _q(db, user, "payable", describe=True)
    assert desc["datasets"][0]["dataset"] == "payable" and any(f["key"] == "overdue" for f in desc["datasets"][0]["filters"])
    assert {d["dataset"] for d in T.run_tool(db, user, "dataset_query", {})["datasets"]} == {
        "purchase", "payable", "payment_request"}


def test_moi_bo_khai_du_va_mo_qua_mcp_khoa_doc():
    from app.modules.agent_hub import mcp

    assert "dataset_query" in mcp.READ_TOOLS
    for ds in datasets.registry().values():
        assert ds.measures and ds.dimensions and ds.filters and ds.entity
        #  Bộ nào không qua apply_scope phải là bảng không có khóa phạm vi (lịch sử giá) — khai rõ, không lặng lẽ.
        assert ds.scope_entity or ds.key == "purchase", ds.key
