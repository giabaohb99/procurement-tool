"""BƯỚC 0 đồng bộ app đặt xe / duyệt dấu cũ — app cũ không được đè thao tác làm trên ERP (duoc-CR-682).

Bối cảnh: chiều app cũ -> ERP chạy thật; chiều ERP -> app cũ đang TẮT (và anh Được chốt 26/10/2026 không ghi gì
sang app cũ — bên đó là prod). App cũ vì thế không biết ERP đã làm gì, và mỗi lần phiếu bên đó đổi (cộng lượt quét
ép 02:15 hằng đêm) chiều nhận lại chép đè: phiếu điều phối trên ERP lùi về "Đã duyệt" nhưng còn giữ xe, phiếu
hoàn tất / đóng dấu trên ERP lùi trạng thái, nội dung người dùng sửa trên ERP bị trả về bản cũ.

Không thể cấm cứng app cũ ghi: người ta VẪN điều phối bên app cũ, ERP đang soi gương (đại ca chốt 17/09/2026).
Nên phân xử THEO PHIẾU:

* `erp_action_at` — dấu "ERP đã đụng vào phiếu gốc app cũ lúc…". Bộ nghe `_before_flush` tự đóng khi BẤT KỲ cột
  nghiệp vụ nào đổi NGOÀI lượt đồng bộ (`is_sync_in_progress()` sai) trên phiếu có `legacy_id` — nút trên web, lưu
  nháp, hook bộ máy duyệt, việc nền. Đã đóng thì không gỡ. Migration lấp dấu cho phiếu ERP đã thao tác trước đó
  (nhật ký thao tác của NGƯỜI DÙNG, `actor_kind = 1`).
* Phiếu có dấu: ERP làm chủ CẢ phiếu — chiều nhận không chép ô nào nữa (review H1: chép nội dung thì lượt quét đêm
  trả mục đích người dùng vừa sửa trên ERP về bản cũ). Ngoại lệ duy nhất: app cũ HỦY / TỪ CHỐI phiếu chưa chốt bên
  ERP thì vẫn nhận TRẠNG THÁI đó — ý định thật của người dùng bên kia. Phiếu đã chốt thì trạng thái không đổi nữa
  (`service._write`). Lịch sử duyệt soi gương cũng thôi dựng lại (review M3).
* Phiếu chưa có dấu: soi gương như cũ.

Đánh đổi đã biết (review H3): ERP đụng vào rồi thì tiến độ làm TIẾP bên app cũ (vd điều phối bên đó sau khi ERP
duyệt) không sang ERP nữa. Chấp nhận vì chiều ERP -> app cũ đang tắt: không có cách nào hòa hai bên mà không ghi
sang app cũ; ERP hiện đã bị chặn duyệt phiếu gốc app cũ đang chờ (phiên soi gương `flow_id=0`).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.modules.seal_request.model import SEAL_CANCELLED, SEAL_REJECTED, SealRequest
from app.modules.sync_log.service import is_sync_in_progress
from app.modules.vehicle_booking.model import BK_CANCELLED, BK_REJECTED, VehicleBooking

LOGGER = logging.getLogger(__name__)

#  Bảng được theo dõi + ô TIẾN TRÌNH của mỗi bảng (để đọc — luật làm chủ hiện áp cho CẢ phiếu, xem docstring).
PROCESS_FIELDS = {
    VehicleBooking: frozenset({
        "status", "approved_by", "approved_at",
        "assigned_vehicle_id", "assigned_driver_id", "dispatched_by", "dispatched_at", "driver_status",
        "actual_start_time", "actual_end_time", "distance_km", "cost",
    }),
    SealRequest: frozenset({"status", "approved_by", "approved_at", "completed_by", "completed_at"}),
}

#  Trạng thái app cũ được đưa vào phiếu ERP đã làm chủ: hủy / từ chối từ bên kia là ý định thật.
LEGACY_TERMINAL_STATUSES = {
    VehicleBooking: frozenset({BK_CANCELLED, BK_REJECTED}),
    SealRequest: frozenset({SEAL_CANCELLED, SEAL_REJECTED}),
}


def is_erp_owned(row) -> bool:
    return bool(getattr(row, "erp_action_at", ""))


#  Cột không phải dữ liệu nghiệp vụ — đổi chúng không tính là "ERP đụng vào phiếu".
META_FIELDS = frozenset({"updated_at", "updated_by", "legacy_id", "erp_action_at", "is_deleted"})


def allowed_fields(target, new_status) -> frozenset[str] | None:
    """Ô app cũ ĐƯỢC chép vào phiếu này lượt này. `None` = không giới hạn (soi gương như cũ)."""
    model = type(target)
    if not is_erp_owned(target) or model not in PROCESS_FIELDS:
        return None
    if new_status in LEGACY_TERMINAL_STATUSES[model]:
        return frozenset({"status"})
    return frozenset()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _before_flush(session: Session, flush_context, instances) -> None:
    if is_sync_in_progress():
        return
    try:
        for obj in list(session.dirty):
            if type(obj) not in PROCESS_FIELDS or not getattr(obj, "legacy_id", "") or is_erp_owned(obj):
                continue
            state = inspect(obj)
            if any(attr.key not in META_FIELDS and state.attrs[attr.key].history.has_changes()
                   for attr in state.mapper.column_attrs):
                obj.erp_action_at = _now()
    except Exception:  # noqa: BLE001 — đánh dấu hỏng không được kéo nghiệp vụ hỏng theo
        LOGGER.warning("datxe: không đánh dấu được phiếu ERP đã thao tác", exc_info=True)


def install_erp_ownership_listener() -> None:
    if not event.contains(Session, "before_flush", _before_flush):
        event.listen(Session, "before_flush", _before_flush)
