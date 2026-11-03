"""YCMH — phòng ban của phiếu: phòng lập, phòng xử lý, trưởng phòng phê duyệt (bao-CR-715 tách từ service.py)."""
from sqlalchemy.orm import Session

from app.core.central_purchasing import central_dept_ids, get_central_dept_id, normalize_handler_dept_id

from .model import PurchaseRequest
from .base_service import ENTITY


def find_dept_head(db: Session, department_name: str = "", department_id: int = 0) -> str:
    """Tên Trưởng bộ phận của 1 phòng ban (theo field manager_id chọn cứng). '' nếu chưa gán.

    CR-086: truyền được `department_id` thì dùng id; chỉ phiếu cũ chưa có id mới dò theo tên."""
    from app.modules.employee.model import Employee
    dep = _find_dept(db, department_name, department_id)
    if not dep or not dep.manager_id:
        return ""
    head = db.get(Employee, dep.manager_id)
    return head.full_name if head else ""


def find_dept_head_id(db: Session, department_name: str = "", department_id: int = 0) -> int:
    """Id NHÂN SỰ của Trưởng bộ phận theo `Department.manager_id`. 0 = chưa gán."""
    dep = _find_dept(db, department_name, department_id)
    return int(dep.manager_id or 0) if dep else 0


def fill_department_from_employee(db: Session, pr: PurchaseRequest, user_id: int) -> None:
    """Phiếu chưa có phòng ban thì lùi về phòng trong HỒ SƠ NHÂN SỰ — bao-CR-465.

    Chốt an toàn cuối cùng, cố ý đặt ở backend chứ không chỉ vá màn hình: phòng ban là
    thứ quyết định ai nhìn thấy phiếu (phạm vi `dept` của `core/scoping.py` lọc theo cột
    `department_id`), nên phiếu rỗng phòng ban là phiếu KHÔNG AI DUYỆT ĐƯỢC và không ai
    nhận được thư — một lỗi câm, người lập không hề biết. Giao diện cũ từng để lọt đúng
    ca đó vì tra tên phòng trong một danh sách nạp song song; vá ở đây thì mọi đường vào
    (giao diện cũ, giao diện mới, gọi thẳng API) đều được che, không riêng một màn hình.

    Nguồn ưu tiên là nhân sự ĐỨNG TÊN yêu cầu, không phải người bấm nút: hành chính lập hộ
    cho phòng khác thì phòng của phiếu phải là phòng người được lập hộ. Không suy ra được
    thì để nguyên rỗng — đoán bừa một phòng còn tệ hơn để trống, vì phiếu sẽ rơi vào tầm
    mắt của một trưởng phòng không liên quan.

    Không đụng tới phiếu ĐÃ có phòng ban: người lập chọn tay thì tiếng nói của họ là cuối.
    """
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    if int(getattr(pr, "department_id", 0) or 0) or (pr.department or "").strip():
        return
    emp = None
    if int(getattr(pr, "requester_id", 0) or 0):
        emp = db.get(Employee, pr.requester_id)
    if not emp and user_id:
        user = db.get(User, user_id)
        if user and user.employee_id:
            emp = db.get(Employee, user.employee_id)
    if not emp or not emp.department_id:
        return
    pr.department_id = emp.department_id
    pr.department = emp.department_name or ""


def list_self_purchasing_dept_ids(db: Session) -> set[int]:
    """Các phòng TỰ MUA HÀNG — bao-CR-480.

    Một phòng là phòng tự mua khi có người đang hoạt động giữ vai trò thu mua bậc
    `dept_proc` trên yêu cầu mua hàng (vai trò "Quản lý thu mua phòng" của bao-CR-414).
    Suy từ phân quyền thay vì thêm một ô cấu hình: chính phân quyền là thứ đã quyết
    "phòng này có bộ máy mua riêng" — lập một bộ tài khoản cho nhà máy là nhà máy tự
    mua, gỡ hết là thôi, không có chỗ thứ hai để hai bên lệch nhau.
    """
    from app.modules.employee.model import Employee
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole

    rows = (db.query(Employee.department_id)
            .join(User, User.employee_id == Employee.id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Permission, Permission.role_id == UserRole.role_id)
            .filter(Permission.entity == ENTITY, Permission.scope == "dept_proc",
                    User.is_active == True, Employee.department_id != 0)  # noqa: E712
            .distinct().all())
    return {int(r[0]) for r in rows}


def default_handler_dept_id(db: Session, department_id: int) -> int:
    """Phòng xử lý mặc định lúc LẬP phiếu — bao-CR-480, đổi ở bao-CR-524.

    Người của phòng tự mua hàng lập phiếu thì phòng xử lý là chính phòng họ; ai khác thì là
    PHÒNG THU MUA MẶC ĐỊNH (bao-CR-524: id thật của mã PBA017 "Sản xuất -Thu mua", trước đó là
    `0` = "Thu mua chung" ảo; danh mục chưa có phòng đó thì vẫn `0`). Chỉ áp lúc tạo mới: sau đó
    người lập đổi phòng xử lý là lựa chọn có chủ ý, cửa cập nhật không được tra đè.

    Vì sao phải mặc định: từ CR-480 bộ thu mua chung loại trừ theo PHÒNG XỬ LÝ, nên phiếu
    nhà máy mà quên chọn phòng xử lý là phiếu rơi vào tầm mắt thu mua chung — đúng thứ
    nhà máy muốn tránh (bao-CR-414: nhà máy tự mua vì sợ lộ công thức).
    """
    dept_id = int(department_id or 0)
    if dept_id and dept_id in list_self_purchasing_dept_ids(db):
        return dept_id
    return get_central_dept_id(db)


def backfill_handling_dept(db: Session, dept_ids: set[int] | None = None,
                           dry_run: bool = False) -> dict[str, int]:
    """Chuyển đổi phiếu CŨ của phòng tự mua hàng sang luật bao-CR-480 — chạy lại được.

    Trước CR-480, phiếu của nhà máy "không nhờ ai" (`handler_dept_id = 0`) ngầm hiểu là
    nhà máy tự lo. Từ CR-480, `0` nghĩa là THU MUA CHUNG xử lý — nên phiếu cũ của phòng tự
    mua nếu để nguyên sẽ (1) hiện "Thu mua chung" sai sự thật và (2) lọt vào tầm mắt bộ thu
    mua chung, đúng thứ nhà máy muốn tránh. Hàm này gán lại phòng xử lý = phòng lập cho
    YCMH · YCBG · ĐMH có `handler_dept_id = 0` mà phòng lập là phòng tự mua; phiếu rỗng
    phòng ban thì tra hồ sơ nhân sự của người yêu cầu (ĐMH thì theo YCMH nguồn).

    ⚠️ Phải chạy MỖI KHI một phòng vừa được cấp bộ máy mua riêng (vai trò "Quản lý thu mua
    phòng") — xem bài HDSD "Lập bộ tài khoản phòng tự mua hàng". Không tự chạy lúc khởi động:
    phiếu nhà máy đã chủ động chọn "Thu mua chung" sau CR này cũng mang `0`, chạy tự động
    là lật ngược lựa chọn đó mỗi lần deploy. Trả `{bảng: số dòng đã đổi}`.
    """
    from app.modules.employee.model import Employee
    from app.modules.purchase_order.model import PurchaseOrder
    from app.modules.survey_request.model import SurveyRequest

    targets = set(dept_ids) if dept_ids is not None else list_self_purchasing_dept_ids(db)
    counts = {"purchase_request": 0, "survey_request": 0, "purchase_order": 0}
    if not targets:
        return counts
    # bao-CR-524: phiếu "thu mua chung" nay mang id phòng thu mua mặc định chứ không chỉ `0` —
    # quét cả hai để chạy lại hàm này sau backfill CR-524 vẫn cho đúng kết quả như trước.
    central_values = list(central_dept_ids(db))

    def _dept_of_requester(requester_id: int) -> tuple[int, str]:
        emp = db.get(Employee, int(requester_id or 0)) if requester_id else None
        if not emp or not emp.department_id:
            return 0, ""
        return int(emp.department_id), emp.department_name or ""

    for model, key in ((PurchaseRequest, "purchase_request"), (SurveyRequest, "survey_request")):
        #  ai-CR-170: cả hai model đều xóa mềm — phiếu đã xóa không đụng tới.
        for row in db.query(model).filter(model.handler_dept_id.in_(central_values),
                                          model.is_deleted == False).all():   # noqa: E712
            dept_id = int(row.department_id or 0)
            if not dept_id:
                dept_id, dept_name = _dept_of_requester(getattr(row, "requester_id", 0))
                if dept_id in targets and not dry_run:
                    row.department_id, row.department = dept_id, dept_name
            if dept_id not in targets or dept_id == int(row.handler_dept_id or 0):
                continue
            counts[key] += 1
            if not dry_run:
                row.handler_dept_id = dept_id
    for po in db.query(PurchaseOrder).filter(PurchaseOrder.handler_dept_id.in_(central_values),
                                             PurchaseOrder.is_deleted == False).all():   # noqa: E712 — ai-CR-176
        dept_id = int(po.department_id or 0)
        if not dept_id and (po.pr_code or "").strip():
            src = db.query(PurchaseRequest).filter(PurchaseRequest.code == po.pr_code).first()
            dept_id = int(src.handler_dept_id or src.department_id or 0) if src else 0
        if dept_id not in targets or dept_id == int(po.handler_dept_id or 0):
            continue
        counts["purchase_order"] += 1
        if not dry_run:
            po.handler_dept_id = dept_id
    if not dry_run:
        db.commit()
    return counts


def handler_dept_name_of(db: Session, handler_dept_id: int) -> str:
    """Tên phòng xử lý để HIỂN THỊ. bao-CR-524: `0` cũ (chưa backfill) = phòng thu mua mặc định
    nên trả tên phòng đó; chỉ khi danh mục chưa có phòng mặc định mới trả rỗng."""
    dept_id = normalize_handler_dept_id(db, handler_dept_id)
    dep = _find_dept(db, "", dept_id) if dept_id else None
    return dep.name if dep else ""


def resolve_employee_department(db: Session, requester_id: int) -> tuple[int, str]:
    """`(id, tên)` phòng trong HỒ SƠ NHÂN SỰ của người yêu cầu — bao-CR-480.

    Chỉ để hiển thị phiếu cũ còn rỗng ô Phòng ban (lập trước bao-CR-465); ghi xuống phiếu
    vẫn là việc của `fill_department_from_employee` lúc lưu / gửi duyệt.
    """
    from app.modules.employee.model import Employee
    emp = db.get(Employee, int(requester_id or 0)) if requester_id else None
    if not emp or not emp.department_id:
        return 0, ""
    return int(emp.department_id), emp.department_name or ""


def _find_dept(db: Session, department_name: str = "", department_id: int = 0):
    """Phòng ban theo id (ưu tiên) hoặc theo tên (đường lùi cho phiếu chưa điền lùi được id)."""
    from app.modules.department.model import Department
    if department_id:
        dep = db.get(Department, department_id)
        if dep:
            return dep
    name = (department_name or "").strip()
    if not name:
        return None
    return db.query(Department).filter(Department.name == name).first()


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
        return complete_head_choices(db, [], int(pr.department_id or 0))
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
    return complete_head_choices(db, out, int(pr.department_id or 0))


def complete_head_choices(db: Session, rows: list[dict], department_id: int) -> list[dict]:
    """bao-CR-552 — ô "Trưởng bộ phận (TBP) / Người liên hệ" LUÔN chọn được.

    Danh sách gốc chỉ có người duyệt theo phạm vi phòng; phòng không có ai như vậy (vd "Lập trình &
    IT nội bộ") thì rỗng và hai giao diện khóa cứng ô TBP — đại ca báo lỗi 01/10/2026. Luôn kèm trưởng
    phòng của phòng lập; vẫn rỗng thì đưa trưởng phòng mọi phòng (đúng bộ ô TBP của YCBG).
    """
    from app.core.approver_candidates import department_managers, get_department_head_id
    from app.modules.employee.model import Employee
    out = list(rows)
    head_id = get_department_head_id(db, department_id)
    if head_id and all(r["employee_id"] != head_id for r in out):
        e = db.get(Employee, head_id)
        if e and e.status != "resigned":
            out.append({"employee_id": e.id, "name": e.full_name or "", "code": e.code or "",
                        "position": e.position or ""})
    if not out:
        out = department_managers(db)
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
    _dep = _find_dept(db, department, 0)
    _dep_id = int(_dep.id) if _dep else 0
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
        return complete_head_choices(db, [], _dep_id)
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
    return complete_head_choices(db, out, _dep_id)


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
    """Ghi kép ô Trưởng bộ phận: có id thì tên chạy theo id, chỉ có tên thì tra ngược ra id.

    CR-087 gom về `employee.service.sync_employee_ref` — YCMH / YCBG / ĐMH dùng chung một
    đường, khỏi mỗi nơi một kiểu. Trước đây hàm này chỉ chạy chiều id → tên, nên phiếu gửi
    lên chỉ có tên mà phòng chưa có trưởng thì `head_of_dept_id` nằm 0 vĩnh viễn — đúng món
    nợ mà migration `d5b2f9c31a08` vừa điền lùi xong.
    """
    from app.modules.employee.service import sync_employee_ref
    sync_employee_ref(db, pr, "head_of_dept_id", "head_of_dept")
