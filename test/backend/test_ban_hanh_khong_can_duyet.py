"""BAN HÀNH KHÔNG QUA DUYỆT + NÚT BAN HÀNH CỦA NGƯỜI SOẠN (29/09/2026).

Hai lỗi cùng một chỗ:

1. Ô «Cần duyệt» của loại văn bản chỉ để trưng: thẻ *Người duyệt dự kiến* báo
   «KHÔNG cần phê duyệt» mà văn bản vẫn phải gửi duyệt. Đại ca chốt: loại đó bỏ
   hẳn chặng duyệt — người soạn bấm *Ban hành* là có hiệu lực.
2. Nút *Ban hành* ở trạng thái *Chờ ban hành* gọi `/approve`, đường đó đòi quyền
   Duyệt — vai trò «Văn bản — soạn & sửa» (không có Duyệt) bấm vào chỉ ăn 403.
   Nay cả hai ca đi qua `/issue`, gác bằng quyền SỬA + đúng người.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import instance_service
from app.modules.doc_catalog.model import DocType
from app.modules.document import controller, serializer, service
from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                        STATUS_PENDING_ISSUE)
from app.modules.document.schema import DocumentCreate
from app.modules.document.version_model import VERSION_SUBMITTED


@pytest.fixture()
def kinds(db):
    bm = DocType(code="BM", name="Biểu mẫu", id_scheme=1, number_when=2, needs_approval=False)
    qc = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2, needs_approval=True)
    db.add_all([bm, qc])
    db.commit()
    return {"bm": bm, "qc": qc}


def _draft(db, seed, kind, *, content="<p>Mẫu phiếu đề nghị.</p>"):
    return service.create_document(db, DocumentCreate(
        doc_type_id=kind.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, drafter_employee_id=seed.emp_req_id,
        title="Mẫu đề nghị thanh toán", content_html=content,
    ), seed.u_req_id)


def _user(seed, user_id, employee_id):
    return SimpleNamespace(id=user_id, employee_id=employee_id)


# ── Tầng nghiệp vụ ───────────────────────────────────────────────────────────

def test_loai_khong_can_duyet_ban_hanh_thang_co_so_va_hieu_luc(db, seed, kinds):
    doc = _draft(db, seed, kinds["bm"])

    service.issue_without_approval(db, doc, seed.u_req_id)
    db.refresh(doc)

    assert doc.status == STATUS_EFFECTIVE
    assert doc.doc_code, "ban hành thẳng vẫn phải cấp số hiệu như ban hành thường"
    #  Không có phiên duyệt nào treo lại — không ai phải duyệt cái đã có hiệu lực.
    assert instance_service.running_instance(db, "document", doc.id) is None


def test_loai_can_duyet_khong_duoc_ban_hanh_thang(db, seed, kinds):
    doc = _draft(db, seed, kinds["qc"])

    with pytest.raises(HTTPException) as err:
        service.issue_without_approval(db, doc, seed.u_req_id)
    assert err.value.status_code == 400
    db.refresh(doc)
    assert doc.status == STATUS_DRAFT


def test_ban_hanh_thang_van_kiem_nhu_gui_duyet(db, seed, kinds):
    """Bỏ chặng duyệt KHÔNG có nghĩa là bỏ luôn mấy điều người duyệt lẽ ra kiểm."""
    doc = _draft(db, seed, kinds["bm"], content="")

    with pytest.raises(HTTPException) as err:
        service.issue_without_approval(db, doc, seed.u_req_id)
    assert "trống" in err.value.detail
    db.refresh(doc)
    assert doc.status == STATUS_DRAFT


def test_gui_duyet_loai_khong_can_duyet_van_chay_nhu_cu(db, seed, kinds):
    """Loại cũ trên prod có thể còn `needs_approval = 0` do mặc định cũ là False —
    chặn `submit` là văn bản của loại đó hết đường gửi duyệt. Đổi hành vi nằm ở
    màn hình và đường `/issue`, không ở `submit`."""
    doc = _draft(db, seed, kinds["bm"])

    service.submit(db, doc, seed.u_req_id)

    assert service.open_version(db, doc).status == VERSION_SUBMITTED


def test_serializer_bao_loai_co_can_duyet_khong(db, seed, kinds):
    bm = _draft(db, seed, kinds["bm"])
    qc = _draft(db, seed, kinds["qc"])

    out = {row["id"]: row for row in serializer.serialize_many(db, [bm, qc])}

    assert out[bm.id]["doc_type_needs_approval"] is False
    assert out[qc.id]["doc_type_needs_approval"] is True


# ── Tầng API: ai được bấm «Ban hành» ─────────────────────────────────────────

@pytest.fixture()
def api(monkeypatch):
    """Gỡ `_load` (quyền phạm vi đọc/sửa) để kiểm RIÊNG luật «ai được bấm» của
    `/issue`; và tắt kênh ghi nhật ký cho gọn."""
    state = {"approve": False}
    monkeypatch.setattr(controller, "_load", lambda db, doc_id, user, *_a: service.get_or_404(db, doc_id))
    monkeypatch.setattr(controller, "_can_approve_doc", lambda db, doc, user: state["approve"])
    monkeypatch.setattr(controller, "record", lambda *a, **k: None)
    return state


def test_nguoi_soan_ban_hanh_duoc_du_khong_co_quyen_duyet(db, seed, kinds, api):
    doc = _draft(db, seed, kinds["bm"])

    controller.issue_document(doc.id, None, db, _user(seed, seed.u_req_id, seed.emp_req_id))

    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE


def test_nguoi_ngoai_khong_ban_hanh_duoc(db, seed, kinds, api):
    doc = _draft(db, seed, kinds["bm"])

    with pytest.raises(HTTPException) as err:
        controller.issue_document(doc.id, None, db, _user(seed, seed.u_nstm_id, seed.emp_nstm_id))
    assert err.value.status_code == 403
    db.refresh(doc)
    assert doc.status == STATUS_DRAFT


def test_nguoi_co_quyen_duyet_ban_hanh_thay_duoc(db, seed, kinds, api):
    api["approve"] = True
    doc = _draft(db, seed, kinds["bm"])

    controller.issue_document(doc.id, None, db, _user(seed, seed.u_nstm_id, seed.emp_nstm_id))

    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE


def test_cho_ban_hanh_nguoi_soan_bam_duoc_khong_can_quyen_duyet(db, seed, kinds, api):
    """LỖI ĐÃ XẢY RA: nút *Ban hành* ở *Chờ ban hành* gọi `/approve` đòi quyền
    Duyệt, nên người soạn thuộc vai trò «soạn & sửa» không phát hành được văn
    bản của chính mình."""
    doc = _draft(db, seed, kinds["qc"])
    version = service.open_version(db, doc)
    version.status = VERSION_SUBMITTED
    doc.status = STATUS_PENDING_ISSUE
    db.commit()

    controller.issue_document(doc.id, None, db, _user(seed, seed.u_req_id, seed.emp_req_id))

    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE


def test_cho_ban_hanh_nguoi_khac_khong_bam_thay_duoc(db, seed, kinds, api):
    api["approve"] = True  # có quyền Duyệt cũng không thay được người soạn ở nhịp này
    doc = _draft(db, seed, kinds["qc"])
    version = service.open_version(db, doc)
    version.status = VERSION_SUBMITTED
    doc.status = STATUS_PENDING_ISSUE
    db.commit()

    with pytest.raises(HTTPException) as err:
        controller.issue_document(doc.id, None, db, _user(seed, seed.u_nstm_id, seed.emp_nstm_id))
    assert err.value.status_code == 403


# ── Các lỗ code-review 29/09/2026 ────────────────────────────────────────────

def test_mac_dinh_loai_moi_la_can_duyet():
    """I1 — quên tích ô «Cần duyệt» phải ra «cần duyệt», không phải «tự ban hành»."""
    from app.modules.doc_catalog.schema import DocTypeCreate
    assert DocTypeCreate.model_fields["needs_approval"].default is True
    assert DocType(code="X", name="X").needs_approval in (True, None)


def test_van_ban_da_tung_gui_duyet_khong_ban_hanh_thang_duoc(db, seed, kinds):
    """I2 — bị Trả lại xong mà bấm Ban hành thẳng là xóa lời của người duyệt."""
    from app.modules.approval.instance_model import INSTANCE_RETURNED, ApprovalInstance
    doc = _draft(db, seed, kinds["bm"])
    db.add(ApprovalInstance(entity="document", entity_id=doc.id, flow_id=1, flow_version=1,
                            status=INSTANCE_RETURNED, current_seq=1,
                            created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()

    with pytest.raises(HTTPException) as err:
        service.issue_without_approval(db, doc, seed.u_req_id)
    assert err.value.status_code == 400
    assert "từng gửi duyệt" in err.value.detail


def test_doi_sang_loai_khong_can_duyet_phai_co_quyen_duyet(db, seed, kinds, monkeypatch):
    """I2 — đổi bản nháp «Quy chế» sang «Biểu mẫu» rồi bấm Ban hành là lối tắt."""
    from app.modules.document.schema import DocumentUpdate
    monkeypatch.setattr(service, "user_has_permission", lambda db, user, e, a: False)
    doc = _draft(db, seed, kinds["qc"])

    with pytest.raises(HTTPException) as err:
        service.update_document(db, doc, DocumentUpdate(doc_type_id=kinds["bm"].id),
                                seed.u_req_id, user=_user(seed, seed.u_req_id, seed.emp_req_id))
    assert err.value.status_code == 403

    #  Người có quyền Duyệt thì đổi được — đó là quyết định của người duyệt.
    monkeypatch.setattr(service, "user_has_permission", lambda db, user, e, a: True)
    service.update_document(db, doc, DocumentUpdate(doc_type_id=kinds["bm"].id),
                            seed.u_req_id, user=_user(seed, seed.u_req_id, seed.emp_req_id))
    db.refresh(doc)
    assert doc.doc_type_id == kinds["bm"].id


def test_ban_2_cho_ban_hanh_duoc_nhan_ra(db, seed, kinds):
    """I4 — bản 2 chờ ban hành: văn bản vẫn «Có hiệu lực», nhận ra bằng phiên đã duyệt."""
    from app.modules.approval.instance_model import INSTANCE_APPROVED, ApprovalInstance
    from app.modules.document.version_model import DocumentVersion
    doc = _draft(db, seed, kinds["bm"])
    service.issue_without_approval(db, doc, seed.u_req_id)
    db.refresh(doc)
    first = service.get_or_404(db, doc.id).current_version_id
    v2 = DocumentVersion(document_id=doc.id, major=2, minor=0, prev_version_id=first,
                         status=VERSION_SUBMITTED, change_summary="Sửa lớn",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(v2)
    db.add(ApprovalInstance(entity="document", entity_id=doc.id, flow_id=1, flow_version=1,
                            status=INSTANCE_APPROVED, current_seq=1,
                            created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()

    assert doc.status == STATUS_EFFECTIVE
    assert service.is_pending_issue(db, doc) is True
    assert serializer.serialize(db, doc)["is_pending_issue"] is True


def test_ban_nhap_binh_thuong_khong_phai_cho_ban_hanh(db, seed, kinds):
    doc = _draft(db, seed, kinds["qc"])
    assert service.is_pending_issue(db, doc) is False
