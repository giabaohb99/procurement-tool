import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import assert_unique_product_codes
from app.modules.catalog import lead_time

from .model import PurchaseRequest, PurchaseRequestItem
from .schema import AssignIn, ItemStatusIn, PRCreate, PRUpdate

# request_date/need_date nằm trong whitelist để bộ lọc điều kiện lọc theo ngày; lọc khoảng kiểu cũ
# (<field>_from/_to) vẫn do apply_range_filters lo.
FILTERABLE = ["code", "status", "requester", "department", "is_urgent", "request_date", "need_date"]
ENTITY = "purchase_request"

# CR-074: tách bạch "chưa ai lập ĐMH" với "đã có ĐMH nhưng chưa bấm đặt hàng". Trước đây hai
# tình huống này chung một nhãn nên người yêu cầu không biết NSTM đã bắt tay làm chưa.
LINE_STATUS_NO_PO = "Chưa tạo đơn mua hàng"   # mặc định của dòng mới
LINE_STATUS_NOT_ORDERED = "Chưa đặt hàng"     # đã có dòng ĐMH (kể cả đơn Nháp), chưa bấm đặt
# Nhóm "chưa động tới". bao-CR-292: recompute_status không dùng nữa (mốc rời 'dispatched'
# nay là "đã có ĐMH" = khác LINE_STATUS_NO_PO), giữ lại làm tài liệu cho nơi khác tham chiếu.
LINE_STATUS_IDLE = (LINE_STATUS_NO_PO, LINE_STATUS_NOT_ORDERED)

# Task 4 — NCC 2 cụm (req = bộ phận đề xuất · pur = khảo sát/thu mua) lưu JSON ở cột supplier_info.
_AUTO_NOTE_PREFIX = "Sinh tự động từ Yêu cầu báo giá"   # dấu hiệu phiếu tạo từ YCKS (fallback dữ liệu cũ)


def _empty_cluster() -> dict:
    return {"name": "", "tax_code": "", "contact": ""}


def _norm_cluster(c) -> dict:
    """Chuẩn hóa 1 cụm về đúng 3 khóa string (chống dữ liệu JSON lỗi)."""
    c = c if isinstance(c, dict) else {}
    return {"name": (c.get("name") or ""), "tax_code": (c.get("tax_code") or ""),
            "contact": (c.get("contact") or "")}


def clusters_of(pr) -> dict:
    """Trả về {req, pur, from_survey}. Ưu tiên supplier_info JSON; nếu trống thì suy từ dữ liệu cũ:
    phiếu sinh từ YCKS -> cụm 'pur', còn lại -> cụm 'req' (giữ nguyên cột suggested_supplier*)."""
    raw = (getattr(pr, "supplier_info", "") or "").strip()
    if raw:
        try:
            d = json.loads(raw)
            if isinstance(d, dict):
                return {"req": _norm_cluster(d.get("req")), "pur": _norm_cluster(d.get("pur")),
                        "from_survey": bool(d.get("from_survey"))}
        except Exception:
            pass
    # Dữ liệu cũ (trước Task 4): cột suggested_supplier* xưa CHỈ phía thu mua/nhập liệu điền được
    # (người yêu cầu bị khóa ở Task 5) -> luôn đưa vào cụm 'pur', KHÔNG cho bộ phận yêu cầu thấy.
    legacy = {"name": getattr(pr, "suggested_supplier", "") or "",
              "tax_code": getattr(pr, "suggested_supplier_tax_code", "") or "",
              "contact": getattr(pr, "suggested_supplier_contact", "") or ""}
    from_survey = (getattr(pr, "note", "") or "").startswith(_AUTO_NOTE_PREFIX)
    return {"req": _empty_cluster(), "pur": legacy, "from_survey": from_survey}


def apply_supplier_info(pr, clusters: dict) -> None:
    """Ghi supplier_info (JSON) + đồng bộ 'NCC hiệu lực' xuống cột suggested_supplier* cũ
    (ĐMH/list/mẫu in cũ vẫn dùng). Hiệu lực = cụm pur nếu có tên, ngược lại cụm req."""
    req = _norm_cluster(clusters.get("req"))
    pur = _norm_cluster(clusters.get("pur"))
    fs = bool(clusters.get("from_survey"))
    pr.supplier_info = json.dumps({"req": req, "pur": pur, "from_survey": fs}, ensure_ascii=False)
    eff = pur if pur["name"] else req
    pr.suggested_supplier = eff["name"]
    pr.suggested_supplier_tax_code = eff["tax_code"]
    pr.suggested_supplier_contact = eff["contact"]


def build_clusters(prev: dict, data, can_write_pur: bool, from_survey=None) -> dict:
    """Ghép cụm NCC khi lưu: cụm req ai sửa cũng được; cụm pur chỉ khi có quyền supplier.write.
    Cụm không được gửi/không đủ quyền -> giữ nguyên giá trị cũ (prev)."""
    req = _norm_cluster(prev.get("req"))
    pur = _norm_cluster(prev.get("pur"))
    fs = bool(prev.get("from_survey")) if from_survey is None else bool(from_survey)
    if getattr(data, "supplier_req", None) is not None:
        req = _norm_cluster(data.supplier_req.model_dump())
    if getattr(data, "supplier_pur", None) is not None and can_write_pur:
        pur = _norm_cluster(data.supplier_pur.model_dump())
    return {"req": req, "pur": pur, "from_survey": fs}

# Trạng thái xử lý theo DÒNG hàng (rút gọn — CR-007 #3): gộp 2 mức chứng từ kế toán
# ("Chưa gửi ĐMH cho KT"/"Đã gửi ĐMH cho KT") vào "Đã nhận hàng"; bỏ "Tạm ngưng".
LINE_STATUS = [LINE_STATUS_NO_PO, LINE_STATUS_NOT_ORDERED, "Đã đặt hàng", "Đã nhận hàng",
               "Hoàn thành", "Hủy đơn"]


def find_dept_head(db: Session, department_name: str) -> str:
    """Tên Trưởng bộ phận của 1 phòng ban (theo field manager_id chọn cứng). '' nếu chưa gán."""
    if not department_name:
        return ""
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    dep = db.query(Department).filter(Department.name == department_name).first()
    if not dep or not dep.manager_id:
        return ""
    head = db.get(Employee, dep.manager_id)
    return head.full_name if head else ""


def find_dept_head_id(db: Session, department_name: str) -> int:
    """Id NHÂN SỰ của Trưởng bộ phận theo `Department.manager_id`. 0 = chưa gán."""
    if not department_name:
        return 0
    from app.modules.department.model import Department
    dep = db.query(Department).filter(Department.name == department_name).first()
    return int(dep.manager_id or 0) if dep else 0


# ---------------------------------------------------------------------------
# CR-071 — Trưởng bộ phận trên phiếu: CHỌN ĐƯỢC, nhưng CHỈ ĐỂ LƯU + IN
# ---------------------------------------------------------------------------
# Trước đây ô "Trưởng bộ phận" tự điền theo `Department.manager_id` và không sửa được, nên
# phòng có nhiều người ký (phó phòng, quyền trưởng phòng) thì in ra sai tên. Nay người lập
# CHỌN được một người trong số những người thật sự duyệt được phiếu này.
#
# QUAN TRỌNG — chọn ai KHÔNG khóa quyền duyệt: luật duyệt giữ nguyên như cũ, ai có quyền
# `approve` và phiếu nằm trong phạm vi của họ thì vẫn bấm Duyệt được. Ô này chỉ mang ý nghĩa
# lưu trữ + in phiếu. Đừng thêm điều kiện chặn duyệt theo `head_of_dept_id` ở đây.

def _approver_users(db: Session):
    """Ứng viên: tài khoản đang hoạt động, có nhân sự, giữ vai trò `approve` YCMH phạm vi 'dept'.

    Phạm vi 'proc'/'all' (thu mua điều phối / admin) không phải "trưởng phòng" nên không vào
    danh sách chọn — nhưng quyền duyệt của họ không đổi.
    """
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole
    role_ids = [p.role_id for p in db.query(Permission).filter(
        Permission.entity == "purchase_request", Permission.can_approve == True,   # noqa: E712
        Permission.scope == "dept").all()]
    if not role_ids:
        return []
    uids = {ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).all()}
    if not uids:
        return []
    return (db.query(User).filter(User.id.in_(uids), User.is_active == True,      # noqa: E712
                                  User.employee_id > 0).all())


def _can_user_approve_row(db: Session, u, pr_id: int) -> bool:
    """Người `u` có thấy phiếu này trong phạm vi duyệt của họ không.

    Chạy ĐÚNG `apply_scope` chứ không chép lại luật phạm vi — nếu tự viết lại điều kiện
    theo tên phòng thì danh sách chọn và nút Duyệt sẽ lệch nhau, mà lệch ở đây nghĩa là
    chọn được một người không bấm duyệt nổi.
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    q = db.query(PurchaseRequest.id).filter(PurchaseRequest.id == pr_id)
    return apply_scope(q, PurchaseRequest, "purchase_request", u,
                       get_perm_profile(db, u)).first() is not None


def dept_head_candidates(db: Session, pr: PurchaseRequest) -> list[dict]:
    """Những người duyệt được bước 1 CỦA ĐÚNG PHIẾU NÀY — nguồn cho ô chọn TBP.

    Tính ngược `apply_scope`: thay vì hỏi "phiếu nào người này thấy" thì hỏi "ai thấy
    phiếu này". Tốn một hồ sơ quyền cho mỗi ứng viên, nhưng số người có quyền duyệt YCMH
    phạm vi phòng chỉ vài chục, và endpoint này chỉ gọi khi người dùng mở ô chọn.
    """
    from app.modules.employee.model import Employee
    users = [u for u in _approver_users(db) if _can_user_approve_row(db, u, pr.id)]
    if not users:
        return []
    emps = {e.id: e for e in db.query(Employee).filter(
        Employee.id.in_([u.employee_id for u in users])).all()}
    out = []
    for u in users:
        e = emps.get(u.employee_id)
        if not e:
            continue
        out.append({"employee_id": e.id, "name": e.full_name or "", "code": e.code or "",
                    "position": e.position or ""})
    out.sort(key=lambda r: r["name"])
    return out


def dept_head_candidates_by_department(db: Session, department: str, company_id: int = 0) -> list[dict]:
    """Cùng danh sách như trên nhưng cho màn TẠO MỚI — lúc đó chưa có phiếu để soi phạm vi.

    Dựng một phiếu TẠM trong bộ nhớ (không `add` vào session) rồi vẫn hỏi `apply_scope` bằng
    một truy vấn giả theo cột phòng ban/pháp nhân, để danh sách khi tạo và khi sửa ra như nhau.
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    from app.modules.employee.model import Employee
    if not department:
        return []
    users = []
    for u in _approver_users(db):
        q = db.query(PurchaseRequest.id).filter(PurchaseRequest.department == department)
        if company_id:
            q = q.filter(PurchaseRequest.company_id == company_id)
        # Không có phiếu thật để thử, nên hỏi ngược: điều kiện phạm vi của người này có
        # cho phép phòng/pháp nhân NÀY không. Dùng chính `apply_scope` để không chép lại luật.
        sub = apply_scope(q, PurchaseRequest, "purchase_request", u, get_perm_profile(db, u))
        if _scope_allows_department(db, u, department, company_id, sub, q):
            users.append(u)
    if not users:
        return []
    emps = {e.id: e for e in db.query(Employee).filter(
        Employee.id.in_([u.employee_id for u in users])).all()}
    out = []
    for u in users:
        e = emps.get(u.employee_id)
        if not e:
            continue
        out.append({"employee_id": e.id, "name": e.full_name or "", "code": e.code or "",
                    "position": e.position or ""})
    out.sort(key=lambda r: r["name"])
    return out


def _scope_allows_department(db: Session, u, department: str, company_id: int, scoped_q, plain_q) -> bool:
    """Phạm vi của `u` có phủ phòng/pháp nhân này không.

    Phòng có sẵn phiếu thì so hai truy vấn là biết ngay. Phòng CHƯA có phiếu nào (phiếu đầu
    tiên) thì cả hai đều rỗng, không kết luận được — lúc đó dựa vào chính hồ sơ quyền: người
    có grant `approve` phạm vi 'dept' mà phòng của họ trùng thì cho vào.
    """
    from app.core.auth import get_perm_profile
    if plain_q.first() is not None:
        return scoped_q.first() is not None
    prof = get_perm_profile(db, u)
    for g in prof.get("grants", []):
        p = g["perms"].get("purchase_request")
        if not (p and p.get("approve")):
            continue
        if p.get("scope") in ("company", "all"):
            return True
        if p.get("scope") == "dept" and (prof.get("dept_name") or "") == department:
            return True
    return False


def sync_head_of_dept_name(db: Session, pr: PurchaseRequest) -> None:
    """Lưu bằng id thì ô TÊN (dùng để in) phải chạy theo, khỏi in một đằng lưu một nẻo."""
    if not getattr(pr, "head_of_dept_id", 0):
        return
    from app.modules.employee.model import Employee
    emp = db.get(Employee, pr.head_of_dept_id)
    if emp and emp.full_name:
        pr.head_of_dept = emp.full_name


def has_cancelled_line(db: Session, pr_id: int) -> bool:
    return db.query(PurchaseRequestItem).filter(
        PurchaseRequestItem.pr_id == pr_id, PurchaseRequestItem.line_status == "Hủy đơn").first() is not None


def _misa_covered_codes(db: Session, pr_code: str) -> set[str]:
    """bao-CR-292 (ticket 22) — các mã hàng ĐÃ được phủ bởi ĐMH có nhập mã đơn MISA.

    'Phủ' = tồn tại dòng ĐMH (khớp product_code) thuộc đơn còn sống (bỏ nháp/chờ duyệt/
    bị trả lại/đã từ chối — cùng rổ với sync_from_purchase_orders) mà đơn đó đã có
    `misa_code`, và bản thân dòng ĐMH không bị Hủy đơn."""
    if not pr_code:
        return set()
    from sqlalchemy import func
    from app.modules.purchase_order.model import PurchaseOrder, POItem
    rows = (db.query(POItem.product_code)
            .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
            .filter(PurchaseOrder.pr_code == pr_code,
                    PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]),
                    func.trim(func.coalesce(PurchaseOrder.misa_code, "")) != "",
                    POItem.progress_status != "Hủy đơn")
            .distinct().all())
    return {r[0] for r in rows}


def recompute_status(db: Session, pr: PurchaseRequest) -> None:
    """Tự suy trạng thái phiếu từ trạng thái các dòng (chỉ khi đã điều phối trở đi).

    CR-034: 'approved' (TP duyệt xong) KHÔNG nằm ở đây — lúc đó phiếu chưa có NSTM, chưa đặt
    hàng được nên không có gì để suy. Mốc "làm việc được" giờ là 'dispatched'.
    Ngoại lệ: công tắc điều phối TẮT thì 'approved' cũng là mốc làm việc (phiếu cũ còn kẹt lại).

    bao-CR-292 (ticket 22): 'Đang xử lý' tách thành BA mốc theo mã đơn MISA + độ phủ mã hàng
    (luật chốt với khách 05/09/2026, phải khớp nhãn tiến độ dòng của luồng gộp — doc/erp/12 P6-13):
      - processing  «Đang xử lý»  : đã có ĐMH (kể cả đơn Nháp) nhưng CHƯA đơn nào nhập MISA;
      - purchasing  «Đang mua hàng»: có ĐMH nhập MISA nhưng mới phủ MỘT PHẦN mã hàng;
      - purchased   «Đã mua hàng» : MỌI mã hàng (trừ dòng Hủy) đều có ĐMH đã nhập MISA.
    Mốc lên 'processing' cũng ĐỔI theo khách: trước đây phải có dòng ĐÃ ĐẶT HÀNG, nay chỉ cần
    NSTM đã tạo ĐMH ("Chưa đặt hàng" trở đi) là phiếu rời 'dispatched'."""
    moc = ["dispatched", "processing", "purchasing", "purchased", "completed"]
    if not dispatch_enabled():
        moc.append("approved")
    if pr.status not in moc:
        return
    items = items_of(db, pr.id)
    st = [(i.line_status or LINE_STATUS_NO_PO) for i in items]
    if not st:
        return
    was_completed = pr.status == "completed"
    # Dòng đã Hủy KHÔNG tính vào điều kiện hoàn thành (1 dòng hủy + các dòng còn lại đủ = vẫn hoàn thành)
    active = [s for s in st if s != "Hủy đơn"]
    if active and all(s == "Hoàn thành" for s in active):
        pr.status = "completed"
    elif any(s != LINE_STATUS_NO_PO for s in active):
        # Đã có ít nhất một dòng được lập ĐMH → nằm trong cụm ba mốc "đang xử lý".
        active_codes = {i.product_code for i in items
                        if (i.line_status or LINE_STATUS_NO_PO) != "Hủy đơn"}
        covered = _misa_covered_codes(db, pr.code) & active_codes
        if not covered:
            pr.status = "processing"
        elif active_codes - covered:
            pr.status = "purchasing"
        else:
            pr.status = "purchased"
    else:
        pr.status = "dispatched"   # chưa dòng nào có ĐMH → vẫn ở mốc đã điều phối
    db.commit()
    if pr.status == "completed" and not was_completed:
        _notify_survey_request_done(db, pr.id, pr.updated_by or 0)
        # Thông báo cho Người tạo PYC khi YCMH hoàn thành toàn bộ
        if pr.created_by:
            from app.modules.notification.service import trigger_notification
            trigger_notification(
                db=db, event="pr_completed", doc_type="purchase_request", doc_code=pr.code,
                creator_id=pr.created_by, background_tasks=None, link=f"/purchase-requests/{pr.id}",
                recipient_ids=[pr.created_by]
            )


# Thứ tự tiến độ dòng (đồng bộ với ĐMH); dòng YCMH = mức KÉM TIẾN NHẤT trong các dòng ĐMH liên kết
# Phải KHỚP PROGRESS_ORDER của ĐMH (Task 8 chèn "Chưa gửi ĐMH cho KT"); thiếu sẽ khiến
# sync đặt nhầm dòng về "Chưa đặt hàng".
_PROGRESS_ORDER = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng",
                   "Chưa gửi ĐMH cho KT", "Đã gửi ĐMH cho KT", "Hoàn thành"]


def sync_from_purchase_orders(db: Session, pr_code: str) -> None:
    """Suy trạng thái + tiến độ SL từng dòng YCMH từ các dòng ĐMH liên kết (khớp product_code),
    rồi suy lại trạng thái phiếu.
    - Chỉ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/bị trả lại/đã từ chối).
    - Dòng ĐMH Hủy: không cộng SL; dòng Tạm ngưng: dùng mức tiến độ trước khi tạm ngưng.
    - Trạng thái dòng YCMH rút gọn còn 6 mức; dòng bị Hủy THỦ CÔNG trên YCMH thì giữ nguyên.
    - qty_ordered/qty_received: tổng SL đặt/nhận theo product_code (đồng bộ vào DB).
    - CR-074: sản phẩm CHƯA có dòng ĐMH nào thì mang nhãn riêng "Chưa tạo đơn mua hàng".
      Mốc "đã tạo đơn" tính CẢ đơn còn Nháp / Chờ duyệt / Bị trả lại — chỉ đơn đã Hủy là
      không tính, vì đơn đó chết rồi thì coi như chưa ai lập."""
    if not pr_code:
        return
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).first()
    if not pr:
        return
    from sqlalchemy import func
    from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
    lines = (db.query(POItem).join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
             .filter(PurchaseOrder.pr_code == pr_code,
                     PurchaseOrder.status.notin_(["draft", "submitted", "cancelled", "rejected"]))
             .all())
    # CR-074: rổ RỘNG HƠN `lines` — chỉ để trả lời "sản phẩm này đã có ai lập đơn chưa".
    # KHÔNG dùng để tính SL/tiến độ (đơn Nháp chưa phải cam kết gì).
    created_prods = {r[0] for r in
                     db.query(POItem.product_code).join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
                     .filter(PurchaseOrder.pr_code == pr_code,
                             PurchaseOrder.status != "cancelled",
                             POItem.progress_status != "Hủy đơn").distinct().all()}
    # Tổng SL đã nhận theo từng dòng ĐMH (gom các lần giao).
    recv_by_item: dict[int, float] = {}
    item_ids = [ln.id for ln in lines]
    if item_ids:
        rows = (db.query(PODelivery.po_item_id, func.coalesce(func.sum(PODelivery.received_qty), 0))
                .filter(PODelivery.po_item_id.in_(item_ids)).group_by(PODelivery.po_item_id).all())
        recv_by_item = {r[0]: float(r[1] or 0) for r in rows}
    ordered_min: dict[str, int] = {}      # sp -> mức KÉM TIẾN NHẤT trong các dòng ĐÃ ĐẶT (>= "Đã đặt hàng")
    has_cancel: set[str] = set()          # sp có dòng Hủy đơn
    ordered_by_prod: dict[str, float] = {}   # sp -> tổng SL đã đặt
    received_by_prod: dict[str, float] = {}  # sp -> tổng SL đã nhận
    expected_max: dict[str, str] = {}        # sp -> ngày dự kiến có hàng MUỘN NHẤT trong các dòng ĐMH
    for ln in lines:
        p = ln.product_code
        ps = ln.progress_status or "Chưa đặt hàng"
        if ps == "Hủy đơn":
            has_cancel.add(p); continue      # dòng hủy: không tính SL, không tính tiến độ
        # Dự kiến có hàng: một dòng YCMH có thể trải ra NHIỀU ĐMH (nhiều NCC, nhiều đợt) nên
        # lấy ngày MUỘN NHẤT — đó mới là lúc dòng được đáp ứng đủ. Ô trống không tính vào max.
        # Ngày lưu dạng ISO 'YYYY-MM-DD' nên so sánh chuỗi là so sánh đúng thứ tự thời gian.
        _ed = (ln.expected_date or "").strip()
        if _ed and _ed > expected_max.get(p, ""):
            expected_max[p] = _ed
        if ps == "Tạm ngưng":
            ps = ln.status_before_pause or "Đã đặt hàng"   # dùng mức trước khi tạm ngưng
        idx = _PROGRESS_ORDER.index(ps) if ps in _PROGRESS_ORDER else 0
        # Dòng ĐMH CHƯA đặt (kể cả đơn đã duyệt nhưng chưa bấm đặt, hoặc đơn nháp mới tạo)
        # KHÔNG kéo trạng thái/tiến độ YCMH xuống — bỏ qua hoàn toàn.
        if idx < 1:
            continue
        ordered_by_prod[p] = ordered_by_prod.get(p, 0.0) + float(ln.qty_order or 0)
        received_by_prod[p] = received_by_prod.get(p, 0.0) + recv_by_item.get(ln.id, 0.0)
        cur = ordered_min.get(p)
        ordered_min[p] = idx if cur is None else min(cur, idx)
    _DONE = _PROGRESS_ORDER.index("Hoàn thành")
    
    prev_statuses = {it.id: (it.line_status or "") for it in items_of(db, pr.id)}
    new_receives = False

    for it in items_of(db, pr.id):
        p = it.product_code
        ordered = ordered_by_prod.get(p, 0.0)
        received = received_by_prod.get(p, 0.0)
        it.qty_ordered = round(ordered, 3)
        it.qty_received = round(received, 3)
        old_st = prev_statuses.get(it.id, "")
        # Ngoại lệ đặt thủ công trên YCMH thì giữ nguyên Hủy đơn khi CHƯA có ĐMH mới (chưa tạo & chưa đặt).
        # Nếu đã tạo ĐMH mới hoặc đặt hàng mới cho sản phẩm này, trạng thái tự động cập nhật theo ĐMH mới.
        if (it.line_status or "") == "Hủy đơn" and p not in ordered_min and p not in created_prods:
            continue
        # Dự kiến có hàng cuộn NGƯỢC từ ĐMH lên:
        #  - ô trên YCMH còn TRỐNG  -> ghi thẳng (đúng nhánh mà luật hiện hành cho sửa tự do)
        #  - ô đã CÓ giá trị và LỆCH -> KHÔNG ghi đè, và KHÔNG báo gì ở đây. Người sửa ĐMH đã
        #    được cảnh báo bằng popup ngay trên màn hình đơn mua hàng (CR-062); có sửa YCMH hay
        #    không là quyền của NSTM, và khi họ sửa thật thì update_item_status mới báo cho
        #    người yêu cầu. Ghi đè ở đây sẽ đi vòng qua luật "đổi ngày phải kèm lý do".
        _emax = expected_max.get(p, "")
        if _emax and not (it.expected_date or "").strip():
            it.expected_date = _emax
        # Suy trạng thái theo SL/tiến độ THỰC (không bị dòng ĐMH chưa đặt làm sai):
        if p not in ordered_min:
            if p in has_cancel and p not in created_prods:
                it.line_status = "Hủy đơn"
            else:
                # CR-074: có dòng ĐMH (kể cả đơn Nháp) → "Chưa đặt hàng"; không có gì → "Chưa tạo đơn mua hàng"
                it.line_status = LINE_STATUS_NOT_ORDERED if p in created_prods else LINE_STATUS_NO_PO
        elif ordered_min[p] >= _DONE:
            it.line_status = "Hoàn thành"        # mọi dòng ĐMH đã đặt đều Hoàn thành
        elif received > 0:
            it.line_status = "Đã nhận hàng"      # đã nhận (một phần trở lên)
        else:
            it.line_status = "Đã đặt hàng"       # đã đặt, chưa nhận

        if (it.line_status in ("Đã nhận hàng", "Hoàn thành")) and (old_st not in ("Đã nhận hàng", "Hoàn thành")):
            new_receives = True

    db.commit()
    recompute_status(db, pr)

    # Thông báo cho Người tạo PYC khi dòng hàng vừa được nhận đủ / hoàn thành
    if new_receives and pr.created_by:
        from app.modules.notification.service import trigger_notification
        trigger_notification(
            db=db, event="pr_items_received", doc_type="purchase_request", doc_code=pr.code,
            creator_id=pr.created_by, background_tasks=None, link=f"/purchase-requests/{pr.id}",
            recipient_ids=[pr.created_by]
        )


def _notify_expected_changed(db: Session, pr: PurchaseRequest, changes: list[str],
                             actor_id: int) -> None:
    """Báo cho NGƯỜI YÊU CẦU khi NSTM vừa đổi "thời gian dự kiến có hàng" trên YCMH.

    Chỉ chạy khi ngày thực sự đổi trên YCMH (không phải khi ĐMH lệch) — sửa hay không là
    quyền của NSTM, còn người yêu cầu thì cần biết hàng của mình lùi/sớm ngày.
    Người nhận: tài khoản của nhân sự người yêu cầu (`requester_id`), không có thì người tạo
    phiếu. Không tự báo cho chính người vừa thao tác.
    """
    from app.modules.user.model import User
    from app.modules.notification.service import trigger_notification

    uid = None
    if pr.requester_id:
        u = (db.query(User)
             .filter(User.employee_id == pr.requester_id, User.is_active == True)
             .first())
        uid = u.id if u else None
    uid = uid or pr.created_by
    if not uid or uid == actor_id:
        return

    trigger_notification(
        db=db, event="pr_expected_date_changed", doc_type="purchase_request", doc_code=pr.code,
        creator_id=actor_id or pr.created_by, background_tasks=None,
        reason="\n".join(f"- {c}" for c in changes),
        link=f"/purchase-requests/{pr.id}", recipient_ids=[uid])


def update_item_status(db: Session, pid: int, data: ItemStatusIn, user_id: int, emp_code: str, is_manager: bool) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không thể cập nhật")
    rows = {i.id: i for i in items_of(db, pid)}
    _expected_changes: list[str] = []
    for it in data.items:
        row = rows.get(it.id)
        if row is None:
            continue
        if not is_manager and (row.assignee or "") != (emp_code or "__none__"):
            continue  # NSTM chỉ sửa dòng được giao cho mình
        if it.line_status is not None:
            row.line_status = it.line_status
        if it.progress_note is not None:
            row.progress_note = it.progress_note
        if it.note is not None:
            row.note = it.note
        # Thời gian dự kiến có hàng: rỗng → cập nhật tự do; ĐÃ có giá trị → đổi phải kèm lý do.
        if it.expected_date is not None:
            old = (row.expected_date or "").strip()
            new = (it.expected_date or "").strip()
            if new != old:
                reason = (it.expected_date_reason or "").strip()
                if old and not reason:
                    raise HTTPException(400, f"Đổi 'thời gian dự kiến có hàng' của '{row.product_name}' "
                                             f"(từ {old}) phải kèm lý do.")
                row.expected_date = new
                _expected_changes.append(f"{row.product_name}: {old or '—'} → {new or '—'}"
                                         + (f" · lý do: {reason}" if reason else ""))
    pr.updated_by = user_id
    db.commit()
    recompute_status(db, pr)
    record(db, user_id, ENTITY, pid, "line_status", "Cập nhật trạng thái dòng")
    for msg in _expected_changes:
        record(db, user_id, ENTITY, pid, "expected_date", msg)
    if _expected_changes:
        _notify_expected_changed(db, pr, _expected_changes, user_id)
    db.refresh(pr)
    return pr


def cancel_pr(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = "cancelled"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "cancelled", reason)
    db.refresh(pr)
    return pr


def return_pr(db: Session, pid: int, reason: str, user_id: int) -> PurchaseRequest:
    """Trả phiếu về "Bị trả lại" (rejected) — người tạo SỬA & GỬI DUYỆT LẠI được (đồng bộ YCKS).
    Xóa nhân sự phụ trách + reset trạng thái mọi dòng về 'Chưa tạo đơn mua hàng' (CR-074)."""
    pr = get_pr(db, pid)
    for it in items_of(db, pid):
        it.assignee = ""
        it.line_status = LINE_STATUS_NO_PO
    pr.assignee_id = 0
    pr.status = "rejected"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "returned", reason)
    db.refresh(pr)
    return pr


def complete_pr(db: Session, pid: int, user_id: int) -> PurchaseRequest:
    pr = get_pr(db, pid)
    # Chỉ hoàn thành phiếu khi MỌI dòng đã ở điểm cuối ("Hoàn thành"/"Hủy đơn") —
    # tránh bấm Hoàn thành khi sản phẩm còn chưa đặt hàng/đang xử lý.
    items = items_of(db, pid)
    pending = [it for it in items if (it.line_status or LINE_STATUS_NO_PO) not in ("Hoàn thành", "Hủy đơn")]
    if not items or pending:
        raise HTTPException(400, "Chưa có sản phẩm đặt hàng hoàn tất — chỉ hoàn thành phiếu khi mọi sản phẩm đã Hoàn thành hoặc Hủy.")
    pr.status = "completed"
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "completed", "")
    _notify_survey_request_done(db, pid, user_id)
    db.refresh(pr)
    return pr


def _notify_survey_request_done(db: Session, pr_id: int, user_id: int) -> None:
    """Kích hoạt tự hoàn thành Yêu cầu khảo sát liên quan (nếu mọi PR của nó đã hoàn thành)."""
    try:
        from app.modules.survey_request import service as sr_service
        sr_service.auto_complete_from_pr(db, pr_id, user_id)
    except Exception:
        pass


def dispatch_enabled() -> bool:
    """CR-034 — CÔNG TẮC bước duyệt lần 2 (điều phối).

    BẬT (mặc định): phiếu dừng ở 'approved' cho tới khi thu mua bấm duyệt lần 2.
    TẮT: quay về luồng cũ — duyệt phát là phân bổ NSTM luôn, phiếu đi thẳng sang 'dispatched'.
    Nguồn: màn Cấu hình hệ thống (key `pr_dispatch_enabled`, lưu DB) → fallback .env
    (`PR_DISPATCH_ENABLED`). Đổi có hiệu lực ngay, không cần deploy."""
    from app.core import app_settings
    return bool(app_settings.get("pr_dispatch_enabled"))


def dispatch_pr(db: Session, pid: int, user_id: int) -> tuple[PurchaseRequest, int, int]:
    """CR-034 — ĐIỀU PHỐI (duyệt lần 2, phía thu mua).

    Trưởng phòng duyệt xong phiếu chỉ dừng ở 'approved' và CHƯA có nhân sự phụ trách.
    Quản lý/Admin thu mua xem lại rồi bấm Điều phối: lúc này mới tự động phân bổ NSTM theo
    phân loại (logic cũ giữ nguyên, chỉ dời thời điểm) và phiếu chuyển sang 'dispatched' —
    mốc duy nhất cho phép tạo Đơn mua hàng.

    Trả về (phiếu, số dòng vừa gán tự động, số dòng vẫn chưa có người)."""
    pr = get_pr(db, pid)
    if pr.status != "approved":
        raise HTTPException(400, "Chỉ điều phối được phiếu ở trạng thái Đã duyệt "
                                 "(trưởng phòng duyệt xong, chưa điều phối).")
    from app.modules.category_assignee.service import auto_assign_by_category
    n = auto_assign_by_category(db, pr)
    con_trong = sum(1 for it in items_of(db, pid) if not (it.assignee or "").strip())
    pr.status = "dispatched"
    # bao-CR-293 (ticket 20): Ngày tiếp nhận = ngày thu mua duyệt điều phối, KHÔNG phải ngày lập
    # phiếu — thời gian quy định có hàng phải đếm từ lúc thu mua thật sự nhận việc. Dòng nào
    # "Thời gian dự kiến có hàng" vẫn là giá trị TỰ ĐIỀN theo mốc cũ thì dời theo mốc mới;
    # dòng NSTM đã sửa tay (giá trị khác bản tự điền) giữ nguyên.
    from datetime import date
    old_base = (pr.request_date or "").strip()
    new_base = date.today().isoformat()
    std = lead_time.std_days_map(db)
    for it in items_of(db, pid):
        auto_old = lead_time.regulated_date(std, it.item_group or "", old_base)
        if auto_old and (it.expected_date or "").strip() == auto_old:
            it.expected_date = lead_time.regulated_date(std, it.item_group or "", new_base)
    pr.request_date = new_base
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "dispatched",
           f"Điều phối — tự động phân bổ {n} dòng" + (f", còn {con_trong} dòng chưa có người" if con_trong else "")
           + (f" · Ngày tiếp nhận {old_base or '(trống)'} -> {new_base}" if old_base != new_base else ""))
    # Mốc gốc dời muộn hơn -> ngày QĐ có hàng dời theo, dòng "cần sớm hơn ngày QĐ" có thể phát
    # sinh mới -> soát lại cờ Đơn gấp (CR-082: chỉ BẬT, không tự tắt).
    apply_auto_urgent(db, pr, user_id, std)
    db.refresh(pr)
    return pr, n, con_trong


def assign(db: Session, pid: int, data: AssignIn, user_id: int) -> PurchaseRequest:
    """Phân bổ NSTM cho từng dòng — chạy được cả khi phiếu đã gửi duyệt (không bị khóa như sửa)."""
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed", "done"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không phân bổ được")
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
    rows = {i.id: i for i in items_of(db, pid)}
    for it in data.items:
        row = rows.get(it.id)
        if row is not None:
            row.assignee = it.assignee
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "assign", "Phân bổ NSTM")
    return pr


def urgent_reasons(std: dict, base: str, lines) -> list[str]:
    """CR-082 — các dòng có NGÀY CẦN HÀNG sớm hơn NGÀY QUY ĐỊNH của phân loại.

    Luật chốt với khách: thiếu ĐÚNG MỘT ngày cũng là gấp (cần trong 14 ngày mà phân loại quy
    định 15 ngày -> gấp), nên phép so là `<` chứ không có ngưỡng dung sai. Ngày lưu dạng
    'YYYY-MM-DD' nên so chuỗi là so đúng thứ tự thời gian.

    Bỏ qua: dòng chưa nhập ngày cần hàng, dòng đã Hủy đơn, và cả phiếu chưa có Ngày tiếp nhận
    (không có mốc gốc thì không suy ra được ngày QĐ).
    """
    if not (base or "").strip():
        return []
    out: list[str] = []
    for it in lines or []:
        want = (getattr(it, "required_date", "") or "").strip()
        if not want or (getattr(it, "line_status", "") or "") == "Hủy đơn":
            continue
        group = getattr(it, "item_group", "") or ""
        due = lead_time.regulated_date(std, group, base)
        if due and want < due:
            out.append(f'"{getattr(it, "product_name", "") or getattr(it, "product_code", "")}" '
                       f'cần {want} < ngày QĐ {due} '
                       f'(phân loại "{group or "chưa chọn"}": {lead_time.std_days_of(std, group)} ngày)')
    return out


def apply_auto_urgent(db: Session, pr: PurchaseRequest, user_id: int, std: dict | None = None) -> bool:
    """Tự BẬT cờ Đơn gấp khi có ≥1 dòng cần hàng sớm hơn thời gian quy định của phân loại.

    Chỉ bật, KHÔNG bao giờ tự tắt: cờ do người dùng bật tay (hoặc bật ở phiếu cũ) phải giữ
    nguyên, còn muốn bỏ gấp thì sửa ngày cần hàng rồi tắt tay bằng nút Đơn gấp.
    Phiếu đã hủy thì không đụng tới. Trả về True nếu vừa bật.
    """
    if pr is None or pr.is_urgent or pr.status == "cancelled":
        return False
    reasons = urgent_reasons(std if std is not None else lead_time.std_days_map(db),
                             (pr.request_date or "").strip(), items_of(db, pr.id))
    if not reasons:
        return False
    pr.is_urgent = True
    pr.updated_by = user_id
    db.commit()
    if pr.code:   # cờ gấp của YCMH đè xuống mọi ĐMH cùng pr_code (như khi bật tay)
        from app.modules.purchase_order.service import sync_urgent_group
        sync_urgent_group(db, pr.code, True)
    record(db, user_id, ENTITY, pr.id, "update",
           "Tự bật Đơn gấp — " + "; ".join(reasons[:5]))
    return True


def _save_items(db: Session, pr_id: int, items, user_id: int, auto_urgent: bool = True):
    """Upsert dòng THEO id — dòng có id thì cập nhật TẠI CHỖ (giữ nguyên id), dòng không id
    thêm mới, dòng cũ không còn trong danh sách thì xóa. GIỮ id để ảnh đối chiếu
    (đính kèm entity 'purchase_request_line_image' theo id dòng) không bị mồ côi khi lưu lại phiếu."""
    existing = {i.id: i for i in db.query(PurchaseRequestItem)
                .filter(PurchaseRequestItem.pr_id == pr_id).all()}
    # Mã hàng duy nhất trên phiếu — xem app/core/utils.assert_unique_product_codes
    assert_unique_product_codes([getattr(it, "product_code", "") for it in (items or [])],
                                [r.product_code for r in existing.values()])
    _pr = db.get(PurchaseRequest, pr_id)
    _base = (getattr(_pr, "request_date", "") or "").strip()   # Ngày tiếp nhận = mốc tính ngày QĐ
    _std = lead_time.std_days_map(db)
    keep: set[int] = set()
    for it in items or []:
        data = it.model_dump()
        rid = data.pop("id", None)
        # Task 4: thành tiền dòng GỒM VAT (qty × giá × (1 + vat%/100))
        _vp = data.get("vat_pct") or 0
        data["amount"] = round((data.get("qty") or 0) * (data.get("price") or 0) * (1 + _vp / 100), 2)
        row = existing.get(rid) if rid else None
        if row is not None:                       # cập nhật tại chỗ -> id không đổi
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_by = user_id
            keep.add(row.id)
        else:                                     # dòng mới
            # Thời gian dự kiến có hàng mặc định = NGÀY QĐ CÓ HÀNG theo phân loại
            # (Ngày tiếp nhận phiếu + số ngày QĐ; xem catalog/lead_time.py). CHỈ điền lúc TẠO
            # dòng: NSTM sửa lại sau (đổi giá trị đã có vẫn phải kèm lý do), và dòng đang sửa
            # mà người dùng cố ý xóa trắng thì giữ trắng.
            if not (data.get("expected_date") or "").strip():
                data["expected_date"] = lead_time.regulated_date(
                    _std, data.get("item_group") or "", _base)
            db.add(PurchaseRequestItem(pr_id=pr_id, created_by=user_id, updated_by=user_id, **data))
    for rid, row in existing.items():             # dòng bị bỏ khỏi danh sách -> xóa
        if rid not in keep:
            db.delete(row)
    db.flush()
    # Đồng bộ ngày cần hàng sớm nhất lên header phiếu (để lọc khoảng ngày trên CSDL chuẩn xác)
    all_req = [it.required_date for it in items_of(db, pr_id)
               if (it.required_date or "").strip() and it.line_status != "Hủy đơn"]
    if _pr:
        _pr.need_date = min(all_req) if all_req else ""
    db.commit()
    if auto_urgent:
        apply_auto_urgent(db, _pr, user_id, _std)   # CR-082 — dòng cần sớm hơn ngày QĐ -> Đơn gấp


def items_of(db: Session, pr_id: int):
    return db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id).all()


def get_pr(db: Session, pid: int) -> PurchaseRequest:
    obj = db.query(PurchaseRequest).filter(
        PurchaseRequest.id == pid,
        PurchaseRequest.is_deleted == False,
    ).first()
    if not obj:
        raise HTTPException(404, "Không tìm thấy yêu cầu mua")
    return obj


def list_pr(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(PurchaseRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def copy_pr(db: Session, pid: int, user_id: int) -> PurchaseRequest:
    """Nhân bản phiếu thành 1 phiếu Nháp mới: giữ dòng hàng, reset mã/trạng thái/NSTM/trạng thái dòng."""
    src = get_pr(db, pid)
    # NGƯỜI YÊU CẦU của bản sao = người BẤM NHÂN BẢN (không giữ người yêu cầu phiếu gốc): nếu giữ
    # nguyên thì created_by=người clone + requester=người gốc -> lệch danh + cả hai đều có quyền YC.
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    _u = db.get(User, user_id) if user_id else None
    _emp = db.get(Employee, getattr(_u, "employee_id", 0) or 0) if _u and getattr(_u, "employee_id", 0) else None
    if _emp:
        _requester, _requester_id = (_emp.full_name or ""), _emp.id
        _requester_position, _department = (_emp.position or ""), (_emp.department_name or "")
        _head_of_dept = _emp.manager_name or ""
        # CR-071: bản sao đổi phòng theo người bấm nhân bản → chỉ định TBP phải tính lại
        # theo phòng MỚI, không bê id của phiếu gốc sang.
        _head_of_dept_id = find_dept_head_id(db, _department)
    else:
        _requester, _requester_id = "", 0
        _requester_position, _department, _head_of_dept = "", src.department, src.head_of_dept
        _head_of_dept_id = src.head_of_dept_id
    pr = PurchaseRequest(
        code="", company_id=src.company_id, requester=_requester,
        requester_id=_requester_id,
        requester_position=_requester_position, department=_department,
        head_of_dept=_head_of_dept, head_of_dept_id=_head_of_dept_id,
        purpose=src.purpose, request_date=src.request_date,
        need_date=src.need_date, is_urgent=src.is_urgent, note=src.note,
        status="draft", assignee_id=0, created_by=user_id, updated_by=user_id,
        show_code_on_print=src.show_code_on_print, suggested_supplier=src.suggested_supplier,
        suggested_supplier_tax_code=src.suggested_supplier_tax_code,
        suggested_supplier_contact=src.suggested_supplier_contact,
        quote_filename=src.quote_filename, quote_file_url=src.quote_file_url,
        supplier_info=src.supplier_info or "",   # Task 4: giữ 2 cụm NCC khi nhân bản
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        from datetime import datetime
        date_str = datetime.now().strftime("%d%m%y")
        prefix = f"PYC{date_str}"
        last = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        seq = 1
        if last and last.code.startswith(prefix):
            try:
                seq = int(last.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _COPY = ["product_code", "product_name", "item_group", "group_desc", "qty", "unit",
             "price", "vat_pct", "amount", "warehouse", "required_date", "note"]
    _std = lead_time.std_days_map(db)
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _COPY}
        db.add(PurchaseRequestItem(pr_id=pr.id, created_by=user_id, updated_by=user_id,
                                   assignee="", line_status=LINE_STATUS_NO_PO, progress_note="",
                                   # Ngày dự kiến của phiếu gốc là chuyện của phiếu gốc — dòng nhân
                                   # bản khởi tạo lại theo ngày QĐ như dòng mới.
                                   expected_date=lead_time.regulated_date(
                                       _std, it.item_group, (pr.request_date or "").strip()),
                                   **data))
    db.commit()
    record(db, user_id, ENTITY, pr.id, "create", f"Nhân bản từ {src.code}")
    apply_auto_urgent(db, pr, user_id, _std)   # CR-082 — dòng nhân bản vẫn giữ ngày cần hàng cũ
    db.refresh(pr)
    return pr


def create_pr(db: Session, data: PRCreate, user_id: int, can_write_pur: bool = False) -> PurchaseRequest:
    pr = PurchaseRequest(
        code=data.code or "", company_id=data.company_id, requester=data.requester,
        requester_id=data.requester_id,
        requester_position=data.requester_position, department=data.department,
        head_of_dept=data.head_of_dept, head_of_dept_id=data.head_of_dept_id,
        purpose=data.purpose, request_date=data.request_date,
        need_date=data.need_date, is_urgent=data.is_urgent, vat_rate=data.vat_rate,
        note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        show_code_on_print=data.show_code_on_print,
        quote_filename=data.quote_filename,
        quote_file_url=data.quote_file_url,
    )
    # Task 4: NCC 2 cụm. Back-compat: body cũ gửi suggested_supplier* -> vào cụm 'req'.
    prev = {"req": {"name": data.suggested_supplier, "tax_code": data.suggested_supplier_tax_code,
                    "contact": data.suggested_supplier_contact},
            "pur": _empty_cluster(), "from_survey": False}
    apply_supplier_info(pr, build_clusters(prev, data, can_write_pur, from_survey=False))
    # Tự điền Trưởng bộ phận theo phòng ban của người yêu cầu (nếu phòng có trưởng)
    if not pr.head_of_dept_id and pr.department:
        pr.head_of_dept_id = find_dept_head_id(db, pr.department)
    sync_head_of_dept_name(db, pr)
    if not pr.head_of_dept and pr.department:
        pr.head_of_dept = find_dept_head(db, pr.department)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        date_str = ""
        if pr.request_date and len(pr.request_date) >= 10 and "-" in pr.request_date:
            parts = pr.request_date.split("-")
            if len(parts) == 3:
                date_str = f"{parts[2]}{parts[1]}{parts[0][-2:]}"
        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%d%m%y")
            
        prefix = f"PYC{date_str}"
        last_pr = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        
        seq = 1
        if last_pr and last_pr.code.startswith(prefix):
            try:
                seq = int(last_pr.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
                
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _save_items(db, pr.id, data.items, user_id)
    record(db, user_id, ENTITY, pr.id, "create")
    return pr


def update_pr(db: Session, pid: int, data: PRUpdate, user_id: int, can_write_pur: bool = False) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại "
                                 "(phiếu Đã từ chối đã khóa — hãy Nhân bản thành phiếu mới).")
    old_urgent = bool(pr.is_urgent)
    # supplier_req/supplier_pur xử lý riêng bên dưới (không phải cột của model)
    for key, value in data.model_dump(exclude_unset=True,
                                      exclude={"items", "supplier_req", "supplier_pur"}).items():
        setattr(pr, key, value)
    # Task 4: cập nhật cụm NCC (req do người yêu cầu · pur cần quyền supplier.write)
    if data.supplier_req is not None or data.supplier_pur is not None:
        apply_supplier_info(pr, build_clusters(clusters_of(pr), data, can_write_pur))
    # CR-071: đổi người duyệt chỉ định thì tên in trên phiếu phải chạy theo
    if data.head_of_dept_id is not None:
        sync_head_of_dept_name(db, pr)
    pr.updated_by = user_id
    db.commit()
    if data.items is not None:
        # CR-082: nếu chính lần lưu này là hành động TẮT cờ gấp thì đừng tự bật lại ngay —
        # người dùng vừa quyết định, hệ thống không cãi. Lần lưu sau mới xét lại.
        _save_items(db, pid, data.items, user_id,
                    auto_urgent=not (old_urgent and not bool(pr.is_urgent)))
    # Cờ Đơn gấp đổi → YCMH đè lên tất cả ĐMH cùng pr_code (đồng bộ nhóm)
    if bool(pr.is_urgent) != old_urgent and pr.code:
        from app.modules.purchase_order.service import sync_urgent_group
        sync_urgent_group(db, pr.code, bool(pr.is_urgent))
    record(db, user_id, ENTITY, pid, "update")
    db.refresh(pr)
    return pr


def set_urgent(db: Session, pid: int, is_urgent: bool, user_id: int) -> PurchaseRequest:
    """Bật/tắt cờ Đơn gấp trực tiếp (mọi trạng thái trừ đã hủy) + đồng bộ xuống các ĐMH cùng pr_code."""
    pr = get_pr(db, pid)
    if pr.status == "cancelled":
        raise HTTPException(400, "Phiếu đã hủy — không đổi được cờ Đơn gấp.")
    pr.is_urgent = bool(is_urgent)
    pr.updated_by = user_id
    db.commit()
    from app.modules.purchase_order.service import sync_urgent_group
    sync_urgent_group(db, pr.code, bool(is_urgent))
    record(db, user_id, ENTITY, pid, "update", f"Đơn gấp = {is_urgent}")
    db.refresh(pr)
    return pr


def delete_pr(db: Session, pid: int, user_id: int) -> None:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected", "cancelled"):
        raise HTTPException(400, "Chỉ xóa được phiếu ở trạng thái Nháp, Bị trả lại hoặc Đã từ chối")
    pr.is_deleted = True
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")


def set_status(db: Session, pid: int, status: str, user_id: int, message: str = "") -> PurchaseRequest:
    pr = get_pr(db, pid)
    pr.status = status
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, status, message)
    db.refresh(pr)
    return pr
