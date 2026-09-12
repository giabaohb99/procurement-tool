"""Khối BÁO CÁO THỰC HIỆN trên phiếu YCBG (tab_survey_request_report_*).

Bốn thứ phải khóa bằng test:

1. `init_report` idempotent — bấm «Khởi tạo» hai lần không nhân đôi khung.
2. Ba đường XÓA phải dọn hậu quả: xóa nút → hồ sơ về Chung; xóa hồ sơ → gỡ khỏi
   danh sách tiên quyết của hồ sơ khác; xóa giai đoạn còn hồ sơ → CHẶN.
3. Vòng tiên quyết bị chặn lúc lưu — để lọt là cả cụm hồ sơ khóa lẫn nhau vĩnh viễn.
4. Trần độ dài chuỗi kiểm ở tầng SCHEMA — test backend chạy SQLite, nơi VARCHAR
   không bị ép, nên ghi xuống DB rồi khẳng định là xanh giả (duoc-CR-316).
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.survey_request import report_service as svc
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.survey_request.report_constants import DEFAULT_PHASES, RD_DONE
from app.modules.survey_request.report_model import (SurveyReportDoc,
                                                     SurveyReportItem,
                                                     SurveyReportPhase)
from app.modules.survey_request.report_schema import (ReportDocIn, ReportDocPatch,
                                                      ReportItemIn)


def _sr(db, code="YCKS-BC1", **kw) -> SurveyRequest:
    s = SurveyRequest(code=code, status="processing", **kw)
    db.add(s)
    db.commit()
    return s


def _line(db, sr_id, **kw) -> SurveyRequestLine:
    ln = SurveyRequestLine(survey_request_id=sr_id, **kw)
    db.add(ln)
    db.commit()
    return ln


def _doc(db, sr_id, phase_id, title="Hồ sơ", **kw) -> SurveyReportDoc:
    return svc.create_doc(db, sr_id, ReportDocIn(title=title, phase_id=phase_id, **kw),
                          user_id=1)


# ── init_report ─────────────────────────────────────────────────────────────────
def test_khoi_tao_dung_khung_va_khong_nhan_doi(db):
    s = _sr(db)
    _line(db, s.id, requirement_detail="K2SO4 tinh khiết 98%\ndòng hai bị cắt")
    _line(db, s.id, requirement_detail="", item_group="Phân bón")
    _line(db, s.id)          # dòng trống hoàn toàn -> tên «Dòng 3»

    assert svc.init_report(db, s.id, user_id=1) is True
    payload = svc.get_report_payload(db, s.id)
    assert [p["name"] for p in payload["phases"]] == [n for n, _ in DEFAULT_PHASES]
    # Tên nút: mô tả yêu cầu (chỉ dòng đầu) > phân loại > «Dòng N».
    assert [i["name"] for i in payload["items"]] == [
        "K2SO4 tinh khiết 98%", "Phân bón", "Dòng 3"]

    # Bấm lần hai: không đụng gì.
    assert svc.init_report(db, s.id, user_id=1) is False
    again = svc.get_report_payload(db, s.id)
    assert len(again["phases"]) == 5 and len(again["items"]) == 3


# ── xóa nút / hồ sơ / giai đoạn ─────────────────────────────────────────────────
def test_xoa_nut_thi_ho_so_ve_chung_khong_mat(db):
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    item = svc.create_item(db, s.id, "KNO3", 1)
    doc = _doc(db, s.id, ph.id, title="GP tiền chất", item_id=item.id)
    db.commit()

    svc.delete_item(db, s.id, item.id, user_id=1)
    db.commit()
    assert db.get(SurveyReportDoc, doc.id).item_id == 0    # về Chung, không bị xóa lây


def test_xoa_ho_so_thi_go_khoi_tien_quyet_cua_ho_so_khac(db):
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    a = _doc(db, s.id, ph.id, title="RFQ")
    b = _doc(db, s.id, ph.id, title="Hợp đồng", depends=[a.id])
    db.commit()

    svc.delete_doc(db, s.id, a.id, user_id=1)
    db.commit()
    # Không gỡ thì b chờ một id chết -> khóa vĩnh viễn.
    assert db.get(SurveyReportDoc, b.id).depends == []


def test_xoa_giai_doan_con_ho_so_bi_chan(db):
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    _doc(db, s.id, ph.id)
    db.commit()

    with pytest.raises(HTTPException) as e:
        svc.delete_phase(db, s.id, ph.id)
    assert e.value.status_code == 400

    ph2 = svc.create_phase(db, s.id, "GĐ trống", "", 1)
    db.commit()
    svc.delete_phase(db, s.id, ph2.id)        # giai đoạn rỗng xóa được
    db.commit()
    assert db.get(SurveyReportPhase, ph2.id) is None


# ── tiên quyết ──────────────────────────────────────────────────────────────────
def test_tien_quyet_chan_vong_va_tu_tro_minh(db):
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    a = _doc(db, s.id, ph.id, title="A")
    b = _doc(db, s.id, ph.id, title="B", depends=[a.id])
    c = _doc(db, s.id, ph.id, title="C", depends=[b.id])
    db.commit()

    # A chờ C trong khi C -> B -> A: vòng ba đỉnh, phải chặn.
    with pytest.raises(HTTPException):
        svc.update_doc(db, s.id, a.id, ReportDocPatch(depends=[c.id]), user_id=1)
    with pytest.raises(HTTPException):
        svc.update_doc(db, s.id, a.id, ReportDocPatch(depends=[a.id]), user_id=1)


def test_tien_quyet_phai_cung_phieu(db):
    s1, s2 = _sr(db), _sr(db, code="YCKS-BC2")
    ph1 = svc.create_phase(db, s1.id, "GĐ1", "", 1)
    ph2 = svc.create_phase(db, s2.id, "GĐ1", "", 1)
    ngoai = _doc(db, s2.id, ph2.id, title="Của phiếu khác")
    db.commit()

    with pytest.raises(HTTPException):
        _doc(db, s1.id, ph1.id, title="X", depends=[ngoai.id])


def test_payload_loc_id_tien_quyet_chet(db):
    """Id chết lọt vào `depends` (dữ liệu cũ, sửa tay DB) không được ra FE —
    FE đếm nó là «chưa xong» và hồ sơ khóa vĩnh viễn."""
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    a = _doc(db, s.id, ph.id, title="A")
    b = _doc(db, s.id, ph.id, title="B")
    db.commit()
    db.get(SurveyReportDoc, b.id).depends = [a.id, 999999]
    db.commit()

    docs = {d["title"]: d for d in svc.get_report_payload(db, s.id)["docs"]}
    assert docs["B"]["depends"] == [a.id]


def test_ho_so_cua_phieu_khac_khong_lo_sang(db):
    s1, s2 = _sr(db), _sr(db, code="YCKS-BC3")
    ph2 = svc.create_phase(db, s2.id, "GĐ1", "", 1)
    _doc(db, s2.id, ph2.id, title="Riêng tư")
    db.commit()

    assert svc.get_report_payload(db, s1.id) == {"items": [], "phases": [], "docs": []}
    with pytest.raises(HTTPException):        # sửa chéo phiếu -> 404
        svc.update_doc(db, s1.id,
                       svc.get_report_payload(db, s2.id)["docs"][0]["id"],
                       ReportDocPatch(status=RD_DONE), user_id=1)


# ── schema: trần độ dài kiểm ở tầng schema (SQLite không ép VARCHAR) ────────────
def test_schema_chan_chuoi_dai_va_ma_trang_thai_la(db):
    ph_id = 1
    with pytest.raises(ValidationError):
        ReportDocIn(title="x" * 256, phase_id=ph_id)
    with pytest.raises(ValidationError):
        ReportDocIn(title="ok", phase_id=ph_id, file_note="x" * 501)
    with pytest.raises(ValidationError):
        ReportDocIn(title="ok", phase_id=ph_id, status=9)
    with pytest.raises(ValidationError):
        ReportDocIn(title="ok", phase_id=ph_id, depends=list(range(1, 33)))
    with pytest.raises(ValidationError):
        ReportItemIn(name="   ")
    with pytest.raises(ValidationError):
        ReportItemIn(name="x" * 101)


def test_tran_so_dong_moi_bang_con(db):
    """`sort_order` là SMALLINT — không trần thì dòng 32768 tràn số im lặng."""
    s = _sr(db)
    for i in range(50):
        svc.create_item(db, s.id, f"Nút {i}", 1)
    with pytest.raises(HTTPException) as e:
        svc.create_item(db, s.id, "Nút 51", 1)
    assert e.value.status_code == 400
