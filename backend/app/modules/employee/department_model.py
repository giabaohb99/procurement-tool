"""KIÊM NHIỆM — một nhân sự thuộc NHIỀU phòng ban (CR-167).

Trước đây `tab_employee.department_id` là một số duy nhất, nên người kiêm nhiệm
hai bộ phận chỉ khai được một. Hệ quả không nằm ở màn hồ sơ mà ở **phạm vi dữ
liệu**: vai trò phạm vi *phòng ban* mở đúng một phòng ghi trên hồ sơ, nên trưởng
phòng kiêm nhiệm chỉ thấy phiếu của một trong hai bộ phận mình phụ trách.

⚠️ **`tab_employee.department_id` VẪN CÒN và vẫn là phòng CHÍNH.** Mười hai chỗ
trong mã đang đọc nó (dựng bối cảnh phiếu, gửi thông báo cho trưởng phòng, phạm
vi áp dụng văn bản, dấu vết…). Bảng này **cộng thêm**, không thay thế: dòng
`is_primary` luôn được giữ khớp với cột kia, và `dat_phong_ban()` là chỗ duy nhất
ghi cả hai để chúng không lệch nhau.

⚠️ **Đây là bảng NHẠY VỀ QUYỀN.** Thêm một phòng cho ai đó là mở rộng tầm nhìn dữ
liệu của họ. Chốt chặn nằm ở `employee/department_service.py` — đọc trước khi mở
thêm cửa ghi vào bảng này.
"""
from sqlalchemy import BigInteger, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmployeeDepartment(Base, AuditMixin):
    """Một dòng = «nhân sự X có chân ở phòng Y»."""

    __tablename__ = "tab_employee_department"
    __table_args__ = (
        #  Khai trùng một phòng hai lần không thêm nghĩa gì, chỉ làm mọi phép
        #  đếm theo phòng cộng dư.
        UniqueConstraint("employee_id", "department_id", name="uq_employee_department"),
        #  Hai chiều tra đều nóng: «người này thuộc phòng nào» (dựng hồ sơ quyền,
        #  chạy mỗi request) và «phòng này có ai» (gửi thông báo, đếm quân số).
        Index("ix_employee_department_employee", "employee_id"),
        Index("ix_employee_department_department", "department_id"),
    )

    employee_id: Mapped[int] = mapped_column(BigInteger, index=True)
    department_id: Mapped[int] = mapped_column(BigInteger, index=True)

    #  PHÒNG CHÍNH — đúng một dòng mỗi nhân sự, và luôn khớp
    #  `tab_employee.department_id`.
    #
    #  Vì sao cần đánh dấu thay vì "phòng nào cũng như nhau": phiếu do người này
    #  lập phải ghi MỘT phòng chủ trì, thông báo gửi cho trưởng phòng phải chọn
    #  MỘT người. Không có phòng chính thì mấy chỗ đó phải tự đoán.
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
