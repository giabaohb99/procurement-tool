"""duoc-CR-756: tab_employee_concurrent.kind — kiêm nhiệm thành hai loại dòng độc lập (Phòng ban / Công ty)

Revision ID: kn756a
Revises: kn755a
Create Date: 2026-11-13

CR-755 lưu một dòng = cặp (công ty, phòng). Người chủ chốt chốt lại (13/11/2026): hai loại dòng ĐỘC LẬP —
**Phòng ban** (`kind = 1`: phòng của công ty HIỆN TẠI, `company_id` = công ty chính) và **Công ty**
(`kind = 2`: công ty khác, `department_id = 0`).

Các bước (VIẾT TAY, không autogenerate — repo này autogenerate trôi ~650 dòng mỗi lần):
 (a) thêm cột `kind` SMALLINT NOT NULL mặc định 1;
 (b) dòng có công ty KHÁC công ty chính của nhân sự -> `kind = 2`, `department_id = 0` (mất phòng — chấp nhận, chỉ
     có trên DB local vì dev/prod chưa có kn755a: dòng chép từ `is_primary = 0` đều mang công ty chính);
 (c) dòng loại 1 mang `company_id = 0` (dữ liệu cũ của nhân sự chưa gắn pháp nhân lúc chép) -> công ty chính hiện tại;
 (d) chỉ mục `ix_employee_concurrent_company_kind (company_id, kind)` cho trang công ty;
 (e) in số dòng bị bỏ phòng và số cặp loại 2 chồng giai đoạn (để nguyên — sửa ở tab, sẽ gặp 409 khi sửa).

Chạy lại được: cột / chỉ mục đã có thì bỏ qua; bước (b) chỉ xét dòng còn `kind = 1`. Hai câu UPDATE dùng truy vấn con
tương quan (không UPDATE ... JOIN) để chạy cả trên SQLite của bài kiểm.

⚠️ downgrade: bỏ chỉ mục + cột `kind`. Dòng loại 2 ở lại với `department_id = 0` — hồ sơ quyền của CR-755 bỏ qua
phòng 0 (`core/auth.get_perm_profile`) nên hạ KHÔNG mở thêm quyền nào; phòng đã bỏ ở bước (b) không dựng lại được.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "kn756a"
down_revision: Union[str, None] = "kn755a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_employee_concurrent"
INDEX = "ix_employee_concurrent_company_kind"

#  Công ty chính HIỆN TẠI của nhân sự dòng đó (0 nếu hồ sơ trống / không còn).
_EMP_COMPANY = "COALESCE((SELECT e.company_id FROM tab_employee e WHERE e.id = tab_employee_concurrent.employee_id), 0)"


def _iso(value) -> str | None:
    """Ngày -> 'YYYY-MM-DD' (MySQL trả `date`, SQLite trả chuỗi); None giữ None."""
    return None if value is None else str(value)[:10]


def _count_overlapping_pairs(bind) -> int:
    """Số cặp dòng loại 2 CÙNG (nhân sự, công ty) có giai đoạn chồng nhau (hai đầu bao gồm; None = vô cực)."""
    rows = bind.execute(sa.text(
        f"SELECT employee_id, company_id, from_date, to_date FROM {TABLE} WHERE kind = 2")).fetchall()
    groups: dict[tuple, list[tuple]] = {}
    for emp, company, start, end in rows:
        groups.setdefault((emp, company), []).append((_iso(start), _iso(end)))
    total = 0
    for spans in groups.values():
        for i, (a_from, a_to) in enumerate(spans):
            for b_from, b_to in spans[i + 1:]:
                if (a_from is None or b_to is None or a_from <= b_to) \
                        and (b_from is None or a_to is None or b_from <= a_to):
                    total += 1
    return total


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "kind" not in {c["name"] for c in insp.get_columns(TABLE)}:
        op.add_column(TABLE, sa.Column("kind", sa.SmallInteger(), nullable=False, server_default="1"))

    # (b) Công ty dòng khác công ty chính -> loại Công ty, bỏ phòng. Đếm trước để in.
    dropped = bind.execute(sa.text(
        f"SELECT COUNT(*) FROM {TABLE} WHERE kind = 1 AND company_id <> 0 AND department_id <> 0 "
        f"AND company_id <> {_EMP_COMPANY}")).scalar() or 0
    bind.execute(sa.text(
        f"UPDATE {TABLE} SET kind = 2, department_id = 0 "
        f"WHERE kind = 1 AND company_id <> 0 AND company_id <> {_EMP_COMPANY}"))

    # (c) Loại 1 mang công ty 0 -> công ty chính hiện tại (chỉ khi hồ sơ đã có pháp nhân).
    bind.execute(sa.text(
        f"UPDATE {TABLE} SET company_id = {_EMP_COMPANY} "
        f"WHERE kind = 1 AND company_id = 0 AND {_EMP_COMPANY} <> 0"))

    # (d) Chỉ mục cho trang công ty.
    if INDEX not in {i["name"] for i in sa.inspect(bind).get_indexes(TABLE)}:
        op.create_index(INDEX, TABLE, ["company_id", "kind"])

    # (e) Báo cáo dữ liệu cần để mắt tới.
    print(f"[kn756a] dòng khác công ty chính chuyển sang loại Công ty (bỏ phòng): {dropped}")
    print(f"[kn756a] cặp dòng loại Công ty chồng giai đoạn (để nguyên): {_count_overlapping_pairs(bind)}")


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if INDEX in {i["name"] for i in insp.get_indexes(TABLE)}:
        op.drop_index(INDEX, table_name=TABLE)
    if "kind" in {c["name"] for c in sa.inspect(bind).get_columns(TABLE)}:
        op.drop_column(TABLE, "kind")
