"""Phân hệ Điểm cà phê (POS365) — bộ IntEnum và 5 bảng dữ liệu.

Thiết kế chốt ở `doc/erp/diem-ca-phe/02-bang-du-lieu.md` (08/09/2026). Đây là phase
**CP1**: nền dữ liệu + phân quyền, nghiệp vụ ở `service.py`/`tasks.py` (CP2).

Năm quy ước xuyên suốt — đọc trước khi thêm cột:

1. **Người là `employee_id` (ID NHÂN SỰ)** — điểm là phúc lợi của nhân sự; tài khoản
   không gắn nhân sự (`employee_id = 0`) không có ví. ĐỪNG lẫn với `created_by` của
   `AuditMixin` (cột đó là user_id toàn hệ).
2. **Sổ cái `tab_coffee_ledger` CHỈ INSERT.** Không endpoint nào UPDATE/DELETE nó; sửa
   sai bằng dòng đảo ngược (`ADJUST`). Số dư KHÔNG có cột — luôn là `SUM(points)`.
3. **Điểm là số nguyên CÓ DẤU, đơn vị = đồng** (N1: 1 điểm = 1 đồng, chờ xác nhận).
   `GRANT/REFUND` dương, `EXPIRE/SPEND/REVOKE` âm, `ADJUST` hai chiều — số dư là một
   phép SUM, không phải CASE theo loại.
4. **Trạng thái / loại / cấp là `SMALLINT` + `IntEnum`** (luật R2/QĐ-11), khai ngay tại
   tệp này theo khuôn `work/model.py`; nhãn tiếng Việt ở `ENUM_LABELS`, API trả kèm —
   giao diện KHÔNG gõ lại.
5. **Mọi bảng có `company_id`** (quán có thể thuộc pháp nhân khác công ty mẹ); model
   đăng ở `all_models.py` kẻo autogenerate bỏ sót.
"""
from enum import IntEnum

from sqlalchemy import (BigInteger, DateTime, Index, Integer, Numeric,
                        SmallInteger, String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class CoffeeLevel(IntEnum):
    """Cấp phúc lợi cà phê (A-02) — BỘ CHỐT theo lời sếp 08/09/2026.

    "Cấp nhân sự" chưa tồn tại trong hệ (`tab_employee.position` là chữ tự do) nên
    bản 1 gán cấp tay ở `tab_coffee_member`; khi HR5 (danh mục chức danh) có thật
    thì nối qua `title_id`. Thêm cấp mới = thêm thành viên enum (sự kiện hiếm, cố ý
    qua review); đổi MỨC ĐIỂM thì là dữ liệu (`tab_coffee_policy`), không đụng code.
    """

    INTERN = 1       # Thực tập sinh
    PROBATION = 2    # Thử việc
    STAFF = 3        # Nhân viên chính thức
    DEPT_HEAD = 4    # Trưởng bộ phận
    OVERLORD = 5     # Chúa tể Hội đồng quản trị — VÔ HẠN điểm


#  Cấp VÔ HẠN: không cấp/không thu kỳ nào, quầy không chặn, ví hiện "Không giới
#  hạn" — nhưng dòng TIÊU vẫn ghi sổ đầy đủ (báo cáo vẫn biết chúa tể uống bao
#  nhiêu; "vô hạn" là không ai chặn, không phải không ai đếm).
UNLIMITED_LEVELS = frozenset({int(CoffeeLevel.OVERLORD)})


class CoffeeLedgerType(IntEnum):
    """Loại dòng sổ cái. `EXPIRE` = thu hết dư kỳ cũ lúc reset; `REVOKE` = thu hồi
    nghỉ việc; `REFUND` = hoàn do đơn POS365 bị void."""

    GRANT = 1
    EXPIRE = 2
    SPEND = 3
    REFUND = 4
    ADJUST = 5
    REVOKE = 6


class CoffeeMemberStatus(IntEnum):
    """`SUSPENDED` = tạm ngưng hưởng (nghỉ không lương/thai sản — N6 của `09`):
    không cấp kỳ mới, giữ số dư. `LEFT` = đã nghỉ việc, khóa hẳn (số dư đã revoke)."""

    ACTIVE = 1
    SUSPENDED = 2
    LEFT = 3


class PosOrderMatchStatus(IntEnum):
    """`UNMATCHED` = đơn "Trừ điểm" không khớp được nhân sự (hàng chờ D-02, người
    xử lý — hệ KHÔNG đoán); `IGNORED` = người xử lý bỏ qua có lý do."""

    MATCHED = 1
    UNMATCHED = 2
    IGNORED = 3


class PosSyncKind(IntEnum):
    PULL_ORDERS = 1
    CHECK_VOIDS = 2
    MONTHLY_RESET = 3
    RECONCILE = 4
    MIRROR = 5


class PosSyncStatus(IntEnum):
    """`SKIPPED` = cầu dao `POS365_HARD_OFF` đang bật — là CHỦ Ý, không phải sự cố,
    nên không tính vào chuỗi FAILED của cảnh báo D-06."""

    RUNNING = 1
    SUCCESS = 2
    FAILED = 3
    SKIPPED = 4


#  Nhãn tiếng Việt — giao diện đọc qua API, KHÔNG gõ lại bên TypeScript (luật R2:
#  tiếng Việt chỉ sống ở tầng hiển thị, khai một chỗ).
ENUM_LABELS: dict[str, dict[int, str]] = {
    "coffee_level": {
        CoffeeLevel.INTERN: "Thực tập sinh",
        CoffeeLevel.PROBATION: "Thử việc",
        CoffeeLevel.STAFF: "Nhân viên chính thức",
        CoffeeLevel.DEPT_HEAD: "Trưởng bộ phận",
        CoffeeLevel.OVERLORD: "Chúa tể Hội đồng quản trị",
    },
    "coffee_ledger_type": {
        CoffeeLedgerType.GRANT: "Cấp kỳ",
        CoffeeLedgerType.EXPIRE: "Thu cuối kỳ",
        CoffeeLedgerType.SPEND: "Tiêu tại quầy",
        CoffeeLedgerType.REFUND: "Hoàn (hủy đơn)",
        CoffeeLedgerType.ADJUST: "Điều chỉnh tay",
        CoffeeLedgerType.REVOKE: "Thu hồi (nghỉ việc)",
    },
    "coffee_member_status": {
        CoffeeMemberStatus.ACTIVE: "Đang hưởng",
        CoffeeMemberStatus.SUSPENDED: "Tạm ngưng",
        CoffeeMemberStatus.LEFT: "Đã nghỉ",
    },
    "pos_order_match_status": {
        PosOrderMatchStatus.MATCHED: "Đã khớp",
        PosOrderMatchStatus.UNMATCHED: "Chưa khớp",
        PosOrderMatchStatus.IGNORED: "Bỏ qua",
    },
    "pos_sync_kind": {
        PosSyncKind.PULL_ORDERS: "Kéo đơn hàng",
        PosSyncKind.CHECK_VOIDS: "Soát đơn hủy",
        PosSyncKind.MONTHLY_RESET: "Reset kỳ tháng",
        PosSyncKind.RECONCILE: "Đối chiếu",
        PosSyncKind.MIRROR: "Soi gương số dư",
    },
    "pos_sync_status": {
        PosSyncStatus.RUNNING: "Đang chạy",
        PosSyncStatus.SUCCESS: "Thành công",
        PosSyncStatus.FAILED: "Lỗi",
        PosSyncStatus.SKIPPED: "Bỏ qua (HARD_OFF)",
    },
}


class CoffeePolicy(Base, AuditMixin):
    """Chính sách cấp điểm theo cấp (A-01).

    Đổi mức = THÊM dòng `effective_from` mới, không sửa dòng cũ — để tra được "mức
    của tháng trước". Không có `effective_to`: dòng sau tự kết thúc dòng trước.
    Mức áp cho một kỳ = dòng có `effective_from` lớn nhất ≤ ngày 1 của kỳ.
    """

    __tablename__ = "tab_coffee_policy"
    __table_args__ = (
        UniqueConstraint("company_id", "level_code", "effective_from",
                         name="uq_coffee_policy_level_from"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    level_code: Mapped[int] = mapped_column(SmallInteger)          # CoffeeLevel
    monthly_points: Mapped[int] = mapped_column(Integer, default=0)
    effective_from: Mapped[str] = mapped_column(String(10))        # "YYYY-MM-DD"
    note: Mapped[str] = mapped_column(String(500), default="")

    @property
    def level_label(self) -> str:
        return ENUM_LABELS["coffee_level"].get(self.level_code, "")


class CoffeeMember(Base, AuditMixin):
    """Thành viên chương trình + khóa ghép POS365 (B-01, B-02).

    `pos_partner_id` ghi MỘT lần lúc người xác nhận ghép; mọi lần sau chỉ đối chiếu
    theo cột này — KHÔNG bao giờ tự tra lại theo tên/SĐT (luật A3 của `09` §8).
    Muốn ghép lại phải gỡ trước (có audit), service chặn ghi đè.
    """

    __tablename__ = "tab_coffee_member"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    level_code: Mapped[int] = mapped_column(SmallInteger)          # CoffeeLevel
    #  Để dành cho HR5 (danh mục chức danh) — bản 1 chưa dùng (A-02).
    title_id: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=int(CoffeeMemberStatus.ACTIVE))
    pos_partner_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    pos_partner_code: Mapped[str] = mapped_column(String(50), default="")
    matched_by: Mapped[int] = mapped_column(BigInteger, default=0)
    matched_at: Mapped[str] = mapped_column(String(19), default="")  # "YYYY-MM-DD HH:MM:SS"
    note: Mapped[str] = mapped_column(String(500), default="")

    @property
    def level_label(self) -> str:
        return ENUM_LABELS["coffee_level"].get(self.level_code, "")

    @property
    def status_label(self) -> str:
        return ENUM_LABELS["coffee_member_status"].get(self.status, "")

    @property
    def is_unlimited(self) -> bool:
        return self.level_code in UNLIMITED_LEVELS


class CoffeeLedger(Base, AuditMixin):
    """Sổ cái điểm (C-01) — CHỈ INSERT, ghi qua duy nhất `service.append_ledger`.

    `uniq_key` là khóa idempotent sinh trong service (MySQL/SQLite cho nhiều NULL
    trong UNIQUE): GRANT `G-{emp}-{period}` · EXPIRE `E-{emp}-{period}` ·
    SPEND `S-{pos_order_id}` · REFUND `R-{pos_order_id}` · ADJUST/REVOKE = NULL.
    Tầng DB là lớp chặn trùng CUỐI — không tin bộ nhớ tiến trình.
    """

    __tablename__ = "tab_coffee_ledger"
    __table_args__ = (
        Index("ix_coffee_ledger_emp_period", "employee_id", "period"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, index=True)
    period: Mapped[str] = mapped_column(String(6), index=True)     # "YYYYMM"
    type: Mapped[int] = mapped_column(SmallInteger)                # CoffeeLedgerType
    points: Mapped[int] = mapped_column(Integer)                   # CÓ DẤU
    pos_order_id: Mapped[int] = mapped_column(BigInteger, default=0)
    reason: Mapped[str] = mapped_column(String(500), default="")
    uniq_key: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)

    @property
    def type_label(self) -> str:
        return ENUM_LABELS["coffee_ledger_type"].get(self.type, "")


class PosOrder(Base, AuditMixin):
    """Bản sao đơn hàng "Trừ điểm" kéo về từ POS365 (D-01).

    `pos_status` lưu NGUYÊN số POS365 trả — enum của họ, họ đổi mình không gãy.
    `raw_json` là chứng cứ khi đối chất với quầy — đã lọc trường `Password` của
    Partner ở tầng client trước khi tới đây.
    """

    __tablename__ = "tab_pos_order"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    pos_order_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    pos_code: Mapped[str] = mapped_column(String(50), default="")
    purchase_date: Mapped[str] = mapped_column(String(19), default="", index=True)
    pos_partner_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    points_paid: Mapped[int] = mapped_column(Integer, default=0)
    pos_status: Mapped[int] = mapped_column(Integer, default=0)
    match_status: Mapped[int] = mapped_column(
        SmallInteger, default=int(PosOrderMatchStatus.UNMATCHED))
    is_voided: Mapped[int] = mapped_column(SmallInteger, default=0)
    resolve_note: Mapped[str] = mapped_column(String(500), default="")
    raw_json: Mapped[str] = mapped_column(Text, default="")
    synced_at: Mapped[str] = mapped_column(String(19), default="")

    @property
    def match_status_label(self) -> str:
        return ENUM_LABELS["pos_order_match_status"].get(self.match_status, "")


class PosSyncRun(Base, AuditMixin):
    """Nhật ký mỗi lần đồng bộ (D-05) — "quán kêu thiếu điểm là tra ra trong một phút".

    `created_by` (AuditMixin) = ai bấm chạy tay; `0` = beat tự động.
    `detail` = JSON kết quả (vd bảng lệch của RECONCILE) để màn đối soát đọc.
    """

    __tablename__ = "tab_pos_sync_run"

    kind: Mapped[int] = mapped_column(SmallInteger, index=True)    # PosSyncKind
    status: Mapped[int] = mapped_column(
        SmallInteger, default=int(PosSyncStatus.RUNNING), index=True)
    started_at: Mapped[str] = mapped_column(String(19), default="")
    finished_at: Mapped[str] = mapped_column(String(19), default="")
    cursor_from: Mapped[str] = mapped_column(String(30), default="")
    cursor_to: Mapped[str] = mapped_column(String(30), default="")
    fetched: Mapped[int] = mapped_column(Integer, default=0)
    written: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    detail: Mapped[str] = mapped_column(Text, default="")

    @property
    def kind_label(self) -> str:
        return ENUM_LABELS["pos_sync_kind"].get(self.kind, "")

    @property
    def status_label(self) -> str:
        return ENUM_LABELS["pos_sync_status"].get(self.status, "")
