"""ho_so_nhan_su_mo_rong — HRM Đợt 1: mở rộng hồ sơ nhân sự + 2 bảng con

Thiết kế: `doc/erp/hrm/01-ho-so-nhan-su.md`.

⚠️ **Tệp này được CẮT TAY.** `alembic --autogenerate` trên máy local quét ra thêm
một đống thay đổi KHÔNG thuộc đợt này (bảng diễn đàn, cột phân bổ của Yêu cầu
thanh toán, một loạt `NOT NULL` của mailbox/ticket/vehicle…) — đó là độ lệch tích
lũy giữa model và database local, không phải việc của migration này. Gộp chúng
vào đây là để một migration mang tên "hồ sơ nhân sự" âm thầm sửa cấu trúc của
bốn phân hệ khác trên hệ thật. Đã bỏ hết, chỉ giữ đúng phần hồ sơ nhân sự.

Revision ID: a3f8e9d62714
Revises: 6835fb9cfecd
Create Date: 2026-09-08 01:44:31.471782
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3f8e9d62714'
down_revision: Union[str, None] = '6835fb9cfecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


#  (tên cột, kiểu, cho phép NULL). Cột chữ đặt `server_default=""` chứ không để
#  NULL: hàng trăm dòng đang có sẽ được điền chuỗi rỗng ngay lúc ALTER, nên tầng
#  đọc không phải thêm nhánh `or ""` ở ba mươi chỗ. Cột NGÀY thì ngược lại —
#  không có ngày mặc định nào đúng, và `0000-00-00` của MySQL là một cái bẫy.
_TEXT_COLUMNS = [
    # Nhóm 1 — cá nhân
    ("place_of_birth", sa.String(255)),
    ("ethnicity", sa.String(50)),
    ("religion", sa.String(50)),
    ("personal_email", sa.String(255)),
    ("tax_code", sa.String(20)),
    ("major", sa.String(255)),
    # Nhóm 2 — công việc
    ("work_location", sa.String(255)),
    # Nhóm 3 — liên hệ
    ("permanent_address", sa.String(500)),
    ("current_address", sa.String(500)),
    # Nhóm 4 — ngân hàng
    ("bank_account_no", sa.String(50)),
    ("bank_account_name", sa.String(255)),
    ("bank_name", sa.String(100)),
    ("bank_branch", sa.String(255)),
    # Nhóm 5 — giấy tờ, BHXH/BHYT
    ("id_number", sa.String(20)),
    ("id_issue_place", sa.String(255)),
    ("id_front_image", sa.String(500)),
    ("id_back_image", sa.String(500)),
    ("social_insurance_no", sa.String(20)),
    ("health_care_place", sa.String(255)),
    ("health_care_code", sa.String(20)),
]

#  Cột MÃ SỐ — `0` luôn nghĩa là CHƯA KHAI (xem `employee/constants.py`), nên
#  `server_default="0"` là giá trị đúng cho mọi dòng cũ, không phải một phỏng đoán.
_SMALLINT_COLUMNS = ["marital_status", "children_count", "education_level",
                     "employment_type", "job_level"]

_DATE_COLUMNS = ["date_of_birth", "resign_date", "id_issue_date", "id_expiry_date"]


def upgrade() -> None:
    for name, coltype in _TEXT_COLUMNS:
        op.add_column("tab_employee",
                      sa.Column(name, coltype, nullable=False, server_default=""))
    for name in _SMALLINT_COLUMNS:
        op.add_column("tab_employee",
                      sa.Column(name, sa.SmallInteger(), nullable=False, server_default="0"))
    for name in _DATE_COLUMNS:
        op.add_column("tab_employee", sa.Column(name, sa.Date(), nullable=True))

    #  Người quản lý TRỰC TIẾP. `0` = chưa gán. CỐ Ý KHÔNG khai khóa ngoại trỏ
    #  vào chính `tab_employee.id`: FK tự trỏ khiến mọi lần xóa hồ sơ phải chờ
    #  database phân xử thứ tự, mà `0` (chưa gán) thì không phải một id hợp lệ
    #  nên FK sẽ chặn ngay dòng đầu tiên. Việc dọn khi xóa làm ở tầng dịch vụ
    #  (`service.delete_employee` gỡ `manager_id` về 0).
    op.add_column("tab_employee",
                  sa.Column("manager_id", sa.BigInteger(), nullable=False, server_default="0"))
    op.create_index("ix_tab_employee_manager_id", "tab_employee", ["manager_id"])

    #  Ô tùy biến. `nullable=True` vì JSON trong MySQL 8 KHÔNG nhận
    #  `server_default` — dòng cũ mang NULL, và `Employee.extra_fields_map` đọc
    #  NULL thành `{}`.
    op.add_column("tab_employee", sa.Column("extra_fields", sa.JSON(), nullable=True))

    op.create_table(
        "tab_employee_contact",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("relation", sa.String(50), nullable=False, server_default=""),
        sa.Column("address", sa.String(500), nullable=False, server_default=""),
        sa.Column("phone", sa.String(25), nullable=False, server_default=""),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["employee_id"], ["tab_employee.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_employee_contact_employee_id", "tab_employee_contact",
                    ["employee_id"])

    op.create_table(
        "tab_employee_family",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("relation", sa.String(50), nullable=False, server_default=""),
        sa.Column("gender", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(25), nullable=False, server_default=""),
        sa.Column("id_number", sa.String(20), nullable=False, server_default=""),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["employee_id"], ["tab_employee.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_employee_family_employee_id", "tab_employee_family",
                    ["employee_id"])


def downgrade() -> None:
    op.drop_table("tab_employee_family")
    op.drop_table("tab_employee_contact")
    op.drop_index("ix_tab_employee_manager_id", table_name="tab_employee")
    for name in (["manager_id", "extra_fields"] + _DATE_COLUMNS + _SMALLINT_COLUMNS
                 + [c[0] for c in _TEXT_COLUMNS]):
        op.drop_column("tab_employee", name)
