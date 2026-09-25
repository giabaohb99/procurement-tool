"""van_ban_chan_hai_goc_phap_nhan

Chặn HAI gốc thư mục pháp nhân cho cùng một công ty (M8, rà soát 23/09/2026 —
`frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/reports/
code-reviewer-260923-2053-van-ban.md`).

`folder_root_service.ensure_company_roots` trước đây check-then-insert THUẦN:
hai request tạo cùng một pháp nhân (hoặc seed chạy trùng lúc `_company_root_id`
tự vá gốc thiếu) đều đọc "chưa có gốc" rồi đều chèn → hai dòng `kind=1` cho
cùng một `company_id`, thư mục văn bản của pháp nhân đó chia đôi ngẫu nhiên
giữa hai gốc.

Thêm cột `root_company_id` (`NULL` với thư mục THƯỜNG, `= company_id` với thư
mục GỐC) + chỉ mục UNIQUE trên cột đó. `NULL` không đụng UNIQUE (ngữ nghĩa SQL
chuẩn — nhiều `NULL` không va nhau), nên thư mục thường không bị ảnh hưởng; chỉ
gốc mới bị ép duy nhất. Không dùng cột SINH (`GENERATED`) của MySQL để tránh
lệch cú pháp với SQLite (bộ test dùng `Base.metadata.create_all`, cùng chủ
trương "không FK" đã ghi ở đầu `folder_model.py`) — tầng SERVICE tự gán giá
trị (`folder_root_service.ensure_company_roots`).

Bước dữ liệu: backfill `root_company_id = company_id` cho MỌI dòng `kind=1`
đang có (nếu môi trường có sẵn hai gốc trùng company_id — dữ liệu hỏng từ lỗi
đang vá — UNIQUE sẽ chặn backfill dòng thứ hai; migration KHÔNG tự dọn, in ra
cảnh báo để người vận hành xóa/gộp tay trước khi chạy lại).

Revision ID: 32b55e9888f6
Revises: 83679db84fd1
Create Date: 2026-09-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '32b55e9888f6'
down_revision: Union[str, None] = '83679db84fd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FOLDER_KIND_COMPANY = 1


def upgrade() -> None:
    op.add_column('tab_doc_folder', sa.Column('root_company_id', sa.BigInteger(), nullable=True))

    #  Backfill: gốc pháp nhân ĐANG CÓ nhận đúng `company_id` của chính nó.
    #  Nếu có hai gốc trùng `company_id` (dữ liệu hỏng từ lỗi M8 đang vá), dòng
    #  đầu (id nhỏ hơn) được gán trước — dòng thứ hai VẪN giữ `NULL` (UNIQUE
    #  chưa tạo nên chưa chặn ở bước này), migration in cảnh báo để người vận
    #  hành xử lý tay TRƯỚC khi câu tạo UNIQUE bên dưới chạy tới đúng dòng đó.
    connection = op.get_bind()
    rows = connection.execute(sa.text(
        "SELECT id, company_id FROM tab_doc_folder WHERE kind = :kind ORDER BY company_id, id"
    ), {"kind": FOLDER_KIND_COMPANY}).fetchall()
    seen_companies: set[int] = set()
    duplicates: list[tuple[int, int]] = []
    for folder_id, company_id in rows:
        if company_id in seen_companies:
            duplicates.append((folder_id, company_id))
            continue
        seen_companies.add(company_id)
        connection.execute(sa.text(
            "UPDATE tab_doc_folder SET root_company_id = :company_id WHERE id = :id"
        ), {"company_id": company_id, "id": folder_id})
    if duplicates:
        print(  # noqa: T201 — cảnh báo vận hành, cố ý in ra log migration
            f"⚠️  {len(duplicates)} gốc pháp nhân TRÙNG company_id chưa gán "
            f"root_company_id (giữ NULL để UNIQUE bên dưới không chặn upgrade): "
            f"{duplicates}. Xử lý tay: gộp văn bản của gốc thừa sang gốc còn lại "
            f"rồi xóa dòng thừa."
        )

    op.create_index('ux_doc_folder_root_company', 'tab_doc_folder', ['root_company_id'],
                    unique=True)


def downgrade() -> None:
    op.drop_index('ux_doc_folder_root_company', table_name='tab_doc_folder')
    op.drop_column('tab_doc_folder', 'root_company_id')
