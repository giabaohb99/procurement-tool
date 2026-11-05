from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.bulk_delete import ensure_all_draft
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.notification.service import trigger_notification

from . import service
#  bao-CR-711: dựng kết quả ở `serializer.py`, truy vấn ở `service.py`. Controller chỉ còn
#  nhận · gác quyền + phạm vi · gọi · trả.
from .model import POItem, PurchaseOrder
from .schema import (CostLinesFinalizeIn, CostStageAdvanceIn, CostStageReopenIn, DocumentStatusIn,
                     ItemProgressIn, POCreate, POUpdate, RejectIn)
from .serializer import _out, _out_lines, _out_list, _out_print, _stage_label

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase_order"])


def _in_scope(db: Session, pid: int, user, action: str) -> PurchaseOrder:
    """Nạp ĐMH theo id NHƯNG chỉ khi nó nằm trong phạm vi `action` của người gọi.

    `require(entity, action)` chỉ trả lời "vai trò này được làm hành động đó không"; nó
    KHÔNG biết đơn thuộc pháp nhân nào. Trước bản vá này mọi nhánh GHI/IN dừng ở
    `service.get_po` = `db.get` trần, nên đổi đuôi URL sang `/print` là vòng qua được đúng
    bộ lọc mà `GET /{pid}` ngay bên trên đã đặt.

    `action` PHẢI khớp `require(...)` của route gọi (in → `print`, duyệt → `approve`, …);
    lấy `read` cho tất cả là mượn phạm vi rộng hơn phạm vi thật của hành động.

    404 cho cả "không có" lẫn "ngoài phạm vi" — cùng mã lỗi `service.get_po` vẫn trả, nên
    người ngoài phạm vi không suy ra được đơn có thật hay không.
    """
    po = apply_scope(service.query_by_id(db, pid),
                     PurchaseOrder, "purchase_order", user,
                     get_perm_profile(db, user), action).first()
    if not po:
        raise HTTPException(404, "Không tìm thấy đơn mua hàng")
    return po


def _require_awaiting_approval(db: Session, pid: int, action_label: str) -> None:
    """CR-073: duyệt / từ chối / trả về chỉ hợp lệ khi đơn đang CHỜ DUYỆT.

    Trước đây các endpoint này gọi thẳng `service.set_status`, mà hàm đó chỉ GÁN trạng thái
    chứ không kiểm gì — nên gọi API trực tiếp là chuyển đơn sang trạng thái bất kỳ, kể cả
    ngược chiều (đơn đã Hoàn thành vẫn "duyệt" lại được). Giao diện có ẩn nút, nhưng ẩn nút
    không phải là chốt chặn.
    """
    if service.get_po(db, pid).status != "submitted":
        raise HTTPException(400, f"Chỉ {action_label} được đơn đang ở trạng thái Chờ duyệt")


def _list_query(request: Request, db: Session, user):
    """Bộ lọc + phạm vi của màn danh sách — dùng chung cho danh sách và xuất Excel (CR-068)."""
    q = service.build_list_query(db, request)
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    return apply_sort_from_request(q, PurchaseOrder, request)


@router.get("")
def list_po(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
            user=Depends(require("purchase_order", "read"))):
    """Danh sách đơn mua hàng (ĐMH) trong phạm vi được xem, có lọc và phân trang."""
    q = _list_query(request, db, user)
    total, items = service.list_po(db, q, pg)
    return success({"total": total, "items": _out_list(db, items)})


@router.get("/meta/approver-candidates")
def approver_candidates_meta(department: str = "", department_id: int = 0, company_id: int = 0,
                             handler_dept_id: int = 0, head_of_dept_id: int = 0, db: Session = Depends(get_db),
                             user=Depends(require("purchase_order", "read"))):
    """bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt".

    Khai TRƯỚC `/{pid}` kẻo FastAPI nuốt "meta" thành id.
    """
    #  bao-CR-552: + Trưởng bộ phận, bỏ tài khoản Quản trị hệ thống (luật nằm ở core).
    from app.core.approver_candidates import draft_fields, list_candidates_for_draft
    fields = draft_fields(db, user, department, department_id, company_id, handler_dept_id)
    return success({"items": list_candidates_for_draft(db, PurchaseOrder, "purchase_order", fields,
                                                       head_of_dept_id)})


@router.get("/{pid}/approver-candidates")
def approver_candidates_(pid: int, db: Session = Depends(get_db),
                         user=Depends(require("purchase_order", "read"))):
    """bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve)."""
    from app.core.approver_candidates import list_candidates_for_row
    row = _in_scope(db, pid, user, "read")
    return success({"items": list_candidates_for_row(db, PurchaseOrder, "purchase_order", row)})   # bao-CR-552


@router.get("/export/xlsx")
def export_xlsx(request: Request, ids: str = "", cols: str = "",
                db: Session = Depends(get_db), user=Depends(require("purchase_order", "export"))):
    """CR-068 — xuất Excel danh sách ĐMH, cột dòng hàng lấy đúng bộ cột màn Tiến độ mua hàng
    (một hàng = một lần giao).

    `ids` = đơn người dùng tick chọn; rỗng thì theo bộ lọc đang đặt. `cols` = cột đang hiện.
    Cũng như `/lines`, phải khai báo TRƯỚC `/{pid}`.
    """
    from app.core.auth import user_has_permission
    from app.core.export_xlsx import check_row_limit, parse_ids, pick_columns, xlsx_response
    from . import export as ex

    q = _list_query(request, db, user)
    id_list = parse_ids(ids)
    if id_list:
        q = q.filter(PurchaseOrder.id.in_(id_list))
    pos = q.order_by(PurchaseOrder.id.desc()).all()
    check_row_limit(len(pos))
    show_supplier = user_has_permission(db, user, "supplier", "read")
    rows = ex.build_rows(db, pos, show_supplier)
    check_row_limit(len(rows))
    columns = pick_columns(ex.HEADER_COLS, cols) + ex.line_columns(show_supplier)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)


# PHẢI khai báo TRƯỚC `/{pid}`, nếu không "lines" sẽ rơi vào route đó và lỗi ép kiểu int.
@router.get("/lines")
def list_po_lines(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("purchase_order", "read"))):
    """Danh sách DÒNG HÀNG của các đơn mua hàng — dùng cho trang chi tiết Kho.

    `warehouse_code`: lấy dòng có "Kho nhận mặc định" là kho này, HOẶC có lần giao về kho này
    (lần giao đổi kho so với mặc định vẫn là hàng thực về kho → không được bỏ sót).
    `qty_received_here` = SL đã nhận riêng ở kho đang xem (khác qty_received là tổng mọi kho):
    tổng SL nhận của các lần giao ghi rõ kho này, cộng phần đã nhận CHƯA gắn kho nào —
    phần đó quy về kho mặc định của dòng (dữ liệu nhập lịch sử chỉ có SL nhận trên dòng,
    không tách lần giao, nếu bỏ qua thì kho nào cũng hiện 0).
    """
    wh = (request.query_params.get("warehouse_code") or "").strip()
    q = service.build_line_query(db, request, wh)
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))

    total = q.count()
    rows = (q.order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.id.desc(), POItem.id.asc())
            .offset(pg["offset"]).limit(pg["limit"]).all())

    # SL nhận theo lần giao, gom theo dòng: (nhận tại kho đang xem, nhận đã gắn kho bất kỳ)
    recv = service.received_by_warehouse(db, [it.id for _, it in rows], wh) if (wh and rows) else {}
    return success({"total": total, "items": _out_lines(rows, recv, wh)})


@router.get("/{pid}")
def get_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "read"))):
    """Chi tiết một ĐMH."""
    scoped = apply_scope(service.query_by_id(db, pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, service.get_po(db, pid)))


@router.get("/{pid}/print")
def print_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "print"))):
    """Dữ liệu in một ĐMH (người ký, công ty, dòng hàng)."""
    po = _in_scope(db, pid, user, "print")
    return success(_out_print(db, po))


@router.get("/{pid}/purchase-request")
def get_po_purchase_request(pid: int, db: Session = Depends(get_db),
                            user=Depends(require("purchase_order", "print"))):
    """Phiếu YCMH nguồn của đơn, đã cắt còn đúng các dòng hàng có trên đơn — bao-CR-314.

    Cổng đặt ở ĐƠN MUA HÀNG chứ không ở phiếu yêu cầu, cố ý: một phiếu YCMH chia cho nhiều
    NSTM phụ trách (`tab_purchase_request_item.assignee`) nên phạm vi dữ liệu của người cầm
    đơn thường KHÔNG với tới cả phiếu — gọi thẳng `/api/purchase-requests/{id}` là 403 đúng
    những người cần in. Ai mở được đơn (quyền `print` + đơn nằm trong phạm vi) thì in được
    phần phiếu tương ứng, và không thấy hàng của người khác vì danh sách đã cắt theo mã hàng
    trên đơn. Luật che NCC cụm `pur` (Task 4) giữ nguyên vì vẫn đi qua `_out` của YCMH.
    """
    scoped = apply_scope(service.query_by_id(db, pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    po = service.get_po(db, pid)
    pr_code = (po.pr_code or "").strip()
    if not pr_code:
        raise HTTPException(404, "Đơn mua hàng này không gắn phiếu yêu cầu mua hàng")
    #  Nhập trong hàm: serializer YCMH nạp cả cụm model/service của YCMH, kéo lên đầu tệp là
    #  buộc hai phân hệ phụ thuộc vòng nhau lúc `app.main` dựng router (bao-CR-711: `_out` đã
    #  dời từ `purchase_request.controller` sang `purchase_request.serializer`).
    from app.modules.purchase_request.serializer import _out as pr_out
    pr = service.live_pr_by_code(db, pr_code)
    if not pr:
        raise HTTPException(404, f"Không tìm thấy phiếu yêu cầu mua hàng {pr_code}")
    data = service.pr_items_for_po(pr_out(db, pr, user), service.items_of(db, po.id))
    data["po_code"] = po.code
    return success(data)


@router.post("")
def create_po(data: POCreate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    """Tạo ĐMH mới ở trạng thái Nháp."""
    return success(_out(db, service.create_po(db, data, user.id)), "Đã tạo đơn mua hàng", 201)


@router.post("/{pid}/copy")
def copy_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    """Nhân bản một ĐMH thành đơn Nháp mới."""
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.post("/{pid}/clone")
def clone_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    """Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS)."""
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.patch("/{pid}")
def update_po(pid: int, data: POUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "write"))):
    """Sửa ĐMH."""
    _in_scope(db, pid, user, "write")
    return success(_out(db, service.update_po(db, pid, data, user.id)), "Đã cập nhật")


@router.patch("/{pid}/document-status")
def set_document_status(pid: int, body: DocumentStatusIn, db: Session = Depends(get_db),
                        user=Depends(require("purchase_order", "write"))):
    """Task 10b: cập nhật tay trạng thái hồ sơ chứng từ (cho phép cả khi đơn đã hoàn thành)."""
    _in_scope(db, pid, user, "write")
    po = service.set_document_status(db, pid, body.document_status, user.id)
    return success(_out(db, po), "Đã cập nhật hồ sơ chứng từ")


@router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    """Xóa một ĐMH."""
    _in_scope(db, pid, user, "delete")
    service.delete_po(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_pos(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    """Xóa nhiều ĐMH theo danh sách id trong phạm vi được xóa."""
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    # Lọc phạm vi TRƯỚC vòng lặp (khuôn của `contract/controller.py`) — lặp theo id trần
    # thì gửi đại một dãy số là xóa được đơn Nháp của pháp nhân khác.
    rows = apply_scope(service.query_by_ids(db, id_list),
                       PurchaseOrder, "purchase_order", user,
                       get_perm_profile(db, user), "delete").all()
    if not rows:
        raise HTTPException(403, "Ngoài phạm vi được phép xóa")
    #  bao-CR-547: kiểm CẢ LÔ trước khi xóa đơn nào — chỉ đơn Nháp (đại ca chốt 01/10/2026).
    ensure_all_draft(rows, "đơn mua hàng")
    for pid in [r.id for r in rows]:
        try:
            service.delete_po(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa đơn ID {pid}: {str(e)}") from e
    # Báo đúng số ĐÃ xóa, không báo số đã gửi lên.
    return success(None, f"Đã xóa {len(rows)} bản ghi")


@router.post("/{pid}/submit")
def submit_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    # CR-073: trước đây gọi thẳng set_status nên gửi duyệt được đơn thiếu NCC, thiếu dòng
    # hàng, hoặc đơn đang ở trạng thái bất kỳ. set_status chỉ GÁN trạng thái, không kiểm gì —
    # chốt phải đặt ở đây (đồng bộ cách làm của submit_pr).
    """Gửi duyệt ĐMH ở trạng thái Nháp hoặc Bị trả lại; báo thiếu nhà cung cấp hay dòng hàng."""
    po = _in_scope(db, pid, user, "write")
    if po.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ gửi duyệt được đơn ở trạng thái Nháp hoặc Bị trả lại")
    missing = []
    if not (po.supplier_code or "").strip():
        missing.append("nhà cung cấp")
    items = service.items_of(db, pid)
    if not items:
        missing.append("ít nhất một dòng hàng")
    if missing:
        raise HTTPException(400, f"Chưa gửi duyệt được — đơn còn thiếu {' và '.join(missing)}.")
    # CR-095: từng dòng hàng phải điền đủ bộ trường bắt buộc. Nêu ĐÍCH DANH dòng nào
    # thiếu ô nào — báo chung chung thì người lập phải mở lần lượt từng dòng để dò.
    line_errors = [f"dòng {i} ({it.product_code or 'chưa có mã hàng'}): {', '.join(t)}"
                for i, it in enumerate(items, 1) if (t := service.missing_line_fields(it))]
    if line_errors:
        raise HTTPException(400, "Chưa gửi duyệt được — còn thiếu " + "; ".join(line_errors) + ".")
    po = service.set_status(db, pid, "submitted", user.id)
    trigger_notification(db=db, event="po_submitted", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         is_urgent=bool(po.is_urgent), link=f"/purchase-orders/{po.id}",
                         doc_id=po.id,   # duoc-CR-662: lọc người duyệt theo phạm vi của chính đơn
                         # bao-CR-499: người được CHỌN ở ô "Trưởng phòng phê duyệt" cũng nhận báo duyệt.
                         extra_employee_ids=[po.approver_employee_id] if po.approver_employee_id else None)
    return success(_out(db, po), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
               user=Depends(require("purchase_order", "approve"))):
    """Duyệt ĐMH đang chờ duyệt và ghi người duyệt lên bản in."""
    _in_scope(db, pid, user, "approve")
    _require_awaiting_approval(db, pid, "duyệt")
    po = service.set_status(db, pid, "approved", user.id)
    # bao-CR-490: ghi nhân sự vừa duyệt vào "Trưởng phòng phê duyệt".
    from app.core.print_signers import stamp_approver
    stamp_approver(db, po, user.id)
    db.commit()
    trigger_notification(db=db, event="po_approved", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã duyệt")


@router.post("/{pid}/unapprove")
def unapprove_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
                 user=Depends(require("purchase_order", "approve"))):
    """Hủy duyệt — đơn về Nháp để sửa rồi gửi duyệt lại (CR-108, phiếu hỗ trợ TK19082604).

    Chỉ người có quyền DUYỆT được bấm: sau khi duyệt, đơn là cam kết đã ký với NCC, mở
    lại để sửa là quyết định của trưởng phòng chứ không phải của người lập đơn.
    """
    _in_scope(db, pid, user, "approve")
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy duyệt")
    po = service.unapprove_po(db, pid, user.id, data.reason.strip())
    # bao-CR-499: KHÔNG xóa cột người duyệt nữa — từ nay nó là "người được chọn / đã duyệt"; về Nháp
    # thì người vừa duyệt vẫn là người được chọn cho lần gửi duyệt sau, người lập đổi được.
    db.commit()
    return success(_out(db, po), "Đã hủy duyệt — đơn về Nháp")


@router.post("/{pid}/reject")
def reject_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Từ chối = KHÓA đơn (Đã từ chối) — không sửa/gửi lại được, phải Nhân bản thành đơn mới.
    """Từ chối ĐMH đang chờ duyệt (đơn chuyển Đã hủy) kèm lý do, báo người tạo."""
    _in_scope(db, pid, user, "approve")
    _require_awaiting_approval(db, pid, "từ chối")
    po = service.set_status(db, pid, "cancelled", user.id, data.reason)
    trigger_notification(db=db, event="po_rejected", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã từ chối")


@router.post("/{pid}/return")
def return_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Trả về = Bị trả lại — người tạo SỬA & GỬI DUYỆT LẠI được (đồng bộ YCMH).
    """Trả ĐMH đang chờ duyệt về người tạo để sửa, kèm lý do."""
    _in_scope(db, pid, user, "approve")
    _require_awaiting_approval(db, pid, "trả về")
    po = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="po_returned", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã trả đơn về (Bị trả lại)")


@router.post("/{pid}/cancel")
def cancel_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "cancel"))):
    """Hủy ĐMH kèm lý do bắt buộc; đơn đã Hủy hay Hoàn thành thì không hủy lại."""
    _in_scope(db, pid, user, "cancel")
    # Hủy phải có lý do
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy đơn")
    # CR-073: đơn đã ở điểm cuối thì không hủy lại được nữa
    if service.get_po(db, pid).status in ("cancelled", "completed"):
        raise HTTPException(400, "Đơn đã Hủy/Hoàn thành — không hủy lại được")
    # Có sản phẩm nào đã Hoàn thành → KHÔNG cho hủy
    if service.has_completed_item(db, pid):
        raise HTTPException(400, "Đơn có sản phẩm đã Hoàn thành — không thể hủy")
    return success(_out(db, service.set_status(db, pid, "cancelled", user.id, data.reason)), "Đã hủy đơn")


@router.post("/{pid}/complete")
def complete_po(pid: int, db: Session = Depends(get_db),
                user=Depends(require("purchase_order", "write"))):
    # Chỉ cho Hoàn thành ĐƠN khi MỌI dòng đã ở điểm cuối (`completed`/`cancelled`) —
    # giữ header nhất quán với tiến độ dòng (tránh đơn đã hoàn thành mà dòng chưa nhập
    # Số HĐ / chưa thanh toán, dẫn tới không tạo được Yêu cầu thanh toán).
    """Chuyển ĐMH sang Hoàn thành khi mọi dòng đã xong hoặc đã hủy."""
    _in_scope(db, pid, user, "write")
    lines = service.items_unsorted_of(db, pid)
    pending = [it for it in lines
               if (it.progress_status or "") not in (service.PROG_COMPLETED, service.PROG_CANCELLED)]
    if pending:
        names = ", ".join((it.product_name or it.product_code or f"#{it.id}") for it in pending[:5])
        more = f" (+{len(pending) - 5} dòng nữa)" if len(pending) > 5 else ""
        raise HTTPException(
            400,
            f"Còn {len(pending)} dòng chưa Hoàn thành/Hủy: {names}{more}. "
            "Hãy hoàn tất tiến độ từng dòng (nhập Số HĐ → tạo & chi Yêu cầu thanh toán → Hoàn thành dòng) "
            "trước khi hoàn thành đơn.")
    po = service.get_po(db, pid)
    # bao-CR-453: đơn có dòng chi phí thu mua thì phải ở Quyết toán mới đóng được.
    service.block_complete_not_final_costs(db, po)
    # bao-CR-319: đơn nhập khẩu còn phải trả đủ chi phí lô hàng (cước, thuế, phí) mới được đóng.
    service.block_complete_unpaid_import_costs(db, po)
    return success(_out(db, service.set_status(db, pid, "completed", user.id)), "Đã hoàn thành đơn")


@router.post("/{pid}/reopen")
def reopen_po(pid: int, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    """Mở lại ĐMH đã hoàn thành để xử lý tiếp."""
    _in_scope(db, pid, user, "write")
    po = service.reopen_po(db, pid, user.id)
    return success(_out(db, po), "Đã mở lại đơn để xử lý tiếp")


@router.post("/{pid}/items/{item_id}/progress")
def set_item_progress(pid: int, item_id: int, data: ItemProgressIn, db: Session = Depends(get_db),
                      user=Depends(require("purchase_order", "write"))):
    """Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH."""
    _in_scope(db, pid, user, "write")
    return success(_out(db, service.set_item_progress(db, pid, item_id, data.status, data.reason, user.id)),
                   "Đã cập nhật trạng thái dòng")


# ───────────────────────── Giai đoạn chi phí thu mua (bao-CR-453) ─────────────────────────
def _require_editable_costs(po: PurchaseOrder) -> None:
    """Đơn đã Hủy / Từ chối / Hoàn thành thì bộ chi phí đóng theo — không chốt, không mở lại."""
    if (po.status or "") in ("cancelled", "rejected", "completed"):
        raise HTTPException(400, "Đơn đã đóng, không đổi giai đoạn chi phí thu mua được nữa")


@router.post("/{pid}/cost-stage/advance")
def advance_cost_stage(pid: int, data: CostStageAdvanceIn, db: Session = Depends(get_db),
                       user=Depends(require("purchase_order", "write"))):
    """Chốt Tạm tính / Quyết toán. Có `import_costs` thì lưu bảng chi phí trước rồi mới chốt."""
    po = _in_scope(db, pid, user, "write")
    _require_editable_costs(po)
    if data.import_costs is not None:
        service.update_po(db, pid, POUpdate(import_costs=data.import_costs), user.id)
        po = service.get_po(db, pid)
    service.advance_cost_stage(db, po, data.target, user.id)
    return success(_out(db, service.get_po(db, pid)),
                   f"Đã chốt {_stage_label(data.target)} chi phí thu mua")


@router.post("/{pid}/cost-stage/reopen")
def reopen_cost_stage(pid: int, data: CostStageReopenIn, db: Session = Depends(get_db),
                      user=Depends(require("purchase_order", "approve"))):
    """Mở lại bộ chi phí về giai đoạn thấp hơn — cần quyền duyệt + lý do."""
    po = _in_scope(db, pid, user, "approve")
    _require_editable_costs(po)
    service.reopen_cost_stage(db, po, data.target, data.reason, user.id)
    return success(_out(db, service.get_po(db, pid)),
                   f"Đã mở lại chi phí thu mua về {_stage_label(data.target)}")


@router.post("/{pid}/costs/{cost_id}/finalize")
def finalize_cost_line(pid: int, cost_id: int, db: Session = Depends(get_db),
                       user=Depends(require("purchase_order", "write"))):
    """Quyết toán RIÊNG một dòng chi phí (hóa đơn khoản đó về trước)."""
    po = _in_scope(db, pid, user, "write")
    _require_editable_costs(po)
    service.finalize_cost_line(db, po, cost_id, user.id)
    return success(_out(db, service.get_po(db, pid)), "Đã quyết toán dòng chi phí")


@router.post("/{pid}/cost-lines/finalize")
def finalize_cost_lines(pid: int, data: CostLinesFinalizeIn, db: Session = Depends(get_db),
                        user=Depends(require("purchase_order", "write"))):
    """bao-CR-469 — Quyết toán NHIỀU dòng chi phí một lượt (tick chọn, hoặc chốt hết).

    Đường riêng `cost-lines` chứ không nối thêm vào `/costs/...` để không đứng cạnh đường có
    tham số id — "finalize" rơi vào chỗ chờ một con số thì lỗi trả về nói chuyện kiểu dữ liệu,
    không ai đoán ra là gọi nhầm đường.
    """
    po = _in_scope(db, pid, user, "write")
    _require_editable_costs(po)
    # bao-CR-476: có bảng đang gõ thì lưu trước rồi mới chốt, để chốt đúng số người dùng thấy.
    if data.import_costs is not None:
        service.update_po(db, pid, POUpdate(import_costs=data.import_costs), user.id)
        po = service.get_po(db, pid)
    rows = service.finalize_cost_lines(db, po, data.cost_ids, user.id)
    # bao-CR-478 — dòng chưa có Dự toán bị bỏ qua: nói ra, đừng để người dùng tưởng đã chốt hết.
    skipped = service.count_costs_missing_estimate(db, po, data.cost_ids)
    note = f" — bỏ qua {skipped} dòng chưa có Dự toán" if skipped else ""
    return success(_out(db, service.get_po(db, pid)),
                   f"Đã quyết toán {len(rows)} dòng chi phí{note}")


@router.post("/{pid}/costs/{cost_id}/reopen")
def reopen_cost_line(pid: int, cost_id: int, data: RejectIn, db: Session = Depends(get_db),
                     user=Depends(require("purchase_order", "approve"))):
    """Mở lại một dòng đã quyết toán riêng — cần quyền duyệt + lý do."""
    po = _in_scope(db, pid, user, "approve")
    _require_editable_costs(po)
    service.reopen_cost_line(db, po, cost_id, data.reason, user.id)
    return success(_out(db, service.get_po(db, pid)), "Đã mở lại dòng chi phí")


