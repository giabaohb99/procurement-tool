"""
test_print_texts_cr149.py — CR-149 (ticket #14): sửa câu chữ bản in phiếu YCTT.

Người dùng muốn tự sửa 3 câu trên bản in (Nội dung thanh toán / Diễn giải bảng /
Nội dung chuyển khoản) thay vì luôn in câu tự động theo prepay (CR-146).
Lưu 1 cột JSON `print_texts` {"content","line_desc","transfer"}; khóa rỗng -> in câu tự động.

Phủ:
1. Phiếu mới / chưa sửa -> API trả {} (bản in giữ nguyên câu tự động, không cần backfill).
2. Sửa lúc Nháp: lưu đúng, khóa lạ bị bỏ, chuỗi cắt 500 ký tự, xóa trắng -> về {}.
3. Phiếu Chờ duyệt / Đã duyệt: PATCH CHỈ chứa print_texts thì được (in sau khi duyệt);
   kèm bất kỳ trường nào khác thì vẫn khóa như CR-066.
4. Đã chi / Đã từ chối: khóa hẳn, kể cả chỉ sửa print_texts.
5. Endpoint /print trả dict đã parse cho trang in.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.controller import print_
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate


@pytest.fixture
def payable(db, seed):
    p = Payable(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                source_type="goods", po_code="PO-PT-01", invoice_no="HD-PT01",
                incur_date="2026-08-20", due_date="2026-09-20",
                total=500000, paid_amount=0, remaining=500000,
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.commit()
    return p


@pytest.fixture
def req(db, seed, payable):
    data = PRequestCreate(request_date="2026-08-20",
                          lines=[LineIn(payable_id=payable.id, amount=500000)])
    return S.create_requests(db, data, seed.u_req_id)[0]


def _set_status(db, req, status):
    """Đặt thẳng trạng thái để test khóa sửa — không đi qua set_status (khỏi đụng công nợ)."""
    req.status = status
    db.commit()
    return req


PT = {"content": "Chi tạm ứng đợt 1", "line_desc": "TT theo HĐ 05/2026", "transfer": "DEGO chuyen tien HD 05"}


class TestSuaLucNhap:
    def test_phieu_moi_tra_rong(self, db, seed, req):
        """Chưa sửa gì -> {} — bản in dùng câu tự động, phiếu cũ không cần backfill."""
        assert S.parse_print_texts(req.print_texts) == {}

    def test_luu_du_3_khoa(self, db, seed, req):
        r = S.update_request(db, req.id, PRequestUpdate(print_texts=PT), seed.u_req_id)
        assert S.parse_print_texts(r.print_texts) == PT

    def test_khoa_la_bi_bo(self, db, seed, req):
        r = S.update_request(db, req.id,
                             PRequestUpdate(print_texts={"content": "A", "hacker": "x", "status": "paid"}),
                             seed.u_req_id)
        assert S.parse_print_texts(r.print_texts) == {"content": "A"}

    def test_cat_500_ky_tu(self, db, seed, req):
        r = S.update_request(db, req.id, PRequestUpdate(print_texts={"content": "x" * 900}), seed.u_req_id)
        assert len(S.parse_print_texts(r.print_texts)["content"]) == 500

    def test_xoa_trang_ve_cau_tu_dong(self, db, seed, req):
        S.update_request(db, req.id, PRequestUpdate(print_texts=PT), seed.u_req_id)
        r = S.update_request(db, req.id, PRequestUpdate(print_texts={"content": "", "line_desc": "  "}),
                             seed.u_req_id)
        assert r.print_texts == "" and S.parse_print_texts(r.print_texts) == {}

    def test_patch_khac_khong_dung_den(self, db, seed, req):
        """PATCH chỉ sửa ghi chú -> print_texts giữ nguyên (exclude_unset)."""
        S.update_request(db, req.id, PRequestUpdate(print_texts=PT), seed.u_req_id)
        r = S.update_request(db, req.id, PRequestUpdate(note="sửa ghi chú"), seed.u_req_id)
        assert S.parse_print_texts(r.print_texts) == PT


class TestSauKhiGuiDuyet:
    @pytest.mark.parametrize("status", ["submitted", "approved"])
    def test_chi_print_texts_thi_duoc(self, db, seed, req, status):
        """Người dùng in phiếu SAU khi duyệt nên câu chữ bản in phải sửa được lúc đó."""
        _set_status(db, req, status)
        r = S.update_request(db, req.id, PRequestUpdate(print_texts=PT), seed.u_req_id)
        assert S.parse_print_texts(r.print_texts) == PT

    @pytest.mark.parametrize("status", ["submitted", "approved"])
    def test_kem_truong_khac_van_khoa(self, db, seed, req, status):
        """Khóa CR-066 không được nới: PATCH kèm note/tiền/dòng vẫn bị chặn."""
        _set_status(db, req, status)
        with pytest.raises(HTTPException) as e:
            S.update_request(db, req.id, PRequestUpdate(print_texts=PT, note="lách khóa"), seed.u_req_id)
        assert e.value.status_code == 400

    @pytest.mark.parametrize("status", ["paid", "cancelled"])
    def test_da_chi_tu_choi_khoa_han(self, db, seed, req, status):
        _set_status(db, req, status)
        with pytest.raises(HTTPException) as e:
            S.update_request(db, req.id, PRequestUpdate(print_texts=PT), seed.u_req_id)
        assert e.value.status_code == 400


def test_ban_in_tra_dict_da_parse(db, seed, req):
    """Trang in đọc d['print_texts'] (dict, không phải chuỗi JSON) để đè câu tự động."""
    S.update_request(db, req.id, PRequestUpdate(print_texts=PT), seed.u_req_id)
    d = json.loads(print_(req.id, db=db, user=None).body)["data"]
    assert d["print_texts"] == PT


@pytest.mark.parametrize("raw", [None, "", "khong phai json", "[1,2]", '"chuoi"'])
def test_gia_tri_hong_khong_lung(raw):
    """Hàng cũ để NULL (migration nullable=True) hay dữ liệu hỏng -> parse trả {} chứ không nổ."""
    assert S.parse_print_texts(raw) == {}
