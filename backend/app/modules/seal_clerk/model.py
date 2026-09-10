from enum import IntEnum

from sqlalchemy import BigInteger, Boolean, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class ClerkStatus(IntEnum):
    """Trạng thái phân công văn thư (R2/QĐ-11 — cột trạng thái là SMALLINT + IntEnum).

    Chỉ `ACTIVE` mới nhận phiếu đóng dấu; hai trạng thái còn lại (nghỉ phép, ngưng
    dùng) đều GIỮ phân công nhưng NGỪNG nhận phiếu — khác nhau ở ý nghĩa hiển thị.
    """

    ACTIVE = 1     # Đang hoạt động — nhận phiếu bình thường.
    ON_LEAVE = 2   # Nghỉ phép — tạm ngừng nhận phiếu, sẽ quay lại.
    INACTIVE = 3   # Ngưng sử dụng — không còn làm văn thư.


CLERK_ACTIVE = int(ClerkStatus.ACTIVE)
CLERK_ON_LEAVE = int(ClerkStatus.ON_LEAVE)
CLERK_INACTIVE = int(ClerkStatus.INACTIVE)

CLERK_STATUS_LABELS: dict[int, str] = {
    CLERK_ACTIVE: "Đang hoạt động",
    CLERK_ON_LEAVE: "Nghỉ phép",
    CLERK_INACTIVE: "Ngưng sử dụng",
}


class SealClerk(Base, AuditMixin):
    """Phân công VĂN THƯ (Duyệt dấu) theo công ty.

    Mỗi dòng = một văn thư phụ trách đóng dấu cho MỘT công ty. Một người phụ trách
    nhiều công ty thì nhiều dòng.

    ⚠️ **Đây là bảng CẤU HÌNH lái phạm vi dữ liệu**, giống `tab_category_assignee`
    lái cột `assignee` của YCMH. Nó được đọc TRỰC TIẾP trong nhánh `seal_request`
    `scope == "company"` của `core/scoping.py` (văn thư chỉ thấy phiếu Đã duyệt của
    công ty mình phụ trách) và trong `seal_request/notify.py` (báo đúng văn thư).

    `is_head` = VĂN THƯ TỔNG: phụ trách phiếu cần dấu của NHIỀU công ty (đa công ty).
    Phiếu một công ty do văn thư của chính công ty đó xử lý — văn thư tổng KHÔNG thấy.
    Dòng văn thư tổng để `company_id = 0`.
    """

    __tablename__ = "tab_seal_clerk"

    employee_id: Mapped[int] = mapped_column(BigInteger, index=True)   # văn thư (tab_employee.id)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # 0 khi là văn thư tổng
    is_head: Mapped[bool] = mapped_column(Boolean, default=False)      # văn thư tổng (đa công ty)
    #  Trạng thái phân công (theo văn thư): Tạm dừng thì scoping + notify BỎ QUA người
    #  này — giữ nguyên danh sách công ty nhưng ngừng nhận phiếu cho tới khi bật lại.
    status: Mapped[int] = mapped_column(SmallInteger, default=CLERK_ACTIVE, server_default=str(CLERK_ACTIVE))
