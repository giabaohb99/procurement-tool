"""duoc-CR-744 — màn Tiến độ báo giá: mọi cột đều sắp xếp được tại server.

Lỗi người dùng báo: bấm tiêu đề cột Trễ / Số ngày xử lý / Tiến độ dòng / Số PA / Nhà cung cấp /
Tên SP báo giá / Đơn giá báo… không có gì xảy ra. Các cột đó không nằm thẳng trong DB nên
`_sort_map()` không có khóa, giao diện cũng không bật `sortable`. Cột Công ty thì xếp được
nhưng theo `company_id`, nên thứ tự chữ trên màn trông như xếp lộn.

Chốt kiểm:

1. Cột tính xếp đúng như giá trị đang hiện: trễ nhiều đứng đầu khi xếp giảm, ô trống đứng cuối.
2. Tiến độ dòng xếp theo DÒNG ĐỜI (Chưa tiếp nhận -> Hoàn thành), không theo chữ cái.
3. Cột phương án chốt xếp theo phương án ĐÃ CHỐT, dòng chưa chốt dồn về một phía.
4. Công ty xếp theo TÊN.
5. Không có `supplier.read` thì xếp theo tên NCC bị bỏ qua — thứ tự dòng theo tên NCC là
   đủ để mò ra NCC dù cột đã che.
6. Canh: mọi cột của bảng (trừ STT) đều có cách xếp — thêm cột mới mà quên là bài này đỏ.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.company.model import Company
from app.modules.survey_progress import controller as sp
from app.modules.survey_progress import export as ex
from app.modules.survey_progress.sort_expressions import get_computed_sort_expression
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)
from app.modules.user.model import User

TODAY = date(2026, 11, 10)


def req(qs: str):
    """Request giả — `_build_query` chỉ đụng tới `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    """Cột Trễ của dòng chưa trả kết quả đo tới hôm nay, nên hôm nay phải cố định."""
    monkeypatch.setattr(sp, "_today", lambda: TODAY)


@pytest.fixture
def viewer(db, cap_quyen):
    user = User(email="sort743@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "survey_request", scope="all", read=True)
    db.commit()
    return user


def _add_line(db, code: str, company_id: int = 1, **line_kw) -> SurveyRequestLine:
    s = SurveyRequest(code=code, status="processing", company_id=company_id)
    db.add(s)
    db.flush()
    base = dict(survey_request_id=s.id, item_group="Bao bì", assignee="NV01",
                received_date="", result_due_date="", result_date="",
                line_status="", no_option=False, pr_code="")
    base.update(line_kw)
    ln = SurveyRequestLine(**base)
    db.add(ln)
    db.flush()
    return ln


def _rows(db, user, qs: str, show_supplier: bool = True) -> list[dict]:
    prof = get_perm_profile(db, user)
    q = sp._build_query(req(qs), db, user, prof, show_supplier)
    return sp._decorate(db, q.all(), show_supplier, 0)


def _codes(db, user, qs: str, show_supplier: bool = True) -> list[str]:
    return [r["code"] for r in _rows(db, user, qs, show_supplier)]


# ── 1. Cột tính Trễ / Số ngày xử lý ──────────────────────────────────────────────
def test_xep_tre_giam_dan_tre_nhieu_dung_dau_o_trong_dung_cuoi(db, viewer):
    _add_line(db, "A-ON-TIME", result_due_date="2026-11-30", result_date="2026-11-01")
    _add_line(db, "B-LATE-3", result_due_date="2026-10-01", result_date="2026-10-04")
    _add_line(db, "C-NO-DUE")
    #  Chưa trả kết quả, hạn 31/10 -> đang trễ 10 ngày tính tới 10/11.
    _add_line(db, "D-LATE-10-OPEN", result_due_date="2026-10-31")
    db.commit()

    rows = _rows(db, viewer, "sort_by=days_late&sort_dir=desc")
    assert [r["code"] for r in rows[:2]] == ["D-LATE-10-OPEN", "B-LATE-3"]
    assert [r["days_late"] for r in rows[:2]] == [10, 3]
    assert {r["days_late"] for r in rows[2:]} == {None}


def test_xep_so_ngay_xu_ly_tang_dan_theo_dung_so_dang_hien(db, viewer):
    _add_line(db, "A-5", received_date="2026-10-01", result_date="2026-10-06")
    _add_line(db, "B-1", received_date="2026-10-01", result_date="2026-10-02")
    _add_line(db, "C-OPEN", received_date="2026-10-01")
    _add_line(db, "D-12", received_date="2026-10-01", result_date="2026-10-13")
    db.commit()

    rows = _rows(db, viewer, "sort_by=handling_days&sort_dir=desc")
    assert [r["handling_days"] for r in rows] == [12, 5, 1, None]


# ── 2. Tiến độ dòng theo dòng đời ────────────────────────────────────────────────
def test_xep_tien_do_dong_theo_dong_doi_khong_theo_chu_cai(db, viewer):
    _add_line(db, "A-DONE", line_status="completed")
    _add_line(db, "B-NOT-RECEIVED", assignee="")
    _add_line(db, "C-NO-OPTION", result_date="2026-10-10", no_option=True)
    _add_line(db, "D-PR", pr_code="PYC1", pr_id=1)
    _add_line(db, "E-RECEIVED")
    db.commit()

    asc = [r["progress_state"] for r in _rows(db, viewer, "sort_by=progress_state&sort_dir=asc")]
    assert asc == [ex.STATE_NOT_RECEIVED, ex.STATE_RECEIVED, ex.STATE_NO_OPTION,
                   ex.STATE_PR_CREATED, ex.STATE_DONE]
    desc = [r["progress_state"] for r in _rows(db, viewer, "sort_by=progress_state&sort_dir=desc")]
    assert desc == list(reversed(asc))


# ── 3. Cụm phương án chốt + số phương án ─────────────────────────────────────────
@pytest.fixture
def option_lines(db):
    """Ba dòng có phương án chốt giá khác nhau và một dòng chỉ có phương án CHƯA chốt."""
    for code, price, supplier, extra_options in (
        ("A-MID", 200, "Beta NCC", 0),
        ("B-HIGH", 900, "Alpha NCC", 2),
        ("C-LOW", 50, "Gamma NCC", 1),
    ):
        ln = _add_line(db, code, result_date="2026-10-10")
        db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, is_chosen=True,
                                   snap_price_by_volume=price, supplier_name=supplier))
        for i in range(extra_options):
            db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=i + 2,
                                       snap_price_by_volume=1, supplier_name="Zeta NCC"))
    #  Phương án chưa chốt KHÔNG được góp giá vào cột "Đơn giá báo".
    ln = _add_line(db, "D-UNCHOSEN")
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, is_chosen=False,
                               snap_price_by_volume=99999, supplier_name="Aaa NCC"))
    db.commit()


def test_xep_don_gia_bao_theo_phuong_an_da_chot(db, viewer, option_lines):
    codes = _codes(db, viewer, "sort_by=opt_price&sort_dir=desc")
    assert codes[:3] == ["B-HIGH", "A-MID", "C-LOW"]
    assert codes[3] == "D-UNCHOSEN"


def test_xep_so_phuong_an(db, viewer, option_lines):
    rows = _rows(db, viewer, "sort_by=option_count&sort_dir=desc")
    assert [r["option_count"] for r in rows] == [3, 2, 1, 1]
    assert rows[0]["code"] == "B-HIGH"


def test_xep_ten_ncc_khi_co_quyen_xem_ncc(db, viewer, option_lines):
    codes = _codes(db, viewer, "sort_by=opt_supplier_name&sort_dir=asc")
    #  Theo tên NCC của phương án CHỐT; dòng chưa chốt (ô trống) xuống cuối ở cả hai chiều.
    assert codes == ["B-HIGH", "A-MID", "C-LOW", "D-UNCHOSEN"]
    assert _codes(db, viewer, "sort_by=opt_supplier_name&sort_dir=desc") == [
        "C-LOW", "A-MID", "B-HIGH", "D-UNCHOSEN"]


def test_khong_co_quyen_xem_ncc_thi_xep_theo_ten_ncc_bi_bo_qua(db, viewer, option_lines):
    default = _codes(db, viewer, "", show_supplier=False)
    assert _codes(db, viewer, "sort_by=opt_supplier_name&sort_dir=asc", show_supplier=False) == default
    assert _codes(db, viewer, "sort_by=opt_supplier_name&sort_dir=desc", show_supplier=False) == default


# ── 4. Công ty theo tên ──────────────────────────────────────────────────────────
def test_xep_cong_ty_theo_ten_khong_theo_id(db, viewer):
    db.add_all([Company(id=1, code="ZZ", name="Zeta Holding"),
                Company(id=2, code="AA", name="Alpha Farm")])
    db.flush()
    _add_line(db, "A-ZETA", company_id=1)
    _add_line(db, "B-ALPHA", company_id=2)
    db.commit()

    assert _codes(db, viewer, "sort_by=company&sort_dir=asc") == ["B-ALPHA", "A-ZETA"]
    assert _codes(db, viewer, "sort_by=company&sort_dir=desc") == ["A-ZETA", "B-ALPHA"]


def test_khoa_la_khong_vo_truy_van_va_giu_thu_tu_mac_dinh(db, viewer):
    _add_line(db, "B-2")
    _add_line(db, "A-1")
    db.commit()
    assert _codes(db, viewer, "sort_by=khong_co_that&sort_dir=desc") == ["A-1", "B-2"]


# ── 5. Canh: mọi cột của bảng đều có cách xếp ────────────────────────────────────
def test_moi_cot_cua_bang_deu_xep_duoc(db):
    """Thêm cột mới vào `export.COLS` mà quên khai cách xếp thì giao diện lại có cột bấm không
    ăn — đúng lỗi của CR này."""
    smap = sp._sort_map()
    missing = [c.key for c in ex.COLS if c.key != "stt" and c.key not in smap
               and get_computed_sort_expression(db, c.key, "2026-11-10") is None]
    assert missing == []


# ── 6. Bổ sung sau khi rà mã ─────────────────────────────────────────────────────
def test_tt_phieu_va_tt_dong_xep_theo_dong_doi_khong_theo_chu_cai_cua_ma(db, viewer):
    """Cột lưu MÃ (`cancelled`, `done`, `draft`…) mà ô bày nhãn: xếp theo chữ cái của mã thì
    "Đã từ chối" đứng đầu, "Hoàn thành" đứng thứ hai — người xem tưởng bảng xếp lộn."""
    for code, status in (("A", "done"), ("B", "draft"), ("C", "cancelled"), ("D", "processing")):
        s = SurveyRequest(code=code, status=status, company_id=1)
        db.add(s)
        db.flush()
        db.add(SurveyRequestLine(survey_request_id=s.id, item_group="Bao bì", assignee="NV01",
                                 received_date="", result_due_date="", result_date="",
                                 line_status="", no_option=False, pr_code=""))
    db.commit()
    assert _codes(db, viewer, "sort_by=status&sort_dir=asc") == ["B", "D", "A", "C"]


def test_tt_dong_xep_theo_dong_doi_o_trong_xuong_cuoi_ca_hai_chieu(db, viewer):
    _add_line(db, "A-DONE", line_status="completed")
    _add_line(db, "B-BLANK")
    _add_line(db, "C-RESURVEY", line_status="resurvey")
    db.commit()
    assert _codes(db, viewer, "sort_by=line_status&sort_dir=asc") == ["C-RESURVEY", "A-DONE", "B-BLANK"]
    assert _codes(db, viewer, "sort_by=line_status&sort_dir=desc") == ["A-DONE", "C-RESURVEY", "B-BLANK"]


@pytest.mark.parametrize("hidden_key", ex.SUPPLIER_HIDDEN_KEYS)
def test_khong_co_quyen_xem_ncc_thi_moi_cot_bi_che_deu_khong_xep_duoc(db, viewer, hidden_key):
    """`internal_line_code` từng nằm trong `_sort_map()` mà không bị gác — người thiếu
    `supplier.read` gõ tay `?sort_by=internal_line_code` là xếp được theo cột đang bị che."""
    for code, value in (("A", "zz"), ("B", "mm"), ("C", "aa")):
        ln = _add_line(db, code, internal_line_code=value)
        db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, is_chosen=True,
                                   supplier_code=value, supplier_name=value,
                                   snap_internal_code=value, nstm_note=value))
    db.commit()
    #  Có quyền thì xếp được thật (giảm dần: zz, mm, aa) — chứng tỏ dữ liệu mẫu đủ làm lệch thứ tự.
    assert _codes(db, viewer, f"sort_by={hidden_key}&sort_dir=desc") == ["A", "B", "C"]
    assert _codes(db, viewer, f"sort_by={hidden_key}&sort_dir=asc", show_supplier=False) == ["A", "B", "C"]


def test_phuong_an_chot_nhan_trong_xep_theo_chu_option_dang_hien(db, viewer):
    for code, label, public_id in (("A", "Option 9 — ID 1", 9), ("B", "", 3)):
        ln = _add_line(db, code)
        db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=public_id,
                                   display_label=label, is_chosen=True))
    db.commit()
    rows = _rows(db, viewer, "sort_by=opt_label&sort_dir=asc")
    assert [r["opt_label"] for r in rows] == ["Option 3", "Option 9 — ID 1"]


def test_so_ngay_xu_ly_am_khi_tra_truoc_ngay_tiep_nhan_van_xep_dung(db, viewer):
    _add_line(db, "A-NEG", received_date="2026-10-10", result_date="2026-10-08")
    _add_line(db, "B-POS", received_date="2026-10-01", result_date="2026-10-03")
    db.commit()
    rows = _rows(db, viewer, "sort_by=handling_days&sort_dir=asc")
    assert [r["handling_days"] for r in rows] == [-2, 2]
