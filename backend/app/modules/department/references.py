"""ai-CR-190 — chỗ tham chiếu tới PHÒNG BAN cho sổ `core/reference_guard`.

`tab_department_company` là bảng con (FK CASCADE) nên không khai — xóa phòng là đi theo. `tab_user_scope` lưu
`value` = TÊN phòng dạng chuỗi, không đếm được bằng khóa số — bỏ qua (doc/erp/20 §4). `created_by` không tính.
Tệp này được `department/service.py` import lúc khởi động.
"""
from app.core import reference_guard as rg
from app.modules.category_assignee.model import CategoryAssignee
from app.modules.doc_catalog.folder_access_model import DocFolderAccess
from app.modules.document.access_model import SUBJECT_DEPARTMENT, DocumentAccess
from app.modules.document.model import Document
from app.modules.document.recipient_model import RECIPIENT_DEPARTMENT, DocumentRecipient
from app.modules.document.request_model import DocumentRequest
from app.modules.document.scope_model import DocumentScope
from app.modules.dossier.model import Dossier
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.forum.model import ForumPost
from app.modules.labor_contract.model import LaborContract
from app.modules.leave.request_model import LeaveRequest
from app.modules.meeting_room.model import RoomBooking
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.report_access.model import ReportAccess
from app.modules.seal_request.model import SealRequest
from app.modules.survey_request.model import SurveyRequest
from app.modules.vehicle_booking.model import VehicleBooking
from app.modules.work.model import WorkGroupMember, WorkListMember

from .model import Department

ENTITY = "department"


def _subject_department(model):
    return [model.subject_kind == SUBJECT_DEPARTMENT]


rg.register(ENTITY, "Phòng ban", [
    #  Tổ chức
    rg.Reference(Department, "parent", "phòng ban con"),
    rg.Reference(Employee, "department_id", "nhân sự"),
    rg.Reference(EmployeeDepartment, "department_id", "kiêm nhiệm của nhân sự"),
    rg.Reference(JobPosition, "department_id", "chức vụ"),
    rg.Reference(EmployeeWorkHistory, "department_id", "quá trình công tác"),
    rg.Reference(LaborContract, "department_id", "hợp đồng lao động"),
    rg.Reference(CategoryAssignee, "department_id", "phân công nhóm hàng"),
    #  Thu mua
    rg.Reference(PurchaseRequest, "department_id", "yêu cầu mua hàng"),
    rg.Reference(PurchaseRequest, "handler_dept_id", "yêu cầu mua hàng (phòng xử lý)"),
    rg.Reference(SurveyRequest, "department_id", "yêu cầu báo giá"),
    rg.Reference(SurveyRequest, "handler_dept_id", "yêu cầu báo giá (phòng xử lý)"),
    rg.Reference(PurchaseOrder, "department_id", "đơn mua hàng"),
    rg.Reference(PurchaseOrder, "handler_dept_id", "đơn mua hàng (phòng xử lý)"),
    rg.Reference(Payable, "department_id", "công nợ"),
    rg.Reference(PaymentRequest, "department_id", "yêu cầu thanh toán"),
    #  Văn thư
    rg.Reference(Document, "department_id", "văn bản"),
    rg.Reference(DocumentRequest, "department_id", "yêu cầu văn bản"),
    rg.Reference(DocumentScope, "department_id", "phạm vi áp dụng văn bản"),
    rg.Reference(DocumentRecipient, "recipient_id", "nơi nhận văn bản",
                 extra=lambda m: [m.recipient_kind == RECIPIENT_DEPARTMENT]),
    rg.Reference(DocumentAccess, "subject_id", "quyền xem văn bản", extra=_subject_department),
    rg.Reference(DocFolderAccess, "subject_id", "quyền thư mục văn bản", extra=_subject_department),
    rg.Reference(ReportAccess, "subject_id", "quyền xem báo cáo", extra=_subject_department),
    rg.Reference(Dossier, "department_id", "hồ sơ"),
    rg.Reference(SealRequest, "department_id", "phiếu đóng dấu"),
    #  Hành chính
    rg.Reference(LeaveRequest, "department_id", "đơn nghỉ phép"),
    rg.Reference(RoomBooking, "department_id", "lịch đặt phòng họp"),
    rg.Reference(VehicleBooking, "department_id", "phiếu đặt xe"),
    rg.Reference(ForumPost, "dept_id", "bài diễn đàn"),
    #  Công việc
    rg.Reference(WorkGroupMember, "department_id", "thành viên nhóm công việc"),
    rg.Reference(WorkListMember, "department_id", "thành viên bảng công việc"),
])
