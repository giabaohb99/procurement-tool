"""them nspt_id (DMH) + head_of_dept_id (YCBG) va dien lui theo ten — CR-087

Nối tiếp CR-086 nhưng cho chiều NHÂN SỰ. Chỗ hỏng thật: `apply_scope` của ĐMH khớp
`nspt == ten_nhan_su`, mà `tab_employee.full_name` KHÔNG duy nhất — hai người trùng tên
là thấy đơn của nhau, không lỗi, không log.

Điền lùi hai lượt, y hệt CR-086: khớp `(tên, pháp nhân)` trước rồi mới tới tên duy nhất
toàn cục. TRÙNG TÊN KHÔNG PHÂN GIẢI ĐƯỢC THÌ ĐỂ 0 — giữ chuỗi tên và chạy đường lùi
trong `scoping._emp_match`, không đoán bừa vì đoán sai ở đây là trao nhầm quyền xem đơn.

CẤM `raise`: `start.prod.sh` chạy `alembic upgrade head` lúc khởi động, migration chết là
api không lên → prod 502. Dòng không khớp chỉ được ĐẾM và IN ra.

Đảo một quyết định của CR-071: hồi đó CỐ Ý không điền lùi `tab_purchase_request.head_of_dept_id`
từ chuỗi tên vì id đó đang định đoạt QUYỀN DUYỆT. Khách đã bác phần chặn duyệt ngay trong
CR-071, nên nay ô TBP chỉ còn để lưu + in — điền lùi theo tên DUY NHẤT là vô hại, và không
điền thì N-008 không xóa được cột chuỗi.

Revision ID: d5b2f9c31a08
Revises: c4e8b1a7d260
Create Date: 2026-08-18
"""
from alembic import op
import sqlalchemy as sa

revision = "d5b2f9c31a08"
down_revision = "c4e8b1a7d260"
branch_labels = None
depends_on = None

# (bảng, cột id, cột tên, có đánh index không)
_REFS = (
    ("tab_purchase_order", "nspt_id", "nspt", True),
    ("tab_survey_request", "head_of_dept_id", "head_of_dept", False),
    ("tab_purchase_request", "head_of_dept_id", "head_of_dept", False),
)


def _backfill_nspt_qua_ycmh(bind) -> None:
    """Lượt 3, CHỈ cho ĐMH: đơn còn kẹt vì TRÙNG TÊN thì hỏi YCMH nguồn.

    Dòng YCMH ghi người phụ trách bằng MÃ nhân sự (`tab_employee.code` là UNIQUE) nên ở đây
    có bằng chứng thật, không phải suy đoán: lấy người phụ trách của YCMH nguồn, và CHỈ điền
    khi tên người đó khớp đúng chuỗi `nspt` đang lưu, đồng thời cả phiếu chỉ suy ra ĐÚNG MỘT
    người. Chính những dòng trùng tên này là chỗ đang rò quyền, nên đáng thêm một lượt.
    """
    bind.execute(sa.text("""
        UPDATE tab_purchase_order po
          JOIN (SELECT pr.code pcode, TRIM(e.full_name) nm, MIN(e.id) eid
                  FROM tab_purchase_request pr
                  JOIN tab_purchase_request_item pri ON pri.pr_id = pr.id
                  JOIN tab_employee e ON e.code = TRIM(pri.assignee)
                 WHERE TRIM(pri.assignee) <> ''
                 GROUP BY pr.code, TRIM(e.full_name)
                HAVING COUNT(DISTINCT e.id) = 1) u
            ON u.pcode = po.pr_code AND u.nm = TRIM(po.nspt)
           SET po.nspt_id = u.eid
         WHERE po.nspt_id = 0 AND TRIM(po.nspt) <> ''
    """))


def _backfill(bind, table: str, col_id: str, col_name: str) -> None:
    # Lượt 1: trùng tên nhưng khác pháp nhân → pháp nhân phân giải giúp.
    bind.execute(sa.text(f"""
        UPDATE {table} t
          JOIN (SELECT TRIM(e.full_name) nm, e.company_id cid, MIN(e.id) eid
                  FROM tab_employee e
                 GROUP BY TRIM(e.full_name), e.company_id HAVING COUNT(*) = 1) u
            ON u.nm = TRIM(t.{col_name}) AND u.cid = t.company_id
           SET t.{col_id} = u.eid
         WHERE t.{col_id} = 0 AND TRIM(t.{col_name}) <> ''
    """))
    # Lượt 2: tên duy nhất trên toàn hệ → không cần pháp nhân.
    bind.execute(sa.text(f"""
        UPDATE {table} t
          JOIN (SELECT TRIM(e.full_name) nm, MIN(e.id) eid
                  FROM tab_employee e
                 GROUP BY TRIM(e.full_name) HAVING COUNT(*) = 1) u
            ON u.nm = TRIM(t.{col_name})
           SET t.{col_id} = u.eid
         WHERE t.{col_id} = 0 AND TRIM(t.{col_name}) <> ''
    """))
    if table == "tab_purchase_order":
        _backfill_nspt_qua_ycmh(bind)
    named = bind.execute(sa.text(
        f"SELECT COUNT(*) FROM {table} WHERE TRIM({col_name}) <> ''")).scalar() or 0
    left = bind.execute(sa.text(
        f"SELECT COUNT(*) FROM {table} "
        f"WHERE {col_id} = 0 AND TRIM({col_name}) <> ''")).scalar() or 0
    print(f"[CR-087] {table}.{col_name}: {named - left}/{named} dong co ten da dien duoc id; "
          f"{left} dong khong suy ra duoc (giu ten, {col_id} = 0)")


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tab_purchase_request")}

    for table, col_id, col_name, indexed in _REFS:
        if table == "tab_purchase_request" and col_id in cols:
            continue        # đã có từ CR-071 (migration a1c7f4d92e63) — chỉ điền lùi
        op.add_column(table, sa.Column(col_id, sa.BigInteger(), nullable=False,
                                       server_default="0"))
        if indexed:
            op.create_index(op.f(f"ix_{table}_{col_id}"), table, [col_id])

    # Cặp trùng tên là NGUỒN của lỗi đang có — in ra để còn biết đường xử tay.
    dup = bind.execute(sa.text("""
        SELECT TRIM(full_name), COUNT(*) FROM tab_employee
         GROUP BY TRIM(full_name) HAVING COUNT(*) > 1
    """)).fetchall()
    print(f"[CR-087] tab_employee: {len(dup)} ten bi trung "
          + (f"({', '.join(f'{r[0]} x{r[1]}' for r in dup)})" if dup else ""))

    for table, col_id, col_name, _ in _REFS:
        _backfill(bind, table, col_id, col_name)


def downgrade() -> None:
    op.drop_index(op.f("ix_tab_purchase_order_nspt_id"), table_name="tab_purchase_order")
    op.drop_column("tab_purchase_order", "nspt_id")
    op.drop_column("tab_survey_request", "head_of_dept_id")
    # `tab_purchase_request.head_of_dept_id` do CR-071 tạo — không xóa ở đây.
