"""P6-3 (bao-CR-281) — chốt phương án + tạo thẳng đơn mua hàng (doc/erp/12 §P6-3).

Ba luật cần khóa bằng test:

1. `confirm_line_option` — chỉ chốt được dòng ĐANG có phương án được chọn; dòng đã
   Hoàn thành thì không chốt; bỏ chốt giữ nguyên lựa chọn (về "Đã chọn phương án").
2. Chốt là KHÓA: `choose_option` phải chặn 400 khi dòng đang chốt — thu mua có thể
   đang lên đơn theo đúng phương án đó, đổi lựa chọn sau lưng là mua sai hàng.
3. `create_pos_from_confirmed` — gom theo NCC mỗi NCC 1 ĐMH nháp, giá/VAT từ snapshot
   (VAT rỗng lấy vat_pct dòng — bài học CR-058), pr_code để RỖNG (ràng buộc P6-5,
   nguồn YCBG đi bằng survey_code + tab_survey_request_po), dòng ghi po_code rồi
   tự bỏ chọn + gỡ chốt để tái sử dụng (mua lại), phiếu survey_done -> pr_created.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.survey_request import line_state, service
from app.modules.survey_request.model import (LS_COMPLETED, LS_CONFIRMED,
                                              SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption,
                                              SurveyRequestPo)


def _sr(db, status: str = "survey_done", code: str = "YCBG-P63"):
    s = SurveyRequest(code=code, status=status)
    db.add(s)
    db.commit()
    return s


def _line(db, sid: int, **kw):
    ln = SurveyRequestLine(survey_request_id=sid, item_group="Thùng",
                           request_qty=kw.pop("request_qty", 10), **kw)
    db.add(ln)
    db.commit()
    return ln


def _opt(db, line_id: int, public_id: int, supplier: str = "NCC-A",
         chosen: bool = False, **kw):
    o = SurveyRequestOption(survey_request_line_id=line_id, public_id=public_id,
                            supplier_code=supplier, is_chosen=chosen, **kw)
    db.add(o)
    db.commit()
    return o


# ───────────────────────── confirm_line_option: chốt / bỏ chốt ─────────────────────────

def test_chot_doi_dong_phai_dang_chon_phuong_an(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    _opt(db, ln.id, 1)   # có phương án nhưng CHƯA chọn

    with pytest.raises(HTTPException) as e:
        service.confirm_line_option(db, s.id, ln.id, True, user_id=1)
    assert e.value.status_code == 400


def test_chot_xong_dong_mang_trang_thai_confirmed(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    _opt(db, ln.id, 1, chosen=True)

    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    db.refresh(ln)
    assert ln.line_status == LS_CONFIRMED
    assert line_state.progress_state(ln, True, 1) == line_state.STATE_CONFIRMED


def test_dong_hoan_thanh_khong_chot_duoc(db, seed):
    s = _sr(db)
    ln = _line(db, s.id, line_status=LS_COMPLETED, is_completed=True)
    _opt(db, ln.id, 1, chosen=True)

    with pytest.raises(HTTPException) as e:
        service.confirm_line_option(db, s.id, ln.id, True, user_id=1)
    assert e.value.status_code == 400


def test_bo_chot_giu_nguyen_lua_chon(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    o = _opt(db, ln.id, 1, chosen=True)
    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    service.confirm_line_option(db, s.id, ln.id, False, user_id=1)

    db.refresh(ln)
    db.refresh(o)
    assert ln.line_status == "" and o.is_chosen, "bỏ chốt chỉ mở khóa, không được vứt lựa chọn"
    assert line_state.progress_state(ln, True, 1) == line_state.STATE_CHOSEN


def test_dong_da_chot_khoa_doi_va_bo_lua_chon(db, seed):
    """Chốt = khóa: đổi sang phương án khác HAY bấm bỏ chọn đều phải 400."""
    s = _sr(db)
    ln = _line(db, s.id)
    dang_chon = _opt(db, ln.id, 1, chosen=True)
    khac = _opt(db, ln.id, 2)
    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    for oid in (khac.id, dang_chon.id):
        with pytest.raises(HTTPException) as e:
            service.choose_option(db, ln.id, oid, user_id=1)
        assert e.value.status_code == 400

    db.refresh(dang_chon)
    assert dang_chon.is_chosen


# ───────────────────── create_pos_from_confirmed: tạo thẳng ĐMH ─────────────────────

def test_chua_co_dong_chot_thi_khong_tao_don(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    _opt(db, ln.id, 1, chosen=True)   # mới CHỌN, chưa chốt

    with pytest.raises(HTTPException) as e:
        service.create_pos_from_confirmed(db, s.id, user_id=1)
    assert e.value.status_code == 400


def test_tao_don_tu_dong_da_chot_gia_vat_tu_snapshot(db, seed):
    s = _sr(db)
    ln = _line(db, s.id, product_code="VT-P63-01", warehouse="KHO-01",
               required_date="2026-09-20", request_qty=7)
    _opt(db, ln.id, 1, chosen=True, system_product_code="VT-P63-01",
         snap_product_name="Thùng giấy 5 lớp", snap_quote_unit="Cái",
         snap_price_by_volume=1234.5678, snap_vat=8,
         snap_delivery_time="7 ngày", snap_delivery_place="Kho Cần Thơ",
         supplier_name="Cty A")
    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1)

    assert len(pos) == 1
    po = db.get(PurchaseOrder, pos[0].id)
    assert po.status == "draft"
    assert po.survey_code == s.code, "nguồn YCBG đi bằng survey_code"
    assert po.pr_code == "", "P6-5: pr_code giữ nghĩa 'mã YCMH nguồn' — luồng v2 không có YCMH"
    assert po.supplier_code == "NCC-A" and po.supplier_name == "Cty A"
    it = db.query(POItem).filter(POItem.po_id == po.id).one()
    assert it.product_code == "VT-P63-01"
    assert float(it.qty_order) == 7 and float(it.qty_request) == 7
    assert float(it.price) == pytest.approx(1234.5678)
    assert float(it.vat) == 8
    assert it.warehouse_code == "KHO-01" and it.required_date == "2026-09-20"
    assert "7 ngày" in it.note and "Kho Cần Thơ" in it.note


def test_vat_snapshot_rong_lay_vat_pct_cua_dong(db, seed):
    """Bài học CR-058: quên VAT là dòng ĐMH nhận 0% dù NCC báo 8%."""
    s = _sr(db)
    ln = _line(db, s.id, vat_pct=10)
    _opt(db, ln.id, 1, chosen=True, snap_vat=0)
    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1)

    it = db.query(POItem).filter(POItem.po_id == pos[0].id).one()
    assert float(it.vat) == 10


def test_gom_theo_ncc_moi_ncc_mot_don(db, seed):
    s = _sr(db)
    ln1 = _line(db, s.id, product_code="VT-1")
    ln2 = _line(db, s.id, product_code="VT-2")
    ln3 = _line(db, s.id, product_code="VT-3")
    _opt(db, ln1.id, 1, supplier="NCC-A", chosen=True)
    _opt(db, ln2.id, 1, supplier="NCC-A", chosen=True)
    _opt(db, ln3.id, 1, supplier="NCC-B", chosen=True)
    for ln in (ln1, ln2, ln3):
        service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1)

    assert len(pos) == 2
    by_sup = {p.supplier_code: p for p in pos}
    assert db.query(POItem).filter(POItem.po_id == by_sup["NCC-A"].id).count() == 2
    assert db.query(POItem).filter(POItem.po_id == by_sup["NCC-B"].id).count() == 1


def test_dong_chua_chot_khong_bi_keo_vao_don(db, seed):
    s = _sr(db)
    da_chot = _line(db, s.id, product_code="VT-1")
    chua_chot = _line(db, s.id, product_code="VT-2")
    _opt(db, da_chot.id, 1, chosen=True)
    _opt(db, chua_chot.id, 1, chosen=True)   # chọn nhưng KHÔNG chốt
    service.confirm_line_option(db, s.id, da_chot.id, True, user_id=1)

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1)

    assert len(pos) == 1
    assert db.query(POItem).filter(POItem.po_id == pos[0].id).count() == 1
    db.refresh(chua_chot)
    assert chua_chot.po_code == ""


def test_sau_khi_len_don_dong_tai_su_dung_duoc(db, seed):
    """Sau tạo đơn: dòng ghi po_code (tiến độ 'Đã lên đơn'), option tự bỏ chọn,
    chốt được gỡ, và có 1 dòng lịch sử tab_survey_request_po."""
    s = _sr(db)
    ln = _line(db, s.id)
    o = _opt(db, ln.id, 1, chosen=True)
    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1)

    db.refresh(ln)
    db.refresh(o)
    assert ln.po_id == pos[0].id and ln.po_code == pos[0].code
    # P6-4 (bao-CR-282): dòng CÓ mã SP thì sync cuối create_pos đổi ngay ra "not_ordered"
    # (xem test_tao_don_xong_dong_ra_not_ordered); dòng này KHÔNG có mã — không có khóa
    # để khớp nên sync cố ý bỏ qua, trạng thái giữ "" và tiến độ vẫn suy từ po_code.
    assert ln.line_status == "" and not o.is_chosen
    assert line_state.progress_state(ln, False, 1) == line_state.STATE_PO_CREATED
    links = db.query(SurveyRequestPo).filter(SurveyRequestPo.survey_request_id == s.id).all()
    assert len(links) == 1
    assert links[0].po_code == pos[0].code and links[0].option_id == o.id


def test_phieu_survey_done_len_pr_created_phieu_done_giu_nguyen(db, seed):
    for status, expect in (("survey_done", "pr_created"), ("done", "done")):
        s = _sr(db, status=status, code=f"YCBG-P63-{status}")
        ln = _line(db, s.id)
        _opt(db, ln.id, 1, chosen=True)
        service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

        service.create_pos_from_confirmed(db, s.id, user_id=1)

        db.refresh(s)
        assert s.status == expect


def test_trung_ma_hang_cung_ncc_chan_truoc_khi_tao(db, seed):
    """2 dòng cùng NCC cùng mã -> 2 dòng trùng mã trên ĐMH, sai đồng bộ SL (P6-4). Chặn
    TRƯỚC vòng lặp: không được để lại đơn tạo dở."""
    s = _sr(db)
    ln1 = _line(db, s.id, product_code="VT-TRUNG")
    ln2 = _line(db, s.id, product_code="VT-TRUNG")
    _opt(db, ln1.id, 1, chosen=True)
    _opt(db, ln2.id, 1, chosen=True)
    for ln in (ln1, ln2):
        service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    with pytest.raises(HTTPException) as e:
        service.create_pos_from_confirmed(db, s.id, user_id=1)
    assert e.value.status_code == 400
    assert db.query(PurchaseOrder).count() == 0, "chặn giữa chừng là để lại đơn rác"
