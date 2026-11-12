from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.bulk_delete import ensure_all_draft
from app.core.auth import get_perm_profile, require, user_has_permission
from app.core.central_purchasing import get_central_dept_id, is_central_dept
from app.core.scoping import apply_scope, approves_only_in_dept_proc, holds_handling_dept
from app.core.base_controller import apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.notification.service import trigger_notification

from . import option_service, service
#  bao-CR-711: chốt quyền dùng chung với serializer nằm ở `access.py`, dựng kết quả ở
#  `serializer.py`, truy vấn ở `service.py`. Controller chỉ còn nhận · gác · gọi · trả.
from .access import _can_dispatch, _can_return_requester, _in_approve_scope, _scope_ok
from .model import PurchaseRequest
from .sort_expressions import list_sort_allow
from .schema import (ApproveIn, AssignIn, ItemStatusIn, PRAssignSupplierIn, PRCreate,
                     PROptionCompleteIn, PROptionManualIn, PROptionDetailsIn, PROptionSupplierIn,
                     PROptionSurveyIn, PROptionUpdateIn, PRUpdate,
                     ReasonIn, RejectIn, TransferDeptIn, UrgentIn)
from .serializer import _out, _out_list, _out_option, _out_survey_lines

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase_request"])


def _in_scope(db: Session, pid: int, user, action: str) -> PurchaseRequest:
    """Nạp YCMH theo id NHƯNG chỉ khi nó nằm trong phạm vi `action` của người gọi.

    `require(entity, action)` chỉ trả lời "vai trò này được làm hành động đó không"; nó
    KHÔNG biết phiếu thuộc pháp nhân/phòng nào. Trước bản vá này mọi nhánh GHI đều dừng ở
    `service.get_pr` = `db.get` trần, nên gõ id vào URL là sửa/xóa/duyệt được phiếu của
    pháp nhân khác dù danh sách giấu đúng.

    `action` PHẢI khớp `require(...)` của chính route gọi nó — dùng `read` cho tất cả là
    lặp lại đúng lỗi của `_in_approve_scope` cũ (phạm vi duyệt rộng bằng phạm vi xem).

    Trả **404 "Không tìm thấy"** cho cả hai kiểu trượt (không có / ngoài phạm vi), đúng
    khuyến nghị ở docstring `get_scoped`: người ngoài phạm vi không cần biết phiếu có thật
    hay không. Đây cũng đúng mã lỗi mà `service.get_pr` vẫn trả cho id không tồn tại, nên
    các nhánh GHI không đổi hình dạng lỗi.
    """
    pr = apply_scope(service.query_live_by_id(db, pid),
                     PurchaseRequest, "purchase_request", user,
                     get_perm_profile(db, user), action).first()
    if not pr:
        raise HTTPException(404, "Không tìm thấy yêu cầu mua")
    return pr


def _read_scoped_or_403(db: Session, pid: int, user, profile: dict) -> PurchaseRequest:
    """Cổng ĐỌC cũ của `GET /{pid}` và hai đường đọc anh em: phạm vi `read`, KHÔNG bỏ phiếu xóa
    mềm, trượt thì 403 "Ngoài phạm vi được phép xem" — giữ nguyên mã lỗi lẫn câu chữ."""
    pr = apply_scope(service.query_by_id(db, pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return pr


def _notify_assigned(db: Session, pr, user, background_tasks: BackgroundTasks) -> None:
    """Báo "được phân công phụ trách" cho NSTM vừa được gán tự động.
    Gọi ở bước điều phối (công tắc BẬT) hoặc ngay khi duyệt (công tắc TẮT) — nội dung y như nhau."""
    uids = service.assigned_user_ids(db, pr)
    if uids:
        trigger_notification(db=db, event="pr_assigned", doc_type="purchase_request", doc_code=pr.code,
                             creator_id=user.id, background_tasks=background_tasks,
                             link=f"/purchase-requests/{pr.id}", recipient_ids=uids)


def _list_query(request: Request, db: Session, user):
    """Câu truy vấn danh sách (lọc + phạm vi + sắp xếp) — dùng chung cho màn danh sách và xuất Excel."""
    query = service.build_list_query(db, request)
    query = apply_scope(query, PurchaseRequest, "purchase_request", user, get_perm_profile(db, user))
    # duoc-CR-738: cột tính toán (`total`) sắp được nhờ biểu thức SQL riêng
    return apply_sort_from_request(query, PurchaseRequest, request, allow=list_sort_allow())


@router.get("")
def list_pr(
    request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("purchase_request", "read")),
):
    """Danh sách yêu cầu mua hàng (YCMH) trong phạm vi được xem, có lọc và phân trang."""
    query = _list_query(request, db, user)
    total, items = service.list_pr(db, query, pg)
    return success({"total": total, "items": _out_list(db, items, user)})


@router.get("/export/xlsx")
def export_xlsx(
    request: Request, ids: str = "", cols: str = "",
    db: Session = Depends(get_db), user=Depends(require("purchase_request", "export")),
):
    """CR-068 — xuất Excel danh sách YCMH, mỗi dòng hàng một hàng.

    `ids` = các phiếu người dùng tự tick (ưu tiên); bỏ trống thì xuất theo đúng bộ lọc đang đặt.
    `cols` = danh sách cột đang hiện trên bảng, để file khớp với những gì họ nhìn thấy.
    Phải khai báo TRƯỚC route `/{pid}` kẻo 'export' bị nuốt thành id.
    """
    from app.core.export_xlsx import check_row_limit, parse_ids, pick_columns, xlsx_response
    from . import export as ex

    query = _list_query(request, db, user)
    id_list = parse_ids(ids)
    if id_list:
        query = query.filter(PurchaseRequest.id.in_(id_list))
    prs = query.order_by(PurchaseRequest.id.desc()).all()
    check_row_limit(len(prs))
    rows = ex.build_rows(db, prs)
    check_row_limit(len(rows))
    columns = pick_columns(ex.HEADER_COLS, cols) + list(ex.LINE_COLS)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)


def _see_all_items(profile: dict, pr, user) -> bool:
    """Người tạo / người duyệt / xem toàn bộ chứng từ thu mua (scope proc/dept/company/all)
    → thấy mọi dòng. Nhân viên thu mua scope 'assigned/own' → chỉ thấy dòng phân bổ cho mình."""
    if pr.created_by == user.id:
        return True
    # Người YÊU CẦU (dù admin tạo giùm) cũng thấy mọi dòng của phiếu mình
    rid = getattr(user, "employee_id", 0) or 0
    if rid and getattr(pr, "requester_id", 0) == rid:
        return True
    for g in profile.get("grants", []):
        p = g["perms"].get("purchase_request")
        if not p:
            continue
        if p.get("approve"):
            return True
        if p.get("read") and p.get("scope") in ("proc", "dept_proc", "dept", "company", "all"):
            return True
    return False


@router.get("/meta/approver-candidates")
def approver_candidates_meta(department: str = "", department_id: int = 0, company_id: int = 0,
                             handler_dept_id: int = 0, head_of_dept_id: int = 0, db: Session = Depends(get_db),
                             user=Depends(require("purchase_request", "read"))):
    """bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt".

    Khai TRƯỚC `/{pid}` kẻo FastAPI nuốt "meta" thành id.
    """
    #  bao-CR-552: mọi người duyệt được (trừ Quản trị hệ thống) + Trưởng bộ phận — thôi dùng chung
    #  bộ với ô TBP (bản đó chỉ có trưởng phòng theo phòng, phòng IT không ai duyệt là ô khóa cứng).
    from app.core.approver_candidates import draft_fields, list_candidates_for_draft
    fields = draft_fields(db, user, department, department_id, company_id, handler_dept_id)
    return success({"items": list_candidates_for_draft(db, PurchaseRequest, "purchase_request", fields,
                                                       head_of_dept_id)})


@router.get("/{pid}/approver-candidates")
def approver_candidates_(pid: int, db: Session = Depends(get_db),
                         user=Depends(require("purchase_request", "read"))):
    """bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve)."""
    from app.core.approver_candidates import list_candidates_for_row
    row = _in_scope(db, pid, user, "read")
    return success({"items": list_candidates_for_row(db, PurchaseRequest, "purchase_request", row)})   # bao-CR-552


@router.get("/meta/dept-head")
def dept_head(department: str = "", department_id: int = 0, db: Session = Depends(get_db),
              user=Depends(require("purchase_request", "read"))):
    """Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không được xem DS nhân sự) tự điền TBP.

    bao-CR-474: trả kèm `head_of_dept_id` để màn tạo mới v2 điền sẵn cả NGƯỜI lẫn tên (ô chọn
    cần id để hiện đúng người), và nhận `department_id` (CR-086: neo bằng id, tên chỉ để lùi)."""
    return success({"head_of_dept": service.find_dept_head(db, department, department_id),
                    "head_of_dept_id": service.find_dept_head_id(db, department, department_id)})


@router.get("/meta/dept-head-candidates")
def dept_head_candidates_meta(department: str = "", company_id: int = 0, db: Session = Depends(get_db),
                              user=Depends(require("purchase_request", "read"))):
    """CR-071 — cùng danh sách nhưng tra theo PHÒNG BAN, cho màn TẠO MỚI (chưa có id phiếu).

    Phải khai TRƯỚC `/{pid}` nếu không FastAPI nuốt "meta" thành pid.
    """
    return success({"items": service.dept_head_candidates_by_department(db, department, company_id)})


@router.get("/{pid}/assignable-staff")
def assignable_staff_(pid: int, db: Session = Depends(get_db),
                      user=Depends(require("purchase_request", "read"))):
    """bao-CR-486 — NSTM chọn được cho phiếu này: đi theo ô "Phòng xử lý" (xem
    `category_assignee.service.assignable_staff`). Ô chọn ở màn chi tiết đọc từ đây thay vì lọc
    danh mục nhân sự theo tên phòng."""
    from app.modules.category_assignee.service import assignable_staff
    pr = _in_scope(db, pid, user, "read")
    return success({"items": [{"id": e.id, "code": e.code, "full_name": e.full_name,
                               "department_id": int(e.department_id or 0)}
                              for e in assignable_staff(db, pr)]})


@router.get("/{pid}/dept-head-candidates")
def dept_head_candidates(pid: int, db: Session = Depends(get_db),
                         user=Depends(require("purchase_request", "read"))):
    """CR-071 — những người duyệt được bước 1 phiếu này, để ô "Trưởng bộ phận" cho chọn.

    Ô này CHỈ để lưu + in (xem ghi chú ở `service.py`), không khóa quyền duyệt của ai.
    Danh sách rỗng = chưa ai đủ điều kiện; lúc đó FE để ô ở dạng chữ như cũ.
    """
    pr = _read_scoped_or_403(db, pid, user, get_perm_profile(db, user))
    return success({"items": service.dept_head_candidates(db, pr)})


@router.get("/{pid}")
def get_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Chi tiết một YCMH; người chỉ phụ trách một số dòng chỉ thấy dòng của mình."""
    profile = get_perm_profile(db, user)
    pr = _read_scoped_or_403(db, pid, user, profile)
    data = _out(db, pr, user)
    if not _see_all_items(profile, pr, user):
        code = profile.get("emp_code") or ""
        data["items"] = [it for it in data["items"] if (it.get("assignee") or "") == code]
    return success(data)


@router.get("/{pid}/order-progress")
def order_progress(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Tổng SL đã ĐẶT (qty_order) theo từng mã hàng, gộp từ các ĐMH cùng mã PYC.
    CHỈ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/hủy/từ chối) — phiếu nháp KHÔNG tính là đã đặt,
    khớp với logic đồng bộ trạng thái dòng (sync_from_purchase_orders).
    Dùng để prefill 'số lượng còn thiếu' khi tạo ĐMH mới + cảnh báo đặt vượt."""
    pr = _read_scoped_or_403(db, pid, user, get_perm_profile(db, user))
    # bao-CR-619: thêm `pending` (đơn nháp / chờ duyệt / bị trả lại) + `orders` (từng đơn theo mã) cho
    # cảnh báo đặt vượt; `ordered` giữ nguyên nghĩa cũ.
    return success(service.order_progress(db, pr.code))


@router.post("")
def create_pr(data: PRCreate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    """Tạo YCMH mới ở trạng thái Nháp; cụm nhà cung cấp thu mua chỉ người có quyền sửa NCC mới ghi."""
    can_pur = user_has_permission(db, user, "supplier", "write")   # Task 4: chỉ QL/Admin sửa cụm NCC thu mua
    return success(_out(db, service.create_pr(db, data, user.id, can_pur), user), "Đã tạo yêu cầu mua", 201)


@router.post("/{pid}/copy")
def copy_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    """Nhân bản một YCMH thành phiếu Nháp mới."""
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_pr(db, pid, user.id), user), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.post("/{pid}/clone")   # alias để nút Nhân bản ở danh sách (CrudList) dùng chung 1 đường dẫn
def clone_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    """Nhân bản một YCMH thành phiếu Nháp mới (tên cũ của đường `/copy`, giữ cho màn cũ)."""
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_pr(db, pid, user.id), user), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.patch("/{pid}/assign")
def assign_pr(pid: int, data: AssignIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    """Giao người phụ trách mua cho YCMH đã duyệt và báo chuông người được giao."""
    _in_scope(db, pid, user, "approve")
    pr = service.assign(db, pid, data, user.id)
    # Thông báo "được phân công phụ trách" cho NSTM (NSTM header + NSTM từng dòng)
    uids = [uid for uid in service.assigned_user_ids(db, pr) if uid != user.id]   # không tự báo mình
    if uids:
        trigger_notification(db=db, event="pr_assigned", doc_type="purchase_request", doc_code=pr.code,
                             creator_id=user.id, background_tasks=background_tasks,
                             link=f"/purchase-requests/{pr.id}", recipient_ids=uids)
    return success(_out(db, pr, user), "Đã lưu phân bổ NSTM")


@router.patch("/{pid}/urgent")
def set_urgent(pid: int, data: UrgentIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "write"))):
    """Bật/tắt cờ Đơn gấp (cả khi phiếu đã duyệt) + đồng bộ xuống ĐMH cùng pr_code."""
    _in_scope(db, pid, user, "write")
    pr = service.set_urgent(db, pid, data.is_urgent, user.id)
    return success(_out(db, pr, user))


@router.patch("/{pid}/item-status")
def update_item_status(pid: int, data: ItemStatusIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Cập nhật trạng thái một dòng hàng của YCMH; quản lý sửa mọi dòng, người phụ trách chỉ dòng của mình."""
    _in_scope(db, pid, user, "read")   # bảng dòng lọc theo phiếu cha — phiếu cha phải lọc phạm vi
    prof = get_perm_profile(db, user)
    pr_perm = prof["perms_union"].get("purchase_request", {})
    is_manager = bool(pr_perm.get("cancel") or pr_perm.get("approve"))   # quản lý/admin sửa mọi dòng
    emp_code = prof.get("emp_code") or ""
    return success(_out(db, service.update_item_status(db, pid, data, user.id, emp_code, is_manager), user), "Đã cập nhật trạng thái")


def _ensure_can_return_or_reject(db: Session, user, pr: PurchaseRequest):
    """Trả về / Từ chối: Quản lý (quyền cancel) làm được mọi giai đoạn;
    Người duyệt (quyền approve) chỉ làm được ở bước Chờ duyệt (submitted) VÀ trong phạm vi của mình.

    ⚠️ Nhánh "Quản lý" ĐI TẮT trước khi tới `_in_approve_scope`, nên trước bản vá này nó chỉ
    hỏi QUYỀN chứ không hỏi PHẠM VI — đọc lướt rất dễ tưởng cả hàm đã lọc. Nay mỗi nhánh
    kiểm phạm vi của ĐÚNG hành động đã cho nó đi qua (`cancel` / `approve`).
    """
    if user_has_permission(db, user, "purchase_request", "cancel") \
            and _scope_ok(db, user, pr.id, "cancel"):
        return
    if pr.status == "submitted" and user_has_permission(db, user, "purchase_request", "approve") \
            and _in_approve_scope(db, user, pr.id):
        return
    raise HTTPException(403, "Bạn không có quyền trả về / từ chối phiếu này")


@router.post("/{pid}/cancel")
def cancel_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Hủy YCMH kèm lý do và báo người tạo."""
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.cancel_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_cancelled", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr, user), "Đã hủy phiếu")


@router.post("/{pid}/return")
def return_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Trả YCMH về người yêu cầu để sửa; chỉ khi phiếu chờ duyệt hoặc đã duyệt mà chưa dòng nào lên đơn mua."""
    pr = service.get_pr(db, pid)
    if not _can_return_requester(db, user, pr):   # bao-CR-554: cùng cờ với nút trên giao diện
        if pr.status not in ("submitted",) + service.TRANSFERABLE_STATUSES or not service.can_return_requester(db, pr):
            raise HTTPException(400, "Chỉ trả về được phiếu đang chờ duyệt, hoặc đã duyệt mà chưa dòng nào "
                                     "lên đơn mua hàng — hủy đơn liên quan trước")
        raise HTTPException(403, "Bạn không có quyền trả về phiếu này")
    pr = service.return_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_returned", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr, user), "Đã trả phiếu về (Bị trả lại)")


def _ensure_holds_handling_dept(db: Session, user, pr) -> None:
    """bao-CR-414 GĐ5: chỉ quản lý thu mua của phòng ĐANG CẦM phiếu (hoặc toàn hệ) mới đẩy được."""
    if not holds_handling_dept(get_perm_profile(db, user), "purchase_request", pr, get_central_dept_id(db)):
        raise HTTPException(403, "Chỉ quản lý thu mua của phòng đang xử lý mới chuyển được phiếu này")


def _transfer_dept(db: Session, pid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                   user, *, target: int, message: str):
    pr = _in_scope(db, pid, user, "approve")
    _ensure_holds_handling_dept(db, user, pr)
    old_assignees = [it.assignee for it in service.items_of(db, pid) if (it.assignee or "").strip()]
    pr = service.transfer_handler_dept(db, pid, target, data.reason, user.id)
    where = "phòng thu mua" if not int(target or 0) else "phòng xử lý khác"   # bao-CR-524
    link = f"/purchase-requests/{pr.id}"
    reason = data.reason.strip()
    service.notify_users(db, [pr.created_by or user.id], f"{pr.code} — Chuyển {where}",
                         f"Yêu cầu mua hàng {pr.code} được chuyển sang {where}. Lý do: {reason}",
                         link, user.id, background_tasks)
    if old_assignees:                                  # NSTM bị gỡ khỏi dòng cũng cần biết
        service.notify_users(db, service.user_ids_of_employee_codes(db, old_assignees),
                             f"{pr.code} — Gỡ phân công mua hàng",
                             f"Phiếu {pr.code} đã chuyển {where}, phần phụ trách của bạn được gỡ. Lý do: {reason}",
                             link, user.id, background_tasks)
    return success(_out(db, pr, user), message)


@router.post("/{pid}/transfer-dept")
def transfer_dept_(pid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    """bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ (đường 2): gỡ NSTM mọi dòng, đổi phòng, phiếu về
    "Đã duyệt (chưa điều phối)" để phòng nhận điều phối lại. Lý do bắt buộc, ghi nhật ký."""
    return _transfer_dept(db, pid, data, background_tasks, user, target=data.handler_dept_id,
                          message="Đã chuyển phòng xử lý")


@router.post("/{pid}/return-dept")
def return_dept_(pid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    """bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện với chuyển phòng, đích là phòng thu mua
    mặc định (bao-CR-524: ghi id thật của PBA017, không còn `0` = "Thu mua chung" ảo). Khác "Trả
    về (Bị trả lại)": phiếu KHÔNG mất trạng thái đã duyệt."""
    return _transfer_dept(db, pid, data, background_tasks, user, target=0,
                          message="Đã trả phiếu về phòng thu mua")


@router.post("/{pid}/complete")
def complete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "cancel"))):
    """Chuyển YCMH sang Hoàn thành."""
    _in_scope(db, pid, user, "cancel")
    return success(_out(db, service.complete_pr(db, pid, user.id), user), "Đã hoàn thành phiếu")


def _can_edit_own(db: Session, pr, user) -> bool:
    """Người TẠO / người YÊU CẦU (admin tạo giùm) / người có quyền write được sửa & gửi duyệt."""
    rid = getattr(user, "employee_id", 0) or 0
    if pr.created_by == user.id or (rid and getattr(pr, "requester_id", 0) == rid):
        return True
    return user_has_permission(db, user, "purchase_request", "write")


@router.patch("/{pid}")
def update_pr(pid: int, data: PRUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    # Phạm vi đi theo `read` (đúng `require` của route): người YÊU CẦU thường chỉ được cấp
    # read+create trên YCMH (vai trò `employee` trong seed), lọc bằng `write` là khóa luôn
    # đường sửa phiếu nháp của chính họ.
    """Sửa YCMH; chỉ người tạo khi phiếu còn sửa được, hoặc người có quyền sửa."""
    pr = _in_scope(db, pid, user, "read")
    if not _can_edit_own(db, pr, user):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    can_pur = user_has_permission(db, user, "supplier", "write")   # Task 4: cụm NCC thu mua chỉ QL/Admin sửa
    return success(_out(db, service.update_pr(db, pid, data, user.id, can_pur), user), "Đã cập nhật")


@router.delete("/{pid}")
def delete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    """Xóa một YCMH."""
    _in_scope(db, pid, user, "delete")
    service.delete_pr(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_prs(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    """Xóa nhiều YCMH theo danh sách id trong phạm vi được xóa."""
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    # Lọc phạm vi TRƯỚC vòng lặp (khuôn của `contract/controller.py`): xóa hàng loạt mà chỉ
    # lặp theo id thì gửi đại một dãy số là dọn sạch phiếu Nháp của mọi pháp nhân.
    rows = apply_scope(service.query_live_by_ids(db, id_list),
                       PurchaseRequest, "purchase_request", user,
                       get_perm_profile(db, user), "delete").all()
    if not rows:
        raise HTTPException(403, "Ngoài phạm vi được phép xóa")
    #  bao-CR-547: kiểm CẢ LÔ trước khi xóa phiếu nào — chỉ phiếu Nháp (đại ca chốt 01/10/2026).
    ensure_all_draft(rows, "phiếu yêu cầu mua hàng")
    for pid in [r.id for r in rows]:
        try:
            service.delete_pr(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {pid}: {str(e)}") from e
    # Báo đúng số ĐÃ xóa, không báo số đã gửi lên — lệch nhau là có id ngoài phạm vi.
    return success(None, f"Đã xóa {len(rows)} bản ghi")


@router.post("/{pid}/submit")
def submit_pr(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    """Gửi duyệt YCMH ở trạng thái Nháp hoặc Bị trả lại."""
    pr = _in_scope(db, pid, user, "read")   # cùng lẽ với `update_pr`: phạm vi theo `require`
    if not _can_edit_own(db, pr, user):
        raise HTTPException(403, "Không có quyền gửi duyệt phiếu này")
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt được phiếu ở trạng thái Nháp hoặc Bị trả lại")
    # bao-CR-466: gửi duyệt phải có Phòng ban + Trưởng bộ phận. Hàm này tự CHỮA trước
    # (ô rỗng thì tra lại từ hồ sơ nhân sự / danh mục phòng ban — tài khoản có thể vừa
    # được gắn phòng sau khi phiếu ra đời) rồi mới CHẶN. Đặt trước `set_status` để phiếu
    # thiếu dữ liệu không bao giờ chạm được trạng thái `submitted`.
    service.ensure_submit_ready(db, pr, user.id)
    # bao-CR-499: phiếu cũ / phiếu chưa chọn người duyệt → mặc định Trưởng bộ phận vừa chốt ở trên.
    from app.core.print_signers import default_approver_to_head
    default_approver_to_head(pr)
    #  bao-CR-590 (đại ca chốt 05/10/2026): gửi duyệt BUỘC có Trưởng phòng phê duyệt. Hôm nay hai
    #  dòng trên đã bảo đảm điều đó (có TBP → người duyệt mặc định là TBP); chốt này giữ luật đứng
    #  vững nếu sau này ai đổi luật mặc định — phiếu không người duyệt là phiếu không ai được báo.
    if not pr.approver_employee_id:
        raise HTTPException(400, "Phiếu chưa có Trưởng phòng phê duyệt — chọn người duyệt rồi gửi lại")
    # CR-082: chốt cờ Đơn gấp trước khi gửi duyệt — phiếu cũ (tạo trước luật này) hoặc phiếu
    # sửa dòng bằng đường khác vẫn được đánh dấu đúng, và thông báo duyệt đi kèm mức ưu tiên thật.
    service.apply_auto_urgent(db, pr, user.id)
    pr = service.set_status(db, pid, "submitted", user.id)
    trigger_notification(
        db=db,
        event="pr_submitted",
        doc_type="purchase_request",
        doc_code=pr.code,
        creator_id=pr.created_by or user.id,
        background_tasks=background_tasks,
        is_urgent=bool(pr.is_urgent),
        link=f"/purchase-requests/{pr.id}",
        department=pr.department or "",
        department_id=pr.department_id or 0,
        # bao-CR-474: người được chọn ở ô TBP cũng nhận chuông báo duyệt (ngoài trưởng phòng
        # gán cứng + vai trò dept_head của phòng). Người trong danh sách chọn đều duyệt được.
        # bao-CR-499: người được CHỌN ở ô "Trưởng phòng phê duyệt" cũng nhận chuông + mail.
        extra_employee_ids=[x for x in (pr.head_of_dept_id, pr.approver_employee_id) if x] or None,
    )
    return success(_out(db, pr, user), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_pr(pid: int, data: ApproveIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    # Duyệt lần 1 (trưởng phòng) — chỉ trong phạm vi được phép duyệt. Phạm vi 'proc' (Admin thu mua)
    # không thấy phiếu 'submitted' nên tự động bị loại: họ chỉ điều phối, không duyệt thay trưởng phòng.
    """Duyệt YCMH; phiếu thuộc diện bỏ qua điều phối thì tự chuyển sang bước kế."""
    if not _in_approve_scope(db, user, pid):
        raise HTTPException(403, "Ngoài phạm vi được phép duyệt")
    # CR-071 — KHÔNG chặn theo `head_of_dept_id`: ô TBP chỉ để lưu + in, luật duyệt giữ như cũ.
    # CR-034: mặc định KHÔNG tự động phân bổ NSTM ở đây — phiếu dừng ở "Đã duyệt", chờ Quản lý/Admin
    # thu mua duyệt lần 2 (/dispatch). Nếu công tắc `pr_dispatch_enabled` bị TẮT thì chạy luôn bước
    # điều phối ngay tại đây (luồng cũ: duyệt phát là có nhân sự phụ trách).
    # bao-CR-485: đường công tắc TẮT ghi sổ ĐÚNG MỘT dòng "Duyệt" của trưởng phòng (kèm ghi chú
    # hệ thống tự phân bổ) — trước đây ghi thêm dòng "Điều phối" dưới tên họ, đọc như thể trưởng
    # phòng bấm Điều phối, một việc họ không có quyền.
    # bao-CR-497: ngoài công tắc chung, phiếu THỎA "điều kiện bỏ qua điều phối" (màn Cấu hình hệ
    # thống) cũng đi thẳng — để nhà máy tự mua không phải qua thu mua chung trong khi các phòng
    # khác vẫn hai bước. Ô điều kiện rỗng = hành vi cũ.
    pr = service.get_pr(db, pid)
    auto_dispatch = service.skip_dispatch_for(db, pr)
    pr = service.set_status(db, pid, "approved", user.id, audit=not auto_dispatch)
    # bao-CR-490: ghi nhân sự vừa duyệt vào "Trưởng phòng phê duyệt".
    from app.core.print_signers import stamp_approver
    stamp_approver(db, pr, user.id)
    db.commit()
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    n = blank_count = 0
    if auto_dispatch:
        # bao-CR-414: người duyệt chỉ có bậc `dept_proc` (quản lý thu mua CỦA PHÒNG) → chỉ dùng bộ
        # phân công riêng của phòng, không rơi về bộ của phòng thu mua mặc định (bao-CR-524).
        dept_only = approves_only_in_dept_proc(get_perm_profile(db, user), "purchase_request")
        # bao-CR-497: phiếu bỏ qua điều phối NHỜ điều kiện mà có phòng xử lý riêng thì chỉ dùng bộ
        # phân công của phòng đó — tách hẳn khỏi thu mua chung là mục đích của việc bỏ qua.
        # bao-CR-524: phiếu phòng thu mua mặc định xử lý (id PBA017 hoặc `0` cũ) KHÔNG tính là
        # "có phòng xử lý riêng" — giữ đúng hành vi thời "Thu mua chung".
        dept_only = dept_only or (service.dispatch_enabled()
                                  and not is_central_dept(db, pr.handler_dept_id))
        pr, n, blank_count = service.dispatch_pr(db, pid, user.id, allow_global_assignee=not dept_only,
                                                 audit_action="approved")
        _notify_assigned(db, pr, user, background_tasks)
    trigger_notification(
        db=db,
        event="pr_approved",
        doc_type="purchase_request",
        doc_code=pr.code,
        creator_id=pr.created_by or user.id,
        background_tasks=background_tasks,
        is_urgent=bool(pr.is_urgent),
        approve_note=pr.note or "",
        link=f"/purchase-requests/{pr.id}"
    )
    if not service.dispatch_enabled():
        msg = f"Đã duyệt — tự động phân bổ {n} dòng"
        if blank_count:
            msg += f" · còn {blank_count} dòng chưa có người phụ trách, hãy chọn tay"
        return success(_out(db, pr, user), msg)
    return success(_out(db, pr, user), "Đã duyệt — phiếu chờ thu mua duyệt điều phối")


@router.post("/{pid}/dispatch")
def dispatch_pr(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                user=Depends(require("purchase_request", "approve"))):
    """CR-034 — Duyệt lần 2 phía thu mua (điều phối): tự động phân bổ NSTM rồi mở khóa tạo ĐMH."""
    if not service.dispatch_enabled():
        raise HTTPException(400, "Bước duyệt điều phối đang TẮT — phiếu được phân bổ nhân sự "
                                 "ngay khi trưởng bộ phận duyệt.")
    # Cổng VAI TRÒ trước, cổng PHẠM VI sau: trưởng phòng không điều phối được thì câu trả
    # lời đúng là "không phải việc của bạn" (403), không phải "không có phiếu nào" (404).
    profile = get_perm_profile(db, user)
    if not _can_dispatch(profile):
        raise HTTPException(403, "Chỉ Quản lý / Admin thu mua mới duyệt điều phối được phiếu")
    _in_scope(db, pid, user, "approve")
    # bao-CR-414: quản lý thu mua CỦA PHÒNG (chỉ bậc `dept_proc`) điều phối thì chỉ tra bộ phân
    # công riêng của phòng, không rơi về bộ của phòng thu mua mặc định (bao-CR-524) — thiếu thì họ
    # chọn tay người trong phòng.
    dept_only = approves_only_in_dept_proc(profile, "purchase_request")
    pr, n, blank_count = service.dispatch_pr(db, pid, user.id, allow_global_assignee=not dept_only)
    # Thông báo "được phân công phụ trách" cho NSTM vừa được gán (trước CR-034 nằm ở bước duyệt)
    _notify_assigned(db, pr, user, background_tasks)
    msg = f"Đã duyệt điều phối — tự động phân bổ {n} dòng"
    if blank_count:
        msg += f" · còn {blank_count} dòng chưa có người phụ trách, hãy chọn tay"
    return success(_out(db, pr, user), msg)


@router.post("/{pid}/reject")
def reject_pr(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    """Từ chối YCMH kèm lý do và báo người tạo."""
    _in_scope(db, pid, user, "approve")
    pr = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(
        db=db,
        event="pr_rejected",
        doc_type="purchase_request",
        doc_code=pr.code,
        creator_id=pr.created_by or user.id,
        background_tasks=background_tasks,
        is_urgent=bool(pr.is_urgent),
        reason=data.reason or "",
        link=f"/purchase-requests/{pr.id}"
    )
    return success(_out(db, pr, user), "Đã từ chối")


# ═══════════════ PHƯƠNG ÁN trên dòng YCMH (bao-CR-310) ═══════════════
#
# Xử lý khảo sát làm THẲNG trên Yêu cầu mua hàng: NSTM gắn phương án (NCC + giá) lên
# từng dòng, chốt, rồi lên Đơn mua hàng. Yêu cầu báo giá không đụng tới.
#
# ⚠️ Mọi nhánh GHI đều đi qua `_open_line(...)` — nó gộp đủ BỐN cổng (phạm vi phiếu ·
# giai đoạn phiếu · dòng có thuộc phiếu không · dòng có được giao cho mình không).
# Gọi thiếu một cổng là mở đúng lỗ mà `_in_scope` sinh ra để bịt.


def _open_line(db: Session, pid: int, item_id: int, user, action: str):
    """Nạp (phiếu, dòng) cho một thao tác phương án, sau khi qua đủ các cổng."""
    pr = _in_scope(db, pid, user, action)
    option_service.ensure_stage(pr)
    item = option_service.get_item(db, pr, item_id)
    profile = get_perm_profile(db, user)
    option_service.ensure_own_line(item, profile.get("emp_code") or "",
                                   _see_all_items(profile, pr, user))
    return pr, item


@router.get("/{pid}/items/{item_id}/options")
def list_options(pid: int, item_id: int, db: Session = Depends(get_db),
                 user=Depends(require("purchase_request", "read"))):
    """Danh sách phương án (giá, nhà cung cấp) của một dòng YCMH."""
    pr = _in_scope(db, pid, user, "read")
    item = option_service.get_item(db, pr, item_id)
    # Đọc thì KHÔNG chặn theo giai đoạn phiếu (xem lại phiếu đã đóng vẫn phải thấy phương
    # án đã chốt), nhưng vẫn chặn theo dòng: màn hình giấu dòng của người khác thì API
    # cũng phải giấu, không thì gõ id dòng là đọc được giá NCC của phần việc không phải mình.
    profile = get_perm_profile(db, user)
    option_service.ensure_own_line(item, profile.get("emp_code") or "",
                                   _see_all_items(profile, pr, user))
    can_sup_read = user_has_permission(db, user, "supplier", "read")
    option_service.ensure_option_zero(db, pr, [item])   # sinh bù H.10.1, xem `_out`
    rows = option_service.options_of(db, item.id)
    return success({"items": [_out_option(db, o, can_sup_read) for o in rows]})


@router.get("/{pid}/items/{item_id}/available-survey-lines")
def available_survey_lines(pid: int, item_id: int, supplier_code: str = "", item_group: str = "",
                           search: str = "", page: int = 1, page_size: int = 8,
                           sort_by: str = "", sort_dir: str = "desc",
                           db: Session = Depends(get_db),
                           user=Depends(require("purchase_request", "write"))):
    """Kho phương án: các dòng khảo sát SẢN PHẨM đã duyệt, để NSTM nhặt vào dòng YCMH.

    Dùng lại nguyên hàm tra cứu của Yêu cầu báo giá — nó chỉ hỏi bảng khảo sát, không
    dính gì tới YCBG, nên chép sang đây là đẻ ra hai bản luật lọc phải giữ đồng bộ.
    Đòi `supplier.read` vì kết quả là danh sách NCC kèm giá.
    """
    from app.modules.survey_request import service as sr_service

    if not user_has_permission(db, user, "supplier", "read"):
        raise HTTPException(403, "Cần quyền xem nhà cung cấp để tra kho khảo sát")
    pr, item = _open_line(db, pid, item_id, user, "write")
    # Bỏ trống hết tiêu chí thì trả rỗng thay vì quét cả bảng khảo sát (cùng lối với YCBG).
    if not (supplier_code or (item_group or "").strip() or (search or "").strip()):
        return success({"items": [], "total": 0})
    rows, total = sr_service.available_survey_lines(
        db, supplier_code=supplier_code, item_group=item_group, search=search,
        page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir)
    return success({"items": _out_survey_lines(db, rows), "total": total})


@router.post("/{pid}/items/{item_id}/options")
def add_option_from_survey(pid: int, item_id: int, data: PROptionSurveyIn,
                           db: Session = Depends(get_db),
                           user=Depends(require("purchase_request", "write"))):
    """Gắn một phương án vào dòng YCMH lấy từ dòng phiếu khảo sát đã duyệt."""
    pr, item = _open_line(db, pid, item_id, user, "write")
    option_service.ensure_line_not_done(item)
    o = option_service.create_from_survey(db, pr, item, data.product_survey_line_id, user.id)
    return success(_out_option(db, o, user_has_permission(db, user, "supplier", "read")),
                   "Đã gắn phương án từ khảo sát", 201)


@router.post("/{pid}/items/{item_id}/options/manual")
def add_option_manual(pid: int, item_id: int, data: PROptionManualIn,
                      db: Session = Depends(get_db),
                      user=Depends(require("purchase_request", "write"))):
    """Phương án NSTM gõ tay — dùng khi giá biến động liên tục, kho khảo sát không kịp
    theo, NSTM phải đưa ra một mức hợp lý cho người yêu cầu chốt.

    Đòi `supplier.read` chứ KHÔNG phải `supplier.write`: đây là công cụ chính của NSTM,
    mà `pur_staff` chỉ có `supplier.read` — đòi `write` là khóa chết đúng người dùng nó.
    Và `supplier.write` là quyền sửa cả DANH MỤC nhà cung cấp, rộng hơn hẳn việc ghi một
    cái tên NCC vào phương án của một dòng. Xem hàng rào 2 cụm NCC ở Task 4.
    """
    if not user_has_permission(db, user, "supplier", "read"):
        raise HTTPException(403, "Cần quyền xem nhà cung cấp để nhập tay phương án")
    pr, item = _open_line(db, pid, item_id, user, "write")
    option_service.ensure_line_not_done(item)
    o = option_service.create_manual(db, pr, item, data, user.id)
    return success(_out_option(db, o, True), "Đã thêm phương án nhập tay", 201)


@router.patch("/{pid}/items/{item_id}/options/{oid}/supplier")
def set_option_supplier(pid: int, item_id: int, oid: int, data: PROptionSupplierIn,
                        db: Session = Depends(get_db),
                        user=Depends(require("purchase_request", "write"))):
    """H.10.4 — điền/sửa NCC trên PHƯƠNG ÁN 0 / nhập tay, dùng được cả SAU khi dòng đã
    chốt hoàn thành (đúng một khe nới, cố ý KHÔNG gọi `ensure_line_not_done`). Cổng
    `supplier.read` cùng lý lẽ với nhập tay phương án: `pur_staff` chỉ có read."""
    if not user_has_permission(db, user, "supplier", "read"):
        raise HTTPException(403, "Cần quyền xem nhà cung cấp để áp NCC vào phương án")
    pr, item = _open_line(db, pid, item_id, user, "write")
    o = option_service.set_option_supplier(db, pr, item, oid, data, user.id)
    return success(_out_option(db, o, True), "Đã áp nhà cung cấp vào phương án")


@router.patch("/{pid}/items/{item_id}/options/{oid}/details")
def update_option_details(pid: int, item_id: int, oid: int, data: PROptionDetailsIn,
                          db: Session = Depends(get_db),
                          user=Depends(require("purchase_request", "write"))):
    """bao-CR-583 — sửa thông tin PHƯƠNG ÁN 0 / NHẬP TAY (tên hàng, mã VTBB, NCC, giá, giao
    hàng…), ở màn xử lý lẫn màn chọn. Cùng cổng với `set_option_supplier`: write +
    supplier.read, đúng dòng mình phụ trách (hoặc người xem hết), dùng được cả sau khi dòng
    đã chốt (khe H.10.4)."""
    if not user_has_permission(db, user, "supplier", "read"):
        raise HTTPException(403, "Cần quyền xem nhà cung cấp để sửa phương án")
    pr, item = _open_line(db, pid, item_id, user, "write")
    o = option_service.update_option_details(db, pr, item, oid, data, user.id)
    return success(_out_option(db, o, True), f"Đã cập nhật {o.display_label}")


@router.post("/{pid}/items/{item_id}/options/{oid}/zero/reset")
def reset_option_zero(pid: int, item_id: int, oid: int, db: Session = Depends(get_db),
                      user=Depends(require("purchase_request", "write"))):
    """bao-CR-583 — "Khôi phục ban đầu": phương án 0 về đúng như dòng yêu cầu lúc sinh."""
    if not user_has_permission(db, user, "supplier", "read"):
        raise HTTPException(403, "Cần quyền xem nhà cung cấp để khôi phục phương án 0")
    pr, item = _open_line(db, pid, item_id, user, "write")
    o = option_service.reset_option_zero(db, pr, item, oid, user.id)
    return success(_out_option(db, o, True), "Đã khôi phục Phương án 0 về như dòng yêu cầu")


@router.post("/{pid}/options/assign-supplier")
def assign_supplier_bulk(pid: int, data: PRAssignSupplierIn, db: Session = Depends(get_db),
                         user=Depends(require("purchase_request", "write"))):
    """H.10.5 — "Áp 1 NCC cho nhiều dòng" trên màn chọn: tick các dòng đang thiếu NCC,
    chọn một NCC, áp một phát vào PHƯƠNG ÁN ĐANG CHỌN của từng dòng (giá sửa kèm theo
    dòng nếu cần). Cũng là khe H.10.4 nên không chặn theo `options_done`."""
    if not user_has_permission(db, user, "supplier", "read"):
        raise HTTPException(403, "Cần quyền xem nhà cung cấp để áp NCC vào phương án")
    pr = _in_scope(db, pid, user, "write")
    option_service.ensure_stage(pr)
    profile = get_perm_profile(db, user)
    n = option_service.assign_supplier_bulk(db, pr, data, user.id,
                                            profile.get("emp_code") or "",
                                            _see_all_items(profile, pr, user))
    return success({"updated": n}, f"Đã áp nhà cung cấp cho {n} dòng")


@router.patch("/{pid}/items/{item_id}/options/{oid}")
def update_option(pid: int, item_id: int, oid: int, data: PROptionUpdateIn,
                  db: Session = Depends(get_db),
                  user=Depends(require("purchase_request", "write"))):
    """Sửa một phương án của dòng YCMH; dòng đã chốt thì chỉ thu mua có quyền xem NCC mới sửa được giá."""
    pr, item = _open_line(db, pid, item_id, user, "write")
    if item.options_done:
        # H.10.4 — khe nới duy nhất sau chốt: sửa GIÁ của mọi phương án, dành cho
        # người có write + supplier.read (tầng thu mua của màn chọn). Trường khác
        # vẫn khóa — service từ chối cả gói nếu gửi kèm.
        if not user_has_permission(db, user, "supplier", "read"):
            raise HTTPException(403, "Dòng đã chốt hoàn thành — chỉ thu mua (có quyền "
                                     "xem NCC) mới sửa được giá sau chốt")
        o = option_service.update_option(db, item.id, oid, data, user.id, price_only=True)
    else:
        o = option_service.update_option(db, item.id, oid, data, user.id)
    return success(_out_option(db, o, user_has_permission(db, user, "supplier", "read")),
                   "Đã cập nhật phương án")


@router.delete("/{pid}/items/{item_id}/options/{oid}")
def delete_option(pid: int, item_id: int, oid: int, db: Session = Depends(get_db),
                  user=Depends(require("purchase_request", "write"))):
    """Gỡ một phương án khỏi dòng YCMH chưa chốt."""
    pr, item = _open_line(db, pid, item_id, user, "write")
    option_service.ensure_line_not_done(item)
    option_service.delete_option(db, pr, item.id, oid, user.id)
    return success(None, "Đã gỡ phương án")


@router.post("/{pid}/items/{item_id}/options/{oid}/choose")
def choose_option(pid: int, item_id: int, oid: int, db: Session = Depends(get_db),
                  user=Depends(require("purchase_request", "read"))):
    """Chốt phương án cho dòng — bấm lại đúng phương án đang chốt thì BỎ chốt.

    Cổng ở đây KHÁC các nhánh ghi còn lại: đòi `read` chứ không `write`, vì người
    chốt là NGƯỜI YÊU CẦU — họ thường chỉ có `read` trên phiếu sau khi phiếu đã duyệt.
    Ai được chốt thì `ensure_can_choose` quyết, xem docstring của nó.
    """
    pr, item = _open_line(db, pid, item_id, user, "read")
    option_service.ensure_can_choose(
        pr, user, user_has_permission(db, user, "purchase_request", "approve"))
    # bao-CR-570 (02/10/2026): BỎ cổng "NSTM phải chốt hoàn thành xử lý dòng" (đợt 3b). Đại ca
    # chốt làm như YCBG — phương án gắn tới đâu người yêu cầu thấy và chọn tới đó, vì người lập
    # đơn là chính nhân sự thu mua, không cần thêm một nhịp bàn giao.
    o = option_service.choose_option(db, pr, item, oid, user.id)
    msg = "Đã chốt phương án" if o.is_chosen else "Đã bỏ chốt phương án"
    return success(_out_option(db, o, user_has_permission(db, user, "supplier", "read")), msg)


@router.post("/{pid}/options/complete")
def complete_options(pid: int, data: PROptionCompleteIn, db: Session = Depends(get_db),
                     user=Depends(require("purchase_request", "write"))):
    """NSTM "Chốt hoàn thành xử lý" phần của mình trên phiếu (đợt 3b, khuôn YCBG
    `complete_sr`): mọi dòng mình phụ trách phải có phương án hoặc được tick chốt
    rỗng. Chốt theo NGƯỜI GỌI — phiếu nhiều NSTM thì mỗi người chốt phần mình."""
    pr = _in_scope(db, pid, user, "write")
    option_service.ensure_stage(pr)
    profile = get_perm_profile(db, user)
    done, empty, all_done = option_service.complete_options(
        db, pr, user, profile.get("emp_code") or "",
        _see_all_items(profile, pr, user), data.empty_item_ids)
    msg = "Đã chốt hoàn thành xử lý phương án"
    if all_done:
        msg += " — cả phiếu đã xử lý xong"
        # bao-CR-419: ĐỢI XONG CẢ PHIẾU mới báo người yêu cầu. Phiếu nhiều NSTM thì
        # người chốt cuối cùng mới làm nổ chuông, mỗi phiếu đúng một cái.
        # Đang TẮT — xem `option_service.OPTION_BELLS_ENABLED`; lời gọi giữ nguyên
        # để lúc mở lại chỉ phải đổi đúng hằng đó.
        option_service.notify_options_ready(db, pr, user.id)
    return success({"done": done, "empty": empty, "all_done": all_done}, msg)


@router.post("/{pid}/options/choice-complete")
def complete_option_choice(pid: int, db: Session = Depends(get_db),
                           user=Depends(require("purchase_request", "read"))):
    """bao-CR-419 — NGƯỜI YÊU CẦU "Chốt xong lựa chọn" cho cả phiếu, rồi chuông báo
    NSTM của từng dòng vào gom đơn.

    Cổng `read` + `ensure_can_choose` y hệt nút chốt phương án: đây là nút kết của
    chính việc chốt đó, ai chốt được phương án thì chốt được phần lựa chọn.
    """
    pr = _in_scope(db, pid, user, "read")
    option_service.ensure_stage(pr)
    option_service.ensure_can_choose(
        pr, user, user_has_permission(db, user, "purchase_request", "approve"))
    lines = option_service.mark_choice_done(db, pr, user)
    # Chuông đang TẮT — xem `option_service.OPTION_BELLS_ENABLED`. Mốc chốt vẫn ghi,
    # nên thu mua vẫn nhìn thấy phiếu đã chốt xong ở màn chi tiết.
    option_service.notify_options_chosen(db, pr, user.id)
    return success({"options_chosen_at": pr.options_chosen_at, "lines": lines},
                   "Đã chốt xong lựa chọn — thu mua sẽ lập đơn theo phương án đã chọn")


@router.post("/{pid}/items/{item_id}/options/reopen")
def reopen_options_line(pid: int, item_id: int, db: Session = Depends(get_db),
                        user=Depends(require("purchase_request", "read"))):
    """Người yêu cầu / quản lý MỞ LẠI một dòng đã chốt hoàn thành để NSTM sửa tiếp
    (khuôn "Cần khảo sát lại" của YCBG). Đòi `read` cùng lý do với `choose`: người
    yêu cầu thường chỉ còn quyền đọc sau khi phiếu duyệt; ai được bấm do
    `ensure_can_choose` quyết — mở lại là mặt trái của quyền chọn."""
    pr, item = _open_line(db, pid, item_id, user, "read")
    option_service.ensure_can_choose(
        pr, user, user_has_permission(db, user, "purchase_request", "approve"))
    option_service.reopen_line(db, pr, item, user)
    return success({"item_id": item.id, "options_done": False, "no_option": False},
                   "Đã mở lại dòng cho NSTM xử lý tiếp")


@router.post("/{pid}/options/generate-orders")
def generate_orders_from_options(pid: int, db: Session = Depends(get_db),
                                 user=Depends(require("purchase_order", "create"))):
    """H.10.6 — "Tạo đơn mua hàng theo phương án": gom phương án ĐANG CHỌN của từng
    dòng theo NCC thành các ĐMH NHÁP một lượt; dòng thiếu NCC gom vào một đơn riêng.

    Cổng theo `purchase_order:create` chứ không theo quyền phiếu — nút này LẬP ĐƠN,
    ai lập được đơn tay thì bấm được nút gom. Vẫn phải THẤY phiếu: `_in_scope` đọc
    theo phạm vi `purchase_request.read` của người gọi (ngoài phạm vi -> 404)."""
    pr = _in_scope(db, pid, user, "read")
    option_service.ensure_stage(pr)
    out = option_service.generate_purchase_orders(db, pr, user.id)
    n = len(out["orders"])
    return success(out, f"Đã tạo {n} đơn mua hàng nháp theo phương án")
