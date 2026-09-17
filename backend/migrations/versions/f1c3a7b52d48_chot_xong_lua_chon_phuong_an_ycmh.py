"""Them moc "chot xong lua chon phuong an" tren tab_purchase_request (bao-CR-419)

Revision ID: f1c3a7b52d48
Revises: e2621286669e
Create Date: 2026-09-17

Luong phuong an (bao-CR-310) co hai lan ban giao, nhung truoc CR nay chi lan thu
nhat co dau vet: NSTM "chot hoan thanh xu ly" ghi vao `options_done` tung dong.
Chieu nguoc lai — nguoi yeu cau da chon xong chua — khong the SUY ra duoc, vi
H.10.2 cho phuong an 0 duoc tick san: moi dong luon co mot phuong an dang chon ke
ca khi nguoi yeu cau chua he mo phieu. Im lang va da xong nhin giong het nhau.

Nen them MOT moc thoi diem o cap PHIEU (khong phai cap dong): nguoi yeu cau bam
"Chot xong lua chon" mot lan cho ca phieu, thu mua thay moc do thi biet duoc vao
gom don. Day chinh la thu de treo chuong `pr_options_chosen` vao.

KHONG mau thuan voi loi canh bao trong docstring cua `PurchaseRequestItemOption`
("khong them cot da chot phuong an chua tren dong YCMH"): cot do se la nguon su
that thu hai cua `is_chosen`. Hai cot o day ghi mot SU KIEN cap phieu — ai bam,
luc nao — khong suy lai duoc tu bang phuong an. Cung ho voi `options_done`.

`options_chosen_at` NULL = vong nay chua chot xong. Mo lai bat ky dong nao
(`options_reopen`) se xoa moc ve NULL: mo lai la mo mot vong thuong luong moi.
"""

from alembic import op
import sqlalchemy as sa

revision = "f1c3a7b52d48"
down_revision = "e2621286669e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tab_purchase_request",
        sa.Column("options_chosen_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "tab_purchase_request",
        sa.Column("options_chosen_by", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tab_purchase_request", "options_chosen_by")
    op.drop_column("tab_purchase_request", "options_chosen_at")
