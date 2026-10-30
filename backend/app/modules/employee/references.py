"""ai-CR-190 — chỗ tham chiếu tới NHÂN SỰ cho sổ `core/reference_guard`.

KHÔNG khai ở đây (cố ý):
- Bảng con của chính hồ sơ (liên hệ, gia đình, kiêm nhiệm, quá trình công tác, HĐLĐ nháp/đã hủy) — `delete_employee`
  dọn kèm; HĐLĐ đã ký / đã chấm dứt vẫn chặn 409 ở `labor_contract.ensure_employee_deletable` (giữ nguyên, chạy trước).
- `tab_user.employee_id`: tài khoản gắn hồ sơ KHÔNG tính là tham chiếu — `delete_user` đã chặn "tài khoản còn hồ sơ thì
  không xóa", nếu chiều này cũng chặn thì không bao giờ xóa được cả hai (bế tắc). Giữ lối CR-023: xóa hồ sơ → tự khóa
  + gỡ tài khoản kèm theo.
- `created_by` / `updated_by` / `actor_employee_id` (lịch sử duyệt) / `creator_employee_id`: nhật ký.
Tệp này được `employee/service.py` import lúc khởi động.
"""
from app.core import reference_guard as rg
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.flow_model import APPROVER_EMPLOYEE, ApprovalNode
from app.modules.approval.instance_model import ApprovalInstance, ApprovalTask
from app.modules.catalog.model import Brand
from app.modules.category_assignee.model import CategoryAssignee
from app.modules.coffee_point.model import CoffeeMember
from app.modules.company.model import Company
from app.modules.department.model import Department, DepartmentCompany
from app.modules.doc_catalog.book_model import DocumentBookMember
from app.modules.doc_catalog.folder_access_model import DocFolderAccess
from app.modules.document.access_model import SUBJECT_EMPLOYEE, DocumentAccess
from app.modules.document.incoming_register_model import IncomingRegister
from app.modules.document.model import Document
from app.modules.document.recipient_model import RECIPIENT_EMPLOYEE, DocumentRecipient
from app.modules.document.request_model import DocumentRequest
from app.modules.document.scope_model import DocumentScope
from app.modules.document.signature_model import DocumentSignature
from app.modules.dossier.model import Dossier
from app.modules.dossier.progress_model import DossierProgress
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.request_model import LeaveHandover, LeaveRequest
from app.modules.meeting_room.model import RoomBooking, RoomBookingAttendee
from app.modules.notification.mailbox_model import MailboxMember
from app.modules.payment_request.model import PaymentRequest
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.report_access.model import ReportAccess
from app.modules.seal_clerk.model import SealClerk
from app.modules.seal_request.model import SealRequest
from app.modules.survey_request.model import SurveyRequest
from app.modules.survey_request.report_model import SurveyReportDoc
from app.modules.ticket.model import Ticket
from app.modules.vehicle_booking.model import VehicleBooking
from app.modules.work.model import WorkGroupMember, WorkListMember
from app.modules.work.task_model import WorkTaskAssignee

from .model import Employee

ENTITY = "employee"


def _subject_employee(model):
    return [model.subject_kind == SUBJECT_EMPLOYEE]


rg.register(ENTITY, "Nhân sự", [
    #  Tổ chức
    rg.Reference(Employee, "manager_id", "nhân sự do người này quản lý"),
    rg.Reference(Department, "manager_id", "phòng ban làm trưởng bộ phận"),
    rg.Reference(DepartmentCompany, "manager_employee_id", "phòng ban tại pháp nhân làm trưởng bộ phận"),
    rg.Reference(Company, "legal_representative_id", "công ty làm người đại diện pháp luật"),
    rg.Reference(CategoryAssignee, "primary_employee_id", "phân công nhóm hàng (chính)"),
    rg.Reference(CategoryAssignee, "backup_employee_id", "phân công nhóm hàng (dự phòng)"),
    rg.Reference(Brand, "manager_id", "thương hiệu phụ trách"),
    #  Bộ máy duyệt
    rg.Reference(ApprovalNode, "approver_ref", "chặng duyệt đích danh",
                 extra=lambda m: [m.approver_kind == APPROVER_EMPLOYEE]),
    rg.Reference(ApprovalNode, "fallback_employee_id", "chặng duyệt (người dự phòng)"),
    rg.Reference(ApprovalInstance, "started_by_employee_id", "phiếu duyệt đã trình"),
    rg.Reference(ApprovalTask, "assignee_employee_id", "việc duyệt được giao"),
    rg.Reference(Delegation, "from_employee_id", "ủy quyền duyệt (người ủy quyền)"),
    rg.Reference(Delegation, "to_employee_id", "ủy quyền duyệt (người nhận)"),
    #  Thu mua
    rg.Reference(PurchaseRequest, "requester_id", "yêu cầu mua hàng (người yêu cầu)"),
    rg.Reference(PurchaseRequest, "head_of_dept_id", "yêu cầu mua hàng (trưởng bộ phận)"),
    rg.Reference(PurchaseRequest, "approver_employee_id", "yêu cầu mua hàng (người duyệt)"),
    rg.Reference(PurchaseRequest, "assignee_id", "yêu cầu mua hàng (người phụ trách)"),
    rg.Reference(SurveyRequest, "requester_id", "yêu cầu báo giá (người yêu cầu)"),
    rg.Reference(SurveyRequest, "head_of_dept_id", "yêu cầu báo giá (trưởng bộ phận)"),
    rg.Reference(SurveyRequest, "approver_employee_id", "yêu cầu báo giá (người duyệt)"),
    rg.Reference(SurveyReportDoc, "assignee_id", "báo cáo thực hiện (người phụ trách)"),
    rg.Reference(PurchaseOrder, "approver_employee_id", "đơn mua hàng (người duyệt)"),
    rg.Reference(PaymentRequest, "head_of_dept_id", "yêu cầu thanh toán (trưởng bộ phận)"),
    #  Văn thư
    rg.Reference(Document, "owner_employee_id", "văn bản (người chủ trì)"),
    rg.Reference(Document, "drafter_employee_id", "văn bản (người soạn)"),
    rg.Reference(Document, "signer_employee_id", "văn bản (người ký)"),
    rg.Reference(DocumentRequest, "requester_employee_id", "yêu cầu văn bản"),
    rg.Reference(DocumentScope, "employee_id", "phạm vi áp dụng văn bản"),
    rg.Reference(DocumentRecipient, "recipient_id", "nơi nhận văn bản",
                 extra=lambda m: [m.recipient_kind == RECIPIENT_EMPLOYEE]),
    rg.Reference(DocumentSignature, "signer_employee_id", "chữ ký văn bản"),
    rg.Reference(IncomingRegister, "assigned_employee_id", "văn bản đến được giao"),
    rg.Reference(DocumentBookMember, "employee_id", "thành viên sổ văn bản"),
    rg.Reference(DocumentAccess, "subject_id", "quyền xem văn bản", extra=_subject_employee),
    rg.Reference(DocFolderAccess, "subject_id", "quyền thư mục văn bản", extra=_subject_employee),
    rg.Reference(ReportAccess, "subject_id", "quyền xem báo cáo", extra=_subject_employee),
    rg.Reference(Dossier, "owner_employee_id", "hồ sơ (người phụ trách)"),
    rg.Reference(DossierProgress, "assignee_id", "tiến độ hồ sơ (người phụ trách)"),
    rg.Reference(SealRequest, "requester_id", "phiếu đóng dấu (người yêu cầu)"),
    rg.Reference(SealRequest, "first_approver_id", "phiếu đóng dấu (người duyệt)"),
    rg.Reference(SealClerk, "employee_id", "văn thư giữ dấu"),
    #  Hành chính – nhân sự
    rg.Reference(LeaveRequest, "employee_id", "đơn nghỉ phép"),
    rg.Reference(LeaveHandover, "employee_id", "bàn giao nghỉ phép"),
    rg.Reference(LeaveBalance, "employee_id", "quỹ phép"),
    rg.Reference(RoomBooking, "requester_employee_id", "lịch đặt phòng họp"),
    rg.Reference(RoomBookingAttendee, "employee_id", "người tham dự họp"),
    rg.Reference(VehicleBooking, "requester_id", "phiếu đặt xe (người yêu cầu)"),
    rg.Reference(VehicleBooking, "first_approver_id", "phiếu đặt xe (người duyệt)"),
    rg.Reference(Ticket, "requester_id", "phiếu hỗ trợ"),
    rg.Reference(MailboxMember, "employee_id", "thành viên hộp thư"),
    rg.Reference(CoffeeMember, "employee_id", "thành viên điểm cà phê"),
    #  Công việc
    rg.Reference(WorkTaskAssignee, "employee_id", "thẻ công việc được giao"),
    rg.Reference(WorkGroupMember, "employee_id", "thành viên nhóm công việc"),
    rg.Reference(WorkListMember, "employee_id", "thành viên bảng công việc"),
])
