"""LUỒNG DUYỆT và các BƯỚC của nó (I01–I05, I26).

Bộ máy này **không dành riêng cho văn bản**. `flow.entity` nhận mọi loại chứng
từ — văn bản, YCMH, ĐMH, khảo sát, YCBG, YCTT — và về sau thay được 5 luồng
duyệt viết tay của Thu mua. Vì thế không có cột nào ở đây biết gì về văn bản.

⚠️ Bộ máy mới đứng **CẠNH** mã duyệt cũ, không thay chỗ. Bật/tắt theo từng loại
chứng từ bằng `tab_approval_switch` — tắt là quay về đường duyệt cũ ngay, không
cần deploy. Đó là đường lui của cả phase.
"""
from sqlalchemy import (BigInteger, Boolean, Integer, SmallInteger, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

# ── Vai trò của bước trong quy trình (I02) ──────────────────────────────────
ROLE_PROPOSE = 1   # đề xuất
ROLE_EXECUTE = 2   # thực hiện
ROLE_CHECK = 3     # kiểm tra
ROLE_APPROVE = 4   # phê duyệt

ROLE_LABELS = {
    ROLE_PROPOSE: "Đề xuất",
    ROLE_EXECUTE: "Thực hiện",
    ROLE_CHECK: "Kiểm tra",
    ROLE_APPROVE: "Phê duyệt",
}

# ── Bước làm gì (I15) ───────────────────────────────────────────────────────
NODE_APPROVAL = 1  # phải bấm duyệt mới đi tiếp
NODE_CC = 2        # chỉ nhận thông báo, KHÔNG chặn luồng

NODE_KIND_LABELS = {
    NODE_APPROVAL: "Bước duyệt",
    NODE_CC: "Nhận bản sao",
}

# ── Sáu cách chọn người duyệt (I03) ─────────────────────────────────────────
APPROVER_EMPLOYEE = 1     # người cụ thể            → approver_ref = employee_id
APPROVER_ROLE = 2         # theo vai trò            → approver_ref = mã vai trò
APPROVER_DEPT_HEAD = 3    # trưởng phòng người nộp  → không cần ref
APPROVER_LEVEL_UP = 4     # lên N cấp              → approver_ref = số cấp
APPROVER_COMPANY_REP = 5  # người đại diện pháp nhân → không cần ref
APPROVER_FIELD = 6        # lấy từ một ô trên phiếu → approver_ref = tên cột
#  Trưởng bộ phận của MỘT PHÒNG BAN CỤ THỂ, không phải phòng của người nộp.
#  `approver_ref` = danh sách department_id, ngăn bằng dấu phẩy.
#
#  Vì sao cần: `APPROVER_DEPT_HEAD` luôn bám theo phòng của người trình, nên
#  không khai được những bước có thật như «đơn nghỉ phép của mọi phòng đều phải
#  qua trưởng phòng Nhân sự» hay «hợp đồng qua trưởng phòng Pháp chế». Trước đây
#  muốn thế phải khai đích danh một CON NGƯỜI (`APPROVER_EMPLOYEE`) — người đó
#  đổi vị trí là luồng trỏ sai mà không có gì báo.
APPROVER_DEPT_HEAD_OF = 7

APPROVER_KIND_LABELS = {
    APPROVER_EMPLOYEE: "Người cụ thể",
    APPROVER_ROLE: "Theo vai trò",
    APPROVER_DEPT_HEAD: "Trưởng bộ phận người nộp",
    APPROVER_LEVEL_UP: "Lên N cấp quản lý",
    APPROVER_COMPANY_REP: "Người đại diện pháp nhân",
    APPROVER_FIELD: "Lấy từ một ô trên phiếu",
    APPROVER_DEPT_HEAD_OF: "Trưởng bộ phận của phòng ban chỉ định",
}

# ── Nhiều người trong một bước (I05) ────────────────────────────────────────
MULTI_ANY = 1        # một người duyệt là đủ
MULTI_ALL = 2        # tất cả phải duyệt
MULTI_SEQUENTIAL = 3 # lần lượt theo thứ tự
MULTI_QUORUM = 4     # đủ tỷ lệ

MULTI_MODE_LABELS = {
    MULTI_ANY: "Một người duyệt là đủ",
    MULTI_ALL: "Tất cả phải duyệt",
    MULTI_SEQUENTIAL: "Lần lượt theo thứ tự",
    MULTI_QUORUM: "Đủ tỷ lệ",
}

# ── Trùng người thì bỏ qua (I06) ────────────────────────────────────────────
SKIP_NONE = 0       # không bỏ qua, vẫn bắt bấm
SKIP_ADJACENT = 1   # chỉ bỏ khi trùng bước LIỀN TRƯỚC
SKIP_ANY_BEFORE = 2 # bỏ khi đã duyệt ở bất kỳ bước nào phía trước

SKIP_MODE_LABELS = {
    SKIP_NONE: "Không bỏ qua",
    SKIP_ADJACENT: "Bỏ qua nếu trùng bước liền trước",
    SKIP_ANY_BEFORE: "Bỏ qua nếu đã duyệt ở bước bất kỳ phía trước",
}

# ── Không tìm được người duyệt thì làm gì (I07) ─────────────────────────────
#  ⚠️ CỐ Ý KHÔNG CÓ giá trị "tự động duyệt qua". Lark có tùy chọn đó; với văn
#  bản nó tạo ra văn bản CÓ HIỆU LỰC mà không ai chịu trách nhiệm. Không khai
#  giá trị thì sau này không ai bật nhầm được.
NO_APPROVER_FALLBACK = 1  # chuyển cho người dự phòng khai ở bước
#  ⚠️ ĐÃ BỎ (21/08/2026, CR-114) — giữ hằng số để đọc được dữ liệu cũ, nhưng
#  không còn là lựa chọn khai được và bộ máy KHÔNG chạy nhánh này nữa.
#
#  Vì sao bỏ: "đẩy lên cấp trên" là bộ máy **tự chọn một người khác** thay cho
#  người đã khai trong luồng. Chủ đầu tư chốt: phiếu phải đi đúng luồng đã khai,
#  không có ai thay thế ai. Bước hụt người thì dừng lại và kêu lên — người quản
#  trị sửa luồng, chứ không phải hệ tự đoán hộ.
NO_APPROVER_ESCALATE = 2
NO_APPROVER_BLOCK = 3     # dừng phiếu và báo người quản trị

NO_APPROVER_LABELS = {
    NO_APPROVER_FALLBACK: "Chuyển cho người dự phòng",
    #  Nhãn còn để phiếu/luồng cũ đã khai giá trị 2 vẫn đọc ra chữ, không hiện
    #  số thô. Nó KHÔNG nằm trong danh sách chọn nữa — xem `NO_APPROVER_CHOICES`.
    NO_APPROVER_ESCALATE: "Đẩy lên cấp trên (đã bỏ)",
    NO_APPROVER_BLOCK: "Dừng phiếu và báo quản trị",
}

#  Những lựa chọn CÒN KHAI ĐƯỢC — đây mới là thứ màn khai luồng đổ ra ô chọn.
#  Tách khỏi bảng nhãn ở trên vì hai bảng trả lời hai câu khác nhau: "số này đọc
#  là gì" (phải phủ cả dữ liệu cũ) và "được chọn cái nào" (chỉ cái còn dùng).
NO_APPROVER_CHOICES = (NO_APPROVER_FALLBACK, NO_APPROVER_BLOCK)


class ApprovalFlow(Base, AuditMixin):
    """Một luồng duyệt của một loại chứng từ (I01)."""

    __tablename__ = "tab_approval_flow"
    __table_args__ = (
        UniqueConstraint("entity", "code", "version_no", name="uq_approval_flow_code_version"),
    )

    #  Loại chứng từ: `document`, `purchase_request`, `purchase_order`, …
    #  Cố ý là chuỗi tự do chứ không phải khóa ngoại: bộ máy phải nhận được cả
    #  loại chứng từ chưa tồn tại lúc viết bảng này.
    entity: Mapped[str] = mapped_column(String(50), index=True)
    code: Mapped[str] = mapped_column(String(50), default="")
    name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(String(500), default="")

    #  I21 — tăng mỗi lần sửa luồng. Phiếu đang chạy giữ nguyên bản cũ nhờ
    #  `flow_snapshot`, nên số này chỉ để người dùng đọc và để tra lịch sử.
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    #  Bỏ trống = áp cho mọi pháp nhân. Có giá trị = chỉ pháp nhân đó.
    company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Nhiều luồng cùng một loại chứng từ thì chọn theo `priority` giảm dần rồi
    #  tới điều kiện của từng luồng; luồng nào không khai điều kiện là luồng
    #  mặc định.
    priority: Mapped[int] = mapped_column(Integer, default=0)
    #  Điều kiện chọn luồng, cùng cú pháp với `ApprovalNode.condition`.
    condition: Mapped[str] = mapped_column(Text, default="")


class ApprovalNode(Base, AuditMixin):
    """Một BƯỚC trong luồng (I02–I07)."""

    __tablename__ = "tab_approval_node"
    __table_args__ = (
        UniqueConstraint("flow_id", "seq", "branch_key", name="uq_approval_node_seq"),
    )

    flow_id: Mapped[int] = mapped_column(BigInteger, index=True)
    #  Thứ tự bước, đếm từ 1. Các bước cùng `seq` khác `branch_key` là các NHÁNH
    #  song song của cùng một chặng — đúng một nhánh được chọn lúc chạy.
    seq: Mapped[int] = mapped_column(Integer, default=1)
    branch_key: Mapped[str] = mapped_column(String(50), default="")
    name: Mapped[str] = mapped_column(String(200), default="")

    node_kind: Mapped[int] = mapped_column(SmallInteger, default=NODE_APPROVAL)
    flow_role: Mapped[int] = mapped_column(SmallInteger, default=ROLE_APPROVE)

    approver_kind: Mapped[int] = mapped_column(SmallInteger, default=APPROVER_EMPLOYEE)
    #  Nghĩa của ô này đổi theo `approver_kind` — xem chú thích ở hằng số.
    #  Nhiều người thì ngăn bằng dấu phẩy.
    approver_ref: Mapped[str] = mapped_column(String(300), default="")

    multi_mode: Mapped[int] = mapped_column(SmallInteger, default=MULTI_ANY)
    #  Chỉ dùng khi `multi_mode = MULTI_QUORUM`. 50 nghĩa là quá nửa.
    quorum_percent: Mapped[int] = mapped_column(Integer, default=50)

    #  I04 — điều kiện rẽ nhánh, JSON: [{"field": "total", "op": "gte", "value": 50000000}]
    condition: Mapped[str] = mapped_column(Text, default="")
    #  ⚠️ CỘT CHỐNG MẤT PHIẾU. Không có nhánh mặc định thì phiếu không khớp điều
    #  kiện nào sẽ rơi vào khoảng không: không nhánh nào nhận, biến mất khỏi mọi
    #  danh sách, tới lúc có người đi hỏi mới phát hiện.
    is_default_branch: Mapped[bool] = mapped_column(Boolean, default=False)

    skip_duplicate: Mapped[int] = mapped_column(SmallInteger, default=SKIP_ADJACENT)
    #  I18 — hạn duyệt tính từ lúc việc được giao. 0 = không đặt hạn.
    sla_hours: Mapped[int] = mapped_column(Integer, default=0)

    fallback_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    on_no_approver: Mapped[int] = mapped_column(SmallInteger, default=NO_APPROVER_BLOCK)


class ApprovalSwitch(Base, AuditMixin):
    """I26 — bật/tắt bộ máy mới theo từng loại chứng từ.

    Đây là **đường lui của cả phase 3**. Tắt là mọi chứng từ loại đó quay về
    đường duyệt cũ ngay lập tức, không cần deploy lại. Mặc định TẮT: thêm bảng
    mới không được đổi hành vi của thứ đang chạy.

    Phiếu đã bắt đầu chạy bằng bộ máy mới thì **vẫn chạy tiếp** khi tắt cờ —
    xem `is_running()`. Cắt ngang giữa chừng là bỏ rơi phiếu ở trạng thái không
    màn hình nào nhặt lên.
    """

    __tablename__ = "tab_approval_switch"
    __table_args__ = (UniqueConstraint("entity", name="uq_approval_switch_entity"),)

    entity: Mapped[str] = mapped_column(String(50))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(String(500), default="")
