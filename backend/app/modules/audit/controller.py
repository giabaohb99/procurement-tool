from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.action_catalog import ACTION_LABELS, label_of_action
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

#  ⚠️ BẢNG NHÃN TỪNG NẰM Ở ĐÂY (khoảng 50 dòng) — đã dời sang
#  `core/action_catalog.py` (bao-CR-358 / NT-4). Ở đó mỗi mã khai một dòng gồm
#  ĐỦ mã + nhãn + nhóm, thay vì nhãn ở tệp này còn nhóm ở `core/logging_codes`.
#  Ba mã Duyệt dấu cổng 2 (seal_completed / seal_return_clerk / seal_reject_clerk)
#  đã thêm vào catalog nhóm APPROVE khi gộp nhánh pltgiang.
#
#  Giữ tên cũ `ACTION_LABEL` vì `work/activity_service.py` và ba bài kiểm đang
#  import theo tên đó.
ACTION_LABEL = ACTION_LABELS

#  Mã hành động do VĂN THƯ thực hiện (cổng 2) — hiện "Tên (Văn thư)" ở dòng nhật ký.
#  `seal_completed` KHÔNG nằm đây: nhãn "Hoàn thành (đóng dấu)" đã ngụ ý văn thư.
_CLERK_ROLE_ACTIONS = {"seal_return_clerk", "seal_reject_clerk"}


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

    Ba chốt bổ sung ngày 09/09/2026 (bao-CR-313, chuyển ngược từ nhánh `main`).
    """
    #  Người đọc được toàn hệ thì đọc được từng phần. Không có nhánh này, quản trị
    #  LỌC theo `entity=auth` ngay trên màn Nhật ký hệ thống lại ăn 403, vì `auth`
    #  không phải khóa quyền nên `user_has_permission` luôn trả False — tức là lọc
    #  khắt khe hơn không lọc, đúng cái màn nhật ký đăng nhập cần dùng nhất.
    is_system_admin = (user_has_permission(db, user, "setting", "read")
                       or user_has_permission(db, user, "setting", "write"))
    if not entity:
        if not is_system_admin:
            raise HTTPException(403, "Không có quyền xem nhật ký toàn hệ thống")
        return None
    if is_system_admin:
        return None

    #  Hồ sơ của CHÍNH MÌNH thì luôn xem được lịch sử, không cần khóa nào.
    #  Trang cá nhân (`/me`) dựng `<AuditTimeline entity="user" entityId={profile.id} />`
    #  cho mọi người dùng, mà `user.read` là khóa QUẢN TRỊ TÀI KHOẢN — nhân viên
    #  thường không có. Thiếu ngoại lệ này thì ai cũng thấy Trang cá nhân của
    #  mình trống lịch sử, và vì 403 trên GET đang im lặng (xem `http-client.ts`)
    #  thì trống đó không phân biệt được với "chưa có thao tác nào".
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
        by = resolve_actor(db, l.created_by)
        #  Chú thích VAI TRÒ sau tên: thao tác cổng-2 do Văn thư thực hiện thì hiện
        #  "Tên (Văn thư)" — vai trò là chú thích của người, không nhét vào nội dung.
        if l.action in _CLERK_ROLE_ACTIONS:
            by = f"{by} (Văn thư)"
        return {
            "id": l.id,
            "entity": l.entity,
            "entity_id": l.entity_id,
            "action": l.action,
            #  Qua hàm chứ không tra thẳng bảng: hàm còn nhận cả HỌ mã theo tiền
            #  tố (`tool:list_pr` → «Trợ lý AI gọi công cụ ‹list_pr›»), thứ mà
            #  tra bảng phẳng luôn trượt.
            "action_label": label_of_action(l.action),
            "message": l.message,
            "by": by,
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
