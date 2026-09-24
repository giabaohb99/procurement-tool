"""thu_muc_nhom_cong_ty

Thư mục NHÓM «Công ty» ở gốc cây (24/09/2026) — mọi thư mục pháp nhân dời vào
trong đó thay vì đứng thẳng ở gốc, chừa gốc cây cho thư mục người dùng tự tạo.
`kind = 3` (`FolderKind.COMPANY_GROUP`), `company_id = 0`, đúng MỘT dòng.

Bước dữ liệu, cho TỪNG thư mục pháp nhân đang ở gốc (`kind = 1`, `parent_id = 0`):
cả nhánh của nó (lọc bằng tiền tố `path`) được gắn thêm tiền tố `/<nhóm>` vào
`path` và cộng 1 vào `depth`; riêng dòng gốc đổi `parent_id` sang nhóm.
Chạy lại không lặp: có nhóm rồi thì dùng lại, và chỉ đụng gốc pháp nhân CÒN
đứng ở gốc cây.

Revision ID: c0mpgr0up01
Revises: c0nt3ntm0d01
Create Date: 2026-09-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c0mpgr0up01"
down_revision: Union[str, None] = "c0nt3ntm0d01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

KIND_COMPANY = 1
KIND_COMPANY_GROUP = 3
STATUS_ACTIVE = 1
ACCESS_VIEW = 1


def upgrade() -> None:
    bind = op.get_bind()
    group_id = bind.execute(
        sa.text("SELECT id FROM tab_doc_folder WHERE kind = :k ORDER BY id LIMIT 1"),
        {"k": KIND_COMPANY_GROUP},
    ).scalar()
    if group_id is None:
        bind.execute(
            sa.text(
                "INSERT INTO tab_doc_folder (company_id, parent_id, kind, name, code, description,"
                " path, depth, sort_order, status, default_access, created_by, updated_by,"
                " created_at, updated_at)"
                " VALUES (0, 0, :k, :name, '', '', '', 1, 0, :st, :acc, 0, 0, NOW(), NOW())"
            ),
            {"k": KIND_COMPANY_GROUP, "name": "Công ty", "st": STATUS_ACTIVE, "acc": ACCESS_VIEW},
        )
        group_id = bind.execute(
            sa.text("SELECT id FROM tab_doc_folder WHERE kind = :k ORDER BY id LIMIT 1"),
            {"k": KIND_COMPANY_GROUP},
        ).scalar()
        bind.execute(
            sa.text("UPDATE tab_doc_folder SET path = :p WHERE id = :id"),
            {"p": f"/{group_id}/", "id": group_id},
        )

    roots = bind.execute(
        sa.text("SELECT id, path FROM tab_doc_folder WHERE kind = :k AND parent_id = 0"),
        {"k": KIND_COMPANY},
    ).fetchall()
    for root_id, root_path in roots:
        bind.execute(
            sa.text(
                "UPDATE tab_doc_folder SET path = CONCAT(:prefix, path), depth = depth + 1"
                " WHERE path LIKE :like"
            ),
            {"prefix": f"/{group_id}", "like": f"{root_path}%"},
        )
        bind.execute(
            sa.text("UPDATE tab_doc_folder SET parent_id = :g WHERE id = :id"),
            {"g": group_id, "id": root_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    group = bind.execute(
        sa.text("SELECT id, path FROM tab_doc_folder WHERE kind = :k ORDER BY id LIMIT 1"),
        {"k": KIND_COMPANY_GROUP},
    ).fetchone()
    if group is None:
        return
    group_id, group_path = group
    cut = len(group_path)  # "/<nhóm>/" — bỏ "/<nhóm>" ở đầu, giữ dấu "/" sau nó
    bind.execute(
        sa.text(
            "UPDATE tab_doc_folder SET path = SUBSTRING(path, :start), depth = depth - 1"
            " WHERE path LIKE :like AND id <> :g"
        ),
        {"start": cut, "like": f"{group_path}%", "g": group_id},
    )
    bind.execute(
        sa.text("UPDATE tab_doc_folder SET parent_id = 0 WHERE parent_id = :g"),
        {"g": group_id},
    )
    bind.execute(sa.text("DELETE FROM tab_doc_folder WHERE id = :g"), {"g": group_id})
