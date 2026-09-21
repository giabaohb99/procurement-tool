"""Tool lập BỘ TÀI KHOẢN thu mua qua Trợ lý AI (bao-CR-435) — tầng GHI có xác nhận.

Ra đời từ hướng dẫn `doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md`:
mỗi tài khoản đi qua bốn bước bấm tay, bộ B còn phải mở hộp Phạm vi tìm đúng ô «Loại trừ
phòng ban». Tool này gom Bước 3 (gán vai trò) + Bước 4 (phạm vi) thành MỘT đề xuất:

  · DÒ TRƯỚC: hồ sơ nhân sự có chưa · đã có tài khoản đăng nhập chưa · đang giữ vai trò
    gì · ô phạm vi của từng vai trò đang ghi gì;
  · ĐỀ XUẤT từng dòng «thêm / bỏ / không đổi» — chạy lại y nguyên thì mọi dòng «không đổi»;
  · NGƯỜI bấm *Xác nhận* thì `confirm_account_setup` mới ghi, qua ĐÚNG hai service của màn
    Phân quyền tài khoản (`assign_roles` + `set_user_scope`) nên nhật ký, xóa cache quyền và
    ba chốt chống tự nâng quyền (`core/privilege_escalation`) ăn nguyên.

Tool KHÔNG làm — cố ý, đừng nới:
  · không tạo hồ sơ nhân sự, không tạo tài khoản đăng nhập, không đụng mật khẩu (Bước 1-2 vẫn
    bấm tay; chưa có tài khoản thì đề xuất DỪNG và nói rõ);
  · không tạo vai trò mới — chỉ gán vai trò CÓ SẴN trong bộ mẫu `TEMPLATE_ROLE_CODES`
    (tạo vai trò theo yêu cầu khách là đợt 2, chưa làm);
  · không khai «Chỉ trong công ty» (bao-CR-434: pháp nhân trên hồ sơ chỉ là chuyện pháp lý,
    phòng nhà máy mua cho nhiều pháp nhân). Ngược lại có thể GỠ dòng đó khi được bảo.

Quyền: chạy dưới danh tính người hỏi, đòi `user.write` (cửa ghi thật của màn Phân quyền)
+ `role.read` + `employee.read`; kiểm ở cả hai bước, tài khoản đích phải nằm trong phạm vi
`user` của người hỏi (B-07), và L1/L2 của `privilege_escalation` áp y như bấm trên màn.
"""
import json

from cryptography.fernet import InvalidToken
from fastapi import HTTPException
from sqlalchemy import func

from app.core import privilege_escalation
from app.core.auth import get_perm_profile, user_has_permission
from app.core.scoping import apply_scope, get_scoped
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user import service as user_service
from app.modules.user.model import User
from app.modules.user.schema import RoleAssign, ScopeUpdate

from .base import ToolContext, ToolSpec
from .update_tool import CONFIRM_TTL_SECONDS, _fernet

PROPOSAL_KIND = "account_setup_proposal"

#  Bộ vai trò mẫu của hướng dẫn 20 — tool chỉ gán trong tập này. Quản trị hệ thống, kế toán,
#  HR... không gán qua chat: một câu gõ nhầm không được thành một cú phong quyền.
TEMPLATE_ROLE_CODES = ("employee", "dept_head", "pur_staff", "pur_manager",
                       "pur_dept_manager", "pur_admin")
PURCHASING_ROLE_CODES = frozenset({"pur_staff", "pur_manager", "pur_dept_manager", "pur_admin"})

REQUIRED_PERMS = (("user", "write"), ("role", "read"), ("employee", "read"))

MAX_CANDIDATES = 6
USER_PERMISSION_URL = "/system/permissions/users/{user_id}"

_DESC = (
    "Lập / chỉnh BỘ TÀI KHOẢN thu mua cho MỘT nhân sự: gán vai trò có sẵn (employee, "
    "dept_head, pur_staff, pur_manager, pur_dept_manager, pur_admin) và khai ô «Loại trừ "
    "phòng ban» (ví dụ bộ Thu mua trừ nhà máy: loại trừ Dego Organic). Tool CHỈ ĐỀ XUẤT: dò "
    "hồ sơ, tài khoản, vai trò và phạm vi hiện có rồi trả bảng từng dòng thêm / bỏ / không "
    "đổi kèm nút Xác nhận — hệ thống chỉ ghi khi NGƯỜI DÙNG bấm nút. KHÔNG tạo hồ sơ nhân "
    "sự, KHÔNG tạo tài khoản đăng nhập, KHÔNG đụng mật khẩu, KHÔNG tạo vai trò mới. Chạy "
    "lại cùng yêu cầu thì mọi dòng «không đổi». Chưa có tài khoản đăng nhập thì trả blocked "
    "kèm hướng dẫn tạo tay."
)

_PARAMS = {
    "type": "object",
    "properties": {
        "employee": {
            "type": "string",
            "description": "Mã nhân viên, họ tên hoặc email đăng nhập của người cần lập tài khoản.",
        },
        "role_codes": {
            "type": "array",
            "items": {"type": "string", "enum": list(TEMPLATE_ROLE_CODES)},
            "description": "Mã vai trò cần có. employee = nhân sự lập phiếu; dept_head = trưởng "
                           "phòng duyệt; pur_staff = nhân viên thu mua; pur_manager = quản lý thu "
                           "mua toàn quyền; pur_dept_manager = quản lý thu mua CỦA PHÒNG (phòng tự "
                           "mua hàng); pur_admin = admin thu mua.",
        },
        "replace_roles": {
            "type": "boolean",
            "description": "true = tài khoản chỉ còn đúng các vai trò trong role_codes (bỏ vai trò "
                           "khác đang giữ); false (mặc định) = chỉ THÊM, giữ vai trò đang có.",
        },
        "exclude_departments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tên phòng ban cần LOẠI TRỪ khỏi phạm vi của các vai trò trong role_codes "
                           "(bộ Thu mua trừ nhà máy: [\"Dego Organic\"]). Bộ Nhà máy để trống.",
        },
        "remove_company_include": {
            "type": "boolean",
            "description": "true = gỡ dòng «Chỉ trong công ty» đang có ở các vai trò trong role_codes "
                           "(bao-CR-434: bộ thu mua KHÔNG nên nhốt theo pháp nhân). Mặc định false: "
                           "chỉ cảnh báo nếu đang có.",
        },
    },
    "required": ["employee", "role_codes"],
}


# ── Dò trước ──────────────────────────────────────────────────────────────────────────────

def _denied(reason: str) -> dict:
    """`base.denied` nói «không có quyền XEM» — đây là cửa GHI nên câu phải nói cho đúng."""
    return {"denied": True, "reason": reason}


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _find_employees(ctx: ToolContext, needle: str) -> list[Employee]:
    """Hồ sơ khớp mã (chính xác) → email tài khoản (chính xác) → họ tên (chứa). Lọc theo phạm vi
    `employee` của người hỏi: ngoài phạm vi thì với tool này cũng như không có."""
    base = apply_scope(ctx.db.query(Employee), Employee, "employee", ctx.user, ctx.profile)
    lowered = needle.lower()
    by_code = base.filter(func.lower(Employee.code) == lowered).all()
    if by_code:
        return by_code
    acct = ctx.db.query(User).filter(func.lower(User.email) == lowered, User.employee_id > 0).first()
    if acct:
        by_email = base.filter(Employee.id == acct.employee_id).all()
        if by_email:
            return by_email
    return (base.filter(Employee.full_name.ilike(f"%{needle}%"))
            .order_by(Employee.full_name).limit(MAX_CANDIDATES + 1).all())


def _employee_brief(db, emp: Employee) -> dict:
    dept = db.get(Department, emp.department_id) if emp.department_id else None
    account = db.query(User).filter(User.employee_id == emp.id).first()
    return {
        "code": emp.code, "full_name": emp.full_name,
        "department": dept.name if dept else "",
        "position": emp.position or "",
        "has_account": account is not None,
        "account_active": bool(account.is_active) if account else False,
    }


def _roles_by_code(db, codes) -> dict[str, Role]:
    rows = db.query(Role).filter(Role.code.in_(list(codes))).all() if codes else []
    return {r.code: r for r in rows}


def _resolve_departments(db, names: list[str]) -> tuple[dict[str, str], list[str]]:
    """Tên phòng gõ vào → tên CHÍNH THỨC trong danh mục (so không phân biệt hoa thường).
    Trả (map tên gõ → tên chuẩn, danh sách tên không tìm thấy)."""
    resolved, missing = {}, []
    for raw in names:
        name = _clean(raw)
        if not name:
            continue
        row = db.query(Department).filter(func.lower(Department.name) == name.lower()).first()
        if row is None:
            missing.append(name)
        else:
            resolved[name] = row.name
    return resolved, missing


# ── Tính đề xuất ──────────────────────────────────────────────────────────────────────────

def _plan_roles(db, target: User, requested: list[Role], replace: bool) -> tuple[list[int], list[dict]]:
    """Tập vai trò SAU khi xác nhận + từng dòng thêm / bỏ / không đổi."""
    current_ids = user_service._role_ids(db, target.id)
    requested_ids = [r.id for r in requested]
    final_ids = sorted(set(requested_ids)) if replace else sorted(set(current_ids) | set(requested_ids))
    seen = sorted(set(current_ids) | set(final_ids))
    roles = {r.id: r for r in db.query(Role).filter(Role.id.in_(seen)).all()} if seen else {}
    lines = []
    for rid in seen:
        role = roles.get(rid)
        if rid in final_ids and rid not in current_ids:
            status = "thêm"
        elif rid in current_ids and rid not in final_ids:
            status = "bỏ"
        else:
            status = "không đổi"
        lines.append({"kind": "role", "role_code": role.code if role else f"#{rid}",
                      "label": role.name if role else f"Vai trò #{rid}", "status": status})
    return final_ids, lines


def _plan_scope(db, target: User, role: Role, exclude_names: list[str],
                remove_company_include: bool) -> tuple[dict, list[dict], list[str]]:
    """Phạm vi MỚI của (tài khoản, vai trò) = phạm vi hiện có + loại trừ thêm (− «Chỉ trong công
    ty» nếu được bảo). Trả (ScopeUpdate dạng dict, dòng đề xuất, cảnh báo)."""
    current = user_service.get_user_scope(db, target.id, role.id)
    new = {k: list(v) for k, v in current.items()}
    lines, warnings = [], []
    for name in exclude_names:
        if name in current["exclude_departments"]:
            status = "không đổi"
        else:
            new["exclude_departments"].append(name)
            status = "thêm"
        lines.append({"kind": "scope", "role_code": role.code,
                      "label": f"{role.name}: loại trừ phòng «{name}»", "status": status})
    if current["companies"]:
        if remove_company_include:
            new["companies"] = []
            lines.append({"kind": "scope", "role_code": role.code,
                          "label": f"{role.name}: «Chỉ trong công ty» ({len(current['companies'])} dòng)",
                          "status": "bỏ"})
        elif role.code in PURCHASING_ROLE_CODES:
            warnings.append(
                f"Vai trò {role.name} đang có «Chỉ trong công ty» ({len(current['companies'])} pháp "
                "nhân) — bao-CR-434: bộ thu mua thường KHÔNG nên nhốt theo pháp nhân. Muốn gỡ thì "
                "gọi lại với remove_company_include = true.")
    return new, lines, warnings


# ── Bước 1: đề xuất ───────────────────────────────────────────────────────────────────────

def _run_propose(ctx: ToolContext, args: dict) -> dict:
    for entity, action in REQUIRED_PERMS:
        if not ctx.can(entity, action):
            return _denied(f"Bạn không có quyền lập bộ tài khoản (thiếu {entity}.{action}).")

    needle = _clean(args.get("employee"))
    if not needle:
        return {"error": "Cần mã nhân viên, họ tên hoặc email của người cần lập tài khoản."}

    codes = [_clean(c) for c in (args.get("role_codes") or []) if _clean(c)]
    unknown = sorted({c for c in codes if c not in TEMPLATE_ROLE_CODES})
    if not codes or unknown:
        return {"error": "role_codes chỉ nhận vai trò trong bộ mẫu: " + ", ".join(TEMPLATE_ROLE_CODES)
                + (f". Không nhận: {', '.join(unknown)}." if unknown else ".")}
    roles_map = _roles_by_code(ctx.db, codes)
    absent = [c for c in codes if c not in roles_map]
    if absent:
        return {"error": f"Hệ chưa có vai trò {', '.join(absent)} — chạy seed sau CR-414 rồi thử lại. "
                         "Tool không tự tạo vai trò."}
    requested = [roles_map[c] for c in dict.fromkeys(codes)]

    exclude_map, missing = _resolve_departments(ctx.db, args.get("exclude_departments") or [])
    if missing:
        return {"error": "Không tìm thấy phòng ban để loại trừ: " + ", ".join(f"«{m}»" for m in missing)
                + ". Kiểm tên ở Nhân sự › Phòng ban rồi gọi lại."}
    exclude_names = list(dict.fromkeys(exclude_map.values()))
    replace = bool(args.get("replace_roles"))
    remove_company = bool(args.get("remove_company_include"))

    found = _find_employees(ctx, needle)
    if not found:
        return {"status": "blocked", "reason": "not_found",
                "message": f"Không thấy hồ sơ nhân sự khớp «{needle}» trong phạm vi của bạn. Bước 1 "
                           "của hướng dẫn (tạo hồ sơ nhân sự) vẫn làm tay ở Nhân sự › Nhân viên."}
    if len(found) > 1:
        return {"status": "ambiguous",
                "candidates": [_employee_brief(ctx.db, e) for e in found[:MAX_CANDIDATES]],
                "message": "Nhiều hồ sơ khớp — hỏi lại người dùng đúng MÃ nhân viên rồi gọi lại."}
    emp = found[0]
    brief = _employee_brief(ctx.db, emp)

    target = ctx.db.query(User).filter(User.employee_id == emp.id).first()
    if target is None:
        return {"status": "blocked", "reason": "no_account", "employee": brief,
                "message": f"{emp.full_name} ({emp.code}) chưa có tài khoản đăng nhập. Tool không tạo "
                           "tài khoản và không đặt mật khẩu — làm Bước 2 của hướng dẫn ở Quản trị › "
                           "Phân quyền tài khoản › Thêm tài khoản, rồi gọi lại tool này."}
    if target.id == ctx.user.id:
        return _denied(privilege_escalation.SELF_CHANGE_MESSAGE)
    if get_scoped(ctx.db, User, "user", target.id, ctx.user, ctx.profile, "write") is None:
        return _denied(f"Tài khoản của {emp.full_name} nằm ngoài phạm vi tài khoản bạn được sửa.")

    final_ids, role_lines = _plan_roles(ctx.db, target, requested, replace)
    try:
        privilege_escalation.block_role_escalation(ctx.db, ctx.user, final_ids)
    except HTTPException as e:
        return {"denied": True, "reason": str(e.detail)}

    scopes, scope_lines, warnings = {}, [], []
    for role in requested:
        new_scope, lines, warns = _plan_scope(ctx.db, target, role, exclude_names, remove_company)
        if lines:
            scopes[str(role.id)] = new_scope
        scope_lines.extend(lines)
        warnings.extend(warns)
    if not brief["account_active"]:
        warnings.append("Tài khoản đang KHÓA — gán xong vẫn chưa đăng nhập được, mở khóa ở màn "
                        "Phân quyền tài khoản.")

    lines = role_lines + scope_lines
    changed = sum(1 for line in lines if line["status"] != "không đổi")
    payload = {"k": PROPOSAL_KIND, "u": ctx.user.id, "t": target.id,
               "roles": final_ids, "scopes": scopes}
    token = _fernet().encrypt(json.dumps(payload, ensure_ascii=False).encode()).decode()
    return {
        "status": "ready",
        "proposal": {
            "kind": PROPOSAL_KIND,
            "target_label": f"{emp.full_name} ({emp.code})",
            "employee": brief,
            "lines": lines,
            "warnings": warnings,
            "changed": changed,
            "confirm_token": token,
            "url": USER_PERMISSION_URL.format(user_id=target.id),
        },
        "total": changed,
        "reminder": ("Mọi dòng đều «không đổi» — tài khoản đã đúng bộ, không cần xác nhận."
                     if changed == 0 else
                     "CHƯA ghi gì. Giao diện đang hiện thẻ đề xuất; chỉ khi người dùng bấm "
                     "'Xác nhận' hệ thống mới gán vai trò / đặt phạm vi. Đừng nói đã gán."),
    }


PROPOSE_ACCOUNT_SETUP_SPEC = ToolSpec(
    name="propose_account_setup",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run_propose,
)


# ── Bước 2: người bấm Xác nhận ────────────────────────────────────────────────────────────

def confirm_account_setup(db, user, token: str) -> dict:
    """Ghi thật. Kiểm lại TẤT CẢ tại lúc bấm: token còn hạn + đúng chủ + đúng loại; quyền;
    phạm vi tài khoản; L1/L2; vai trò còn tồn tại — rồi mới gọi hai service của màn Phân quyền."""
    try:
        payload = json.loads(_fernet().decrypt(token.encode(), ttl=CONFIRM_TTL_SECONDS))
    except (InvalidToken, ValueError, TypeError) as e:
        raise HTTPException(400, "Đề xuất đã hết hạn hoặc không hợp lệ — nhờ trợ lý đề xuất lại.") from e
    if payload.get("k") != PROPOSAL_KIND or payload.get("u") != user.id:
        raise HTTPException(403, "Đề xuất không thuộc về bạn.")

    for entity, action in REQUIRED_PERMS:
        if not user_has_permission(db, user, entity, action):
            raise HTTPException(403, f"Bạn không còn quyền {entity}.{action} để lập bộ tài khoản.")

    target_id = int(payload.get("t") or 0)
    profile = get_perm_profile(db, user)
    target = get_scoped(db, User, "user", target_id, user, profile, "write")
    if target is None:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    privilege_escalation.block_edit_own_permissions(target_id, user)

    final_ids = [int(r) for r in payload.get("roles") or []]
    privilege_escalation.block_missing_roles(db, final_ids)
    privilege_escalation.block_role_escalation(db, user, final_ids)

    updated = []
    if user_service._role_ids(db, target_id) != sorted(final_ids):
        user_service.assign_roles(db, target_id, RoleAssign(role_ids=final_ids), user.id)
        updated.append("vai trò")

    for role_id_text, scope in (payload.get("scopes") or {}).items():
        role_id = int(role_id_text)
        if role_id not in final_ids:
            continue
        data = ScopeUpdate(**scope)
        if user_service.get_user_scope(db, target_id, role_id) == data.model_dump():
            continue
        user_service.set_user_scope(db, target_id, role_id, data, user.id)
        role_name = (user_service._role_names(db, [role_id]) or [f"#{role_id}"])[0]
        updated.append(f"phạm vi {role_name}")

    return {
        "target_label": user_service.user_label(db, target_id),
        "roles": user_service._role_names(db, final_ids),
        "updated": updated,
        "url": USER_PERMISSION_URL.format(user_id=target_id),
    }
