"""avatar: chuyển tab_user.avatar (URL chuỗi) sang avatar_file_id (tab_file.id)

Ảnh đại diện giờ là 1 file trong hệ thống (tab_file) thay vì URL rời, để:
- chỉ còn MỘT nguồn ảnh (kể cả ảnh Google cũng tải hẳn về storage),
- đổi ảnh thì xóa được file cũ (hết ảnh mồ côi trên R2).

Backfill: ảnh R2/local NỘI BỘ (key có '/avatar/') → tạo dòng tab_file trỏ tới.
Ảnh Google (URL ngoài) không tải được ở đây → để nguyên, lần đăng nhập Google kế
tiếp `sync_google_avatar` sẽ tự tải về.

Revision ID: a3f7c012e9b5
Revises: ec566321ff0d
"""
from alembic import op
import sqlalchemy as sa

revision: str = "a3f7c012e9b5"
down_revision: str = "b2f4d80c1e77"
branch_labels = None
depends_on = None


def _internal_key(url: str):
    """Suy ra file_key từ URL ảnh cũ, chỉ nhận ảnh nội bộ (đường dẫn có '/avatar/').
    Trả None với URL ngoài (Google...) để bỏ qua backfill."""
    if not url:
        return None
    if "/api/uploads/" in url:
        key = url.split("/api/uploads/", 1)[1]
    elif "://" in url:
        rest = url.split("://", 1)[1]
        parts = rest.split("/", 1)
        if len(parts) < 2:
            return None
        key = parts[1]
    else:
        key = url.lstrip("/")
    key = key.split("?")[0]
    return key if "/avatar/" in key else None


def upgrade() -> None:
    op.add_column("tab_user", sa.Column("avatar_file_id", sa.BigInteger(),
                                        nullable=False, server_default="0"))
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, avatar FROM tab_user WHERE avatar IS NOT NULL AND avatar <> ''"
    )).fetchall()
    for uid, avatar in rows:
        key = _internal_key(avatar)
        if not key:
            continue  # URL ngoài (Google) — để lần đăng nhập Google kế tự đồng bộ
        res = conn.execute(sa.text(
            "INSERT INTO tab_file (filename, file_key, url, content_type, size, sha256, "
            "created_by, updated_by) VALUES (:fn, :k, :u, '', 0, '', 0, 0)"
        ), {"fn": key.rsplit("/", 1)[-1], "k": key, "u": avatar})
        conn.execute(sa.text("UPDATE tab_user SET avatar_file_id=:f WHERE id=:i"),
                     {"f": res.lastrowid, "i": uid})

    op.drop_column("tab_user", "avatar")
    # đã điền xong → bỏ server_default, để mặc định do tầng ứng dụng giữ (=0)
    op.alter_column("tab_user", "avatar_file_id",
                    existing_type=sa.BigInteger(), server_default=None)


def downgrade() -> None:
    op.add_column("tab_user", sa.Column("avatar", sa.String(length=500),
                                        nullable=False, server_default=""))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE tab_user u JOIN tab_file f ON u.avatar_file_id = f.id "
        "SET u.avatar = f.url WHERE u.avatar_file_id <> 0"
    ))
    op.drop_column("tab_user", "avatar_file_id")
    op.alter_column("tab_user", "avatar",
                    existing_type=sa.String(length=500), server_default=None)
