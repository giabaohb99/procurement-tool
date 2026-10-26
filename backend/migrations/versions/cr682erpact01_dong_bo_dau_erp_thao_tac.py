"""duoc-CR-682 — Bước 0 đồng bộ app cũ: dấu `erp_action_at` trên phiếu đặt xe và phiếu duyệt dấu.

«ERP đã đụng vào phiếu gốc app cũ lúc…» — có dấu thì chiều nhận không chép đè nữa (`legacy_datxe/erp_ownership.py`).

LẤP DẤU cho phiếu ERP đã thao tác TRƯỚC migration (review M2 — không lấp thì lượt quét 02:15 đêm deploy vẫn kéo lùi
chúng): phiếu có `legacy_id` mà nhật ký thao tác có dòng của NGƯỜI DÙNG (`actor_kind = 1`), trừ thao tác chỉ đọc.
Dòng nhập từ app cũ mang `actor_kind = 3` (script), lượt đồng bộ ghi bằng tài khoản hệ thống — không lọt vào đây.
Dòng cũ trước khi có `actor_kind` (= 0) không tính: không đoán.

Revision ID: cr682erpact01
Revises: cr681vbrqco01
"""
import sqlalchemy as sa
from alembic import op

revision = "cr682erpact01"
down_revision = "cr681vbrqco01"
branch_labels = None
depends_on = None

_TABLES = {"tab_vehicle_booking": "vehicle_booking", "tab_seal_request": "seal_request"}
_READ_ONLY_ACTIONS = ("view", "print", "export", "download")


def upgrade():
    for table in _TABLES:
        op.add_column(table, sa.Column("erp_action_at", sa.String(20), nullable=False, server_default=""))
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    actions = ", ".join(f"'{a}'" for a in _READ_ONLY_ACTIONS)
    for table, entity in _TABLES.items():
        op.execute(f"""
            UPDATE {table} t
            JOIN (
                SELECT a.entity_id, DATE_FORMAT(MAX(a.created_at), '%Y-%m-%dT%H:%i:%s') AS last_at
                FROM tab_audit_log a
                WHERE a.entity = '{entity}' AND a.actor_kind = 1 AND a.action NOT IN ({actions})
                GROUP BY a.entity_id
            ) x ON x.entity_id = t.id
            SET t.erp_action_at = x.last_at
            WHERE t.legacy_id <> '' AND t.erp_action_at = ''
        """)


def downgrade():
    for table in _TABLES:
        op.drop_column(table, "erp_action_at")
