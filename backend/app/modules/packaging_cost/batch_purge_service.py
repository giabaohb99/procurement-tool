"""Xem trước và xóa dữ liệu theo LÔ NHẬP của cụm Giá NVL sản xuất (duoc-CR-784, phase 07).

Ba loại lô của Quản lý Import (mã `ImportModule`) và dòng dữ liệu mỗi loại để lại:
  4 Định mức bao bì   -> `tab_packaging_bom.import_batch_id = lô` (thành phần xóa theo, ORM cascade + xóa tường minh)
  5 Báo giá VTBB      -> `tab_product_price_quote` có `source_type = 2` (Nhập Excel) và `source_id = lô`
  6 Sổ Misa (xlsx)    -> `tab_product_price_ledger.import_batch_id = lô` (nguồn 3); xóa xong TÍNH LẠI mốc sổ Misa

Dòng "đã sửa tay sau khi nhập" = `updated_at` (định mức, báo giá) / `synced_at` (sổ giá) muộn hơn giờ kết thúc lô quá `EDIT_GRACE`
(đồng hồ Python ghi giờ kết thúc, đồng hồ CSDL ghi giờ dòng, MySQL làm tròn giây nên cần một khoảng đệm). Mặc định xóa xong KHÔNG
đụng nhóm này; người dùng chọn `include_edited` thì xóa luôn.

Lô nhập cùng một mã nhiều lần: dòng mang id lô của LẦN GHI CUỐI (định mức, theo luật "lần ghi cuối thắng"), nên xóa lô cũ không đụng
dòng đã bị lô mới ghi đè. Sổ Misa chỉ ghi id lô lên dòng THÊM MỚI nên dòng đã có từ trước không bị xóa theo lô sau.
"""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import Delete, and_, delete, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.core.audit import record
from app.core.packaging_price_codes import PriceSourceType, QuoteSourceType
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus
from app.modules.product_price.misa_cutoff import get_misa_cutoff, set_misa_cutoff
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.model import ProductPriceQuote as Q

from .model import PackagingBom, PackagingBomPart
from .import_registry import PACKAGING_IMPORT_MODULES

EDIT_GRACE = timedelta(seconds=3)
AUDIT_ENTITY = "import_batch"


class BatchPurgeError(Exception):
    """Lô không xóa theo lô được (sai loại, chưa ghi thật, chưa xong) — controller đổi thành HTTP 400."""


@dataclass(frozen=True)
class _Kind:
    label: str                       # chữ trong thông báo: "định mức", "báo giá", "dòng sổ Misa"
    match: Callable[[int], ColumnElement]          # (id lô) -> điều kiện chọn dòng của lô
    edited_col: Callable[[], ColumnElement]        # () -> cột giờ sửa cuối để so với giờ kết thúc lô


_KINDS = {
    int(ImportModule.PACKAGING_BOM): _Kind("định mức bao bì", lambda bid: PackagingBom.import_batch_id == bid,
                                           lambda: PackagingBom.updated_at),
    int(ImportModule.PACKAGING_QUOTE): _Kind(
        "báo giá VTBB", lambda bid: and_(Q.source_type == int(QuoteSourceType.EXCEL_IMPORT), Q.source_id == bid),
        lambda: Q.updated_at),
    int(ImportModule.PACKAGING_MISA): _Kind(
        "dòng sổ Misa", lambda bid: and_(L.source_type == int(PriceSourceType.MISA), L.import_batch_id == bid),
        lambda: L.synced_at),
}
_MODELS = {int(ImportModule.PACKAGING_BOM): PackagingBom, int(ImportModule.PACKAGING_QUOTE): Q,
           int(ImportModule.PACKAGING_MISA): L}


def _check(batch: ImportBatch) -> _Kind:
    if batch.module not in PACKAGING_IMPORT_MODULES:
        raise BatchPurgeError("Chỉ xóa theo lô được với lô Định mức bao bì, Báo giá VTBB hoặc Sổ Misa")
    if batch.mode != ImportMode.APPLY:
        raise BatchPurgeError("Lô chạy thử không ghi dữ liệu nào để xóa")
    if batch.status != ImportStatus.DONE:
        raise BatchPurgeError("Chỉ xóa theo lô được với lô đã ghi thật và hoàn tất")
    return _KINDS[int(batch.module)]


def _edited_cond(kind: _Kind, batch: ImportBatch) -> ColumnElement | None:
    """Điều kiện "đã sửa sau khi nhập"; `None` khi lô chưa có giờ kết thúc (không phân biệt được -> coi như không ai sửa)."""
    if batch.finished_at is None:
        return None
    return kind.edited_col() > batch.finished_at + EDIT_GRACE


def _count(db: Session, model, *conds) -> int:
    return int(db.execute(select(func.count()).select_from(model).where(*conds)).scalar() or 0)


def preview(db: Session, batch: ImportBatch) -> dict:
    """Số dòng của lô: `total` (còn trên hệ thống), `edited` (đã sửa tay sau nhập, tách riêng), `untouched` = total - edited."""
    kind = _check(batch)
    model = _MODELS[int(batch.module)]
    where = kind.match(batch.id)
    total = _count(db, model, where)
    edited_cond = _edited_cond(kind, batch)
    edited = _count(db, model, where, edited_cond) if edited_cond is not None and total else 0
    return {"batch_id": batch.id, "module": int(batch.module), "target_label": kind.label,
            "total": total, "untouched": total - edited, "edited": edited,
            "recomputes_cutoff": int(batch.module) == int(ImportModule.PACKAGING_MISA)}


def _delete_rows(db: Session, batch: ImportBatch, where: ColumnElement) -> int:
    """Xóa đúng các dòng thỏa `where`; định mức thì xóa thành phần trước (không dựa vào khóa ngoại của CSDL — SQLite kiểm không bật)."""
    if int(batch.module) == int(ImportModule.PACKAGING_BOM):
        ids = select(PackagingBom.id).where(where)
        db.execute(delete(PackagingBomPart).where(PackagingBomPart.bom_id.in_(ids)))
        stmt: Delete = delete(PackagingBom).where(where)
    elif int(batch.module) == int(ImportModule.PACKAGING_QUOTE):
        stmt = delete(Q).where(where)
    else:
        stmt = delete(L).where(where)
    return int(db.execute(stmt.execution_options(synchronize_session=False)).rowcount or 0)


def _recompute_misa_cutoff(db: Session) -> str:
    """Mốc = ngày lớn nhất của mọi dòng Misa CÒN LẠI (cùng luật lúc nạp); hết dòng Misa thì bỏ mốc. Trả câu mô tả cho nhật ký."""
    old = get_misa_cutoff(db)
    new = db.execute(select(func.max(L.price_date)).where(L.source_type == int(PriceSourceType.MISA))).scalar()
    set_misa_cutoff(db, new)
    fmt = lambda d: d.strftime("%d/%m/%Y") if d else "(chưa có)"          # noqa: E731
    return f"Mốc sổ Misa: {fmt(old)} -> {fmt(new)}."


def purge(db: Session, batch: ImportBatch, user_id: int, *, include_edited: bool = False) -> dict:
    """Xóa dòng của lô (bỏ nhóm đã sửa tay trừ khi `include_edited`), ghi nhật ký thao tác, commit. Trả số dòng đã xóa / còn giữ."""
    kind = _check(batch)
    where = kind.match(batch.id)
    edited_cond = _edited_cond(kind, batch)
    kept_edited = 0
    if not include_edited and edited_cond is not None:
        kept_edited = _count(db, _MODELS[int(batch.module)], where, edited_cond)
        where = and_(where, ~edited_cond)
    try:
        deleted = _delete_rows(db, batch, where)
        cutoff_note = _recompute_misa_cutoff(db) if int(batch.module) == int(ImportModule.PACKAGING_MISA) else ""
        message = (f"Xóa theo lô nhập #{batch.id} ({kind.label}): xóa {deleted} dòng"
                   + (f", giữ {kept_edited} dòng đã sửa tay" if kept_edited else "")
                   + (" (gồm cả dòng đã sửa tay)" if include_edited else "") + ". " + cutoff_note).strip()
        record(db, user_id, AUDIT_ENTITY, batch.id, "delete", message, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"batch_id": batch.id, "deleted": deleted, "kept_edited": kept_edited, "message": message}
