"""bao-CR-602 — khối Báo cáo thực hiện dùng chung YCBG + ĐMH.

Bốn thứ khóa bằng test:

1. ĐẦU báo cáo tạo lười, mỗi chứng từ một đầu, hai loại chứng từ cùng id KHÔNG đụng nhau.
2. ĐMH: nút dòng hàng bám dòng đơn — thêm dòng thì thêm nút, đổi tên hàng thì đổi tên
   nút, xóa dòng thì xóa nút mà hồ sơ về Chung; khối CHƯA khởi tạo thì đồng bộ không
   đẻ gì (người chỉ xem không thấy một khối «có nội dung» chỉ vì đơn có dòng).
3. Luật theo loại chứng từ ở controller: ĐMH cấm sửa nút tay (400), khóa khi đơn
   Hoàn thành/Hủy, cửa ghi là `purchase_order.write`.
4. Cột «Kết quả» (`result`) có trần độ dài ở schema (SQLite không ép VARCHAR).
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.survey_request import report_controller as ctl
from app.modules.survey_request import report_service as svc
from app.modules.survey_request.model import SurveyRequest
from app.modules.survey_request.report_constants import DEFAULT_TEMPLATE_DOCS
from app.modules.survey_request.report_model import ExecReport, SurveyReportDoc
from app.modules.survey_request.report_schema import ReportDocIn, ReportDocPatch

PO = "purchase_order"
SR = "survey_request"


def _po(db, seed, code="PO-BC598", status="approved") -> PurchaseOrder:
    po = PurchaseOrder(code=code, order_date="2026-10-01", status=status,
                       company_id=seed.company_id)
    db.add(po)
    db.commit()
    return po


def _po_line(db, po_id: int, name: str, code: str = "") -> POItem:
    row = POItem(po_id=po_id, product_code=code or name[:10], product_name=name, qty_order=1)
    db.add(row)
    db.commit()
    return row


# ── 1. đầu báo cáo ──────────────────────────────────────────────────────────────
def test_dau_bao_cao_tao_luoi_va_khong_dung_nhau_giua_hai_loai_chung_tu(db, seed):
    po = _po(db, seed)
    sr = SurveyRequest(code="YCKS-598", status="processing")
    db.add(sr)
    db.commit()
    #  Cố tình cho YCBG và ĐMH cùng id chứng từ: hai đầu phải khác nhau.
    assert svc.report_id_of(db, PO, po.id) == 0
    head_po = svc.ensure_report(db, PO, po.id, user_id=1)
    head_sr = svc.ensure_report(db, SR, po.id, user_id=1)
    db.commit()
    assert head_po.id != head_sr.id
    assert svc.ensure_report(db, PO, po.id, user_id=1).id == head_po.id     # không nhân đôi
    assert db.query(ExecReport).count() == 2
    #  Loại chứng từ lạ → 404 chứ không âm thầm tạo đầu.
    with pytest.raises(HTTPException) as e:
        svc.ensure_report(db, "payment_request", 1, user_id=1)
    assert e.value.status_code == 404
    #  Chưa có đầu thì khối rỗng và không chặn đóng chứng từ.
    assert svc.get_report_payload(db, 0)["docs"] == []
    assert svc.required_docs_pending_of(db, PO, 999) == []


# ── 2. nút bám dòng đơn ─────────────────────────────────────────────────────────
def test_khoi_tao_dmh_dung_nut_theo_dong_don_va_dong_bo_khi_don_doi(db, seed):
    po = _po(db, seed)
    a = _po_line(db, po.id, "Abamectin 3.6EC")
    b = _po_line(db, po.id, "", code="SP-KHONG-TEN")        # không tên → lùi về mã hàng
    rid = svc.ensure_report(db, PO, po.id, user_id=1).id

    lines = ctl._po_lines(db, po)
    assert lines == [(a.id, "Abamectin 3.6EC"), (b.id, "SP-KHONG-TEN")]
    assert svc.init_report(db, rid, lines, user_id=1) == len(DEFAULT_TEMPLATE_DOCS)
    db.commit()
    items = svc.get_report_payload(db, rid)["items"]
    assert [(i["line_id"], i["name"]) for i in items] == lines

    #  Đơn đổi: thêm dòng c, đổi tên a, xóa b (hồ sơ gắn b phải về Chung, không mất).
    phase_id = svc.get_report_payload(db, rid)["phases"][0]["id"]
    item_b = next(i for i in items if i["line_id"] == b.id)
    doc = svc.create_doc(db, rid, ReportDocIn(title="GP riêng của b", phase_id=phase_id,
                                               item_id=item_b["id"]), user_id=1)
    #  Thêm c TRƯỚC khi xóa b: SQLite của bộ test tái dùng id vừa xóa (MySQL thì không),
    #  xóa trước là c nhận đúng id của b và bài kiểm xanh giả.
    c = _po_line(db, po.id, "Dầu khoáng")
    a.product_name = "Abamectin 3.6EC (thùng 20L)"
    db.delete(b)
    db.commit()

    assert svc.sync_line_items(db, rid, ctl._po_lines(db, po), user_id=1) is True
    db.commit()
    items = svc.get_report_payload(db, rid)["items"]
    assert [(i["line_id"], i["name"]) for i in items] == [
        (a.id, "Abamectin 3.6EC (thùng 20L)"), (c.id, "Dầu khoáng")]
    assert db.get(SurveyReportDoc, doc.id).item_id == 0
    #  Đồng bộ lần hai không đổi gì → False (controller không commit thừa).
    assert svc.sync_line_items(db, rid, ctl._po_lines(db, po), user_id=1) is False


def test_dong_bo_khong_de_nut_khi_khoi_chua_khoi_tao(db, seed):
    po = _po(db, seed)
    _po_line(db, po.id, "Hàng A")
    rid = svc.ensure_report(db, PO, po.id, user_id=1).id
    db.commit()
    assert svc.sync_line_items(db, rid, ctl._po_lines(db, po), user_id=1) is False
    assert svc.get_report_payload(db, rid)["items"] == []


def test_nut_dat_tay_cua_ycbg_khong_bi_dong_bo_dung_toi(db, seed):
    """YCBG vẫn là nút đặt tay (`line_id = 0`) — có gọi đồng bộ cũng không xóa/đổi tên."""
    sr = SurveyRequest(code="YCKS-598b", status="processing")
    db.add(sr)
    db.commit()
    rid = svc.ensure_report(db, SR, sr.id, user_id=1).id
    svc.create_item(db, rid, "Nút tay", user_id=1)
    db.commit()
    assert svc.sync_line_items(db, rid, [(777, "Dòng lạ")], user_id=1) is True   # chỉ THÊM 777
    names = [(i["line_id"], i["name"]) for i in svc.get_report_payload(db, rid)["items"]]
    assert names == [(0, "Nút tay"), (777, "Dòng lạ")]


# ── 3. luật theo loại chứng từ ở controller ────────────────────────────────────
def test_luat_dmh_khoa_nut_tay_va_cua_ghi_la_write():
    rule = ctl._rule_of(PO)
    assert rule.items_locked is True
    assert (rule.read_action, rule.write_action, rule.write_scope_action) == ("read", "write", "write")
    assert rule.locked_statuses == ("completed", "cancelled")
    with pytest.raises(HTTPException) as e:
        ctl._items_editable(PO)
    assert e.value.status_code == 400
    ctl._items_editable(SR)                     # YCBG vẫn sửa nút tay được

    sr_rule = ctl._rule_of(SR)
    assert sr_rule.items_locked is False
    #  Cờ `process` không có grant phạm vi → phạm vi ghi của YCBG vẫn hỏi theo `read`.
    assert (sr_rule.write_action, sr_rule.write_scope_action) == ("process", "read")
    with pytest.raises(HTTPException) as e:
        ctl._rule_of("payment_request")
    assert e.value.status_code == 404


@pytest.fixture
def no_scope(monkeypatch):
    """Bỏ lớp phạm vi của ĐMH để kiểm riêng luật của khối (phạm vi đã có bài riêng)."""
    import dataclasses

    rule = ctl._OWNER_RULES[PO]
    monkeypatch.setitem(ctl._OWNER_RULES, PO, dataclasses.replace(
        rule, load=lambda db, oid, user, action: db.get(PurchaseOrder, oid)))


def test_don_hoan_thanh_hoac_huy_thi_khoa_bao_cao(db, seed, no_scope):
    """`_writable` chặn 400 khi đơn đã chốt — kể cả người có quyền `write`."""
    from types import SimpleNamespace

    admin = SimpleNamespace(id=seed.u_nstm_id)
    done = _po(db, seed, code="PO-DONE", status="completed")
    with pytest.raises(HTTPException) as e:
        ctl._writable(db, PO, done.id, admin)
    assert e.value.status_code == 400 and "hoàn thành" in e.value.detail
    live = _po(db, seed, code="PO-LIVE", status="approved")
    parent, rid = ctl._writable(db, PO, live.id, admin)
    assert parent.id == live.id and rid == svc.report_id_of(db, PO, live.id) > 0


def test_doc_dmh_tu_dong_bo_nut_theo_dong_don(db, seed, no_scope):
    """GET của ĐMH chạy đồng bộ: dòng thêm sau khi khởi tạo tự có nút."""
    from types import SimpleNamespace

    admin = SimpleNamespace(id=seed.u_nstm_id)
    po = _po(db, seed, code="PO-GET")
    _po_line(db, po.id, "Hàng 1")
    parent, rid = ctl._writable(db, PO, po.id, admin)
    svc.init_report(db, rid, ctl._po_lines(db, parent), user_id=admin.id)
    db.commit()
    _po_line(db, po.id, "Hàng 2")
    _, rid2 = ctl._readable(db, PO, po.id, admin)
    assert rid2 == rid
    assert [i["name"] for i in svc.get_report_payload(db, rid)["items"]] == ["Hàng 1", "Hàng 2"]


# ── 4. cột Kết quả ──────────────────────────────────────────────────────────────
def test_cot_ket_qua_luu_duoc_va_co_tran_o_schema(db, seed):
    po = _po(db, seed, code="PO-KQ")
    rid = svc.ensure_report(db, PO, po.id, user_id=1).id
    ph = svc.create_phase(db, rid, "GĐ1", "", 1)
    doc = svc.create_doc(db, rid, ReportDocIn(title="Deal giá", phase_id=ph.id,
                                               result="Đã chốt Aston, công nợ 60 ngày"), user_id=1)
    db.commit()
    assert svc.get_report_payload(db, rid)["docs"][0]["result"] == "Đã chốt Aston, công nợ 60 ngày"
    svc.update_doc(db, rid, doc.id, ReportDocPatch(result=""), user_id=1)
    db.commit()
    assert db.get(SurveyReportDoc, doc.id).result == ""
    #  Hoàn tác giữ cả cột Kết quả.
    svc.update_doc(db, rid, doc.id, ReportDocPatch(result="KQ"), user_id=1)
    db.commit()                     # mỗi thao tác là một request riêng, controller commit từng cái
    svc.delete_all(db, rid, user_id=1)
    svc.restore_latest(db, rid, user_id=1)
    db.commit()
    assert svc.get_report_payload(db, rid)["docs"][0]["result"] == "KQ"
    with pytest.raises(ValidationError):
        ReportDocIn(title="ok", phase_id=1, result="x" * 1001)
    with pytest.raises(ValidationError):
        ReportDocPatch(result="x" * 1001)
