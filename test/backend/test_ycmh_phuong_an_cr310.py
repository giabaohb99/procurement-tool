"""bao-CR-310 — PHƯƠNG ÁN gắn thẳng lên dòng Yêu cầu mua hàng.

NSTM không phải lập Yêu cầu báo giá nữa: sau khi thu mua TIẾP NHẬN phiếu, họ gắn
phương án (NCC + giá) lên từng dòng YCMH — lấy từ kho khảo sát đã duyệt hoặc gõ tay —
rồi chốt. Test canh đúng những chỗ dễ vỡ:

  - cổng GIAI ĐOẠN: phiếu chưa được thu mua tiếp nhận thì chưa gắn được;
  - snapshot chép từ dòng khảo sát (sửa phiếu khảo sát sau đó không đổi phương án);
  - phương án gõ tay đánh dấu `source` riêng và tự điền theo dòng YCMH khi bỏ trống;
  - "đã chốt" SUY từ `is_chosen`, bấm lại là bỏ chốt — dòng YCMH không có cột nào lưu;
  - che cụm NCC khi thiếu `supplier.read`;
  - NSTM không đụng được dòng không giao cho mình;
  - đợt 3b (khuôn YCBG `complete_sr`): NSTM "chốt hoàn thành xử lý" phần của mình
    (dòng trống phải tick chốt rỗng), chốt xong NSTM hết sửa và người yêu cầu mới
    bắt đầu chọn; muốn sửa tiếp phải được người yêu cầu / quản lý MỞ LẠI dòng.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.purchase_request import controller as C
from app.modules.purchase_request import option_service as OS
from app.modules.purchase_request import service as SV
from app.modules.purchase_request.constants import (PR_OPT_MANUAL, PR_OPT_ORIGINAL,
                                                    PR_OPT_SURVEY)
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import (PRAssignSupplierIn,
                                                 PRAssignSupplierLineIn,
                                                 PROptionCompleteIn, PROptionManualIn,
                                                 PROptionSupplierIn, PROptionSurveyIn,
                                                 PROptionUpdateIn)
from app.modules.user.model import User


def _data(resp):
    """Controller trả `JSONResponse` bọc phong bì {success, message, data}."""
    return json.loads(resp.body)["data"]


@pytest.fixture(autouse=True)
def bat_cum_phuong_an(monkeypatch):
    """bao-CR-468: cả cụm phương án nằm sau một công tắc và mặc định TẮT. Bộ kiểm này kiểm
    nghiệp vụ BÊN TRONG cụm nên bật sẵn; bản thân công tắc có bộ kiểm riêng
    (`test_cong_tac_phuong_an_cr468.py`)."""
    monkeypatch.setattr(OS, "options_enabled", lambda: True)


def _complete(db, pr, user, empty_ids=None):
    """NSTM "Chốt hoàn thành xử lý" phần của mình (đợt 3b) — người yêu cầu chỉ chọn
    được sau bước này, nên mọi test chốt phương án đều phải đi qua đây trước."""
    return _data(C.complete_options(
        pr.id, PROptionCompleteIn(empty_item_ids=empty_ids or []), db=db, user=user))


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
    _complete(db, pr, nstm)

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
    _complete(db, pr, user)
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
    # `_out` sinh bù PHƯƠNG ÁN 0 và tick chọn sẵn (H.10.2): chưa ai chọn gì thì mặc
    # định là "mua theo đúng yêu cầu gốc"; option_count vẫn chỉ đếm phương án NSTM gắn.
    assert line["option_count"] == 2
    assert line["chosen_option"]["public_id"] == 0
    assert line["options_done"] is False and line["no_option"] is False
    _complete(db, pr, user)
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
    # list_options cũng sinh bù PHƯƠNG ÁN 0 — public_id 0 nên đứng đầu danh sách
    assert len(rows) == 2 and rows[0]["public_id"] == 0
    o = rows[1]
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


# ── Đợt 3b: chốt hoàn thành xử lý + chốt rỗng + mở lại (khuôn YCBG) ─────────────

def test_con_dong_trong_khong_tick_rong_thi_chan(db, seed, cap_quyen):
    """Y luật `complete_sr`: dòng chưa có phương án mà không tick chốt rỗng thì chưa
    được tuyên bố xong — chốt rỗng phải là hành động CÓ Ý THỨC, không phải mặc định."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        _complete(db, pr, user)
    assert e.value.status_code == 400
    assert "chốt rỗng" in e.value.detail


def test_chot_rong_dong_khong_co_ncc_phu_hop(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    out = _complete(db, pr, user, [it.id])
    assert out["done"] == 1 and out["empty"] == 1 and out["all_done"] is True
    line = C._out(db, pr, user)["items"][0]
    assert line["options_done"] is True and line["no_option"] is True


def test_dong_co_phuong_an_thi_tick_rong_khong_an(db, seed, cap_quyen):
    """Vừa có phương án vừa bị tick rỗng thì phương án thắng — cùng cách xử YCBG."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"), db=db, user=user)
    out = _complete(db, pr, user, [it.id])
    assert out["done"] == 1 and out["empty"] == 0
    line = C._out(db, pr, user)["items"][0]
    assert line["options_done"] is True and line["no_option"] is False


def test_sau_chot_nstm_het_sua_phuong_an(db, seed, cap_quyen):
    """Chốt xong là khóa các cửa ghi: gắn từ khảo sát, nhập tay, gỡ. Riêng SỬA còn
    đúng một khe GIÁ (H.10.4) — kiểm ở test_sau_chot_van_sua_duoc_gia bên dưới."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                                  db=db, user=user))
    _complete(db, pr, user)
    for act in (
        lambda: C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
            product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user),
        lambda: C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                                    db=db, user=user),
        lambda: C.delete_option(pr.id, it.id, o["id"], db=db, user=user),
    ):
        with pytest.raises(HTTPException) as e:
            act()
        assert e.value.status_code == 400
        assert "chốt hoàn thành" in e.value.detail
    # Sửa trường NGOÀI giá sau chốt cũng bị chặn — khe H.10.4 chỉ mở đúng ô giá
    with pytest.raises(HTTPException) as e:
        C.update_option(pr.id, it.id, o["id"], PROptionUpdateIn(nstm_note="thêm ghi chú"),
                        db=db, user=user)
    assert e.value.status_code == 400
    assert "GIÁ" in e.value.detail


def test_chua_chot_thi_nguoi_yc_chua_chon_duoc(db, seed, cap_quyen):
    """Người yêu cầu chỉ chọn trên danh sách NSTM đã tuyên bố xong — chưa chốt mà
    chọn là chọn trên dữ liệu đang gắn dở."""
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                                  db=db, user=nstm))
    req = _requester(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        C.choose_option(pr.id, it.id, o["id"], db=db, user=req)
    assert e.value.status_code == 400
    assert "chưa chốt hoàn thành" in e.value.detail


def test_nguoi_yc_mo_lai_dong_cho_nstm_sua_tiep(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    _complete(db, pr, nstm, [it.id])                    # chốt rỗng
    req = _requester(db, seed, cap_quyen)
    out = _data(C.reopen_options_line(pr.id, it.id, db=db, user=req))
    assert out["options_done"] is False and out["no_option"] is False
    # Mở lại xong NSTM gắn tiếp được — và cờ chốt rỗng cũ không được sót lại
    C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"), db=db, user=nstm)
    line = C._out(db, pr, nstm)["items"][0]
    assert line["options_done"] is False and line["no_option"] is False


def test_nstm_khong_tu_mo_lai_duoc(db, seed, cap_quyen):
    """Mở lại là mặt trái của quyền CHỌN (người yêu cầu / quản lý) — NSTM tự mở lại
    được thì cờ chốt hoàn thành thành vô nghĩa."""
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    _complete(db, pr, nstm, [it.id])
    with pytest.raises(HTTPException) as e:
        C.reopen_options_line(pr.id, it.id, db=db, user=nstm)
    assert e.value.status_code == 403


def test_chot_theo_nguoi_goi_khong_dung_dong_nguoi_khac(db, seed, cap_quyen):
    """Phiếu nhiều NSTM: mỗi người chốt phần mình, dòng của người khác giữ nguyên
    và phiếu chưa được coi là xử lý xong."""
    pr, it = _make_pr(db, seed)
    it2 = PurchaseRequestItem(pr_id=pr.id, product_code="SP-B", product_name="Thùng SP B",
                              item_group="Thùng", qty=10, unit="cái", price=8000,
                              vat_pct=8, amount=86400, assignee=seed.emp_backup_code,
                              created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(it2)
    db.commit()
    user = _nstm(db, seed, cap_quyen)
    C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"), db=db, user=user)
    out = _complete(db, pr, user)
    assert out["done"] == 1 and out["all_done"] is False
    lines = {l["product_code"]: l for l in C._out(db, pr, user)["items"]}
    assert lines["SP-A"]["options_done"] is True
    assert lines["SP-B"]["options_done"] is False


# ── Đợt 2: PHƯƠNG ÁN 0 (H.10) — sinh, chọn sẵn, ngoài trần, chốt rỗng đổi nghĩa ─

def _pa0(db, it):
    """Phương án 0 của một dòng — nhận diện bằng nguồn, không bằng vị trí."""
    return next(o for o in OS.options_of(db, it.id) if o.source == PR_OPT_ORIGINAL)


def _make_item(db, seed, pr, code="SP-B", name="Thùng SP B", assignee=None):
    it = PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name=name,
                             item_group="Thùng", qty=10, unit="cái", price=8000,
                             vat_pct=8, amount=86400,
                             assignee=assignee or seed.emp_nstm_code,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(it)
    db.commit()
    return it


def test_dieu_phoi_sinh_phuong_an_0(db, seed, cap_quyen):
    """Điểm sinh chính: `service.dispatch_pr` — cả đường công tắc điều phối TẮT cũng
    đi qua đây. Ruột chụp từ chính dòng yêu cầu, chưa có NCC, tick chọn sẵn."""
    pr, it = _make_pr(db, seed, status="approved")
    SV.dispatch_pr(db, pr.id, seed.u_req_id)
    o = _pa0(db, it)
    assert o.public_id == 0 and o.display_label == "Phương án 0"
    assert bool(o.is_chosen) is True                      # H.10.2 — im lặng = mua theo yêu cầu gốc
    assert o.snap_product_name == "Nhãn SP A" and o.snap_quote_unit == "cuộn"
    assert float(o.snap_price_by_volume) == 4800.0 and float(o.snap_vat) == 8.0
    assert o.supplier_code == "" and o.supplier_name == ""
    assert o.snap_internal_code == "SP-A"                 # mã hàng CỦA DÒNG, để H.3.9 đồng nhất
    assert o.created_by == 0                              # hệ thống tạo, không phải người nào


def test_sinh_bu_idempotent(db, seed, cap_quyen):
    """Phiếu điều phối TRƯỚC khi có tính năng: đường đọc sinh bù, gọi lại không đẻ thêm."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)
    C._out(db, pr, user)
    C.list_options(pr.id, it.id, db=db, user=user)
    rows = OS.options_of(db, it.id)
    assert len(rows) == 1 and rows[0].source == PR_OPT_ORIGINAL


def test_sinh_bu_khong_gianh_quyen_chon(db, seed, cap_quyen):
    """Sinh bù trên phiếu đang chạy dở KHÔNG được giật quyền chọn: dòng đã chọn phương
    án khác thì phương án 0 sinh ra ở trạng thái không chọn."""
    pr, it = _make_pr(db, seed)
    nstm = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                                  db=db, user=nstm))
    _complete(db, pr, nstm)
    req = _requester(db, seed, cap_quyen)
    C.choose_option(pr.id, it.id, o["id"], db=db, user=req)
    C._out(db, pr, nstm)                                  # sinh bù chạy ở đây
    assert bool(_pa0(db, it).is_chosen) is False
    assert OS.chosen_option_of(db, it.id).id == o["id"]


def test_phuong_an_0_khong_xoa_duoc(db, seed, cap_quyen):
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)
    with pytest.raises(HTTPException) as e:
        C.delete_option(pr.id, it.id, _pa0(db, it).id, db=db, user=user)
    assert e.value.status_code == 400
    assert "không gỡ được" in e.value.detail


def test_phuong_an_0_ngoai_tran_5(db, seed, cap_quyen):
    """Trần 5 chỉ đếm phương án NSTM gắn — có phương án 0 rồi vẫn gắn đủ 5, cái thứ 6 chặn."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)                                  # sinh phương án 0 trước
    for _ in range(OS.MAX_OPTIONS_PER_LINE):
        C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                            db=db, user=user)
    with pytest.raises(HTTPException):
        C.add_option_manual(pr.id, it.id, PROptionManualIn(supplier_code="NX"),
                            db=db, user=user)
    assert len(OS.options_of(db, it.id)) == 6             # 5 NSTM + phương án 0


def test_chot_rong_van_mua_duoc_theo_phuong_an_0(db, seed, cap_quyen):
    """H.10.3 — chốt rỗng = KHÔNG có phương án NSTM nào (phương án 0 không tính), là
    lời khai "khảo sát không ra NCC"; dòng vẫn giữ phương án 0 đang chọn nên vẫn mua được."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)                                  # dòng đã CÓ phương án 0
    with pytest.raises(HTTPException) as e:
        _complete(db, pr, user)                           # nhưng chốt rỗng vẫn phải tick có ý thức
    assert e.value.status_code == 400
    out = _complete(db, pr, user, [it.id])
    assert out["empty"] == 1
    line = C._out(db, pr, user)["items"][0]
    assert line["no_option"] is True and line["option_count"] == 0
    assert line["chosen_option"]["public_id"] == 0        # vẫn chọn phương án 0 -> vẫn mua được


def test_sau_chot_van_sua_duoc_gia(db, seed, cap_quyen):
    """Khe nới H.10.4: sau chốt hoàn thành, người có write + supplier.read sửa được
    GIÁ của mọi phương án; thiếu supplier.read thì 403."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    _complete(db, pr, user)
    out = _data(C.update_option(pr.id, it.id, o["id"],
                                PROptionUpdateIn(snap_price_by_volume=4444),
                                db=db, user=user))
    assert out["snap_price_by_volume"] == 4444.0


def test_sau_chot_thieu_quyen_ncc_thi_khong_sua_gia(db, seed, cap_quyen):
    """Khe H.10.4 dành cho tầng thu mua của màn chọn — thiếu `supplier.read` là 403.
    (User dựng THIẾU quyền ngay từ đầu: `cap_quyen` không hạ quyền đã cấp.)"""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen, supplier_read=False)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    _complete(db, pr, user)
    with pytest.raises(HTTPException) as e:
        C.update_option(pr.id, it.id, o["id"], PROptionUpdateIn(snap_price_by_volume=1),
                        db=db, user=user)
    assert e.value.status_code == 403


def test_ap_ncc_vao_phuong_an_0_ke_ca_sau_chot(db, seed, cap_quyen):
    """H.10.4 — điền NCC vào phương án 0 qua đường riêng, dùng được cả sau chốt rỗng."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)
    _complete(db, pr, user, [it.id])                      # chốt rỗng — dòng đã khóa sửa thường
    out = _data(C.set_option_supplier(pr.id, it.id, _pa0(db, it).id,
                                      PROptionSupplierIn(supplier_code="NX",
                                                         snap_price_by_volume=4500),
                                      db=db, user=user))
    assert out["supplier_code"] == "NX" and out["supplier_name"] == seed.sup_name
    assert out["snap_price_by_volume"] == 4500.0


def test_khong_ap_ncc_vao_phuong_an_khao_sat(db, seed, cap_quyen):
    """NCC của phương án khảo sát là dữ kiện khảo sát — đổi NCC là một phương án khác."""
    pr, it = _make_pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    with pytest.raises(HTTPException) as e:
        C.set_option_supplier(pr.id, it.id, o["id"],
                              PROptionSupplierIn(supplier_code="NX"), db=db, user=user)
    assert e.value.status_code == 400


def test_ap_1_ncc_cho_nhieu_dong(db, seed, cap_quyen):
    """H.10.5 — tick các dòng thiếu NCC, áp một NCC (kèm giá riêng từng dòng) vào
    phương án đang chọn của mỗi dòng."""
    pr, it = _make_pr(db, seed)
    it2 = _make_item(db, seed, pr)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)                                  # cả hai dòng có phương án 0 đang chọn
    _complete(db, pr, user, [it.id, it2.id])
    out = _data(C.assign_supplier_bulk(pr.id, PRAssignSupplierIn(
        supplier_code="NX",
        items=[PRAssignSupplierLineIn(item_id=it.id, snap_price_by_volume=4700),
               PRAssignSupplierLineIn(item_id=it2.id)]), db=db, user=user))
    assert out["updated"] == 2
    a, b = _pa0(db, it), _pa0(db, it2)
    assert a.supplier_code == "NX" and a.supplier_name == seed.sup_name
    assert float(a.snap_price_by_volume) == 4700.0
    assert b.supplier_code == "NX"
    assert float(b.snap_price_by_volume) == 8000.0        # không gửi giá thì giữ giá cũ


def test_ap_hang_loat_chan_dong_chon_khao_sat(db, seed, cap_quyen):
    """Một dòng không hợp lệ là từ chối CẢ LÔ — không áp nửa vời."""
    pr, it = _make_pr(db, seed)
    it2 = _make_item(db, seed, pr)
    user = _manager(db, seed, cap_quyen)
    C._out(db, pr, user)
    o = _data(C.add_option_from_survey(pr.id, it.id, PROptionSurveyIn(
        product_survey_line_id=seed.psl_nhan_1_id), db=db, user=user))
    _complete(db, pr, user, [it2.id])
    C.choose_option(pr.id, it.id, o["id"], db=db, user=user)   # dòng 1 chọn khảo sát
    with pytest.raises(HTTPException) as e:
        C.assign_supplier_bulk(pr.id, PRAssignSupplierIn(
            supplier_code="NX",
            items=[PRAssignSupplierLineIn(item_id=it.id),
                   PRAssignSupplierLineIn(item_id=it2.id)]), db=db, user=user)
    assert e.value.status_code == 400
    assert _pa0(db, it2).supplier_code == ""              # dòng hợp lệ trong lô cũng không bị áp


# ── Đợt 2: H.3.9 — chép mã hàng lên dòng khi chốt ───────────────────────────────

def test_chot_chep_ma_hang_len_dong_chua_co_ma(db, seed, cap_quyen):
    """Dòng chưa có mã + phương án chốt có `snap_internal_code` -> chép mã lên dòng;
    bỏ chốt KHÔNG xóa mã đã chép — mã đã thành dữ liệu của dòng."""
    pr, it_a = _make_pr(db, seed)
    it = _make_item(db, seed, pr, code="", name="Hàng chưa mã")
    user = _manager(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(
        supplier_code="NX", snap_internal_code="MA-MOI"), db=db, user=user))
    _complete(db, pr, user, [it_a.id])                     # dòng SP-A chốt rỗng cho đủ phiếu
    C.choose_option(pr.id, it.id, o["id"], db=db, user=user)
    db.refresh(it)
    assert it.product_code == "MA-MOI"
    C.choose_option(pr.id, it.id, o["id"], db=db, user=user)   # bỏ chốt
    db.refresh(it)
    assert it.product_code == "MA-MOI"


def test_khong_chep_ma_trung_dong_khac(db, seed, cap_quyen):
    """CR-047: mỗi mã một dòng trên phiếu — dòng khác đã mang mã thì thôi không chép."""
    pr, it_a = _make_pr(db, seed)                          # it_a mang sẵn SP-A
    it = _make_item(db, seed, pr, code="", name="Hàng chưa mã")
    user = _manager(db, seed, cap_quyen)
    o = _data(C.add_option_manual(pr.id, it.id, PROptionManualIn(
        supplier_code="NX", snap_internal_code="SP-A"), db=db, user=user))
    _complete(db, pr, user, [it_a.id])
    C.choose_option(pr.id, it.id, o["id"], db=db, user=user)
    db.refresh(it)
    assert it.product_code == ""                           # không được đẻ ra phiếu trùng mã


# ── Đợt 2 chặng (c): H.10.6 — "Tạo đơn mua hàng theo phương án" ─────────────────

def _buyer(db, seed, cap_quyen):
    """Người bấm nút gom: thấy phiếu (`purchase_request.read`) + lập được đơn
    (`purchase_order.create`) — đúng hai cổng của endpoint generate-orders."""
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="all", read=True, write=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True, create=True)
    return db.get(User, seed.u_nstm_id)


def _po_lines(db, po_id):
    from app.modules.purchase_order.model import POItem
    return db.query(POItem).filter(POItem.po_id == po_id).order_by(POItem.id).all()


def test_gom_theo_ncc_va_don_khong_ncc_rieng(db, seed, cap_quyen):
    """Dòng có NCC gom theo NCC, dòng mà phương án chọn CHƯA có NCC gom vào MỘT đơn
    nháp riêng; giá/VAT lấy từ snapshot phương án; dòng YCMH nhảy `not_ordered`."""
    from app.modules.purchase_order.model import PurchaseOrder
    pr, it = _make_pr(db, seed)
    it2 = _make_item(db, seed, pr)                        # SP-B, chưa có NCC
    user = _buyer(db, seed, cap_quyen)
    C._out(db, pr, user)                                  # sinh phương án 0, tick chọn sẵn
    C.set_option_supplier(pr.id, it.id, _pa0(db, it).id,
                          PROptionSupplierIn(supplier_code="NX",
                                             snap_price_by_volume=4500),
                          db=db, user=user)
    out = _data(C.generate_orders_from_options(pr.id, db=db, user=user))
    assert len(out["orders"]) == 2
    with_sup, without_sup = out["orders"]
    assert with_sup["supplier_code"] == "NX" and with_sup["line_count"] == 1
    assert without_sup["supplier_code"] == "" and without_sup["line_count"] == 1

    po_a = db.get(PurchaseOrder, with_sup["id"])
    assert po_a.status == "draft" and po_a.pr_code == pr.code
    line_a = _po_lines(db, po_a.id)[0]
    assert line_a.product_code == "SP-A"
    assert float(line_a.price) == 4500.0                  # giá đã sửa trên phương án
    assert float(line_a.vat) == 8.0                       # snap_vat chụp từ dòng lúc sinh PA0
    line_b = _po_lines(db, without_sup["id"])[0]
    assert line_b.product_code == "SP-B"
    assert float(line_b.price) == 8000.0

    db.refresh(it), db.refresh(it2)                       # CR-074: nháp cũng đổi tiến độ dòng
    assert it.line_status == SV.LINE_STATUS_NOT_ORDERED
    assert it2.line_status == SV.LINE_STATUS_NOT_ORDERED


def test_bam_lai_khong_de_don_trung(db, seed, cap_quyen):
    """Chống bấm hai lần bằng `line_status` (KHÔNG bỏ chốt phương án — đó là quyết
    định của người yêu cầu): mọi dòng đã lên đơn thì lần hai ăn 400, không đẻ thêm."""
    from app.modules.purchase_order.model import PurchaseOrder
    pr, it = _make_pr(db, seed)
    user = _buyer(db, seed, cap_quyen)
    C._out(db, pr, user)
    _data(C.generate_orders_from_options(pr.id, db=db, user=user))
    n_before = db.query(PurchaseOrder).count()
    with pytest.raises(HTTPException) as e:
        C.generate_orders_from_options(pr.id, db=db, user=user)
    assert e.value.status_code == 400
    assert db.query(PurchaseOrder).count() == n_before
    assert _pa0(db, it).is_chosen                          # phương án chọn còn nguyên


def test_dong_bo_chot_het_thi_bo_qua(db, seed, cap_quyen):
    """Dòng mà người yêu cầu đã BỎ CHỐT mọi phương án = "khoan mua dòng này" —
    nút gom bỏ qua, không tự lôi phương án 0 ra chọn lại."""
    pr, it = _make_pr(db, seed)
    it2 = _make_item(db, seed, pr)
    user = _buyer(db, seed, cap_quyen)
    C._out(db, pr, user)
    pa0_b = _pa0(db, it2)
    pa0_b.is_chosen = False                                # người yêu cầu đã bỏ chốt (rút gọn)
    db.commit()
    out = _data(C.generate_orders_from_options(pr.id, db=db, user=user))
    assert len(out["orders"]) == 1
    assert out["orders"][0]["line_count"] == 1
    assert out["skipped"]["no_chosen"] == 1
    assert not _pa0(db, it2).is_chosen                     # sinh bù không giành lại quyền chọn


def test_vat_trong_roi_ve_vat_dong(db, seed, cap_quyen):
    """CR-058: phương án không khai VAT thì dòng đơn lấy `vat_pct` của dòng yêu cầu,
    đừng để 0% âm thầm rồi thiếu tiền thuế."""
    pr, it = _make_pr(db, seed)
    user = _buyer(db, seed, cap_quyen)
    C._out(db, pr, user)
    pa0 = _pa0(db, it)
    pa0.snap_vat = 0                                       # phương án bỏ trống VAT
    db.commit()
    out = _data(C.generate_orders_from_options(pr.id, db=db, user=user))
    line = _po_lines(db, out["orders"][0]["id"])[0]
    assert float(line.vat) == 8.0


def test_ngoai_pham_vi_thi_404(db, seed, cap_quyen):
    """Có `purchase_order.create` nhưng KHÔNG thấy phiếu (không grant YCMH) thì 404 —
    nút gom không phải cửa đọc lậu phiếu ngoài phạm vi."""
    pr, it = _make_pr(db, seed)
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True, create=True)
    user = db.get(User, seed.u_nstm_id)
    with pytest.raises(HTTPException) as e:
        C.generate_orders_from_options(pr.id, db=db, user=user)
    assert e.value.status_code == 404
