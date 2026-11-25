"""danh_dau_lo_nhap_dinh_muc_va_so_gia: `import_batch_id` o `tab_packaging_bom` + `tab_product_price_ledger` (duoc-CR-784, phase 07)

Revision ID: bombatch784
Revises: fgname784
Create Date: 2026-11-25

Chu du an hoi 25/11/2026: 1.000 dong dinh muc nap tu ban mau HTML, sau nay muon xoa thi dinh danh the nao. Hai bang chua luu dong nao
thuoc lo nhap Excel nao (`tab_import_batch`), nen them cot `import_batch_id` BIGINT NOT NULL DEFAULT 0 (0 = nhap tay / khong do lo nao)
+ chi muc:
  - `tab_packaging_bom.import_batch_id` (`ix_pbom_import_batch`): lo module 4 TAO hoac SUA dong lan cuoi;
  - `tab_product_price_ledger.import_batch_id` (`ix_ppl_import_batch`): lo module 6 (so Misa xlsx) THEM dong.
Bao gia da co (`source_type = 2`, `source_id` = id lo) tu phase 03 nen khong them cot.

upgrade: them hai cot + chi muc, roi DANH DAU dinh muc da co (`mark_bom_rows`): voi MOI lo module 4 ghi that da xong (theo thu tu id),
  tim dong chua co lo, cung nguoi tao, `created_at` nam trong cua so [gio len lo - 3 giay, gio ket thuc + 3 giay]; CHI gan khi so dong
  tim duoc DUNG BANG `created_count` cua lo, lech thi bo qua va in canh bao (khong doan). In dong tom tat `[bombatch784] ...`.
  Dong so Misa da co khong danh dau (khong phan biet duoc voi dong nap bang script HTML) - giu 0.
downgrade: bo chi muc va cot (mat thong tin lo; khong anh huong du lieu khac).

VIET TAY, KHONG autogenerate. Chay duoc tren MySQL 8 va SQLite (bai kiem).
"""
from datetime import timedelta
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "bombatch784"
down_revision: Union[str, None] = "fgname784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BOM = "tab_packaging_bom"
LEDGER = "tab_product_price_ledger"
BATCH = "tab_import_batch"
PACKAGING_BOM_MODULE = 4          # ImportModule.PACKAGING_BOM - chep tay (migration phai dung yen theo thoi gian)
APPLY_MODE, DONE_STATUS = 1, 2    # ImportMode.APPLY, ImportStatus.DONE
GRACE = timedelta(seconds=3)      # dong ho Python (gio lo) lech dong ho CSDL (gio dong) + MySQL lam tron giay


def _add_column(table: str, index: str) -> None:
    with op.batch_alter_table(table) as batch:     # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        batch.add_column(sa.Column("import_batch_id", sa.BigInteger(), nullable=False, server_default="0"))
        batch.create_index(index, ["import_batch_id"])


def _drop_column(table: str, index: str) -> None:
    with op.batch_alter_table(table) as batch:
        batch.drop_index(index)
        batch.drop_column("import_batch_id")


def mark_bom_rows(conn) -> list[str]:
    """Danh dau dinh muc theo lo module 4 (xem docstring). Tra danh sach cau thong bao (de in va de kiem)."""
    bom = sa.table(BOM, sa.column("id", sa.BigInteger), sa.column("created_by", sa.BigInteger),
                   sa.column("created_at", sa.DateTime), sa.column("import_batch_id", sa.BigInteger))
    batch = sa.table(BATCH, sa.column("id", sa.BigInteger), sa.column("module", sa.SmallInteger), sa.column("mode", sa.SmallInteger),
                     sa.column("status", sa.SmallInteger), sa.column("created_count", sa.Integer),
                     sa.column("created_by", sa.BigInteger), sa.column("created_at", sa.DateTime),
                     sa.column("finished_at", sa.DateTime))
    notes: list[str] = []
    batches = conn.execute(
        sa.select(batch.c.id, batch.c.created_count, batch.c.created_by, batch.c.created_at, batch.c.finished_at)
        .where(batch.c.module == PACKAGING_BOM_MODULE, batch.c.mode == APPLY_MODE, batch.c.status == DONE_STATUS,
               batch.c.created_count > 0).order_by(batch.c.id)).all()
    for bid, created_count, created_by, created_at, finished_at in batches:
        start, end = created_at - GRACE, (finished_at or created_at) + GRACE
        where = sa.and_(bom.c.import_batch_id == 0, bom.c.created_by == created_by,
                        bom.c.created_at >= start, bom.c.created_at <= end)
        found = conn.execute(sa.select(sa.func.count()).select_from(bom).where(where)).scalar() or 0
        if found != created_count:
            notes.append(f"lo {bid}: bo qua (lo ghi {created_count} dong tao moi, tim thay {found} dong khop nguoi tao + gio) - canh bao")
            continue
        conn.execute(bom.update().where(where).values(import_batch_id=bid))
        notes.append(f"lo {bid}: danh dau {found} dong dinh muc")
    return notes


def upgrade() -> None:
    _add_column(BOM, "ix_pbom_import_batch")
    _add_column(LEDGER, "ix_ppl_import_batch")
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table(BATCH):
        notes = mark_bom_rows(conn)
        print("[bombatch784] " + ("; ".join(notes) if notes else "khong co lo dinh muc ghi that nao de danh dau"))
    else:
        print("[bombatch784] khong co bang lo nhap - bo qua danh dau")


def downgrade() -> None:
    _drop_column(LEDGER, "ix_ppl_import_batch")
    _drop_column(BOM, "ix_pbom_import_batch")
