"""gop vai tro trung ten "Quan tri he thong" (ADMINISTRATOR -> admin)

Revision ID: b7e4d2a9c561
Revises: a3f5c81d7e64
Create Date: 2026-08-05

Tren DB that dang ton tai HAI vai tro cung ten hien thi "Quan tri he thong":
  - code `ADMINISTRATOR` (id 1, ban legacy)
  - code `admin`         (ban seed.py dang dung lam chuan)
Nguoi dung nhin thay 2 dong giong het nhau o man Vai tro -> khong biet chon dong nao.

Migration nay GOP ve mot: chuyen moi tai khoan / phan pham vi (UserScope) dang gan
`ADMINISTRATOR` sang `admin`, roi xoa `ADMINISTRATOR` cung ma tran quyen cua no.
`admin` duoc giu vi toan bo code (seed.py, notification, ticket) coi day la vai tro chuan;
neu xoa `admin` thi lan khoi dong sau seed se tao lai -> trung tiep.

An toan: moi cho trong code kiem tra vai tro quan tri deu xet CA HAI ma
(`Role.code.in_(["admin", "ADMINISTRATOR"])`) nen bo mot ma khong lam mat quyen.
Idempotent: DB nao khong co `ADMINISTRATOR` thi khong lam gi.
"""
from alembic import op
import sqlalchemy as sa


revision = 'b7e4d2a9c561'
down_revision = 'a3f5c81d7e64'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    old_id = conn.execute(sa.text(
        "SELECT id FROM tab_role WHERE code = 'ADMINISTRATOR' LIMIT 1")).scalar()
    if not old_id:
        return
    new_id = conn.execute(sa.text(
        "SELECT id FROM tab_role WHERE code = 'admin' LIMIT 1")).scalar()
    if not new_id:
        # Chua co vai tro chuan -> doi ma vai tro cu thanh 'admin' la xong (giu nguyen quyen + gan).
        conn.execute(sa.text("UPDATE tab_role SET code = 'admin' WHERE id = :o"), {"o": old_id})
        return

    p = {"o": old_id, "n": new_id}
    # 1) Tai khoan dang co CA HAI vai tro -> bo dong cu (tranh trung khoa khi doi role_id)
    conn.execute(sa.text(
        "DELETE FROM tab_user_role WHERE role_id = :o AND user_id IN "
        "(SELECT user_id FROM (SELECT user_id FROM tab_user_role WHERE role_id = :n) x)"), p)
    conn.execute(sa.text("UPDATE tab_user_role SET role_id = :n WHERE role_id = :o"), p)

    # 2) Pham vi du lieu (UserScope) gan theo vai tro cu -> chuyen sang vai tro chuan
    conn.execute(sa.text(
        "DELETE FROM tab_user_scope WHERE role_id = :o AND user_id IN "
        "(SELECT user_id FROM (SELECT user_id FROM tab_user_scope WHERE role_id = :n) x)"), p)
    conn.execute(sa.text("UPDATE tab_user_scope SET role_id = :n WHERE role_id = :o"), p)

    # 3) Xoa ma tran quyen + vai tro cu
    conn.execute(sa.text("DELETE FROM tab_permission WHERE role_id = :o"), p)
    conn.execute(sa.text("DELETE FROM tab_role WHERE id = :o"), p)


def downgrade() -> None:
    # Khong tach lai duoc (khong biet tai khoan nao von thuoc vai tro cu).
    pass
