"""CR-157: tách khóa quyền Văn thư theo màn hình, kế thừa từ doc_type

Bốn màn danh mục của Văn thư trước đây dùng CHUNG khóa `doc_type`, nên không tách
được ba nhóm việc khác nhau (khai loại văn bản · khai quy tắc đánh số · khai quy
tắc quan hệ). Nay mỗi màn một khóa:

    doc_type            → Thiết lập ▸ Loại văn bản          (giữ nguyên)
    doc_template        → Thiết lập ▸ Thư viện văn bản mẫu  (mới)
    doc_numbering_rule  → Quy tắc đánh số                   (mới)
    doc_link_rule       → Quy tắc quan hệ                   (mới)

⚠️ **Migration này CHÉP quyền, không đặt lại quyền.** Vai trò đang có `doc_type`
sẽ nhận đúng bộ cờ đó trên cả ba khóa mới. Không chép thì deploy xong người đang
khai báo văn thư mất quyền vào ba màn cho tới khi quản trị tick lại tay — và họ
sẽ không biết vì sao, vì màn hình không đổi gì.

Không dùng `SEED_FORCE_SYNC=true` cho việc này: cờ đó ghi đè theo `STD_ROLES`,
tức là xóa luôn mọi chỉnh tay khác trên màn Phân quyền.

Chạy lại được nhiều lần: chỉ chèn khóa nào vai trò CHƯA có.

Revision ID: e7c3a91d55b2
Revises: d4b21f7e8a35
"""
from alembic import op
import sqlalchemy as sa

revision = "e7c3a91d55b2"
down_revision = "d4b21f7e8a35"
branch_labels = None
depends_on = None

#  Ba khóa mới, tất cả kế thừa từ `doc_type` — đó chính là khóa đã gác chúng
#  trước hôm nay, nên chép sang là giữ nguyên hiện trạng.
KHOA_MOI = ("doc_template", "doc_numbering_rule", "doc_link_rule")

CO = ("can_read", "can_create", "can_write", "can_delete",
      "can_approve", "can_cancel", "can_print", "can_export")

#  `tab_permission` mang `AuditMixin`: `created_by` / `updated_by` là NOT NULL và
#  KHÔNG có giá trị mặc định ở tầng CSDL. Chép luôn của dòng nguồn để dòng mới
#  mang đúng dấu vết «ai đã dựng bộ quyền này», thay vì một số 0 vô danh.
COT_DAU_VET = ("created_by", "updated_by")


def upgrade() -> None:
    conn = op.get_bind()
    chep = (*CO, *COT_DAU_VET)
    nguon = conn.execute(sa.text(
        f"SELECT role_id, scope, {', '.join(chep)} FROM tab_permission WHERE entity = 'doc_type'"
    )).mappings().all()
    if not nguon:
        return

    da_co = {
        (row["role_id"], row["entity"])
        for row in conn.execute(sa.text(
            "SELECT role_id, entity FROM tab_permission WHERE entity IN :ds"
        ).bindparams(sa.bindparam("ds", expanding=True)), {"ds": list(KHOA_MOI)}).mappings()
    }

    cot = ", ".join(chep)
    tham_so = ", ".join(f":{ten}" for ten in chep)
    for row in nguon:
        for entity in KHOA_MOI:
            if (row["role_id"], entity) in da_co:
                continue
            conn.execute(
                sa.text(
                    f"INSERT INTO tab_permission (role_id, entity, scope, {cot}) "
                    f"VALUES (:role_id, :entity, :scope, {tham_so})"
                ),
                {"role_id": row["role_id"], "entity": entity, "scope": row["scope"],
                 **{ten: row[ten] for ten in chep}},
            )


def downgrade() -> None:
    #  Gỡ sạch ba khóa mới. An toàn vì trước migration này chúng không tồn tại:
    #  không có chỉnh tay nào của quản trị nằm ở đây để mà mất.
    op.get_bind().execute(
        sa.text("DELETE FROM tab_permission WHERE entity IN :ds").bindparams(
            sa.bindparam("ds", expanding=True)),
        {"ds": list(KHOA_MOI)},
    )
