"""backfill_ncc_pur — chuyển NCC cũ (suggested_supplier*) sang cụm 'pur' của supplier_info

Cột suggested_supplier* xưa CHỈ phía thu mua/nhập liệu điền được (người yêu cầu bị khóa) ->
chuyển vào cụm 'pur', cụm 'req' để rỗng để bộ phận yêu cầu KHÔNG thấy NCC do thu mua/import.

Tách riêng khỏi f3a7c1e9b2d4 để chạy ĐỒNG NHẤT mọi môi trường: dev đã áp f3a7c1e9b2d4 từ
trước khi có code backfill (nên backfill nhúng không chạy), còn VPS thì chạy fresh — migration
này bảo đảm cả hai đều backfill đúng một lần. Idempotent: CHỈ đụng phiếu supplier_info còn rỗng.

Dùng SQLAlchemy tham số hóa + json.dumps(ensure_ascii=False) để tránh mojibake tiếng Việt.

Revision ID: b4d6f8a02c15
Revises: a2c4e6f80b13
Create Date: 2026-07-29 00:00:00.000000
"""
import json
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "b4d6f8a02c15"
down_revision: Union[str, None] = "a2c4e6f80b13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Phiếu sinh tự động từ Yêu cầu khảo sát/báo giá đều mở đầu note bằng "Sinh tự động từ".
_AUTO_NOTE_PREFIX = "Sinh tự động từ"


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(text(
        "SELECT id, suggested_supplier, suggested_supplier_tax_code, "
        "suggested_supplier_contact, note FROM tab_purchase_request "
        "WHERE (supplier_info IS NULL OR supplier_info = '') "
        "AND (COALESCE(suggested_supplier, '') <> '' "
        "OR COALESCE(suggested_supplier_tax_code, '') <> '' "
        "OR COALESCE(suggested_supplier_contact, '') <> '')"
    )).fetchall()
    for r in rows:
        note = r[4] or ""
        payload = {
            "req": {"name": "", "tax_code": "", "contact": ""},
            "pur": {"name": r[1] or "", "tax_code": r[2] or "", "contact": r[3] or ""},
            "from_survey": bool(note.startswith(_AUTO_NOTE_PREFIX)),
        }
        conn.execute(
            text("UPDATE tab_purchase_request SET supplier_info = :v WHERE id = :id"),
            {"v": json.dumps(payload, ensure_ascii=False), "id": r[0]},
        )

    # Chuẩn hóa cờ from_survey cho phiếu ĐÃ có supplier_info từ trước (materialize bằng prefix cũ
    # "Yêu cầu báo giá" nên bỏ sót note "Yêu cầu khảo sát"). CHỈ sửa cờ khi cụm 'req' rỗng
    # (không đụng dữ liệu NCC do người yêu cầu nhập) -> an toàn, idempotent, đúng mọi môi trường.
    rows2 = conn.execute(text(
        "SELECT id, supplier_info, note FROM tab_purchase_request "
        "WHERE supplier_info IS NOT NULL AND supplier_info <> '' AND note LIKE :pat"
    ), {"pat": _AUTO_NOTE_PREFIX + "%"}).fetchall()
    for r in rows2:
        try:
            j = json.loads(r[1])
        except (ValueError, TypeError):
            continue
        req = j.get("req") or {}
        if req.get("name") or req.get("tax_code") or req.get("contact"):
            continue  # người yêu cầu có nhập NCC -> không tự ý gắn nguồn khảo sát
        if j.get("from_survey") is True:
            continue  # đã đúng
        j["from_survey"] = True
        conn.execute(
            text("UPDATE tab_purchase_request SET supplier_info = :v WHERE id = :id"),
            {"v": json.dumps(j, ensure_ascii=False), "id": r[0]},
        )


def downgrade() -> None:
    # Không hạ cấp dữ liệu: cụm 'pur' vẫn có thể suy lại từ suggested_supplier* nếu cần.
    pass
