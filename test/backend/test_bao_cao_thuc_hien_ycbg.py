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

from app.modules.employee.model import Employee
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

    empty = svc.get_report_payload(db, s1.id)
    assert empty["items"] == [] and empty["phases"] == [] and empty["docs"] == []
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


# ── ngày bắt đầu / hết hiệu lực / nhân sự thực hiện ─────────────────────────────
def test_tao_ho_so_luu_ngay_va_nhan_su_resolve_ten(db):
    emp = Employee(code="NV01", full_name="Nguyễn Văn An")
    db.add(emp)
    db.commit()
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    _doc(db, s.id, ph.id, title="Giấy phép", start_date="2026-09-01",
         expires_at="2026-12-31", assignee_id=emp.id)
    db.commit()

    doc = svc.get_report_payload(db, s.id)["docs"][0]
    assert doc["start_date"] == "2026-09-01"
    assert doc["expires_at"] == "2026-12-31"
    assert doc["assignee_id"] == emp.id
    assert doc["assignee_name"] == "Nguyễn Văn An"


def test_nhan_su_id_chet_ra_ten_rong(db):
    """Nhân sự bị xóa sau khi đã cử — id chết không được làm vỡ payload, chỉ ra ''."""
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    _doc(db, s.id, ph.id, title="X", assignee_id=999999)
    db.commit()
    doc = svc.get_report_payload(db, s.id)["docs"][0]
    assert doc["assignee_id"] == 999999 and doc["assignee_name"] == ""


def test_patch_chuoi_rong_xoa_ngay_khac_none_bo_qua(db):
    """'' = XÓA ngày (ghi None); không gửi = giữ nguyên. Hai nghĩa phải khác nhau."""
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    doc = _doc(db, s.id, ph.id, title="X", start_date="2026-09-01", expires_at="2026-10-01")
    db.commit()

    # Không gửi expires_at -> giữ nguyên; gửi start_date='' -> xóa.
    svc.update_doc(db, s.id, doc.id, ReportDocPatch(start_date=""), user_id=1)
    db.commit()
    row = db.get(SurveyReportDoc, doc.id)
    assert row.start_date is None and row.expires_at is not None


def test_schema_chan_ngay_sai_dinh_dang(db):
    # Sai định dạng phải 422 (ValidationError) chứ không đâm xuống DB thành 500.
    with pytest.raises(ValidationError):
        ReportDocIn(title="ok", phase_id=1, expires_at="31/12/2026")
    with pytest.raises(ValidationError):
        ReportDocIn(title="ok", phase_id=1, start_date="2026-13-99")
    # Rỗng là hợp lệ (chưa đặt).
    assert ReportDocIn(title="ok", phase_id=1, start_date="", expires_at="").expires_at == ""


def test_tran_so_dong_moi_bang_con(db):
    """`sort_order` là SMALLINT — không trần thì dòng 32768 tràn số im lặng."""
    s = _sr(db)
    for i in range(50):
        svc.create_item(db, s.id, f"Nút {i}", 1)
    with pytest.raises(HTTPException) as e:
        svc.create_item(db, s.id, "Nút 51", 1)
    assert e.value.status_code == 400


# ── điều kiện đóng phiếu: hồ sơ báo cáo BẮT BUỘC phải hoàn tất ──────────────────
def test_required_docs_pending_chi_dem_bat_buoc_chua_xong(db):
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    _doc(db, s.id, ph.id, title="Bắt buộc chưa xong", required=True, status=0)
    _doc(db, s.id, ph.id, title="Bắt buộc xong", required=True, status=RD_DONE)
    _doc(db, s.id, ph.id, title="Tùy chọn chưa xong", required=False, status=0)
    db.commit()

    pending = svc.required_docs_pending(db, s.id)
    assert [d.title for d in pending] == ["Bắt buộc chưa xong"]


def _sr_at(db, code, status):
    """Phiếu ở đúng một trạng thái — `_sr` cố định 'processing' nên set lại rồi commit."""
    s = _sr(db, code=code)
    s.status = status
    db.commit()
    return s


def test_finalize_bi_chan_khi_con_ho_so_bat_buoc(db):
    from app.modules.survey_request.service import finalize_sr

    s = _sr_at(db, "YCKS-FIN", "survey_done")
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    doc = _doc(db, s.id, ph.id, title="Giấy phép", required=True, status=0)
    db.commit()

    with pytest.raises(HTTPException) as e:
        finalize_sr(db, s.id, user_id=1)
    assert e.value.status_code == 400

    # Hoàn tất hồ sơ bắt buộc -> đóng được.
    svc.update_doc(db, s.id, doc.id, ReportDocPatch(status=RD_DONE), user_id=1)
    db.commit()
    assert finalize_sr(db, s.id, user_id=1).status == "done"


# ── xóa cả khối + hoàn tác ─────────────────────────────────────────────────────
def test_xoa_ca_khoi_roi_hoan_tac_dung_cau_truc_va_tien_quyet(db):
    s = _sr(db)
    ph1 = svc.create_phase(db, s.id, "GĐ1", "Nơi 1", 1)
    ph2 = svc.create_phase(db, s.id, "GĐ2", "Nơi 2", 2)
    item = svc.create_item(db, s.id, "KNO3", 1)
    a = _doc(db, s.id, ph1.id, title="A", item_id=item.id, required=True, status=RD_DONE)
    b = _doc(db, s.id, ph2.id, title="B", depends=[a.id], required=False)
    db.commit()

    # Xóa cả khối -> rỗng, còn 1 bản trash chưa hoàn tác.
    trash = svc.delete_all(db, s.id, user_id=1)
    trash.audit_id = 555
    db.commit()
    payload = svc.get_report_payload(db, s.id)
    assert payload["docs"] == [] and payload["phases"] == [] and payload["items"] == []
    assert payload["restorable"] is True and payload["restorable_audit_id"] == 555

    # Hoàn tác -> dựng lại 2 giai đoạn, 1 nút, 2 hồ sơ; depends B->A ánh xạ đúng id mới.
    assert svc.restore_latest(db, s.id, user_id=1) is not None
    db.commit()
    p2 = svc.get_report_payload(db, s.id)
    assert len(p2["phases"]) == 2 and len(p2["items"]) == 1 and len(p2["docs"]) == 2
    by_title = {d["title"]: d for d in p2["docs"]}
    assert by_title["A"]["status"] == RD_DONE and by_title["A"]["required"] is True
    # B phụ thuộc A theo ID MỚI (không phải id cũ đã chết).
    assert by_title["B"]["depends"] == [by_title["A"]["id"]]
    assert by_title["A"]["item_id"] == p2["items"][0]["id"]     # nút cũng ánh xạ đúng
    # Đã hoàn tác thì hết restorable.
    assert p2["restorable"] is False


def test_hoan_tac_khong_nhan_doi_khi_khoi_da_co_noi_dung(db):
    """Xóa rồi tự thêm hồ sơ mới, sau đó bấm Hoàn tác: KHÔNG dựng chồng lên."""
    s = _sr(db)
    ph = svc.create_phase(db, s.id, "GĐ1", "", 1)
    _doc(db, s.id, ph.id, title="Cũ")
    db.commit()
    svc.delete_all(db, s.id, user_id=1)
    db.commit()
    # Người dùng dựng nội dung mới.
    ph2 = svc.create_phase(db, s.id, "GĐ mới", "", 1)
    _doc(db, s.id, ph2.id, title="Mới")
    db.commit()

    svc.restore_latest(db, s.id, user_id=1)      # không được nhân đôi
    db.commit()
    titles = [d["title"] for d in svc.get_report_payload(db, s.id)["docs"]]
    assert titles == ["Mới"]


def test_finalize_qua_khi_khong_co_bao_cao_hoac_chi_tuy_chon(db):
    """Báo cáo là TÙY CHỌN — phiếu không khai báo cáo, hoặc chỉ có hồ sơ tùy chọn
    chưa xong, vẫn đóng được."""
    from app.modules.survey_request.service import finalize_sr

    s1 = _sr_at(db, "YCKS-F1", "survey_done")           # không có báo cáo
    assert finalize_sr(db, s1.id, user_id=1).status == "done"

    s2 = _sr_at(db, "YCKS-F2", "pr_created")
    ph = svc.create_phase(db, s2.id, "GĐ1", "", 1)
    _doc(db, s2.id, ph.id, title="Tùy chọn", required=False, status=0)
    db.commit()
    assert finalize_sr(db, s2.id, user_id=1).status == "done"
