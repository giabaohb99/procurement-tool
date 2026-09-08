"""bao-CR-310 — PHƯƠNG ÁN gắn thẳng lên dòng Yêu cầu mua hàng.

NSTM không phải lập Yêu cầu báo giá nữa: sau khi thu mua TIẾP NHẬN phiếu, họ gắn
phương án (NCC + giá) lên từng dòng YCMH — lấy từ kho khảo sát đã duyệt hoặc gõ tay —
rồi chốt. Test canh đúng những chỗ dễ vỡ:

  - cổng GIAI ĐOẠN: phiếu chưa được thu mua tiếp nhận thì chưa gắn được;
  - snapshot chép từ dòng khảo sát (sửa phiếu khảo sát sau đó không đổi phương án);
  - phương án gõ tay đánh dấu `source` riêng và tự điền theo dòng YCMH khi bỏ trống;
  - "đã chốt" SUY từ `is_chosen`, bấm lại là bỏ chốt — dòng YCMH không có cột nào lưu;
  - che cụm NCC khi thiếu `supplier.read`;
  - NSTM không đụng được dòng không giao cho mình.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.purchase_request import controller as C
from app.modules.purchase_request import option_service as OS
from app.modules.purchase_request.constants import PR_OPT_MANUAL, PR_OPT_SURVEY
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import (PROptionManualIn, PROptionSurveyIn,
                                                 PROptionUpdateIn)
from app.modules.user.model import User


def _data(resp):
    """Controller trả `JSONResponse` bọc phong bì {success, message, data}."""
    return json.loads(resp.body)["data"]


def _make_pr(db, seed, status="dispatched", code="PYC-CR310"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         department_id=seed.dept_id, status=status,
                         request_date="2026-09-07",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_code="SP-A", product_name="Nhãn SP A",
                             item_group="Nhãn", qty=100, unit="cuộn", price=4800,
                             vat_pct=8, amount=518400, assignee=seed.emp_nstm_code,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(it)
    db.commit()
    return pr, it


def _nstm(db, seed, cap_quyen, supplier_read=True):
    """NSTM thật — dựng đúng bộ quyền của vai trò `pur_staff`: ghi YCMH phạm vi
    'được giao', XEM được nhà cung cấp nhưng KHÔNG sửa danh mục NCC."""
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="assigned", read=True, write=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=supplier_read)
    return db.get(User, seed.u_nstm_id)


def _requester(db, seed, cap_quyen):
    """Người yêu cầu: đọc được phiếu của mình, KHÔNG có quyền nhà cung cấp.
    Đây là người CHỐT phương án (bao-CR-310)."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    return db.get(User, seed.u_req_id)


def _manager(db, seed, cap_quyen):
    """Quản lý / Admin thu mua: có `purchase_request.approve` nên chốt thẳng được,
    dùng cho hàng gấp khỏi chờ người yêu cầu."""
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="all",
              read=True, write=True, approve=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    return db.get(User, seed.u_nstm_id)


# ── Cổng giai đoạn ──────────────────────────────────────────────────────────────

def test_chua_tiep_nhan_thi_chua_gan_duoc(db, seed, cap_quyen):
    """Phiếu mới được TBP duyệt (`approved`) vẫn nằm ngoài giai đoạn: khách chốt điểm
    chèn là SAU khi thu mua tiếp nhận."""
    pr, it = _make_pr(db, seed, status="approved")
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
            product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user)
    assert e.value.status_code == 400
    assert "tiếp nhận" in e.value.detail


def test_phieu_da_dong_thi_khoa(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed, status="completed")
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
            product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user)
    assert e.value.status_code == 400


# ── Gắn từ kho khảo sát ─────────────────────────────────────────────────────────

def test_gan_tu_khao_sat_chep_snapshot(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    assert o["source"] == PR_OPT_SURVEY and o["source_label"] == "Từ khảo sát"
    assert o["public_id"] == 1 and o["display_label"] == "Phương án 1"
    assert o["snap_product_name"] == "Nhãn Sản Phẩm A"
    assert o["snap_price_by_volume"] == 5000.0 and o["snap_vat"] == 8.0
    assert o["snap_moq"] == 100.0 and o["snap_delivery_time"] == "7 ngày"
    assert o["supplier_code"] == "NX" and o["supplier_name"] == seed.sup_name
    assert o["snap_internal_code"] == "NX-NHAN-A"       # nội bộ NSTM, có quyền nên thấy
    assert o["is_chosen"] is False                       # gắn xong CHƯA phải là chốt


def test_khong_gan_trung_mot_dong_khao_sat(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    data = PROptionSurveyIn(product_survey_line_id=seed.psl_nhan_1_id)
    C.add_option_from_survey(pr.id, it.id, data, db=db, user=user)
    with pytest.raises(HTTPException) as e:
        C.add_option_from_survey(pr.id, it.id, data, db=db, user=user)
    assert e.value.status_code == 400


def test_dong_khao_sat_chua_duyet_thi_tu_choi(db, seed, cap_quyen):
    from app.modules.survey.model import SurveyProductLine
    psl = db.get(SurveyProductLine, seed.psl_nhan_2_id)
    psl.line_approve = ""
    db.commit()
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
            product_survey_line_id=seed.psl_nhan_2_id), db=db, user=user)
    assert e.value.status_code == 400


def test_snapshot_khong_doi_khi_phieu_khao_sat_sua_gia(db, seed, cap_quyen):
    """Lý do bảng này CHÉP chứ không đọc live: giá khảo sát đổi về sau KHÔNG được
    làm đổi phương án của một YCMH đang chạy."""
    from app.modules.survey.model import SurveyProductLine
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user)
    psl = db.get(SurveyProductLine, seed.psl_nhan_1_id)
    psl.price_by_volume = 9999
    db.commit()
    assert float(OS.options_of(db, it.id)[0].snap_price_by_volume) == 5000.0


# ── Nhập tay ────────────────────────────────────────────────────────────────────

def test_nhap_tay_tu_dien_theo_dong_ycmh(db, seed, cap_quyen):
    """Bỏ trống tên SP / ĐVT / VAT thì lấy theo dòng YCMH — thao tác này phải nhanh."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(
        supplier_code="NX", snap_price_by_volume=4700), db=db, user=user))
    assert o["source"] == PR_OPT_MANUAL and o["source_label"] == "Nhập tay"
    assert o["product_survey_line_id"] == 0
    assert o["snap_product_name"] == "Nhãn SP A"      # theo dòng YCMH
    assert o["snap_quote_unit"] == "cuộn"             # theo ĐVT dòng
    assert o["snap_vat"] == 8.0                       # theo vat_pct dòng
    assert o["supplier_name"] == seed.sup_name        # mã có trong danh mục -> tra ra tên


def test_nhap_tay_thieu_ncc_thi_chan(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.add_option_manual(pr.id, it.id, PROptionManualIn(snap_price_by_volume=4700),
                            db=db, user=user)
    assert e.value.status_code == 400


def test_nhap_tay_can_quyen_xem_ncc(db, seed, cap_quyen):
    """Cổng là `supplier.read`, KHÔNG phải `supplier.write` — `pur_staff` chỉ có read,
    đòi write là khóa chết đúng người dùng tính năng này."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen, supplier_read=False)
    with pytest.raises(HTTPException) as e:
        C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                            db=db, user=user)
    assert e.value.status_code == 403


def test_ma_ncc_ngoai_danh_muc_giu_lai_ma(db, seed, cap_quyen):
    """Tra không ra tên thì trả lại chính mã — trả rỗng là mất luôn thông tin duy nhất."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="CHUA-CO"),
                                  db=db, user=user))
    assert o["supplier_name"] == "CHUA-CO"


# ── Chốt / bỏ chốt ──────────────────────────────────────────────────────────────

def test_chot_roi_bam_lai_la_bo_chot(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    a = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=nstm))
    b = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_2_id), db=db, user=nstm))

    user = _requester(db, seed, cap_quyen)
    C.choose_option(pr.id, it.id, a["id"], db=db, user=user)
    assert OS.chosen_option_of(db, it.id).id == a["id"]
    # Chốt phương án khác -> phương án cũ tự nhả, mỗi dòng chỉ một phương án chốt
    C.choose_option(pr.id, it.id, b["id"], db=db, user=user)
    assert OS.chosen_option_of(db, it.id).id == b["id"]
    # Bấm lại đúng phương án đang chốt -> bỏ chốt cả dòng
    out = _data(C.choose_option(pr.id, it.id, b["id"], db=db, user=user))
    assert out["is_chosen"] is False
    assert OS.chosen_option_of(db, it.id) is None


def test_nstm_gan_duoc_nhung_khong_tu_chot(db, seed, cap_quyen):
    """NSTM chỉ biết giá bao nhiêu; người yêu cầu mới biết giá đó còn đáng mua không."""
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=nstm))
    with pytest.raises(HTTPException) as e:
        C.choose_option(pr.id, it.id, o["id"], db=db, user=nstm)
    assert e.value.status_code == 403
    assert OS.chosen_option_of(db, it.id) is None


def test_quan_ly_thu_mua_chot_thang_duoc(db, seed, cap_quyen):
    """Hàng gấp: người có `purchase_request.approve` chốt luôn, khỏi chờ người yêu cầu."""
    pr, it = _make_pr(db, seed)
    user = _manager(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    C.choose_option(pr.id, it.id, o["id"], db=db, user=user)
    assert OS.chosen_option_of(db, it.id).id == o["id"]


def test_phieu_tra_kem_so_phuong_an_va_ban_da_chot(db, seed, cap_quyen):
    """`option_count` + `chosen_option` là thứ màn chi tiết đọc để biết dòng nào đã
    chốt — không có cột nào trên dòng YCMH lưu việc đó."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    a = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_2_id), db=db, user=user)
    line = C._out(db, pr, user)["items"][0]
    assert line["option_count"] == 2 and line["chosen_option"] is None
    C.choose_option(pr.id, it.id, a["id"], db=db, user=_requester(db, seed, cap_quyen))
    line = C._out(db, pr, user)["items"][0]
    assert line["chosen_option"]["id"] == a["id"]
    assert line["chosen_option"]["snap_price_by_volume"] == 5000.0


# ── Sửa / gỡ ────────────────────────────────────────────────────────────────────

def test_sua_gia_va_ghi_chu(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    out = _data(C.update_option(pr.id, it.id, o["id"],
                                PROptionUpdateIn(snap_price_by_volume=4900,
                                                 nstm_note="NCC đồng ý giảm"),
                                db=db, user=user))
    assert out["snap_price_by_volume"] == 4900.0
    assert out["nstm_note"] == "NCC đồng ý giảm"
    assert out["supplier_code"] == "NX"       # đổi NCC cố ý không đi qua đường này


def test_go_phuong_an(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    C.delete_option(pr.id, it.id, o["id"], db=db, user=user)
    assert OS.options_of(db, it.id) == []


def test_so_hieu_khong_dung_lai_so_da_xoa(db, seed, cap_quyen):
    """Gỡ phương án 1 rồi gắn mới phải ra "Phương án 3": số hiệu là nhãn để hai bên gọi
    nhau trong lúc trao đổi, dùng lại số cũ là hai người nói về hai thứ khác nhau."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    a = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_2_id), db=db, user=user)
    C.delete_option(pr.id, it.id, a["id"], db=db, user=user)
    out = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                                    db=db, user=user))
    assert out["display_label"] == "Phương án 3"


def test_toi_da_nam_phuong_an_moi_dong(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    for _ in range(OS.MAX_OPTIONS_PER_LINE):
        C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                            db=db, user=user)
    with pytest.raises(HTTPException) as e:
        C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                            db=db, user=user)
    assert e.value.status_code == 400


# ── Ẩn nhà cung cấp + hàng rào theo dòng ────────────────────────────────────────

def test_nguoi_yeu_cau_thay_gia_nhung_khong_thay_ncc(db, seed, cap_quyen):
    """Đúng luật cụm `pur` của Task 4: người YC cần so giá để chốt, chỉ không được
    biết giá đó của ai."""
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=nstm)

    req = _requester(db, seed, cap_quyen)
    rows = _data(C.list_options(pr.id, it.id, db=db, user=req))["items"]
    assert len(rows) == 1
    o = rows[0]
    assert o["snap_price_by_volume"] == 5000.0 and o["snap_vat"] == 8.0
    assert o["supplier_code"] == "" and o["supplier_name"] == ""
    assert o["snap_internal_code"] == "" and o["supplier_survey_id"] == 0


def test_nstm_khong_dung_duoc_dong_cua_nguoi_khac(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    it2 = PurchaseRequestItem(pr_id=pr.id, product_code="SP-B", product_name="Thùng SP B",
                              item_group="Thùng", qty=10, unit="cái", price=8000,
                              vat_pct=8, amount=86400, assignee=seed.emp_backup_code,
                              created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(it2)
    db.commit()
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.add_option_from_survey(pr.id, it2.id, PROptionSurveyIn(
            product_survey_line_id=seed.psl_thung_1_id), db=db, user=user)
    assert e.value.status_code == 403


def test_khong_gan_xuyen_phieu(db, seed, cap_quyen):
    """Dòng phải thuộc đúng phiếu đang mở — thiếu vế này thì gõ id dòng của phiếu khác
    vào URL là gắn phương án xuyên phiếu."""
    pr_a, _ = _make_pr(db, seed, code="PYC-CR310-A")
    pr_b, it_b = _make_pr(db, seed, code="PYC-CR310-B")
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.add_option_from_survey(pr_a.id, it_b.id, PROptionSurveyIn(
            product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user)
    assert e.value.status_code == 404
