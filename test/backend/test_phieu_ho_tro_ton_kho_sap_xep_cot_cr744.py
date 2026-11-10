"""duoc-CR-744 — bấm tiêu đề cột Phiếu hỗ trợ và Tồn kho xếp được tại SERVER.

Trước đây hai bảng không khai `sortable` nên không bấm được cột nào (`GET /api/tickets` đọc `sort_by` nhưng
chỉ cho cột vật lý; `GET /api/inventory` bỏ qua hẳn và cố định theo mã sản phẩm). Kiểm: từng khóa cột, cả hai
chiều, trên cả tập; người gửi / người xử lý xếp theo TÊN HIỂN THỊ; ưu tiên / trạng thái theo hạng nghiệp vụ;
Công ty (Tồn kho) theo tên; ô trống xuống cuối cả hai chiều; khóa phụ `id` giảm dần.

Không đụng DB thật — fixture SQLite in-memory ở conftest. Dữ liệu dùng chữ ASCII vì SQLite so chuỗi theo mã byte.
"""
import json
from datetime import datetime
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.inventory import controller as inv_ctl
from app.modules.inventory.model import Inventory
from app.modules.ticket import controller as ticket_ctl
from app.modules.ticket.model import Ticket
from app.modules.user.model import User

PAGE = {"offset": 0, "limit": 100}


def _req(qs: str = ""):
    return SimpleNamespace(query_params=QueryParams(qs))


def _items(resp) -> list[dict]:
    return json.loads(resp.body)["data"]["items"]


# ── Phiếu hỗ trợ ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tickets(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "ticket", read=True)
    emp_z = Employee(code="TKZ", full_name="Zeta Gui", is_active=True)
    emp_a = Employee(code="TKA", full_name="Alpha Xu Ly", is_active=True)
    db.add_all([emp_z, emp_a])
    db.flush()
    #  Người gửi 'Zeta Gui' tạo TRƯỚC (id nhỏ); tài khoản không gắn nhân sự thì hiện email.
    u_z = User(email="zeta@x.vn", employee_id=emp_z.id, password_hash="x", is_active=True)
    u_a = User(email="alpha@x.vn", employee_id=emp_a.id, password_hash="x", is_active=True)
    u_mail = User(email="Mail.only@x.vn", employee_id=0, password_hash="x", is_active=True)
    db.add_all([u_z, u_a, u_mail])
    db.flush()

    def _t(code, **kw):
        t = Ticket(code=code, subject=kw.pop("subject", code), **kw)
        db.add(t)
        db.flush()
        return t

    t1 = _t("TK-1", subject="Bao loi in", department="Kho", priority="urgent", status="closed",
            created_by=u_z.id, assignee_id=u_a.id)
    t2 = _t("TK-2", subject="An cai dat", department="IT", priority="low", status="open",
            created_by=u_a.id, assignee_id=0)
    t3 = _t("TK-3", subject="Cap quyen", department="", priority="high", status="answered",
            created_by=u_mail.id, assignee_id=u_z.id)
    t4 = _t("TK-4", subject="", department="Ke toan", priority="normal", status="in_progress",
            created_by=u_z.id, assignee_id=u_mail.id)
    return SimpleNamespace(user=db.get(User, seed.u_req_id), t1=t1, t2=t2, t3=t3, t4=t4)


def _ticket_ids(db, w, key, direction):
    mine = {w.t1.id, w.t2.id, w.t3.id, w.t4.id}
    resp = ticket_ctl.list_(request=_req(f"sort_by={key}&sort_dir={direction}"), pg=PAGE, db=db, user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_phieu_uu_tien_xep_theo_hang_khong_theo_chu_cai_cua_ma(db, tickets):
    """low < normal < high < urgent. Theo chữ cái của mã: high < low < normal < urgent — sai thứ tự đọc."""
    w = tickets
    assert _ticket_ids(db, w, "priority", "asc") == [w.t2.id, w.t4.id, w.t3.id, w.t1.id]
    assert _ticket_ids(db, w, "priority", "desc") == [w.t1.id, w.t3.id, w.t4.id, w.t2.id]


def test_phieu_trang_thai_xep_theo_vong_doi(db, tickets):
    """open < in_progress < answered < closed (chữ cái của mã: answered < closed < in_progress < open)."""
    w = tickets
    assert _ticket_ids(db, w, "status", "asc") == [w.t2.id, w.t4.id, w.t3.id, w.t1.id]
    assert _ticket_ids(db, w, "status", "desc") == [w.t1.id, w.t3.id, w.t4.id, w.t2.id]


def test_phieu_nguoi_gui_xep_theo_ten_hien_thi_thieu_ten_thi_email(db, tickets):
    """t1/t4 'Zeta Gui', t2 'Alpha Xu Ly', t3 không gắn nhân sự -> hiện email 'Mail.only@x.vn'."""
    w = tickets
    asc = _ticket_ids(db, w, "requester_name", "asc")
    assert asc[0] == w.t2.id and asc[1] == w.t3.id and set(asc[2:]) == {w.t1.id, w.t4.id}
    desc = _ticket_ids(db, w, "requester_name", "desc")
    assert set(desc[:2]) == {w.t1.id, w.t4.id} and desc[2] == w.t3.id and desc[3] == w.t2.id


def test_phieu_nguoi_xu_ly_chua_ai_nhan_xuong_cuoi_ca_hai_chieu(db, tickets):
    """t1 'Alpha Xu Ly' < t4 'Mail.only@x.vn' < t3 'Zeta Gui'; t2 chưa ai nhận (assignee_id = 0)."""
    w = tickets
    assert _ticket_ids(db, w, "assignee_name", "asc") == [w.t1.id, w.t4.id, w.t3.id, w.t2.id]
    assert _ticket_ids(db, w, "assignee_name", "desc") == [w.t3.id, w.t4.id, w.t1.id, w.t2.id]


def test_phieu_chu_de_bo_phan_o_trong_xuong_cuoi(db, tickets):
    w = tickets
    #  subject: t4 trống; department: t3 trống.
    assert _ticket_ids(db, w, "subject", "asc")[-1] == w.t4.id
    assert _ticket_ids(db, w, "subject", "desc")[-1] == w.t4.id
    assert _ticket_ids(db, w, "department", "asc")[-1] == w.t3.id
    assert _ticket_ids(db, w, "department", "desc")[-1] == w.t3.id
    assert _ticket_ids(db, w, "department", "asc")[:3] == [w.t2.id, w.t4.id, w.t1.id]   # IT < Ke toan (t4) < Kho (t1)


def test_phieu_cot_id_tu_them_cua_bang_va_khoa_la(db, tickets):
    w = tickets
    assert _ticket_ids(db, w, "id", "asc") == sorted([w.t1.id, w.t2.id, w.t3.id, w.t4.id])
    assert _ticket_ids(db, w, "id", "desc") == sorted([w.t1.id, w.t2.id, w.t3.id, w.t4.id], reverse=True)
    #  Khóa lạ: về thứ tự mặc định (id giảm dần), không nổ.
    assert _ticket_ids(db, w, "khong_co_cot_nay", "asc") == sorted(
        [w.t1.id, w.t2.id, w.t3.id, w.t4.id], reverse=True)


def test_phieu_khoa_phu_id_giam_dan_khi_trung_gia_tri(db, tickets):
    w = tickets
    for t in (w.t1, w.t2, w.t3, w.t4):
        t.priority = "normal"
    db.flush()
    expected = sorted([w.t1.id, w.t2.id, w.t3.id, w.t4.id], reverse=True)
    assert _ticket_ids(db, w, "priority", "asc") == expected
    assert _ticket_ids(db, w, "priority", "desc") == expected


def test_phieu_cap_nhat_xep_theo_thoi_gian(db, tickets):
    w = tickets
    w.t3.updated_at = datetime(2026, 1, 1)
    w.t1.updated_at = datetime(2026, 2, 1)
    w.t4.updated_at = datetime(2026, 3, 1)
    w.t2.updated_at = datetime(2026, 4, 1)
    db.flush()
    assert _ticket_ids(db, w, "updated_at", "asc") == [w.t3.id, w.t1.id, w.t4.id, w.t2.id]
    assert _ticket_ids(db, w, "updated_at", "desc") == [w.t2.id, w.t4.id, w.t1.id, w.t3.id]


# ── Tồn kho ───────────────────────────────────────────────────────────────────────

@pytest.fixture()
def stock(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "inventory", read=True)
    cty_b = Company(code="TKB", name="Cty Beta", is_active=True)
    cty_a = Company(code="TKA", name="Cty Alpha", is_active=True)
    db.add_all([cty_b, cty_a])
    db.flush()

    def _i(**kw):
        row = Inventory(**kw)
        db.add(row)
        db.flush()
        return row

    r1 = _i(company_id=cty_b.id, warehouse_code="K2", product_code="SP-C", product_name="Cat", unit="Kg",
            qty=10, avg_cost=5, value=50)
    r2 = _i(company_id=cty_a.id, warehouse_code="K1", product_code="SP-A", product_name="Ao", unit="Cai",
            qty=-3, avg_cost=100, value=-300)
    r3 = _i(company_id=cty_b.id, warehouse_code="K1", product_code="SP-B", product_name="Bot", unit="Hop",
            qty=0, avg_cost=0, value=0)
    #  Trống: công ty không còn trong danh mục, chưa có kho / tên / ĐVT.
    r4 = _i(company_id=0, warehouse_code="", product_code="SP-D", product_name="", unit="",
            qty=7, avg_cost=2, value=14)
    return SimpleNamespace(user=db.get(User, seed.u_req_id), cty_a=cty_a, cty_b=cty_b, r1=r1, r2=r2, r3=r3, r4=r4)


def _stock_ids(db, w, qs):
    mine = {w.r1.id, w.r2.id, w.r3.id, w.r4.id}
    resp = inv_ctl.list_inventory(request=_req(qs), pg=PAGE, db=db, user=w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_ton_kho_mac_dinh_van_la_ma_san_pham_tang_dan(db, stock):
    w = stock
    assert _stock_ids(db, w, "") == [w.r2.id, w.r3.id, w.r1.id, w.r4.id]   # SP-A, SP-B, SP-C, SP-D


def test_ton_kho_cot_so_xep_theo_so_that_so_0_khong_phai_o_trong(db, stock):
    w = stock
    assert _stock_ids(db, w, "sort_by=qty&sort_dir=asc") == [w.r2.id, w.r3.id, w.r4.id, w.r1.id]
    assert _stock_ids(db, w, "sort_by=qty&sort_dir=desc") == [w.r1.id, w.r4.id, w.r3.id, w.r2.id]
    assert _stock_ids(db, w, "sort_by=value&sort_dir=asc") == [w.r2.id, w.r3.id, w.r4.id, w.r1.id]
    assert _stock_ids(db, w, "sort_by=value&sort_dir=desc") == [w.r1.id, w.r4.id, w.r3.id, w.r2.id]
    assert _stock_ids(db, w, "sort_by=avg_cost&sort_dir=asc") == [w.r3.id, w.r4.id, w.r1.id, w.r2.id]
    assert _stock_ids(db, w, "sort_by=avg_cost&sort_dir=desc") == [w.r2.id, w.r1.id, w.r4.id, w.r3.id]


def test_ton_kho_cong_ty_xep_theo_ten_khong_theo_id_o_trong_cuoi(db, stock):
    w = stock
    assert w.cty_b.id < w.cty_a.id
    asc = _stock_ids(db, w, "sort_by=company&sort_dir=asc")
    assert asc[0] == w.r2.id and set(asc[1:3]) == {w.r1.id, w.r3.id} and asc[3] == w.r4.id
    desc = _stock_ids(db, w, "sort_by=company&sort_dir=desc")
    assert set(desc[:2]) == {w.r1.id, w.r3.id} and desc[2] == w.r2.id and desc[3] == w.r4.id


def test_ton_kho_cot_chu_o_trong_xuong_cuoi_ca_hai_chieu(db, stock):
    w = stock
    for key in ("warehouse_code", "product_name", "unit"):
        assert _stock_ids(db, w, f"sort_by={key}&sort_dir=asc")[-1] == w.r4.id, key
        assert _stock_ids(db, w, f"sort_by={key}&sort_dir=desc")[-1] == w.r4.id, key
    assert _stock_ids(db, w, "sort_by=product_name&sort_dir=asc") == [w.r2.id, w.r3.id, w.r1.id, w.r4.id]
    assert _stock_ids(db, w, "sort_by=product_name&sort_dir=desc") == [w.r1.id, w.r3.id, w.r2.id, w.r4.id]


def test_ton_kho_cot_id_khoa_la_va_khoa_phu(db, stock):
    w = stock
    assert _stock_ids(db, w, "sort_by=id&sort_dir=asc") == sorted([w.r1.id, w.r2.id, w.r3.id, w.r4.id])
    assert _stock_ids(db, w, "sort_by=nope&sort_dir=desc") == [w.r2.id, w.r3.id, w.r1.id, w.r4.id]
    #  Hai kho cùng tên SP -> khóa phụ id giảm dần.
    w.r1.product_name = "Ao"
    w.r2.product_name = "Ao"
    db.flush()
    got = _stock_ids(db, w, "sort_by=product_name&sort_dir=asc")
    assert got[:2] == sorted([w.r1.id, w.r2.id], reverse=True)


def test_ton_kho_xep_ket_hop_bo_loc_phan_loai_khong_join_hai_lan(db, stock):
    """Lọc `item_group` đã JOIN sang sản phẩm; xếp cùng lúc không được lỗi cột `id` mơ hồ."""
    w = stock
    resp = inv_ctl.list_inventory(request=_req("item_group=Khong+co&sort_by=qty&sort_dir=desc"), pg=PAGE, db=db,
                                  user=w.user)
    assert _items(resp) == []
