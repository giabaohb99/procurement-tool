"""Hoàn tác lô "Nhập Excel Nhân sự" (duoc-CR-628, vòng review).

Bản chụp mỗi bản ghi SỬA là `{attr: [cũ, mới]}` — CHỈ cột thật sự đổi. Hoàn tác khôi phục từng cột về
"cũ" chỉ khi giá trị hiện tại vẫn là "mới"; có cột đã bị sửa về sau thì TỪ CHỐI CẢ LƯỢT (nêu mã + tên cột,
KHÔNG nêu giá trị vì có thể là CCCD/STK). Quyền + phạm vi kiểm CHO TỪNG dòng trước khi đụng gì.
"""
import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import reference_guard
from app.core.scoping import get_perm_profile, get_scoped
from app.modules.employee import department_service, position_role_service, service
from app.modules.employee.contact_model import EmployeeContact, EmployeeFamily
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.user.model import User

from .employee_import import dept_pairs
from .employee_import_fields import DATE_ATTRS, SENSITIVE_ATTRS, label_of

_MANAGER_REF_LABEL = "nhân sự do người này quản lý"
_PENDING_KEY = "employee_revert_after"


def _norm(attr: str, v):
    """So sánh giá trị hiện tại với giá trị trong bản chụp (đã qua JSON). Chuẩn hóa NGÀY chỉ cho cột ngày (L-B)."""
    if v is None:
        return ""
    if attr in DATE_ATTRS:
        return v.isoformat() if isinstance(v, date) else str(v)[:10]
    return v


def _cols(ch) -> dict:
    try:
        return json.loads(ch.snapshot).get("cols", {}) if ch.snapshot else {}
    except ValueError:
        return {}


def _reference_problem(db: Session, emp: Employee, allowed_subordinates: set[int]) -> str | None:
    """Còn chỗ tham chiếu? Chỉ BỎ QUA cấp dưới do chính lô này tạo / gán quản lý là hồ sơ này (L-A)."""
    refs = []
    for label, n in reference_guard.count_references(db, service.ENTITY, emp):
        if label == _MANAGER_REF_LABEL:
            q = db.query(Employee).filter(Employee.manager_id == emp.id)
            if allowed_subordinates:
                q = q.filter(Employee.id.notin_(allowed_subordinates))
            n = q.count()
        if n:
            refs.append(label)
    return f"còn được dùng ở: {', '.join(refs)}" if refs else None


def _child_problem(db: Session, emp: Employee, stamp: str) -> str | None:
    """M4/M-B: dữ liệu con thêm vào SAU khi nhập, hoặc hồ sơ bị sửa sau (dấu `updated_at` lúc nhập đã đổi)."""
    from app.modules.labor_contract.model import LaborContract

    found = []
    for label, model in (("liên hệ", EmployeeContact), ("người thân", EmployeeFamily),
                         ("quá trình công tác", EmployeeWorkHistory), ("hợp đồng lao động", LaborContract)):
        if db.query(model).filter(model.employee_id == emp.id).count():
            found.append(label)
    extra = db.query(EmployeeDepartment).filter(EmployeeDepartment.employee_id == emp.id,
                                                EmployeeDepartment.department_id != (emp.department_id or 0)).count()
    if extra:
        found.append("phòng kiêm nhiệm")
    if found:
        return "đã có thêm dữ liệu sau khi nhập: " + ", ".join(found)
    if not stamp or not emp.updated_at or emp.updated_at.isoformat() != stamp:
        return "hồ sơ đã được chỉnh sửa sau khi nhập"
    return None


def _label(attr: str) -> str:
    return {"position": "Chức vụ", "_depts": "Phòng ban kiêm nhiệm"}.get(attr) or label_of(attr)


def revert_blockers(db: Session, changes, user_id: int, batch=None) -> list[str]:
    """Danh sách lý do TỪ CHỐI cả lượt hoàn tác (rỗng = được)."""
    from app.modules.labor_contract import service as labor_contract_service

    user = db.get(User, user_id)
    if not user:
        return ["Không xác định được người hoàn tác"]
    profile = get_perm_profile(db, user)
    perms = profile.get("perms_union") or {}
    can = lambda ent, act: bool((perms.get(ent) or {}).get(act))      # noqa: E731
    sensitive_ok = can("employee_sensitive", "write") and can("employee_sensitive", "read")
    new_ids = {ch.survey_id for ch in changes if ch.was_new}
    #  Cấp dưới được phép khi xét xóa người quản lý: (a) nhân sự do lô tạo, (b) hồ sơ cũ mà lô GÁN quản lý = người này.
    set_manager_of: dict[int, set[int]] = {}
    for ch in changes:
        if not ch.was_new:
            pair = _cols(ch).get("manager_id")
            if pair and pair[1]:
                set_manager_of.setdefault(int(pair[1]), set()).add(ch.survey_id)
    problems: list[str] = []

    for ch in changes:
        emp = db.get(Employee, ch.survey_id)
        if not emp:
            continue
        code = emp.code
        #  H3: quyền + phạm vi cho TỪNG dòng.
        if not can("employee", "write") or get_scoped(db, Employee, "employee", emp.id, user, profile, "write") is None:
            problems.append(f"{code}: bạn không có quyền sửa hồ sơ này (thiếu quyền hoặc ngoài phạm vi)")
            continue
        if ch.was_new:
            if not can("employee", "delete") or \
                    get_scoped(db, Employee, "employee", emp.id, user, profile, "delete") is None:
                problems.append(f"{code}: bạn không có quyền xóa hồ sơ này (thiếu quyền hoặc ngoài phạm vi)")
                continue
            stamp = _cols(ch).get("_stamp", "")
            why = _child_problem(db, emp, stamp) or _reference_problem(
                db, emp, new_ids | set_manager_of.get(emp.id, set()))
            if not why:
                try:
                    labor_contract_service.ensure_employee_deletable(db, emp.id)
                except HTTPException as e:
                    why = str(e.detail)
            if not why and db.query(User.id).filter(User.employee_id == emp.id).first():
                why = "đã gắn tài khoản đăng nhập"
            if why:
                problems.append(f"{code}: {why}")
            continue
        cols = _cols(ch)
        sens = [a for a in cols if a in SENSITIVE_ATTRS]
        if sens and not sensitive_ok:
            problems.append(f"{code}: cần quyền đọc+ghi thông tin nhạy cảm để hoàn tác cột "
                            + ", ".join(label_of(a) for a in sens))
            continue
        conflict = [a for a, pair in cols.items()
                    if a not in ("_depts", "_stamp") and _norm(a, getattr(emp, a, None)) != _norm(a, pair[1])]
        depts = cols.get("_depts")
        if depts and dept_pairs(db, emp.id) != depts[1]:
            conflict.append("_depts")
        if conflict:
            problems.append(f"{code}: đã bị sửa sau khi nhập ở cột " + ", ".join(
                _label(a) for a in conflict))
            continue
        #  M-A: hoàn tác đổi phòng ban/pháp nhân cũng phải qua L1/L2 như lúc nhập.
        if depts or "department_id" in cols or "company_id" in cols:
            old_ids = [d for d, _ in (depts[0] if depts else [])] or \
                      ([cols["department_id"][0]] if cols.get("department_id") and cols["department_id"][0] else [])
            try:
                department_service.block_edit_own_department(db, emp.id, user)
                department_service.block_out_of_scope_departments(db, old_ids, user, profile)
            except HTTPException as e:
                problems.append(f"{code}: {e.detail}")
    return problems


def revert(db: Session, changes, user_id: int) -> tuple[int, int]:
    """Mới -> xóa (lõi xóa, dọn bảng con); cũ -> khôi phục các cột đã đổi. Duyệt `changes` theo thứ tự đã
    được `revert_batch` sắp xếp (id GIẢM DẦN): cấp dưới tạo sau được xóa trước người quản lý tạo trước.

    ⚠️ KHÔNG mở lại tài khoản đã bị khóa vì nghỉ việc: "quay lại làm" là quyết định tay (bao-CR-400).
    Nhật ký + xóa cache quyền chạy SAU commit qua `after_revert`."""
    deleted = restored = 0
    pending = db.info.setdefault(_PENDING_KEY, [])
    for ch in changes:
        emp = db.get(Employee, ch.survey_id)
        if not emp:
            continue
        code = emp.code
        if ch.was_new:
            service.delete_employee_core(db, ch.survey_id, user_id)
            pending.append((ch.survey_id, "delete", f"Hoàn tác lô nhập Excel #{ch.batch_id}: xóa {code}", False, [], code))
            deleted += 1
            continue
        cols = _cols(ch)
        cols.pop("_stamp", None)
        depts = cols.pop("_depts", None)
        if not cols and not depts:
            continue
        old = {a: pair[0] for a, pair in cols.items()}
        for a in DATE_ATTRS:
            if a in old:
                v = old[a]
                old[a] = date.fromisoformat(v[:10]) if isinstance(v, str) and v else None
        #  Chức vụ khôi phục TRỰC TIẾP (id + nhãn): qua `sync_label` sẽ chặn chức vụ đã ngừng dùng.
        pos_id, pos_label = old.pop("position_id", None), old.pop("position", None)
        data = EmployeeUpdate.model_construct(_fields_set=set(old), **old)
        try:
            #  lock_users=True (chốt sản phẩm): hoàn tác về "nghỉ việc / ngưng dùng" thì khóa lại tài khoản.
            out = service.update_employee_core(db, emp, data, user_id, lock_users=True)
            if depts:
                #  Khôi phục CHÍNH XÁC tập phòng ban (cả phòng kiêm nhiệm bị hạ/gỡ), tránh để lại phạm vi rộng hơn.
                before = depts[0]
                primary = next((d for d, is_primary in before if is_primary), None)
                department_service.set_departments(db, emp, [d for d, _ in before], user_id,
                                                   primary_department=primary)
        except HTTPException as e:
            raise HTTPException(400, f"Không hoàn tác được {code}: {e.detail}") from None
        if pos_id is not None:
            emp.position_id = pos_id or 0
        if pos_label is not None:
            emp.position = pos_label or ""
        if pos_id is not None:
            position_role_service.sync_employee_roles(db, emp, user_id, "hoàn tác lô nhập")
        pending.append((emp.id, "update", f"Hoàn tác lô nhập Excel #{ch.batch_id}",
                        out.scope_changed or bool(depts), [(u.id, u.email or str(u.id)) for u in out.locked_users], code))
        db.flush()          # để chốt tham chiếu của lần xóa kế tiếp thấy trạng thái đã khôi phục
        restored += 1
    db.flush()
    return deleted, restored


def after_revert(db: Session, batch, user_id: int) -> None:
    """SAU commit: nhật ký từng nhân sự (+ từng tài khoản bị khóa lại) + xóa cache quyền (M5/M-C).

    Lưu ý (L-D): `perm_cache_clear` chỉ xóa bộ nhớ của TIẾN TRÌNH hiện tại; các worker/process khác tự hết hạn sau
    ≤ 60 giây — cùng giới hạn với mọi đường sửa phạm vi dữ liệu khác."""
    from app.core.audit import record

    for eid, action, msg, scope_changed, locked, code in db.info.pop(_PENDING_KEY, []):
        record(db, user_id, service.ENTITY, eid, action, msg)
        for uid, label in locked:
            record(db, user_id, "user", uid, "deactivate",
                   f"Khóa tài khoản {label} vì hồ sơ nhân sự {code} về nghỉ việc (hoàn tác lô nhập Excel #{batch.id})")
        if scope_changed and action == "update":
            service.clear_perm_cache_of(db, eid)
