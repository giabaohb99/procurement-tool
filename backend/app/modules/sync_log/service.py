"""Nghiệp vụ của sổ đồng bộ — viết chung cho mọi hệ nguồn.

Nhịp dùng điển hình của một lượt NHẬN VỀ:

    entry = open_entry(db, source="datxe", entity="seal_request", ...)  # ghi CHỜ
    if entry is None:                       # event_id đã nhận rồi -> thôi
        return
    mark_running(db, entry)
    with suppress_outbound():               # chống dội ngược (§7)
        ... tạo/sửa bản ghi ERP ...
    finish_ok(db, entry, "Đã tạo phiếu", local_id=obj.id)

Ba luật ở `model.py` được cài thẳng vào đây: `open_entry` **commit ngay** dòng
*chờ* trước khi ai kịp làm gì; mọi hàm `finish_*` chỉ đụng vào ĐÚNG dòng của
lượt đó; và `purge_success` là nơi duy nhất xóa, chỉ xóa dòng *thành công*.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .constants import (
    PURGE_AFTER_MONTHS,
    WARNING_SEPARATOR,
    WARNINGS_MAX_LENGTH,
    SyncAction,
    SyncDirection,
    SyncGrain,
    SyncStatus,
)
from .model import SyncLog
from .registry import require_source

LOGGER = logging.getLogger(__name__)

#: Giờ Việt Nam. Cột `last_tried_at` là CHUỖI nên phải tự chốt múi giờ, không
#: thì đọc sổ ra hai đồng hồ lệch nhau 7 tiếng.
VN_TZ = timezone(timedelta(hours=7))

#  --- Chống dội ngược (§7) -------------------------------------------------
#  Đang xử lý một tín hiệu NHẬN VỀ thì mọi thay đổi sinh ra trong lúc đó KHÔNG
#  được bắn ngược lại hệ nguồn, nếu không hai bên đá qua đá lại vô tận. Cùng
#  khuôn với chốt của `tab_change_log`.
_sync_in_progress: ContextVar[bool] = ContextVar("sync_in_progress", default=False)


def is_sync_in_progress() -> bool:
    return _sync_in_progress.get()


@contextmanager
def suppress_outbound():
    """Bọc đoạn ghi dữ liệu do hệ ngoài đẩy sang, để không bắn tín hiệu ngược."""
    token = _sync_in_progress.set(True)
    try:
        yield
    finally:
        _sync_in_progress.reset(token)


#  --- Băm và mã sự kiện ----------------------------------------------------

def compute_hash(payload) -> str:
    """Băm PHẦN NGHIỆP VỤ để biết "có thật sự đổi gì không".

    `sort_keys=True` là bắt buộc: JSON cùng nội dung nhưng khác thứ tự khóa phải
    ra cùng một mã băm, không thì lần nào cũng tưởng là có thay đổi.
    """
    if isinstance(payload, (dict, list)):
        text = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    else:
        text = str(payload or "")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_event_id(source: str, entity: str, legacy_id: str, action: int) -> str:
    """Mã sự kiện do PHÍA ERP tự sinh — dùng khi chiều GỬI ĐI, hoặc khi hệ ngoài
    không gửi mã. Có phần ngẫu nhiên vì một bản ghi sinh nhiều sự kiện."""
    return f"{source}.{entity}.{legacy_id}.{int(action)}.{uuid.uuid4().hex[:12]}"[:64]


def now_text() -> str:
    """Chuỗi ISO giờ Việt Nam, vừa đúng trần String(20)."""
    return datetime.now(VN_TZ).strftime("%Y-%m-%dT%H:%M:%S")


#  --- Cờ cảnh báo ----------------------------------------------------------

def join_warnings(flags) -> str:
    """Gộp cờ: khử trùng, giữ thứ tự, cắt cho vừa String(255)."""
    seen: list[str] = []
    for flag in flags or []:
        flag = (flag or "").strip()
        if flag and flag not in seen:
            seen.append(flag)
    text = WARNING_SEPARATOR.join(seen)
    if len(text) <= WARNINGS_MAX_LENGTH:
        return text
    #  Cắt ở ranh giới cờ, đừng cắt giữa một cờ -> đọc ra cờ không tồn tại.
    trimmed: list[str] = []
    for flag in seen:
        candidate = WARNING_SEPARATOR.join(trimmed + [flag])
        if len(candidate) > WARNINGS_MAX_LENGTH:
            break
        trimmed.append(flag)
    return WARNING_SEPARATOR.join(trimmed)


def add_warning(entry: SyncLog, *flags: str) -> None:
    """Gắn thêm cờ vào một dòng đang mở. Không ghi DB, để người gọi tự chốt."""
    entry.warnings = join_warnings(entry.warning_list + list(flags))


#  --- Tra cứu --------------------------------------------------------------

def find_by_event(db: Session, event_id: str) -> SyncLog | None:
    if not event_id:
        return None
    return db.execute(
        select(SyncLog).where(SyncLog.event_id == event_id)
    ).scalar_one_or_none()


def last_entry(db: Session, source: str, entity: str, legacy_id: str) -> SyncLog | None:
    """Dòng sổ gần nhất của một bản ghi — để so `content_hash`."""
    return db.execute(
        select(SyncLog)
        .where(
            SyncLog.source == source,
            SyncLog.entity == entity,
            SyncLog.legacy_id == legacy_id,
        )
        .order_by(SyncLog.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def is_unchanged(db: Session, source: str, entity: str, legacy_id: str,
                 content_hash: str) -> bool:
    """Lần trước đã xử lý THÀNH CÔNG đúng nội dung này thì lần này bỏ qua.

    Chỉ tính dòng thành công: lần trước lỗi mà nội dung y hệt thì vẫn phải làm
    lại, không thì một lỗi tạm thời khóa luôn bản ghi đó.
    """
    if not content_hash:
        return False
    previous = db.execute(
        select(SyncLog.content_hash)
        .where(
            SyncLog.source == source,
            SyncLog.entity == entity,
            SyncLog.legacy_id == legacy_id,
            SyncLog.status == int(SyncStatus.SUCCESS),
        )
        .order_by(SyncLog.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return bool(previous) and previous == content_hash


#  --- Vòng đời một dòng sổ -------------------------------------------------

def open_entry(
    db: Session,
    *,
    source: str,
    entity: str,
    direction: int = int(SyncDirection.INBOUND),
    action: int = int(SyncAction.CREATE),
    legacy_id: str = "",
    local_id: int = 0,
    event_id: str = "",
    payload=None,
    content_hash: str = "",
    warnings=None,
    message: str = "",
    run_id: int = 0,
    user_id: int = 0,
) -> SyncLog | None:
    """Ghi dòng *chờ* và CHỐT XUỐNG DB trước khi làm bất cứ việc gì.

    Trả `None` khi `event_id` đã có trong sổ — tín hiệu lặp, người gọi nên dừng.
    Ràng buộc UNIQUE là chốt thật; kiểm trước chỉ để đỡ một lần va.
    """
    src = require_source(source)
    if not event_id:
        event_id = make_event_id(src.code, entity, legacy_id, action)
    if find_by_event(db, event_id) is not None:
        LOGGER.info("Bỏ qua sự kiện lặp %s", event_id)
        return None

    if payload is not None and not isinstance(payload, str):
        payload = json.dumps(payload, ensure_ascii=False, default=str)

    entry = SyncLog(
        source=src.code,
        grain=int(SyncGrain.RECORD),
        run_id=run_id or 0,
        entity=entity,
        direction=int(direction),
        action=int(action),
        legacy_id=(legacy_id or "")[:64],
        local_id=local_id or 0,
        status=int(SyncStatus.PENDING),
        message=message or "",
        payload=payload or "",
        content_hash=content_hash or "",
        event_id=event_id[:64],
        attempt_count=0,
        last_tried_at="",
        warnings=join_warnings(warnings),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError:
        #  Hai lượt gọi song song cùng một `event_id` — bên kia đã ghi trước.
        db.rollback()
        LOGGER.info("Sự kiện %s đã được ghi bởi lượt khác", event_id)
        return None
    db.refresh(entry)
    return entry


def mark_running(db: Session, entry: SyncLog) -> SyncLog:
    """Bắt đầu thử một lượt: tăng số lần thử và đóng mốc thời gian."""
    entry.status = int(SyncStatus.RUNNING)
    entry.attempt_count = (entry.attempt_count or 0) + 1
    entry.last_tried_at = now_text()
    db.commit()
    db.refresh(entry)
    return entry


#  --- Dòng LƯỢT CHẠY (grain = RUN) -----------------------------------------

def open_run(db: Session, source: str, job: str, *, entity: str = "",
             direction: int = int(SyncDirection.INBOUND),
             user_id: int = 0) -> SyncLog:
    """Mở một lượt chạy ở trạng thái *đang chạy* và chốt xuống DB ngay.

    `created_by` = ai bấm chạy tay; `0` = lịch chạy nền. Trả về dòng cha để các
    dòng bản ghi trong lượt gắn `run_id` vào.
    """
    src = require_source(source)
    if job and src.jobs and job not in src.jobs:
        raise ValueError(f"Nguồn '{src.code}' chưa khai công việc '{job}' trong registry")
    run = SyncLog(
        source=src.code,
        grain=int(SyncGrain.RUN),
        job=job,
        entity=entity,
        direction=int(direction),
        action=int(SyncAction.UPDATE),
        status=int(SyncStatus.RUNNING),
        event_id=make_event_id(src.code, job or "run", "", SyncAction.UPDATE),
        attempt_count=1,
        last_tried_at=now_text(),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_run(db: Session, run: SyncLog, status: SyncStatus, *, message: str = "",
               fetched: int = 0, written: int = 0, skipped: int = 0,
               cursor_from: str = "", cursor_to: str = "", detail=None) -> SyncLog:
    """Đóng một lượt chạy: đếm được bao nhiêu, con trỏ tới đâu, hỏng vì gì."""
    run.status = int(status)
    run.message = message or ""
    run.fetched = int(fetched or 0)
    run.written = int(written or 0)
    run.skipped = int(skipped or 0)
    run.cursor_from = (cursor_from or "")[:30]
    run.cursor_to = (cursor_to or "")[:30]
    if detail is not None:
        run.payload = (detail if isinstance(detail, str)
                       else json.dumps(detail, ensure_ascii=False, default=str))
    run.finished_at = now_text()
    db.commit()
    db.refresh(run)
    return run


def last_successful_run(db: Session, source: str, job: str) -> SyncLog | None:
    """Lượt chạy THÀNH CÔNG gần nhất của một công việc — chỗ đọc con trỏ lần trước.

    Con trỏ chỉ tiến khi thành công: hệ ngoài sập thì chu kỳ sau tự kéo bù.
    """
    return db.execute(
        select(SyncLog)
        .where(
            SyncLog.source == source,
            SyncLog.grain == int(SyncGrain.RUN),
            SyncLog.job == job,
            SyncLog.status == int(SyncStatus.SUCCESS),
            SyncLog.cursor_to != "",
        )
        .order_by(SyncLog.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def recent_runs(db: Session, source: str, job: str, limit: int,
                statuses=None) -> list[SyncLog]:
    """N lượt chạy gần nhất của một công việc — dùng để đếm chuỗi lỗi liên tiếp."""
    query = select(SyncLog).where(
        SyncLog.source == source,
        SyncLog.grain == int(SyncGrain.RUN),
        SyncLog.job == job,
    )
    if statuses:
        query = query.where(SyncLog.status.in_([int(s) for s in statuses]))
    return list(db.execute(query.order_by(SyncLog.id.desc()).limit(limit)).scalars())


#: Dòng lỗi phải cũ hơn ngần này giờ mới đáng gọi người. Phần lớn sự cố đồng bộ
#: tự khỏi ở vòng `retry_pending` kế tiếp (10 phút một lần); báo ngay thì chuông
#: kêu cả ngày vì những thứ đã lành trước khi ai kịp mở màn hình.
STALE_FAILURE_HOURS = 24

#: Trần số dòng một lượt quét. Sổ lỗi dài hơn ngần này thì vấn đề không còn nằm
#: ở từng dòng nữa — chuông chỉ cần nói "nhiều quá, vào mà xem".
STALE_FAILURE_LIMIT = 500

#: Kết cục được coi là ĐÃ VÁ. `SKIPPED` tính là vá: nó nghĩa là lần sau nhìn lại
#: thì bên ERP đã có hàng đúng rồi, không còn việc gì phải làm.
HEALED_STATUSES = (SyncStatus.SUCCESS, SyncStatus.SKIPPED)


def find_stale_failures(db: Session, *, hours: int = STALE_FAILURE_HOURS,
                        limit: int = STALE_FAILURE_LIMIT,
                        source: str = "") -> list[SyncLog]:
    """Dòng LỖI cũ hơn `hours` giờ mà tới giờ vẫn chưa ai vá được.

    "Vá được" nghĩa là SAU dòng lỗi đó, sổ có một dòng khác cùng đối tượng kết
    thúc êm. Phải xét vòng vèo như vậy vì `clone_for_retry` cố ý KHÔNG sửa dòng
    cũ (luật §3.2): bấm chạy lại mười lần thì dòng lỗi đầu tiên vẫn mang trạng
    thái *lỗi* vĩnh viễn. Đếm thẳng theo trạng thái là sáng nào chuông cũng réo
    lại đúng mấy dòng người ta đã xử xong từ tuần trước, và chuông nào kêu sai
    vài lần thì người ta thôi đọc nó.

    Dòng BẢN GHI soi theo (nguồn, đối tượng, mã bên cũ); dòng LƯỢT CHẠY soi theo
    (nguồn, công việc) — một lượt kéo thành công sau đó đã kéo bù phần lỡ, vì
    con trỏ chỉ tiến khi thành công.

    Bản ghi không có mã bên cũ thì không soi được, và cố ý coi như CHƯA vá: đó
    là dòng hỏng tới mức không nhận ra nó nói về phiếu nào, càng cần người nhìn.

    Cố ý KHÔNG chặn trần tuổi: một dòng hỏng ba tháng không ai đụng vẫn phải kêu
    mỗi sáng. Đường tắt duy nhất để im là vá nó, đúng như mong muốn.
    """
    cutoff = (datetime.now(VN_TZ) - timedelta(hours=max(hours, 0))).replace(tzinfo=None)
    query = select(SyncLog).where(
        SyncLog.status == int(SyncStatus.FAILED),
        SyncLog.created_at < cutoff,
    )
    if source:
        query = query.where(SyncLog.source == source)
    failures = list(db.execute(query.order_by(SyncLog.id.desc()).limit(limit)).scalars())
    if not failures:
        return []

    records = [f for f in failures if f.grain != int(SyncGrain.RUN) and f.legacy_id]
    runs = [f for f in failures if f.grain == int(SyncGrain.RUN) and f.job]
    healed = _find_healed_records(db, records)
    healed_runs = _find_healed_runs(db, runs)

    stale: list[SyncLog] = []
    for row in failures:
        if row.grain == int(SyncGrain.RUN) and row.job:
            if healed_runs.get((row.source, row.job), 0) > row.id:
                continue
        elif row.legacy_id:
            if healed.get((row.source, row.entity, row.legacy_id), 0) > row.id:
                continue
        stale.append(row)
    return stale


#  Hai hàm dưới cố ý lọc bằng BA (hoặc HAI) mệnh đề `IN` rời nhau thay vì một
#  `IN` trên bộ ba cột. Ràng buộc rời là một tập CHA của tập cần tìm — nhưng
#  `GROUP BY` trả về đúng khóa thật, mà bên gọi chỉ tra theo khóa thật, nên kết
#  quả vẫn chính xác. Đổi lại: chạy được trên cả MySQL lẫn SQLite của bộ test,
#  và dùng được chỉ mục `ix_sync_log_source_legacy` thay vì quét bảng.

def _find_healed_records(db: Session, rows: list[SyncLog]) -> dict[tuple, int]:
    """{(nguồn, đối tượng, mã bên cũ): id dòng êm MỚI NHẤT}."""
    if not rows:
        return {}
    found = db.execute(
        select(SyncLog.source, SyncLog.entity, SyncLog.legacy_id, func.max(SyncLog.id))
        .where(
            SyncLog.id > min(r.id for r in rows),
            SyncLog.status.in_([int(s) for s in HEALED_STATUSES]),
            SyncLog.source.in_({r.source for r in rows}),
            SyncLog.entity.in_({r.entity for r in rows}),
            SyncLog.legacy_id.in_({r.legacy_id for r in rows}),
        )
        .group_by(SyncLog.source, SyncLog.entity, SyncLog.legacy_id)
    ).all()
    return {(source, entity, legacy_id): int(newest)
            for source, entity, legacy_id, newest in found}


def _find_healed_runs(db: Session, rows: list[SyncLog]) -> dict[tuple, int]:
    """{(nguồn, công việc): id lượt chạy THÀNH CÔNG mới nhất}."""
    if not rows:
        return {}
    found = db.execute(
        select(SyncLog.source, SyncLog.job, func.max(SyncLog.id))
        .where(
            SyncLog.id > min(r.id for r in rows),
            SyncLog.grain == int(SyncGrain.RUN),
            SyncLog.status == int(SyncStatus.SUCCESS),
            SyncLog.source.in_({r.source for r in rows}),
            SyncLog.job.in_({r.job for r in rows}),
        )
        .group_by(SyncLog.source, SyncLog.job)
    ).all()
    return {(source, job): int(newest) for source, job, newest in found}


def _finish(db: Session, entry: SyncLog, status: SyncStatus, message: str,
            local_id: int | None = None, warnings=None,
            content_hash: str = "") -> SyncLog:
    entry.status = int(status)
    #  NGUYÊN VĂN câu của bên kia, không diễn giải lại.
    entry.message = message or ""
    if local_id is not None:
        entry.local_id = local_id or 0
    if content_hash:
        entry.content_hash = content_hash
    if warnings:
        add_warning(entry, *warnings)
    if not entry.last_tried_at:
        entry.last_tried_at = now_text()
    entry.finished_at = now_text()
    db.commit()
    db.refresh(entry)
    return entry


def finish_ok(db: Session, entry: SyncLog, message: str = "",
              local_id: int | None = None, warnings=None,
              content_hash: str = "") -> SyncLog:
    """Xong. Dòng thành công VẪN có thể mang cờ cảnh báo — đó là cách lọc lại
    được mọi bản ghi có dữ liệu bịa."""
    return _finish(db, entry, SyncStatus.SUCCESS, message, local_id, warnings,
                   content_hash)


def finish_failed(db: Session, entry: SyncLog, message: str,
                  warnings=None) -> SyncLog:
    """Hỏng. Dòng này KHÔNG BAO GIỜ bị dọn đi."""
    return _finish(db, entry, SyncStatus.FAILED, message, None, warnings)


def finish_skipped(db: Session, entry: SyncLog, message: str = "Không có gì thay đổi",
                   local_id: int | None = None, warnings=None) -> SyncLog:
    """Bỏ qua. **Vẫn nên truyền `local_id` khi hàng bên ERP đã tồn tại**: cửa nhận
    trả ô đó về cho hệ nguồn ghi ngược, mà "không có gì phải làm" không có nghĩa
    là "chưa có hàng nào" — trả `0` là bảo bên kia xóa trắng mối nối vừa có."""
    return _finish(db, entry, SyncStatus.SKIPPED, message, local_id, warnings)


def clone_for_retry(db: Session, entry: SyncLog, user_id: int = 0) -> SyncLog:
    """Bấm "Chạy lại" thì sinh DÒNG MỚI, không sửa dòng cũ.

    Luật §3.2: một dòng = một sự kiện, không ghi đè lịch sử. Lần thử thứ hai là
    một sự kiện khác, phải nhìn thấy cả hai.
    """
    fresh = SyncLog(
        source=entry.source,
        grain=entry.grain,
        run_id=entry.run_id,
        job=entry.job,
        entity=entry.entity,
        direction=entry.direction,
        action=entry.action,
        legacy_id=entry.legacy_id,
        local_id=entry.local_id,
        status=int(SyncStatus.PENDING),
        message=f"Chạy lại từ dòng #{entry.id}",
        payload=entry.payload,
        content_hash=entry.content_hash,
        event_id=make_event_id(entry.source, entry.entity, entry.legacy_id, entry.action),
        attempt_count=0,
        last_tried_at="",
        warnings=entry.warnings,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(fresh)
    db.commit()
    db.refresh(fresh)
    return fresh


#  --- Dọn sổ ---------------------------------------------------------------

def purge_success(db: Session, months: int = PURGE_AFTER_MONTHS,
                  source: str = "") -> int:
    """Dọn dòng THÀNH CÔNG cũ hơn `months` tháng. Trả về số dòng đã dọn.

    ⚠️ Đây là nơi DUY NHẤT được phép xóa trong sổ, và nó chỉ chạm vào trạng
    thái *thành công*. Dòng lỗi giữ vĩnh viễn — sổ mất dòng lỗi thì lúc đi tra
    một sự cố cũ không còn gì để đọc.
    """
    cutoff = datetime.now(VN_TZ) - timedelta(days=30 * max(months, 1))
    query = select(SyncLog).where(
        SyncLog.status == int(SyncStatus.SUCCESS),
        SyncLog.created_at < cutoff.replace(tzinfo=None),
    )
    if source:
        query = query.where(SyncLog.source == source)
    rows = list(db.execute(query).scalars())
    for row in rows:
        db.delete(row)
    db.commit()
    LOGGER.info("Dọn sổ đồng bộ: xóa %s dòng thành công cũ hơn %s tháng.",
                len(rows), months)
    return len(rows)
