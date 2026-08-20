"""CR-109: lab_result thanh KET LUAN (Mau dat / Mau khong dat)

Truoc: `lab_result` la o chu tu do, moi nguoi go mot kieu nen khong loc,
khong to mau, khong doi chieu duoc.
Sau:   `lab_result` chi con hai gia tri "Mau dat" / "Mau khong dat" (rong =
chua co ket qua), phan nhan xet dai chuyen sang `lab_note`.

Migration nay DON DU LIEU CU: moi gia tri lab_result khong thuoc hai lua chon
duoc day sang lab_note de khong mat chu, roi lab_result tra ve rong.

Revision ID: c9e4b1a7d260
Revises: 4b6d2f0a97c5
"""
from alembic import op
import sqlalchemy as sa

revision = "c9e4b1a7d260"
down_revision = "4b6d2f0a97c5"
branch_labels = None
depends_on = None

DAT = "Mẫu đạt"
KHONG_DAT = "Mẫu không đạt"


def upgrade() -> None:
    # lab_note thuong rong nen phep CASE nay hau het chi la mot phep gan; chi
    # noi chuoi khi ca hai o deu co chu — mat chu cu la mat can cu duyet.
    op.execute(
        sa.text(
            """
            UPDATE tab_survey_product_line
               SET lab_note = CASE
                     WHEN lab_note IS NULL OR lab_note = '' THEN lab_result
                     ELSE CONCAT(lab_result, '\n', lab_note)
                   END,
                   lab_result = ''
             WHERE lab_result IS NOT NULL
               AND lab_result <> ''
               AND lab_result NOT IN (:dat, :khong_dat)
            """
        ).bindparams(dat=DAT, khong_dat=KHONG_DAT)
    )


def downgrade() -> None:
    # Khong quay lui duoc: sau khi don, khong con biet doan nao cua lab_note la
    # lab_result cu. Chu dong de trong thay vi doan bua roi ghi de du lieu that.
    pass
