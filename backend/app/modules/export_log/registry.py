"""Khai báo các bảng được phép Xuất dữ liệu tập trung (Đ-13b).

Mỗi đối tượng khai một *adapter*: model · khóa phạm vi (cho `apply_scope`) · bộ cột
(dùng lại `export_xlsx.Col`, chung cho cả CSV và XLSX). Thêm bảng xuất mới = thêm
một adapter, không đụng service/controller.

Giá trị ô đọc bằng `getattr(item, col.key, "")` nên khai được cả THUỘC TÍNH tính toán
(vd `department_name`, `company_name`, `status_label`) lẫn cột thật; khóa lạ trả rỗng.
"""
from app.core.export_xlsx import Col
from app.modules.catalog.model import ItemGroup, Unit, Warehouse
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.product.model import Product
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.seal_request.model import SealRequest, SealType
from app.modules.supplier.model import Supplier
from app.modules.survey_request.model import SurveyRequest
from app.modules.vehicle_booking.model import Driver, Vehicle, VehicleBooking

EXPORT_ADAPTERS: dict[str, dict] = {
    "employee": {
        "label": "Nhân sự",
        "module": "hr",
        "model": Employee,
        "scope": "employee",
        # Cột KHỚP mẫu import (mã hóa tham chiếu) -> xuất ra import lại được ngay.
        "columns": [
            Col("code", "Mã NV", width=16),
            Col("full_name", "Họ tên", width=28),
            Col("email", "Email", width=24),
            Col("phone", "Điện thoại", width=16),
            Col("company_id", "Công ty (mã)", ref="company", width=16),
            Col("department_id", "Phòng ban (mã)", ref="department", width=16),
            Col("position", "Chức vụ", width=18),
            Col("status", "Trạng thái (official/probation/…)", width=24),
            Col("is_active", "Hoạt động (1/0)", kind="bool", width=14),
        ],
    },
    "department": {
        "label": "Phòng ban",
        "module": "hr",
        "model": Department,
        "scope": "department",
        # Cột KHỚP mẫu import: Loại (int) · Công ty/Phòng cấp trên/Trưởng bộ phận
        # xuất bằng MÃ -> import lại được, và Trưởng bộ phận theo MÃ NV nên 2 người
        # trùng tên khác mã vẫn phân biệt.
        "columns": [
            Col("code", "Mã", width=16),
            Col("name", "Tên phòng ban", width=28),
            Col("issue_code", "Mã hiệu văn bản", width=18),
            Col("kind", "Loại (1 chức năng/2 kinh doanh/3 dự án)", kind="int", width=30),
            Col("company_id", "Công ty (mã)", ref="company", width=16),
            Col("parent", "Phòng cấp trên (mã)", ref="self", width=18),
            Col("manager_id", "Trưởng bộ phận (mã NV)", ref="employee", width=20),
            Col("is_active", "Hoạt động (1/0)", kind="bool", width=14),
        ],
    },
    "company": {
        "label": "Công ty",
        "module": "hr",
        "model": Company,
        "scope": "company",
        "columns": [
            Col("code", "Mã", width=16),
            Col("name", "Tên công ty", width=28),
            Col("short_name", "Tên viết tắt", width=18),
            Col("tax_code", "Mã số thuế", width=16),
            Col("address", "Địa chỉ", width=30),
            Col("invoice_email", "Email nhận hóa đơn", width=24),
            Col("is_active", "Hoạt động", kind="bool", width=12),
        ],
    },
    # ── Thu mua (chứng từ — xuất dòng ĐẦU PHIẾU) ─────────────────────────────
    "survey_request": {
        "label": "Yêu cầu báo giá",
        "module": "procurement",
        "model": SurveyRequest,
        "scope": "survey_request",
        "columns": [
            Col("code", "Mã YCBG", width=18),
            Col("requester", "Người yêu cầu", width=22),
            Col("department", "Phòng ban", width=22),
            Col("purpose", "Mục đích", width=26),
            Col("request_date", "Ngày yêu cầu", kind="date", width=14),
            Col("status", "Trạng thái", width=14),
        ],
    },
    "purchase_request": {
        "label": "Yêu cầu mua hàng",
        "module": "procurement",
        "model": PurchaseRequest,
        "scope": "purchase_request",
        "columns": [
            Col("code", "Mã YCMH", width=18),
            Col("requester", "Người yêu cầu", width=22),
            Col("department", "Phòng ban", width=22),
            Col("purpose", "Mục đích", width=26),
            Col("request_date", "Ngày yêu cầu", kind="date", width=14),
            Col("need_date", "Ngày cần hàng", kind="date", width=14),
            Col("status", "Trạng thái", width=14),
        ],
    },
    "purchase_order": {
        "label": "Đơn mua hàng",
        "module": "procurement",
        "model": PurchaseOrder,
        "scope": "purchase_order",
        "columns": [
            Col("code", "Mã ĐMH", width=16),
            Col("misa_code", "Mã Misa", width=16),
            Col("pr_code", "Mã YCMH", width=16),
            Col("supplier_name", "Nhà cung cấp", width=26),
            Col("department", "Phòng ban", width=22),
            Col("order_date", "Ngày đặt", kind="date", width=14),
            Col("status", "Trạng thái", width=14),
        ],
    },
    # ── Sản xuất (danh mục) ──────────────────────────────────────────────────
    "supplier": {
        "label": "Nhà cung cấp",
        "module": "production",
        "model": Supplier,
        "scope": "supplier",
        "columns": [
            Col("code", "Mã", width=16),
            Col("name", "Tên pháp lý", width=28),
            Col("tax_code", "Mã số thuế", width=16),
            Col("address", "Địa chỉ", width=30),
            Col("supplier_type", "Loại NCC", width=14),
            Col("contact_person", "Người liên hệ", width=20),
            Col("phone", "Điện thoại", width=16),
            Col("payment_terms", "Hình thức thanh toán", width=22),
            Col("is_active", "Hoạt động", kind="bool", width=12),
        ],
    },
    "product": {
        "label": "Sản phẩm & Vật tư",
        "module": "production",
        "model": Product,
        "scope": "product",
        "columns": [
            Col("code", "Mã VTBB/NL", width=18),
            Col("name", "Tên VTBB/NL", width=28),
            Col("invoice_name", "Tên trên hóa đơn", width=24),
            Col("item_group", "Phân loại", width=16),
            Col("unit", "ĐVT", width=10),
            Col("hh_code", "Mã HH", width=14),
            Col("hh_name", "Tên HH", width=24),
            Col("specs", "Thông số kỹ thuật", width=28),
            Col("is_active", "Hoạt động", kind="bool", width=12),
        ],
    },
    "unit": {
        "label": "Đơn vị tính",
        "module": "production",
        "model": Unit,
        "scope": "unit",
        "columns": [
            Col("code", "Mã", width=16),
            Col("name", "Tên", width=24),
            Col("is_active", "Hoạt động", kind="bool", width=12),
        ],
    },
    "item_group": {
        "label": "Phân loại VTBB",
        "module": "production",
        "model": ItemGroup,
        "scope": "item_group",
        "columns": [
            Col("code", "Mã", width=16),
            Col("name", "Tên", width=24),
            Col("std_days", "Ngày QĐ (có sẵn)", width=16),
            Col("std_days_unavail", "Ngày QĐ (không sẵn)", width=18),
            Col("apply_date", "Ngày áp dụng", width=14),
            Col("is_active", "Hoạt động", kind="bool", width=12),
        ],
    },
    # ── Kho ──────────────────────────────────────────────────────────────────
    "warehouse": {
        "label": "Danh mục kho",
        "module": "inventory",
        "model": Warehouse,
        "scope": "warehouse",
        "columns": [
            Col("code", "Mã", width=16),
            Col("name", "Tên kho", width=24),
            Col("address", "Địa chỉ", width=30),
            Col("is_active", "Hoạt động", kind="bool", width=12),
        ],
    },
    # ── Đặt xe ───────────────────────────────────────────────────────────────
    "vehicle": {
        "label": "Xe",
        "module": "vehicle-booking",
        "model": Vehicle,
        "scope": "vehicle",
        "columns": [
            Col("license_plate", "Biển số / Tên xe", width=20),
            Col("model", "Mẫu xe", width=20),
            Col("type", "Loại xe", width=14),
            Col("capacity", "Tải (người/tấn)", width=16),
            Col("status", "Trạng thái", width=14),
            Col("is_external", "Thuê ngoài (1/0)", kind="bool", width=14),
            Col("external_company", "Đơn vị (thuê ngoài)", width=24),
            Col("tax_code", "Mã số thuế", width=16),
        ],
    },
    "driver": {
        "label": "Tài xế",
        "module": "vehicle-booking",
        "model": Driver,
        "scope": "driver",
        "columns": [
            Col("name", "Họ tên", width=24),
            Col("phone", "Điện thoại", width=16),
            Col("email", "Email", width=22),
            Col("license_number", "Số GPLX", width=16),
            Col("license_class", "Hạng GPLX", width=12),
            Col("status", "Trạng thái", width=14),
            Col("is_external", "Thuê ngoài (1/0)", kind="bool", width=14),
            Col("external_company", "Đơn vị (thuê ngoài)", width=24),
        ],
    },
    "vehicle_booking": {
        "label": "Yêu cầu đặt xe",
        "module": "vehicle-booking",
        "model": VehicleBooking,
        "scope": "vehicle_booking",
        #  Bộ cột HỢP NHẤT cho cả đặt xe công tác lẫn giao hàng — nhãn khớp mẫu import
        #  (xuất ra import lại được). Loại/Trạng thái xuất NHÃN; Công ty/Xe/Tài xế theo
        #  mã/biển số/tên; thời gian là chuỗi ISO đã lưu; Tệp đính kèm gộp tên tệp.
        "columns": [
            Col("code", "Mã yêu cầu", width=16),
            Col("request_type_label", "Loại yêu cầu", width=16),
            Col("purpose", "Tiêu đề", width=28),
            Col("status_label", "Trạng thái chung", width=16),
            Col("requester", "Tên người tạo", width=22),
            Col("company_id", "Công ty", ref="company", width=16),
            Col("department_id", "Phòng ban người tạo", ref="department", width=18),
            Col("start_time", "Thời gian đi", width=18),
            Col("end_time", "Thời gian về", width=18),
            Col("start_location", "Điểm đi", width=22),
            Col("end_location", "Điểm đến", width=22),
            Col("passenger_count", "Số hành khách", kind="int", width=12),
            Col("attendees", "Người tham gia", width=22),
            Col("contact_phone", "SĐT người tham gia", width=16),
            Col("is_round_trip", "Khứ hồi", kind="bool", width=10),
            Col("note", "Ghi chú", width=28),
            Col("goods_name", "Tên hàng hóa", width=20),
            Col("goods_size", "Kích thước/KL", width=14),
            Col("sender_name", "Tên người gửi", width=18),
            Col("sender_phone", "SĐT người gửi", width=16),
            Col("receiver_name", "Tên người nhận", width=18),
            Col("receiver_phone", "SĐT người nhận", width=16),
            Col("special_instructions", "Chỉ dẫn đặc biệt", width=28),
            Col("dispatched_at", "Thời gian điều phối", width=18),
            Col("assigned_vehicle_id", "Biển số xe", ref="vehicle", width=16),
            Col("assigned_driver_id", "Tên tài xế", ref="driver", width=20),
            Col("driver_status_label", "Trạng thái tài xế", width=16),
            Col("actual_start_time", "Bắt đầu thực tế", width=18),
            Col("actual_end_time", "Kết thúc thực tế", width=18),
            Col("_attachments", "Tệp đính kèm", kind="attachments", width=24),
            Col("created_at", "Ngày tạo", kind="datetime", width=18),
        ],
    },
    # ── Duyệt dấu ────────────────────────────────────────────────────────────
    "seal_type": {
        "label": "Loại con dấu",
        "module": "seal",
        "model": SealType,
        "scope": "seal_type",
        "columns": [
            Col("name", "Tên loại con dấu", width=24),
            Col("description", "Mô tả", width=30),
            Col("is_active", "Đang dùng (1/0)", kind="bool", width=14),
        ],
    },
    "seal_request": {
        "label": "Yêu cầu đóng dấu",
        "module": "seal",
        "model": SealRequest,
        "scope": "seal_request",
        #  Nhãn khớp mẫu import (xuất ra import lại được). Trạng thái xuất NHÃN; Công
        #  ty/Phòng ban theo mã; Người duyệt (id tài khoản) hiện HỌ TÊN; Tệp đính kèm
        #  gộp tên tệp.
        "columns": [
            Col("code", "Mã yêu cầu", width=16),
            Col("title", "Tiêu đề", width=28),
            Col("purpose", "Chi tiết loại", width=24),
            Col("status_label", "Trạng thái chung", width=16),
            Col("requester", "Tên người tạo", width=22),
            Col("department_id", "Phòng ban người tạo", ref="department", width=18),
            Col("company_id", "Công ty", ref="company", width=16),
            Col("first_approver_id", "Người duyệt cấp 1", ref="approver", width=20),
            Col("note", "Ghi chú", width=28),
            Col("_attachments", "Tệp đính kèm", kind="attachments", width=24),
            Col("created_at", "Ngày tạo", kind="datetime", width=18),
        ],
    },
}


def is_exportable(entity: str) -> bool:
    return entity in EXPORT_ADAPTERS
