"""lich_su_mua_them_giai_doan: cot `line_stage` o `tab_purchase_history` (bao-CR-790)

Revision ID: phstage790
Revises: bombatch784
Create Date: 2026-11-27

Chu du an yeu cau 27/11/2026: lich su mua hang phai co tu luc HANG VE KHO, khong doi dong DMH hoan thanh (thuc te tren prod 743 dong
da nhan hang ma chi 5 dong co lich su). Ban ghi sinh luc nhan hang con doi theo DMH (doi gia / SL / huy) nen can phan biet voi ban ghi
da chot. Them cot `line_stage` SMALLINT NOT NULL DEFAULT 2, cung bo ma `LedgerLineStage` cua so gia:
  1 = dang mo (da nhan hang, chua hoan thanh, con dong bo theo DMH);
  2 = da chot (dong hoan thanh hoac du lieu cu nap tu Excel) - bat bien.

upgrade: them cot, mac dinh 2 nen MOI dong dang co (du lieu cu + dong da hoan thanh) deu la da chot - khong doi hanh vi cu.
  Ban ghi dang mo cho cac dong DMH da nhan hang tu truoc do script `scripts/sync_po_purchase_history.py` dung (chay thu truoc).
downgrade: xoa cac ban ghi dang mo (chung khong ton tai trong mo hinh cu) roi bo cot.

VIET TAY, KHONG autogenerate. Chay duoc tren MySQL 8 va SQLite (bai kiem).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "phstage790"
down_revision: Union[str, None] = "bombatch784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_purchase_history"
OPEN_STAGE = 1          # LedgerLineStage.OPEN - chep tay (migration phai dung yen theo thoi gian)


def upgrade() -> None:
    with op.batch_alter_table(TABLE) as batch:     # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        batch.add_column(sa.Column("line_stage", sa.SmallInteger(), nullable=False, server_default="2"))


def downgrade() -> None:
    op.execute(sa.text(f"DELETE FROM {TABLE} WHERE line_stage = :stage").bindparams(stage=OPEN_STAGE))
    with op.batch_alter_table(TABLE) as batch:
        batch.drop_column("line_stage")
