"""Cửa NHẬN của app đặt xe cũ: `POST /api/sync/datxe/events` (§5.2 bản thiết kế).

Đây là cửa MÁY GỌI MÁY, không có người đăng nhập đứng sau. Không có token, không
có phiên, không có phân quyền theo vai trò — thứ duy nhất gác cửa là chữ ký HMAC
chung khóa với app cũ (`SYNC_SHARED_SECRET`, khai hai đầu ở `.env`, dev khác
prod). Vì vậy:

- Chữ ký ký trên **nguyên văn body**, nên phải đọc `await request.body()` chứ
  không đọc qua Pydantic: Pydantic dựng lại chuỗi khác đi một dấu cách là chữ ký
  trượt hết.
- Chữ ký sai thì trả **401 và KHÔNG ghi gì xuống DB**. Ghi lại mọi cú gọi hỏng
  chữ ký là mở đường cho người ngoài bơm đầy sổ đồng bộ.
- Nguồn bị ghim cứng bằng `SOURCE_DATXE`: header `X-Sync-Source` chỉ để bên kia
  tự khai, không được phép chọn giùm ERP là dùng khóa của hệ nào.
- Nguồn TẮT (`SYNC_DATXE_ENABLED=false`) cũng trượt ngay ở `verify_signature` —
  đó là cái công tắc để đại ca đóng cửa này lại mà không cần deploy.

App cũ chờ câu trả lời của cửa này rồi mới xong thao tác của người dùng, nên
đường này phải NHANH và không bao giờ được ném lỗi ra ngoài dạng 500 trần trụi.
"""
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error, success
from app.core.sync_signature import (
    HEADER_SIGNATURE,
    HEADER_SOURCE,
    HEADER_TIMESTAMP,
    verify_signature,
)
from app.modules.sync_log.constants import SyncStatus
from app.modules.sync_log.registry import SOURCE_DATXE

from .resolver import LegacyCatalog
from .service import MODEL, apply_legacy_record, entity_of, find_local_id

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync/datxe", tags=["sync-datxe"])

PATH_EVENTS = "/api/sync/datxe/events"

#: Việc app cũ báo sang. `delete` cố ý KHÔNG xóa gì bên ERP — xem `_handle`.
ACTION_DELETE = "delete"


@router.post("/events")
async def receive_legacy_event(request: Request, db: Session = Depends(get_db)):
    """Nhận MỘT sự kiện từ app cũ.

    Thân yêu cầu theo hợp đồng §5.2:
    `{event_id, occurred_at, entity, action, legacy_id, erp_id, data}`.
    Trả về `{erp_id, status, sync_log_id}` để bên kia ghi ngược `erpId` vào
    Firebase và khỏi gửi lại phiếu đó nữa.
    """
    raw = await request.body()
    body = raw.decode("utf-8", errors="replace")
    source = request.headers.get(HEADER_SOURCE, "")
    ok, reason = verify_signature(
        SOURCE_DATXE, PATH_EVENTS, body,
        request.headers.get(HEADER_TIMESTAMP, ""),
        request.headers.get(HEADER_SIGNATURE, ""),
    )
    if source != SOURCE_DATXE:
        ok, reason = False, "Hệ nguồn không hợp lệ"
    if not ok:
        #  Ghi log ỨNG DỤNG chứ không ghi sổ đồng bộ: sổ chỉ dành cho việc thật.
        LOGGER.warning("Từ chối sự kiện app cũ: %s", reason)
        return error(reason, code="sync_unauthorized", status_code=401)

    try:
        payload = await request.json()
    except ValueError:
        return error("Thân yêu cầu không phải JSON", code="sync_bad_body")
    if not isinstance(payload, dict):
        return error("Thân yêu cầu phải là một đối tượng JSON", code="sync_bad_body")

    return _handle(db, payload)


def _handle(db: Session, payload: dict):
    legacy_id = str(payload.get("legacy_id") or "").strip()
    if not legacy_id:
        return error("Thiếu legacy_id", code="sync_bad_body")

    node = payload.get("data")
    if not isinstance(node, dict):
        return error("Thiếu phần data của phiếu", code="sync_bad_body")

    action = str(payload.get("action") or "").strip().lower()
    if action == ACTION_DELETE:
        #  Bên app cũ xóa phiếu thì ERP GIỮ NGUYÊN. Phiếu ở đây đã kéo theo
        #  lịch sử duyệt, tệp đính kèm và dấu vết thao tác; xóa chúng theo một
        #  lệnh máy gọi máy là mất dữ liệu không lấy lại được, mà chiều ngược
        #  chưa có ai đối chứng. Ai muốn bỏ thì hủy phiếu bên ERP bằng tay.
        LOGGER.info("App cũ báo xóa phiếu %r — ERP giữ nguyên", legacy_id)
        return success({"erp_id": 0, "status": int(SyncStatus.SKIPPED),
                        "sync_log_id": 0},
                       message="ERP không xóa phiếu theo app cũ, đã bỏ qua")

    entity = str(payload.get("entity") or "").strip() or entity_of(node)
    if entity not in MODEL:
        return error(f"Chưa hỗ trợ loại dữ liệu {entity!r}", code="sync_bad_entity")

    try:
        entry = apply_legacy_record(
            db, node=node, legacy_id=legacy_id, entity=entity,
            event_id=str(payload.get("event_id") or "").strip(),
            catalog=LegacyCatalog(db),
        )
    except ValueError as exc:
        return error(str(exc), code="sync_bad_body")

    if entry is None:
        #  Trùng sự kiện hoặc nội dung y hệt lần trước. Trả 200 có chủ ý: bên
        #  kia đã làm đúng việc của nó, báo lỗi thì nó thử lại vô ích. Nhưng
        #  `erp_id` vẫn phải là id THẬT — bên kia ghi ô đó vào `erpId`, trả `0`
        #  là xóa mất mối nối của chính phiếu vừa nhận xong.
        return success({"erp_id": find_local_id(db, entity, legacy_id),
                        "status": int(SyncStatus.SKIPPED), "sync_log_id": 0},
                       message="Đã nhận trước đó, không có gì phải làm")

    return success({"erp_id": entry.local_id, "status": entry.status,
                    "sync_log_id": entry.id},
                   message=entry.message or "Đã nhận")
