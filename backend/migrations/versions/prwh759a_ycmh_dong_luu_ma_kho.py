"""bao-CR-759: tab_purchase_request_item.warehouse_code — dòng YCMH lưu MÃ kho, không chỉ TÊN kho

Revision ID: prwh759a
Revises: stix723
Create Date: 2026-11-16

Dòng YCMH trước giờ chỉ lưu TÊN kho (cột `warehouse`, chữ tự do khớp `tab_warehouse.name`), trong khi ĐMH, lần
giao, phiếu nhập kho, tồn kho đều lưu MÃ kho. Đổi tên kho là dòng YCMH mất liên kết, và mọi chỗ cần mã (tạo ĐMH từ
YCMH, in phiếu) phải tự tra ngược tên -> mã — giao diện v2 quên bước đó nên ĐMH tạo từ YCMH bị trống kho nhận.

Các bước (VIẾT TAY, không autogenerate — repo này autogenerate trôi ~650 dòng mỗi lần):
 (a) thêm cột `warehouse_code` VARCHAR(25) NOT NULL mặc định '' (cùng độ dài `tab_warehouse.code`);
 (b) điền mã cho dòng đã có tên kho mà chưa có mã: khớp ĐÚNG tên với `tab_warehouse.name`; trùng tên (danh mục
     không chặn trùng tên) thì lấy kho đang dùng, rồi kho có id nhỏ nhất. Đã đo trên prod 16/11/2026: 817/817 dòng
     khớp tên đúng từng byte;
 (c) in số dòng có tên kho mà không khớp kho nào (để nguyên mã trống — tên cũ vẫn giữ, máy chủ tự suy lại khi lưu).

Cột `warehouse` (tên) GIỮ NGUYÊN: báo cáo, xuất Excel, trợ lý AI, bản in v1 đang đọc nó. Từ nay máy chủ giữ hai cột
khớp nhau lúc lưu (`purchase_request/warehouse_ref.py`).

Chạy lại được: cột đã có thì bỏ qua bước (a); bước (b) chỉ xét dòng còn mã trống. So khớp tên làm trong Python
(khớp đúng từng byte, tránh lệch collation giữa hai bảng), ghi theo lô id — chạy được cả trên SQLite của bài kiểm.

Nối thẳng sau `stix723` (head của prod), KHÔNG sau `kn756a`: duoc-CR-755/756 chưa duyệt lên prod, nối sau chúng thì
cherry-pick CR-759 lên main là gãy chuỗi. Trên erp-v2 hai nhánh gặp lại ở migration gộp `mrg759a`.

downgrade: bỏ cột `warehouse_code`. Tên kho vẫn còn ở cột `warehouse` nên không mất dữ liệu nào.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "prwh759a"
down_revision: Union[str, None] = "stix723"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_purchase_request_item"
COLUMN = "warehouse_code"

_BATCH = 500


def _code_by_name(bind) -> dict[str, str]:
    """Tên kho -> mã, khớp ĐÚNG từng byte. Trùng tên thì kho đang dùng trước, rồi id nhỏ nhất."""
    rows = bind.execute(sa.text(
        "SELECT code, name FROM tab_warehouse ORDER BY is_active DESC, id ASC")).fetchall()
    out: dict[str, str] = {}
    for code, name in rows:
        if (code or "").strip() and (name or "").strip():
            out.setdefault(name.strip(), code.strip())
    return out


def backfill_codes(bind) -> int:
    """Bước (b) + (c): điền mã cho dòng còn mã trống; trả số dòng có tên mà không khớp kho nào.

    So khớp làm trong Python chứ không UPDATE ... (SELECT ...) trên CSDL: hai bảng có thể khác collation
    ("Illegal mix of collations" trên MySQL), và collation không phân biệt hoa thường sẽ khớp cả tên chỉ
    giống gần đúng — thứ đã đo trên prod là khớp ĐÚNG từng byte.
    """
    by_name = _code_by_name(bind)
    rows = bind.execute(sa.text(
        f"SELECT id, warehouse FROM {TABLE} WHERE {COLUMN} = '' AND warehouse <> ''")).fetchall()
    ids_by_code: dict[str, list[int]] = {}
    unmatched = 0
    for row_id, name in rows:
        code = by_name.get((name or "").strip())
        if code:
            ids_by_code.setdefault(code, []).append(int(row_id))
        else:
            unmatched += 1
    stmt = sa.text(f"UPDATE {TABLE} SET {COLUMN} = :code WHERE id IN :ids").bindparams(
        sa.bindparam("ids", expanding=True))
    for code, ids in ids_by_code.items():
        for start in range(0, len(ids), _BATCH):
            bind.execute(stmt, {"code": code, "ids": ids[start:start + _BATCH]})
    return unmatched


def upgrade() -> None:
    bind = op.get_bind()
    if COLUMN not in {c["name"] for c in sa.inspect(bind).get_columns(TABLE)}:
        op.add_column(TABLE, sa.Column(COLUMN, sa.String(25), nullable=False, server_default=""))
    unmatched = backfill_codes(bind)
    print(f"[prwh759a] dòng YCMH có tên kho nhưng không khớp kho nào (để mã trống): {unmatched}")


def downgrade() -> None:
    bind = op.get_bind()
    if COLUMN in {c["name"] for c in sa.inspect(bind).get_columns(TABLE)}:
        op.drop_column(TABLE, COLUMN)
