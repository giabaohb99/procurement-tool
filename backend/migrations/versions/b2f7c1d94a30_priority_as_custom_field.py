"""Công việc: ĐỘ ƯU TIÊN từ cột cứng thành TRƯỜNG TÙY BIẾN của từng dự án.

Trước: `tab_work_task.priority` là SMALLINT 0…4, nhãn P1…P4 gõ cứng trong mã
nguồn nên mọi dự án phải dùng chung bốn bậc, không đổi được tên lẫn màu.

Sau: mỗi list có một dòng `tab_work_label_field` mang `system_key = 'priority'`
kèm bốn giá trị; giá trị cũ của từng task chuyển thành một dòng
`tab_work_task_label`. Từ đó trở đi nó là một trường tùy biến như mọi trường
khác — đổi tên, đổi màu, thêm bậc, xóa hẳn đều được ngay trên giao diện.

Revision ID: b2f7c1d94a30
Revises: 9e357b249200
"""
from alembic import op
import sqlalchemy as sa

revision = "b2f7c1d94a30"
down_revision = "9e357b249200"
branch_labels = None
depends_on = None

#  Bốn bậc cũ. Giữ nguyên tên và màu để bảng nhìn y như trước lúc nâng cấp.
BAC = [
    (1, "P1 — Khẩn", "red"),
    (2, "P2 — Cao", "orange"),
    (3, "P3 — Vừa", "sky"),
    (4, "P4 — Thấp", "slate"),
]


def upgrade() -> None:
    op.add_column("tab_work_label_field",
                  sa.Column("system_key", sa.String(length=30), nullable=False,
                            server_default=""))
    op.create_index("ix_tab_work_label_field_system_key", "tab_work_label_field",
                    ["system_key"])

    conn = op.get_bind()
    lists = conn.execute(sa.text(
        "SELECT id, company_id FROM tab_work_list")).fetchall()

    for list_id, company_id in lists:
        #  Đã có trường ưu tiên (chạy lại migration) thì bỏ qua, đừng tạo trùng.
        san_co = conn.execute(sa.text(
            "SELECT id FROM tab_work_label_field "
            "WHERE list_id = :lid AND system_key = 'priority'"),
            {"lid": list_id}).fetchone()
        if san_co:
            continue

        #  Tên trường phải DUY NHẤT trong list (uq_work_label_field). Dự án nào
        #  đã tự khai một trường tên "Độ ưu tiên" thì đặt tên khác cho trường hệ,
        #  chứ không để migration chết giữa chừng.
        ten = "Độ ưu tiên"
        if conn.execute(sa.text(
                "SELECT id FROM tab_work_label_field WHERE list_id = :lid AND name = :ten"),
                {"lid": list_id, "ten": ten}).fetchone():
            ten = "Độ ưu tiên (hệ thống)"

        conn.execute(sa.text(
            "INSERT INTO tab_work_label_field "
            "(company_id, list_id, name, sort_order, field_type, system_key, "
            " created_by, updated_by, created_at, updated_at) "
            "VALUES (:cid, :lid, :ten, 0, 1, 'priority', 0, 0, NOW(), NOW())"),
            {"cid": company_id or 0, "lid": list_id, "ten": ten})
        field_id = conn.execute(sa.text("SELECT LAST_INSERT_ID()")).scalar()

        option_id = {}
        for muc, ten_bac, mau in BAC:
            conn.execute(sa.text(
                "INSERT INTO tab_work_label_option "
                "(field_id, name, color, sort_order, created_by, updated_by, "
                " created_at, updated_at) "
                "VALUES (:fid, :ten, :mau, :thu_tu, 0, 0, NOW(), NOW())"),
                {"fid": field_id, "ten": ten_bac, "mau": mau, "thu_tu": muc - 1})
            option_id[muc] = conn.execute(sa.text("SELECT LAST_INSERT_ID()")).scalar()

        #  `priority = 0` là "không đặt" — không sinh dòng nào, đúng như một
        #  trường tùy biến chưa chọn giá trị.
        for muc in option_id:
            conn.execute(sa.text(
                "INSERT INTO tab_work_task_label "
                "(task_id, field_id, option_id, value_text, value_date, "
                " created_by, updated_by, created_at, updated_at) "
                "SELECT id, :fid, :oid, '', '', 0, 0, NOW(), NOW() "
                "FROM tab_work_task WHERE list_id = :lid AND priority = :muc"),
                {"fid": field_id, "oid": option_id[muc], "lid": list_id, "muc": muc})

    op.drop_column("tab_work_task", "priority")


def downgrade() -> None:
    op.add_column("tab_work_task",
                  sa.Column("priority", sa.SmallInteger(), nullable=False,
                            server_default="0"))
    conn = op.get_bind()
    #  Trả bậc về cột cũ theo THỨ TỰ của giá trị trong trường (1 = bậc đầu),
    #  vì tên bậc có thể đã được đổi.
    conn.execute(sa.text(
        "UPDATE tab_work_task t "
        "JOIN tab_work_task_label tl ON tl.task_id = t.id "
        "JOIN tab_work_label_field f ON f.id = tl.field_id AND f.system_key = 'priority' "
        "JOIN tab_work_label_option o ON o.id = tl.option_id "
        "SET t.priority = LEAST(o.sort_order + 1, 4)"))
    conn.execute(sa.text(
        "DELETE tl FROM tab_work_task_label tl "
        "JOIN tab_work_label_field f ON f.id = tl.field_id "
        "WHERE f.system_key = 'priority'"))
    conn.execute(sa.text(
        "DELETE o FROM tab_work_label_option o "
        "JOIN tab_work_label_field f ON f.id = o.field_id "
        "WHERE f.system_key = 'priority'"))
    conn.execute(sa.text("DELETE FROM tab_work_label_field WHERE system_key = 'priority'"))
    op.drop_index("ix_tab_work_label_field_system_key", table_name="tab_work_label_field")
    op.drop_column("tab_work_label_field", "system_key")
