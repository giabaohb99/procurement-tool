"""duoc_cr475_thu_muc_van_ban

Cây thư mục văn bản (duoc-CR-475, phase 03) — thiết kế ở
`frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/phase-03-backend-cay-thu-muc.md`.

1. `tab_doc_folder` — cây CHUNG cho toàn hệ. Tầng gốc là THƯ MỤC PHÁP NHÂN
   (`kind=1`), tự sinh, một dòng cho mỗi `tab_company`. Thư mục thường
   (`kind=2`) chỉ nằm dưới một nhánh pháp nhân. `path`/`depth` là đường dẫn vật
   hóa (`/1/5/9/`) để lọc cả nhánh bằng một chỉ mục thay vì đệ quy.
2. `tab_document_folder_link` — bảng nối NHIỀU-NHIỀU văn bản ↔ thư mục, đúng
   một dòng `is_primary=1` cho mỗi văn bản.
3. `tab_doc_type.default_folder_id` — thư mục mặc định của từng loại văn bản
   (tùy chọn, `0` = chưa khai).
4. BƯỚC DỮ LIỆU (gọn, không autogenerate — repo này drift ~650 dòng mỗi lần
   autogenerate, xem `CLAUDE.md`):
     a. Tạo một thư mục pháp nhân cho MỌI `tab_company` đang có.
     b. Gắn MỌI văn bản đang có (`tab_document`) vào thư mục pháp nhân của
        pháp nhân ban hành, làm thư mục CHÍNH.

   ⚠️ Văn bản có `company_id IS NULL` hoặc `= 0`: đếm trên bản sao LOCAL lúc
   viết migration này ra ĐÚNG 0 dòng (`SELECT COUNT(*) FROM tab_document WHERE
   company_id IS NULL OR company_id = 0` → 0/5). Không có bản sao prod để đếm
   lại, nên bước dữ liệu KHÔNG đoán: những văn bản dạng đó (nếu môi trường
   khác có) bị BỎ QUA ở bước này — không có pháp nhân thì không có thư mục
   pháp nhân nào đúng để gán, và gán đại vào thư mục của pháp nhân #1 sẽ làm
   sai chủ sở hữu văn bản. Ứng dụng có lưới đỡ thứ hai
   (`folder_link_service.ensure_not_orphan`), nhưng lưới đó CŨNG cần
   `company_id` hợp lệ — văn bản `company_id=0` vẫn treo tới khi ai gán đúng
   pháp nhân cho nó. Deploy lên dev-UAT/prod phải chạy lại phép đếm này trước
   khi upgrade và xử lý tay nếu ra khác 0.

Downgrade xóa cả hai bảng + cột `default_folder_id`.

Revision ID: e4a1c9d572b6
Revises: 05a62d38a47a
Create Date: 2026-09-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e4a1c9d572b6'
down_revision: Union[str, None] = '05a62d38a47a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FOLDER_KIND_COMPANY = 1
FOLDER_STATUS_ACTIVE = 1
#  `FolderAccessLevel.CONTRIBUTE` (`doc_catalog/folder_constants.py`) — mức nền
#  của thư mục pháp nhân, dùng ở phase 04.
COMPANY_ROOT_DEFAULT_ACCESS = 2


def upgrade() -> None:
    op.create_table(
        'tab_doc_folder',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('parent_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('kind', sa.SmallInteger(), nullable=False, server_default='2'),
        sa.Column('name', sa.String(150), nullable=False, server_default=''),
        sa.Column('code', sa.String(50), nullable=False, server_default=''),
        sa.Column('description', sa.String(500), nullable=False, server_default=''),
        sa.Column('path', sa.String(255), nullable=False, server_default=''),
        sa.Column('depth', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('status', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('default_access', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_doc_folder_company', 'tab_doc_folder', ['company_id', 'status'])
    op.create_index('ix_doc_folder_parent', 'tab_doc_folder', ['parent_id'])
    op.create_index('ix_doc_folder_path', 'tab_doc_folder', ['path'])

    op.create_table(
        'tab_document_folder_link',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('folder_id', sa.BigInteger(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'folder_id', name='uq_document_folder_link'),
    )
    op.create_index('ix_document_folder_link_document', 'tab_document_folder_link', ['document_id'])
    op.create_index('ix_document_folder_link_folder', 'tab_document_folder_link', ['folder_id'])

    op.add_column('tab_doc_type',
                  sa.Column('default_folder_id', sa.BigInteger(), nullable=False,
                            server_default='0'))

    _backfill()


def _backfill() -> None:
    """(a) một thư mục pháp nhân cho mọi công ty · (b) gắn mọi văn bản đang có
    vào đúng thư mục đó, làm thư mục CHÍNH. Xem lý do bỏ qua `company_id=0`/
    `NULL` ở docstring đầu tệp."""
    conn = op.get_bind()

    company_ids = [row[0] for row in conn.execute(sa.text('SELECT id FROM tab_company'))]
    for company_id in company_ids:
        result = conn.execute(
            sa.text(
                'INSERT INTO tab_doc_folder '
                '(company_id, parent_id, kind, name, code, description, path, depth, '
                ' sort_order, status, default_access, created_by, updated_by) '
                'VALUES (:cid, 0, :kind, \'\', \'\', \'\', \'\', 1, 0, :status, :access, 0, 0)'
            ),
            {'cid': company_id, 'kind': FOLDER_KIND_COMPANY, 'status': FOLDER_STATUS_ACTIVE,
             'access': COMPANY_ROOT_DEFAULT_ACCESS},
        )
        root_id = result.lastrowid
        conn.execute(
            sa.text('UPDATE tab_doc_folder SET path = :path WHERE id = :id'),
            {'path': f'/{root_id}/', 'id': root_id},
        )

    #  Gắn văn bản → thư mục pháp nhân của nó. `NOT EXISTS` để idempotent nếu
    #  migration này lỡ chạy lại (khớp lối `05a62d38a47a._seed_cost_types`).
    conn.execute(sa.text(
        'INSERT INTO tab_document_folder_link (document_id, folder_id, is_primary, created_by) '
        'SELECT d.id, f.id, 1, 0 '
        'FROM tab_document d '
        'JOIN tab_doc_folder f ON f.company_id = d.company_id AND f.kind = :kind '
        'WHERE d.company_id IS NOT NULL AND d.company_id <> 0 '
        '  AND NOT EXISTS ('
        '    SELECT 1 FROM tab_document_folder_link l WHERE l.document_id = d.id)'
    ), {'kind': FOLDER_KIND_COMPANY})


def downgrade() -> None:
    op.drop_column('tab_doc_type', 'default_folder_id')

    op.drop_index('ix_document_folder_link_folder', table_name='tab_document_folder_link')
    op.drop_index('ix_document_folder_link_document', table_name='tab_document_folder_link')
    op.drop_table('tab_document_folder_link')

    op.drop_index('ix_doc_folder_path', table_name='tab_doc_folder')
    op.drop_index('ix_doc_folder_parent', table_name='tab_doc_folder')
    op.drop_index('ix_doc_folder_company', table_name='tab_doc_folder')
    op.drop_table('tab_doc_folder')
