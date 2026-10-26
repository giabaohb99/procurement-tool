"""duoc-CR-681 — phiếu đặt xe lưu thêm pháp nhân của NGƯỜI TẠO (`requester_company_id`).

Phiếu chọn công ty khác công ty mình (hai ô độc lập) thì người phạm vi «Công ty» ở CẢ HAI bên đều phải
thấy phiếu: `core/scoping` khớp `company_id` HOẶC `requester_company_id` (`company_alt`). Chụp lúc tạo,
không suy động từ hồ sơ — người tạo chuyển công ty sau đó thì phiếu cũ không đổi người thấy.

Lấp dữ liệu cũ: pháp nhân trên hồ sơ của tài khoản người tạo; không lần ra thì lấy `company_id` của phiếu.

Revision ID: cr681vbrqco01
Revises: cr676chgreq01
"""
import sqlalchemy as sa
from alembic import op

revision = "cr681vbrqco01"
down_revision = "cr676chgreq01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tab_vehicle_booking", sa.Column("requester_company_id", sa.BigInteger(), nullable=False,
                                                   server_default="0"))
    op.create_index("ix_tab_vehicle_booking_requester_company_id", "tab_vehicle_booking", ["requester_company_id"])
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        op.execute("""
            UPDATE tab_vehicle_booking b
            JOIN tab_user u ON u.id = b.requester_id
            JOIN tab_employee e ON e.id = u.employee_id
            SET b.requester_company_id = e.company_id
            WHERE e.company_id > 0
        """)
    op.execute("UPDATE tab_vehicle_booking SET requester_company_id = company_id WHERE requester_company_id = 0")


def downgrade():
    op.drop_index("ix_tab_vehicle_booking_requester_company_id", table_name="tab_vehicle_booking")
    op.drop_column("tab_vehicle_booking", "requester_company_id")
