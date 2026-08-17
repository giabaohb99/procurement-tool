"""CR-075 — màn "Tiến độ báo giá" + mốc "ngày trả kết quả thực tế".

Ba nhóm việc được kiểm ở đây:

1. `_stamp_result_date` — mốc ghi MỘT LẦN. Dòng bị trả về "cần khảo sát lại" rồi chốt lần hai
   KHÔNG được ghi đè mốc cũ, nếu không thì mọi dấu trễ hạn đều bị xóa sạch bằng một lần khảo
   sát lại.
2. Hai cột tính `days_late` / `handling_days` — ranh giới quan trọng: chưa trả kết quả mà đã
   quá hạn thì vẫn phải hiện số ngày đang trễ, còn trả sớm thì để trống (cột này soi việc trễ).
3. `progress_state` và luật ẩn NCC (`supplier.read` là cờ RỜI — bài học CR-071).
"""
from datetime import date

import pytest

from app.modules.survey_progress import export as ex
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)
from app.modules.survey_request.service import _stamp_result_date

TODAY = date(2026, 8, 17)


def _line(**kw) -> SurveyRequestLine:
    base = dict(survey_request_id=1, item_group="Bao bì", assignee="DEMONV",
                received_date="", result_due_date="", result_date="",
                line_status="", no_option=False, pr_code="")
    base.update(kw)
    return SurveyRequestLine(**base)


# ── 1. Mốc ngày trả kết quả ghi một lần ─────────────────────────────────────────
def test_stamp_result_date_ghi_moc_cho_dong_con_trong():
    ln = _line()
    _stamp_result_date(ln)
    assert len(ln.result_date) == 10 and ln.result_date[4] == "-"


def test_stamp_result_date_khong_ghi_de_moc_cu():
    """Khảo sát lại rồi chốt lần hai vẫn giữ mốc gốc — không xóa dấu trễ của lần đầu."""
    ln = _line(result_date="2026-07-01")
    _stamp_result_date(ln)
    assert ln.result_date == "2026-07-01"


def test_stamp_result_date_coi_chuoi_trang_la_chua_co_moc():
    ln = _line(result_date="   ")
    _stamp_result_date(ln)
    assert ln.result_date.strip() != ""


def test_complete_sr_dong_dau_tien_duoc_dong_moc(db, seed):
    """Chốt khảo sát -> dòng có phương án và dòng chốt rỗng đều được đóng mốc."""
    from app.modules.survey_request.service import complete_sr
    s = SurveyRequest(code="YCBG1", status="processing", created_by=seed.u_nstm_id)
    db.add(s); db.flush()
    co_pa = _line(survey_request_id=s.id)
    chot_rong = _line(survey_request_id=s.id)
    db.add_all([co_pa, chot_rong]); db.flush()
    db.add(SurveyRequestOption(survey_request_line_id=co_pa.id, public_id=1,
                               display_label="Option 1"))
    db.commit()

    user = type("U", (), {"id": seed.u_nstm_id, "employee_id": 0})()
    complete_sr(db, s.id, user, profile={"grants": []}, empty_line_ids=[chot_rong.id])
    db.commit()
    assert co_pa.result_date != "" and chot_rong.result_date != ""


def test_complete_sr_lan_hai_giu_nguyen_moc_cu(db, seed):
    from app.modules.survey_request.service import complete_sr
    s = SurveyRequest(code="YCBG2", status="processing", created_by=seed.u_nstm_id)
    db.add(s); db.flush()
    ln = _line(survey_request_id=s.id, result_date="2026-01-05",
               line_status="resurvey")
    db.add(ln); db.flush()
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1))
    db.commit()

    user = type("U", (), {"id": seed.u_nstm_id, "employee_id": 0})()
    complete_sr(db, s.id, user, profile={"grants": []})
    db.commit()
    assert ln.result_date == "2026-01-05"
    assert ln.line_status == ""      # khảo sát lại xong thì gỡ cờ, nhưng mốc vẫn nguyên


# ── 2. Cột tính: trễ hạn & số ngày xử lý ────────────────────────────────────────
@pytest.mark.parametrize("due,result,mong_doi", [
    ("2026-08-10", "2026-08-14", 4),      # trả muộn 4 ngày
    ("2026-08-10", "2026-08-10", None),   # đúng hạn -> để trống
    ("2026-08-20", "2026-08-14", None),   # trả sớm -> KHÔNG hiện số âm
    ("2026-08-10", "", 7),                # chưa trả, quá hạn -> đang trễ tính tới hôm nay
    ("2026-08-25", "", None),             # chưa trả, chưa tới hạn
    ("", "2026-08-14", None),             # không có hạn thì không đo được
    ("hong", "2026-08-14", None),         # dữ liệu hỏng -> ô trống, không nổ
])
def test_days_late(due, result, mong_doi):
    assert ex._days_late(due, result, TODAY) == mong_doi


@pytest.mark.parametrize("received,result,mong_doi", [
    ("2026-08-01", "2026-08-06", 5),
    ("2026-08-01", "2026-08-01", 0),
    ("", "2026-08-06", None),
    ("2026-08-01", "", None),
])
def test_handling_days(received, result, mong_doi):
    assert ex._handling_days(received, result) == mong_doi


# ── 3. Tiến độ dòng ─────────────────────────────────────────────────────────────
def test_progress_state_chua_giao_ai_thi_chua_tiep_nhan():
    assert ex.progress_state(_line(assignee=""), False, 0) == ex.STATE_NOT_RECEIVED


def test_progress_state_da_giao_nhung_chua_lam_gi():
    assert ex.progress_state(_line(), False, 0) == ex.STATE_RECEIVED


def test_progress_state_co_phuong_an_nhung_chua_chot():
    assert ex.progress_state(_line(), False, 3) == ex.STATE_SURVEYING


def test_progress_state_da_chot_thi_la_da_tra_ket_qua():
    assert ex.progress_state(_line(result_date="2026-08-10"), False, 2) == ex.STATE_ANSWERED


def test_progress_state_chot_rong():
    ln = _line(result_date="2026-08-10", no_option=True)
    assert ex.progress_state(ln, False, 0) == ex.STATE_NO_OPTION


def test_progress_state_nguoi_yc_da_chon_phuong_an():
    assert ex.progress_state(_line(result_date="2026-08-10"), True, 2) == ex.STATE_CHOSEN


def test_progress_state_can_khao_sat_lai_de_len_tren_da_chon():
    """Dòng bị trả về phải hiện "Cần khảo sát lại" kể cả khi vẫn còn phương án đã chọn cũ."""
    ln = _line(line_status="resurvey", result_date="2026-08-10")
    assert ex.progress_state(ln, True, 2) == ex.STATE_RESURVEY


def test_progress_state_da_tao_ycmh_de_len_tren_cac_moc_khao_sat():
    ln = _line(pr_code="PYC001", line_status="resurvey")
    assert ex.progress_state(ln, True, 2) == ex.STATE_PR_CREATED


def test_progress_state_hoan_thanh():
    assert ex.progress_state(_line(line_status="completed"), True, 1) == ex.STATE_DONE


def test_progress_state_hoan_thanh_thang_da_tao_ycmh(db):
    """CR-077: Hoàn thành là ĐIỂM CUỐI. Một dòng tạo được YCMH nhiều lần (mua lại) nên `pr_code`
    không khép dòng lại; chỉ khi người YC chốt hoàn thành thì dòng mới thật sự xong.
    Trước CR-077 nhãn này thua "Đã tạo YCMH" nên lệch với màn chi tiết Yêu cầu báo giá."""
    from app.modules.survey_progress.controller import _state_cond
    ln = _line(pr_code="PYC001", line_status="completed")
    assert ex.progress_state(ln, True, 2) == ex.STATE_DONE

    # Bộ lọc SQL phải đảo theo, nếu không chọn "Hoàn thành" sẽ không ra dòng này
    s = SurveyRequest(code="YCBG8", status="processing")
    db.add(s); db.flush()
    row = _line(survey_request_id=s.id, pr_code="PYC001", line_status="completed")
    db.add(row); db.commit()
    ids_done = {r.id for r in db.query(SurveyRequestLine).filter(_state_cond(ex.STATE_DONE)).all()}
    ids_pr = {r.id for r in db.query(SurveyRequestLine).filter(_state_cond(ex.STATE_PR_CREATED)).all()}
    assert row.id in ids_done and row.id not in ids_pr


# ── 4. Ẩn nhà cung cấp ──────────────────────────────────────────────────────────
def _row(show_supplier: bool) -> dict:
    s = SurveyRequest(code="YCBG9", status="processing", company_id=1)
    ln = _line(internal_line_code="D-001", received_date="2026-08-01",
               result_due_date="2026-08-10", result_date="2026-08-14")
    opt = SurveyRequestOption(survey_request_line_id=1, public_id=1, display_label="Option 1",
                              supplier_code="NX", supplier_name="NCC Nam Xuân",
                              snap_internal_code="SP-NX-01", snap_product_name="Thùng carton")
    return ex.row_values(s, ln, opt, 2, "DEMONV — Nguyễn Văn A", "DEGO", show_supplier, TODAY)


def test_co_quyen_supplier_thi_thay_du_cot_ncc():
    r = _row(True)
    assert r["opt_supplier_name"] == "NCC Nam Xuân"
    assert r["opt_internal_code"] == "SP-NX-01" and r["internal_line_code"] == "D-001"


def test_khong_co_quyen_supplier_thi_go_han_khoi_du_lieu():
    """Gỡ khỏi DỮ LIỆU chứ không phải chỉ ẩn cột — API không được rò tên NCC ra ngoài."""
    r = _row(False)
    for k in ex.SUPPLIER_HIDDEN_KEYS:
        assert k not in r
    assert r["opt_product_name"] == "Thùng carton"   # thông số sản phẩm vẫn hiện bình thường


def test_bo_cot_xuat_excel_theo_quyen_supplier():
    keys_co = {c.key for c in ex.columns_for(True)}
    keys_khong = {c.key for c in ex.columns_for(False)}
    assert set(ex.SUPPLIER_HIDDEN_KEYS) <= keys_co
    assert set(ex.SUPPLIER_HIDDEN_KEYS).isdisjoint(keys_khong)
    assert keys_co - keys_khong == set(ex.SUPPLIER_HIDDEN_KEYS)


def test_hang_khong_co_phuong_an_van_du_cot_moc_tien_do():
    """Dòng chưa có phương án nào vẫn phải ra được hàng — cụm cột phương án để trống."""
    s = SurveyRequest(code="YCBG8", status="processing")
    r = ex.row_values(s, _line(result_due_date="2026-08-01"), None, 0, "", "", True, TODAY)
    assert r["progress_state"] == ex.STATE_RECEIVED
    assert r["days_late"] == 16 and r["option_count"] == 0
    assert "opt_supplier_name" not in r


# ── 5. Lọc theo "Tiến độ dòng" (cột TÍNH -> SQL) ────────────────────────────────
def test_loc_theo_tien_do_dong_chia_dung_het_khong_trung(db):
    """Bộ lọc SQL phải CHIA ĐÔI KHỚP với cột tính: mỗi dòng rơi vào đúng một nhãn, tổng các
    nhãn = tổng số dòng. Đây là chỗ dễ vỡ nhất — quên vế "và không khớp mốc xa hơn" là nhãn
    "Đang khảo sát" kéo về cả những dòng đã chốt xong từ lâu."""
    from app.modules.survey_progress.controller import _state_cond

    s = SurveyRequest(code="YCBG7", status="processing")
    db.add(s); db.flush()
    mau = [
        _line(survey_request_id=s.id, assignee=""),                                   # chưa tiếp nhận
        _line(survey_request_id=s.id),                                                # đã tiếp nhận
        _line(survey_request_id=s.id),                                                # đang khảo sát (thêm PA bên dưới)
        _line(survey_request_id=s.id, result_date="2026-08-10"),                      # đã trả kết quả
        _line(survey_request_id=s.id, result_date="2026-08-10", no_option=True),      # chốt rỗng
        _line(survey_request_id=s.id, result_date="2026-08-10"),                      # đã chọn PA (thêm PA chốt)
        _line(survey_request_id=s.id, line_status="resurvey"),                # cần khảo sát lại
        _line(survey_request_id=s.id, line_status="completed"),                      # hoàn thành
        _line(survey_request_id=s.id, pr_code="PYC7", pr_id=7),                       # đã tạo YCMH
        _line(survey_request_id=s.id, pr_code="PYC8", pr_id=8, line_status="completed"),  # CR-077: hoàn thành thắng
    ]
    db.add_all(mau); db.flush()
    db.add(SurveyRequestOption(survey_request_line_id=mau[2].id, public_id=1))
    db.add(SurveyRequestOption(survey_request_line_id=mau[5].id, public_id=1, is_chosen=True))
    db.commit()

    # Nhãn mà cột tính gán cho từng dòng
    def nhan(ln):
        opts = db.query(SurveyRequestOption).filter(
            SurveyRequestOption.survey_request_line_id == ln.id).all()
        return ex.progress_state(ln, any(o.is_chosen for o in opts), len(opts))

    mong_doi = {}
    for ln in mau:
        mong_doi.setdefault(nhan(ln), set()).add(ln.id)

    tong = 0
    for state in ex.STATES:
        ids = {r.id for r in db.query(SurveyRequestLine).filter(_state_cond(state)).all()}
        assert ids == mong_doi.get(state, set()), f"lệch ở nhãn {state}"
        tong += len(ids)
    assert tong == len(mau)


def test_loc_nhan_la_thi_khong_loc_gi(db):
    """Người dùng sửa URL thành nhãn không có thật -> coi như không lọc, hơn là bảng rỗng khó hiểu."""
    from app.modules.survey_progress.controller import _state_cond
    assert _state_cond("Nhan-khong-co-that") is None
