from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require, user_has_permission
from app.core.scoping import apply_scope, approves_only_in_dept_proc, holds_handling_dept
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, apply_sort_from_request, pagination
from app.core.ref_filter import apply_ref_filters
from app.core.database import get_db
from app.core.response import success
from app.core.status_codes import PR_LINE_STATUS
from app.modules.notification.service import trigger_notification

from sqlalchemy import and_ as sa_and, func, or_ as sa_or, select
from . import option_service, service
from .constants import PR_OPTION_SOURCE_LABELS
from .model import (STATUS_AFTER_APPROVE, STATUS_AFTER_DISPATCH,
                    PurchaseRequest, PurchaseRequestItem)
from .schema import (ApproveIn, AssignIn, ItemStatusIn, PRAssignSupplierIn, PRCreate,
                     PROptionCompleteIn, PROptionManualIn, PROptionSupplierIn,
                     PROptionSurveyIn, PROptionUpdateIn, PRUpdate,
                     ReasonIn, RejectIn, TransferDeptIn, UrgentIn)

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase_request"])

HEADER_COLS = ["id", "code", "company_id", "requester", "requester_id", "requester_position",
               "department_id", "handler_dept_id", "department", "head_of_dept", "head_of_dept_id",
               # bao-CR-316: `received_date` CHỈ có ở đây (đọc ra), cố ý KHÔNG nằm trong
               # PRCreate/PRUpdate — Ngày tiếp nhận do `dispatch_pr` điền, không ai sửa tay.
               "purpose", "request_date", "received_date", "need_date",
               "status", "is_urgent", "vat_rate", "assignee_id", "note",
               "show_code_on_print", "suggested_supplier", "suggested_supplier_tax_code",
               "suggested_supplier_contact", "quote_filename", "quote_file_url"]


_SUPPLIER_FIELDS = ("suggested_supplier", "suggested_supplier_tax_code", "suggested_supplier_contact")


def _blank_supplier(d: dict) -> None:
    """Task 5: che NCC đề xuất khi user không có quyền supplier.read."""
    for k in _SUPPLIER_FIELDS:
        d[k] = ""


def _out_option(db: Session, o, can_sup_read: bool) -> dict:
    """Một phương án ra API (bao-CR-310).

    Cụm NCC (`supplier_*`, `snap_internal_code`, `supplier_survey_id`) chỉ trả cho người
    có `supplier.read` — đúng luật cụm `pur` của Task 4. Phần thông số + GIÁ thì người
    yêu cầu ĐƯỢC thấy, giống hệt thẻ phương án bên Yêu cầu báo giá: họ cần so giá để
    chốt, chỉ không được biết giá đó của ai.
    """
    d = {
        "id": o.id, "pr_item_id": o.pr_item_id,
        "source": int(o.source or 0),
        "source_label": PR_OPTION_SOURCE_LABELS.get(int(o.source or 0), ""),
        "product_survey_line_id": o.product_survey_line_id,
        "public_id": o.public_id, "display_label": o.display_label,
        "is_chosen": bool(o.is_chosen),
        "snap_product_name": o.snap_product_name, "snap_spec": o.snap_spec,
        "snap_origin": o.snap_origin, "snap_quote_unit": o.snap_quote_unit,
        "snap_moq": float(o.snap_moq or 0),
        "snap_price_by_volume": float(o.snap_price_by_volume or 0),
        "snap_volume_range": o.snap_volume_range,
        "snap_vat": float(o.snap_vat or 0),
        "snap_delivery_time": o.snap_delivery_time,
        "snap_delivery_place": o.snap_delivery_place,
        "snap_shipping_cost": float(o.snap_shipping_cost or 0),
        "snap_sample_ready": bool(o.snap_sample_ready),
        "snap_lab_result": o.snap_lab_result,
        "nstm_note": o.nstm_note,
        "created_at": o.created_at,
    }
    if can_sup_read:
        d.update({"supplier_code": o.supplier_code, "supplier_name": o.supplier_name,
                  "supplier_survey_id": o.supplier_survey_id,
                  "snap_internal_code": o.snap_internal_code})
    else:
        d.update({"supplier_code": "", "supplier_name": "", "supplier_survey_id": 0,
                  "snap_internal_code": ""})
    return d


def _can_dispatch(profile: dict) -> bool:
    """CR-034 — ai được ĐIỀU PHỐI (duyệt lần 2). Điều kiện: có quyền `approve` trên YCMH VỚI
    phạm vi thu mua/toàn bộ ('proc'/'all'). Trưởng phòng có approve nhưng phạm vi 'dept' →
    chỉ duyệt lần 1, không điều phối. Cùng lối đọc grant với `_see_all_items`."""
    # bao-CR-414: quản lý thu mua CỦA PHÒNG (bậc `dept_proc`) cũng điều phối được — phạm vi
    # đã khoanh phiếu về đúng phòng mình ở `_in_scope`.
    for g in profile.get("grants", []):
        p = g["perms"].get("purchase_request")
        if p and p.get("approve") and p.get("scope") in ("proc", "dept_proc", "all"):
            return True
    return False


def _scope_ok(db: Session, user, pid: int, action: str) -> bool:
    """Phiếu này có nằm trong phạm vi `action` của người gọi không (chỉ hỏi, không nạp).

    Tách khỏi `_in_scope` cho những chỗ đã cầm sẵn bản ghi hoặc cần trả True/False
    (cờ `can_approve` trên phiếu, cổng trả về/từ chối).
    """
    return apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                       PurchaseRequest, "purchase_request", user,
                       get_perm_profile(db, user), action).first() is not None


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
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid,
                                                      PurchaseRequest.is_deleted == False),
                     PurchaseRequest, "purchase_request", user,
                     get_perm_profile(db, user), action).first()
    if not pr:
        raise HTTPException(404, "Không tìm thấy yêu cầu mua")
    return pr


def _in_approve_scope(db: Session, user, pid: int) -> bool:
    """Phiếu có nằm trong phạm vi DUYỆT của người này không.
    CR-034: Admin thu mua có `approve` phạm vi 'proc' (để duyệt điều phối) — phạm vi đó không
    thấy phiếu 'submitted' nên họ tự động bị loại khỏi bước duyệt 1, không cần luật riêng.

    ⚠️ Trước bản vá này hàm KHÔNG truyền `action`, tức mượn phạm vi `read`. Sai cả hai
    chiều trên cùng một dòng: cấu hình "xem toàn công ty, duyệt phòng mình" làm cổng duyệt
    rộng bằng cổng xem; còn người chỉ được tick ô «Duyệt» mà không tick ô «Xem» thì
    `scope_condition` bỏ qua mọi grant (không grant nào có `read`) và trả `false()` — cổng
    đóng với MỌI phiếu, kể cả phòng mình. Truyền đúng `action="approve"` bịt cả hai vế.
    """
    return _scope_ok(db, user, pid, "approve")


def _notify_assigned(db: Session, pr, user, background_tasks: BackgroundTasks) -> None:
    """Báo "được phân công phụ trách" cho NSTM vừa được gán tự động.
    Gọi ở bước điều phối (công tắc BẬT) hoặc ngay khi duyệt (công tắc TẮT) — nội dung y như nhau."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User as _User
    emp_ids = set()
    if pr.assignee_id:
        emp_ids.add(pr.assignee_id)
    codes = [it.assignee for it in service.items_of(db, pr.id) if it.assignee]
    if codes:
        emp_ids.update(e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all())
    if not emp_ids:
        return
    uids = [u.id for u in db.query(_User).filter(_User.employee_id.in_(emp_ids), _User.is_active == True).all()]
    if uids:
        trigger_notification(db=db, event="pr_assigned", doc_type="purchase_request", doc_code=pr.code,
                             creator_id=user.id, background_tasks=background_tasks,
                             link=f"/purchase-requests/{pr.id}", recipient_ids=uids)


# Chữ ký 2 bước duyệt trên phiếu in chỉ có hiệu lực từ mốc trạng thái tương ứng trở đi.
# Phiếu bị TRẢ VỀ (Nháp / Chờ duyệt) sẽ KHÔNG in lại chữ ký duyệt của lần trước.
_AFTER_APPROVE = STATUS_AFTER_APPROVE
_AFTER_DISPATCH = STATUS_AFTER_DISPATCH


def _purchasing_head(db: Session, dispatcher_uid: int) -> tuple[str, str]:
    """bao-CR-397 — TRƯỞNG PHÒNG của phòng ban mà người bấm Điều phối đang thuộc.

    Ô "TP/BP mua hàng" trên bản in là chữ ký của trưởng phòng thu mua, không phải của
    người bấm nút: trên prod người điều phối thường là ADMIN thu mua (Châu Phúc Hậu) nên
    tên admin in vào ô trưởng phòng. Hệ không có cờ "phòng thu mua", nên lấy phòng của
    chính người điều phối (tài khoản -> nhân sự -> `department_id`) rồi đọc
    `Department.manager_id` — cột trưởng bộ phận chọn cứng ở danh mục Phòng ban.

    Trả `("", "")` khi không suy ra được (tài khoản chưa gắn nhân sự, nhân sự chưa có
    phòng, phòng chưa gán trưởng) — chỗ gọi tự lùi về người điều phối như trước CR này.
    Chữ ký tra theo NHÂN SỰ trưởng phòng (`resolve_signature_by_employee`) để ảnh khớp
    đúng tên đang in.
    """
    from app.core.audit import resolve_signature_by_employee
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    user = db.get(User, dispatcher_uid) if dispatcher_uid else None
    emp = db.get(Employee, user.employee_id) if (user and user.employee_id) else None
    dept = db.get(Department, emp.department_id) if (emp and emp.department_id) else None
    head = db.get(Employee, dept.manager_id) if (dept and dept.manager_id) else None
    if not head or not (head.full_name or "").strip():
        return "", ""
    return head.full_name, resolve_signature_by_employee(db, head.id)


def _approval_signers(db: Session, pr) -> dict:
    """Người ký 2 bước duyệt của phiếu — tra từ nhật ký thao tác (audit log).

    Bước 1 `approved`  (trưởng phòng duyệt)  -> ô "TP/BP đề xuất" trên phiếu in.
    Bước 2 `dispatched` (thu mua điều phối)  -> `dispatcher_*` (người bấm nút, giữ cho
    tương thích) và `purchasing_head_*` = TRƯỞNG PHÒNG của người đó (bao-CR-397) -> ô
    "TP/BP mua hàng". Phòng chưa gán trưởng thì `purchasing_head_*` lùi về người điều phối.
    Công tắc `pr_dispatch_enabled` TẮT: từ bao-CR-485 sổ chỉ còn MỘT dòng `approved` (không
    còn dòng `dispatched` dưới tên người duyệt), nên ở đây lùi: người điều phối = người duyệt
    → ô "TP/BP mua hàng" ra trưởng phòng của NGƯỜI DUYỆT — chấp nhận như trước, vì luồng đó
    không có thu mua nào chạm vào phiếu. Phiếu cũ (trước CR-485) vẫn có dòng `dispatched` nên
    đi đường thường.
    """
    from app.core.audit import resolve_actor, resolve_signature
    from app.modules.audit.model import AuditLog

    out = {"approver_name": "", "approver_signature": "",
           "dispatcher_name": "", "dispatcher_signature": "",
           "purchasing_head_name": "", "purchasing_head_signature": ""}
    want = ([("approved", "approver")] if pr.status in _AFTER_APPROVE else []) + \
           ([("dispatched", "dispatcher")] if pr.status in _AFTER_DISPATCH else [])
    if not want:
        return out
    actions = [a for a, _ in want]
    rows = (db.query(AuditLog.action, AuditLog.created_by)
            .filter(AuditLog.entity == service.ENTITY, AuditLog.entity_id == pr.id,
                    AuditLog.action.in_(actions))
            .order_by(AuditLog.id.desc()).all())
    latest: dict[str, int] = {}
    for action, uid in rows:
        latest.setdefault(action, uid)        # dòng đầu = lần duyệt GẦN NHẤT
    if ("dispatched" in actions and "dispatched" not in latest and latest.get("approved")
            and not service.dispatch_enabled()):
        latest["dispatched"] = latest["approved"]     # bao-CR-485, xem docstring
    for action, key in want:
        uid = latest.get(action)
        if uid:
            out[f"{key}_name"] = resolve_actor(db, uid)
            out[f"{key}_signature"] = resolve_signature(db, uid)
    # bao-CR-490: có cột «Trưởng phòng phê duyệt» thì ô «TP/BP đề xuất» tra theo NHÂN SỰ đó
    # (khớp đúng tên in), nhật ký chỉ còn là đường lùi cho phiếu cũ.
    from app.core.print_signers import person_block
    stored = person_block(db, int(getattr(pr, "approver_employee_id", 0) or 0))
    if stored["name"] and pr.status in _AFTER_APPROVE:
        out["approver_name"], out["approver_signature"] = stored["name"], stored["signature"]
    dispatcher_uid = latest.get("dispatched")
    if dispatcher_uid:
        head_name, head_sign = _purchasing_head(db, dispatcher_uid)
        out["purchasing_head_name"] = head_name or out["dispatcher_name"]
        out["purchasing_head_signature"] = head_sign if head_name else out["dispatcher_signature"]
    return out


def _has_quote_file(db: Session, pr) -> bool:
    """bao-CR-317 — phiếu này có BÁO GIÁ đính kèm hay không (ô tick trên bản in).

    Trước CR này bản in chỉ soi cột `quote_file_url` — ô tải đúng 1 file từ thời đầu, nay
    không màn nào ghi vào nữa (prod: 0/116 phiếu có giá trị). Chứng từ đã dời hết sang khối
    "Chứng từ & Tài liệu đính kèm" (`tab_file_link`, loại `quotation`), nên bản in luôn tick
    "Không" kể cả khi phiếu có báo giá thật. Đếm lại theo cả ba nguồn:
      1. cột cũ `quote_file_url` — phiếu đời đầu, giữ để không mất dữ liệu;
      2. file loại "Báo giá" trong khối đính kèm — đường đi hiện tại;
      3. entity cũ `purchase_request_quote` — khối tải báo giá riêng, loại chứng từ để rỗng.
    """
    from app.modules.attachment.model import FileLink

    if (pr.quote_file_url or "").strip():
        return True
    q = (db.query(FileLink.id)
         .filter(FileLink.entity_id == pr.id,
                 sa_or(sa_and(FileLink.entity == "purchase_request", FileLink.doc_type == "quotation"),
                       FileLink.entity == "purchase_request_quote")))
    return db.query(q.exists()).scalar() is True


def _linked_survey_requests(db: Session, pr) -> list[dict]:
    """bao-CR-318 (mở rộng bao-CR-422) — MỌI YÊU CẦU BÁO GIÁ (YCBG) đã sinh ra phiếu này.

    Đơn mua hàng có `pr_code` trỏ ngược về YCMH, nhưng chiều YCMH -> YCBG thì chỉ nằm trong
    câu chữ ở ô Nội dung, bấm không ra. Liên kết thật vốn đã có sẵn trong CSDL:
      - `tab_survey_request_pr`: mỗi lần chốt phương án tạo YCMH ghi 1 dòng (nguồn chuẩn);
      - `tab_survey_request_line.pr_id`: đường cũ, dùng cho phiếu tạo trước khi có bảng trên.

    Bản đầu (bao-CR-318) chỉ lấy MỘT phiếu bằng `limit(1)`, và điều đó giấu bớt sự thật: một
    YCMH gom được nhiều dòng đã chốt phương án, mà các dòng ấy có thể nằm ở những YCBG khác
    nhau. Người xem thấy đúng một mã liền tưởng phiếu chỉ có một nguồn. Nay trả cả danh sách,
    xếp theo thứ tự liên kết được ghi (nguồn đầu tiên đứng đầu).

    Không tra ra thì trả danh sách rỗng — phiếu lập tay là chuyện bình thường, không phải lỗi.
    """
    from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                                  SurveyRequestPr)

    # Gom id theo ĐÚNG thứ tự gặp và khử trùng: một YCBG có nhiều dòng cùng đổ vào một YCMH
    # thì vẫn chỉ là một nguồn, bày hai lần là người đọc tưởng có hai phiếu.
    sr_ids: list[int] = []
    for (sr_id,) in (db.query(SurveyRequestPr.survey_request_id)
                     .filter(SurveyRequestPr.pr_id == pr.id)
                     .order_by(SurveyRequestPr.id.asc()).all()):
        if sr_id and sr_id not in sr_ids:
            sr_ids.append(int(sr_id))
    if not sr_ids:
        for (sr_id,) in (db.query(SurveyRequestLine.survey_request_id)
                         .filter(SurveyRequestLine.pr_id == pr.id)
                         .order_by(SurveyRequestLine.id.asc()).all()):
            if sr_id and sr_id not in sr_ids:
                sr_ids.append(int(sr_id))
    if not sr_ids:
        return []

    rows = (db.query(SurveyRequest.id, SurveyRequest.code, SurveyRequest.status,
                     SurveyRequest.request_date, SurveyRequest.requester)
            .filter(SurveyRequest.id.in_(sr_ids)).all())
    by_id = {int(r[0]): r for r in rows}
    out: list[dict] = []
    for sid in sr_ids:
        r = by_id.get(sid)
        # Phiếu nguồn đã bị xóa thì bỏ qua: liên kết còn nhưng không có gì để bấm vào.
        if not r or not r[1]:
            continue
        out.append({"id": sid, "code": r[1], "status": r[2] or "",
                    "request_date": r[3] or "", "requester": r[4] or ""})
    return out


def _out(db: Session, pr, user=None) -> dict:
    from app.core.audit import (resolve_actor, resolve_signature,
                                resolve_signature_by_employee)
    d = {c: getattr(pr, c) for c in HEADER_COLS}
    d["vat_rate"] = float(pr.vat_rate or 0)
    # Trưởng bộ phận: phiếu lập lúc phòng chưa gán trưởng sẽ lưu rỗng và ở rỗng vĩnh viễn.
    # Rỗng thì lấy theo Department.manager_id hiện tại để HIỂN THỊ (không ghi đè dữ liệu đã lưu).
    if not d.get("head_of_dept") and (pr.department_id or pr.department):
        d["head_of_dept"] = service.find_dept_head(db, pr.department, pr.department_id)
    # bao-CR-480: ô Phòng ban rỗng thì HIỂN THỊ cho ra tên — có id phòng mà thiếu tên (phiếu
    # dựng bằng script) thì tra danh mục; không có cả id (lập trước bao-CR-465) thì theo hồ sơ
    # nhân sự của người yêu cầu. Không ghi đè dữ liệu: lưu / gửi duyệt mới ghi.
    if not (d.get("department") or "").strip():
        if d.get("department_id"):
            d["department"] = service.handler_dept_name_of(db, d["department_id"])
        else:
            d["department_id"], d["department"] = service.resolve_employee_department(db, pr.requester_id)
    # bao-CR-480: tên phòng xử lý đi kèm phiếu — màn hình không cần quyền đọc danh mục phòng
    # ban mới hiện được tên (trước đây người thiếu quyền chỉ thấy «Phòng #5»).
    d["handler_dept_name"] = service.handler_dept_name_of(db, pr.handler_dept_id)
    # bao-CR-490: trưởng phòng phê duyệt (người thực bấm Duyệt) + trưởng phòng theo hồ sơ.
    from app.core.print_signers import approver_fields
    d.update(approver_fields(db, pr))
    # Task 4: NCC 2 cụm. Cụm 'req' (bộ phận đề xuất) MỌI người xem/sửa được — sửa bug người
    # yêu cầu không nhập nổi NCC của chính mình. Cụm 'pur' (khảo sát/thu mua) cần supplier.read
    # để xem, supplier.write để sửa.
    can_sup_read = user is None or user_has_permission(db, user, "supplier", "read")
    cl = service.clusters_of(pr)
    d["supplier_req"] = cl["req"]
    d["supplier_pur"] = cl["pur"] if can_sup_read else service._empty_cluster()
    d["supplier_from_survey"] = cl["from_survey"]
    d["can_edit_supplier_pur"] = user is not None and user_has_permission(db, user, "supplier", "write")
    # CR-034: nút duyệt lần 2 (điều phối) — quyền tính ở server (phạm vi grant không có ở map
    # quyền phía FE). Công tắc tắt thì không ai thấy nút, vì phiếu không dừng ở 'approved' nữa.
    d["dispatch_enabled"] = service.dispatch_enabled()
    # bao-CR-468: công tắc cụm phương án. Đi kèm phiếu chứ không phải một đường API riêng —
    # người dùng thường KHÔNG có quyền `setting.read`, mà hai chỗ phải ẩn (nút Xử lý phương án,
    # thẻ Chọn phương án) đều đã cầm sẵn dữ liệu phiếu này.
    d["options_enabled"] = option_service.options_enabled()
    d["can_dispatch"] = bool(user is not None and pr.status == "approved" and d["dispatch_enabled"]
                             and _can_dispatch(get_perm_profile(db, user)))
    # bao-CR-414 GĐ5: nút "Chuyển phòng xử lý" / "Trả về phòng lập" — chỉ quản lý thu mua của
    # phòng ĐANG CẦM phiếu (hoặc toàn hệ) và khi việc mua chưa thật sự bắt đầu.
    d["can_transfer_dept"] = bool(user is not None and service.can_transfer_dept(db, pr)
                                  and holds_handling_dept(get_perm_profile(db, user), "purchase_request", pr))
    d["can_return_dept"] = bool(d["can_transfer_dept"] and (pr.handler_dept_id or 0))
    # Duyệt bước 1: cũng phải tính ở server vì có quyền `approve` chưa chắc đúng PHẠM VI —
    # Admin thu mua (phạm vi 'proc') có approve để duyệt điều phối nhưng không duyệt bước 1.
    # CR-071: ô TBP (`head_of_dept_id`) CHỈ để lưu + in, KHÔNG khóa quyền duyệt — chọn ai
    # thì ai có quyền trong phạm vi vẫn duyệt được như trước.
    d["can_approve"] = bool(user is not None and pr.status == "submitted"
                            and user_has_permission(db, user, "purchase_request", "approve")
                            and _in_approve_scope(db, user, pr.id))
    # NCC "hiệu lực" ở cột cũ (suggested_supplier*) — che nếu không có supplier.read (giữ Task 5).
    if not can_sup_read:
        _blank_supplier(d)
    d["created_at"] = pr.created_at
    d["created_by_name"] = resolve_actor(db, pr.created_by)
    # bao-CR-419: mốc người yêu cầu chốt xong lựa chọn phương án (None = vòng này chưa xong).
    d["options_chosen_at"] = pr.options_chosen_at
    d["options_chosen_by_name"] = resolve_actor(db, pr.options_chosen_by) if pr.options_chosen_by else ""
    # bao-CR-317: ô "Báo giá đính kèm" trên bản in — xem `_has_quote_file`.
    d["has_quote_file"] = _has_quote_file(db, pr)
    # bao-CR-318 + bao-CR-422: đường quay về YCBG nguồn — xem `_linked_survey_requests`.
    # Danh sách rỗng = phiếu lập tay. Hai khóa vô hướng bên dưới là phiếu nguồn ĐẦU TIÊN, giữ
    # nguyên tên cũ vì giao diện cũ (`frontend/`) và bản in đang đọc thẳng chúng — thêm khóa
    # mới thì bên đó không phải sửa gì.
    srs = _linked_survey_requests(db, pr)
    d["survey_requests"] = srs
    d["survey_request_id"] = srs[0]["id"] if srs else 0
    d["survey_request_code"] = srs[0]["code"] if srs else ""
    # Chữ ký ô "Người lập" trên phiếu in. Tra theo NHÂN SỰ người yêu cầu (đúng cái TÊN đang in);
    # phiếu cũ chưa có requester_id thì mới lấy chữ ký người tạo, và chỉ khi tên trùng nhau —
    # tránh in chữ ký người A dưới tên người B khi thu mua lập phiếu hộ bộ phận khác.
    d["requester_signature"] = resolve_signature_by_employee(db, pr.requester_id)
    if not d["requester_signature"] and not pr.requester_id:
        if (d["created_by_name"] or "").strip() == (pr.requester or "").strip():
            d["requester_signature"] = resolve_signature(db, pr.created_by)
    # Chữ ký + họ tên 2 ô duyệt trên phiếu in (TP/BP đề xuất · TP/BP mua hàng)
    d.update(_approval_signers(db, pr))

    # Fetch company name safely to avoid permission issues on the frontend
    d["company_name"] = ""
    if pr.company_id:
        from app.modules.company.model import Company
        comp = db.query(Company).filter(Company.id == pr.company_id).first()
        if comp:
            d["company_name"] = comp.name

    items = service.items_of(db, pr.id)
    # Batch resolve ảnh gốc theo product_code (2 query/phiếu, tránh N+1).
    from app.modules.product.model import Product
    from app.modules.attachment.model import FileLink, StoredFile
    codes = {i.product_code for i in items if i.product_code}
    prod_by_code: dict[str, int] = {}
    if codes:
        for pid_, code_ in db.query(Product.id, Product.code).filter(Product.code.in_(codes)):
            prod_by_code.setdefault(code_, pid_)   # code catalog duy nhất
    thumb_by_pid: dict[int, str] = {}
    if prod_by_code:
        q = (db.query(FileLink.entity_id, StoredFile.url)
             .join(StoredFile, StoredFile.id == FileLink.file_id)
             .filter(FileLink.entity == "product", FileLink.entity_id.in_(prod_by_code.values()))
             .order_by(FileLink.entity_id, FileLink.sort_order.asc(), FileLink.id.desc()))
        for eid, url in q:
            thumb_by_pid.setdefault(eid, url)      # ảnh sort_order nhỏ nhất mỗi SP
    # H.10.1 — SINH BÙ phương án 0 cho phiếu điều phối từ trước khi có tính năng
    # (idempotent; phiếu ngoài giai đoạn mở thì hàm tự bỏ qua). Đặt TRƯỚC hai truy
    # vấn tóm tắt để option_count/chosen_option của lần đọc này đã thấy nó.
    option_service.ensure_option_zero(db, pr, items)
    # bao-CR-310: tóm tắt phương án cho từng dòng — 2 truy vấn cho cả phiếu, không N+1.
    item_ids = [i.id for i in items]
    opt_counts = option_service.count_map(db, item_ids)
    chosen_by_item = option_service.chosen_map(db, item_ids)
    d["items"] = []
    for i in items:
        pid_ = prod_by_code.get(i.product_code or "")
        chosen = chosen_by_item.get(i.id)
        d["items"].append(
            {"id": i.id, "product_code": i.product_code, "product_name": i.product_name,
             "item_group": i.item_group, "group_desc": i.group_desc, "qty": float(i.qty or 0),
             "unit": i.unit, "price": float(i.price or 0), "vat_pct": float(i.vat_pct or 0),
             "amount": float(i.amount or 0),
             "warehouse": i.warehouse, "required_date": i.required_date, "assignee": i.assignee,
             "expected_date": i.expected_date,
             "line_status": i.line_status,
             # B-06: cột lưu MÃ, giao diện dùng mã để tô màu/lọc nên phải trả kèm nhãn
             "line_status_label": PR_LINE_STATUS.label_of(i.line_status),
             "progress_note": i.progress_note, "note": i.note,
             "qty_ordered": float(i.qty_ordered or 0), "qty_received": float(i.qty_received or 0),
             "product_id": pid_ or 0,                          # 0 = code không khớp catalog
             "product_thumbnail_url": thumb_by_pid.get(pid_, "") if pid_ else "",
             # bao-CR-310 — "đã chốt phương án chưa" SUY từ bảng phương án, dòng YCMH
             # không có cột nào lưu việc đó (một nguồn sự thật).
             "option_count": opt_counts.get(i.id, 0),
             "chosen_option": _out_option(db, chosen, can_sup_read) if chosen else None,
             # Đợt 3b — cờ "NSTM đã chốt hoàn thành xử lý" + chốt rỗng của dòng
             "options_done": bool(i.options_done), "no_option": bool(i.no_option)}
        )
    # Task 4: PYC tính VAT lại theo dòng — tiền hàng (chưa VAT) · VAT · tổng cộng (gồm VAT)
    subtotal = round(sum(x["qty"] * x["price"] for x in d["items"]), 2)   # chưa VAT
    total = round(sum(x["amount"] for x in d["items"]), 2)                # gồm VAT
    d["subtotal"] = subtotal
    d["vat"] = round(total - subtotal, 2)
    d["total"] = total
    return d


def _list_query(request: Request, db: Session, user):
    """Câu truy vấn danh sách (lọc + phạm vi + sắp xếp) — dùng chung cho màn danh sách và xuất Excel."""
    from sqlalchemy import or_
    # `code` bị loại khỏi lọc TRẦN vì param `code=` dưới đây là ô tìm kiếm đa trường; nhưng bộ
    # lọc điều kiện (`code__contains=...`) vẫn phải lọc được nên giữ nguyên FILTERABLE đầy đủ.
    filterable = [f for f in service.FILTERABLE if f != "code"]
    query = apply_filters(db.query(PurchaseRequest).filter(PurchaseRequest.is_deleted == False), PurchaseRequest, request, filterable, operator_filterable=service.FILTERABLE)
    query = apply_ref_filters(query, PurchaseRequest, request, db)   # CR-088
    query = apply_range_filters(query, PurchaseRequest, request,
                                ["request_date", "received_date", "need_date"])
    query = apply_equals(query, PurchaseRequest, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.item_group.like(f"%{item_group}%"))
        query = query.filter(PurchaseRequest.id.in_(sub))
    assignee = (request.query_params.get("assignee") or "").strip()
    if assignee:
        sub2 = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.assignee == assignee)
        query = query.filter(PurchaseRequest.id.in_(sub2))
    # Ô tìm kiếm nhanh: Tìm theo Mã PYC, Người yêu cầu, Mục đích, Mã sản phẩm hoặc Tên sản phẩm ở dòng hàng
    search = (request.query_params.get("code") or request.query_params.get("q") or request.query_params.get("search") or request.query_params.get("product") or "").strip()
    if search:
        like = f"%{search}%"
        matching_ids = [
            r[0] for r in db.query(PurchaseRequestItem.pr_id)
            .filter(or_(PurchaseRequestItem.product_code.like(like), PurchaseRequestItem.product_name.like(like))).all()
            if r[0]
        ]
        conds = [
            PurchaseRequest.code.like(like),
            PurchaseRequest.requester.like(like),
            PurchaseRequest.purpose.like(like),
        ]
        if matching_ids:
            conds.append(PurchaseRequest.id.in_(matching_ids))
        query = query.filter(or_(*conds))
    query = apply_scope(query, PurchaseRequest, "purchase_request", user, get_perm_profile(db, user))
    return apply_sort_from_request(query, PurchaseRequest, request)


@router.get("")
def list_pr(
    request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("purchase_request", "read")),
):
    query = _list_query(request, db, user)
    total, items = service.list_pr(db, query, pg)
    
    pr_ids = [p.id for p in items]
    subtotals = {}
    need_dates = {}
    if pr_ids:
        subtotals = {
            pr_id: float(amount or 0) for pr_id, amount in db.query(
                PurchaseRequestItem.pr_id,
                func.sum(PurchaseRequestItem.amount)
            ).filter(PurchaseRequestItem.pr_id.in_(pr_ids)).group_by(PurchaseRequestItem.pr_id).all()
        }
        need_rows = db.query(
            PurchaseRequestItem.pr_id,
            func.min(PurchaseRequestItem.required_date)
        ).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids),
            PurchaseRequestItem.required_date != "",
            PurchaseRequestItem.required_date.isnot(None),
            PurchaseRequestItem.line_status != service.LINE_STATUS_CANCELLED
        ).group_by(PurchaseRequestItem.pr_id).all()
        need_dates = {r[0]: r[1] for r in need_rows if r[1]}

    cancelled_ids = set()
    if pr_ids:
        cancelled_ids = {r[0] for r in db.query(PurchaseRequestItem.pr_id).filter(
            PurchaseRequestItem.pr_id.in_(pr_ids),
            PurchaseRequestItem.line_status == service.LINE_STATUS_CANCELLED).distinct().all()}

    can_see_supplier = user_has_permission(db, user, "supplier", "read")   # Task 5
    out_items = []
    for p in items:
        d = {c: getattr(p, c) for c in HEADER_COLS}
        d["created_at"] = p.created_at   # thời điểm tạo (có giờ) — hiển thị giờ VN ở list
        d["updated_at"] = p.updated_at   # bao-CR-294 — cột "Ngày cập nhật" + sort ở màn danh sách
        d["need_date"] = need_dates.get(p.id) or p.need_date or ""
        d["total"] = round(subtotals.get(p.id, 0.0), 2)   # gồm VAT (tính từ amount dòng)
        d["has_cancelled_line"] = p.id in cancelled_ids
        if not can_see_supplier:
            _blank_supplier(d)   # ẩn NCC đề xuất
        out_items.append(d)

    return success({"total": total, "items": out_items})


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
    """bao-CR-486 — NSTM chọn được cho phiếu này: đi theo ô «Phòng xử lý» (xem
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
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success({"items": service.dept_head_candidates(db, pr)})


@router.get("/{pid}")
def get_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
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
    profile = get_perm_profile(db, user)
    pr = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id == pid),
                     PurchaseRequest, "purchase_request", user, profile).first()
    if not pr:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    from app.modules.purchase_order import service as po_service
    rows = (db.query(POItem.product_code, func.coalesce(func.sum(POItem.qty_order), 0))
            .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
            .filter(PurchaseOrder.pr_code == pr.code,
                    PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]),
                    POItem.progress_status.notin_([po_service.PROG_NOT_ORDERED,
                                                   po_service.PROG_CANCELLED]))
            .group_by(POItem.product_code).all())
    ordered = {code: float(qty or 0) for code, qty in rows if code}
    return success({"ordered": ordered})


@router.post("")
def create_pr(data: PRCreate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    can_pur = user_has_permission(db, user, "supplier", "write")   # Task 4: chỉ QL/Admin sửa cụm NCC thu mua
    return success(_out(db, service.create_pr(db, data, user.id, can_pur), user), "Đã tạo yêu cầu mua", 201)


@router.post("/{pid}/copy")
def copy_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_pr(db, pid, user.id), user), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.post("/{pid}/clone")   # alias để nút Nhân bản ở danh sách (CrudList) dùng chung 1 đường dẫn
def clone_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    _in_scope(db, pid, user, "create")
    return success(_out(db, service.copy_pr(db, pid, user.id), user), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.patch("/{pid}/assign")
def assign_pr(pid: int, data: AssignIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    _in_scope(db, pid, user, "approve")
    pr = service.assign(db, pid, data, user.id)
    # Thông báo "được phân công phụ trách" cho NSTM (NSTM header + NSTM từng dòng)
    from app.modules.employee.model import Employee
    from app.modules.user.model import User as _User
    emp_ids = set()
    if pr.assignee_id:
        emp_ids.add(pr.assignee_id)
    codes = [it.assignee for it in service.items_of(db, pid) if it.assignee]
    if codes:
        emp_ids.update(e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all())
    if emp_ids:
        uids = [u.id for u in db.query(_User).filter(_User.employee_id.in_(emp_ids), _User.is_active == True).all()
                if u.id != user.id]   # không tự báo mình
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
    _in_scope(db, pid, user, "read")   # bảng dòng lọc theo phiếu cha — phiếu cha phải lọc phạm vi
    prof = get_perm_profile(db, user)
    pr_perm = prof["perms_union"].get("purchase_request", {})
    is_manager = bool(pr_perm.get("cancel") or pr_perm.get("approve"))   # quản lý/admin sửa mọi dòng
    emp_code = prof.get("emp_code") or ""
    return success(_out(db, service.update_item_status(db, pid, data, user.id, emp_code, is_manager), user), "Đã cập nhật trạng thái")


def _ensure_can_return_or_reject(db: Session, user, pr: PurchaseRequest):
    """Trả về / Từ chối: Quản lý (quyền cancel) làm được mọi giai đoạn;
    Người duyệt (quyền approve) chỉ làm được ở bước Chờ duyệt (submitted) VÀ trong phạm vi của mình.

    ⚠️ Nhánh «Quản lý» ĐI TẮT trước khi tới `_in_approve_scope`, nên trước bản vá này nó chỉ
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
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.cancel_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_cancelled", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr, user), "Đã hủy phiếu")


@router.post("/{pid}/return")
def return_pr(pid: int, data: ReasonIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    _ensure_can_return_or_reject(db, user, service.get_pr(db, pid))
    pr = service.return_pr(db, pid, data.reason, user.id)
    trigger_notification(db=db, event="pr_returned", doc_type="purchase_request", doc_code=pr.code,
                         creator_id=pr.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-requests/{pr.id}")
    return success(_out(db, pr, user), "Đã trả phiếu về (Bị trả lại)")


def _ensure_holds_handling_dept(db: Session, user, pr) -> None:
    """bao-CR-414 GĐ5: chỉ quản lý thu mua của phòng ĐANG CẦM phiếu (hoặc toàn hệ) mới đẩy được."""
    if not holds_handling_dept(get_perm_profile(db, user), "purchase_request", pr):
        raise HTTPException(403, "Chỉ quản lý thu mua của phòng đang xử lý mới chuyển được phiếu này")


def _notify_users(db: Session, user_ids: list[int], title: str, body: str, link: str,
                  creator_id: int, background_tasks: BackgroundTasks | None) -> None:
    """Chuông trong app + Web Push (best-effort) cho một nhóm tài khoản — dùng cho sự kiện
    chuyển phòng (bao-CR-414 GĐ5), thứ chưa có mẫu câu trong `trigger_notification`."""
    from app.modules.notification.model import Notification
    uids = sorted({int(u) for u in user_ids if u})
    if not uids:
        return
    for uid in uids:
        db.add(Notification(user_id=uid, title=title, body=body, link=link, created_by=creator_id))
    db.commit()
    try:
        from app.modules.push import service as push_service
        from app.core.database import SessionLocal
        if background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal, uids, title, body, link)
        else:
            push_service.send_to_users(SessionLocal, uids, title, body, link)
    except Exception:
        pass


def _user_ids_of_employee_codes(db: Session, codes: list[str]) -> list[int]:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    codes = [c for c in codes if c]
    if not codes:
        return []
    emp_ids = [e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all()]
    return [u.id for u in db.query(User).filter(User.employee_id.in_(emp_ids)).all()] if emp_ids else []


def _transfer_dept(db: Session, pid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                   user, *, target: int, message: str):
    pr = _in_scope(db, pid, user, "approve")
    _ensure_holds_handling_dept(db, user, pr)
    old_assignees = [it.assignee for it in service.items_of(db, pid) if (it.assignee or "").strip()]
    pr = service.transfer_handler_dept(db, pid, target, data.reason, user.id)
    where = "phòng lập" if target == 0 else "phòng xử lý khác"
    link = f"/purchase-requests/{pr.id}"
    reason = data.reason.strip()
    _notify_users(db, [pr.created_by or user.id], f"{pr.code} — Chuyển {where}",
                  f"Yêu cầu mua hàng {pr.code} được chuyển sang {where}. Lý do: {reason}",
                  link, user.id, background_tasks)
    if old_assignees:                                  # NSTM bị gỡ khỏi dòng cũng cần biết
        _notify_users(db, _user_ids_of_employee_codes(db, old_assignees),
                      f"{pr.code} — Gỡ phân công mua hàng",
                      f"Phiếu {pr.code} đã chuyển {where}, phần phụ trách của bạn được gỡ. Lý do: {reason}",
                      link, user.id, background_tasks)
    return success(_out(db, pr, user), message)


@router.post("/{pid}/transfer-dept")
def transfer_dept_(pid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    """bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ (đường 2): gỡ NSTM mọi dòng, đổi phòng, phiếu về
    «Đã duyệt (chưa điều phối)» để phòng nhận điều phối lại. Lý do bắt buộc, ghi nhật ký."""
    return _transfer_dept(db, pid, data, background_tasks, user, target=data.handler_dept_id,
                          message="Đã chuyển phòng xử lý")


@router.post("/{pid}/return-dept")
def return_dept_(pid: int, data: TransferDeptIn, background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    """bao-CR-414 GĐ5 — TRẢ VỀ PHÒNG LẬP: cùng điều kiện với chuyển phòng, đích là phòng lập
    (`handler_dept_id` = 0). Khác «Trả về (Bị trả lại)»: phiếu KHÔNG mất trạng thái đã duyệt."""
    return _transfer_dept(db, pid, data, background_tasks, user, target=0,
                          message="Đã trả phiếu về phòng lập")


@router.post("/{pid}/complete")
def complete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "cancel"))):
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
    pr = _in_scope(db, pid, user, "read")
    if not _can_edit_own(db, pr, user):
        raise HTTPException(403, "Không có quyền sửa phiếu này")
    can_pur = user_has_permission(db, user, "supplier", "write")   # Task 4: cụm NCC thu mua chỉ QL/Admin sửa
    return success(_out(db, service.update_pr(db, pid, data, user.id, can_pur), user), "Đã cập nhật")


@router.delete("/{pid}")
def delete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    _in_scope(db, pid, user, "delete")
    service.delete_pr(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_prs(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    # Lọc phạm vi TRƯỚC vòng lặp (khuôn của `contract/controller.py`): xóa hàng loạt mà chỉ
    # lặp theo id thì gửi đại một dãy số là dọn sạch phiếu Nháp của mọi pháp nhân.
    rows = apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.id.in_(id_list),
                                                        PurchaseRequest.is_deleted == False),
                       PurchaseRequest, "purchase_request", user,
                       get_perm_profile(db, user), "delete").all()
    if not rows:
        raise HTTPException(403, "Ngoài phạm vi được phép xóa")
    for pid in [r.id for r in rows]:
        try:
            service.delete_pr(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {pid}: {str(e)}")
    # Báo đúng số ĐÃ xóa, không báo số đã gửi lên — lệch nhau là có id ngoài phạm vi.
    return success(None, f"Đã xóa {len(rows)} bản ghi")


@router.post("/{pid}/submit")
def submit_pr(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
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
        extra_employee_ids=[pr.head_of_dept_id] if pr.head_of_dept_id else None,
    )
    return success(_out(db, pr, user), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_pr(pid: int, data: ApproveIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    # Duyệt lần 1 (trưởng phòng) — chỉ trong phạm vi được phép duyệt. Phạm vi 'proc' (Admin thu mua)
    # không thấy phiếu 'submitted' nên tự động bị loại: họ chỉ điều phối, không duyệt thay trưởng phòng.
    if not _in_approve_scope(db, user, pid):
        raise HTTPException(403, "Ngoài phạm vi được phép duyệt")
    # CR-071 — KHÔNG chặn theo `head_of_dept_id`: ô TBP chỉ để lưu + in, luật duyệt giữ như cũ.
    # CR-034: mặc định KHÔNG tự động phân bổ NSTM ở đây — phiếu dừng ở "Đã duyệt", chờ Quản lý/Admin
    # thu mua duyệt lần 2 (/dispatch). Nếu công tắc `pr_dispatch_enabled` bị TẮT thì chạy luôn bước
    # điều phối ngay tại đây (luồng cũ: duyệt phát là có nhân sự phụ trách).
    # bao-CR-485: đường công tắc TẮT ghi sổ ĐÚNG MỘT dòng «Duyệt» của trưởng phòng (kèm ghi chú
    # hệ thống tự phân bổ) — trước đây ghi thêm dòng «Điều phối» dưới tên họ, đọc như thể trưởng
    # phòng bấm Điều phối, một việc họ không có quyền.
    # bao-CR-497: ngoài công tắc chung, phiếu THỎA «điều kiện bỏ qua điều phối» (màn Cấu hình hệ
    # thống) cũng đi thẳng — để nhà máy tự mua không phải qua thu mua chung trong khi các phòng
    # khác vẫn hai bước. Ô điều kiện rỗng = hành vi cũ.
    pr = service.get_pr(db, pid)
    auto_dispatch = service.skip_dispatch_for(db, pr)
    pr = service.set_status(db, pid, "approved", user.id, audit=not auto_dispatch)
    # bao-CR-490: ghi nhân sự vừa duyệt vào «Trưởng phòng phê duyệt».
    from app.core.print_signers import stamp_approver
    stamp_approver(db, pr, user.id)
    db.commit()
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    n = blank_count = 0
    if auto_dispatch:
        # bao-CR-414: người duyệt chỉ có bậc `dept_proc` (quản lý thu mua CỦA PHÒNG) → chỉ dùng bộ
        # phân công riêng của phòng, không rơi về bộ "Thu mua chung".
        dept_only = approves_only_in_dept_proc(get_perm_profile(db, user), "purchase_request")
        # bao-CR-497: phiếu bỏ qua điều phối NHỜ điều kiện mà có phòng xử lý riêng thì chỉ dùng bộ
        # phân công của phòng đó — tách hẳn khỏi thu mua chung là mục đích của việc bỏ qua.
        dept_only = dept_only or (service.dispatch_enabled() and bool(pr.handler_dept_id))
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
    # công riêng của phòng, không rơi về bộ "Thu mua chung" — thiếu thì họ chọn tay người trong phòng.
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
    from app.modules.survey.model import Survey
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
    sv_cache: dict = {}
    out = []
    for r in rows:
        sv = sv_cache.get(r.survey_id)
        if r.survey_id not in sv_cache:
            sv = sv_cache[r.survey_id] = db.get(Survey, r.survey_id)
        out.append({
            "id": r.id, "supplier_code": r.supplier_code,
            "supplier_name": sr_service.resolve_supplier_name(db, r.supplier_code or ""),
            "internal_code": r.internal_code, "product_name": r.product_name,
            "spec": r.spec, "origin": r.origin, "quote_unit": r.quote_unit,
            "moq": float(r.moq or 0), "price_by_volume": float(r.price_by_volume or 0),
            "volume_range": r.volume_range, "vat": float(r.vat or 0),
            "delivery_time": r.delivery_time, "delivery_place": r.delivery_place,
            "shipping_cost": float(r.shipping_cost or 0), "lab_result": r.lab_result,
            "result_date": r.result_date,
            "survey_code": sv.code if sv else "",
            "survey_item_code": sv.item_code if sv else "",
            "survey_item_group": sv.item_group if sv else "",   # để FE cảnh báo lệch phân loại
        })
    return success({"items": out, "total": total})


@router.post("/{pid}/items/{item_id}/options")
def add_option_from_survey(pid: int, item_id: int, data: PROptionSurveyIn,
                           db: Session = Depends(get_db),
                           user=Depends(require("purchase_request", "write"))):
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
    # Đợt 3b: chỉ chọn trên dòng NSTM ĐÃ chốt hoàn thành — chưa chốt thì danh sách
    # phương án còn đang gắn dở, chọn lúc đó là chọn trên dữ liệu chưa xong.
    option_service.ensure_line_done(item)
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
