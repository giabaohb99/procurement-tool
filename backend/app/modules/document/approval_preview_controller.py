"""API XEM TRƯỚC «NGƯỜI DUYỆT DỰ KIẾN» (phase 01, duoc-CR-473).

Tệp RIÊNG, KHÔNG đụng `document/controller.py` — controller đó đang được một
agent khác sửa song song trong cùng đợt việc này.

Chỉ ĐỌC: không mở phiên duyệt, không ghi audit, không commit. Xem
`app/modules/approval/preview_service.py` cho phần tính toán chính; ở đây chỉ
có lớp API (gác quyền, kiểm `DocType.needs_approval`, dựng `subject`).

⚠️ Route TĨNH dưới `/api/documents/...` — phải đăng ký TRƯỚC `document_router`
trong `main.py` (router đó có `/{document_id}` khớp mọi chuỗi), cùng luật với
`document_link_router` / `document_scope_router` / …
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import get_scoped

from . import approval_bridge
from .service import doc_type_or_400
from ..approval.preview_service import preview_flow

router = APIRouter(prefix="/api/documents", tags=["document"])


class PreviewApprovalIn(BaseModel):
    """Đúng bộ trường `approval_bridge.entity_context()`, trừ `id` — văn bản
    CHƯA tồn tại lúc xem trước nên không có id nào để khớp điều kiện riêng
    từng bản (`ApprovalFlow.condition` kiểu `id in [...]`).

    `doc_type_id` / `company_id` bắt buộc dương: đây là hai ô luôn phải chọn
    trước khi màn tạo có gì để xem trước (frontend chỉ gọi API khi đã có cả
    hai — xem `use-document-approval-preview.ts`). Phần còn lại để trống được,
    `0` là "chưa chọn" — cùng quy ước sentinel với phần còn lại của hệ thống.
    """

    doc_type_id: int = Field(gt=0)
    company_id: int = Field(gt=0)
    department_id: int = 0
    secrecy_level: int = 0
    urgency: int = 0
    owner_employee_id: int = 0
    drafter_employee_id: int = 0
    signer_employee_id: int = 0
    #  ≠ 0 → xem trước cho BẢN CLONE (pháp nhân con): chỉ xét luồng RIÊNG của
    #  đúng pháp nhân đó, không rơi về luồng dùng chung của bản gốc — cùng chốt
    #  với `approval_bridge.submit_for_approval` / `ensure_dedicated_flow`.
    source_document_id: int = 0


def _subject(data: PreviewApprovalIn) -> dict:
    return {
        "doc_type_id": data.doc_type_id,
        "company_id": data.company_id,
        "department_id": data.department_id,
        "secrecy_level": data.secrecy_level,
        "urgency": data.urgency,
        "owner_employee_id": data.owner_employee_id,
        "drafter_employee_id": data.drafter_employee_id,
        "signer_employee_id": data.signer_employee_id,
    }


def _submitter_employee_id(user, data: PreviewApprovalIn) -> int | None:
    """Người nộp SẼ LÀ ai — cùng thứ tự ưu tiên với `approval_bridge.submit_for_approval`:
    nhân sự của người đang bấm, lùi về người soạn/chịu trách nhiệm ghi trên phiếu
    khi tài khoản chưa gắn hồ sơ nhân sự (tài khoản hệ thống, tác vụ nền)."""
    return (getattr(user, "employee_id", 0)
            or data.drafter_employee_id
            or data.owner_employee_id
            or None)


@router.post("/approval-preview")
def preview_approval(
    data: PreviewApprovalIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "create")),
):
    """Xem trước luồng duyệt SẼ áp nếu gửi duyệt ngay bây giờ.

    Ba trạng thái (`mode`): `"none"` — loại văn bản không cần duyệt
    (`DocType.needs_approval = false`, hỏi TRƯỚC khi gọi `preview_service` vì
    bộ máy duyệt không biết khái niệm "loại văn bản"); `"flow"` — luồng nhiều
    chặng; `"legacy"` — không luồng nào khớp hoặc bộ máy đang tắt, văn bản sẽ
    duyệt một bước kiểu cũ.

    ⚠️ M3 (rà soát 23/09/2026): `company_id`/`department_id`/ba id nhân sự do
    NGƯỜI GỌI tự gõ — trước đây không kiểm gì cả, ai có `document.create` (hầu
    hết mọi người soạn văn bản) cũng dò được tên người duyệt/quản lý trực tiếp
    (APPROVER_LEVEL_UP) của BẤT KỲ nhân viên/pháp nhân nào trong hệ, ngoài
    phạm vi thật của họ. Chặn `company_id` ngoài phạm vi `document.create`, và
    `department_id`/nhân sự ngoài phạm vi đọc tương ứng — 400, không 403 (cùng
    câu với thư mục/nhân sự không tồn tại, không cho dò "có tồn tại không").

    Kiểm phạm vi CHẠY SAU nhánh `"none"` — loại không cần duyệt trả về một câu
    TRẢ LỜI CHUNG (không tên người/phòng nào), không có gì để lộ, nên không
    cần đọc hồ sơ nhân sự/phòng ban của người gọi cho trường hợp đó.
    """
    doc_type = doc_type_or_400(db, data.doc_type_id)
    if not doc_type.needs_approval:
        return success({"mode": "none", "engine_enabled": False,
                        "flow_name": "", "steps": [], "cc": []})

    from app.modules.department.model import Department
    from app.modules.doc_catalog.folder_access_service import company_reach
    from app.modules.employee.model import Employee

    profile = get_perm_profile(db, user)
    reach = company_reach(profile, "document", "create")
    if reach is not None and data.company_id not in reach:
        raise HTTPException(
            400, "Không tìm thấy pháp nhân này, hoặc bạn không có quyền tạo văn bản cho pháp nhân đó")

    if (data.department_id
            and get_scoped(db, Department, "department", data.department_id, user, profile, "read")
            is None):
        raise HTTPException(400, "Không tìm thấy phòng ban này, hoặc bạn không có quyền xem")

    for emp_id in {data.owner_employee_id, data.drafter_employee_id, data.signer_employee_id}:
        if emp_id and get_scoped(db, Employee, "employee", emp_id, user, profile, "read") is None:
            raise HTTPException(400, "Không tìm thấy nhân sự này, hoặc bạn không có quyền xem")

    if data.source_document_id:
        from . import access_service
        from .model import Document

        source_doc = db.get(Document, data.source_document_id)
        if source_doc is None or not access_service.can(db, source_doc, user, profile, "read"):
            raise HTTPException(400, "Không tìm thấy văn bản gốc này, hoặc bạn không có quyền xem")

    result = preview_flow(
        db, approval_bridge.ENTITY, _subject(data),
        _submitter_employee_id(user, data),
        company_flow_only=bool(data.source_document_id),
    )
    return success(result)
