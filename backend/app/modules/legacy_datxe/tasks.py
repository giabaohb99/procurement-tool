"""Hai vòng chạy nền của app đặt xe cũ. Lịch beat khai ở `core/celery_app.py`.

1. `datxe.pull_updated` — LƯỚI AN TOÀN (§11). Đường chính là cái móc bên app cũ
   gọi thẳng vào `/api/sync/datxe/events`; vòng này chỉ vá lúc cái móc trượt
   (mạng chập, Worker lỗi, người ta sửa phiếu thẳng dưới Firebase Console). Nó
   hỏi Firebase "phiếu nào có `updatedAt` mới hơn con trỏ lần trước" rồi đẩy qua
   đúng cửa `apply_legacy_record` mà cái móc đang dùng.

2. `datxe.retry_pending` — chạy lại dòng sổ đang *chờ* hoặc đang *lỗi*. Nút
   "Chạy lại" trên màn sổ chỉ sinh ra một dòng *chờ* rồi thả đó (cố ý: cửa HTTP
   không ngồi đợi một hệ ngoài đang chết); NGƯỜI NHẶT VIỆC chính là task này.
   Thiếu nó thì nút kia bấm xong không có gì xảy ra.

Cả hai đều bọc trong một dòng LƯỢT CHẠY (`grain = RUN`) của quyển sổ chung, và
các dòng phiếu bên trong gắn `run_id` về dòng đó — mở nhật ký đồng bộ là thấy
"lượt 10h05 kéo 12 phiếu, ghi 9, bỏ 2, hỏng 1" rồi bấm xuống từng phiếu.

CON TRỎ LÀ MỐC BAO GỒM, không phải mốc loại trừ: lượt sau bắt đầu ĐÚNG tại
`updatedAt` lớn nhất lượt trước, nên phiếu ở ranh giới được nhìn lại lần nữa.
Cộng thêm một mili-giây thì hai phiếu sửa cùng một mili-giây sẽ mất một; còn
nhìn lại thì `is_unchanged` chặn ngay, không tốn dòng sổ nào.
"""
import json
import logging
import time

from sqlalchemy import select

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.modules.sync_log.constants import SyncGrain, SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE, require_source
from app.modules.sync_log.service import (
    finish_failed,
    finish_run,
    last_successful_run,
    open_run,
)

from . import firebase
from .builder import PeopleResolver
from .resolver import LegacyCatalog
from .service import (
    ENTITY_SEAL,
    MODEL,
    apply_legacy_record,
    entity_of,
    get_seal_type_id,
    run_entry,
)

LOGGER = logging.getLogger(__name__)

JOB_PULL = "pull_updated"
JOB_RETRY = "retry_pending"

#: Nhánh chứa phiếu bên app cũ, và ô mốc thời gian dùng làm con trỏ.
NODE_REQUESTS = "requests"
CURSOR_FIELD = "updatedAt"

#: Lượt ĐẦU TIÊN (sổ chưa có con trỏ nào) nhìn lại 365 ngày để kéo phiếu cũ.
FIRST_RUN_LOOKBACK_HOURS = 24 * 365

#: Trần phiếu một lượt. Sửa dồn quá trần thì lượt sau kéo tiếp từ chỗ con trỏ
#: dừng — chậm chứ không mất.
MAX_RECORDS_PER_RUN = 200

#: Trần dòng chạy lại một lượt, và trần số lần thử của MỘT dòng.
MAX_RETRY_PER_RUN = 50
MAX_ATTEMPTS = 3


class LegacySyncOff(RuntimeError):
    """Nguồn đang tắt hoặc chưa cấu hình — *bỏ qua*, không phải sự cố."""


def now_ms() -> int:
    return int(time.time() * 1000)


def read_cursor(db) -> tuple[int, str]:
    """Mốc bắt đầu của lượt này. Trả `(mốc, chuỗi con trỏ lần trước)`."""
    previous = last_successful_run(db, SOURCE_DATXE, JOB_PULL)
    if previous is not None:
        try:
            return int(previous.cursor_to), previous.cursor_to
        except (TypeError, ValueError):
            LOGGER.warning("Con trỏ lượt trước không phải số: %r", previous.cursor_to)
    return now_ms() - FIRST_RUN_LOOKBACK_HOURS * 3600 * 1000, ""


def check_ready() -> None:
    """Chưa bật hoặc chưa có khóa đọc Firebase thì dừng sớm, đừng gọi ra ngoài."""
    if not require_source(SOURCE_DATXE).is_enabled():
        raise LegacySyncOff("SYNC_DATXE_ENABLED đang tắt")
    if not firebase.is_configured():
        raise LegacySyncOff("Chưa khai LEGACY_FIREBASE_DB_URL / LEGACY_FIREBASE_SECRET")


def pull_updated(db, *, run_id: int = 0, user_id: int = 0, start_at: int | None = None, fetch=None) -> dict:
    """Kéo phiếu có `updatedAt` mới hơn con trỏ. Trả bộ đếm cho dòng lượt chạy.

    `fetch` thay được để bài kiểm khỏi đi hỏi Firebase thật.
    """
    check_ready()
    if start_at is None:
        start_at_val, cursor_from = read_cursor(db)
    else:
        start_at_val, cursor_from = start_at, str(start_at)
    fetch = fetch or firebase.query_node
    nodes = fetch(NODE_REQUESTS, order_by=CURSOR_FIELD, start_at=start_at_val,
                  limit=MAX_RECORDS_PER_RUN) or {}

    #  Xếp theo `updatedAt` tăng dần rồi mới xử: con trỏ phải tiến theo đúng thứ
    #  tự thời gian, không theo thứ tự khóa Firebase trả về.
    ordered = sorted(nodes.items(), key=lambda kv: _updated_at(kv[1]))

    people = PeopleResolver(db)
    catalog = LegacyCatalog(db, actor_id=user_id)
    stats = {"fetched": len(ordered), "written": 0, "skipped": 0, "failed": 0,
             "unknown_type": 0, "cursor_from": cursor_from, "cursor_to": ""}
    seal_type_id = 0
    cursor_to = start_at

    for legacy_id, node in ordered:
        if not isinstance(node, dict):
            stats["unknown_type"] += 1
            continue
        entity = entity_of(node)
        if entity not in MODEL:
            #  Nhánh `requests` bên app cũ còn loại phiếu khác (vd đặt phòng
            #  họp). Không phải lỗi — chỉ là không thuộc phần đang đồng bộ.
            stats["unknown_type"] += 1
            cursor_to = max(cursor_to, _updated_at(node))
            continue
        if entity == ENTITY_SEAL and not seal_type_id:
            seal_type_id = get_seal_type_id(db)

        entry = run_one(db, legacy_id=legacy_id, node=node, entity=entity,
                        run_id=run_id, people=people, catalog=catalog,
                        seal_type_id=seal_type_id, user_id=user_id)
        _count(stats, entry)
        cursor_to = max(cursor_to, _updated_at(node))

    #  Con trỏ tiến kể cả khi vài phiếu hỏng: mỗi phiếu hỏng đã có dòng sổ *lỗi*
    #  của riêng nó, và `datxe.retry_pending` nhặt lại. Neo con trỏ lại vì một
    #  phiếu hỏng vĩnh viễn thì cứ năm phút lại kéo nguyên đám đó về, mãi mãi.
    stats["cursor_to"] = str(cursor_to)
    return stats


def run_one(db, *, legacy_id: str, node: dict, entity: str, run_id: int,
            people: PeopleResolver, catalog: LegacyCatalog, seal_type_id: int,
            user_id: int) -> SyncLog | None:
    """Một phiếu trong lượt quét. Nuốt lỗi CỦA LƯỢT, không nuốt lỗi của phiếu.

    `apply_legacy_record` tự đóng dòng sổ *lỗi* cho phiếu hỏng; thứ cần chặn ở
    đây là lỗi ném ra TRƯỚC khi có dòng sổ (vd `legacy_id` rỗng), vì nó sẽ giết
    cả lượt và những phiếu còn lại không ai xử.
    """
    try:
        return apply_legacy_record(db, node=node, legacy_id=legacy_id, entity=entity,
                                   run_id=run_id, people=people, catalog=catalog,
                                   seal_type_id=seal_type_id, user_id=user_id)
    except ValueError as exc:
        LOGGER.warning("Bỏ phiếu %r của app cũ: %s", legacy_id, exc)
        return None


def retry_pending(db, *, run_id: int = 0, user_id: int = 0) -> dict:
    """Chạy lại dòng sổ đang *chờ* / *lỗi* bằng chính `payload` đã lưu.

    Không đi hỏi Firebase: dòng sổ giữ nguyên văn phiếu lúc nhận, nên chạy lại là
    chạy lại ĐÚNG cái đã hỏng chứ không phải một bản mới hơn. Muốn bản mới hơn
    thì đó là việc của vòng quét.

    Chạy lại TẠI CHỖ (`attempt_count` tăng lên) chứ không đẻ dòng mới: cùng một
    `event_id`, cùng một `payload` — đó vẫn là một sự kiện, chỉ là lần thử thứ
    hai. Nút "Chạy lại" của người dùng thì khác, nó là một QUYẾT ĐỊNH mới nên
    `clone_for_retry` sinh hẳn dòng riêng; dòng đó rơi vào đây ở lần thử đầu.
    """
    check_ready()
    rows = list(db.execute(
        select(SyncLog)
        .where(
            SyncLog.source == SOURCE_DATXE,
            SyncLog.grain == int(SyncGrain.RECORD),
            SyncLog.status.in_([int(SyncStatus.PENDING), int(SyncStatus.FAILED)]),
            SyncLog.attempt_count < MAX_ATTEMPTS,
        )
        .order_by(SyncLog.id)
        .limit(MAX_RETRY_PER_RUN)
    ).scalars())

    people = PeopleResolver(db)
    catalog = LegacyCatalog(db, actor_id=user_id)
    stats = {"fetched": len(rows), "written": 0, "skipped": 0, "failed": 0,
             "unknown_type": 0, "cursor_from": "", "cursor_to": ""}
    seal_type_id = 0

    for row in rows:
        node = _payload_of(row)
        if node is None or row.entity not in MODEL:
            #  Hỏng ngay ở khâu đọc lại thì đóng luôn dòng đó, đừng để nó quay
            #  vòng mỗi năm phút cho tới khi chạm trần số lần thử.
            finish_failed(db, row, "Không đọc lại được nội dung phiếu đã lưu")
            stats["failed"] += 1
            continue
        if row.entity == ENTITY_SEAL and not seal_type_id:
            seal_type_id = get_seal_type_id(db)
        if run_id:
            row.run_id = run_id
        entry = run_entry(db, row, node=node, entity=row.entity,
                          legacy_id=row.legacy_id, people=people, catalog=catalog,
                          seal_type_id=seal_type_id, user_id=user_id)
        _count(stats, entry)

    return stats


def _updated_at(node) -> int:
    try:
        val = (node or {}).get(CURSOR_FIELD) or (node or {}).get("createdAt") or 0
        return int(val)
    except (TypeError, ValueError):
        return 0


def _payload_of(row: SyncLog) -> dict | None:
    try:
        node = json.loads(row.payload or "")
    except ValueError:
        return None
    return node if isinstance(node, dict) else None


def _count(stats: dict, entry: SyncLog | None) -> None:
    if entry is None:
        stats["skipped"] += 1
    elif entry.status == int(SyncStatus.SUCCESS):
        stats["written"] += 1
    elif entry.status == int(SyncStatus.FAILED):
        stats["failed"] += 1
    else:
        stats["skipped"] += 1


#  --- Vỏ Celery ------------------------------------------------------------

def run_logged(job: str, fn, actor_id: int = 0) -> dict:
    """Khung chung: mở dòng lượt chạy → chạy → đóng dòng. Cùng khuôn với
    `coffee_point/tasks.py::_run_logged`, cùng quyển sổ."""
    db = SessionLocal()
    run = open_run(db, SOURCE_DATXE, job, user_id=actor_id)
    status, message, stats = SyncStatus.SUCCESS, "", {}
    try:
        stats = fn(db, run.id) or {}
        return {"status": "success", "run_id": run.id, **stats}
    except LegacySyncOff as exc:
        db.rollback()
        status, message = SyncStatus.SKIPPED, str(exc)
        return {"status": "skipped", "run_id": run.id}
    except Exception as exc:  # noqa: BLE001 — mọi lỗi phải thành một dòng sổ *lỗi*
        db.rollback()
        status, message = SyncStatus.FAILED, str(exc)[:2000]
        LOGGER.exception("Vòng đồng bộ app cũ '%s' hỏng", job)
        return {"status": "failed", "run_id": run.id, "error": str(exc)[:200]}
    finally:
        detail = dict(stats)
        if status == SyncStatus.SUCCESS and not message:
            message = (f"Kéo {detail.get('fetched', 0)} phiếu, ghi "
                       f"{detail.get('written', 0)}, bỏ qua {detail.get('skipped', 0)}, "
                       f"hỏng {detail.get('failed', 0)}")
        finish_run(
            db, run, status, message=message,
            fetched=int(detail.pop("fetched", 0) or 0),
            written=int(detail.pop("written", 0) or 0),
            skipped=int(detail.pop("skipped", 0) or 0),
            cursor_from=str(detail.pop("cursor_from", "") or ""),
            cursor_to=str(detail.pop("cursor_to", "") or ""),
            detail=detail or None,
        )
        db.close()


@celery_app.task(name="datxe.pull_updated")
def pull_updated_task(actor_id: int = 0) -> dict:
    return run_logged(JOB_PULL,
                      lambda db, run_id: pull_updated(db, run_id=run_id, user_id=actor_id),
                      actor_id)


@celery_app.task(name="datxe.retry_pending")
def retry_pending_task(actor_id: int = 0) -> dict:
    return run_logged(JOB_RETRY,
                      lambda db, run_id: retry_pending(db, run_id=run_id, user_id=actor_id),
                      actor_id)
