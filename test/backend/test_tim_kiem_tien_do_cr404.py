"""bao-CR-404 — ô TÌM KIẾM của màn Tiến độ mua hàng.

Lỗi gốc: `_build_query` lọc thêm `POItem.nspt`, một cột KHÔNG tồn tại (NSPT chỉ nằm
trên đơn). Mọi lượt gõ vào ô tìm kiếm ném `AttributeError` -> 500. Giao diện v1 chỉ tự
báo lỗi cho request không-phải-GET, nên màn hình đứng im với bảng cũ và người dùng đọc
ra là "ô tìm kiếm hỏng". Xuất Excel kèm từ khóa cũng chết cùng đường vì dùng chung hàm.

Hai chốt ở đây:

1. `_search_columns()` **gọi được** — cột không có thật thì nổ ngay tại đây, đỏ ở test
   thay vì đỏ ở màn hình người dùng.
2. Chạy thật `_build_query` với `q=` và khẳng định nó LỌC (chứ không chỉ "không nổ").
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.user.model import User


def req(qs: str):
    """Request giả — `_build_query` chỉ đụng tới `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


@pytest.fixture
def nguoi_xem_het(db, cap_quyen):
    """Tài khoản thấy mọi đơn — để bài kiểm đo đúng ô tìm kiếm, không đo phạm vi."""
    user = User(email="tiendo@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    db.commit()
    return user


@pytest.fixture
def ba_don(db):
    """3 đơn khác nhau ở 3 chỗ mà ô tìm kiếm phải quét được: mã SP, tên NCC, NSPT."""
    data = [
        ("PO001", "Công ty Bao bì Phương Nam", "Lâm Bích Dư", "VTO187", "Seal thoát khí"),
        ("PO002", "Công ty Bao bì Đông Tây", "Nguyễn Thanh Tiên", "THCO183", "Thùng Agritech"),
        ("PO003", "Công ty Bao bì Cẩm Hưng", "Nguyễn Thanh Tiên", "NHG5136", "Nuti Rice Max"),
    ]
    for code, ncc, nspt, sp_code, sp_name in data:
        po = PurchaseOrder(code=code, status="approved", supplier_name=ncc, nspt=nspt,
                           order_date="2026-08-01")
        db.add(po)
        db.flush()
        it = POItem(po_id=po.id, product_code=sp_code, product_name=sp_name,
                    qty_order=10, price=1000)
        db.add(it)
        db.flush()
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1))
    db.commit()


def _tim(db, user, kw: str) -> set[str]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(f"q={kw}"), db, user, prof, True, True)
    return {po.code for po, _it, _dl in q.all()}


def test_moi_cot_cua_o_tim_kiem_phai_la_cot_that():
    """Chốt chính. Khai một cột không có thật thì dòng này nổ AttributeError."""
    cols = pp._search_columns()
    assert len(cols) >= 10
    for c in cols:
        assert c.class_ in (PurchaseOrder, POItem, PODelivery)
        assert hasattr(c.class_, c.key)


def test_tim_theo_ma_san_pham_ra_dung_mot_don(db, nguoi_xem_het, ba_don):
    assert _tim(db, nguoi_xem_het, "VTO187") == {"PO001"}


def test_tim_theo_ten_ncc_va_theo_nspt_deu_chay(db, nguoi_xem_het, ba_don):
    assert _tim(db, nguoi_xem_het, "Cẩm Hưng") == {"PO003"}
    # NSPT nằm trên ĐƠN — đúng chỗ đã gây ra lỗi
    assert _tim(db, nguoi_xem_het, "Thanh Tiên") == {"PO002", "PO003"}


def test_khong_khop_thi_rong_chu_khong_tra_ve_ca_bang(db, nguoi_xem_het, ba_don):
    """Lỗi cũ trả 500 và màn hình giữ nguyên bảng cũ — trông y như "tìm không lọc"."""
    assert _tim(db, nguoi_xem_het, "khong-co-gi-khop") == set()
    assert _tim(db, nguoi_xem_het, "") == {"PO001", "PO002", "PO003"}
