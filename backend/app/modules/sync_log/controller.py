"""Màn SỔ ĐỒNG BỘ — một API dùng chung cho mọi hệ ngoài.

Người xem: nhóm quản trị hệ thống (`sync_log.read`). Nút "Chạy lại" đòi
`sync_log.write` — bấm nó là gọi lại sang hệ ngoài, không phải chỉ đọc.

Cố ý KHÔNG có cửa xóa. Luật §3.2: không bao giờ xóa dòng lỗi; việc dọn dòng
*thành công* cũ hơn sáu tháng chạy nền qua `service.purge_success`, có ghi lại
đã dọn bao nhiêu dòng.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from .constants import (
    ACTION_LABELS,
    DIRECTION_LABELS,
    GRAIN_LABELS,
    RETRYABLE_STATUSES,
    STATUS_LABELS,
    SyncStatus,
)
from .model import SyncLog
from .registry import entity_options, job_options, source_options, warning_labels
from .schema import serialize_detail, serialize_entry
from .service import clone_for_retry

router = APIRouter(prefix="/api/sync-logs", tags=["sync-log"])

ENTITY = "sync_log"

#: Trần khoảng thời gian một lần hỏi, tính bằng ngày. Sổ này dày nhất hệ thống
#: (mỗi bản ghi một dòng), lọc hở là quét cả bảng.
DAYS_MAX = 365


def _apply_filters(query, *, source: str, grain: int, job: str, run_id: int,
                   entity: str, direction: int, status: int,
                   legacy_id: str, local_id: int, only_warning: bool,
                   days: int, keyword: str):
    if source:
        query = query.filter(SyncLog.source == source)
    if grain:
        query = query.filter(SyncLog.grain == grain)
    if job:
        query = query.filter(SyncLog.job == job)
    if run_id:
        #  Mở một lượt chạy ra xem nó đã ghi được những bản ghi nào.
        query = query.filter(SyncLog.run_id == run_id)
    if entity:
        query = query.filter(SyncLog.entity == entity)
    if direction:
        query = query.filter(SyncLog.direction == direction)
    if status:
        query = query.filter(SyncLog.status == status)
    if legacy_id:
        query = query.filter(SyncLog.legacy_id == legacy_id)
    if local_id:
        query = query.filter(SyncLog.local_id == local_id)
    if only_warning:
        #  Dòng THÀNH CÔNG vẫn có thể mang cờ — đây là đường lọc ra mọi bản ghi
        #  có dữ liệu bịa, đừng nhầm với lọc theo trạng thái lỗi.
        query = query.filter(SyncLog.warnings != "")
    if days:
        query = query.filter(SyncLog.created_at >= datetime.now() - timedelta(days=days))
    if keyword:
        #  Tìm trong câu trả lời NGUYÊN VĂN của bên kia — chỗ người đi tra sự cố
        #  gõ vào một mẩu câu lỗi họ nhớ được.
        query = query.filter(SyncLog.message.like(f"%{keyword}%"))
    return query


@router.get("/meta")
def sync_log_meta(user=Depends(require(ENTITY, "read"))):
    """Bộ chọn cho các ô lọc: nguồn, đối tượng, mã trạng thái, nhãn cờ.

    Giao diện đọc ở đây chứ không chép hằng số sang TypeScript — thêm một hệ
    nguồn mới ở `registry.py` là ô lọc tự có, không phải sửa frontend.
    """
    return success({
        "sources": source_options(),
        "entities": entity_options(),
        "jobs": job_options(),
        "grains": [{"code": k, "label": v} for k, v in GRAIN_LABELS.items()],
        "directions": [{"code": k, "label": v} for k, v in DIRECTION_LABELS.items()],
        "actions": [{"code": k, "label": v} for k, v in ACTION_LABELS.items()],
        "statuses": [{"code": k, "label": v} for k, v in STATUS_LABELS.items()],
        "warnings": [{"code": k, "label": v} for k, v in warning_labels().items()],
    })


@router.get("/stats")
def sync_log_stats(
    source: str = Query(""),
    days: int = Query(7, ge=1, le=DAYS_MAX),
    user=Depends(require(ENTITY, "read")),
    db: Session = Depends(get_db),
):
    """Thẻ đếm theo trạng thái trong N ngày gần đây.

    Gom bằng MỘT truy vấn `GROUP BY` chứ không đếm năm lần — sổ này là bảng dày
    nhất hệ thống.
    """
    from sqlalchemy import func

    profile = get_perm_profile(db, user)
    query = db.query(SyncLog.status, func.count(SyncLog.id))
    if source:
        query = query.filter(SyncLog.source == source)
    query = query.filter(SyncLog.created_at >= datetime.now() - timedelta(days=days))
    query = apply_scope(query, SyncLog, ENTITY, user, profile)
    counts = {int(code): int(total) for code, total in query.group_by(SyncLog.status).all()}
    return success({
        "days": days,
        "source": source,
        "total": sum(counts.values()),
        "by_status": [
            {"status": int(s), "label": STATUS_LABELS[s], "count": counts.get(int(s), 0)}
            for s in SyncStatus
        ],
    })


@router.get("")
def list_sync_logs(
    source: str = Query(""),
    grain: int = Query(0, ge=0, le=2),
    job: str = Query(""),
    run_id: int = Query(0, ge=0),
    entity: str = Query(""),
    direction: int = Query(0, ge=0, le=2),
    status: int = Query(0, ge=0, le=5),
    legacy_id: str = Query(""),
    local_id: int = Query(0, ge=0),
    only_warning: bool = Query(False),
    days: int = Query(30, ge=0, le=DAYS_MAX),
    q: str = Query("", max_length=200),
    user=Depends(require(ENTITY, "read")),
    db: Session = Depends(get_db),
    pg: dict = Depends(pagination),
):
    """Danh sách dòng sổ, mới nhất trước. Không trả `payload` (xem `schema.py`)."""
    profile = get_perm_profile(db, user)
    query = _apply_filters(
        db.query(SyncLog), source=source, grain=grain, job=job.strip(),
        run_id=run_id, entity=entity, direction=direction,
        status=status, legacy_id=legacy_id.strip(), local_id=local_id,
        only_warning=only_warning, days=days, keyword=q.strip())
    query = apply_scope(query, SyncLog, ENTITY, user, profile)
    total = query.count()
    rows = (query.order_by(SyncLog.id.desc())
            .offset(pg["offset"]).limit(pg["limit"]).all())
    return success({"items": [serialize_entry(r) for r in rows], "total": total,
                    "page": pg["page"], "page_size": pg["page_size"]})


@router.get("/{log_id}")
def get_sync_log(log_id: int, user=Depends(require(ENTITY, "read")),
                 db: Session = Depends(get_db)):
    """Một dòng, kèm nguyên cục dữ liệu bên kia gửi sang và câu lỗi nguyên văn."""
    profile = get_perm_profile(db, user)
    row = get_scoped(db, SyncLog, ENTITY, log_id, user, profile, "read")
    if not row:
        raise HTTPException(404, "Không tìm thấy dòng sổ đồng bộ")
    return success(serialize_detail(row))


@router.post("/{log_id}/retry")
def retry_sync_log(log_id: int, user=Depends(require(ENTITY, "write")),
                   db: Session = Depends(get_db)):
    """Chạy lại một dòng hỏng — sinh DÒNG MỚI, không sửa dòng cũ.

    Dòng mới ở trạng thái *chờ*; người nhặt việc là tiến trình đồng bộ của hệ
    nguồn tương ứng, không phải endpoint này. Tách vậy để cửa HTTP không ngồi
    chờ một hệ ngoài đang chết.
    """
    profile = get_perm_profile(db, user)
    row = get_scoped(db, SyncLog, ENTITY, log_id, user, profile, "write")
    if not row:
        raise HTTPException(404, "Không tìm thấy dòng sổ đồng bộ")
    if row.status not in [int(s) for s in RETRYABLE_STATUSES]:
        raise HTTPException(400, "Chỉ chạy lại được dòng đang lỗi hoặc đang chờ")
    fresh = clone_for_retry(db, row, user.id)
    record(db, user.id, ENTITY, fresh.id, "retry",
           f"Xếp chạy lại dòng sổ #{row.id} ({row.source}/{row.entity} "
           f"{row.legacy_id or '-'}) thành dòng #{fresh.id}")
    return success(serialize_entry(fresh), "Đã xếp hàng chạy lại")
