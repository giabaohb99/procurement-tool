"""chuan_hoa_dinh_muc_bao_bi_thanh_phan: tach 5 cot ma cua tab_packaging_bom thanh bang tab_packaging_bom_part (duoc-CR-784)

Revision ID: bompart784
Revises: ppld784
Create Date: 2026-11-25

Chu du an chot 25/11/2026 ("them cai type la duoc, roi gan them id vo"): dinh muc bao bi truoc day la MOT dong moi ma HH voi nam
cot ma co dinh (bottle / cap / label / carton_label / carton) va nam chi muc don. Them mot loai thanh phan moi (tem, mang co...)
la phai doi cau truc bang. Nay:

- `tab_packaging_bom` giu vai tro DAU PHIEU (hh_code, ten, quy cach thung, cot kiem toan).
- `tab_packaging_bom_part` moi: (bom_id -> tab_packaging_bom.id ON DELETE CASCADE, part_type SMALLINT = `PackagingRole`, part_code).
  Duy nhat (bom_id, part_type) — hien moi loai mot ma, bo rang buoc nay la cho phep nhieu ma cho mot loai. Chi muc phu (part_code, part_type, bom_id) cho
  tra nguoc "san pham nao dung ma X".

upgrade: tao bang, SAO du lieu tu nam cot (bo qua ma rong), roi XOA nam cot + nam chi muc cu. downgrade: tao lai nam cot + chi muc, sao
nguoc tu bang thanh phan (loai nao khong co dong thi chuoi rong), roi xoa bang thanh phan. Loai thanh phan THEM SAU nam loai nay
(part_type > 5) khong co cot de chua nen mat khi ha cap — chap nhan duoc vi ha cap chi dung de quay dau ngay sau khi len.

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Chay duoc tren MySQL 8 va SQLite (bai kiem). Hai ham
`copy_columns_to_parts` / `copy_parts_to_columns` nhan ket noi de bai kiem goi truc tiep tren du lieu mau.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "bompart784"
down_revision: Union[str, None] = "ppld784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BOM_TABLE = "tab_packaging_bom"
PART_TABLE = "tab_packaging_bom_part"
#  (part_type = PackagingRole, cot cu) — chep tay vao migration (khong import ma ung dung: migration phai dung yen theo thoi gian).
ROLE_COLUMNS = ((1, "bottle_code"), (2, "cap_code"), (3, "label_code"), (4, "carton_label_code"), (5, "carton_code"))
#  (ten chi muc cu, cot) — tao o migration pkgcost784.
OLD_INDEXES = (("ix_pbom_bottle", "bottle_code"), ("ix_pbom_cap", "cap_code"), ("ix_pbom_label", "label_code"),
               ("ix_pbom_carton_label", "carton_label_code"), ("ix_pbom_carton", "carton_code"))


def copy_columns_to_parts(conn) -> None:
    """Moi cot ma khac rong cua moi dinh muc -> mot dong thanh phan (loai = so `PackagingRole`)."""
    for part_type, column in ROLE_COLUMNS:
        conn.execute(sa.text(
            f"INSERT INTO {PART_TABLE} (bom_id, part_type, part_code) "
            f"SELECT id, :part_type, {column} FROM {BOM_TABLE} WHERE {column} <> '' ORDER BY id"), {"part_type": part_type})


def copy_parts_to_columns(conn) -> None:
    """Nguoc lai: dong thanh phan cua tung loai -> cot ma tuong ung (khong co dong thi chuoi rong)."""
    for part_type, column in ROLE_COLUMNS:
        conn.execute(sa.text(
            f"UPDATE {BOM_TABLE} SET {column} = COALESCE((SELECT p.part_code FROM {PART_TABLE} p "
            f"WHERE p.bom_id = {BOM_TABLE}.id AND p.part_type = :part_type), '')"), {"part_type": part_type})


def upgrade() -> None:
    op.create_table(
        PART_TABLE,
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("bom_id", sa.BigInteger(), nullable=False),
        sa.Column("part_type", sa.SmallInteger(), nullable=False),
        sa.Column("part_code", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["bom_id"], [f"{BOM_TABLE}.id"], name="fk_pbom_part_bom", ondelete="CASCADE"),
        sa.UniqueConstraint("bom_id", "part_type", name="uq_pbom_part_bom_type"),
    )
    op.create_index("ix_pbom_part_code", PART_TABLE, ["part_code", "part_type", "bom_id"])      # chi muc PHU cho tra nguoc theo ma

    copy_columns_to_parts(op.get_bind())

    with op.batch_alter_table(BOM_TABLE) as batch:          # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        for name, _ in OLD_INDEXES:
            batch.drop_index(name)
        for _, column in ROLE_COLUMNS:
            batch.drop_column(column)


def downgrade() -> None:
    with op.batch_alter_table(BOM_TABLE) as batch:
        for _, column in ROLE_COLUMNS:
            batch.add_column(sa.Column(column, sa.String(50), nullable=False, server_default=""))
        for name, column in OLD_INDEXES:
            batch.create_index(name, [column])

    copy_parts_to_columns(op.get_bind())

    op.drop_index("ix_pbom_part_code", table_name=PART_TABLE)
    op.drop_table(PART_TABLE)
