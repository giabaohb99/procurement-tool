"""Ba cửa của màn NHẬT KÝ HỆ THỐNG `/system/logs` (bao-CR-407 / CR-312 P5).

Xem `service.py` cho phần vì sao `tab_request_log` là xương sống. Ở đây chỉ có
chuyện phân quyền, và nó là chỗ dễ làm sai nhất của cả đợt:

**HAI khóa, không phải một** (`doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §7):

* `audit` — mở được màn: danh sách, biểu đồ, câu tiếng Việt «ai làm gì».
* `change_log` — xem thêm **giá trị trước/sau, thân yêu cầu, thân phản hồi,
  chi tiết lỗi**. Tách ra vì giá trị cũ có thể chứa **tên nhà cung cấp** — đúng
  thứ cả cơ chế phương án dựng ra để giấu với người yêu cầu. Ai tra được nhật ký
  mà mặc nhiên đọc được luôn phần đó thì cơ chế kia thủng từ cửa sau.

**Thiếu `change_log` thì LƯỢC Ở BACKEND, không giấu ở giao diện.** `build_detail`
nhận cờ `with_change_log` và không bỏ các ô đó vào gói trả về. Giấu bằng giao
diện thì mở DevTools ra là đọc được — chỗ này không phải chuyện thẩm mỹ.

⚠️ Vẫn nhận `setting` làm đường cũ (D-018) — xem ghi chú ở `_can_read_logs`.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service

router = APIRouter(prefix="/api/system-logs", tags=["system-log"])


def _can_read_logs(db: Session, user) -> bool:
    """Mở được màn Nhật ký hệ thống chưa.

    ⚠️ Nhận `audit` HOẶC `setting` — cùng luật với `_guard` của `/api/audit-logs`,
    và cùng lý do: khóa `audit` mới ra đời ở P5, mà seed KHÔNG ghi đè vai trò
    trên hệ đang chạy (D-018). Gác cứng bằng khóa mới là ngày deploy xong mọi
    quản trị hiện tại mất màn này, và họ chỉ phát hiện lúc đang đi tra một sự cố.
    Nhận `write` của `setting` nữa vì vai trò có thể cấp `write` mà quên `read`.

    Bỏ vế `setting` đi được — sau khi đã tick tay `audit` cho các vai trò thật.
    """
    return (user_has_permission(db, user, "audit", "read")
            or user_has_permission(db, user, "setting", "read")
            or user_has_permission(db, user, "setting", "write"))


def _can_read_changes(db: Session, user) -> bool:
    """Xem được giá trị trước/sau chưa.

    KHÔNG rơi về `setting` như hàm trên: đây là khóa mới hoàn toàn, chưa ai từng
    có đường vào phần dữ liệu này nên không có thói quen nào để giữ. Mặc định
    KHÔNG cho là đúng — cấp thêm thì tick tay ở màn Phân quyền.
    """
    return user_has_permission(db, user, "change_log", "read")


def _guard(db: Session, user) -> None:
    if not _can_read_logs(db, user):
        raise HTTPException(403, "Không có quyền xem nhật ký hệ thống")


def _build_query(db: Session, user_id, doc_code, route, ip, field, table,
                 from_time, to_time, status, action_group, source):
    return service.build_query(
        db, user_id=user_id, doc_code=doc_code, route=route, ip=ip, field=field,
        table=table, from_time=from_time, to_time=to_time, status=status,
        action_group=action_group, source=source)


@router.get("")
def list_logs(
    user_id: int | None = Query(None, description="ID tài khoản đã bấm"),
    doc_code: str | None = Query(None, description="Mã chứng từ (vd YCMH-2026-0012)"),
    route: str | None = Query(None, description="Khuôn đường dẫn, khớp một phần"),
    ip: str | None = Query(None, description="Địa chỉ IP, khớp đúng"),
    field: str | None = Query(None, description="Tên cột bị đổi"),
    table: str | None = Query(None, description="Tên bảng bị đổi"),
    from_time: str | None = Query(None, description="Từ lúc (YYYY-MM-DD hoặc ISO)"),
    to_time: str | None = Query(None, description="Đến lúc (YYYY-MM-DD hoặc ISO)"),
    status: str = Query(service.STATUS_ALL, description="all | error | blocked"),
    action_group: int | None = Query(None, description="Nhóm hành động"),
    source: int | None = Query(None, description="Nguồn: 1 API, 2 Celery, 3 script"),
    page: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Danh sách gộp theo `request_id` — mỗi dòng là MỘT lượt gọi."""
    _guard(db, user)
    q = _build_query(db, user_id, doc_code, route, ip, field, table,
                     from_time, to_time, status, action_group, source)
    total = q.count()
    items = service.build_page(db, q, page["offset"], page["limit"])
    return success({"total": total, "items": items,
                    "page": page["page"], "page_size": page["page_size"]})


@router.get("/summary")
def read_summary(
    user_id: int | None = Query(None),
    doc_code: str | None = Query(None),
    route: str | None = Query(None),
    ip: str | None = Query(None),
    field: str | None = Query(None),
    table: str | None = Query(None),
    from_time: str | None = Query(None),
    to_time: str | None = Query(None),
    status: str = Query(service.STATUS_ALL),
    action_group: int | None = Query(None),
    source: int | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Số liệu ba biểu đồ.

    ⚠️ Nhận **đúng bộ tham số của danh sách** — cố ý lặp lại cả mười một ô thay vì
    gọn hơn. Biểu đồ và bảng phải nói cùng một chuyện; cho biểu đồ ít ô lọc hơn
    là người dùng lọc bảng rồi đọc biểu đồ toàn hệ mà tưởng là của phần đã lọc.
    """
    _guard(db, user)
    q = _build_query(db, user_id, doc_code, route, ip, field, table,
                     from_time, to_time, status, action_group, source)
    return success(service.build_summary(db, q))


#  ⚠️ Đặt SAU `/summary`. FastAPI khớp route theo thứ tự khai: để đường có tham số
#  lên trước thì `/api/system-logs/summary` rơi vào đây và «summary» bị đọc thành
#  một mã request — 404, không ai hiểu vì sao.
@router.get("/{request_id}")
def read_detail(
    request_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Gói bốn tab của một lượt gọi: Tổng quan · Request · Thay đổi · Phiên."""
    _guard(db, user)
    raw = service.parse_request_id(request_id)
    if raw is None:
        raise HTTPException(404, "Mã lượt gọi không hợp lệ")
    row = service.find_request(db, raw)
    if row is None:
        raise HTTPException(404, "Không tìm thấy lượt gọi")
    return success(service.build_detail(db, row, with_change_log=_can_read_changes(db, user)))
