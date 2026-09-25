"""VĂN BẢN DUYỆT MỘT BƯỚC phải hiện ở «Chờ tôi duyệt» (25/09/2026).

Lỗi bắt khi test UI: văn bản không khớp luồng nào thì duyệt một bước kiểu cũ —
không sinh việc trong bộ máy duyệt — nên người có quyền duyệt không thấy nó ở
màn «Chờ tôi duyệt», phải tự lần trong danh sách Văn bản.

Danh sách phải khớp ĐÚNG luật của nút «Duyệt và ban hành»: thừa một dòng là
hứa một nút bấm bị chặn; thiếu một dòng là việc treo không ai thấy.
"""
from app.core.auth import get_perm_profile
from app.modules.approval.flow_model import ApprovalSwitch
from app.modules.approval.instance_model import INSTANCE_RUNNING, ApprovalInstance
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, service
from app.modules.document.legacy_pending_approval import list_legacy_pending
from app.modules.document.schema import AccessGrant, DocumentCreate
from app.modules.user.model import User

ACTOR = 1


def _doc(db, seed, code, submit=True):
    doc_type = DocType(code=code, name=f"Loại {code}", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title=f"Văn bản {code}",
        content_html="<p>Nội dung</p>",
    ), ACTOR)
    return service.submit(db, doc, ACTOR) if submit else doc


def _approver(db, seed, cap_quyen):
    user = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "document", scope="all", read=True, approve=True)
    return user


def _ids(db, user):
    return [row["document_id"] for row in list_legacy_pending(db, user, get_perm_profile(db, user))]


def test_submitted_document_without_a_flow_shows_up(db, seed, cap_quyen):
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LP1")
    rows = list_legacy_pending(db, user, get_perm_profile(db, user))
    assert [row["document_id"] for row in rows] == [doc.id]
    assert rows[0]["version_label"] == "1.0"


def test_draft_is_not_waiting_for_anyone(db, seed, cap_quyen):
    user = _approver(db, seed, cap_quyen)
    _doc(db, seed, "LP2", submit=False)
    assert _ids(db, user) == []


def test_a_named_deny_hides_it_even_from_an_approver(db, seed, cap_quyen):
    """Ca test UI: Trưởng bộ phận có quyền duyệt nhưng bị chặn đích danh."""
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LP3")
    access_service.grant(db, doc, AccessGrant(subject_kind=1, subject_id=seed.emp_nstm_id,
                                              effect=2), ACTOR)
    db.commit()
    assert doc.id not in _ids(db, user)


def test_document_already_in_the_multi_step_engine_is_not_listed_twice(db, seed, cap_quyen):
    """Có phiên nhiều bước đang mở thì việc nằm ở bộ máy — nút một bước bị
    `block_legacy_path` chặn, liệt kê ở đây là hứa suông và ra hai dòng."""
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LP4")
    db.add(ApprovalSwitch(entity="document", is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalInstance(entity="document", entity_id=doc.id, flow_id=1,
                            status=INSTANCE_RUNNING, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    assert doc.id not in _ids(db, user)


def test_approver_outside_the_role_scope_does_not_see_it(db, seed, cap_quyen):
    user = db.get(User, seed.u_nstm_id)
    cap_quyen(user.id, "document", scope="own", read=True, approve=True)
    _doc(db, seed, "LP5")
    assert _ids(db, user) == []


# ── ĐÃ DUYỆT (25/09/2026) ────────────────────────────────────────────────────
#  Duyệt một bước xong thì văn bản BIẾN khỏi màn «Chờ tôi duyệt» vì sổ của bộ
#  máy duyệt không có dòng nào. Nhóm «Đã duyệt» đọc nhật ký văn bản thay vào.

from datetime import datetime, timedelta  # noqa: E402

from app.core.audit import record  # noqa: E402
from app.modules.audit.model import AuditLog  # noqa: E402
from app.modules.document.legacy_pending_approval import list_legacy_decisions  # noqa: E402


def _decided(db, user, days=30):
    return list_legacy_decisions(db, user, days)


def test_my_single_step_approval_is_listed_as_approved(db, seed, cap_quyen):
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LD1")
    record(db, user.id, "document", doc.id, "approve", "Ban hành 01/2026/LD1")
    rows = _decided(db, user)
    assert [(row["document_id"], row["action"], row["action_label"]) for row in rows] == [
        (doc.id, 2, "Duyệt")]


def test_a_return_is_listed_with_its_reason(db, seed, cap_quyen):
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LD2")
    record(db, user.id, "document", doc.id, "update", "Trả về: Thiếu chữ ký phụ lục")
    [row] = _decided(db, user)
    assert (row["action"], row["action_label"], row["comment"]) == (4, "Trả lại", "Thiếu chữ ký phụ lục")


def test_ordinary_edits_and_other_peoples_approvals_are_not_mine(db, seed, cap_quyen):
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LD3")
    record(db, user.id, "document", doc.id, "update", "Gửi duyệt")
    record(db, ACTOR, "document", doc.id, "approve", "Ban hành bởi người khác")
    assert _decided(db, user) == []


def test_issuing_after_a_multi_step_flow_is_not_counted_twice(db, seed, cap_quyen):
    """Người soạn bấm ban hành sau luồng nhiều bước cũng ghi «approve» — các
    chặng đã nằm trong sổ bộ máy, liệt kê thêm ở đây là một văn bản hai dòng."""
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LD4")
    db.add(ApprovalInstance(entity="document", entity_id=doc.id, flow_id=1, status=3,
                            created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    record(db, user.id, "document", doc.id, "approve", "Ban hành")
    assert _decided(db, user) == []


def test_decisions_older_than_the_window_drop_out(db, seed, cap_quyen):
    user = _approver(db, seed, cap_quyen)
    doc = _doc(db, seed, "LD5")
    record(db, user.id, "document", doc.id, "approve", "Ban hành")
    log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    log.created_at = datetime.now() - timedelta(days=31)
    db.commit()
    assert _decided(db, user, days=30) == []
    assert len(_decided(db, user, days=60)) == 1
