"""DUYỆT MỘT BƯỚC trong màn «Chờ tôi duyệt» — việc CHỜ và việc ĐÃ LÀM (25/09/2026).

Màn «Chờ tôi duyệt» đọc việc của BỘ MÁY DUYỆT (`/api/approvals/my-tasks`). Văn
bản không khớp luồng nào thì chạy đường DUYỆT MỘT BƯỚC kiểu cũ — không sinh
phiên, không sinh việc — nên người có quyền duyệt không bao giờ thấy nó ở màn
đó, phải tự lần trong danh sách Văn bản (lỗi bắt khi test UI 25/09/2026).

Luật "ai duyệt được" ĐÚNG Y nút «Duyệt và ban hành» ở `controller.approve_document`:
  1. vai trò có `document.approve`            → `require(...)` của route;
  2. đọc được văn bản                          → `access_service.visible_condition`
     (phạm vi vai trò + chia đích danh − CHẶN đích danh);
  3. có phiên bản đang ở `VERSION_SUBMITTED`   → gồm cả bản sửa đổi 2.0 của văn
     bản đang hiệu lực (khi đó `Document.status` vẫn là «Có hiệu lực»);
  4. KHÔNG có phiên duyệt nhiều bước còn mở   → cùng điều kiện `block_legacy_path`,
     không thì văn bản hiện HAI dòng: một ở đây, một ở việc của bộ máy.
Lệch một điều là danh sách hứa một nút bấm mà màn chi tiết lại chặn.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, exists
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import access_service
from .approval_bridge import ENTITY
from .model import STATUS_LABELS, Document
from .version_model import VERSION_SUBMITTED, DocumentVersion

router = APIRouter(prefix="/api/document-approvals", tags=["document"])

#  Trần an toàn — hộp chờ duyệt của một người không bao giờ tới mức này; chạm
#  trần thì màn hình vẫn đúng thứ tự (cũ nhất lên đầu), chỉ thiếu đuôi.
_LIMIT = 200


def list_legacy_pending(db: Session, user, profile: dict) -> list[dict]:
    from app.modules.approval.instance_model import INSTANCE_OPEN_STATUSES, ApprovalInstance

    running = exists().where(and_(
        ApprovalInstance.entity == ENTITY,
        ApprovalInstance.entity_id == Document.id,
        ApprovalInstance.status.in_(INSTANCE_OPEN_STATUSES),
    ))
    query = (db.query(Document, DocumentVersion)
             .join(DocumentVersion, and_(DocumentVersion.document_id == Document.id,
                                         DocumentVersion.status == VERSION_SUBMITTED))
             .filter(~running))
    visible = access_service.visible_condition(user, profile)
    if visible is not None:
        query = query.filter(visible)
    rows = query.order_by(DocumentVersion.updated_at.asc()).limit(_LIMIT).all()
    names = _submitter_names(db, {version.updated_by for _, version in rows})
    return [{
        "document_id": doc.id,
        "code": doc.issue_number or doc.doc_code or "",
        "title": doc.title,
        "version_label": f"{version.major}.{version.minor}",
        "submitted_by_name": names.get(version.updated_by, ""),
        "submitted_at": version.updated_at,
    } for doc, version in rows]


def _submitter_names(db: Session, user_ids: set[int | None]) -> dict[int, str]:
    """Tên người trình — hai truy vấn cho cả trang, không truy vấn trong vòng lặp."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    pairs = (db.query(User.id, Employee.full_name)
             .outerjoin(Employee, Employee.id == User.employee_id)
             .filter(User.id.in_(ids)).all())
    return {uid: name or "" for uid, name in pairs}


@router.get("/legacy-pending")
def legacy_pending(db: Session = Depends(get_db), user=Depends(require("document", "approve"))):
    return success(list_legacy_pending(db, user, get_perm_profile(db, user)))


# ── ĐÃ DUYỆT ────────────────────────────────────────────────────────────────
#  Nhóm «Đã duyệt» của màn đọc `/api/approvals/my-history` — sổ của bộ máy
#  duyệt. Duyệt một bước không đi qua bộ máy nên duyệt xong là văn bản BIẾN khỏi
#  màn, như thể chưa ký gì. Nguồn thật của lượt bấm đó là nhật ký văn bản mà
#  `controller.approve_document` / `reject_document` ghi ngay lúc bấm.
#
#  ⚠️ Nhật ký «approve» còn được ghi khi NGƯỜI SOẠN bấm ban hành văn bản đã
#  qua luồng nhiều bước (nhịp «Chờ ban hành»). Lượt đó không phải một quyết
#  định duyệt, và các chặng của luồng đã có sẵn trong sổ bộ máy — nên loại MỌI
#  văn bản từng có phiên duyệt, không thì cùng một văn bản hiện hai dòng.

#  Mã quyết định dùng lại của bộ máy duyệt để giao diện tô cùng một màu huy hiệu.
_ACTION_APPROVE, _ACTION_RETURN = 2, 4
#  `reject_document` ghi «Trả về: <lý do>» dưới action `update` (bảng nhật ký
#  chỉ có create/update/delete/approve). Tiền tố này là thứ duy nhất phân biệt.
_RETURN_PREFIX = "Trả về: "


def list_legacy_decisions(db: Session, user, days: int) -> list[dict]:
    from app.modules.approval.instance_model import ApprovalInstance
    from app.modules.audit.model import AuditLog
    from sqlalchemy import or_

    ever_in_engine = exists().where(and_(ApprovalInstance.entity == ENTITY,
                                         ApprovalInstance.entity_id == AuditLog.entity_id))
    rows = (db.query(AuditLog, Document)
            .join(Document, Document.id == AuditLog.entity_id)
            .filter(AuditLog.entity == ENTITY,
                    AuditLog.created_by == user.id,
                    AuditLog.created_at >= datetime.now() - timedelta(days=days),
                    or_(AuditLog.action == "approve",
                        and_(AuditLog.action == "update",
                             AuditLog.message.like(f"{_RETURN_PREFIX}%"))),
                    ~ever_in_engine)
            .order_by(AuditLog.created_at.desc())
            .limit(_LIMIT).all())
    out = []
    for log, doc in rows:
        returned = log.action != "approve"
        out.append({
            "id": log.id,
            "document_id": doc.id,
            "code": doc.issue_number or doc.doc_code or "",
            "title": doc.title,
            "action": _ACTION_RETURN if returned else _ACTION_APPROVE,
            "action_label": "Trả lại" if returned else "Duyệt",
            "comment": log.message[len(_RETURN_PREFIX):] if returned else "",
            "decided_at": log.created_at,
            #  Trạng thái HIỆN TẠI của văn bản — «tôi đã duyệt» khác «giờ nó ra sao».
            "status_label": STATUS_LABELS.get(doc.status, ""),
        })
    return out


@router.get("/legacy-decisions")
def legacy_decisions(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user=Depends(require("document", "approve")),
):
    return success(list_legacy_decisions(db, user, days))
