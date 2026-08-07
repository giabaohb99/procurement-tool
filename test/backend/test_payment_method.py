"""
test_payment_method.py — CR-035: hình thức thanh toán trên phiếu Yêu cầu thanh toán (YCTT).

Người lập phiếu chọn Chuyển khoản (transfer) hay Tiền mặt (cash).
Bản in chỉ in cụm "Thông tin chuyển khoản" khi là chuyển khoản; chọn tiền mặt thì
server KHÔNG trả số TK/ngân hàng ra bản in.

Phủ:
1. Mặc định 'transfer' (phiếu cũ + người dùng không chọn gì) → bản in giữ nguyên như trước.
2. Chọn 'cash' lúc tạo → lưu đúng.
3. Giá trị lạ → về 'transfer' (không để bản in mất thông tin NCC vì gõ sai).
4. Sửa hình thức khi phiếu còn Nháp.
5. Endpoint /print: cash thì bank_account + bank_name rỗng, transfer thì có.
"""
import json

import pytest

from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.controller import print_
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate
from app.modules.supplier.model import Supplier


@pytest.fixture
def payable(db, seed):
    """1 khoản nợ đủ điều kiện tạo YCTT (đã có Số hóa đơn) + NCC có thông tin ngân hàng."""
    sup = db.query(Supplier).filter(Supplier.code == "NX").first()
    sup.bank_account = "161816186868"
    sup.bank_name = "Ngân hàng TMCP Á Châu (ACB) - CN Hóc Môn"
    p = Payable(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                source_type="goods", po_code="PO-TT-01", invoice_no="HD-D02",
                incur_date="2026-08-04", due_date="2026-09-04",
                total=1000000, paid_amount=0, remaining=1000000,
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.commit()
    return p


def _create(db, seed, payable, method=None):
    kw = {} if method is None else {"payment_method": method}
    data = PRequestCreate(request_date="2026-08-04",
                          lines=[LineIn(payable_id=payable.id, amount=1000000)], **kw)
    return S.create_requests(db, data, seed.u_req_id)[0]


class TestLuuHinhThuc:
    def test_mac_dinh_la_chuyen_khoan(self, db, seed, payable):
        """Không chọn gì → 'transfer', y như hành vi trước CR-035."""
        assert _create(db, seed, payable).payment_method == "transfer"

    @pytest.mark.parametrize("m", ["cash", "transfer"])
    def test_chon_luc_tao(self, db, seed, payable, m):
        assert _create(db, seed, payable, m).payment_method == m

    @pytest.mark.parametrize("bad", ["CASH", "tienmat", "", "bank"])
    def test_gia_tri_la_ve_chuyen_khoan(self, db, seed, payable, bad):
        """Gõ sai/giá trị lạ không được làm bản in mất thông tin chuyển khoản."""
        assert _create(db, seed, payable, bad).payment_method == "transfer"

    def test_sua_khi_con_nhap(self, db, seed, payable):
        req = _create(db, seed, payable)
        req2 = S.update_request(db, req.id, PRequestUpdate(payment_method="cash"), seed.u_req_id)
        assert req2.payment_method == "cash"

    def test_sua_gia_tri_la_van_ve_chuyen_khoan(self, db, seed, payable):
        req = _create(db, seed, payable, "cash")
        req2 = S.update_request(db, req.id, PRequestUpdate(payment_method="xxx"), seed.u_req_id)
        assert req2.payment_method == "transfer"

    def test_khong_gui_thi_giu_nguyen(self, db, seed, payable):
        """PATCH chỉ sửa ghi chú → hình thức thanh toán không bị reset."""
        req = _create(db, seed, payable, "cash")
        req2 = S.update_request(db, req.id, PRequestUpdate(note="sửa ghi chú"), seed.u_req_id)
        assert req2.payment_method == "cash"


def _print_data(db, rid) -> dict:
    """Gọi thẳng endpoint /print (bỏ qua tầng Depends) và bóc `data` khỏi envelope."""
    return json.loads(print_(rid, db=db, user=None).body)["data"]


class TestBanIn:
    def test_chuyen_khoan_co_thong_tin_ngan_hang(self, db, seed, payable):
        req = _create(db, seed, payable, "transfer")
        d = _print_data(db, req.id)
        assert d["payment_method"] == "transfer"
        assert d["bank_account"] == "161816186868"
        assert d["bank_name"].startswith("Ngân hàng")

    def test_tien_mat_thi_de_trong(self, db, seed, payable):
        """Chi tiền mặt: server không trả số TK/ngân hàng — cụm chuyển khoản trên bản in để trống."""
        req = _create(db, seed, payable, "cash")
        d = _print_data(db, req.id)
        assert d["payment_method"] == "cash"
        assert d["bank_account"] == "" and d["bank_name"] == ""
