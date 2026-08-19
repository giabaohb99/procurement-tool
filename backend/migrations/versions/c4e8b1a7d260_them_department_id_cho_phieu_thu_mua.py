"""them_department_id cho YCMH / YCBG / DMH (CR-086)

Revision ID: c4e8b1a7d260
Revises: 225c3966c99c
Create Date: 2026-08-18 11:20:00.000000

Ba bảng phiếu đang neo phòng ban bằng CHUỖI TÊN (`department`): phân quyền theo phòng, bộ lọc
và thông báo "cần duyệt" đều so tên. Đổi tên một phòng là cả ba lệch cùng lúc mà không có lỗi
nào nổi lên. Thêm `department_id` làm NGUỒN SỰ THẬT; cột tên giữ nguyên làm BẢN CHỤP để in và
đối chiếu phiếu cũ (xóa ở N-008, sau khi có ô snapshot cho bản in).

Điền lùi theo hai vòng, chặt trước lỏng sau:
  1. khớp (tên, pháp nhân) — phòng trùng tên giữa các pháp nhân chỉ suy ra được bằng cách này;
  2. khớp tên, và CHỈ khi đúng một phòng mang tên đó.

Sót là chuyện bình thường (tên phòng đã đổi, phiếu nhập tay, tên trùng không suy ra được).
Dòng sót để `department_id = 0` và GIỮ NGUYÊN tên — `core/scoping.py` còn đường lùi so theo
tên cho đúng nhóm dòng này, nên không ai mất phiếu đang thấy. **Không raise**: `start.prod.sh`
chạy `alembic upgrade head` lúc khởi động container, migration chết là api không lên.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8b1a7d260"
down_revision: Union[str, None] = "225c3966c99c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("tab_purchase_request", "tab_survey_request", "tab_purchase_order")


def upgrade() -> None:
    for t in _TABLES:
        op.add_column(t, sa.Column("department_id", sa.BigInteger(), nullable=False,
                                   server_default="0"))
        op.create_index(op.f(f"ix_{t}_department_id"), t, ["department_id"])

    bind = op.get_bind()
    for t in _TABLES:
        bind.execute(sa.text(f"""
            UPDATE {t} t
              JOIN (SELECT TRIM(d.name) nm, d.company_id cid, MIN(d.id) did
                      FROM tab_department d
                     GROUP BY TRIM(d.name), d.company_id HAVING COUNT(*) = 1) u
                ON u.nm = TRIM(t.department) AND u.cid = t.company_id
               SET t.department_id = u.did
             WHERE t.department_id = 0 AND TRIM(t.department) <> ''
        """))
        bind.execute(sa.text(f"""
            UPDATE {t} t
              JOIN (SELECT TRIM(d.name) nm, MIN(d.id) did
                      FROM tab_department d
                     GROUP BY TRIM(d.name) HAVING COUNT(*) = 1) u
                ON u.nm = TRIM(t.department)
               SET t.department_id = u.did
             WHERE t.department_id = 0 AND TRIM(t.department) <> ''
        """))
        named = bind.execute(sa.text(
            f"SELECT COUNT(*) FROM {t} WHERE TRIM(department) <> ''")).scalar() or 0
        left = bind.execute(sa.text(
            f"SELECT COUNT(*) FROM {t} WHERE department_id = 0 AND TRIM(department) <> ''")).scalar() or 0
        print(f"[CR-086] {t}: {named - left}/{named} dong co ten phong da dien duoc id; "
              f"{left} dong khong suy ra duoc (giu ten, department_id = 0)")

    # 'Phòng ban được xem' (tab_user_scope, dim='department') cũng đang lưu TÊN — đổi sang id để
    # khớp cùng một kiểu với cột trên phiếu. Dòng không suy ra được thì ĐỂ NGUYÊN tên:
    # `core/auth.py` đọc được cả hai kiểu, nên phạm vi của người đó không mất.
    rows = bind.execute(sa.text("""
        SELECT id, value FROM tab_user_scope
         WHERE dim = 'department' AND TRIM(value) <> '' AND value NOT REGEXP '^[0-9]+$'
    """)).fetchall()
    done, miss = 0, []
    for sid, val in rows:
        did = bind.execute(sa.text("""
            SELECT MIN(id) FROM tab_department WHERE TRIM(name) = :nm HAVING COUNT(*) = 1
        """), {"nm": (val or "").strip()}).scalar()
        if did:
            bind.execute(sa.text("UPDATE tab_user_scope SET value = :v WHERE id = :i"),
                         {"v": str(did), "i": sid})
            done += 1
        else:
            miss.append(str(val))
    print(f"[CR-086] tab_user_scope: {done}/{len(rows)} dong pham vi phong ban da doi sang id"
          + (f"; con lai giu ten: {miss}" if miss else ""))


def downgrade() -> None:
    # Không đổi ngược `tab_user_scope` về tên: `core/auth.py` đọc được cả id lẫn tên nên để id
    # vẫn chạy đúng, mà đổi ngược thì phiếu đã đổi tên phòng lại lệch thêm một lần nữa.
    for t in _TABLES:
        op.drop_index(op.f(f"ix_{t}_department_id"), table_name=t)
        op.drop_column(t, "department_id")
