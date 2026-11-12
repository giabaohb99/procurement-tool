"""duoc-CR-755: tab_employee_concurrent — kiêm nhiệm thành bảng riêng, cho khác công ty

Revision ID: kn755a
Revises: stix723
Create Date: 2026-11-12

Mỗi dòng = nhân sự kiêm nhiệm (công ty, phòng, chức vụ, từ ngày, đến ngày, số/ngày quyết định,
ghi chú, công tắc "tính vào phạm vi quyền"). Bảng `tab_employee_department` từ nay CHỈ còn dòng
phòng CHÍNH; dòng phụ (`is_primary = 0`) được CHÉP sang bảng mới rồi xóa khỏi bảng cũ.

VIẾT TAY, không autogenerate — repo này autogenerate trôi ~650 dòng mỗi lần.

Dòng chép từ dữ liệu cũ: công ty = công ty CHÍNH của nhân sự, `from_date`/`to_date` trống (đã có hiệu
lực từ trước, chưa kết thúc), công tắc phạm vi BẬT (giữ nguyên hành vi CR-167), không chức vụ/quyết
định, ghi chú `Chuyển từ kiêm nhiệm cũ`. Chữ tiếng Việt đi qua tham số bind, không qua `mysql -e`.
Chạy lại được: chỉ chép khi chưa có dòng cho cùng (nhân sự, phòng, công ty); bảng đã có thì không tạo lại.
Dòng phụ trùng phòng chính (dữ liệu lệch) không chép — chỉ bị xóa.

⚠️ downgrade: chép lại dòng ĐANG HIỆU LỰC cùng công ty chính về `tab_employee_department`
(`is_primary = 0`, bỏ trùng), rồi bỏ bảng. Dòng KHÁC công ty, ngày, quyết định, tệp quyết định
(`FileLink` entity `employee_concurrent`, để lại trong kho) sẽ mất — sao lưu bảng trước khi hạ.
"""
from datetime import datetime, timedelta
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "kn755a"
down_revision: Union[str, None] = "stix723"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_employee_concurrent"
MIGRATED_NOTE = "Chuyển từ kiêm nhiệm cũ"


def upgrade() -> None:
    bind = op.get_bind()
    if TABLE not in sa.inspect(bind).get_table_names():
        op.create_table(
            TABLE,
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("employee_id", sa.BigInteger(), nullable=False),
            sa.Column("company_id", sa.BigInteger(), nullable=False),
            sa.Column("department_id", sa.BigInteger(), nullable=False),
            sa.Column("position_id", sa.BigInteger(), nullable=False, server_default="0"),
            # Nhãn CHỤP lúc ghi — khớp String(100) của tab_employee.position.
            sa.Column("position_label", sa.String(100), nullable=False, server_default=""),
            # NULL chỉ ở dòng chép từ dữ liệu cũ; dòng tạo mới luôn có từ ngày.
            sa.Column("from_date", sa.Date(), nullable=True),
            sa.Column("to_date", sa.Date(), nullable=True),
            sa.Column("decision_no", sa.String(50), nullable=False, server_default=""),
            sa.Column("decision_date", sa.Date(), nullable=True),
            sa.Column("note", sa.String(500), nullable=False, server_default=""),
            sa.Column("counts_scope", sa.Boolean(), nullable=False, server_default=sa.true()),
            # Dòng quá trình công tác đã Áp ra dòng này (giai đoạn 03); 0 = nhập tay.
            sa.Column("work_history_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_employee_concurrent_employee", TABLE, ["employee_id"])
        op.create_index("ix_employee_concurrent_dept_company", TABLE, ["department_id", "company_id"])
        op.create_index("ix_employee_concurrent_work_history", TABLE, ["work_history_id"])

    # Chép dòng phụ cũ. NOT EXISTS để chạy lại không nhân đôi.
    bind.execute(sa.text(
        "INSERT INTO tab_employee_concurrent "
        "  (employee_id, company_id, department_id, counts_scope, note, created_at, created_by, "
        "   updated_at, updated_by) "
        "SELECT ed.employee_id, COALESCE(e.company_id, 0), ed.department_id, :on, :note, "
        "       ed.created_at, ed.created_by, ed.updated_at, ed.updated_by "
        "FROM tab_employee_department ed "
        "JOIN tab_employee e ON e.id = ed.employee_id "
        "WHERE ed.is_primary = :off AND ed.department_id <> COALESCE(e.department_id, 0) "
        "  AND NOT EXISTS (SELECT 1 FROM tab_employee_concurrent c "
        "                  WHERE c.employee_id = ed.employee_id AND c.department_id = ed.department_id "
        "                    AND c.company_id = COALESCE(e.company_id, 0))"
    ), {"on": True, "off": False, "note": MIGRATED_NOTE})
    bind.execute(sa.text("DELETE FROM tab_employee_department WHERE is_primary = :off"), {"off": False})


def downgrade() -> None:
    bind = op.get_bind()
    today = (datetime.utcnow() + timedelta(hours=7)).date()
    # Chỉ dòng đang hiệu lực + cùng công ty chính + công tắc "Tính vào phạm vi quyền" BẬT mới có chỗ trong mô hình
    # cũ; bỏ trùng theo (nhân sự, phòng). Mô hình cũ coi MỌI dòng phụ là mở phạm vi, nên dòng đã tắt công tắc mà
    # chép về là hạ cấp nới quyền âm thầm — bỏ qua chúng (không có chỗ lưu "ghi nhận nhưng không mở quyền").
    bind.execute(sa.text(
        "INSERT INTO tab_employee_department (employee_id, department_id, is_primary, created_by, updated_by) "
        "SELECT c.employee_id, c.department_id, :off, 0, 0 "
        "FROM tab_employee_concurrent c "
        "JOIN tab_employee e ON e.id = c.employee_id "
        "WHERE c.company_id = COALESCE(e.company_id, 0) AND c.department_id <> COALESCE(e.department_id, 0) "
        "  AND c.counts_scope = :on "
        "  AND (c.from_date IS NULL OR c.from_date <= :today) AND (c.to_date IS NULL OR c.to_date >= :today) "
        "  AND NOT EXISTS (SELECT 1 FROM tab_employee_department d "
        "                  WHERE d.employee_id = c.employee_id AND d.department_id = c.department_id) "
        "GROUP BY c.employee_id, c.department_id"
    ), {"off": False, "on": True, "today": today})
    op.drop_index("ix_employee_concurrent_work_history", table_name=TABLE)
    op.drop_index("ix_employee_concurrent_dept_company", table_name=TABLE)
    op.drop_index("ix_employee_concurrent_employee", table_name=TABLE)
    op.drop_table(TABLE)
