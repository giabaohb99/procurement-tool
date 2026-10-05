"""agent hub: so moi truong + nhat ky thao tac VPS + so su co (ai-CR-067..070, phase 6-7)

Ba bang moi, khong dung bang cu:
  - tab_agent_env      : moi dong mot moi truong bot duoc deploy / xem / thao tac (nap san dev + prod)
  - tab_agent_op       : moi lenh bot chay tren VPS (ghi truoc khi chay, kem sao luu + cach hoan tac)
  - tab_agent_incident : moi lan mot moi truong hong health lien tiep (cham doan, tu chua, thoi gian gian doan)

Revision ID: e8a3c5f1d7b2
Revises: wkhist01
"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e8a3c5f1d7b2'
down_revision: Union[str, None] = 'wkhist01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols() -> list:
    return [
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
    ]


def upgrade() -> None:
    env = op.create_table(
        'tab_agent_env',
        sa.Column('name', sa.String(length=40), nullable=False),
        sa.Column('kind', sa.SmallInteger(), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('ssh_user', sa.String(length=60), nullable=False),
        sa.Column('dir', sa.String(length=255), nullable=False),
        sa.Column('compose_args', sa.String(length=255), nullable=False),
        sa.Column('branch', sa.String(length=80), nullable=False),
        sa.Column('health_url', sa.String(length=255), nullable=False),
        sa.Column('db_name', sa.String(length=64), nullable=False),
        sa.Column('auto_heal', sa.Boolean(), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=False),
        sa.Column('last_health_code', sa.Integer(), nullable=False),
        sa.Column('last_health_at', sa.DateTime(), nullable=True),
        sa.Column('fail_streak', sa.Integer(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        *_audit_cols(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_agent_env_name'), 'tab_agent_env', ['name'], unique=False)

    op.create_table(
        'tab_agent_op',
        sa.Column('env_id', sa.BigInteger(), nullable=False),
        sa.Column('kind', sa.SmallInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('backup_ref', sa.String(length=255), nullable=False),
        sa.Column('undo_params', sa.JSON(), nullable=False),
        sa.Column('undo_of_op_id', sa.BigInteger(), nullable=False),
        sa.Column('undone_by_op_id', sa.BigInteger(), nullable=False),
        sa.Column('incident_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.String(length=50), nullable=False),
        sa.Column('auto', sa.Boolean(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('output', sa.Text(), nullable=False),
        sa.Column('error', sa.String(length=1000), nullable=False),
        *_audit_cols(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_agent_op_env_id'), 'tab_agent_op', ['env_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_op_status'), 'tab_agent_op', ['status'], unique=False)
    op.create_index(op.f('ix_tab_agent_op_incident_id'), 'tab_agent_op', ['incident_id'], unique=False)

    op.create_table(
        'tab_agent_incident',
        sa.Column('env_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('symptom', sa.String(length=255), nullable=False),
        sa.Column('signature', sa.String(length=120), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('diagnosis', sa.Text(), nullable=False),
        sa.Column('cause', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=40), nullable=False),
        sa.Column('heal_op_id', sa.BigInteger(), nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        *_audit_cols(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_agent_incident_env_id'), 'tab_agent_incident', ['env_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_incident_status'), 'tab_agent_incident', ['status'], unique=False)
    op.create_index(op.f('ix_tab_agent_incident_signature'), 'tab_agent_incident', ['signature'], unique=False)

    #  Nạp sẵn hai môi trường đang có (dev + prod chung một VPS; host trống = máy trong .env của runner).
    #  Chỉ chữ ASCII — không chữ tiếng Việt trong dữ liệu nạp.
    now = datetime.now()
    common = dict(host='', port=0, ssh_user='', note='', last_health_code=0, last_health_at=None,
                  fail_streak=0, revoked_at=None, created_at=now, created_by=0, updated_at=now, updated_by=0)
    op.bulk_insert(env, [
        dict(name='dev', kind=1, dir='~/procurement-tool-dev',
             compose_args='--env-file .env.dev -f docker-compose.dev.yml', branch='erp-v2',
             health_url='https://devthumua.degoholding.vn/api/health', db_name='procurement_dev',
             auto_heal=True, **common),
        dict(name='prod', kind=2, dir='~/procurement-tool', compose_args='-f docker-compose.production.yml',
             branch='main', health_url='https://thumua.degoholding.vn/api/health', db_name='procurement',
             auto_heal=False, **common),
    ])


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_incident_signature'), table_name='tab_agent_incident')
    op.drop_index(op.f('ix_tab_agent_incident_status'), table_name='tab_agent_incident')
    op.drop_index(op.f('ix_tab_agent_incident_env_id'), table_name='tab_agent_incident')
    op.drop_table('tab_agent_incident')
    op.drop_index(op.f('ix_tab_agent_op_incident_id'), table_name='tab_agent_op')
    op.drop_index(op.f('ix_tab_agent_op_status'), table_name='tab_agent_op')
    op.drop_index(op.f('ix_tab_agent_op_env_id'), table_name='tab_agent_op')
    op.drop_table('tab_agent_op')
    op.drop_index(op.f('ix_tab_agent_env_name'), table_name='tab_agent_env')
    op.drop_table('tab_agent_env')
