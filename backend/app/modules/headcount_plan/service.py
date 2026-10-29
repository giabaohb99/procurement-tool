"""Luật nghiệp vụ kế hoạch nhân sự: pháp nhân / phòng phải có thật, bộ khóa (năm, loại kỳ, kỳ, pháp nhân, phòng) duy
nhất, CHẶN ghi tiền khi người ghi không đọc được HĐLĐ của pháp nhân đó, văn bản liên kết chỉ gắn được khi đọc được."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.department.model import Department
from app.modules.document.access_service import can as can_read_document
from app.modules.document.model import Document

from .model import HeadcountPlan, HeadcountPlanDocument
from .serializer import can_see_payroll

PAYROLL_DENIED = "Cần quyền xem hợp đồng lao động để khai chi phí nhân sự kế hoạch"
STRUCTURE_DENIED = "Cần quyền xem lương của pháp nhân này để sửa khoản chi phí"
DOCUMENT_DENIED = "Không gắn được văn bản này"
APPROVER_INVALID = "Người duyệt không hợp lệ"
CONFLICT_MESSAGE = "Kế hoạch vừa được người khác sửa, tải lại trang"
DUPLICATE_MESSAGE = "Đã có kế hoạch cho kỳ, pháp nhân và phòng này"


def check_refs(db: Session, company_id: int, department_id: int) -> None:
    """Pháp nhân phải có; phòng (khác 0) phải có thật. Sai → 422.

    KHÔNG bắt phòng «thuộc» pháp nhân: phòng ban ở DEGO dùng chung cho mọi pháp nhân —
    `Department.company_id` để 0 và bảng ánh xạ `tab_department_company` còn rỗng (dev + local,
    kiểm 28/10/2026), nên bắt buộc như bản đầu là từ chối MỌI kế hoạch theo phòng. Cặp
    (pháp nhân × phòng) có nghĩa qua hồ sơ nhân sự: số thực tế đếm người có đúng cặp đó."""
    if db.query(Company.id).filter(Company.id == company_id).first() is None:
        raise HTTPException(422, "Pháp nhân không tồn tại")
    if department_id and db.query(Department.id).filter(Department.id == department_id).first() is None:
        raise HTTPException(422, "Phòng ban không tồn tại")


def ensure_unique(db: Session, year: int, period_type: int, period_no: int, company_id: int, department_id: int,
                  exclude_id: int = 0) -> None:
    q = db.query(HeadcountPlan.id).filter(
        HeadcountPlan.year == year, HeadcountPlan.period_type == period_type, HeadcountPlan.period_no == period_no,
        HeadcountPlan.company_id == company_id, HeadcountPlan.department_id == department_id)
    if exclude_id:
        q = q.filter(HeadcountPlan.id != exclude_id)
    if q.first() is not None:
        raise HTTPException(400, DUPLICATE_MESSAGE)


def check_approver(db: Session, user, profile: dict, approver_employee_id: int) -> None:
    """Người duyệt (0 = chưa chọn) phải tồn tại và nằm trong phạm vi `employee.read` của người ghi, không thì 422."""
    if not approver_employee_id:
        return
    q = apply_scope(db.query(Employee.id).filter(Employee.id == approver_employee_id), Employee, "employee", user, profile)
    if q.first() is None:
        raise HTTPException(422, APPROVER_INVALID)


def deny_blind_money(profile: dict, company_id: int, department_id: int, *amounts) -> None:
    """Khai tiền KHÁC 0 cho pháp nhân mà người ghi không đọc được HĐLĐ của nó → 403. 0 / None không bị chặn:
    biểu mẫu của người không thấy tiền luôn gửi lại ô trống, và bên gọi GIỮ NGUYÊN số đang lưu cho các ô đó."""
    if any(a for a in amounts) and not can_see_payroll(profile, company_id, department_id):
        raise HTTPException(403, PAYROLL_DENIED)


def link_documents(db: Session, plan_id: int, document_ids: list[int], user, profile: dict, actor_id: int) -> None:
    """Thay tập văn bản liên kết. Văn bản MỚI gắn phải tồn tại và người lưu phải ĐỌC được (không thì 403); văn bản
    đã gắn từ trước (có thể người lưu không đọc được) được giữ nếu còn trong danh sách gửi lên."""
    wanted = list(dict.fromkeys(document_ids))
    current = {d.document_id: d for d in db.query(HeadcountPlanDocument).filter(
        HeadcountPlanDocument.plan_id == plan_id).all()}
    for doc_id in wanted:
        if doc_id in current:
            continue
        doc = db.get(Document, doc_id)
        #  Không tồn tại / đã xóa / không đọc được cùng MỘT câu 403 — không cho dò xem số văn bản nào có thật
        if doc is None or doc.is_deleted or not can_read_document(db, doc, user, profile, "read"):
            raise HTTPException(403, DOCUMENT_DENIED)
        db.add(HeadcountPlanDocument(plan_id=plan_id, document_id=doc_id, created_by=actor_id, updated_by=actor_id))
    for doc_id, row in current.items():
        if doc_id not in wanted:
            db.delete(row)

