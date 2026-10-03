"""QUÁ TRÌNH CÔNG TÁC — `tab_employee_work_history` (bản gọn V1, HR ghi tay).

Lịch sử công tác THEO NGƯỜI: mỗi dòng là một sự kiện (tuyển dụng, điều chuyển,
bổ nhiệm, kiêm nhiệm, miễn nhiệm, thôi việc...). Không phiếu nhiều người,
không duyệt — khác hẳn V1-8 (`tab_hr_decision`, CHƯA LÀM) là đầu phiếu có tờ
trình + luồng duyệt. Thiết kế đầy đủ: phase-01 của plan
`frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/`.

⚠️ FK MỀM `employee_id` — khuôn `tab_employee_department`
(`employee/department_model.py`): KHÔNG khai `ForeignKey`, xóa hồ sơ nhân sự
dọn bảng này ở TẦNG SERVICE, không có CASCADE của MySQL.

⚠️ `position_label` là NHÃN ĐÃ CHỤP tại thời điểm ghi dòng, CỐ Ý KHÔNG đi qua
`position_service.propagate_rename` khi danh mục Chức vụ đổi tên hay bị xóa —
khác hẳn `Employee.position` (luôn đồng bộ). Lịch sử phải đứng yên: dòng "Bổ
nhiệm Trưởng phòng Mua hàng" phải mãi đọc đúng chữ đó về sau. Độ dài
`String(100)` PHẢI khớp `Employee.position` — chép sang rồi bị MySQL cắt cụt
thì không ai biết.

Đường nâng lên V1-8 (không đập bỏ): thêm bảng `tab_hr_decision` (đầu phiếu: tờ
trình, số/ngày QĐ, nội dung, PDF, trạng thái duyệt) + cột `decision_id` ở bảng
này (mặc định `0` = dòng ghi tay hiện tại, giữ nguyên) + `replaces_employee_id`
cho "Thay thế cho". Duyệt phiếu V1-8 sinh dòng vào CHÍNH bảng này rồi gọi cùng
hàm áp hồ sơ của phase 02.
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmployeeWorkHistory(Base, AuditMixin):
    """Một dòng = một sự kiện trong quá trình công tác của MỘT nhân sự."""

    __tablename__ = "tab_employee_work_history"
    __table_args__ = (
        #  Mọi truy vấn lọc theo người, xếp theo ngày (tab hồ sơ, /me, áp hồ sơ
        #  theo thứ tự thời gian). KHÔNG unique: một ngày có thể vừa bổ nhiệm
        #  vừa kiêm nhiệm — hai dòng khác `event_type`.
        Index("ix_employee_work_history_emp_from", "employee_id", "from_date"),
    )

    #  FK MỀM — xem cảnh báo đầu tệp. KHÔNG `index=True` riêng (Low, review
    #  03/10/2026): index ghép `ix_employee_work_history_emp_from`
    #  `(employee_id, from_date)` ngay dưới đã làm leftmost-prefix cho mọi truy
    #  vấn lọc theo `employee_id` một mình — thêm index đơn là trùng, và trước
    #  đợt này model khai `index=True` còn migration `wkhist01` không tạo cột
    #  đó, hai bên lệch nhau.
    employee_id: Mapped[int] = mapped_column(BigInteger)

    #  `WorkEventType` (`core/hr_work_history_codes.py`). `0` không phải giá
    #  trị hợp lệ của enum — chặn ở tầng schema (phase 02).
    event_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    #  = NGÀY HIỆU LỰC (Q1 chốt GỘP 03/10/2026) — KHÔNG có cột `effective_date`
    #  riêng.
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    #  NULL = đang hiệu lực (sự kiện chưa kết thúc, ví dụ kiêm nhiệm chưa gỡ).
    to_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    #  `0` = không khai cho sự kiện này (ví dụ "Miễn nhiệm" không cần ghi lại
    #  company/department nếu không đổi).
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    position_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  NHÃN CHỤP — xem cảnh báo đầu tệp.
    position_label: Mapped[str] = mapped_column(String(100), default="")

    decision_no: Mapped[str] = mapped_column(String(50), default="")
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")

    #  Lần ÁP VÀO HỒ SƠ gần nhất (qua `update_employee`/`set_extra_departments`,
    #  phase 02) — NULL = chưa áp. Idempotent (A5): áp lại chỉ cập nhật hai
    #  cột này, không mở đường ghi thứ ba vào hồ sơ.
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    applied_by: Mapped[int] = mapped_column(BigInteger, default=0)
