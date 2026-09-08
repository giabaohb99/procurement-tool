"""bao-CR-316 - tach Ngay tiep nhan ra cot rieng `received_date`

Truoc CR nay chi co MOT cot ngay `request_date`, va `dispatch_pr` (bao-CR-293) GHI DE
no bang ngay dieu phoi. Nghia la cung mot cot: phieu chua tiep nhan thi la ngay LAP,
phieu da tiep nhan thi la ngay TIEP NHAN - con ngay lap goc thi mat han. Bo loc va
bao cao vi the tron hai loai ngay voi nhau.

Sau CR: `request_date` = ngay lap (khong ai ghi de nua), `received_date` = ngay tiep nhan
(rong = chua tiep nhan).

Backfill dung lai du lieu cu theo 3 muc uu tien:
  1. Co dau vet `dispatched` trong tab_audit_log -> `received_date` = ngay cua dau vet,
     va neu loi ghi chu co doan "... <ngay cu> -> <ngay moi>" thi tra `request_date` ve
     <ngay cu> (chinh la ngay lap goc bi ghi de).
  2. Khong co dau vet nhung trang thai da qua buoc dieu phoi -> coi ngay dang co la ngay
     tiep nhan, chep sang `received_date` (ngay lap goc khong con nguon nao de doi chieu
     nen giu nguyen o `request_date`).
  3. Con lai (nhap/cho duyet/tu choi/huy) -> `received_date` rong, `request_date` giu nguyen.

Revision ID: a7c3e91f5b28
Revises: e2f8a5c7d310
Create Date: 2026-09-08
"""
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e91f5b28"
down_revision: Union[str, None] = "e2f8a5c7d310"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Trang thai da di qua buoc dieu phoi - dung cho muc 2 khi khong co dau vet nhat ky.
DISPATCHED_STATUSES = (
    "dispatched", "processing", "purchasing", "purchased", "completed", "done",
)

# Loi ghi chu cua bao-CR-293 co dang "... Ngay tiep nhan 2026-09-05 -> 2026-09-07".
# Bat ngay dung TRUOC dau mui ten; old_base rong thi cho ghi "(trong)" nen khong khop.
_OLD_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})\s*->")


def _as_date_str(value) -> str:
    """Ngay cua dau vet: driver tra datetime hay chuoi deu quy ve YYYY-MM-DD."""
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def _backfill(conn) -> None:
    dispatch_notes: dict[int, tuple[str, str]] = {}
    rows = conn.execute(sa.text(
        "SELECT entity_id, message, created_at FROM tab_audit_log "
        "WHERE entity = 'purchase_request' AND action = 'dispatched' "
        "ORDER BY entity_id, created_at"
    ))
    for entity_id, message, created_at in rows:
        # Dieu phoi lai nhieu lan thi lan CUOI moi la ngay tiep nhan dang hieu luc;
        # nhung ngay LAP goc lai nam o lan DAU. Giu ngay lap cua ban ghi dau tien.
        first_request = dispatch_notes.get(entity_id, ("", ""))[1]
        matched = _OLD_DATE.search(message or "")
        dispatch_notes[entity_id] = (
            _as_date_str(created_at),
            first_request or (matched.group(1) if matched else ""),
        )

    prs = conn.execute(sa.text(
        "SELECT id, status, request_date FROM tab_purchase_request"
    )).fetchall()

    update = sa.text(
        "UPDATE tab_purchase_request SET request_date = :req, received_date = :rec "
        "WHERE id = :id"
    )
    for pr_id, status, request_date in prs:
        request_date = (request_date or "").strip()
        note = dispatch_notes.get(pr_id)
        if note:
            received = note[0] or request_date
            request = note[1] or request_date
        elif (status or "") in DISPATCHED_STATUSES:
            received = request_date
            request = request_date
        else:
            continue
        if received != "" or request != request_date:
            conn.execute(update, {"id": pr_id, "req": request, "rec": received})


def upgrade() -> None:
    op.add_column(
        "tab_purchase_request",
        sa.Column("received_date", sa.String(length=10), nullable=False, server_default=""),
    )
    _backfill(op.get_bind())


def downgrade() -> None:
    # Tra ve mot cot: phieu da tiep nhan thi `request_date` mang lai nghia cu (ngay tiep nhan).
    op.execute(
        "UPDATE tab_purchase_request SET request_date = received_date "
        "WHERE received_date <> ''"
    )
    op.drop_column("tab_purchase_request", "received_date")
