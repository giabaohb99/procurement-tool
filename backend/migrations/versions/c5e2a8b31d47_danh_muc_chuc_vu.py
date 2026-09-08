"""danh_muc_chuc_vu — bảng `tab_job_position` + `tab_employee.position_id`

Khách chốt 08/09/2026: ô «Vị trí / Chức vụ» phải lấy từ một DANH MỤC quản lý
được, không gõ tay nữa. Thiết kế ở `app/modules/employee/position_model.py`.

**Có NẠP LẠI dữ liệu cũ**, khác `b7c1d4e90a52`: cột `tab_employee.position` đã
chạy trên prod từ lâu và đang giữ chức danh thật của từng người. Migration này
gom các giá trị phân biệt (bỏ khoảng trắng thừa, **không phân biệt hoa thường**)
thành dòng danh mục rồi trỏ `position_id` của từng hồ sơ vào đó.

⚠️ Cột chữ `position` GIỮ NGUYÊN, không xóa. Mười chỗ đang đọc thẳng nó để in
phiếu / xuất Excel / dựng hồ sơ cho trợ lý AI; nó thành **nhãn đã chép**, và
`position_service` là nơi duy nhất được ghi vào đó.

⚠️ Gom KHÔNG phân biệt hoa thường là có chủ ý: dữ liệu thật có «Trưởng phòng» và
«Trưởng Phòng» của cùng một chức vụ. Bản viết đầu tiên gom phân biệt hoa thường
và đẻ ra hai dòng danh mục trông giống hệt nhau trong ô chọn — không ai bấm
đúng được cái nào. Nhãn giữ theo bản ghi ĐẦU TIÊN gặp; sửa lại là việc một phút
trên màn danh mục, còn tự động chọn "bản viết hoa đúng" thì đoán mò.

Revision ID: c5e2a8b31d47
Revises: b7c1d4e90a52
Create Date: 2026-09-08 11:20:00.000000
"""
import re
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c5e2a8b31d47'
down_revision: Union[str, None] = 'b7c1d4e90a52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slug_code(name: str, used: set[str], index: int) -> str:
    """Mã gợi nhớ từ tên: «Trưởng phòng Mua hàng» → `TRUONG-PHONG-MUA-HANG`.

    Rơi về `CV<số>` khi tên không còn ký tự nào dùng được (tên toàn ký hiệu) hay
    khi mã đã bị dòng khác chiếm — mã phải DUY NHẤT, và `tab_job_position.code`
    có ràng buộc duy nhất nên trùng là migration nổ giữa chừng.
    """
    plain = unicodedata.normalize("NFD", name or "")
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    plain = plain.replace("đ", "d").replace("Đ", "D")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", plain).strip("-").upper()[:30].strip("-")
    if not slug or slug in used:
        slug = f"CV{index:03d}"
    return slug


def upgrade() -> None:
    op.create_table(
        "tab_job_position",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_job_position_code"),
    )
    op.create_index("ix_job_position_department", "tab_job_position", ["department_id"])

    op.add_column("tab_employee",
                  sa.Column("position_id", sa.BigInteger(), nullable=False,
                            server_default="0"))
    op.create_index("ix_employee_position", "tab_employee", ["position_id"])

    _backfill()


def _backfill() -> None:
    """Dựng danh mục từ chức danh đang có trên hồ sơ, rồi trỏ hồ sơ vào danh mục."""
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, position FROM tab_employee "
        "WHERE position IS NOT NULL AND TRIM(position) <> ''"
    )).fetchall()
    if not rows:
        return

    #  khóa gom (thường hóa) → (nhãn giữ nguyên của bản ghi đầu tiên, [id hồ sơ])
    groups: dict[str, tuple[str, list[int]]] = {}
    for emp_id, raw in rows:
        label = " ".join((raw or "").split())        # bóp mọi khoảng trắng thừa
        if not label:
            continue
        key = label.casefold()
        if key not in groups:
            groups[key] = (label, [])
        groups[key][1].append(emp_id)

    used_codes: set[str] = set()
    for index, (label, employee_ids) in enumerate(
            sorted(groups.values(), key=lambda g: g[0].casefold()), start=1):
        code = _slug_code(label, used_codes, index)
        used_codes.add(code)
        result = conn.execute(
            sa.text("INSERT INTO tab_job_position "
                    "(code, name, is_active, sort_order, note, department_id, "
                    " created_by, updated_by) "
                    "VALUES (:code, :name, 1, :sort_order, '', 0, 0, 0)"),
            {"code": code, "name": label[:100], "sort_order": index * 10},
        )
        position_id = result.lastrowid
        #  ⚠️ Cập nhật THEO DANH SÁCH ID chứ không `WHERE position = :label`:
        #  gom đã bỏ qua hoa thường và khoảng trắng thừa, nên so lại bằng chuỗi
        #  sẽ sót đúng những dòng lệch chính tả — tức những dòng cần nhất.
        conn.execute(
            sa.text("UPDATE tab_employee SET position_id = :pid, position = :name "
                    "WHERE id IN :ids").bindparams(
                        sa.bindparam("ids", expanding=True)),
            {"pid": position_id, "name": label[:100], "ids": employee_ids},
        )


def downgrade() -> None:
    op.drop_index("ix_employee_position", table_name="tab_employee")
    op.drop_column("tab_employee", "position_id")
    op.drop_index("ix_job_position_department", table_name="tab_job_position")
    op.drop_table("tab_job_position")
