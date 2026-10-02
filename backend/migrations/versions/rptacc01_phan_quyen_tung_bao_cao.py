"""phan_quyen_tung_bao_cao: bang tab_report_access + mac dinh cho phep vai tro quan tri

Revision ID: rptacc01
Revises: c7e2a9d4b1f3
Create Date: 2026-10-02

Quyen XEM TUNG BAO CAO (phan he Bao cao) -- `tab_report_access`. Cung hinh dang
voi `tab_doc_folder_access` (migration `1c035ad17323`): bon chu the (nguoi /
phong ban / phap nhan / vai tro), cam thang cho phep, thu hoi la danh dau, co
han hieu luc. Thiet ke: `frontend-v2/plans/261002-0836-phan-quyen-tung-bao-cao/
phase-01-backend-report-key-model-migration-seed.md`.

VIET TAY, khong autogenerate -- repo nay autogenerate troi ~650 dong moi lan.

Danh sach 13 khoa CHEN SAN cho vai tro quan tri duoc DONG BANG ngay trong tep
nay (khong import `ReportKey` tu app/core/report_keys.py): migration phai bat
bien theo thoi gian, doi enum sau nay khong duoc lam doi lai y nghia migration
cu. Day la gia tri SmallInteger 1..13 dung voi `ReportKey` tai thoi diem viet
migration nay -- xem luat bat bien "so da cap khong doi" o dau tep do.

upgrade(): tao bang + 2 index; neu DB da co vai tro quan tri -- `admin` (doi moi)
VA/HOAC `ADMINISTRATOR` (doi cu, cung danh sach `app.seed.ensure_admin_role` coi
hai ma nay la MOT) -- deploy tren DB cu, seed da chay truoc, thi chen san 13
dong CHO PHEP cho TUNG vai tro do (M5, code review: truoc ban vay nay chi chen
cho 'admin', DB con giu 'ADMINISTRATOR' se co nguoi quan tri khong xem duoc bao
cao nao). Bang vua tao con TRONG nen khong can doc lai trang thai giua hai vong
chen -- ca hai vai tro (neu co) deu nhan du 13 dong o lan nay. DB moi (seed chua
chay, chua co vai tro quan tri nao) thi bo qua buoc chen -- `report_access/
seed_defaults.py` lo viec do trong seed.run()/seed_prod.run().
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

#  Hai ma vai tro quan tri -- cung danh sach `app.seed.ensure_admin_role`/
#  `force_resync_roles` va `report_access/seed_defaults.py` dung.
_ADMIN_ROLE_CODES = ("admin", "ADMINISTRATOR")

#  Co dau, KHOP DUNG tung chu voi `report_access.seed_defaults.DEFAULT_REASON` -- hai noi
#  chen cung mot ly do, UTF-8 qua SQLAlchemy/Alembic (khong phai `mysql -e` dong lenh nen
#  khong dinh loi double-encoding, xem CLAUDE.md goc).
_DEFAULT_REASON = "Mặc định khi ra tính năng phân quyền báo cáo"


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
    admin_role_ids = [
        row[0] for row in conn.execute(
            sa.text("SELECT id FROM tab_role WHERE code IN (:c1, :c2)"),
            {"c1": _ADMIN_ROLE_CODES[0], "c2": _ADMIN_ROLE_CODES[1]},
        ).fetchall()
    ]
    if not admin_role_ids:
        #  DB moi, seed chua chay -- `report_access/seed_defaults.py` chen bu
        #  13 dong nay cho tung vai tro quan tri trong seed.run()/seed_prod.run()
        #  ngay sau khi vai tro 'admin' duoc tao.
        print("rptacc01: chua co vai tro quan tri nao -- bo qua chen mac dinh, seed se lo.")
        return

    #  Bang vua CREATE o tren con trong -- khong can doc lai "khoa nao da co dong" giua
    #  hai vai tro, ca hai (neu co ca 'admin' va 'ADMINISTRATOR') deu nhan du 13 dong.
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
            for admin_role_id in admin_role_ids
            for key in _REPORT_KEYS_V1
        ],
    )
    print(f"rptacc01: da chen {len(_REPORT_KEYS_V1) * len(admin_role_ids)} dong cho phep mac "
          f"dinh cho {len(admin_role_ids)} vai tro quan tri.")


def downgrade() -> None:
    op.drop_index("ix_report_access_subject", table_name="tab_report_access")
    op.drop_index("ix_report_access_key", table_name="tab_report_access")
    op.drop_table("tab_report_access")
