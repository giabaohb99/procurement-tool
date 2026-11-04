"""Lô XUẤT TOÀN BỘ (hoặc theo bộ lọc đang chọn) của Tra cứu thị trường — chạy nền, chia nhiều tệp (bao-CR-718).

Nút xuất cũ (`service.export_lines_xlsx`) dựng cả tệp trong bộ nhớ ngay trong lời gọi và chặn ở 50.000 dòng — prod đã
328 nghìn dòng nên không xuất được toàn bộ. Ở đây:

  · `create_batch` — đếm (qua đệm), chụp `max_id`, báo NGAY tổng dòng + số tệp dự kiến; mỗi người một lô đang chạy
    (khóa UNIQUE `active_user_id`).
  · `run_next_part` — ghi MỘT tệp: đọc khối `EXPORT_CHUNK_ROWS` dòng theo `id` tăng từ `last_id` (keyset, không OFFSET),
    nghỉ giữa khối, ghi `openpyxl` chế độ `write_only` ra tệp tạm trên đĩa, lưu kho + một dòng `tab_export_log`. Trả
    True nếu còn tệp kế — task tự hẹn lần sau (`tasks.export_batch_part_task`), nên một task không chiếm worker quá
    một tệp và việc khác chen được giữa hai tệp.
  · `cleanup` — lô kẹt (worker chết) đánh hỏng + nhả khóa; lô quá hạn giữ thì xóa tệp trên kho.

Cùng cột với nút xuất cũ (`service.export_header` / `export_row`, có cột ID + Thao tác) — tệp nào cũng nạp lại được.
Thứ tự dòng trong tệp: `id` tăng dần (thứ tự nạp), không phải ngày giảm dần như màn hình — đọc theo khóa chính mới
đọc theo khối rẻ được.
"""
import logging
import math
import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from openpyxl import Workbook
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.export_xlsx import guard_formula_row
from app.core.storage import dated_key, delete_key, upload_fileobj
from app.modules.attachment.model import StoredFile
from app.modules.export_log.model import ExportLog
from app.modules.notification.model import Notification

from . import read_cache, service
from .constants import (ACTIVE_EXPORT_STATUSES, CUSTOMS_EXPORT_STATUS_LABELS, EXPORT_CHUNK_PAUSE_SECONDS,
                        EXPORT_CHUNK_ROWS, EXPORT_LOG_ENTITY, EXPORT_ROWS_PER_FILE, EXPORT_STALE_HOURS,
                        CustomsExportStatus)
from .model import CustomsExportBatch, CustomsLine

log = logging.getLogger("app.customs.line_export")

XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
BUSY_MESSAGE = "Bạn đang có một lô xuất chưa xong — chờ lô đó xong (hoặc dừng nó) rồi xuất lô mới"
#  Nhãn ô lọc cho câu tóm tắt — khớp nhãn trên màn tra cứu.
FILTER_LABELS = {
    "q": "Tên hàng", "ingredient": "Hoạt chất", "hs_code": "Mã HS", "formulation": "Dạng", "origin": "Xuất xứ",
    "unit": "Đơn vị", "importer_id": "Doanh nghiệp", "partner_id": "Đối tác", "batch_id": "Lô nạp",
    "currency": "Nguyên tệ", "incoterm": "Điều kiện giao", "price_min": "Giá từ", "price_max": "Giá đến",
    "qty_min": "Lượng từ", "qty_max": "Lượng đến", "rate_min": "Tỷ giá từ", "rate_max": "Tỷ giá đến",
    "date_from": "Từ ngày", "date_to": "Đến ngày", "product_kind": "Loại hàng",
}


def keep_days() -> int:
    """Số ngày giữ tệp của lô; 0 = giữ mãi."""
    return max(0, int(app_settings.get("customs_export_keep_days") or 0))


def describe_filters(f: dict) -> str:
    parts = []
    for key, label in FILTER_LABELS.items():
        v = f.get(key)
        if isinstance(v, (list, tuple)):
            v = ", ".join(str(x) for x in v if str(x).strip())
        if v not in (None, "") and str(v).strip():
            parts.append(f"{label}: {str(v).strip()}")
    return (" · ".join(parts) or "Toàn bộ dữ liệu")[:500]


def _clean_filters(f: dict) -> dict:
    """Bỏ ô trống — bộ lọc lưu trên lô gọn, và cùng bộ lọc thì cùng khóa đệm số đếm."""
    out = {}
    for k, v in f.items():
        if isinstance(v, (list, tuple)):
            v = [str(x) for x in v if str(x).strip()]
        if v not in (None, "", []):
            out[k] = v
    return out


def _filtered(db: Session, f: dict, batch: CustomsExportBatch):
    return service.apply_line_filters(db.query(CustomsLine), f or {}).filter(CustomsLine.id <= batch.max_id)


# ── Tạo lô ──────────────────────────────────────────────────────────────────
def create_batch(db: Session, f: dict, user_id: int) -> CustomsExportBatch:
    if db.query(CustomsExportBatch.id).filter(CustomsExportBatch.active_user_id == user_id).first():
        raise HTTPException(409, BUSY_MESSAGE)
    filters = _clean_filters(f)
    max_id = db.query(func.max(CustomsLine.id)).scalar() or 0
    probe = CustomsExportBatch(max_id=max_id)
    total = read_cache.cached(db, "count", f, lambda: _filtered(db, filters, probe)
                              .with_entities(func.count(CustomsLine.id)).scalar() or 0)
    if not total:
        raise HTTPException(400, "Bộ lọc này không có dòng nào để xuất")
    batch = CustomsExportBatch(
        status=int(CustomsExportStatus.QUEUED), active_user_id=user_id, filters=filters,
        filter_summary=describe_filters(filters), total_rows=int(total), rows_per_file=EXPORT_ROWS_PER_FILE,
        file_count=math.ceil(int(total) / EXPORT_ROWS_PER_FILE), max_id=max_id, files=[],
        created_by=user_id, updated_by=user_id)
    db.add(batch)
    try:
        db.commit()
    except IntegrityError:
        #  Hai lần bấm rơi vào hai tiến trình cùng lúc: UNIQUE `active_user_id` chặn lần sau.
        db.rollback()
        raise HTTPException(409, BUSY_MESSAGE) from None
    db.refresh(batch)
    return batch


# ── Ghi một tệp ─────────────────────────────────────────────────────────────
def _status_now(db: Session, batch_id: int) -> int:
    return db.query(CustomsExportBatch.status).filter(CustomsExportBatch.id == batch_id).scalar() or 0


def _store(db: Session, batch: CustomsExportBatch, part: int, path: str, rows: int) -> dict:
    filename = f"tra-cuu-thi-truong-lo-{batch.id}-tep-{part:02d}.xlsx"
    size = os.path.getsize(path)
    key = dated_key("export", filename, uuid.uuid4().hex[:12])
    with open(path, "rb") as fh:
        url = upload_fileobj(fh, key, XLSX_MEDIA)
    sf = StoredFile(filename=filename, file_key=key, url=url, content_type=XLSX_MEDIA, size=size,
                    created_by=batch.created_by, updated_by=batch.created_by)
    db.add(sf)
    db.flush()
    entry = ExportLog(entity=EXPORT_LOG_ENTITY, fmt="xlsx", row_count=rows, filename=filename, file_size=size,
                      file_id=sf.id, created_by=batch.created_by, updated_by=batch.created_by,
                      filter_summary=f"Lô xuất #{batch.id}, tệp {part}/{batch.file_count} · {batch.filter_summary}"[:2000])
    db.add(entry)
    db.flush()
    return {"part": part, "filename": filename, "rows": rows, "size": size, "file_id": sf.id,
            "export_log_id": entry.id}


def run_next_part(db: Session, batch_id: int, *, sleep=time.sleep) -> bool:
    """Ghi tệp kế của lô. True = còn tệp nữa (task hẹn lần sau); False = lô đã kết thúc / bị dừng."""
    batch = db.get(CustomsExportBatch, batch_id)
    if not batch or batch.status not in [int(s) for s in ACTIVE_EXPORT_STATUSES]:
        return False
    if batch.status == CustomsExportStatus.QUEUED:
        batch.status = int(CustomsExportStatus.RUNNING)
        batch.started_at = datetime.now()
        db.commit()
    part = batch.files_done + 1
    last_id, written = batch.last_id, 0
    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix=f"customs-export-{batch.id}-")
    os.close(fd)
    try:
        wb = Workbook(write_only=True)
        ws = wb.create_sheet("Tra cuu thi truong")
        ws.append(service.export_header())
        exhausted = False
        while written < batch.rows_per_file:
            take = min(EXPORT_CHUNK_ROWS, batch.rows_per_file - written)
            rows = (_filtered(db, batch.filters, batch).filter(CustomsLine.id > last_id)
                    .order_by(CustomsLine.id.asc()).limit(take).all())
            for d in service.serialize_lines(db, rows):
                ws.append(guard_formula_row(ws, service.export_row(d)))   # BM-033: dữ liệu từ tệp ngoài
            written += len(rows)
            if rows:
                last_id = rows[-1].id
            for r in rows:
                db.expunge(r)            # khối đã ghi ra tệp — đừng giữ trong phiên
            if len(rows) < take:
                exhausted = True
                break
            #  Kết thúc giao dịch đọc: MySQL REPEATABLE READ giữ ảnh chụp cũ, không commit thì không bao giờ thấy lệnh dừng.
            db.commit()
            if _status_now(db, batch.id) == CustomsExportStatus.CANCELLED:
                return False
            sleep(EXPORT_CHUNK_PAUSE_SECONDS)
        wb.save(path)
        db.refresh(batch)
        if batch.status == CustomsExportStatus.CANCELLED:
            return False
        if written:
            batch.files = [*(batch.files or []), _store(db, batch, part, path, written)]
            batch.files_done = part
            batch.rows_done += written
        batch.last_id = last_id
        if not exhausted:
            #  Đủ một tệp — xem còn dòng nào không, tránh hẹn một tệp rỗng.
            exhausted = _filtered(db, batch.filters, batch).filter(CustomsLine.id > last_id).first() is None
        if exhausted:
            _finish(db, batch, CustomsExportStatus.DONE)
        db.commit()
        return not exhausted
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _finish(db: Session, batch: CustomsExportBatch, status: CustomsExportStatus, error: str = "",
            now: datetime | None = None) -> None:
    batch.status = int(status)
    batch.active_user_id = None
    batch.finished_at = now or datetime.now()
    batch.error = error[:500]
    if status == CustomsExportStatus.DONE:
        batch.file_count = batch.files_done
    days = keep_days()
    batch.expires_at = batch.finished_at + timedelta(days=days) if days else None
    _notify(db, batch)


def _notify(db: Session, batch: CustomsExportBatch) -> None:
    if batch.status == CustomsExportStatus.DONE:
        title = f"Xuất tra cứu thị trường xong — {batch.files_done} tệp"
        body = f"{batch.rows_done:,} dòng".replace(",", ".") + f" · {batch.filter_summary}"
    elif batch.status == CustomsExportStatus.FAILED:
        title = "Xuất tra cứu thị trường bị lỗi"
        body = f"Đã xong {batch.files_done}/{batch.file_count} tệp. {batch.error}"
    else:
        return
    db.add(Notification(user_id=batch.created_by, title=title, body=body[:2000],
                        link=f"/procurement/customs-prices/exports/{batch.id}", created_by=batch.created_by))


def mark_failed(db: Session, batch_id: int, error: str) -> None:
    db.rollback()
    batch = db.get(CustomsExportBatch, batch_id)
    if batch and batch.status in [int(s) for s in ACTIVE_EXPORT_STATUSES]:
        _finish(db, batch, CustomsExportStatus.FAILED, error or "Lỗi không rõ khi ghi tệp")
        db.commit()


def cancel(db: Session, batch: CustomsExportBatch, user_id: int) -> CustomsExportBatch:
    if batch.status not in [int(s) for s in ACTIVE_EXPORT_STATUSES]:
        raise HTTPException(400, "Lô này đã kết thúc, không dừng được")
    _finish(db, batch, CustomsExportStatus.CANCELLED)
    batch.updated_by = user_id
    db.commit()
    return batch


# ── Đọc ─────────────────────────────────────────────────────────────────────
def batch_out(batch: CustomsExportBatch) -> dict:
    files = batch.files or []
    return {"id": batch.id, "status": batch.status,
            "status_label": CUSTOMS_EXPORT_STATUS_LABELS.get(CustomsExportStatus(batch.status), "")
            if batch.status in {int(s) for s in CustomsExportStatus} else "",
            "filter_summary": batch.filter_summary, "filters": batch.filters or {},
            "total_rows": batch.total_rows, "rows_per_file": batch.rows_per_file, "file_count": batch.file_count,
            "files_done": batch.files_done, "rows_done": batch.rows_done, "error": batch.error,
            "files": [{"part": x["part"], "filename": x["filename"], "rows": x["rows"], "size": x["size"],
                       "available": bool(x.get("file_id"))} for x in files],
            "created_at": batch.created_at, "created_by": batch.created_by, "started_at": batch.started_at,
            "finished_at": batch.finished_at, "expires_at": batch.expires_at,
            "active": batch.status in {int(s) for s in ACTIVE_EXPORT_STATUSES}}


def file_of(batch: CustomsExportBatch, part: int) -> dict:
    for x in batch.files or []:
        if x["part"] == part:
            return x
    raise HTTPException(404, "Không có tệp này trong lô")


# ── Dọn (việc chạy ngầm hằng đêm) ───────────────────────────────────────────
def cleanup(db: Session, *, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    stale = 0
    cutoff = now - timedelta(hours=EXPORT_STALE_HOURS)
    for batch in (db.query(CustomsExportBatch)
                  .filter(CustomsExportBatch.status.in_([int(s) for s in ACTIVE_EXPORT_STATUSES]),
                          func.coalesce(CustomsExportBatch.updated_at, CustomsExportBatch.created_at) < cutoff)):
        _finish(db, batch, CustomsExportStatus.FAILED, f"Không nhích quá {EXPORT_STALE_HOURS} giờ — dừng để nhả lượt xuất",
                now=now)
        stale += 1
    db.commit()
    expired = removed = 0
    ended = [int(s) for s in (CustomsExportStatus.DONE, CustomsExportStatus.FAILED, CustomsExportStatus.CANCELLED)]
    for batch in (db.query(CustomsExportBatch)
                  .filter(CustomsExportBatch.status.in_(ended), CustomsExportBatch.expires_at.isnot(None),
                          CustomsExportBatch.expires_at < now)):
        files = []
        for x in batch.files or []:
            sf = db.get(StoredFile, x.get("file_id") or 0)
            if sf:
                try:
                    delete_key(sf.file_key)
                except Exception:  # noqa: BLE001 — kho lỗi thì để đêm sau thử lại
                    log.warning("Không xóa được tệp %s của lô xuất #%s", sf.file_key, batch.id)
                    files.append(x)
                    continue
                db.delete(sf)
                removed += 1
            if x.get("export_log_id"):
                db.query(ExportLog).filter(ExportLog.id == x["export_log_id"]).update({"file_id": 0})
            files.append({**x, "file_id": 0})
        batch.files = files
        if all(not x.get("file_id") for x in files):
            batch.status = int(CustomsExportStatus.EXPIRED)
        expired += 1
        db.commit()
    return {"status": "success", "stale": stale, "expired": expired, "files_removed": removed}
