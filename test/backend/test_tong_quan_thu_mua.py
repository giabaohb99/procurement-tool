"""Trang Tổng quan (`/api/dashboard/overview`) — số nào thuộc khối quyền nào.

Bài này canh một lỗi đã xảy ra thật ở Đ-11: màn Tài chính lấy `top_suppliers`
để hiện "Top nhà cung cấp công nợ lớn". Hai con số đó KHÁC NHAU về cả nguồn lẫn
quyền:

  - `top_suppliers`      = CHI TIÊU, tính trên dòng đơn mua, nằm trong khối `purchase_order`;
  - `top_debt_suppliers` = NỢ CÒN LẠI, tính trên bảng công nợ, nằm trong khối `payable`.

Kế toán chỉ có quyền Công nợ nên khối `purchase_order` bị gác — bảng rỗng vĩnh
viễn mà không báo lỗi gì. Đúng kiểu sai âm thầm.
"""
import json

from app.modules.dashboard.controller import overview
from app.modules.payable.model import Payable
from app.modules.user.model import User


def _tong_quan(db, user):
    """`success()` trả `JSONResponse` chứ không trả dict — phải bóc thân phản hồi."""
    return json.loads(overview(db=db, user=user).body)["data"]


def _no(db, supplier_code, supplier_name, total, paid, status="unpaid"):
    """Một khoản công nợ tối thiểu — chỉ giữ các cột mà Tổng quan đọc tới."""
    row = Payable(
        supplier_code=supplier_code,
        supplier_name=supplier_name,
        total=total,
        paid_amount=paid,
        remaining=total - paid,
        status=status,
        due_date="",
    )
    db.add(row)
    return row


def test_top_ncc_cong_no_cong_don_theo_ncc_va_bo_khoan_da_tra(db, seed, grant_role):
    user = db.get(User, seed.u_req_id)
    grant_role(user.id, "payable", scope="all", read=True)

    _no(db, "NCC_A", "Nhà cung cấp A", 500, 200)      # còn 300
    _no(db, "NCC_A", "Nhà cung cấp A", 200, 0)        # còn 200 -> gộp thành 500
    _no(db, "NCC_B", "Nhà cung cấp B", 400, 0)        # còn 400
    _no(db, "NCC_C", "Nhà cung cấp C", 900, 900, status="paid")   # tất toán, không tính
    db.commit()

    data = _tong_quan(db, user)

    assert data["top_debt_suppliers"] == [
        {"name": "Nhà cung cấp A", "value": 500},
        {"name": "Nhà cung cấp B", "value": 400},
    ]


def test_chi_co_quyen_cong_no_van_thay_top_ncc_no(db, seed, grant_role):
    """Không có quyền Đơn mua hàng thì `top_suppliers` rỗng — nhưng số NỢ phải còn."""
    user = db.get(User, seed.u_req_id)
    grant_role(user.id, "payable", scope="all", read=True)

    _no(db, "NCC_A", "Nhà cung cấp A", 1000, 0)
    db.commit()

    data = _tong_quan(db, user)

    assert data["top_suppliers"] == []
    assert data["top_debt_suppliers"] == [{"name": "Nhà cung cấp A", "value": 1000}]


def test_khong_co_quyen_cong_no_thi_khong_lo_so_no(db, seed, grant_role):
    user = db.get(User, seed.u_req_id)
    grant_role(user.id, "purchase_request", scope="all", read=True)

    _no(db, "NCC_A", "Nhà cung cấp A", 1000, 0)
    db.commit()

    data = _tong_quan(db, user)

    assert data["top_debt_suppliers"] == []
    assert data["ap_aging"] == []
