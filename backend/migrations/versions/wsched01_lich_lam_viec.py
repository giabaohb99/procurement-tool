"""lich_lam_viec: 3 bang tab_work_schedule*, seed mau "Hanh chinh T2-T7"

Revision ID: wsched01
Revises: e8a3c5f1d7b2
Create Date: 2026-10-05

Mau lich tuan + gan theo he thong / phap nhan / phong ban / nhan su. Thiet ke:
`frontend-v2/plans/261005-0925-hr-lich-lam-viec/phase-01-*.md`.

VIET TAY, khong autogenerate -- repo nay autogenerate troi ~650 dong moi lan.
FK mem (khong ForeignKey thuc) theo quy uoc repo.

Seed MOT mau «Hành chính T2–T7» (T2-T7 cả ngày 08:00-17:00, nghi trua 12:00-13:00,
CN nghi), KHONG gan cho ai nen so ngay nghi phep khong doi. Chen trong migration
(chay dung mot lan) de HR xoa/sua khong bi seed hoi sinh.
"""
from datetime import time
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "wsched01"
down_revision: Union[str, None] = "e8a3c5f1d7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED_NAME = "Hành chính T2–T7"
# WorkDayKind (app/core/work_schedule_codes.py): OFF=1, FULL=2.
OFF, FULL = 1, 2


def _audit_cols() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table(
        "tab_work_schedule",
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit_cols(),
        sa.UniqueConstraint("name", name="uq_work_schedule_name"),
    )
    op.create_table(
        "tab_work_schedule_day",
        sa.Column("schedule_id", sa.BigInteger(), nullable=False),
        # 0 = Thu hai ... 6 = Chu nhat (= date.weekday()).
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        # WorkDayKind.
        sa.Column("day_kind", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("lunch_start", sa.Time(), nullable=True),
        sa.Column("lunch_end", sa.Time(), nullable=True),
        *_audit_cols(),
        sa.UniqueConstraint("schedule_id", "weekday", name="uq_work_schedule_day"),
    )
    op.create_table(
        "tab_work_schedule_assignment",
        # WorkScheduleLevel.
        sa.Column("target_level", sa.SmallInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("schedule_id", sa.BigInteger(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        # NULL = khong thoi han.
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        # Dong gan "goc" da kich hoat viec tu dong dong/noi dong nay; xoa dong goc thi mo lai.
        sa.Column("linked_assignment_id", sa.BigInteger(), nullable=True),
        *_audit_cols(),
        sa.UniqueConstraint("target_level", "target_id", "effective_from",
                            name="uq_wsa_target_from"),
    )
    op.create_index("ix_wsa_target", "tab_work_schedule_assignment",
                    ["target_level", "target_id", "effective_from"])
    op.create_index("ix_wsa_schedule", "tab_work_schedule_assignment", ["schedule_id"])

    _seed_default_schedule()
    _grant_permissions()


# Vai tro duoc sua lich (CRUD); moi vai tro con lai chi `read` (form nghi phep can doc).
WRITER_ROLES = ("admin", "hr_leave", "hr_profile")
ENTITY = "work_schedule"


def _grant_permissions() -> None:
    """Cap khoa `work_schedule` cho vai tro CO SAN tren DB that.

    Seed o prod chi THEM, khong DE (D-018) nen doi STD_ROLES khong tu ap len vai tro cu. Viet
    TRONG migration nay (chua len prod) thay vi migration rieng. Idempotent: bo qua vai tro da
    co dong (local da duoc seed cap san), nen khong ghi de quyen nguoi dung da chinh tay.
    """
    bind = op.get_bind()
    roles = bind.execute(sa.text("SELECT id, code FROM tab_role")).fetchall()
    have = {r[0] for r in bind.execute(
        sa.text("SELECT role_id FROM tab_permission WHERE entity = :e"), {"e": ENTITY})}
    for role_id, code in roles:
        if role_id in have:
            continue
        w = 1 if code in WRITER_ROLES else 0
        bind.execute(sa.text(
            "INSERT INTO tab_permission (role_id, entity, can_read, can_create, can_write, "
            "can_delete, can_approve, can_cancel, can_print, can_export, scope, "
            "created_by, updated_by) VALUES (:r, :e, 1, :w, :w, :w, 0, 0, 0, 0, 'all', 0, 0)"),
            {"r": role_id, "e": ENTITY, "w": w})


def _seed_default_schedule() -> None:
    bind = op.get_bind()
    schedule = sa.table("tab_work_schedule", sa.column("id", sa.BigInteger),
                        sa.column("name", sa.String), sa.column("note", sa.String),
                        sa.column("is_active", sa.Boolean))
    day = sa.table("tab_work_schedule_day", sa.column("schedule_id", sa.BigInteger),
                   sa.column("weekday", sa.SmallInteger), sa.column("day_kind", sa.SmallInteger),
                   sa.column("start_time", sa.Time), sa.column("end_time", sa.Time),
                   sa.column("lunch_start", sa.Time), sa.column("lunch_end", sa.Time))
    bind.execute(sa.insert(schedule).values(
        name=SEED_NAME,
        note="Thứ hai đến thứ bảy 08:00–17:00, nghỉ trưa 12:00–13:00, nghỉ Chủ nhật.",
        is_active=True))
    sid = bind.execute(sa.select(schedule.c.id).where(schedule.c.name == SEED_NAME)).scalar_one()
    rows = [
        dict(schedule_id=sid, weekday=wd, day_kind=FULL, start_time=time(8, 0),
             end_time=time(17, 0), lunch_start=time(12, 0), lunch_end=time(13, 0))
        for wd in range(6)
    ]
    rows.append(dict(schedule_id=sid, weekday=6, day_kind=OFF, start_time=None,
                     end_time=None, lunch_start=None, lunch_end=None))
    op.bulk_insert(day, rows)


def downgrade() -> None:
    op.get_bind().execute(sa.text("DELETE FROM tab_permission WHERE entity = :e"), {"e": ENTITY})
    op.drop_index("ix_wsa_schedule", table_name="tab_work_schedule_assignment")
    op.drop_index("ix_wsa_target", table_name="tab_work_schedule_assignment")
    op.drop_table("tab_work_schedule_assignment")
    op.drop_table("tab_work_schedule_day")
    op.drop_table("tab_work_schedule")
