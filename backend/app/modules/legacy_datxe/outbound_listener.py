"""Bộ nghe ORM của chiều ERP -> app cũ (P3, bao-CR-596).

Vì sao nghe ở tầng ORM: cùng lý do `core/change_tracker.py`. Phiếu đặt xe và phiếu dấu bị
đổi ở hơn chục chỗ (duyệt, trả về, từ chối, hủy, điều phối, bốn nút của tài xế, km/chi
phí, đóng dấu, tạo, sửa). Cắm tay ở từng chỗ thì chỗ nào sót là im lặng — phiếu bên app cũ
đứng yên mà không ai biết.

BA LUẬT, cùng họ với `change_tracker.py`:

1. **Không ghi DB, không gọi mạng trong flush.** `before_flush` chỉ gom đối tượng,
   `after_flush` chỉ đổi đối tượng thành id (lúc đó phiếu mới đã có khóa chính).
2. **Chỉ giao việc khi đã COMMIT.** Giao dịch quay đầu thì vứt bộ đệm — gửi sang app cũ một
   thay đổi chưa từng xảy ra còn tệ hơn không gửi.
3. **Đang xử tín hiệu NHẬN về thì không gom** (`suppress_outbound`) — không thì hai bên đá
   qua đá lại vô tận (§7 bản vẽ).

Công tắc tắt thì không giao việc gì cả: không ghi sổ, không gửi (đại ca chốt 05/10/2026).
"""
from __future__ import annotations

import logging

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.modules.seal_request.model import SealRequest
from app.modules.sync_log.service import is_sync_in_progress
from app.modules.vehicle_booking.model import VehicleBooking

LOGGER = logging.getLogger(__name__)

TRACKED = {VehicleBooking: "vehicle_booking", SealRequest: "seal_request"}

#: Đổi mấy cột này thôi thì không có gì để gửi: dấu sửa cuối tự nhảy, còn `legacy_id` là
#: chính cú ghi ngược khóa sau khi app cũ tạo phiếu.
IGNORED_ATTRS = frozenset({"updated_at", "updated_by", "legacy_id"})

_OBJS_KEY = "datxe_outbound_objs"
_IDS_KEY = "datxe_outbound_ids"

#: Chờ vài giây rồi mới gửi: một lần bấm thường sinh hai ba lượt commit liền nhau (đổi
#: trạng thái, rồi hook duyệt ghi thêm), gom lại cho khỏi gửi ba lần cùng một ảnh chụp.
PUSH_COUNTDOWN_SECONDS = 3


def _has_real_change(obj) -> bool:
    state = inspect(obj)
    for attr in state.mapper.column_attrs:
        if attr.key in IGNORED_ATTRS:
            continue
        if state.attrs[attr.key].history.has_changes():
            return True
    return False


def _before_flush(session, flush_context, instances) -> None:
    if is_sync_in_progress():
        return
    try:
        bucket = session.info.setdefault(_OBJS_KEY, [])
        for obj in list(session.new):
            entity = TRACKED.get(type(obj))
            if entity:
                bucket.append((entity, obj))
        for obj in list(session.dirty):
            entity = TRACKED.get(type(obj))
            if entity and _has_real_change(obj):
                bucket.append((entity, obj))
    except Exception:  # noqa: BLE001 — đồng bộ hỏng không được kéo nghiệp vụ hỏng theo
        LOGGER.warning("datxe outbound: không gom được thay đổi", exc_info=True)


def _after_flush(session, flush_context) -> None:
    objs = session.info.pop(_OBJS_KEY, None)
    if not objs:
        return
    ids = session.info.setdefault(_IDS_KEY, set())
    for entity, obj in objs:
        row_id = inspect(obj).identity
        if row_id:
            ids.add((entity, int(row_id[0])))


def _after_commit(session) -> None:
    ids = session.info.pop(_IDS_KEY, None)
    if not ids:
        return
    try:
        from app.modules.legacy_datxe.outbound import is_outbound_enabled

        if not is_outbound_enabled():
            return
        from app.core.celery_app import celery_app

        for entity, row_id in sorted(ids):
            celery_app.send_task("datxe.push_outbound", args=[entity, row_id],
                                 countdown=PUSH_COUNTDOWN_SECONDS)
    except Exception:  # noqa: BLE001 — giao việc hỏng thì vòng `retry_outbound` nhặt lại sau
        LOGGER.warning("datxe outbound: không giao được việc gửi", exc_info=True)


def _after_rollback(session) -> None:
    session.info.pop(_OBJS_KEY, None)
    session.info.pop(_IDS_KEY, None)


_INSTALLED = False


def install_outbound_listener() -> None:
    """Gắn vào lớp `Session` — mọi phiên đều đi qua, gọi lại được."""
    global _INSTALLED
    if _INSTALLED:
        return
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "after_flush", _after_flush)
    event.listen(Session, "after_commit", _after_commit)
    event.listen(Session, "after_rollback", _after_rollback)
    _INSTALLED = True
