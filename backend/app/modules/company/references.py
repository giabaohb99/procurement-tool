"""ai-CR-190 — chỗ tham chiếu tới CÔNG TY (pháp nhân) cho sổ `core/reference_guard`.

Còn dòng nào trỏ tới công ty thì không xóa, chỉ ngưng dùng (`is_active`). `created_by` / `updated_by` là nhật ký,
KHÔNG tính. `tab_user_scope` lưu `value` dạng chuỗi (tên phòng / id công ty) nên không đếm được bằng khóa số — bỏ qua,
ghi ở doc/erp/20 §4. Bảng con của khối khác (thành viên nhóm việc, dòng phiếu…) không khai lại: cha đã đếm.
Tệp này được `company/service.py` import lúc khởi động — không nạp qua `core/all_models.py`.
"""
from app.core import reference_guard as rg
from app.modules.approval.flow_model import ApprovalFlow
from app.modules.coffee_point.model import CoffeeMember, CoffeePolicy
from app.modules.contract.model import Contract
from app.modules.department.model import Department, DepartmentCompany
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.folder_model import DocFolder
from app.modules.document.access_model import SUBJECT_COMPANY, DocumentAccess
from app.modules.document.clone_plan_model import DocumentClonePlan
from app.modules.document.incoming_register_model import IncomingRegister
from app.modules.document.model import Document
from app.modules.document.recipient_model import RECIPIENT_COMPANY, DocumentRecipient
from app.modules.document.request_model import DocumentRequest
from app.modules.document.scope_model import DocumentScope
from app.modules.doc_catalog.folder_access_model import DocFolderAccess
from app.modules.dossier.model import Dossier
from app.modules.employee.model import Employee
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.forum.model import ForumPost
from app.modules.goods_receipt.model import GoodsReceipt
from app.modules.inventory.model import Inventory, InventoryMove
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.template_model import LaborContractTemplate
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import Holiday
from app.modules.leave.request_model import LeaveRequest
from app.modules.meeting_room.model import MeetingRoom, RoomBooking
from app.modules.notification.mailbox_model import Mailbox
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.report_access.model import ReportAccess
from app.modules.seal_clerk.model import SealClerk
from app.modules.seal_request.model import SealRequest, SealRequestCompany
from app.modules.survey_request.model import SurveyRequest
from app.modules.ticket.model import Ticket
from app.modules.vehicle_booking.model import VehicleBooking
from app.modules.work.model import WorkGroup, WorkList
from app.modules.work.task_model import WorkTask

from .model import Company

ENTITY = "company"


def _subject_company(model):
    return [model.subject_kind == SUBJECT_COMPANY]


rg.register(ENTITY, "Công ty", [
    #  Tổ chức
    rg.Reference(Company, "parent", "công ty con"),
    rg.Reference(Department, "company_id", "phòng ban"),
    rg.Reference(DepartmentCompany, "company_id", "phòng ban hiện diện tại pháp nhân"),
    rg.Reference(Employee, "company_id", "nhân sự"),
    rg.Reference(EmployeeWorkHistory, "company_id", "quá trình công tác"),
    rg.Reference(LaborContract, "company_id", "hợp đồng lao động"),
    rg.Reference(LaborContractTemplate, "company_id", "mẫu hợp đồng lao động"),
    rg.Reference(ApprovalFlow, "company_id", "luồng duyệt"),
    #  Thu mua
    rg.Reference(PurchaseRequest, "company_id", "yêu cầu mua hàng"),
    rg.Reference(SurveyRequest, "company_id", "yêu cầu báo giá"),
    rg.Reference(PurchaseOrder, "company_id", "đơn mua hàng"),
    rg.Reference(GoodsReceipt, "company_id", "phiếu nhập kho"),
    rg.Reference(Payable, "company_id", "công nợ"),
    rg.Reference(PaymentRequest, "company_id", "yêu cầu thanh toán"),
    rg.Reference(PurchaseHistory, "company_id", "lịch sử mua hàng"),
    rg.Reference(Contract, "company_id", "hợp đồng nhà cung cấp"),
    rg.Reference(Inventory, "company_id", "tồn kho"),
    rg.Reference(InventoryMove, "company_id", "phiếu kho"),
    #  Văn thư
    rg.Reference(Document, "company_id", "văn bản"),
    rg.Reference(DocumentRequest, "company_id", "yêu cầu văn bản"),
    rg.Reference(DocumentScope, "company_id", "phạm vi áp dụng văn bản"),
    rg.Reference(DocumentRecipient, "recipient_id", "nơi nhận văn bản",
                 extra=lambda m: [m.recipient_kind == RECIPIENT_COMPANY]),
    rg.Reference(DocumentClonePlan, "company_id", "kế hoạch sao chép văn bản"),
    rg.Reference(IncomingRegister, "company_id", "sổ văn bản đến"),
    rg.Reference(DocumentBook, "company_id", "sổ văn bản"),
    rg.Reference(DocFolder, "company_id", "thư mục văn bản"),
    rg.Reference(DocumentAccess, "subject_id", "quyền xem văn bản", extra=_subject_company),
    rg.Reference(DocFolderAccess, "subject_id", "quyền thư mục văn bản", extra=_subject_company),
    rg.Reference(ReportAccess, "subject_id", "quyền xem báo cáo", extra=_subject_company),
    rg.Reference(Dossier, "company_id", "hồ sơ"),
    rg.Reference(SealRequest, "company_id", "phiếu đóng dấu"),
    rg.Reference(SealRequestCompany, "company_id", "pháp nhân trên phiếu đóng dấu"),
    rg.Reference(SealClerk, "company_id", "văn thư giữ dấu"),
    #  Hành chính – nhân sự
    rg.Reference(LeaveRequest, "company_id", "đơn nghỉ phép"),
    rg.Reference(LeaveBalance, "company_id", "quỹ phép"),
    rg.Reference(Holiday, "company_id", "ngày lễ"),
    rg.Reference(MeetingRoom, "company_id", "phòng họp"),
    rg.Reference(RoomBooking, "company_id", "lịch đặt phòng họp"),
    rg.Reference(VehicleBooking, "company_id", "phiếu đặt xe"),
    rg.Reference(Ticket, "company_id", "phiếu hỗ trợ"),
    rg.Reference(Mailbox, "company_id", "hộp thư"),
    rg.Reference(ForumPost, "company_id", "bài diễn đàn"),
    rg.Reference(CoffeePolicy, "company_id", "chính sách điểm cà phê"),
    rg.Reference(CoffeeMember, "company_id", "thành viên điểm cà phê"),
    #  Công việc
    rg.Reference(WorkGroup, "company_id", "nhóm công việc"),
    rg.Reference(WorkList, "company_id", "bảng công việc"),
    rg.Reference(WorkTask, "company_id", "thẻ công việc"),
])
