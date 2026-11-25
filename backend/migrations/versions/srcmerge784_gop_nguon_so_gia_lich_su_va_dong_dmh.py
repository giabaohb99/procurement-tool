"""gop_nguon_so_gia_lich_su_va_dong_dmh: lich su mua cua he thong va dong DMH la MOT dong so gia theo po_item_id (duoc-CR-784)

Revision ID: srcmerge784
Revises: bompart784
Create Date: 2026-11-25

Truoc day mot lan mua cua he thong nam o HAI dong so gia: nguon 2 (`tab_po_item.id`) khi dong DMH dang mo, roi bi XOA va chen lai thanh
nguon 1 (`tab_purchase_history.id`, id moi) luc hoan thanh. `tab_purchase_history.po_item_id` la duy nhat nen dong lich su he thong la
ban chup 1-1 cua dong DMH - chu du an chot 25/11/2026 (C1 = A) gop lai: dong DMH la MOT dong so (nguon 2, `source_id = po_item_id`) suot doi,
them cot `line_stage` (1 Dang mo, 2 Da chot); nguon 1 chi con lich su cu nap tu Excel (`po_item_id` trong).

upgrade:
  1. them `line_stage SMALLINT NOT NULL` (mac dinh tam 2); dong nguon 2 hien co = dang mo -> 1;
  2. dong nguon 2 ma `po_item_id` da co dong nguon 1 (theo luat cu phai bang 0) bi xoa, lich su thang (in so dong);
  3. dong nguon 1 cua lich su CO `po_item_id` -> nguon 2, `source_id = po_item_id`, `line_stage = 2` (id dong so giu nguyen);
  4. bo gia tri mac dinh cua `line_stage` (ghi moi phai dat ro).
downgrade: dong nguon 2 da chot (`line_stage = 2`) co dong lich su tro `po_item_id` do -> tra ve nguon 1 (`source_id` = id lich su); dong
da chot khong co lich su va dong dang mo o lai nguon 2 (dung nhu truoc khi gop); roi xoa cot `line_stage`.

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Chay duoc tren MySQL 8 va SQLite (bai kiem). Hai ham
`merge_history_sources` / `split_history_sources` nhan ket noi de bai kiem goi truc tiep tren du lieu mau; cau UPDATE dung truy van con
tuong quan theo khoa chinh nen CUNG MOT cau chay tren ca hai he. Trong cau UPDATE cua MySQL, phep gan `source_id` dat TRUOC `source_type`
(MySQL doi gia tri theo thu tu trai -> phai; SQLite dung gia tri cu cho moi phep gan).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "srcmerge784"
down_revision: Union[str, None] = "bompart784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEDGER = "tab_product_price_ledger"
HISTORY = "tab_purchase_history"
#  Chep tay vao migration (khong import ma ung dung: migration phai dung yen theo thoi gian): PriceSourceType + LedgerLineStage.
SRC_HISTORY, SRC_PO = 1, 2
OPEN, FINAL = 1, 2
BATCH = 1000


def merge_history_sources(conn) -> dict:
    """Gop nguon 1 co DMH vao nguon 2 (sau khi cot `line_stage` da co, moi dong nguon 2 dang la `OPEN`). Tra so dong moi buoc."""
    #  Va cham: dong nguon 2 ma DMH do da co dong lich su nam trong so (nguon 1) - lich su thang, xoa dong nguon 2. Chon id vao bo nho
    #  roi xoa theo lo (MySQL cam xoa bang co truy van con tren chinh bang do - loi 1093).
    clash_ids = [r[0] for r in conn.execute(sa.text(
        f"SELECT l2.id FROM {LEDGER} l2 JOIN {HISTORY} ph ON ph.po_item_id = l2.source_id "
        f"JOIN {LEDGER} l1 ON l1.source_type = :src_history AND l1.source_id = ph.id "
        f"WHERE l2.source_type = :src_po"), {"src_history": SRC_HISTORY, "src_po": SRC_PO}).all()]
    for i in range(0, len(clash_ids), BATCH):
        part = clash_ids[i:i + BATCH]
        marks = ", ".join(f":i{n}" for n in range(len(part)))
        conn.execute(sa.text(f"DELETE FROM {LEDGER} WHERE id IN ({marks})"), {f"i{n}": v for n, v in enumerate(part)})
    moved = conn.execute(sa.text(
        f"UPDATE {LEDGER} SET source_id = (SELECT ph.po_item_id FROM {HISTORY} ph WHERE ph.id = {LEDGER}.source_id), "
        f"source_type = :src_po, line_stage = :final "
        f"WHERE source_type = :src_history AND EXISTS "
        f"(SELECT 1 FROM {HISTORY} ph WHERE ph.id = {LEDGER}.source_id AND ph.po_item_id IS NOT NULL)"),
        {"src_po": SRC_PO, "final": FINAL, "src_history": SRC_HISTORY}).rowcount
    return {"deleted_clashing_po_lines": len(clash_ids), "merged_history_rows": moved or 0}


def split_history_sources(conn) -> int:
    """Nguoc lai: dong nguon 2 da chot co dong lich su tro `po_item_id` do -> nguon 1 (`source_id` = id lich su). Tra so dong tach."""
    return conn.execute(sa.text(
        f"UPDATE {LEDGER} SET source_id = (SELECT ph.id FROM {HISTORY} ph WHERE ph.po_item_id = {LEDGER}.source_id), "
        f"source_type = :src_history "
        f"WHERE source_type = :src_po AND line_stage = :final AND EXISTS "
        f"(SELECT 1 FROM {HISTORY} ph WHERE ph.po_item_id = {LEDGER}.source_id)"),
        {"src_history": SRC_HISTORY, "src_po": SRC_PO, "final": FINAL}).rowcount or 0


def upgrade() -> None:
    with op.batch_alter_table(LEDGER) as batch:      # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        batch.add_column(sa.Column("line_stage", sa.SmallInteger(), nullable=False, server_default=str(FINAL)))
    conn = op.get_bind()
    conn.execute(sa.text(f"UPDATE {LEDGER} SET line_stage = :open WHERE source_type = :src_po"), {"open": OPEN, "src_po": SRC_PO})
    stats = merge_history_sources(conn)
    print(f"[srcmerge784] xoa {stats['deleted_clashing_po_lines']} dong DMH trung lich su; gop {stats['merged_history_rows']} dong lich su vao dong DMH")
    with op.batch_alter_table(LEDGER) as batch:
        batch.alter_column("line_stage", existing_type=sa.SmallInteger(), existing_nullable=False, server_default=None)


def downgrade() -> None:
    moved = split_history_sources(op.get_bind())
    print(f"[srcmerge784] tach {moved} dong DMH da chot tro lai nguon lich su")
    with op.batch_alter_table(LEDGER) as batch:
        batch.drop_column("line_stage")
