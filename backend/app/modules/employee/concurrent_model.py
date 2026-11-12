"""KIÊM NHIỆM (tab riêng, khác công ty được) — `tab_employee_concurrent` (duoc-CR-755).

Mỗi dòng = "nhân sự X kiêm nhiệm phòng Y của công ty Z, chức vụ W, từ ngày … đến ngày …,
theo quyết định số …". Thay cho dòng phụ (`is_primary = 0`) của `tab_employee_department`,
bảng đó từ nay CHỈ còn dòng phòng CHÍNH.

Vì sao bảng mới mà không mở rộng bảng cũ:
- `set_departments` xóa hết rồi chèn lại nên id dòng đổi mỗi lần lưu — tệp quyết định
  (`FileLink.entity_id` = id dòng) sẽ mồ côi. Ở đây dòng được sửa TẠI CHỖ, id bền.
- UNIQUE(employee, department) của bảng cũ chặn phòng dùng chung (`company_id = 0`) vừa là
  phòng chính ở công ty A vừa là phòng kiêm nhiệm ở công ty B. Bảng này KHÔNG có UNIQUE đó;
  chống chồng giai đoạn làm ở service (`concurrent_service.block_overlap`).

⚠️ Đây là bảng NHẠY VỀ QUYỀN: dòng còn hiệu lực + `counts_scope` mở thêm phạm vi dữ liệu
cho người đó (xem `core/auth.get_perm_profile`). Mọi cửa ghi đi qua `concurrent_service` với
ba chốt L1/L2/L3 của `department_service`.

FK MỀM: `employee_id`, `company_id`, `department_id`, `position_id` không khai `ForeignKey`
(cùng khuôn `tab_employee_department`, `tab_employee_work_history`); xóa hồ sơ dọn bảng này ở
tầng service. `position_label` là nhãn CHỤP lúc ghi, không đi theo đổi tên danh mục Chức vụ.
"""
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmployeeConcurrent(Base, AuditMixin):
    """Một dòng kiêm nhiệm của MỘT nhân sự."""

    __tablename__ = "tab_employee_concurrent"
    __table_args__ = (
        #  Dựng hồ sơ quyền (mỗi request) và tab hồ sơ: lọc theo người.
        Index("ix_employee_concurrent_employee", "employee_id"),
        #  "Phòng này ở công ty này có ai kiêm nhiệm" (phòng B thấy người kiêm nhiệm, phase 05).
        Index("ix_employee_concurrent_dept_company", "department_id", "company_id"),
        #  Dòng quá trình công tác đã Áp ra dòng này (phase 03).
        Index("ix_employee_concurrent_work_history", "work_history_id"),
    )

    employee_id: Mapped[int] = mapped_column(BigInteger)
    company_id: Mapped[int] = mapped_column(BigInteger)
    department_id: Mapped[int] = mapped_column(BigInteger)
    position_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  NHÃN CHỤP — String(100) khớp `Employee.position`; xem cảnh báo đầu tệp.
    position_label: Mapped[str] = mapped_column(String(100), default="")

    #  NULL chỉ có ở dòng chép từ dữ liệu cũ (đã hiệu lực từ trước, không rõ ngày). Dòng tạo mới
    #  luôn có từ ngày (chặn ở schema). `to_date` NULL = chưa kết thúc.
    from_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    to_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    decision_no: Mapped[str] = mapped_column(String(50), default="")
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")

    #  Công tắc "Tính vào phạm vi quyền" — tắt thì dòng chỉ là ghi nhận, không mở thêm dữ liệu.
    counts_scope: Mapped[bool] = mapped_column(Boolean, default=True)

    #  Id dòng `tab_employee_work_history` đã Áp ra dòng này (phase 03); 0 = nhập tay ở tab.
    work_history_id: Mapped[int] = mapped_column(BigInteger, default=0)
