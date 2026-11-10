"""duoc-CR-744 — bấm tiêu đề cột màn Công nợ phải sắp xếp được tại SERVER.

Trước đây `GET /api/payables` và `/export/xlsx` bỏ qua `sort_by`/`sort_dir` hoàn toàn. Nay mỗi
cột trên bảng xếp theo ĐÚNG thứ ô đang hiện (xem `payable/sort_expressions.py`). Kiểm:
- từng khóa cột, cả hai chiều, trên cả tập (không riêng một trang);
- ô trống luôn xuống cuối; công ty xếp theo tên; loại nợ / trạng thái / tuổi nợ theo hạng;
- khóa lạ bị bỏ qua (về thứ tự mặc định); xuất Excel cùng thứ tự; canh mọi khóa của bảng.

Không đụng DB thật — fixture SQLite in-memory ở conftest.
"""
import json
from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace

import openpyxl
import pytest
from starlette.datastructures import QueryParams

from app.core.auth import perm_cache_clear
from app.modules.company.model import Company
from app.modules.payable import controller as C
from app.modules.payable.model import Payable
from app.modules.payable.sort_expressions import build_order_by
from app.modules.purchase_order.model import PODelivery, POItem

#  Khóa cột của bảng Công nợ ở frontend (trừ `select`, `offset_prepay` là cột thao tác).
#  Thêm cột mới vào bảng mà quên backend thì bài canh bên dưới đỏ.
TABLE_SORT_KEYS = [
    #  Cột ID do `DataTable` tự thêm ở bìa trái (dòng có trường `id`) — gửi `sort_by=id`.
    "id",
    "supplier_name", "supplier_code", "source_type", "company", "po_code", "invoice_no",
    "invoice_date", "incur_date", "created_at", "due_date", "aging", "amount", "vat", "total",
    "paid_amount", "remaining", "status",
]


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _d(days: int) -> str:
    return (datetime.now().date() + timedelta(days=days)).strftime("%Y-%m-%d")


def _req(qs: str = ""):
    return SimpleNamespace(query_params=QueryParams(qs))


def _grant_all(db, user_id: int):
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    role = Role(code=f"R{user_id}all", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="payable", scope="all", can_read=True, can_export=True))
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.flush()
    perm_cache_clear()


def _payable(db, **kw):
    vals = dict(company_id=0, supplier_code="NX", supplier_name="NCC Xanh", source_type="goods",
                po_code="PO-1", invoice_no="HD-1", incur_date=_d(-5), due_date=_d(10),
                amount=1000, vat=0, total=1000, paid_amount=0, remaining=1000, status="unpaid")
    vals.update(kw)
    p = Payable(**vals)
    db.add(p)
    db.flush()
    return p


@pytest.fixture()
def world_sap_xep(db, seed):
    """Bốn khoản khác nhau ở MỌI cột, một khoản để trống các ô chữ / ngày."""
    from app.modules.user.model import User
    cty_b = Company(name="Cty B Bình", code="CB", is_active=True)
    cty_a = Company(name="Cty A An", code="CA", is_active=True)
    db.add_all([cty_b, cty_a])
    db.flush()
    d_x = PODelivery(po_id=1, po_item_id=0, invoice_date="2026-03-05")
    d_y = PODelivery(po_id=1, po_item_id=0, invoice_date="2026-01-10")
    db.add_all([d_x, d_y])
    db.flush()

    p1 = _payable(db, company_id=cty_b.id, supplier_name="Zeta", supplier_code="Z1", source_type="shipping",
                  po_code="PO-30", invoice_no="HD-3", incur_date="2026-03-01", due_date=_d(30),
                  amount=100, vat=10, total=110, paid_amount=0, remaining=110, status="unpaid",
                  ref_type="delivery", ref_id=d_x.id)
    p2 = _payable(db, company_id=cty_a.id, supplier_name="Alpha", supplier_code="A1", source_type="goods",
                  po_code="PO-10", invoice_no="HD-1", incur_date="2026-01-01", due_date=_d(-10),
                  amount=300, vat=30, total=330, paid_amount=330, remaining=0, status="paid",
                  ref_type="delivery", ref_id=d_y.id)
    p3 = _payable(db, company_id=cty_b.id, supplier_name="Mu", supplier_code="M1", source_type="import_cost",
                  po_code="PO-20", invoice_no="HD-2", incur_date="2026-02-01", due_date=_d(-45),
                  amount=200, vat=20, total=220, paid_amount=100, remaining=120, status="partial")
    #  Khoản trống chữ / ngày: tên rỗng thì hiện mã NCC, chưa số HĐ, chưa hạn trả.
    p4 = _payable(db, company_id=0, supplier_name="", supplier_code="B0", source_type="goods",
                  po_code="", invoice_no="", incur_date="", due_date="",
                  amount=50, vat=5, total=55, paid_amount=0, remaining=55, status="unpaid")
    user = db.get(User, seed.u_req_id)
    _grant_all(db, user.id)
    return SimpleNamespace(p1=p1, p2=p2, p3=p3, p4=p4, user=user)


def _ids(db, user, qs: str) -> list[int]:
    resp = C.list_payables(request=_req(qs), pg={"offset": 0, "limit": 50}, db=db, user=user)
    return [it["id"] for it in json.loads(resp.body)["data"]["items"]]


def _sorted(db, w, key: str, direction: str = "asc") -> list[int]:
    return _ids(db, w.user, f"year=all&sort_by={key}&sort_dir={direction}")


def test_so_tien_va_cot_so_xep_theo_gia_tri(db, world_sap_xep):
    w = world_sap_xep
    for key, asc in [("total", [w.p4, w.p1, w.p3, w.p2]),
                     ("amount", [w.p4, w.p1, w.p3, w.p2]),
                     ("vat", [w.p4, w.p1, w.p3, w.p2]),
                     ("paid_amount", [w.p1, w.p4, w.p3, w.p2]),
                     ("remaining", [w.p2, w.p4, w.p1, w.p3])]:
        ids_asc = [p.id for p in asc]
        got = _sorted(db, w, key, "asc")
        #  paid_amount / remaining có hai khoản bằng nhau -> chỉ so thứ tự giá trị.
        vals = {p.id: float(getattr(p, key)) for p in asc}
        assert [vals[i] for i in got] == sorted(vals[i] for i in ids_asc), key
        got_desc = _sorted(db, w, key, "desc")
        assert [vals[i] for i in got_desc] == sorted((vals[i] for i in ids_asc), reverse=True), key


def test_ten_ncc_xep_theo_chu_dang_hien_ke_ca_khi_thieu_ten(db, world_sap_xep):
    """Ô hiện tên NCC, thiếu tên hiện mã NCC (B0) -> Alpha < B0 < Mu < Zeta."""
    w = world_sap_xep
    assert _sorted(db, w, "supplier_name", "asc") == [w.p2.id, w.p4.id, w.p3.id, w.p1.id]
    assert _sorted(db, w, "supplier_name", "desc") == [w.p1.id, w.p3.id, w.p4.id, w.p2.id]


def test_o_trong_luon_xuong_cuoi_ca_hai_chieu(db, world_sap_xep):
    w = world_sap_xep
    for key in ("po_code", "invoice_no", "incur_date", "due_date"):
        assert _sorted(db, w, key, "asc")[-1] == w.p4.id, key
        assert _sorted(db, w, key, "desc")[-1] == w.p4.id, key


def test_ma_don_va_so_hoa_don_xep_tang_giam(db, world_sap_xep):
    w = world_sap_xep
    assert _sorted(db, w, "po_code", "asc")[:3] == [w.p2.id, w.p3.id, w.p1.id]
    assert _sorted(db, w, "po_code", "desc")[:3] == [w.p1.id, w.p3.id, w.p2.id]
    assert _sorted(db, w, "invoice_no", "asc")[:3] == [w.p2.id, w.p3.id, w.p1.id]


def test_ngay_xep_theo_chuoi_ngay(db, world_sap_xep):
    w = world_sap_xep
    assert _sorted(db, w, "incur_date", "asc")[:3] == [w.p2.id, w.p3.id, w.p1.id]
    assert _sorted(db, w, "incur_date", "desc")[:3] == [w.p1.id, w.p3.id, w.p2.id]
    assert _sorted(db, w, "due_date", "asc")[:3] == [w.p3.id, w.p2.id, w.p1.id]
    assert _sorted(db, w, "due_date", "desc")[:3] == [w.p1.id, w.p2.id, w.p3.id]


def test_ngay_hoa_don_xep_theo_gia_tri_do_tu_dot_giao(db, world_sap_xep):
    """p2 dò ra 10/01, p1 dò ra 05/03 (đợt giao); p3 không đợt giao nhưng có số HĐ -> rơi về
    incur_date 01/02; p4 không số HĐ -> trống, xuống cuối."""
    w = world_sap_xep
    assert _sorted(db, w, "invoice_date", "asc") == [w.p2.id, w.p3.id, w.p1.id, w.p4.id]
    assert _sorted(db, w, "invoice_date", "desc") == [w.p1.id, w.p3.id, w.p2.id, w.p4.id]


def test_ngay_hoa_don_ket_hop_bo_loc_ngay_hoa_don_khong_join_hai_lan(db, world_sap_xep):
    """Lọc khoảng ngày HĐ đã join sẵn đợt giao; xếp cùng cột đó không được join lại (lỗi bảng trùng)."""
    w = world_sap_xep
    got = _ids(db, w.user, "year=all&invoice_from=2026-01-01&invoice_to=2026-12-31"
                           "&sort_by=invoice_date&sort_dir=desc")
    assert got == [w.p1.id, w.p3.id, w.p2.id]


def test_ngay_hoa_don_di_qua_dong_hang_khi_dot_giao_trong(db, seed):
    from app.modules.user.model import User
    item = POItem(po_id=1, product_code="SP", invoice_date="2026-06-06")
    db.add(item)
    db.flush()
    d = PODelivery(po_id=1, po_item_id=item.id, invoice_date="")
    db.add(d)
    db.flush()
    a = _payable(db, ref_type="delivery", ref_id=d.id, invoice_no="X", incur_date="2026-09-09")
    b = _payable(db, ref_type="delivery", ref_id=0, invoice_no="Y", incur_date="2026-07-07")
    user = db.get(User, seed.u_req_id)
    _grant_all(db, user.id)
    assert _ids(db, user, "year=all&sort_by=invoice_date&sort_dir=asc") == [a.id, b.id]


def test_cong_ty_xep_theo_ten_khong_theo_id(db, world_sap_xep):
    """Cty B được tạo TRƯỚC (id nhỏ hơn) nhưng tên 'Cty A An' đứng trước; công ty rỗng xuống cuối."""
    w = world_sap_xep
    asc = _sorted(db, w, "company", "asc")
    assert asc[0] == w.p2.id and set(asc[1:3]) == {w.p1.id, w.p3.id} and asc[3] == w.p4.id
    desc = _sorted(db, w, "company", "desc")
    assert set(desc[:2]) == {w.p1.id, w.p3.id} and desc[2] == w.p2.id and desc[3] == w.p4.id


def test_loai_no_xep_theo_thu_tu_chu_giao_dien(db, world_sap_xep):
    """Chi phí nhập khẩu < Hàng hóa < Vận chuyển (mã DB: import_cost < goods < shipping)."""
    w = world_sap_xep
    asc = _sorted(db, w, "source_type", "asc")
    assert asc[0] == w.p3.id and asc[-1] == w.p1.id
    assert set(asc[1:3]) == {w.p2.id, w.p4.id}
    assert _sorted(db, w, "source_type", "desc")[0] == w.p1.id


def test_trang_thai_xep_theo_vong_doi(db, world_sap_xep):
    """Chờ thanh toán -> một phần -> đã thanh toán (không xếp theo mã chữ: paid < partial < unpaid)."""
    w = world_sap_xep
    asc = _sorted(db, w, "status", "asc")
    assert set(asc[:2]) == {w.p1.id, w.p4.id} and asc[2] == w.p3.id and asc[3] == w.p2.id
    assert _sorted(db, w, "status", "desc")[0] == w.p2.id


def test_tuoi_no_xep_theo_hang_tuoi_no(db, world_sap_xep):
    """p1 (hạn +30) và p4 (chưa hạn) = Chưa đến hạn; p2 (quá 10 ngày) = 1-30; p3 (quá 45) = 31-60."""
    w = world_sap_xep
    asc = _sorted(db, w, "aging", "asc")
    assert set(asc[:2]) == {w.p1.id, w.p4.id} and asc[2] == w.p2.id and asc[3] == w.p3.id
    assert _sorted(db, w, "aging", "desc")[:2] == [w.p3.id, w.p2.id]


def test_khoa_la_bi_bo_qua_ve_thu_tu_mac_dinh(db, world_sap_xep):
    w = world_sap_xep
    mac_dinh = _ids(db, w.user, "year=all")
    assert _ids(db, w.user, "year=all&sort_by=khong_co_that&sort_dir=desc") == mac_dinh
    assert _ids(db, w.user, "year=all&sort_by=password_hash&sort_dir=asc") == mac_dinh


def test_chieu_la_thi_coi_la_tang(db, world_sap_xep):
    w = world_sap_xep
    assert _sorted(db, w, "total", "sideways") == _sorted(db, w, "total", "asc")


def test_xep_tren_ca_tap_khong_rieng_trang(db, world_sap_xep):
    """Trang 1 (2 dòng/trang) của chiều giảm phải là 2 khoản LỚN NHẤT cả tập."""
    w = world_sap_xep
    resp = C.list_payables(request=_req("year=all&sort_by=total&sort_dir=desc"),
                           pg={"offset": 0, "limit": 2}, db=db, user=w.user)
    ids = [it["id"] for it in json.loads(resp.body)["data"]["items"]]
    assert ids == [w.p2.id, w.p3.id]
    resp = C.list_payables(request=_req("year=all&sort_by=total&sort_dir=desc"),
                           pg={"offset": 2, "limit": 2}, db=db, user=w.user)
    assert [it["id"] for it in json.loads(resp.body)["data"]["items"]] == [w.p1.id, w.p4.id]


def test_bo_loc_van_nguyen_khi_xep(db, world_sap_xep):
    w = world_sap_xep
    got = _ids(db, w.user, "year=all&status=unpaid&sort_by=total&sort_dir=desc")
    assert got == [w.p1.id, w.p4.id]


def test_xuat_excel_cung_thu_tu_voi_bang(db, world_sap_xep):
    w = world_sap_xep
    resp = C.export_xlsx(request=_req("year=all&sort_by=total&sort_dir=desc"),
                         cols="total", db=db, user=w.user)
    body = b"".join(resp.body_iterator) if hasattr(resp, "body_iterator") else resp.body
    ws = openpyxl.load_workbook(BytesIO(body)).active
    assert [r[0].value for r in ws.iter_rows(min_row=2)] == [330, 220, 110, 55]


def test_canh_moi_cot_cua_bang_deu_xep_duoc(db):
    """Bảng ở frontend có khóa nào thì backend phải có biểu thức xếp cho khóa đó."""
    for key in TABLE_SORT_KEYS:
        assert build_order_by(db, key, "asc", datetime.now()), f"cột {key} không có biểu thức xếp"
        assert build_order_by(db, key, "desc", datetime.now()), f"cột {key} (desc)"
