"""duoc-CR-744 — bảng Chi tiết YC mua hàng (GET /api/reports/pr-lines) sắp xếp TẠI SERVER theo mọi cột.

Trước đây `sort_by` / `sort_dir` bị bỏ qua hoàn toàn nên bấm tiêu đề cột không đổi gì. Canh:
  - MỌI cột của bảng xếp được, cả hai chiều, và thứ tự theo đúng thứ ô đang hiện (tên chứ không phải id/mã,
    tiến độ theo vòng đời chứ không theo chữ cái, mã ĐMH theo mã đầu tiên của dãy...);
  - xếp trên CẢ TẬP: ghép các trang ra đúng thứ tự của toàn bộ, không xếp riêng từng trang;
  - file xuất Excel ra cùng thứ tự với bảng;
  - `sort_by` lạ bị bỏ qua (ra thứ tự mặc định); cột NCC không xếp được khi thiếu `supplier.read`;
  - canary: tập khóa xếp được = tập khóa cột của dòng trả về, thêm cột mới mà quên xếp là bài này đỏ.
"""
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.core.central_purchasing import get_central_dept_code
from app.core.status_codes import PR_LINE_STATUS
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.product.model import Product
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.report import pr_lines_sort
from app.modules.report import service as report_service

USER = SimpleNamespace(id=0)

LINE_ORDER = list(pr_lines_sort._LINE_STATUS_ORDER)
PR_ORDER = list(pr_lines_sort._PR_STATUS_ORDER)


def _see_all(monkeypatch):
    monkeypatch.setattr(report_service, "report_dept_scope", lambda db, user: None)


def _pr(db, code, company_id, **kw):
    kw.setdefault("status", "approved")
    pr = PurchaseRequest(code=code, company_id=company_id, created_by=1, updated_by=1, **kw)
    db.add(pr)
    db.flush()
    return pr


def _line(db, pr, code, **kw):
    it = PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name=kw.pop("product_name", f"SP {code}"), **kw)
    db.add(it)
    db.flush()
    return it


def _po(db, pr_code, code, supplier, created_at, product_code, status="approved"):
    po = PurchaseOrder(code=code, pr_code=pr_code, supplier_name=supplier, status=status, created_at=created_at)
    db.add(po)
    db.flush()
    item = POItem(po_id=po.id, product_code=product_code, qty_order=5, progress_status="ordered")
    db.add(item)
    db.flush()
    return po, item


@pytest.fixture
def data(db, seed):
    """Ba phiếu x sáu dòng, giá trị của MỖI cột đều khác nhau giữa các dòng (bài canh có kiểm điều đó)."""
    from datetime import datetime

    company_a = Company(name="Cty A Đầu", code="CA", is_active=True)
    company_z = Company(name="Cty Z Cuối", code="CZ", is_active=True)
    central = Department(code=get_central_dept_code(), name="Phòng Mua Chung", company_id=seed.company_id, is_active=True)
    db.add_all([company_a, company_z, central])
    db.flush()
    db.add_all([Product(code="SP-A", name="A", specs="120gsm"), Product(code="SP-C", name="C", specs="300gsm"),
                Product(code="SP-E", name="E", specs="80gsm")])

    pr_a = _pr(db, "PYC-743-A", seed.company_id, request_date="2026-10-01", requester="Bình", department="Phòng Kế",
               purpose="Z mua", is_urgent=True, need_date="2026-10-20", head_of_dept="TBP Bê",
               approver_employee_id=seed.emp_tp_id, handler_dept_id=seed.dept_id, suggested_supplier="NCC Z")
    pr_b = _pr(db, "PYC-743-B", company_a.id, request_date="2026-09-01", requester="An", department="Phòng An",
               purpose="A mua", is_urgent=False, need_date="2026-09-10", status="draft",
               head_of_dept_id=seed.emp_req_id, handler_dept_id=0, suggested_supplier="NCC A")
    pr_c = _pr(db, "PYC-743-C", company_z.id, request_date="2026-11-01", requester="Cường", department="Phòng Cường",
               purpose="M mua", is_urgent=False, need_date="2026-11-30", status="completed",
               head_of_dept="TBP An", handler_dept_id=seed.dept_id, suggested_supplier="NCC M")

    lines = [
        _line(db, pr_a, "SP-A", product_name="Xà phòng", qty=5, price=300, vat_pct=8, amount=1620, unit="Kg",
              warehouse="Kho Z", item_group="Thùng", required_date="2026-10-05", expected_date="2026-10-09",
              assignee="DEMONV", line_status="ordered", qty_ordered=5, qty_received=2, progress_note="b", note="n3"),
        _line(db, pr_a, "SP-B", product_name="Bao bì", qty=50, price=10, vat_pct=0, amount=500, unit="Cái",
              warehouse="Kho A", item_group="Nhãn", required_date="2026-10-02", expected_date="",
              assignee="", line_status="no_po", progress_note="a", note="n1"),
        _line(db, pr_b, "SP-C", product_name="Cốc", qty=1, price=99, vat_pct=10, amount=109, unit="Hộp",
              warehouse="Kho M", item_group="Chai", required_date="2026-09-20", expected_date="2026-09-15",
              assignee="BACKUP01", line_status="received", qty_ordered=1, qty_received=1, progress_note="c", note="n2"),
        _line(db, pr_b, "SP-D", product_name="Dây", qty=7, price=1, vat_pct=5, amount=7, unit="M",
              warehouse="Kho B", item_group="Dây", required_date="2026-09-11", expected_date="2026-09-30",
              assignee="NV-LA", line_status="cancelled", progress_note="d", note="n4"),
        _line(db, pr_c, "SP-E", product_name="Ê ke", qty=9, price=5, vat_pct=8, amount=48, unit="Bộ",
              warehouse="Kho C", item_group="Ke", required_date="2026-11-10", expected_date="2026-11-20",
              assignee="DEMOTP", line_status="completed", qty_ordered=9, qty_received=9, progress_note="e", note="n5"),
        _line(db, pr_c, "SP-F", product_name="Phễu", qty=2, price=7, vat_pct=8, amount=15, unit="Cái",
              warehouse="Kho D", item_group="Phễu", required_date="2026-11-12", expected_date="2026-11-22",
              assignee="DEMONV", line_status="not_ordered", progress_note="f", note="n6"),
    ]
    #  Đơn mua hàng: SP-A có hai đơn (mã đầu = "DMH-9", mã sau nhỏ hơn để phân biệt "mã đầu" với "mã nhỏ nhất"),
    #  SP-C một đơn, SP-E một đơn; SP-B / SP-D / SP-F không có đơn.
    po1, i1 = _po(db, pr_a.code, "DMH-9", "NCC Cũ", datetime(2026, 10, 2), "SP-A")
    po2, i2 = _po(db, pr_a.code, "DMH-1", "NCC Mới", datetime(2026, 10, 5), "SP-A")
    po3, i3 = _po(db, pr_b.code, "DMH-5", "NCC Ba", datetime(2026, 9, 3), "SP-C")
    po4, i4 = _po(db, pr_c.code, "DMH-3", "NCC Tư", datetime(2026, 11, 3), "SP-E")
    db.add_all([
        PODelivery(po_id=po1.id, po_item_id=i1.id, delivery_no=1, received_qty=2, promised_date="2026-10-09"),
        PODelivery(po_id=po2.id, po_item_id=i2.id, delivery_no=1, received_qty=1, promised_date="2026-10-20"),
        PODelivery(po_id=po2.id, po_item_id=i2.id, delivery_no=2, received_qty=3, promised_date="2026-10-25"),
        PODelivery(po_id=po3.id, po_item_id=i3.id, delivery_no=1, received_qty=1, promised_date="2026-09-12"),
        PODelivery(po_id=po4.id, po_item_id=i4.id, delivery_no=1, received_qty=0, promised_date="2026-11-18"),
    ])
    db.commit()
    return SimpleNamespace(lines=lines)


def _rows(db, monkeypatch, **kw):
    _see_all(monkeypatch)
    kw.setdefault("show_supplier", True)
    return report_service.compute_pr_lines(db, USER, year="all", page_size=100, **kw)["items"]


def _shown(key, row):
    """Giá trị mà ô của cột `key` đang HIỆN (làm khóa so sánh thứ tự)."""
    if key == "assignee":
        return row["assignee_name"] or row["assignee"]
    if key == "line_status":
        return LINE_ORDER.index(row["line_status"])
    if key == "status":
        return PR_ORDER.index(row["status"])
    if key == "po_codes":
        return (row["po_codes"] or "").split(", ")[0]
    value = row[key]
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    return value


ALL_KEYS = sorted(pr_lines_sort.sortable_keys())


def _expected(values: list, reverse: bool) -> list:
    """Thứ tự mong đợi: ô có giá trị xếp theo chiều, ô TRỐNG luôn xuống cuối cả hai chiều
    (luật chung `core/sort_order.py`)."""
    def blank(v):
        return v is None or (isinstance(v, str) and not v.strip())
    filled = sorted((v for v in values if not blank(v)), reverse=reverse)
    return filled + [v for v in values if blank(v)]


@pytest.mark.parametrize("key", ALL_KEYS)
def test_moi_cot_xep_duoc_hai_chieu_theo_gia_tri_dang_hien(db, seed, data, monkeypatch, key):
    asc = [_shown(key, r) for r in _rows(db, monkeypatch, sort_by=key, sort_dir="asc")]
    desc = [_shown(key, r) for r in _rows(db, monkeypatch, sort_by=key, sort_dir="desc")]
    assert len(asc) == 6
    assert len(set(asc)) > 1, f"dữ liệu mẫu phải có giá trị khác nhau ở cột {key}, không thì bài này xanh giả"
    assert asc == _expected(asc, False), f"{key} tăng dần sai thứ tự: {asc}"
    assert desc == _expected(desc, True), f"{key} giảm dần sai thứ tự: {desc}"


def test_canary_tap_khoa_xep_duoc_bang_tap_khoa_cot_cua_dong(db, seed, data, monkeypatch):
    row_keys = set(_rows(db, monkeypatch)[0])
    #  `pr_id` là khóa nối sang chi tiết phiếu, `assignee_name` là phần hiện thêm của cột `assignee`: không phải cột.
    assert set(pr_lines_sort.sortable_keys()) == row_keys - {"pr_id", "assignee_name"}


def test_tien_do_va_trang_thai_xep_theo_vong_doi_khong_theo_chu_cai(db, seed, data, monkeypatch):
    codes = [r["line_status"] for r in _rows(db, monkeypatch, sort_by="line_status", sort_dir="asc")]
    assert codes == ["no_po", "not_ordered", "ordered", "received", "completed", "cancelled"]
    statuses = [r["status"] for r in _rows(db, monkeypatch, sort_by="status", sort_dir="asc")]
    assert statuses == ["draft", "draft", "approved", "approved", "completed", "completed"]


def test_bo_ma_trang_thai_dong_khop_thu_tu_vong_doi(db):
    """Thêm mã mới vào `PR_LINE_STATUS` mà quên xếp hạng thì mã đó rơi cuối bảng im lặng."""
    assert sorted(LINE_ORDER) == sorted(code.value for code in PR_LINE_STATUS.codes)


def test_ma_dmh_xep_theo_ma_dau_tien_cua_day_dang_hien(db, seed, data, monkeypatch):
    rows = _rows(db, monkeypatch, sort_by="po_codes", sort_dir="desc")
    assert rows[0]["po_codes"] == "DMH-9, DMH-1", "ô hiện theo đơn tạo trước -> sau, mã đầu DMH-9 lớn nhất"
    assert [r["po_codes"] for r in rows[-3:]] == [None, None, None]


def test_cot_ten_xep_theo_ten_khong_theo_id(db, seed, data, monkeypatch):
    names = [r["company_name"] for r in _rows(db, monkeypatch, sort_by="company_name", sort_dir="asc")]
    assert names == sorted(names) and names[0] == "Cty A Đầu" and names[-1] == "Cty Z Cuối"
    #  Công ty Z tạo SAU cùng (id lớn nhất) nhưng tên xếp cuối chỉ vì chữ Z; công ty A tạo sau Cty Test mà vẫn đứng đầu.
    heads = [r["head_of_dept_name"] for r in _rows(db, monkeypatch, sort_by="head_of_dept_name", sort_dir="asc")]
    assert heads == sorted(heads) and "Người YC" in heads and "TBP An" in heads, "tên nhân sự theo id, lùi về bản chụp"
    handlers = {r["handler_dept_name"] for r in _rows(db, monkeypatch, sort_by="handler_dept_name")}
    assert "Phòng Mua Chung" in handlers, "handler_dept_id = 0 đọc như phòng thu mua mặc định"


def test_xep_tren_ca_tap_ghep_cac_trang_ra_dung_thu_tu(db, seed, data, monkeypatch):
    _see_all(monkeypatch)
    whole = [r["id"] for r in report_service.compute_pr_lines(db, USER, year="all", page_size=100,
                                                                sort_by="amount", sort_dir="desc")["items"]]
    paged = []
    for page in (1, 2, 3):
        out = report_service.compute_pr_lines(db, USER, year="all", page=page, page_size=2,
                                              sort_by="amount", sort_dir="desc")
        paged += [r["id"] for r in out["items"]]
    assert paged == whole and len(whole) == 6
    amounts = {r["id"]: r["amount"] for r in report_service.compute_pr_lines(db, USER, year="all", page_size=100)["items"]}
    assert [amounts[i] for i in whole] == sorted(amounts.values(), reverse=True)


def test_sort_by_la_hoac_rong_giu_thu_tu_mac_dinh(db, seed, data, monkeypatch):
    default = [r["id"] for r in _rows(db, monkeypatch)]
    for bad in ("khong_co_cot_nay", "", "id; DROP TABLE tab_user", "po_codes) desc, (1", None):
        assert [r["id"] for r in _rows(db, monkeypatch, sort_by=bad, sort_dir="desc")] == default
    assert default[0] in {l.id for l in data.lines[-2:]}, "mặc định: ngày lập phiếu mới nhất (phiếu C) đứng đầu"


def test_cot_ncc_khong_xep_duoc_khi_thieu_supplier_read(db, seed, data, monkeypatch):
    """Thứ tự dòng theo tên NCC là đủ để mò ra NCC đang bị che, nên thiếu quyền thì bỏ qua khóa xếp."""
    default = [r["id"] for r in _rows(db, monkeypatch, show_supplier=False)]
    for key in sorted(pr_lines_sort.SUPPLIER_SORT_KEYS):
        shown = _rows(db, monkeypatch, show_supplier=False, sort_by=key, sort_dir="desc")
        assert [r["id"] for r in shown] == default, key
        assert all(r["suggested_supplier"] is None and r["latest_po_supplier"] is None for r in shown)
        with_right = _rows(db, monkeypatch, show_supplier=True, sort_by=key, sort_dir="desc")
        assert [r["id"] for r in with_right] != default, f"có quyền thì {key} phải đổi thứ tự"


def test_xuat_excel_ra_cung_thu_tu_voi_bang(db, seed, data, cap_quyen, monkeypatch):
    from app.core.auth import get_current_user
    from app.core.database import get_db
    from app.main import app
    from app.modules.user.model import User

    _see_all(monkeypatch)
    user = User(email="u743@x.vn", password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "report", read=True, export=True)
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app)
        resp = client.get("/api/reports/pr-lines/export", params={"year": "all", "sort_by": "qty", "sort_dir": "desc"})
        assert resp.status_code == 200, resp.text
        ws = load_workbook(BytesIO(resp.content)).active
        header = [c.value for c in ws[1]]
        col = header.index("SL yêu cầu") + 1
        qty = [ws.cell(row=r, column=col).value for r in range(2, ws.max_row + 1)]
        assert qty == sorted(qty, reverse=True) and len(qty) == 6
        table = client.get("/api/reports/pr-lines", params={"year": "all", "sort_by": "qty", "sort_dir": "desc"})
        assert [r["qty"] for r in table.json()["data"]["items"]] == qty, "bảng và file xuất cùng thứ tự"
        #  sort_dir lạ -> tăng dần, không nổ.
        asc = client.get("/api/reports/pr-lines", params={"year": "all", "sort_by": "qty", "sort_dir": "sideways"})
        assert [r["qty"] for r in asc.json()["data"]["items"]] == sorted(qty)
    finally:
        app.dependency_overrides.clear()
