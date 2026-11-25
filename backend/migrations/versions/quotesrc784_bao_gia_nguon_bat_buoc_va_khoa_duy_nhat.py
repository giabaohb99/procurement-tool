"""bao_gia_nguon_bat_buoc_va_khoa_duy_nhat: `tab_product_price_quote` co `source_type` / `source_id` NOT NULL + khoa duy nhat (duoc-CR-784, phase 03)

Revision ID: quotesrc784
Revises: srcmerge784
Create Date: 2026-11-25

Chu du an chot 25/11/2026: bao gia phai co nguon (C2: 1 Nhap tay, 2 Nhap Excel; 3 de danh cho YCBG), nhap tay `source_id = 0` (C3),
Excel de gia thi nguon doi sang dot nhap cuoi (C4), khoa duy nhat `(product_code, supplier_code, valid_from)` - chinh khoa nhap Excel dung (C5).

upgrade:
  0. DUNG neu da co bao gia trung khoa `(ma, NCC, ngay hieu luc)` - KHONG xoa am tham (MySQL khong hoan tac DDL nen kiem truoc moi
     thay doi): nem loi ghi ro cac nhom trung, nguoi van hanh gop tay roi chay lai. Cau doc tuong ung nam o `DUPLICATE_QUOTE_SQL`;
  1. them `source_type SMALLINT NOT NULL` (tam mac dinh 1) + `source_id BIGINT NOT NULL` (tam mac dinh 0);
  2. dien lai nguon: bao gia khop nhat ky nhap Excel (`tab_import_log`, `category` `quote_new` / `quote_update`; dot `module = 5`,
     `mode = 1` thuc ghi, `status = 2` xong; `updated_by` cua bao gia = nguoi nhap va `updated_at` cach dong nhat ky khong qua 300 giay):
     nguon = lan GHI GIA (them moi, hoac cap nhat co doi don gia / VAT) muoi nhat khong sau lan cham cuoi cua Excel -> `(2, id dot)`;
     khop ma ho (lan cham cuoi thuoc hai dot) hoac khong khop (sua tay sau do, nhat ky khong con) -> giu `(1, 0)`, in so ma ho.
     Nhat ky chi giu toi 300 dong thong tin moi dot nen dot lon co the khop thieu - phan thieu o lai `(1, 0)`;
  3. tao `uq_ppq_key` + `ix_ppq_source`; bo mac dinh tam cua hai cot (ghi moi phai dat ro).
downgrade: bo `uq_ppq_key`, `ix_ppq_source` va hai cot (du lieu nguon mat, khong con noi nao dung).

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Chay duoc tren MySQL 8 va SQLite (bai kiem). Hai ham
`find_duplicate_quote_keys` / `backfill_quote_sources` nhan ket noi de bai kiem goi truc tiep tren du lieu mau.
"""
import re
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "quotesrc784"
down_revision: Union[str, None] = "srcmerge784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

QUOTE = "tab_product_price_quote"
#  Chep tay vao migration (khong import ma ung dung: migration phai dung yen theo thoi gian): QuoteSourceType + ImportModule / ImportMode / ImportStatus.
MANUAL, EXCEL_IMPORT = 1, 2
MODULE_PACKAGING_QUOTE, MODE_APPLY, STATUS_DONE = 5, 1, 2
#  Dong nhat ky va ban ghi bao gia cung do MOT giao dich nhap ghi ra (cung dong ho may chu CSDL) - lech toi da bay nhieu nay giay.
MATCH_WINDOW_SECONDS = 300
MAX_LISTED = 10

#  Cau DOC (khong ghi) de van hanh chay tren dev truoc khi len: ra dong nao thi gop tay roi moi chay migration.
DUPLICATE_QUOTE_SQL = (f"SELECT product_code, supplier_code, valid_from, COUNT(*) AS so_dong, GROUP_CONCAT(id) AS cac_id FROM {QUOTE} "
                       "GROUP BY product_code, supplier_code, valid_from HAVING COUNT(*) > 1")
_DUPLICATE_COUNT_SQL = (f"SELECT product_code, supplier_code, valid_from, COUNT(*) FROM {QUOTE} "
                        "GROUP BY product_code, supplier_code, valid_from HAVING COUNT(*) > 1 ORDER BY product_code, valid_from")
#  Dong nhat ky cua `quote_import.run`: "Them bao gia MA · NCC X · tu dd/mm/yyyy: ..." / "Cap nhat bao gia MA · NCC X · tu dd/mm/yyyy: Don gia: ..."
_LOG_RE = re.compile(r"^(?:Thêm|Cập nhật) báo giá (?P<code>.+?) · NCC (?P<sup>.+?) · từ (?P<d>\d{2})/(?P<m>\d{2})/(?P<y>\d{4}): (?P<rest>.*)$", re.S)
_EMPTY_SUPPLIER = "(trống)"


def _as_datetime(value) -> datetime | None:
    """MySQL tra `datetime`; SQLite (bai kiem) tra chuoi ISO."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _as_date_key(value) -> str:
    return str(value)[:10]


def find_duplicate_quote_keys(conn) -> list[tuple]:
    """Cac nhom `(ma, NCC, ngay hieu luc, so dong)` dang trung khoa. Rong = an toan de dat khoa duy nhat."""
    return [tuple(r) for r in conn.execute(sa.text(_DUPLICATE_COUNT_SQL)).all()]


def _import_log_index(conn) -> dict:
    """{(MA, NCC, yyyy-mm-dd): [(thoi diem dong nhat ky, id dot, nguoi nhap, co ghi gia khong)]} - moi lan GHI THAT cua nhap Excel."""
    rows = conn.execute(sa.text(
        "SELECT l.message, l.created_at, b.id, b.created_by FROM tab_import_log l JOIN tab_import_batch b ON b.id = l.batch_id "
        "WHERE b.module = :module AND b.mode = :mode AND b.status = :done AND l.category IN ('quote_new', 'quote_update')"),
        {"module": MODULE_PACKAGING_QUOTE, "mode": MODE_APPLY, "done": STATUS_DONE}).all()
    index: dict = {}
    for message, logged_at, batch_id, batch_user in rows:
        m = _LOG_RE.match(message or "")
        if not m:
            continue
        #  Them moi va cap nhat doi don gia / VAT la lan GHI GIA; cap nhat chi doi ghi chu thi nguon giu nguyen (C4) nhung van la
        #  mot lan cham vao dong (de nhan ra dong khong bi sua tay sau do).
        writes_price = message.startswith("Thêm") or "Đơn giá:" in m["rest"] or "VAT:" in m["rest"]
        supplier = "" if m["sup"] == _EMPTY_SUPPLIER else m["sup"].upper()
        key = (m["code"].upper(), supplier, f"{m['y']}-{m['m']}-{m['d']}")
        index.setdefault(key, []).append((_as_datetime(logged_at), batch_id, batch_user, writes_price))
    return index


def _source_batch_for(quote_updated_at, quote_updated_by, logs) -> tuple[str, int]:
    """("excel", id dot) | ("ambiguous", 0) | ("manual", 0) cho MOT bao gia, tu cac dong nhat ky cung khoa cua no.

    Lan cham cuoi cua Excel = dong nhat ky cung nguoi nhap, cach `updated_at` cua bao gia khong qua cua so; khong co thi bao gia da bi sua
    tay sau do (hoac nhat ky khong con) -> nhap tay. Nguon = lan GHI GIA muoi nhat khong sau lan cham do.
    """
    stamp = _as_datetime(quote_updated_at)
    if stamp is None:
        return "manual", 0
    touches = [e for e in logs if e[0] is not None and e[2] == quote_updated_by
               and abs((stamp - e[0]).total_seconds()) <= MATCH_WINDOW_SECONDS]
    if not touches:
        return "manual", 0
    if len({e[1] for e in touches}) > 1:
        return "ambiguous", 0
    last_touch = max(e[0] for e in touches)
    writers = [e for e in logs if e[3] and e[0] is not None and e[0] <= last_touch]
    if not writers:
        return "manual", 0
    return "excel", max(writers, key=lambda e: (e[0], e[1]))[1]


def backfill_quote_sources(conn) -> dict:
    """Dat `(2, id dot)` cho bao gia khop nhat ky nhap Excel; con lai giu `(1, 0)`. Tra so dong: excel / ambiguous / manual."""
    index = _import_log_index(conn)
    counts = {"excel": 0, "ambiguous": 0, "manual": 0}
    updates: list[dict] = []
    for qid, code, supplier, valid_from, updated_at, updated_by in conn.execute(sa.text(
            f"SELECT id, product_code, supplier_code, valid_from, updated_at, updated_by FROM {QUOTE}")).all():
        logs = index.get(((code or "").upper(), (supplier or "").upper(), _as_date_key(valid_from)), [])
        kind, batch_id = _source_batch_for(updated_at, updated_by, logs)
        counts[kind] += 1
        if kind == "excel":
            updates.append({"id": qid, "batch": batch_id})
    if updates:
        conn.execute(sa.text(f"UPDATE {QUOTE} SET source_type = :excel, source_id = :batch WHERE id = :id"),
                     [{"excel": EXCEL_IMPORT, **u} for u in updates])
    return counts


def upgrade() -> None:
    conn = op.get_bind()
    duplicates = find_duplicate_quote_keys(conn)
    if duplicates:
        listed = "; ".join(f"{c} / NCC '{s}' / {d} ({n} dòng)" for c, s, d, n in duplicates[:MAX_LISTED])
        raise RuntimeError(
            f"[quotesrc784] DỪNG: có {len(duplicates)} nhóm báo giá trùng khóa (mã, NCC, ngày hiệu lực): {listed}"
            f"{' ...' if len(duplicates) > MAX_LISTED else ''}. Migration KHÔNG tự xóa dòng nào. Xem đủ bằng câu đọc: "
            f"{DUPLICATE_QUOTE_SQL} — gộp / xóa tay các dòng thừa ở màn Báo giá VTBB rồi chạy lại.")
    with op.batch_alter_table(QUOTE) as batch:      # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        batch.add_column(sa.Column("source_type", sa.SmallInteger(), nullable=False, server_default=str(MANUAL)))
        batch.add_column(sa.Column("source_id", sa.BigInteger(), nullable=False, server_default="0"))
    stats = backfill_quote_sources(conn)
    print(f"[quotesrc784] nguồn báo giá: {stats['excel']} dòng nhập Excel (khớp nhật ký), {stats['manual']} dòng nhập tay, "
          f"{stats['ambiguous']} dòng khớp mơ hồ (giữ nhập tay)")
    with op.batch_alter_table(QUOTE) as batch:
        batch.create_unique_constraint("uq_ppq_key", ["product_code", "supplier_code", "valid_from"])
        batch.create_index("ix_ppq_source", ["source_type", "source_id"])
        batch.alter_column("source_type", existing_type=sa.SmallInteger(), existing_nullable=False, server_default=None)
        batch.alter_column("source_id", existing_type=sa.BigInteger(), existing_nullable=False, server_default=None)


def downgrade() -> None:
    with op.batch_alter_table(QUOTE) as batch:
        batch.drop_index("ix_ppq_source")
        batch.drop_constraint("uq_ppq_key", type_="unique")
        batch.drop_column("source_id")
        batch.drop_column("source_type")
