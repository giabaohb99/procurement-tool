"""Hook adapter «Nhập Excel Nhân sự» (duoc-CR-628) — prepare / apply_row / finalize / revert.

Nguyên tắc: MỌI dòng đi qua `employee.service.*_core` (cùng lõi ghi với màn hồ sơ) trong SAVEPOINT
riêng, KHÔNG `setattr` trần. Có phạm vi dữ liệu + quyền `employee.create/write`; cột nhạy cảm cần
`employee_sensitive.write`. Log KHÔNG chứa giá trị ô nhạy cảm (chỉ nêu tên cột).
"""
import logging
from dataclasses import dataclass, field

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError, PendingRollbackError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.scoping import get_perm_profile, get_scoped
from app.modules.department.model import Department
from app.modules.employee import department_service, position_role_service, position_service, service
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.schema import EmployeeCreate, EmployeeUpdate
from app.modules.user.model import User

from .catalog_import import ImportValidationError, resolve_ref_obj
from .employee_import_fields import (EMPLOYEE_FIELDS, EMPTY_SENTINEL, NOT_CLEARABLE,
                                     SENSITIVE_ATTRS, SNAPSHOT_ATTRS, CellError, cell_text,
                                     label_of, parse_scalar)
from .model import LogLevel

logger = logging.getLogger(__name__)


@dataclass
class EmployeeImportCtx:
    user: User
    profile: dict
    apply: bool
    batch_id: int
    can_create: bool
    can_write: bool
    sensitive_ok: bool
    pre_logs: list = field(default_factory=list)   # [(level, category, message)] ghi ở dòng 0
    #  Việc SAU commit: (eid, "create"|"update", notes, scope_changed, locked_users[(id, label)], code)
    after: list = field(default_factory=list)
    seen_codes: dict = field(default_factory=dict)  # mã NV (casefold) đã xử lý trong tệp -> số dòng đầu tiên (H2/L5)
    seen_ids: dict = field(default_factory=dict)    # id hồ sơ đã xử lý -> số dòng (MySQL so mã không phân biệt hoa/thường)


def prepare(db: Session, batch, field_col: dict, apply: bool) -> EmployeeImportCtx:
    """Dựng ngữ cảnh cả lô; bỏ cột nhạy cảm khỏi `field_col` nếu người nhập thiếu quyền đọc+ghi nhạy cảm."""
    user = db.get(User, batch.created_by)
    if not user or not user.is_active:
        raise ImportValidationError("Người tạo lô không còn hoạt động — không nhập Nhân sự được.")
    profile = get_perm_profile(db, user)
    perms = profile.get("perms_union") or {}
    ctx = EmployeeImportCtx(
        user=user, profile=profile, apply=apply, batch_id=batch.id,
        can_create=bool((perms.get("employee") or {}).get("create")),
        can_write=bool((perms.get("employee") or {}).get("write")),
        #  L4: ghi cột nhạy cảm cần CẢ đọc lẫn ghi (không ghi mù thứ mình không được thấy).
        sensitive_ok=bool((perms.get("employee_sensitive") or {}).get("write"))
        and bool((perms.get("employee_sensitive") or {}).get("read")))
    if not (ctx.can_create or ctx.can_write):
        raise ImportValidationError("Bạn không có quyền tạo/sửa Nhân sự.")
    if not ctx.sensitive_ok:
        dropped = [label_of(a) for a in SENSITIVE_ATTRS if field_col.get(a)]
        for a in SENSITIVE_ATTRS:
            field_col[a] = None
        if dropped:
            ctx.pre_logs.append((
                LogLevel.WARNING, "sensitive_ignored",
                "Bạn không có quyền ghi thông tin nhạy cảm — bỏ qua các cột: " + ", ".join(sorted(dropped))))
    return ctx


# ---------- tra tham chiếu ----------
def _resolve_department(db, text: str, company_id: int) -> int:
    dept = db.query(Department).filter(Department.code == text).first()
    if dept:
        return dept.id
    q = db.query(Department).filter(Department.name == text)
    if company_id:
        q = q.filter(Department.company_id == company_id)
    rows = q.limit(2).all()
    if len(rows) > 1:
        raise CellError(f"tên phòng ban '{text}' trùng nhiều phòng — dùng MÃ phòng ban")
    if not rows:
        raise CellError(f"phòng ban '{text}' không có trong danh mục")
    return rows[0].id


def _resolve_manager(db, text: str) -> int:
    emp = db.query(Employee).filter(Employee.code == text).first()
    if not emp:
        raise CellError(f"mã NV '{text}' không tồn tại (nếu ở dòng sau trong tệp, đưa dòng người quản lý lên trước)")
    return emp.id


def _build_fields(db, ctx, existing, raw: dict, log, r: int, code: str) -> dict:
    """Ô thô -> dict ghi. Ném `CellError` (đã có nhãn cột) ở lỗi đầu tiên; ô trống bị bỏ."""
    fields: dict = {}
    for spec in EMPLOYEE_FIELDS:
        attr = spec["attr"]
        if attr == "code" or attr not in raw:
            continue
        v = raw[attr]
        text = cell_text(v)
        if not text:
            continue                                  # ô trống = giữ nguyên
        try:
            if text == EMPTY_SENTINEL and attr in NOT_CLEARABLE:
                raise CellError("không xóa được ô bắt buộc")
            t = spec["t"]
            if t in ("company", "department", "position", "manager"):
                _build_ref(db, spec, text, fields, existing, log, r, code)
            else:
                fields[attr] = parse_scalar(spec, v)
        except CellError as e:
            raise CellError(f"«{label_of(attr)}»: {e}") from None
    return fields


def _build_ref(db, spec, text, fields, existing, log, r, code) -> None:
    attr, t = spec["attr"], spec["t"]
    cleared = text == EMPTY_SENTINEL
    if t == "company":
        if cleared:
            fields[attr] = 0
            return
        obj = resolve_ref_obj(db, "company", text)
        if not obj:
            raise CellError(f"'{text}' không có trong danh mục công ty")
        fields[attr] = obj.id
    elif t == "department":
        if cleared:
            fields[attr] = 0
            return
        cid = fields.get("company_id", existing.company_id if existing else 0) or 0
        fields[attr] = _resolve_department(db, text, int(cid))
    elif t == "manager":
        fields[attr] = 0 if cleared else _resolve_manager(db, text)
    else:   # position
        if cleared:
            fields["position_id"], fields["position"] = 0, ""
            return
        jp = db.query(JobPosition).filter(JobPosition.code == text).first() \
            or position_service.resolve_by_name(db, text)
        if jp:
            fields["position_id"] = jp.id
        else:
            #  Không khớp danh mục: giữ CHỮ làm chức danh VÀ bỏ gắn danh mục (position_id = 0) để hai cột
            #  không lệch nhau (M3). Gán sau lõi ghi vì `sync_label` coi 0 là «bỏ chọn» rồi xóa nhãn.
            fields["position"] = text[:100]
            fields["_free_position"] = text[:100]
            log(r, LogLevel.REVIEW, "position_not_found",
                f"«Chức vụ» = '{text}' không có trong danh mục Chức vụ — giữ làm chữ, chưa gắn danh mục",
                ref_key=code)


def _same(cur, new) -> bool:
    if cur is None:
        return new in ("", 0, None, [])
    return cur == new


def _snapshot(emp: Employee) -> dict:
    return {a: getattr(emp, a, None) for a in SNAPSHOT_ATTRS}


def snapshot_diff(before: dict, emp: Employee) -> dict:
    """H1: CHỈ các cột thật sự đổi, dạng {attr: [cũ, mới]} — hoàn tác chỉ khôi phục đúng chúng và chỉ
    khi giá trị hiện tại vẫn là «mới» (không đè lên sửa đổi về sau)."""
    after = _snapshot(emp)
    blank = ("", 0, None, [])
    return {a: [before[a], after[a]] for a in SNAPSHOT_ATTRS
            if not (before[a] == after[a] or (before[a] in blank and after[a] in blank))}


def dept_pairs(db: Session, eid: int) -> list[list]:
    """Tập phòng ban của hồ sơ `[[id, is_primary], …]` (đã sắp xếp) — để hoàn tác khôi phục ĐÚNG, kể cả phòng
    kiêm nhiệm bị hạ/gỡ khi đổi phòng chính hoặc pháp nhân (mở rộng phạm vi dữ liệu nếu để sót)."""
    rows = db.query(EmployeeDepartment).filter(EmployeeDepartment.employee_id == eid).all()
    return sorted([r.department_id, bool(r.is_primary)] for r in rows)


def _is_fatal_db_error(e: SQLAlchemyError) -> bool:
    """Deadlock (1213) / hết chờ khóa (1205) / phiên đã hỏng: KHÔNG nuốt thành lỗi dòng — transaction không còn tin
    được, phải để cả lô FAILED (L-E)."""
    if isinstance(e, PendingRollbackError):
        return True
    if isinstance(e, OperationalError):
        args = getattr(getattr(e, "orig", None), "args", None) or ()
        return bool(args) and args[0] in (1213, 1205)
    return False


def _preview_code(db: Session) -> str:
    """M2: mã NSU xem trước cho DRY-RUN — không khóa hàng (`generate_code` giữ FOR UPDATE tới hết lô)."""
    last = (db.query(Employee.code).filter(Employee.code.like("NSU%"))
            .order_by(Employee.code.desc()).first())
    try:
        return f"NSU{int(last[0][3:]) + 1:03d}"
    except (TypeError, ValueError):
        return "NSU001"


def _validation_message(e: ValidationError) -> str:
    """Ghép lỗi schema theo nhãn cột. KHÔNG kèm `input` (có thể là CCCD/STK)."""
    parts = []
    for err in e.errors(include_input=False, include_url=False):
        loc = err.get("loc") or ()
        attr = loc[0] if loc else ""
        name = label_of(attr) if attr in {f["attr"] for f in EMPLOYEE_FIELDS} else str(attr)
        msg = str(err.get("msg", "")).removeprefix("Value error, ")
        parts.append(f"«{name}»: {msg}")
    return "; ".join(parts)


def apply_row(db: Session, ctx: EmployeeImportCtx, r: int, code: str, raw: dict, log) -> dict:
    #  L5: đọc Mã NV bằng `cell_text` (giữ số 0 đầu, không biến 123 thành "123.0"), bỏ qua `code` khung truyền.
    code = cell_text(raw.get("code"))
    if code == EMPTY_SENTINEL:
        code = ""

    def fail(category: str, msg: str):
        log(r, LogLevel.ERROR, category, msg, ref_key=code, target_code=code)
        return {"outcome": "error"}

    #  H2: một mã chỉ được xuất hiện MỘT lần trong tệp (kể cả mã vừa tự sinh ở dòng trên). So không phân biệt
    #  hoa/thường (MySQL coi 'abc' = 'ABC') và theo id hồ sơ (L-C).
    key = code.casefold()
    if code and key in ctx.seen_codes:
        return fail("duplicate_code", f"Mã NV trùng dòng {ctx.seen_codes[key]} trong cùng tệp — bỏ qua dòng này")
    if code:
        ctx.seen_codes[key] = r

    existing = db.query(Employee).filter(Employee.code == code).first() if code else None
    try:
        fields = _build_fields(db, ctx, existing, raw, log, r, code)
    except CellError as e:
        return fail("invalid_cell", str(e))
    free_position = fields.pop("_free_position", None)
    if existing:
        if existing.id in ctx.seen_ids:
            return fail("duplicate_code",
                        f"Mã NV trùng dòng {ctx.seen_ids[existing.id]} trong cùng tệp — bỏ qua dòng này")
        ctx.seen_ids[existing.id] = r

    if existing:
        if not ctx.can_write:
            return fail("no_permission", "Bạn không có quyền sửa Nhân sự")
        scoped = get_scoped(db, Employee, "employee", existing.id, ctx.user, ctx.profile, "write")
        if scoped is None:
            return fail("out_of_scope", f"Mã NV '{code}' không ghi được (ngoài phạm vi dữ liệu của bạn)")
    else:
        if not ctx.can_create:
            return fail("no_permission", "Bạn không có quyền tạo Nhân sự mới")
        if not fields.get("full_name"):
            return fail("missing_required", "Thiếu «Họ tên» — không tạo được nhân sự mới")

    #  Phòng ban ĐỔI THẬT: cùng hai chốt L1/L2 với PATCH hồ sơ (bao-CR-507).
    new_dept = fields.get("department_id")
    if new_dept is not None and new_dept != int((existing.department_id if existing else 0) or 0):
        try:
            if existing:
                department_service.block_edit_own_department(db, existing.id, ctx.user)
            department_service.block_out_of_scope_departments(db, [new_dept], ctx.user, ctx.profile)
        except HTTPException as e:
            return fail("department_denied", str(e.detail))

    if existing:
        changed = {k: v for k, v in fields.items() if not _same(getattr(existing, k, None), v)}
        pos_changed = free_position is not None and (existing.position_id or existing.position != free_position)
        if not changed and not pos_changed:
            return {"outcome": "unchanged", "code": code}
        fields = changed

    try:
        payload = (EmployeeUpdate(**fields) if existing
                   else EmployeeCreate(**{**fields, **({"code": code} if code else {})}))
    except ValidationError as e:
        return fail("invalid_value", _validation_message(e))
    #  Dòng mới không mã: xem trước mã không khóa ở chạy thử (M2); ghi thật để lõi sinh mã (có khóa).
    if not existing and not code and not ctx.apply:
        payload.code = _preview_code(db)

    before = _snapshot(existing) if existing else None
    before_depts = dept_pairs(db, existing.id) if existing else None
    try:
        with db.begin_nested():
            if existing:
                out = service.update_employee_core(db, existing, payload, ctx.user.id,
                                                   lock_users=ctx.apply)
                obj = existing
            else:
                obj = service.create_employee_core(db, payload, ctx.user.id)
                out = None
            if free_position is not None:
                old_pos_id = obj.position_id or 0
                obj.position_id, obj.position = 0, free_position
                if existing and old_pos_id:
                    #  duoc-CR-653: chức vụ chữ tự do = bỏ chọn danh mục → thu hồi vai trò tự cấp theo chức vụ cũ.
                    position_role_service.sync_employee_roles(db, obj, ctx.user.id, "nhập Excel")
            db.flush()
            db.refresh(obj, ["updated_at"])     # M-B: dấu thời gian cùng đồng hồ DB, để hoàn tác biết «bị sửa sau»
            #  Kiểm phạm vi SAU ghi: đổi công ty/phòng ban mà đẩy hồ sơ ra khỏi tầm nhìn của chính người nhập
            #  thì lùi savepoint (không tạo hồ sơ "mồ côi").
            if get_scoped(db, Employee, "employee", obj.id, ctx.user, ctx.profile,
                          "write" if ctx.can_write else "create") is None:
                raise HTTPException(403, "sau khi ghi, hồ sơ nằm ngoài phạm vi dữ liệu của bạn")
    except HTTPException as e:
        return fail("rejected", str(e.detail))
    except ValueError as e:
        return fail("rejected", str(e))
    except SQLAlchemyError as e:
        if _is_fatal_db_error(e):
            raise
        #  H4: thông báo SQLAlchemy kèm câu lệnh + THAM SỐ (CCCD/STK) — chỉ nêu tên lớp lỗi, chi tiết vào log máy chủ.
        logger.error("Nhập Excel nhân sự lô #%s dòng %s: %s", ctx.batch_id, r, type(e).__name__, exc_info=True)
        return fail("db_error", f"Lỗi cơ sở dữ liệu khi ghi dòng này ({type(e).__name__}) — dòng bị bỏ qua")

    if out is not None and out.left_company and not ctx.apply:
        log(r, LogLevel.WARNING, "will_lock_user",
            f"Sẽ khóa tài khoản đăng nhập của {obj.code} khi ghi thật", ref_key=obj.code, target_code=obj.code)
    ctx.seen_codes[obj.code.casefold()] = r
    ctx.seen_ids[obj.id] = r
    ctx.after.append((obj.id, "update" if existing else "create",
                      "; ".join(out.notes) if out else "",
                      out.scope_changed if out else False,
                      [(u.id, u.email or str(u.id)) for u in (out.locked_users if out else [])],
                      obj.code))
    if existing:
        snap = snapshot_diff(before, obj)
        after_depts = dept_pairs(db, obj.id)
        if after_depts != before_depts:
            snap["_depts"] = [before_depts, after_depts]
    else:
        snap = {"_stamp": obj.updated_at.isoformat() if obj.updated_at else ""}
    return {"outcome": "updated" if existing else "created", "target_id": obj.id,
            "snapshot": snap, "code": obj.code}


def finalize(db: Session, ctx: EmployeeImportCtx) -> None:
    """Sau commit: nhật ký thao tác + xóa cache quyền (như `update_employee` công khai)."""
    from app.core.audit import record

    for eid, action, notes, scope_changed, locked, code in ctx.after:
        record(db, ctx.user.id, service.ENTITY, eid, action,
               f"Nhập Excel lô #{ctx.batch_id}" + (f"; {notes}" if notes else ""))
        for uid, label in locked:
            record(db, ctx.user.id, "user", uid, "deactivate",
                   f"Khóa tài khoản {label} vì hồ sơ nhân sự {code} nghỉ việc (nhập Excel lô #{ctx.batch_id})")
        if scope_changed:
            service.clear_perm_cache_of(db, eid)
