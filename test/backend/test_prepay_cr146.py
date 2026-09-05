"""
test_prepay_cr146.py — CR-146 (ticket #12): cờ THANH TOÁN TRƯỚC trên phiếu YCTT.

Đơn hàng trả trước nhưng bản in mặc định ghi "Thanh toán công nợ ..." → sai bản chất.
Người lập phiếu đánh dấu prepay = 1 thì frontend đổi nội dung in thành
"Thanh toán trước cho nhà cung cấp <tên NCC> <kỳ>".

Phủ:
1. Mặc định 0 (phiếu cũ + người dùng không chọn gì) → bản in giữ nguyên như trước.
2. Chọn prepay lúc tạo → lưu đúng; giá trị lạ (2, -1...) chuẩn về 1.
3. Sửa khi phiếu còn Nháp; PATCH không gửi prepay thì giữ nguyên.
4. Endpoint /print trả prepay để trang in đổi câu nội dung.
"""
import json

import pytest

from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.controller import print_
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate


@pytest.fixture
def payable(db, seed):
    p = Payable(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                source_type="goods", po_code="PO-TT-02", invoice_no="HD-P01",
                incur_date="2026-08-20", due_date="2026-09-20",
                total=500000, paid_amount=0, remaining=500000,
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.commit()
    return p


def _create(db, seed, payable, prepay=None):
    kw = {} if prepay is None else {"prepay": prepay}
    data = PRequestCreate(request_date="2026-08-20",
                          lines=[LineIn(payable_id=payable.id, amount=500000)], **kw)
    return S.create_requests(db, data, seed.u_req_id)[0]


class TestLuuCoTraTruoc:
    def test_mac_dinh_la_cong_no(self, db, seed, payable):
        """Không chọn gì → 0, bản in giữ nguyên 'Thanh toán công nợ' như trước CR-146."""
        assert _create(db, seed, payable).prepay == 0

    def test_chon_tra_truoc_luc_tao(self, db, seed, payable):
        assert _create(db, seed, payable, 1).prepay == 1

    @pytest.mark.parametrize("raw, expect", [(2, 1), (-1, 1), (0, 0)])
    def test_gia_tri_la_chuan_ve_0_1(self, db, seed, payable, raw, expect):
        """Cột chỉ mang nghĩa cờ — mọi giá trị khác 0 chuẩn về 1."""
        assert _create(db, seed, payable, raw).prepay == expect

    def test_sua_khi_con_nhap(self, db, seed, payable):
        req = _create(db, seed, payable)
        req2 = S.update_request(db, req.id, PRequestUpdate(prepay=1), seed.u_req_id)
        assert req2.prepay == 1

    def test_khong_gui_thi_giu_nguyen(self, db, seed, payable):
        """PATCH chỉ sửa ghi chú → cờ trả trước không bị reset."""
        req = _create(db, seed, payable, 1)
        req2 = S.update_request(db, req.id, PRequestUpdate(note="sửa ghi chú"), seed.u_req_id)
        assert req2.prepay == 1


def test_ban_in_tra_co_prepay(db, seed, payable, cap_quyen):
    """Trang in đọc d['prepay'] để đổi câu 'Thanh toán trước cho nhà cung cấp ...'.

    Phải cấp quyền thật cho người in: từ 05/09/2026 route `/print` nạp phiếu qua
    `get_scoped` (P0 #4), nên `user=None` không còn qua cổng. Bài này canh NỘI DUNG bản
    in, không canh phân quyền — cấp phạm vi «tất cả» cho khỏi vướng.
    """
    from types import SimpleNamespace

    req = _create(db, seed, payable, 1)
    cap_quyen(seed.u_req_id, "payment_request", scope="all", read=True, print=True)
    d = json.loads(print_(req.id, db=db, user=SimpleNamespace(id=seed.u_req_id)).body)["data"]
    assert d["prepay"] == 1
