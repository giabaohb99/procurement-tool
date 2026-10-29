"""loai_van_ban_can_cu_ke_hoach_nhan_su: gieo loai van ban CCKHNS (insert-only)

Revision ID: hcplan04
Revises: hcplan03
Create Date: 2026-10-28

duoc-CR-690. Nut «Tai tep len» o muc Van ban lien ket cua ke hoach nhan su tu tao mot van ban loai `CCKHNS`. Loai la van ban
CA NHAN (`is_personal`) de tep co the chua bang luong khong bi doc theo pham vi vai tro. Cung gia tri voi
`app/seed_data/document_phase1.HEADCOUNT_BASIS_DOC_TYPE`. Chi chen khi chua co ma nay (khong ghi de loai do van thu tu lap).
Downgrade chi xoa loai neu CHUA co van ban nao thuoc loai.
(Da bo duoc-CR-692: buoc thu gon mau goi y — bang mau da bi DROP o hcplan05.) Truoc day kem: thu gon «Mau goi y» ve 4 khoan (Luong, Phu cap, Bao hiem + cong doan 23,5%, Thuong thang 13) neu mau con dung bo 8 khoan ban dau
(`legacy_seed.simplify_suggested_template`) — ke hoach da lap khong doi. Downgrade khong khoi phuc bo 8 khoan.

VIET TAY (khong autogenerate): repo nay autogenerate troi ~650 dong moi lan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "hcplan04"
down_revision: Union[str, None] = "hcplan03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CODE = "CCKHNS"
NAME = "Căn cứ kế hoạch nhân sự"
DESC = ("Tệp căn cứ (quyết định, tờ trình…) tải lên từ kế hoạch nhân sự; "
        "chỉ người tạo và người được chia sẻ đọc được.")


def _doc_type_table() -> sa.Table:
    return sa.table(
        "tab_doc_type", sa.column("id", sa.BigInteger), sa.column("code", sa.String), sa.column("name", sa.String),
        sa.column("group_code", sa.String), sa.column("description", sa.Text), sa.column("id_scheme", sa.SmallInteger),
        sa.column("number_when", sa.SmallInteger), sa.column("default_secrecy", sa.SmallInteger),
        sa.column("is_confidential_type", sa.Boolean), sa.column("is_personal", sa.Boolean),
        sa.column("needs_approval", sa.Boolean), sa.column("needs_signature", sa.Boolean),
        sa.column("needs_decision", sa.Boolean), sa.column("needs_request", sa.Boolean),
        sa.column("review_cycle_months", sa.SmallInteger), sa.column("retention_months", sa.SmallInteger),
        sa.column("default_flow_id", sa.BigInteger), sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean), sa.column("auto_issue_after_approval", sa.Boolean),
        sa.column("default_folder_id", sa.BigInteger), sa.column("created_by", sa.BigInteger),
        sa.column("updated_by", sa.BigInteger))


def upgrade() -> None:
    bind = op.get_bind()
    t = _doc_type_table()
    if bind.execute(sa.select(t.c.id).where(sa.func.upper(t.c.code) == CODE)).first() is not None:
        return
    next_sort = (bind.execute(sa.select(sa.func.max(t.c.sort_order))).scalar() or 0) + 1
    #  `created_by` / `updated_by` / `default_folder_id` chỉ có mặc định phía ORM -> phải ghi tường minh (created_at: server_default).
    op.bulk_insert(t, [{
        "code": CODE, "name": NAME, "group_code": "C", "description": DESC, "id_scheme": 1, "number_when": 1,
        "default_secrecy": 2, "is_confidential_type": True, "is_personal": True, "needs_approval": False,
        "needs_signature": False, "needs_decision": False, "needs_request": False, "review_cycle_months": 0,
        "retention_months": 120, "default_flow_id": 0, "sort_order": next_sort, "is_active": True,
        "auto_issue_after_approval": True, "default_folder_id": 0,
        "created_by": 0, "updated_by": 0}])


def downgrade() -> None:
    bind = op.get_bind()
    t = _doc_type_table()
    doc = sa.table("tab_document", sa.column("doc_type_id", sa.BigInteger))
    type_id = bind.execute(sa.select(t.c.id).where(sa.func.upper(t.c.code) == CODE)).scalar()
    if type_id is None:
        return
    if bind.execute(sa.select(doc.c.doc_type_id).where(doc.c.doc_type_id == type_id).limit(1)).first() is not None:
        return   # đã có văn bản thuộc loại — giữ loại, tránh văn bản mồ côi
    bind.execute(sa.delete(t).where(t.c.id == type_id))
