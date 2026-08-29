"""Công việc: TAG từ bảng riêng thành một TRƯỜNG TÙY BIẾN kiểu chọn nhiều.

Trước: `tab_work_tag` + `tab_work_task_tag` là hai bảng riêng phục vụ đúng một
trường. Mọi việc đụng tới trường ấy — vẽ trên thẻ, ô nhập ở panel chi tiết, lọc,
sắp xếp, hộp sửa danh mục — đều phải viết hai lần: một bản cho tag, một bản cho
trường tùy biến. Hai bản đó đã bắt đầu lệch nhau (bút chì ở menu «Tùy chỉnh» mở
ra hai giao diện khác hẳn).

Sau: mỗi list có một dòng `tab_work_label_field` tên "Tag", `field_type = 2`
(chọn nhiều) và `system_key` RỖNG — tức là một trường tùy biến bình thường, đổi
tên · đổi bộ giá trị · xóa hẳn đều được. Tag cũ thành `tab_work_label_option`,
mỗi dòng `tab_work_task_tag` thành một dòng `tab_work_task_label`.

⚠️ `downgrade` dựng LẠI hai bảng nhưng **không chép dữ liệu về**: sau khi nâng
cấp, trường "Tag" không còn gì phân biệt với trường do người dùng tự khai (cố ý
— đó chính là mục đích), nên không có mốc nào để lần ngược cho đúng.

Revision ID: c8a1d4f60b72
Revises: b2f7c1d94a30
"""
from alembic import op
import sqlalchemy as sa

revision = "c8a1d4f60b72"
down_revision = "b2f7c1d94a30"
branch_labels = None
depends_on = None

#  `WorkLabelFieldType.MULTI` — một task gắn được nhiều tag, y như trước.
MULTI = 2


def upgrade() -> None:
    conn = op.get_bind()
    #  MỌI list, kể cả list chưa khai tag nào: trường "Tag" là thứ dự án nào
    #  cũng được nạp sẵn (`seed_system_label_fields`), chỉ là bộ giá trị rỗng.
    #  Bỏ qua chúng thì dự án cũ thiếu hẳn trường mà dự án mới lại có.
    lists = conn.execute(sa.text(
        "SELECT id, company_id FROM tab_work_list")).fetchall()

    for list_id, company_id in lists:

        #  Tên trường phải DUY NHẤT trong list (uq_work_label_field). Dự án nào
        #  đã tự khai một trường tên "Tag" thì đặt tên khác, chứ không để
        #  migration chết giữa chừng.
        ten = "Tag"
        if conn.execute(sa.text(
                "SELECT id FROM tab_work_label_field WHERE list_id = :lid AND name = :ten"),
                {"lid": list_id, "ten": ten}).fetchone():
            ten = "Tag (cũ)"

        thu_tu = conn.execute(sa.text(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM tab_work_label_field "
            "WHERE list_id = :lid"), {"lid": list_id}).scalar()

        conn.execute(sa.text(
            "INSERT INTO tab_work_label_field "
            "(company_id, list_id, name, sort_order, field_type, system_key, "
            " created_by, updated_by, created_at, updated_at) "
            "VALUES (:cid, :lid, :ten, :thu_tu, :kieu, '', 0, 0, NOW(), NOW())"),
            {"cid": company_id or 0, "lid": list_id, "ten": ten,
             "thu_tu": thu_tu or 0, "kieu": MULTI})
        field_id = conn.execute(sa.text("SELECT LAST_INSERT_ID()")).scalar()

        tags = conn.execute(sa.text(
            "SELECT id, name, color, sort_order FROM tab_work_tag "
            "WHERE list_id = :lid ORDER BY sort_order, id"), {"lid": list_id}).fetchall()

        for thu_tu_tag, (tag_id, ten_tag, mau, _) in enumerate(tags):
            conn.execute(sa.text(
                "INSERT INTO tab_work_label_option "
                "(field_id, name, color, sort_order, created_by, updated_by, "
                " created_at, updated_at) "
                "VALUES (:fid, :ten, :mau, :thu_tu, 0, 0, NOW(), NOW())"),
                {"fid": field_id, "ten": ten_tag, "mau": mau or "",
                 "thu_tu": thu_tu_tag})
            option_id = conn.execute(sa.text("SELECT LAST_INSERT_ID()")).scalar()

            #  Chỉ chép tag của việc CÒN SỐNG trong đúng list này: `tab_work_tag`
            #  và task đều trỏ về list, nhưng dữ liệu cũ có thể còn dòng mồ côi.
            conn.execute(sa.text(
                "INSERT INTO tab_work_task_label "
                "(task_id, field_id, option_id, value_text, value_date, "
                " created_by, updated_by, created_at, updated_at) "
                "SELECT tt.task_id, :fid, :oid, '', '', 0, 0, NOW(), NOW() "
                "FROM tab_work_task_tag tt "
                "JOIN tab_work_task t ON t.id = tt.task_id AND t.list_id = :lid "
                "WHERE tt.tag_id = :tag_id"),
                {"fid": field_id, "oid": option_id, "lid": list_id, "tag_id": tag_id})

    #  Bảng nối trước, bảng gốc sau — ngược lại là vướng khóa ngoại.
    op.drop_table("tab_work_task_tag")
    op.drop_table("tab_work_tag")


def downgrade() -> None:
    op.create_table(
        "tab_work_tag",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("list_id", sa.BigInteger(),
                  sa.ForeignKey("tab_work_list.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("color", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("sort_order", sa.BigInteger(), nullable=False, server_default="0"),
        sa.UniqueConstraint("list_id", "name", name="uq_work_tag_name"),
    )
    op.create_index("ix_tab_work_tag_company_id", "tab_work_tag", ["company_id"])
    op.create_index("ix_tab_work_tag_list_id", "tab_work_tag", ["list_id"])

    op.create_table(
        "tab_work_task_tag",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("task_id", sa.BigInteger(),
                  sa.ForeignKey("tab_work_task.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.BigInteger(),
                  sa.ForeignKey("tab_work_tag.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("task_id", "tag_id", name="uq_work_task_tag"),
    )
    op.create_index("ix_tab_work_task_tag_task_id", "tab_work_task_tag", ["task_id"])
    op.create_index("ix_tab_work_task_tag_tag_id", "tab_work_task_tag", ["tag_id"])
