from sqlalchemy import BigInteger, Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin

# Trạng thái DÒNG khảo sát — lưu bằng slug tiếng Anh cho khớp cột `status` của cùng bảng
# (draft/submitted/approved/...). Nhãn tiếng Việt để ở tầng hiển thị, xem LINE_STATUS_LABEL.
LS_RESURVEY = "resurvey"      # cần khảo sát lại
LS_COMPLETED = "completed"    # hoàn thành
LINE_STATUSES = ("", LS_RESURVEY, LS_COMPLETED)


class SurveyRequest(Base, AuditMixin):
    """Phiếu YÊU CẦU KHẢO SÁT (Task 5). Người YC lập để nhờ thu mua khảo sát sản phẩm/NCC,
    sau khi hoàn thành sẽ chọn option (ẩn NCC) và sinh Phiếu Yêu cầu mua hàng (PYC)."""

    __tablename__ = "tab_survey_request"

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")   # YCKS + DDMMYY + seq
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)           # pháp nhân nhận hóa đơn
    requester: Mapped[str] = mapped_column(String(255), default="")
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)   # id nhân sự người yêu cầu (để so scope)
    requester_position: Mapped[str] = mapped_column(String(100), default="")
    department: Mapped[str] = mapped_column(String(255), default="", index=True)
    head_of_dept: Mapped[str] = mapped_column(String(255), default="")       # trưởng bộ phận
    purpose: Mapped[str] = mapped_column(String(255), default="")
    request_date: Mapped[str] = mapped_column(String(10), default="")
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)  # draft|submitted|approved|rejected|processing|survey_done
    # BỎ: `assignee_id` (NSTM chính toàn phiếu). Việc khảo sát thuộc về DÒNG
    # (`SurveyRequestLine.assignee`) — xem CR-018 trong doc/tai-lieu-ky-thuat/change-log.md.
    # Cột đã drop khỏi DB bằng migration `a3f5c81d7e64`. ĐỪNG nhầm với
    # `PurchaseRequest.assignee_id` (YCMH) — trùng tên nhưng vẫn đang dùng.
    note: Mapped[str] = mapped_column(Text, default="")
    reject_reason: Mapped[str] = mapped_column(Text, default="")


class SurveyRequestLine(Base, AuditMixin):
    """Dòng của phiếu yêu cầu khảo sát — mỗi dòng 1 sản phẩm/nhóm hàng cần khảo sát."""

    __tablename__ = "tab_survey_request_line"

    survey_request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    internal_line_code: Mapped[str] = mapped_column(String(50), default="")  # mã yêu cầu dòng (auto, KHÔNG hiện với người YC)
    received_date: Mapped[str] = mapped_column(String(10), default="")
    result_due_date: Mapped[str] = mapped_column(String(10), default="")
    # CR-075: ngày NSTM TRẢ kết quả khảo sát cho dòng này (lúc bấm "Chốt khảo sát" — có phương án
    # hoặc chốt rỗng). Đi cặp với `result_due_date` để đo trễ hạn ở màn Tiến độ báo giá.
    # Ghi MỘT LẦN, lần chốt đầu tiên; khảo sát lại KHÔNG ghi đè (giữ mốc gốc để không xóa dấu trễ).
    result_date: Mapped[str] = mapped_column(String(10), default="")
    department_requester: Mapped[str] = mapped_column(String(255), default="")  # BP/Người YC
    item_group: Mapped[str] = mapped_column(String(100), default="", index=True)  # phân loại
    requirement_detail: Mapped[str] = mapped_column(Text, default="")        # thông số kỹ thuật & chất lượng
    other_requirement: Mapped[str] = mapped_column(Text, default="")
    request_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)     # SL dự kiến mua
    uom: Mapped[str] = mapped_column(String(25), default="")
    proposed_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)  # giá đề xuất VNĐ — đơn giá giữ 4 số lẻ
    image_file: Mapped[str] = mapped_column(String(500), default="")
    assignee: Mapped[str] = mapped_column(String(100), default="")           # mã NSTM phụ trách dòng
    pr_id: Mapped[int] = mapped_column(BigInteger, default=0)                 # PYC sinh ra từ dòng
    pr_code: Mapped[str] = mapped_column(String(50), default="")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    # Trạng thái dòng do người YC / phòng ban YC cập nhật (Task 2):
    #   "" chưa xác định · LS_RESURVEY cần khảo sát lại · LS_COMPLETED hoàn thành
    # Đồng bộ: is_completed = (line_status == LS_COMPLETED).
    line_status: Mapped[str] = mapped_column(String(30), default="", index=True)
    no_option: Mapped[bool] = mapped_column(Boolean, default=False)           # chốt rỗng: khảo sát nhưng không có phương án phù hợp


class SurveyRequestOption(Base, AuditMixin):
    """Option gắn vào 1 dòng yêu cầu = 1 kết quả khảo sát SP đã duyệt (snapshot).
    Bảng trung tâm cho cơ chế ẩn NCC: field supplier_* KHÔNG trả về API người YC."""

    __tablename__ = "tab_survey_request_option"

    survey_request_line_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_survey_line_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # nguồn: tab_survey_product_line
    public_id: Mapped[int] = mapped_column(Integer, default=0)                # ID ẩn danh (Option 1,2..) trong 1 dòng
    display_label: Mapped[str] = mapped_column(String(50), default="")        # "Option 1 — ID 789"
    is_chosen: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    chosen_by: Mapped[int] = mapped_column(BigInteger, default=0)
    # Mã SP hệ thống (tab_product.code) NSTM gắn cho option — để tạo dòng PYC. KHÔNG bắt buộc.
    system_product_code: Mapped[str] = mapped_column(String(50), default="")

    # SNAPSHOT thông số (copy từ SurveyProductLine tại thời điểm gắn) — hiển thị được với người YC
    snap_product_name: Mapped[str] = mapped_column(String(255), default="")
    snap_spec: Mapped[str] = mapped_column(Text, default="")
    snap_origin: Mapped[str] = mapped_column(String(100), default="")
    snap_quote_unit: Mapped[str] = mapped_column(String(25), default="")
    snap_moq: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    snap_price_by_volume: Mapped[float] = mapped_column(Numeric(18, 4), default=0)   # snapshot đơn giá — 4 số lẻ
    snap_volume_range: Mapped[str] = mapped_column(String(100), default="")
    snap_vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    snap_delivery_time: Mapped[str] = mapped_column(String(100), default="")
    snap_delivery_place: Mapped[str] = mapped_column(String(255), default="")
    snap_shipping_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    snap_sample_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    snap_lab_result: Mapped[str] = mapped_column(String(20), default="")

    # Trường NỘI BỘ NSTM — backend LỌC, KHÔNG trả cho người YC
    snap_internal_code: Mapped[str] = mapped_column(String(50), default="")  # mã SP theo NCC
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    supplier_survey_id: Mapped[int] = mapped_column(BigInteger, default=0)
    # CR-147 (ticket #11): nstm_note (snapshot từ nspt_reason 'Lý do NSPT') nay HIỆN
    # cho người YC trên thẻ phương án — khách chấp nhận rủi ro ghi chú nhắc tên NCC.
    nstm_note: Mapped[str] = mapped_column(Text, default="")


class SurveyRequestPr(Base, AuditMixin):
    """Liên kết mỗi lần tạo YCMH từ 1 option của 1 dòng YCKS (1 dòng có thể tạo NHIỀU YCMH — mua lại)."""

    __tablename__ = "tab_survey_request_pr"

    survey_request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    survey_request_line_id: Mapped[int] = mapped_column(BigInteger, index=True)
    option_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    product_survey_line_id: Mapped[int] = mapped_column(BigInteger, default=0)  # nguồn khảo sát (đếm toàn hệ thống sau này)
    pr_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pr_code: Mapped[str] = mapped_column(String(50), default="")
