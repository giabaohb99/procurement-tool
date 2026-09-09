from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.database import get_db
from app.core.entity_models import model_of
from app.core.permissions import ENTITIES
from app.core.response import success
from app.core.scoping import scope_condition

from .model import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

#  Entity ghi trong nhật ký -> khóa trong bảng quyền, khi hai bên KHÔNG trùng tên.
#  FAQ của Help Center ghi dấu vết dưới entity `faq` nhưng mọi route của nó gác bằng
#  `help_article` (không có khóa `faq` trong ENTITIES). Thiếu dòng này thì màn
#  "Lịch sử" của Help Center mất sạch phần FAQ sau khi gác.
PERMISSION_KEY_ALIAS = {"faq": "help_article"}

ACTION_LABEL = {
    "create": "Tạo mới", "update": "Cập nhật", "delete": "Xóa",
    "submitted": "Gửi duyệt", "approved": "Duyệt", "rejected": "Từ chối",
    "dispatched": "Điều phối",
    "paid": "Ghi nhận đã chi", "cancelled": "Hủy",
    #  Dạng NGUYÊN THỂ của cùng những hành động trên: bảng quyền dùng `approve` /
    #  `cancel`, controller viết sau quen tay ghi dấu vết bằng đúng chữ đó. Nhận cả
    #  hai dạng thay vì sửa lời gọi — dữ liệu đã ghi vẫn nằm trong bảng.
    "submit": "Gửi duyệt", "approve": "Duyệt", "reject": "Từ chối", "cancel": "Hủy",
    "write": "Cập nhật", "print": "In", "export": "Xuất dữ liệu",
    #  Các mã ĐANG có trong `tab_audit_log` prod mà thiếu nhãn (đếm 05/09/2026 trên
    #  erp-v2: 971 dòng hiện mã Anh trần cho người đọc).
    "login": "Đăng nhập",
    "login_failed": "Đăng nhập thất bại",
    "logout": "Đăng xuất",
    #  bao-CR-313 / BM-003: gia hạn phiên bằng refresh token nay có dấu vết + IP.
    "refresh": "Gia hạn phiên",
    "refresh_failed": "Gia hạn phiên thất bại",
    "assign": "Phân bổ",
    "processing": "Đang xử lý",
    "completed": "Hoàn tất",
    "item_progress": "Cập nhật tiến độ dòng",
    "item_progress_auto": "Tự cập nhật tiến độ dòng",
    "document_status": "Đổi trạng thái chứng từ",
    "line_status": "Đổi trạng thái dòng",
    "expected_date": "Đổi ngày dự kiến",
    "view_file": "Xem tệp",
    "adjust": "Điều chỉnh tồn",
    "auto_done": "Tự động hoàn tất",
    "fill_line": "Bổ sung dòng",
    "line_approve": "Duyệt dòng",
    "pr_created": "Sinh yêu cầu mua hàng",
    "sync_options": "Đồng bộ phương án",
    "reply": "Phản hồi",
    #  bao-CR-311 — thao tác phương án trên Yêu cầu báo giá. Trước 07/09/2026 cả ba
    #  KHÔNG ghi dấu vết gì: gắn nhầm một phương án thì dấu duy nhất là cột
    #  `created_by` nằm trên chính dòng option, mà không màn nào hiện nó ra.
    "add_option": "Gắn phương án",
    "del_option": "Gỡ phương án",
    "choose_option": "Chốt phương án",
    "unchoose_option": "Bỏ chốt phương án",
}


def _guard(db: Session, user, entity: str | None, entity_id: int | None):
    """Ai đọc được nhật ký nào. Trả về ĐIỀU KIỆN lọc thêm (hoặc `None`).

    bao-CR-313 / BM-001. Trước bản này route chỉ có `get_current_user`: không `require`,
    không phạm vi, `entity` do người gọi truyền thẳng vào truy vấn và `entity_id` được
    bỏ trống — bất kỳ tài khoản đăng nhập nào cũng đọc được nhật ký của mọi phân hệ,
    trong đó `entity=auth` chứa IP + tài khoản + lịch sử gõ sai mật khẩu của cả công ty.
    Chép từ nhánh `erp-v2` (vá 05/09/2026), thêm chốt "entity không có trong bảng
    quyền thì không ai đọc được".

    Không gác được bằng một khóa quản trị duy nhất: dòng thời gian nhật ký nhúng trong
    `CrudDetail` và mọi màn chi tiết của `frontend/` lẫn Help Center, gác thô là giết
    dòng thời gian của mọi người dùng thường — mà 403 trên GET đang im lặng nên trống
    đó không phân biệt được với "chưa có thao tác nào". Hai chế độ:

    * Widget lịch sử — luôn kèm `entity` (+ `entity_id`). Đòi đúng quyền đọc chứng từ
      đó, rồi soi phạm vi của CHÍNH bản ghi đó (kèm id) hoặc lọc theo tập id nằm trong
      phạm vi (không kèm id). Người mở được trang chi tiết thì qua được cả hai.
    * Không truyền `entity` — lối duyệt toàn hệ, đòi khóa quản trị `setting` (`read`
      HOẶC `write`, vì vai trò có thể cấp `write` mà không cấp `read`). Ai có khóa này
      thì lọc theo entity nào cũng được, kể cả `auth`/`assistant` (không phải khóa quyền).
    """
    is_system_admin = (user_has_permission(db, user, "setting", "read")
                       or user_has_permission(db, user, "setting", "write"))
    if not entity:
        if not is_system_admin:
            raise HTTPException(403, "Không có quyền xem nhật ký toàn hệ thống")
        return None
    if is_system_admin:
        #  Lọc theo entity không được khắt khe hơn "không lọc": người đọc được toàn hệ
        #  thì đọc được từng phần, kể cả `auth` (không phải khóa quyền, nên không thể
        #  cấp `read` cho nó) — đó chính là màn nhật ký đăng nhập của quản trị.
        return None

    #  Hồ sơ của CHÍNH MÌNH thì luôn xem được lịch sử, không cần khóa nào — `user.read`
    #  là khóa QUẢN TRỊ TÀI KHOẢN, nhân viên thường không có.
    is_own_profile = ((entity == "user" and entity_id == user.id)
                      or (entity == "employee" and entity_id
                          and entity_id == getattr(user, "employee_id", 0)))
    if is_own_profile:
        return None

    #  `auth`, `assistant`, chuỗi gõ bừa... không nằm trong bảng quyền nên không vai
    #  trò nào cấp được `read` cho chúng. Nói thẳng thay vì dựa vào việc tra quyền
    #  trả False: mai có người thêm một entity "kỹ thuật" vào ENTITIES thì luật này
    #  vẫn đúng, còn luật ngầm thì không ai nhớ.
    perm_key = PERMISSION_KEY_ALIAS.get(entity, entity)
    if perm_key not in ENTITIES:
        raise HTTPException(403, f"Không có quyền xem nhật ký của: {entity}")
    if not user_has_permission(db, user, perm_key, "read"):
        raise HTTPException(403, f"Không có quyền xem nhật ký của: {entity}")

    #  `model_of` trả None cho entity không lọc theo dòng (danh mục dùng chung, hợp
    #  đồng, bài HDSD...): lớp quyền vai trò ở trên đúng là cổng của chúng.
    model = model_of(entity)
    if model is None:
        return None

    cond = scope_condition(model, entity, user, get_perm_profile(db, user), "read")
    if cond is None:
        return None          # phạm vi «tất cả» — không phải lọc gì thêm

    if entity_id is not None:
        if db.query(model.id).filter(model.id == entity_id, cond).first() is None:
            #  404 chứ không 403, cùng luật với danh sách: người ngoài phạm vi
            #  không cần biết bản ghi đó có thật hay không.
            raise HTTPException(404, "Không tìm thấy bản ghi")
        return None

    #  KHÔNG kèm `entity_id` = lối lọc theo LOẠI chứng từ (Help Center dùng cho
    #  `help_article`). Phải cắt theo phạm vi bằng chính tập id danh sách được thấy:
    #  một cổng chặn đúng ở đường "một bản ghi" mà bỏ ngỏ đường "cả danh sách" thì
    #  chưa chặn gì cả.
    return AuditLog.entity_id.in_(select(model.id).where(cond))


@router.get("")
def list_logs(
    entity: str | None = Query(None, description="Tên entity (vd product, contract). Bỏ trống = toàn hệ, cần quyền setting"),
    entity_id: int | None = Query(None, description="Bỏ trống = lấy log của MỌI bản ghi thuộc entity (trong phạm vi)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    scope_filter = _guard(db, user, entity, entity_id)

    q = db.query(AuditLog)
    if scope_filter is not None:
        q = q.filter(scope_filter)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if entity_id is not None:
        q = q.filter(AuditLog.entity_id == entity_id)

    logs = q.order_by(AuditLog.id.desc()).limit(limit).all()
    return success([
        {
            "action": l.action,
            "action_label": ACTION_LABEL.get(l.action, l.action),
            "message": l.message,
            "entity": l.entity,
            "entity_id": l.entity_id,
            "by": resolve_actor(db, l.created_by),
            "at": l.created_at,
        }
        for l in logs
    ])
