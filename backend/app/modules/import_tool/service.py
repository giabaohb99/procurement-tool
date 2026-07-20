"""Hạ tầng import: lưu file, tạo/đọc batch, ghi log, đếm kết quả."""
import json
import uuid

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.storage import upload_fileobj
from app.modules.attachment.model import StoredFile

from .model import (ImportBatch, ImportChange, ImportLog, ImportMode,
                    ImportModule, ImportStatus, LogLevel)

# tăng đếm theo level của log
_LEVEL_COUNTER = {
    LogLevel.WARNING: "warning_count",
    LogLevel.REVIEW: "review_count",
    LogLevel.ERROR: "error_count",
}


def save_upload(db: Session, upload_file, user_id: int) -> StoredFile:
    """Lưu file .xlsx lên storage (dùng chung StoredFile) — worker đọc lại qua file_key."""
    f = upload_file
    f.file.seek(0, 2); size = f.file.tell(); f.file.seek(0)
    key = f"import/{uuid.uuid4().hex}_{f.filename}"
    url = upload_fileobj(f.file, key, f.content_type or "")
    sf = StoredFile(filename=f.filename or "import.xlsx", file_key=key, url=url,
                    content_type=f.content_type or "", size=size,
                    created_by=user_id, updated_by=user_id)
    db.add(sf); db.commit(); db.refresh(sf)
    return sf


def create_batch(db: Session, module: int, mode: int, sf: StoredFile, user_id: int) -> ImportBatch:
    b = ImportBatch(module=module, mode=mode, filename=sf.filename, file_id=sf.id,
                    file_size=sf.size or 0, sheet_info="", error_summary="",
                    status=ImportStatus.QUEUED, created_by=user_id, updated_by=user_id)
    db.add(b); db.commit(); db.refresh(b)
    return b


def add_log(db: Session, batch: ImportBatch, sheet: str, row_no: int, level: int,
            category: str, message: str, ref_key: str = "", target_code: str = "", raw: str = "") -> None:
    """Ghi 1 dòng log + tăng đếm theo level (INFO không tính vào cảnh báo/lỗi)."""
    db.add(ImportLog(batch_id=batch.id, sheet=sheet, row_no=row_no, level=int(level),
                     category=category, message=message[:60000], ref_key=ref_key[:120],
                     target_code=target_code[:50], raw=raw[:60000], created_by=batch.created_by))
    col = _LEVEL_COUNTER.get(level)
    if col:
        setattr(batch, col, (getattr(batch, col) or 0) + 1)


def list_batches(db: Session, module: int | None, status: int | None, mode: int | None,
                 date_from: str | None, date_to: str | None,
                 created_by_name: str | None, filename: str | None, pg: dict):
    q = db.query(ImportBatch)
    if module:
        q = q.filter(ImportBatch.module == module)
    if status is not None:
        q = q.filter(ImportBatch.status == status)
    if mode is not None:
        q = q.filter(ImportBatch.mode == mode)
    if date_from:
        q = q.filter(ImportBatch.created_at >= date_from + " 00:00:00")
    if date_to:
        q = q.filter(ImportBatch.created_at <= date_to + " 23:59:59")
    if filename:
        q = q.filter(ImportBatch.filename.like(f"%{filename}%"))
    if created_by_name:
        # Resolve name → user IDs
        uids = _resolve_creator_ids(db, created_by_name)
        if uids:
            q = q.filter(ImportBatch.created_by.in_(uids))
        else:
            q = q.filter(ImportBatch.id < 0)  # no match
    total = q.count()
    items = q.order_by(ImportBatch.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def _resolve_creator_ids(db: Session, name: str) -> list[int]:
    """Find user IDs whose resolved name matches the given name."""
    from app.core.audit import resolve_actor
    uid_rows = db.query(ImportBatch.created_by).distinct().all()
    return [uid for (uid,) in uid_rows if resolve_actor(db, uid) == name]


def distinct_creators(db: Session) -> list[str]:
    """Return sorted list of distinct creator names across all batches."""
    from app.core.audit import resolve_actor
    uid_rows = db.query(ImportBatch.created_by).distinct().all()
    names = sorted({resolve_actor(db, uid) for (uid,) in uid_rows})
    return names


def get_batch(db: Session, bid: int) -> ImportBatch | None:
    return db.get(ImportBatch, bid)


def get_logs(db: Session, batch_id: int, level: int | None, pg: dict):
    q = db.query(ImportLog).filter(ImportLog.batch_id == batch_id)
    if level is not None:
        q = q.filter(ImportLog.level == level)
    total = q.count()
    items = (q.order_by(ImportLog.level.desc(), ImportLog.id.asc())
             .offset(pg["offset"]).limit(pg["limit"]).all())
    return total, items


def _apply_cols(obj, data: dict) -> None:
    keys = {c.key for c in sa_inspect(obj.__class__).columns}
    for k, v in data.items():
        if k in keys:
            setattr(obj, k, v)


def revert_batch(db: Session, batch: ImportBatch, user_id: int) -> dict:
    """Hoàn tác 1 batch đã Apply: bản ghi mới -> xoá; bản ghi cũ -> khôi phục snapshot."""
    if batch.mode != ImportMode.APPLY:
        return {"ok": False, "message": "Batch chạy thử — không ghi gì để hoàn tác"}
    if batch.status != ImportStatus.DONE:
        return {"ok": False, "message": "Chỉ hoàn tác batch đã hoàn thành (DONE)"}
    changes = db.query(ImportChange).filter(ImportChange.batch_id == batch.id).all()
    if not changes:
        return {"ok": False, "message": "Không có bản ghi snapshot để hoàn tác"}

    if batch.module == ImportModule.PURCHASE_ORDER:
        deleted, restored = _revert_po(db, changes, user_id)
        what = "đơn"
    else:
        deleted, restored = _revert_survey(db, changes, user_id)
        what = "phiếu"

    batch.status = ImportStatus.REVERTED
    batch.updated_by = user_id
    db.commit()
    return {"ok": True, "deleted": deleted, "restored": restored,
            "message": f"Đã hoàn tác: xoá {deleted} {what} mới, khôi phục {restored} {what} cũ"}


def _revert_survey(db: Session, changes, user_id: int):
    from app.modules.survey.model import (Survey, SurveyProductLine,
                                           SurveySupplierLine)
    deleted = restored = 0
    for ch in changes:
        s = db.get(Survey, ch.survey_id)
        if ch.was_new:
            if s:
                db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == s.id).delete()
                db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == s.id).delete()
                db.delete(s); deleted += 1
            continue
        if not s or not ch.snapshot:
            continue
        snap = json.loads(ch.snapshot)
        _apply_cols(s, snap.get("survey", {}))
        db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == s.id).delete()
        db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == s.id).delete()
        for row in snap.get("sup", []):
            ln = SurveySupplierLine(); _apply_cols(ln, row); db.add(ln)
        for row in snap.get("prod", []):
            ln = SurveyProductLine(); _apply_cols(ln, row); db.add(ln)
        restored += 1
    return deleted, restored


def _delete_po_payments(db, po):
    """Xoá các YCTT (do import tạo) tham chiếu công nợ của đơn này — trước khi xoá/khôi phục đơn."""
    from app.modules.payable.model import Payable
    from app.modules.payment_request.model import (PaymentRequest,
                                                    PaymentRequestLine)
    pay_ids = [p.id for p in db.query(Payable).filter(Payable.po_id == po.id).all()]
    if not pay_ids:
        return
    req_ids = {ln.request_id for ln in
               db.query(PaymentRequestLine).filter(PaymentRequestLine.payable_id.in_(pay_ids)).all()}
    for rid in req_ids:
        db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).delete()
        req = db.get(PaymentRequest, rid)
        if req:
            db.delete(req)
    db.flush()


def _revert_po(db: Session, changes, user_id: int):
    from app.modules.purchase_order import service as po_service
    from app.modules.purchase_order.model import (PODelivery, POItem,
                                                   PurchaseOrder)
    deleted = restored = 0
    for ch in changes:
        po = db.get(PurchaseOrder, ch.survey_id)   # survey_id dùng chung = po_id
        if not po:
            continue
        _delete_po_payments(db, po)
        if ch.was_new:
            po_service.delete_po(db, po.id, user_id)   # cascade GR/tồn/công nợ + dòng + lần giao
            deleted += 1
            continue
        # đơn cũ: xoá dòng+lần giao hiện tại (dọn side-effect) rồi dựng lại từ snapshot + recompute
        if not ch.snapshot:
            continue
        for it in po_service.items_of(db, po.id):
            for d in po_service.deliveries_of(db, it.id):
                po_service._cleanup_delivery(db, d.id)
                db.delete(d)
            db.delete(it)
        db.flush()
        snap = json.loads(ch.snapshot)
        _apply_cols(po, snap.get("po", {}))
        for irow in snap.get("items", []):
            delivs = irow.pop("_deliveries", [])
            it = POItem(); _apply_cols(it, irow); it.po_id = po.id
            db.add(it); db.flush()
            for drow in delivs:
                dv = PODelivery(); _apply_cols(dv, drow); dv.po_item_id = it.id; dv.po_id = po.id
                db.add(dv)
        db.flush()
        po_service.recompute_effects(db, po, user_id)
        restored += 1
    return deleted, restored
