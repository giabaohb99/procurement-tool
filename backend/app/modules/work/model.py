"""Phân hệ Công việc — bộ IntEnum và cụm tổ chức (nhóm · list · thành viên).

Thiết kế chốt ở `doc/erp/cong-viec/` (CR-216, 28/08/2026). Đây là phase **W0**:
chỉ bảng dữ liệu, chưa có nghiệp vụ.

Ba quy ước xuyên suốt cả bốn tệp model của phân hệ — đọc trước khi thêm cột:

1. **Người là `employee_id` (ID NHÂN SỰ)**, nhất quán với `assignee_id` /
   `requester_id` trên chứng từ thu mua (`02-bang-du-lieu.md` §0.1). Hệ quả đã
   chấp nhận: tài khoản không gắn nhân sự (`employee_id = 0`) không tham gia
   list, chỉ đi cửa quản trị.
   ⚠️ ĐỪNG lẫn với `created_by` của `AuditMixin` — cột đó là **user_id** ở mọi
   bảng trong hệ (xem đầu tệp `forum/model.py`). Chỗ nào cần trục nhân sự thì
   có cột riêng đặt tên rõ (`creator_employee_id`, `completed_by`), không mượn
   `created_by` để mang nghĩa khác nghĩa toàn hệ.
2. **Ngày lưu chuỗi `"YYYY-MM-DD"`** (`String(10)`), so sánh từ vựng — khớp cách
   chuông cảnh báo và tab Việc cần làm đang so hạn (`promised_date`, `due_date`).
   Đổi sang `DATE` là lệch khuôn tích hợp F-02/F-03 (§0.2).
3. **Trạng thái / vai trò / ưu tiên là `SMALLINT` + `IntEnum`** (luật R2/QĐ-11),
   khai ngay tại tệp này theo đúng khuôn `forum/model.py`.
   ⚠️ Tài liệu `02` §0.3 ghi "khai ở `status_catalog.py`" — KHÔNG làm được:
   khung đó là bộ mã **chuỗi** của QĐ-9 (`Code.value: str`), `gen_status_ts.py`
   sinh ra từ nó cũng là chuỗi. Bộ số đi theo lối `forum` / `import_tool`;
   nhãn tiếng Việt cho giao diện lấy ở `enum_labels()` bên dưới.
"""
from enum import IntEnum

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class WorkTaskStatus(IntEnum):
    """Trạng thái HỆ THỐNG của task — độc lập với cột kanban (Q2).

    Cột kanban do từng list tự đặt tên nên không đếm được; bộ số này là nguồn sự
    thật duy nhất cho "việc chưa xong", nhắc hạn và báo cáo.
    """

    OPEN = 1
    DONE = 2
    CANCELLED = 3


class WorkPriority(IntEnum):
    """Độ ưu tiên kiểu Lark. `NONE = 0` là mặc định khi người dùng không chọn."""

    NONE = 0
    P1 = 1   # cao nhất, tô đỏ
    P2 = 2
    P3 = 3
    P4 = 4


class WorkMemberRole(IntEnum):
    """Vai trò trong nhóm/list. **Số NHỎ = quyền TO** — cố ý (Q9).

    Vai trò hiệu lực khi một người vừa được mời riêng vừa kế thừa từ nhóm là
    `min()` của các nguồn, nên thứ tự số phải ngược với thứ tự quyền thì mới lấy
    được "vai trò cao hơn" bằng một phép tính, không phải bảng tra.
    """

    OWNER = 1
    ADMIN = 2
    MEMBER = 3
    VIEWER = 4


class WorkLabelFieldType(IntEnum):
    """Kiểu của một TRƯỜNG tùy biến (B-13) — sáu kiểu cơ bản như Lark.

    `SINGLE = 1` là mặc định và là kiểu DUY NHẤT tồn tại trước B-13, nên mọi
    trường đã khai trước đó nhận đúng giá trị này khi migration chạy: không phải
    vá dữ liệu cũ.

    Chỉ hai kiểu CHỌN mới có bộ giá trị (`tab_work_label_option`); bốn kiểu còn
    lại đọc thẳng từ cột `value_*` của `tab_work_task_label`.
    """

    SINGLE = 1      # chọn MỘT giá trị trong bộ
    MULTI = 2       # chọn NHIỀU giá trị trong bộ
    PERSON = 3      # một nhân sự
    NUMBER = 4      # số
    DATE = 5        # ngày, lưu chuỗi YYYY-MM-DD như mọi ngày khác của phân hệ
    TEXT = 6        # chữ một dòng


#  Hai kiểu có bộ giá trị đặt sẵn. Gom lại một chỗ vì cả service lẫn serializer
#  đều phải hỏi "trường này có options không".
LABEL_TYPES_WITH_OPTIONS = (WorkLabelFieldType.SINGLE, WorkLabelFieldType.MULTI)


class WorkAssigneeKind(IntEnum):
    """Người phụ trách hay người theo dõi. Một người chỉ một dòng mỗi task."""

    PIC = 1
    FOLLOWER = 2


#  Nhãn tiếng Việt của bốn bộ trên — giao diện đọc qua API, KHÔNG gõ lại bên
#  TypeScript (luật R2: tiếng Việt chỉ sống ở tầng hiển thị, khai một chỗ).
ENUM_LABELS: dict[str, dict[int, str]] = {
    "work_task_status": {
        WorkTaskStatus.OPEN: "Đang mở",
        WorkTaskStatus.DONE: "Hoàn thành",
        WorkTaskStatus.CANCELLED: "Đã hủy",
    },
    "work_priority": {
        WorkPriority.NONE: "Không đặt",
        WorkPriority.P1: "P1 — Khẩn",
        WorkPriority.P2: "P2 — Cao",
        WorkPriority.P3: "P3 — Vừa",
        WorkPriority.P4: "P4 — Thấp",
    },
    "work_member_role": {
        WorkMemberRole.OWNER: "Chủ sở hữu",
        WorkMemberRole.ADMIN: "Quản trị",
        WorkMemberRole.MEMBER: "Thành viên",
        WorkMemberRole.VIEWER: "Khách xem",
    },
    "work_assignee_kind": {
        WorkAssigneeKind.PIC: "Người phụ trách",
        WorkAssigneeKind.FOLLOWER: "Người theo dõi",
    },
}


def enum_labels(name: str) -> list[dict]:
    """Bộ nhãn dạng `[{value, label}]` cho ô chọn ngoài giao diện."""
    return [{"value": int(v), "label": lb} for v, lb in ENUM_LABELS[name].items()]


class WorkGroup(Base, AuditMixin):
    """Nhóm (thư mục) chứa các task list — tối đa 2 CẤP (A-08).

    `parent_id` trỏ nhóm cha. Chặn cấp 3 là việc của service: cha đã có
    `parent_id` thì không nhận con. Ràng buộc này KHÔNG diễn đạt được bằng khóa
    ngoại nên đừng trông vào DB giữ hộ.

    Lưu trữ (`is_archived`) chứ không xóa cứng: việc cũ còn phải tra lại.
    """

    __tablename__ = "tab_work_group"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_work_group.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)
    is_archived: Mapped[int] = mapped_column(SmallInteger, default=0)


class WorkList(Base, AuditMixin):
    """Danh sách công việc — ĐƠN VỊ PHÂN QUYỀN CHÍNH của phân hệ (A-01).

    `group_id` NULL là hợp lệ: list đứng lẻ ngoài mọi nhóm (A-08).
    """

    __tablename__ = "tab_work_list"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_work_group.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(20), default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)
    is_archived: Mapped[int] = mapped_column(SmallInteger, default=0)


class WorkGroupMember(Base, AuditMixin):
    """Thành viên của NHÓM — vai trò kế thừa xuống mọi list bên trong (A-09).

    `department_id` chừa sẵn cho A-06 (mời cả phòng ban, P1): một dòng = một
    phòng, nở ra nhân sự LÚC TÍNH QUYỀN chứ không chép từng người vào bảng —
    chép thì người mới vào phòng không tự có quyền, đúng cái A-06 muốn tránh.
    Dòng mời phòng để `employee_id = 0`.
    """

    __tablename__ = "tab_work_group_member"
    __table_args__ = (
        UniqueConstraint("group_id", "employee_id", name="uq_work_group_member"),
        Index("ix_work_group_member_emp", "employee_id"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_group.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    role: Mapped[int] = mapped_column(SmallInteger, default=int(WorkMemberRole.MEMBER))


class WorkListMember(Base, AuditMixin):
    """Thành viên của một LIST (A-02). Cùng khuôn với `WorkGroupMember`.

    Cố ý tách hai bảng thay vì một bảng đa hình `target_type/target_id`: tách thì
    giữ được khóa ngoại thật về `tab_work_group` / `tab_work_list`, còn đa hình
    thì không cột nào tham chiếu được và xóa nhóm là bỏ lại dòng mồ côi.

    Mỗi list đúng MỘT dòng `OWNER` — bất biến do service giữ (A-04); DB không
    diễn đạt được "đúng một dòng có role = 1 trong mỗi list".
    """

    __tablename__ = "tab_work_list_member"
    __table_args__ = (
        UniqueConstraint("list_id", "employee_id", name="uq_work_list_member"),
        Index("ix_work_list_member_emp", "employee_id"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    role: Mapped[int] = mapped_column(SmallInteger, default=int(WorkMemberRole.MEMBER))
