"""ai-CR-190 — chỗ tham chiếu tới VAI TRÒ cho sổ `core/reference_guard`.

Vai trò không có `is_active` (không thêm cột — tránh migration): còn người giữ / còn được gán quyền thì chặn, hết thì
xóa. `tab_permission` và `tab_user_scope` là dữ liệu của chính vai trò — `delete_role` dọn kèm, không khai.
Tệp này được `role/service.py` import lúc khởi động.
"""
from app.core import reference_guard as rg
from app.modules.approval.flow_model import APPROVER_ROLE, ApprovalNode
from app.modules.doc_catalog.folder_access_model import DocFolderAccess
from app.modules.employee.position_model import JobPositionRole
from app.modules.document.access_model import SUBJECT_ROLE, DocumentAccess
from app.modules.report_access.model import ReportAccess
from app.modules.user.model import UserRole

ENTITY = "role"


def _subject_role(model):
    return [model.subject_kind == SUBJECT_ROLE]


rg.register(ENTITY, "Vai trò", [
    rg.Reference(UserRole, "role_id", "tài khoản"),
    #  duoc-CR-653 (H3): vai trò còn nằm trong gói quyền mặc định của chức vụ thì không xóa — gỡ khỏi gói trước.
    rg.Reference(JobPositionRole, "role_id", "quyền mặc định của chức vụ"),
    #  Chặng duyệt «theo vai trò» lưu MÃ vai trò (chuỗi) ở `approver_ref`.
    rg.Reference(ApprovalNode, "approver_ref", "chặng duyệt theo vai trò", key_attr="code",
                 extra=lambda m: [m.approver_kind == APPROVER_ROLE]),
    rg.Reference(DocumentAccess, "subject_id", "quyền xem văn bản", extra=_subject_role),
    rg.Reference(DocFolderAccess, "subject_id", "quyền thư mục văn bản", extra=_subject_role),
    rg.Reference(ReportAccess, "subject_id", "quyền xem báo cáo", extra=_subject_role),
])
