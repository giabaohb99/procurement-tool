from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.database import get_db
from app.core.entity_models import model_of
from app.core.response import success
from app.core.scoping import scope_condition

from .model import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

ACTION_LABEL = {
    "create": "Tạo mới",
    "update": "Cập nhật",
    "delete": "Xóa",
    "submitted": "Gửi duyệt",
    "approved": "Duyệt",
    "rejected": "Từ chối",
    #  Hai kết cục của bộ máy duyệt nhiều bước — xem `document/approval_bridge`.
    "returned": "Trả về",
    "withdrawn": "Rút phiếu",
    "dispatched": "Điều phối",
    "paid": "Ghi nhận đã chi",
    "cancelled": "Hủy",
    #  ⚠️ Dạng NGUYÊN THỂ của cùng những hành động trên. Bảng quyền của hệ dùng
    #  `approve` / `cancel` (xem `core/permissions.ACTIONS`), nên controller viết
    #  sau quen tay ghi dấu vết bằng đúng chữ đó — Nghỉ phép và Đặt phòng đều
    #  vậy. Thiếu mấy dòng này thì dòng dấu vết hiện mã Anh trần
    #  («Dego Admin — approve: Duyệt phiếu PH004»), thấy được ngày 04/09/2026.
    #  Nhận CẢ HAI dạng thay vì đi sửa lời gọi: dữ liệu đã ghi bằng dạng nguyên
    #  thể vẫn nằm trong bảng, sửa mã nguồn không làm nó đọc được.
    "submit": "Gửi duyệt",
    "approve": "Duyệt",
    "reject": "Từ chối",
    "return": "Trả về",
    "withdraw": "Rút phiếu",
    "cancel": "Hủy",
    #  Hai hành động còn lại của bảng quyền. Chưa chỗ nào ghi dấu vết bằng chúng,
    #  nhưng `require(entity, "print")` là hợp lệ ở mọi endpoint nên chỉ cần một
    #  người thêm `record(..., "print")` là dòng đó hiện mã trần.
    "print": "In",
    "export": "Xuất dữ liệu",
    #  Bảng quyền gọi việc sửa là `write`, dấu vết cũ gọi là `update` — hai chữ
    #  cho một việc, và cả hai đều đang được ghi ở đâu đó.
    "write": "Cập nhật",
    #  Mười mã dưới đây ĐANG có trong `tab_audit_log` mà thiếu nhãn — đếm trên
    #  dữ liệu thật ngày 05/09/2026: 971 dòng hiện mã Anh trần cho người đọc
    #  («Dego Admin — assign: Phân bổ NSTM»). Đúng thứ ghi chú ở khối trên đã
    #  cảnh báo, chỉ là chưa ai đi soát bảng.
    "login": "Đăng nhập",
    "login_failed": "Đăng nhập thất bại",
    "assign": "Phân bổ",
    "processing": "Đang xử lý",
    "completed": "Hoàn tất",
    "item_progress": "Cập nhật tiến độ dòng",
    "document_status": "Đổi trạng thái chứng từ",
    "line_status": "Đổi trạng thái dòng",
    "expected_date": "Đổi ngày dự kiến",
    "view_file": "Xem tệp",
    #  Chín mã CÓ trong mã nguồn nhưng chưa (hoặc hiếm khi) rơi vào bảng — quét
    #  bằng `ast` chứ không bằng dữ liệu, để bắt NGUỒN thay vì triệu chứng.
    "logout": "Đăng xuất",
    "adjust": "Điều chỉnh tồn",
    "auto_done": "Tự động hoàn tất",
    "fill_line": "Bổ sung dòng",
    "line_approve": "Duyệt dòng",
    "item_progress_auto": "Tự cập nhật tiến độ dòng",
    "pr_created": "Sinh yêu cầu mua hàng",
    "sync_options": "Đồng bộ phương án",
    "reply": "Phản hồi",
}


def _guard(db: Session, user, entity: str | None, entity_id: int | None):
    """Ai đọc được nhật ký nào. Trả về ĐIỀU KIỆN lọc thêm (hoặc `None`).

    HAI chế độ, cắt theo đúng hai chế độ sẵn có của route.

    Trước 05/09/2026 route này chỉ có `get_current_user`. Không `require`, không
    phạm vi, và `audit` **không nằm trong `ENTITIES`** nên cũng không có khóa nào
    để mà gác. Tài khoản không một grant nào đọc được nhật ký cả hệ — trong đó
    `entity=assistant` trả **nguyên văn câu hỏi mọi người gửi Trợ lý AI**, thứ
    người ta gõ khi tưởng chỉ mình đọc.

    ⚠️ **Không gác được bằng một khóa quản trị duy nhất.** `AuditTimeline` nhúng
    trong `CrudDetailPage` và mọi màn chi tiết của cả hai bản giao diện, nên gác
    thô là giết dòng thời gian nhật ký của mọi người dùng thường. Hai chế độ:

    * **Widget lịch sử** — luôn kèm `entity` (+ `entity_id`). Đòi đúng quyền đọc
      chứng từ đó, rồi soi phạm vi của CHÍNH bản ghi đó. Người mở được trang chi
      tiết thì qua được cả hai, nên không màn nào gãy.
    * **Màn «Nhật ký hệ thống»** — không truyền `entity`. Đây là lối duyệt toàn
      hệ, đòi khóa quản trị. Giao diện v2 đã gác menu đó bằng `setting`
      (`system/routes.tsx:57`); backend nay gác cho khớp. Nhận **`read` HOẶC
      `write`** vì vai trò có thể cấp `write` mà không cấp `read` — chặt hơn
      menu là khóa nhầm đúng người đang dùng thật.
    """
    if not entity:
        if not (user_has_permission(db, user, "setting", "read")
                or user_has_permission(db, user, "setting", "write")):
            raise HTTPException(403, "Không có quyền xem nhật ký toàn hệ thống")
        return None

    #  Hồ sơ của CHÍNH MÌNH thì luôn xem được lịch sử, không cần khóa nào.
    #  Trang cá nhân (`/me`) dựng `<AuditTimeline entity="user" entityId={profile.id} />`
    #  cho mọi người dùng, mà `user.read` là khóa QUẢN TRỊ TÀI KHOẢN — nhân viên
    #  thường không có. Thiếu ngoại lệ này thì ai cũng thấy Trang cá nhân của
    #  mình trống lịch sử, và vì 403 trên GET đang im lặng (xem `http-client.ts`)
    #  thì trống đó không phân biệt được với "chưa có thao tác nào".
    minh_xem_minh = ((entity == "user" and entity_id == user.id)
                     or (entity == "employee" and entity_id
                         and entity_id == getattr(user, "employee_id", 0)))
    if not minh_xem_minh and not user_has_permission(db, user, entity, "read"):
        raise HTTPException(403, f"Không có quyền xem nhật ký của: {entity}")
    if minh_xem_minh:
        return None

    #  `model_of` trả None cho entity khai `PUBLIC` (danh mục dùng chung): không
    #  có cột nào để lọc theo dòng, và lớp quyền vai trò ở trên đúng là cổng của
    #  chúng.
    model = model_of(entity)
    if model is None:
        return None

    cond = scope_condition(model, entity, user, get_perm_profile(db, user), "read")
    if cond is None:
        return None          # phạm vi «tất cả» — không phải lọc gì thêm

    if entity_id is not None:
        if db.query(model.id).filter(model.id == entity_id, cond).first() is None:
            #  404 chứ không 403, cùng luật với `get_scoped`: người ngoài phạm vi
            #  không cần biết bản ghi đó có thật hay không.
            raise HTTPException(404, "Không tìm thấy bản ghi")
        return None

    #  ⚠️ KHÔNG kèm `entity_id` = lối lọc theo LOẠI chứng từ. Bản vá đầu bỏ qua
    #  nhánh này với lý lẽ "phạm vi từng dòng không áp được, quyền vai trò là
    #  chốt". Đo trên hệ đang chạy 05/09/2026 thì lý lẽ đó sai: tài khoản
    #  `TESTREQ` (phạm vi `own`) thấy **0** phiếu mua hàng trong danh sách, mở
    #  thẳng một phiếu thì 403, mà vẫn đọc được nhật ký của **25** phiếu.
    #  Lọc bằng chính tập id nằm trong phạm vi — cùng điều kiện danh sách dùng.
    return AuditLog.entity_id.in_(select(model.id).where(cond))


@router.get("")
def list_logs(
    entity: str | None = Query(None, description="Tên entity (vd product, contract). Bỏ trống = tất cả"),
    entity_id: int | None = Query(None, description="ID của bản ghi"),
    action: str | None = Query(None, description="Hành động (vd create, update, delete)"),
    search: str | None = Query(None, description="Từ khóa tìm kiếm trong ghi chú hoặc entity"),
    created_by: int | None = Query(None, description="ID người thao tác"),
    from_date: str | None = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Đến ngày (YYYY-MM-DD)"),
    page: int | None = Query(None, ge=1, description="Số trang (bỏ trống = trả về mảng đơn)"),
    page_size: int = Query(20, ge=1, le=500),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    loc_pham_vi = _guard(db, user, entity, entity_id)

    q = db.query(AuditLog)
    if loc_pham_vi is not None:
        q = q.filter(loc_pham_vi)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if entity_id is not None:
        q = q.filter(AuditLog.entity_id == entity_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if created_by:
        q = q.filter(AuditLog.created_by == created_by)
    if search and search.strip():
        k = f"%{search.strip()}%"
        q = q.filter(or_(AuditLog.message.like(k), AuditLog.entity.like(k)))

    if from_date:
        try:
            fd = datetime.strptime(from_date[:10], "%Y-%m-%d")
            q = q.filter(AuditLog.created_at >= fd)
        except Exception:
            pass
    if to_date:
        try:
            td = datetime.strptime(to_date[:10], "%Y-%m-%d")
            td_end = datetime.combine(td.date(), time.max)
            q = q.filter(AuditLog.created_at <= td_end)
        except Exception:
            pass

    q = q.order_by(AuditLog.id.desc())

    def _format(l: AuditLog):
        return {
            "id": l.id,
            "entity": l.entity,
            "entity_id": l.entity_id,
            "action": l.action,
            "action_label": ACTION_LABEL.get(l.action, l.action),
            "message": l.message,
            "by": resolve_actor(db, l.created_by),
            "by_id": l.created_by,
            "at": l.created_at,
        }

    # Nếu truyền `page`: trả về dạng phân trang cho màn hình Nhật ký hệ thống
    if page is not None:
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return success({"total": total, "items": [_format(l) for l in items], "page": page, "page_size": page_size})

    # Nếu không truyền `page`: trả về mảng đơn cho các widget lịch sử chi tiết
    logs = q.limit(limit).all()
    return success([_format(l) for l in logs])
