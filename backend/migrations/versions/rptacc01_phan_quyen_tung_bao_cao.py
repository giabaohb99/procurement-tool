"""phan_quyen_tung_bao_cao: bang tab_report_access + mac dinh cho phep 'admin'

Revision ID: rptacc01
Revises: c7e2a9d4b1f3
Create Date: 2026-10-02

Quyen XEM TUNG BAO CAO (phan he Bao cao) -- `tab_report_access`. Cung hinh dang
voi `tab_doc_folder_access` (migration `1c035ad17323`): bon chu the (nguoi /
phong ban / phap nhan / vai tro), cam thang cho phep, thu hoi la danh dau, co
han hieu luc. Thiet ke: `frontend-v2/plans/261002-0836-phan-quyen-tung-bao-cao/
phase-01-backend-report-key-model-migration-seed.md`.

VIET TAY, khong autogenerate -- repo nay autogenerate troi ~650 dong moi lan.

Danh sach 13 khoa CHEN SAN cho vai tro 'admin' duoc DONG BANG ngay trong tep
nay (khong import `ReportKey` tu app/core/report_keys.py): migration phai bat
bien theo thoi gian, doi enum sau nay khong duoc lam doi lai y nghia migration
cu. Day la gia tri SmallInteger 1..13 dung voi `ReportKey` tai thoi diem viet
migration nay -- xem luat bat bien "so da cap khong doi" o dau tep do.

upgrade(): tao bang + 2 index; neu DB da co vai tro 'admin' (deploy tren DB cu,
seed da chay truoc) thi chen san 13 dong CHO PHEP cho vai tro do. DB moi (seed
chua chay) thi bo qua buoc chen -- `report_access/seed_defaults.py` lo viec do
trong seed.run()/seed_prod.run().
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "rptacc01"
down_revision: Union[str, None] = "c7e2a9d4b1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  1 nguoi (id NHAN SU) . 2 phong ban . 3 phap nhan . 4 vai tro -- cung bon so
#  voi `document/access_model.SUBJECT_*`.
_SUBJECT_ROLE = 4
#  1 cho phep . 2 cam.
_EFFECT_ALLOW = 1

#  13 khoa `ReportKey` DONG BANG tai thoi diem viet migration nay -- xem canh
#  bao o docstring dau tep. KHONG sua danh sach nay khi them/doi ReportKey sau
#  nay; migration moi se lo phan khoa moi.
_REPORT_KEYS_V1 = tuple(range(1, 14))

_DEFAULT_REASON = "Mac dinh khi ra tinh nang phan quyen bao cao"


def upgrade() -> None:
    op.create_table(
        "tab_report_access",
        sa.Column("report_key", sa.SmallInteger(), nullable=False),
        sa.Column("subject_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        # 1 cho phep . 2 cam. CAM thang CHO PHEP.
        sa.Column("effect", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.Date(), nullable=True),
        # Trong = khong han.
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        # Thu hoi = DANH DAU, dong o lai bang (G19, G20 -- cung luat voi van ban/thu muc).
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("revoke_reason", sa.String(500), nullable=False, server_default=""),

        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_access_key", "tab_report_access", ["report_key", "effect"])
    op.create_index("ix_report_access_subject", "tab_report_access", ["subject_kind", "subject_id"])

    conn = op.get_bind()
    admin_role_id = conn.execute(
        sa.text("SELECT id FROM tab_role WHERE code = :code"), {"code": "admin"}
    ).scalar()
    if admin_role_id is None:
        #  DB moi, seed chua chay -- `report_access/seed_defaults.py` chen bu
        #  13 dong nay trong seed.run()/seed_prod.run() ngay sau khi vai tro
        #  'admin' duoc tao.
        print("rptacc01: chua co vai tro 'admin' -- bo qua chen mac dinh, seed se lo.")
        return

    conn.execute(
        sa.text(
            "INSERT INTO tab_report_access "
            "(report_key, subject_kind, subject_id, effect, reason, created_by, updated_by) "
            "VALUES (:report_key, :subject_kind, :subject_id, :effect, :reason, 0, 0)"
        ),
        [
            {
                "report_key": key,
                "subject_kind": _SUBJECT_ROLE,
                "subject_id": admin_role_id,
                "effect": _EFFECT_ALLOW,
                "reason": _DEFAULT_REASON,
            }
            for key in _REPORT_KEYS_V1
        ],
    )
    print(f"rptacc01: da chen {len(_REPORT_KEYS_V1)} dong cho phep mac dinh cho vai tro 'admin'.")


def downgrade() -> None:
    op.drop_index("ix_report_access_subject", table_name="tab_report_access")
    op.drop_index("ix_report_access_key", table_name="tab_report_access")
    op.drop_table("tab_report_access")
