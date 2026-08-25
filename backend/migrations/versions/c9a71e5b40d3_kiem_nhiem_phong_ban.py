"""CR-167: tab_employee_department — nhân sự kiêm nhiệm nhiều phòng ban

`tab_employee.department_id` là MỘT số, nên người kiêm nhiệm hai bộ phận chỉ khai
được một. Hệ quả nằm ở phạm vi dữ liệu: vai trò phạm vi *phòng ban* mở đúng một
phòng ghi trên hồ sơ.

Bảng này **cộng thêm, không thay thế**. `tab_employee.department_id` vẫn còn và
vẫn là PHÒNG CHÍNH (12 chỗ trong mã đang đọc nó); dòng `is_primary` luôn khớp với
cột đó.

Điền lùi: mỗi nhân sự ĐANG có `department_id` được một dòng `is_primary = 1`.
Người chưa gắn phòng thì không sinh dòng nào — họ vẫn chưa thuộc phòng nào, đúng
hiện trạng.

⚠️ `downgrade` chỉ xóa bảng. Phần kiêm nhiệm khai thêm sau migration này sẽ mất,
còn phòng chính thì không — nó nằm ở `tab_employee.department_id`, không đụng tới.

Revision ID: c9a71e5b40d3
Revises: a4c8e1f9d2b7
"""
from alembic import op
import sqlalchemy as sa

revision = "c9a71e5b40d3"
down_revision = "a4c8e1f9d2b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tab_employee_department",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("department_id", sa.BigInteger(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "department_id", name="uq_employee_department"),
    )
    op.create_index("ix_employee_department_employee", "tab_employee_department",
                    ["employee_id"])
    op.create_index("ix_employee_department_department", "tab_employee_department",
                    ["department_id"])

    #  ĐIỀN LÙI. Chỉ nhân sự đã gắn phòng; `department_id = 0` nghĩa là chưa
    #  phân công, sinh một dòng trỏ vào phòng số 0 là tạo rác.
    op.get_bind().execute(sa.text(
        "INSERT INTO tab_employee_department "
        "  (employee_id, department_id, is_primary, created_by, updated_by) "
        "SELECT id, department_id, 1, 0, 0 FROM tab_employee "
        "WHERE department_id IS NOT NULL AND department_id > 0"
    ))


def downgrade() -> None:
    op.drop_index("ix_employee_department_department", table_name="tab_employee_department")
    op.drop_index("ix_employee_department_employee", table_name="tab_employee_department")
    op.drop_table("tab_employee_department")
