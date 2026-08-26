"""Chạy xuất dữ liệu tập trung + ghi nhật ký (Đ-13b)."""
import csv
import io
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.core.auth import get_perm_profile, user_has_permission
from app.core.export_xlsx import xlsx_response
from app.core.scoping import apply_scope
from app.core.storage import dated_key, upload_fileobj
from app.modules.attachment.model import StoredFile

from .model import ExportLog
from .registry import EXPORT_ADAPTERS

VN_OFFSET = timedelta(hours=7)

#  Màn Xuất tập trung = DUMP CẢ BẢNG, nên trần cao hơn export tương tác (5.000).
#  6.803 dòng sản phẩm vẫn dựng file tức thì; đặt trần an toàn để bảng cực lớn
#  không làm treo request.
EXPORT_MAX_ROWS = 100_000


def _store_file(db: Session, content: bytes, filename: str, media: str, user_id: int) -> int:
    """Lưu file đã xuất lên storage (dùng chung StoredFile) để tải lại ở trang chi tiết."""
    key = dated_key("export", filename, uuid.uuid4().hex[:12])
    url = upload_fileobj(io.BytesIO(content), key, media)
    sf = StoredFile(filename=filename, file_key=key, url=url, content_type=media,
                    size=len(content), created_by=user_id, updated_by=user_id)
    db.add(sf)
    db.flush()
    return sf.id


def available_entities(db: Session, user) -> list[dict]:
    """Các bảng người dùng ĐƯỢC xuất (có quyền `export` trên entity đó)."""
    return [
        {"entity": e, "label": a["label"], "module": a.get("module", "")}
        for e, a in EXPORT_ADAPTERS.items()
        if user_has_permission(db, user, e, "export")
    ]


def can_view_any(db: Session, user) -> bool:
    """Xem nhật ký Xuất: cần có quyền `export` trên ÍT NHẤT một bảng."""
    return any(user_has_permission(db, user, e, "export") for e in EXPORT_ADAPTERS)


def _csv_cell(col, value) -> str:
    if col.kind == "bool":
        return "Có" if value else "Không"   # rõ True/False -> import lại đọc đúng
    return "" if value is None else str(value)


def _code_map(db: Session, ref: str, self_model) -> dict:
    """Bản đồ id -> code cho một bảng tham chiếu (để xuất MÃ thay vì id/tên)."""
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    model = {"company": Company, "department": Department, "employee": Employee}.get(ref)
    if ref == "self":
        model = self_model
    if model is None:
        return {}
    return {row[0]: row[1] for row in db.query(model.id, model.code).all()}


def _build_csv(cols, rows) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([c.label for c in cols])
    for r in rows:
        w.writerow([_csv_cell(c, r.get(c.key)) for c in cols])
    # utf-8-sig: BOM để Excel mở đúng tiếng Việt (giống export CSV cũ).
    return buf.getvalue().encode("utf-8-sig")


def run_export(db: Session, user, entity: str, fmt: str) -> tuple[bytes, str, str, int]:
    """Xuất TOÀN BẢNG (theo phạm vi dữ liệu) ra CSV/XLSX, ghi log, trả (nội dung, tên file, media, số dòng)."""
    adapter = EXPORT_ADAPTERS[entity]
    model = adapter["model"]

    q = db.query(model)
    q = apply_scope(q, model, adapter["scope"], user, get_perm_profile(db, user))
    q = q.order_by(model.id.desc())
    items = q.all()
    if len(items) > EXPORT_MAX_ROWS:
        raise HTTPException(400, f"Bảng có {len(items):,} dòng, vượt mức {EXPORT_MAX_ROWS:,} dòng "
                                 f"cho một lần xuất toàn bảng.")

    cols = adapter["columns"]
    # Cột tham chiếu -> đổi id sang MÃ (xuất một lần bản đồ id->code cho mỗi bảng).
    ref_maps = {c.ref: _code_map(db, c.ref, model) for c in cols if getattr(c, "ref", None)}
    rows = [
        {
            c.key: (ref_maps[c.ref].get(getattr(it, c.key, 0) or 0, "")
                    if getattr(c, "ref", None) else getattr(it, c.key, ""))
            for c in cols
        }
        for it in items
    ]
    stamp = (datetime.utcnow() + VN_OFFSET).strftime("%d%m%Y")

    if fmt == "xlsx":
        content = xlsx_response(f"xuat-{entity}", cols, rows, adapter["label"]).body
        filename = f"xuat-{entity}-{stamp}.xlsx"
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content = _build_csv(cols, rows)
        filename = f"xuat-{entity}-{stamp}.csv"
        media = "text/csv; charset=utf-8"

    file_id = _store_file(db, content, filename, media, user.id)
    db.add(ExportLog(entity=entity, fmt=fmt, row_count=len(items), filename=filename,
                     file_size=len(content), file_id=file_id, filter_summary="",
                     created_by=user.id, updated_by=user.id))
    db.commit()
    return content, filename, media, len(items)


def get_export(db: Session, bid: int) -> ExportLog | None:
    return db.get(ExportLog, bid)


# ---------- nhật ký ----------
def list_exports(db: Session, entity: str | None, fmt: str | None,
                 date_from: str | None, date_to: str | None,
                 created_by_name: str | None, pg: dict):
    q = db.query(ExportLog)
    if entity:
        q = q.filter(ExportLog.entity == entity)
    if fmt:
        q = q.filter(ExportLog.fmt == fmt)
    if date_from:
        q = q.filter(ExportLog.created_at >= date_from + " 00:00:00")
    if date_to:
        q = q.filter(ExportLog.created_at <= date_to + " 23:59:59")
    if created_by_name:
        uids = _resolve_creator_ids(db, created_by_name)
        q = q.filter(ExportLog.created_by.in_(uids)) if uids else q.filter(ExportLog.id < 0)
    total = q.count()
    items = q.order_by(ExportLog.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def _resolve_creator_ids(db: Session, name: str) -> list[int]:
    from app.core.audit import resolve_actor
    uid_rows = db.query(ExportLog.created_by).distinct().all()
    return [uid for (uid,) in uid_rows if resolve_actor(db, uid) == name]


def distinct_creators(db: Session) -> list[str]:
    from app.core.audit import resolve_actor
    uid_rows = db.query(ExportLog.created_by).distinct().all()
    return sorted({resolve_actor(db, uid) for (uid,) in uid_rows})
