"""Sổ đồng bộ chung `tab_sync_log` — gộp luôn `tab_pos_sync_run` vào

P0 của đồng bộ app đặt xe (doc/dong-bo-dat-xe-duyet-dau/mo-ta-ky-thuat.md §3).

MỘT bảng cho mọi hệ ngoài và cho cả hai hạt dữ liệu (`grain`: lượt chạy · bản
ghi). POS365 đang có bảng riêng `tab_pos_sync_run` — migration này chuyển dữ liệu
sang rồi BỎ bảng đó, vì hai bảng nghĩa là hai màn hình và hai bộ mã trạng thái
lệch nhau cho cùng một khái niệm.

Ba chỗ dễ sai khi đọc lại:

  - **Mã trạng thái phải ĐỔI SỐ, không chép thẳng.** `PosSyncStatus` cũ đánh
    RUNNING=1 · SUCCESS=2 · FAILED=3 · SKIPPED=4; `SyncStatus` mới có thêm
    PENDING=1 ở đầu nên mọi mã lùi một bậc: 1→2 · 2→3 · 3→4 · 4→5. Chép thẳng thì
    mọi lượt chạy THÀNH CÔNG cũ hiện thành "đang chạy".
  - **`event_id` là UNIQUE và KHÔNG được để rỗng.** MySQL coi mỗi chuỗi rỗng là
    một giá trị thật, nên dòng thứ hai đụng khóa ngay. Dòng cũ chuyển sang được
    sinh mã từ `id` của bảng cũ.
  - **`started_at` cũ đổ vào `last_tried_at`**, `error` vào `message`, `detail`
    vào `payload`, `kind` (số) vào `job` (mã chữ).

Chiều xuống dựng lại `tab_pos_sync_run` và trả dữ liệu POS365 về (đảo mã trạng
thái ngược lại), nhưng KHÔNG trả lại được dòng của các nguồn khác — chúng không
có chỗ nào để về.

Revision ID: e5a1b9c73d04
Revises: c1d4f8a37b62
Create Date: 2026-09-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'e5a1b9c73d04'
down_revision: Union[str, None] = 'c1d4f8a37b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  `PosSyncKind` (số) -> `job` (mã chữ). Giữ bản chép ở đây thay vì import từ
#  `app.modules.coffee_point.model`: migration phải chạy đúng như ngày viết ra nó,
#  kể cả khi mã nguồn sau này đổi.
_JOB_BY_KIND = {1: 'pull_orders', 2: 'check_voids', 3: 'monthly_reset',
                4: 'reconcile', 5: 'mirror'}


def _payload_type():
    """MEDIUMTEXT ở MySQL, TEXT ở nơi khác (SQLite của test không biết MEDIUMTEXT)."""
    return sa.Text().with_variant(mysql.MEDIUMTEXT(), 'mysql')


def upgrade() -> None:
    op.create_table(
        'tab_sync_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),

        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('grain', sa.SmallInteger(), nullable=False),
        sa.Column('run_id', sa.BigInteger(), nullable=False),
        sa.Column('direction', sa.SmallInteger(), nullable=False),
        sa.Column('entity', sa.String(length=50), nullable=False),
        sa.Column('action', sa.SmallInteger(), nullable=False),

        sa.Column('legacy_id', sa.String(length=64), nullable=False),
        sa.Column('local_id', sa.BigInteger(), nullable=False),

        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload', _payload_type(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),

        sa.Column('attempt_count', sa.SmallInteger(), nullable=False),
        sa.Column('last_tried_at', sa.String(length=20), nullable=False),
        sa.Column('finished_at', sa.String(length=20), nullable=False),
        sa.Column('warnings', sa.String(length=255), nullable=False),

        sa.Column('job', sa.String(length=50), nullable=False),
        sa.Column('cursor_from', sa.String(length=30), nullable=False),
        sa.Column('cursor_to', sa.String(length=30), nullable=False),
        sa.Column('fetched', sa.Integer(), nullable=False),
        sa.Column('written', sa.Integer(), nullable=False),
        sa.Column('skipped', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', name='uq_sync_log_event'),
    )
    op.create_index(op.f('ix_tab_sync_log_source'), 'tab_sync_log', ['source'])
    op.create_index(op.f('ix_tab_sync_log_grain'), 'tab_sync_log', ['grain'])
    op.create_index(op.f('ix_tab_sync_log_run_id'), 'tab_sync_log', ['run_id'])
    op.create_index(op.f('ix_tab_sync_log_legacy_id'), 'tab_sync_log', ['legacy_id'])
    op.create_index(op.f('ix_tab_sync_log_local_id'), 'tab_sync_log', ['local_id'])
    op.create_index(op.f('ix_tab_sync_log_status'), 'tab_sync_log', ['status'])
    op.create_index(op.f('ix_tab_sync_log_job'), 'tab_sync_log', ['job'])
    op.create_index('ix_sync_log_source_status', 'tab_sync_log', ['source', 'status', 'id'])
    op.create_index('ix_sync_log_source_legacy', 'tab_sync_log',
                    ['source', 'entity', 'legacy_id'])
    op.create_index('ix_sync_log_job_status', 'tab_sync_log', ['source', 'job', 'status', 'id'])

    _move_pos_runs_in()
    op.drop_table('tab_pos_sync_run')


def _move_pos_runs_in() -> None:
    """Chuyển từng dòng `tab_pos_sync_run` thành một dòng RUN của nguồn `pos365`.

    Đi bằng SQL tham số hóa chứ không nối chuỗi: `error` và `detail` là dữ liệu
    do POS365 trả về, nối thẳng vào câu lệnh là vừa hỏng vừa nguy hiểm.
    """
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, created_at, created_by, updated_at, updated_by, kind, status, "
        "       started_at, finished_at, cursor_from, cursor_to, "
        "       fetched, written, skipped, error, detail "
        "FROM tab_pos_sync_run ORDER BY id"
    )).mappings().all()
    if not rows:
        return

    insert = sa.text(
        "INSERT INTO tab_sync_log "
        "(created_at, created_by, updated_at, updated_by, source, grain, run_id, "
        " direction, entity, action, legacy_id, local_id, status, message, payload, "
        " content_hash, event_id, attempt_count, last_tried_at, finished_at, warnings, "
        " job, cursor_from, cursor_to, fetched, written, skipped) "
        "VALUES "
        "(:created_at, :created_by, :updated_at, :updated_by, 'pos365', 1, 0, "
        " 1, 'pos_order', 1, '', 0, :status, :message, :payload, "
        " '', :event_id, 1, :last_tried_at, :finished_at, '', "
        " :job, :cursor_from, :cursor_to, :fetched, :written, :skipped)"
    )
    for r in rows:
        conn.execute(insert, {
            "created_at": r["created_at"],
            "created_by": r["created_by"] or 0,
            "updated_at": r["updated_at"],
            "updated_by": r["updated_by"] or 0,
            #  PosSyncStatus -> SyncStatus: bộ mới chèn PENDING=1 vào đầu nên mọi
            #  mã lùi một bậc. Mã lạ (không nên có) về 4 = lỗi, để nó nổi lên chứ
            #  đừng lặng lẽ thành "thành công".
            "status": {1: 2, 2: 3, 3: 4, 4: 5}.get(int(r["status"] or 0), 4),
            "message": r["error"] or "",
            "payload": r["detail"] or "",
            #  UNIQUE, cấm rỗng. `id` của bảng cũ là duy nhất nên mã sinh ra cũng vậy.
            "event_id": f"pos365:run:{r['id']}",
            "last_tried_at": (r["started_at"] or "")[:20],
            "finished_at": (r["finished_at"] or "")[:20],
            "job": _JOB_BY_KIND.get(int(r["kind"] or 0), ""),
            "cursor_from": r["cursor_from"] or "",
            "cursor_to": r["cursor_to"] or "",
            "fetched": r["fetched"] or 0,
            "written": r["written"] or 0,
            "skipped": r["skipped"] or 0,
        })


def downgrade() -> None:
    op.create_table(
        'tab_pos_sync_run',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.Column('kind', sa.SmallInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('started_at', sa.String(length=19), nullable=False),
        sa.Column('finished_at', sa.String(length=19), nullable=False),
        sa.Column('cursor_from', sa.String(length=30), nullable=False),
        sa.Column('cursor_to', sa.String(length=30), nullable=False),
        sa.Column('fetched', sa.Integer(), nullable=False),
        sa.Column('written', sa.Integer(), nullable=False),
        sa.Column('skipped', sa.Integer(), nullable=False),
        sa.Column('error', sa.Text(), nullable=False),
        sa.Column('detail', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_pos_sync_run_kind'), 'tab_pos_sync_run', ['kind'])
    op.create_index(op.f('ix_tab_pos_sync_run_status'), 'tab_pos_sync_run', ['status'])

    #  Chỉ trả về được phần POS365. Dòng của các nguồn khác mất hẳn — đó là cái
    #  giá của việc đi lùi, không phải lỗi.
    kind_by_job = {job: kind for kind, job in _JOB_BY_KIND.items()}
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT created_at, created_by, updated_at, updated_by, job, status, "
        "       last_tried_at, finished_at, cursor_from, cursor_to, "
        "       fetched, written, skipped, message, payload "
        "FROM tab_sync_log WHERE source = 'pos365' AND grain = 1 ORDER BY id"
    )).mappings().all()
    insert = sa.text(
        "INSERT INTO tab_pos_sync_run "
        "(created_at, created_by, updated_at, updated_by, kind, status, started_at, "
        " finished_at, cursor_from, cursor_to, fetched, written, skipped, error, detail) "
        "VALUES (:created_at, :created_by, :updated_at, :updated_by, :kind, :status, "
        " :started_at, :finished_at, :cursor_from, :cursor_to, :fetched, :written, "
        " :skipped, :error, :detail)"
    )
    for r in rows:
        conn.execute(insert, {
            "created_at": r["created_at"],
            "created_by": r["created_by"] or 0,
            "updated_at": r["updated_at"],
            "updated_by": r["updated_by"] or 0,
            "kind": kind_by_job.get(r["job"] or "", 1),
            #  Đảo lại phép lùi bậc ở chiều lên. PENDING=1 không có bản đối ứng
            #  bên bộ mã cũ nên coi như RUNNING=1.
            "status": {2: 1, 3: 2, 4: 3, 5: 4}.get(int(r["status"] or 0), 1),
            "started_at": (r["last_tried_at"] or "")[:19],
            "finished_at": (r["finished_at"] or "")[:19],
            "cursor_from": r["cursor_from"] or "",
            "cursor_to": r["cursor_to"] or "",
            "fetched": r["fetched"] or 0,
            "written": r["written"] or 0,
            "skipped": r["skipped"] or 0,
            "error": r["message"] or "",
            "detail": r["payload"] or "",
        })

    op.drop_table('tab_sync_log')
