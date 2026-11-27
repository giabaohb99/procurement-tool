"""bao-CR-793 — chuyển người của MỘT phòng từ vai trò xem cả cụm Giá nguyên vật liệu sản xuất sang vai trò chỉ xem hai màn.

Chạy TRONG container api (LUÔN chạy thử trước, chỉ ghi khi có --apply):
    docker compose exec -T api python -m scripts.split_packaging_lab_role --dept-id 6            # chạy thử, in kế hoạch
    docker compose exec -T api python -m scripts.split_packaging_lab_role --dept-id 6 --apply    # ghi thật

Việc làm:
  - tạo vai trò `packaging_cost_lab_view` nếu chưa có, cấp đúng hai khóa `packaging_price_list` (Bảng giá VTBB) và
    `packaging_last_price` (Giá mua gần nhất). Cờ Xem / Xuất và phạm vi chép từ vai trò gốc `packaging_cost_view`; không bao giờ
    chép cờ tạo / sửa / xóa;
  - mỗi tài khoản thuộc phòng đang giữ vai trò gốc do GÁN TAY: đổi sang vai trò mới (kèm dòng phạm vi riêng theo người nếu có).
    Vai trò gốc đến từ gói quyền của chức vụ thì KHÔNG đụng (đổi ở gói của chức vụ), chỉ in cảnh báo;
  - người ngoài phòng giữ nguyên vai trò gốc, vẫn xem cả sáu màn.

Phải chạy SAU migration `permsplit792` (vai trò gốc đã mang sáu khóa mới); chưa có thì script dừng, không ghi gì.
An toàn khi chạy lại: lần hai không đổi gì. Máy chủ nhớ quyền 60 giây nên người dùng thấy thay đổi sau tối đa một phút.
"""
import argparse

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from sqlalchemy import func

from app.core.audit import record
from app.core.database import SessionLocal
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPositionRole
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole, UserScope

BASE_ROLE = "packaging_cost_view"
LAB_ROLE = "packaging_cost_lab_view"
LAB_ROLE_NAME = "Giá NVL: Bảng giá và Giá mua gần nhất"
LAB_ROLE_NOTE = "Chỉ xem Bảng giá VTBB và Giá mua gần nhất của cụm Giá nguyên vật liệu sản xuất"
LAB_ENTITIES = ("packaging_price_list", "packaging_last_price")
ACTOR = 0   # người thao tác 0 = script vận hành


def split_lab_role(db, dept_id: int) -> dict:
    """Ghi vào phiên (không commit). Trả {"role_created", "granted", "moved", "skipped_position", "bundles"}."""
    base = db.query(Role).filter(Role.code == BASE_ROLE).first()
    if base is None:
        raise SystemExit(f"Không có vai trò gốc `{BASE_ROLE}`.")
    base_perms = {p.entity: p for p in db.query(Permission).filter(
        Permission.role_id == base.id, Permission.entity.in_(LAB_ENTITIES)).all()}
    if set(base_perms) != set(LAB_ENTITIES):
        raise SystemExit(f"Vai trò gốc chưa mang đủ khóa {LAB_ENTITIES}: chạy migration `permsplit792` trước.")

    out = {"role_created": False, "granted": [], "moved": [], "skipped_position": [], "bundles": 0}
    lab = db.query(Role).filter(Role.code == LAB_ROLE).first()
    if lab is None:
        lab = Role(code=LAB_ROLE, name=LAB_ROLE_NAME, description=LAB_ROLE_NOTE,
                   sort_order=(db.query(func.max(Role.sort_order)).scalar() or 0) + 1, created_by=ACTOR, updated_by=ACTOR)
        db.add(lab)
        db.flush()
        out["role_created"] = True
        record(db, ACTOR, "role", lab.id, "create", f"Script tạo vai trò {LAB_ROLE_NAME}", doc_code=LAB_ROLE, commit=False)
    held = {p.entity for p in db.query(Permission.entity).filter(Permission.role_id == lab.id).all()}
    for entity in LAB_ENTITIES:
        if entity in held:
            continue
        src = base_perms[entity]
        db.add(Permission(role_id=lab.id, entity=entity, scope=src.scope, can_read=bool(src.can_read),
                          can_export=bool(src.can_export), created_by=ACTOR, updated_by=ACTOR))
        out["granted"].append(entity)
    if out["granted"]:
        record(db, ACTOR, "role", lab.id, "set_permissions",
               f"Script phân quyền vai trò {LAB_ROLE_NAME}: " + ", ".join(out["granted"]), doc_code=LAB_ROLE, commit=False)

    rows = (db.query(UserRole, Employee.full_name).join(User, User.id == UserRole.user_id)
            .join(Employee, Employee.id == User.employee_id)
            .filter(UserRole.role_id == base.id, Employee.department_id == dept_id).order_by(UserRole.user_id).all())
    has_lab = {r[0] for r in db.query(UserRole.user_id).filter(UserRole.role_id == lab.id).all()}
    for row, full_name in rows:
        label = f"#{row.user_id} {full_name or ''}".strip()
        if row.granted_by_position_id:
            out["skipped_position"].append(label)
            continue
        if row.user_id in has_lab:
            db.delete(row)
        else:
            row.role_id, row.updated_by = lab.id, ACTOR
        scopes = db.query(UserScope).filter(UserScope.user_id == row.user_id, UserScope.role_id == base.id)
        if db.query(UserScope.id).filter(UserScope.user_id == row.user_id, UserScope.role_id == lab.id).first():
            scopes.delete()
        else:
            scopes.update({UserScope.role_id: lab.id})
        record(db, ACTOR, "user", row.user_id, "assign_roles",
               f"Script đổi vai trò: thêm {LAB_ROLE_NAME}; bỏ {base.name or BASE_ROLE}", commit=False)
        out["moved"].append(label)
    out["bundles"] = db.query(JobPositionRole.id).filter(JobPositionRole.role_id == base.id).count()
    db.flush()
    return out


def main(apply: bool, dept_id: int) -> None:
    db = SessionLocal()
    try:
        dept = db.get(Department, dept_id)
        if dept is None:
            raise SystemExit(f"Không có phòng ban #{dept_id}.")
        result = split_lab_role(db, dept_id)
        print(f"Phòng #{dept_id} {dept.name}")
        print("  vai trò mới:", "tạo mới" if result["role_created"] else "đã có", "· khóa cấp thêm:", result["granted"] or "không")
        print(f"  chuyển {len(result['moved'])} tài khoản:", ", ".join(result["moved"]) or "không ai")
        if result["skipped_position"]:
            print("  KHÔNG đụng (vai trò đến từ gói quyền chức vụ):", ", ".join(result["skipped_position"]))
        if result["bundles"]:
            print(f"  LƯU Ý: {result['bundles']} gói quyền chức vụ đang chứa vai trò gốc, người mới nhận chức vụ đó vẫn xem cả cụm.")
        if apply:
            db.commit()
            print("ĐÃ GHI.")
        else:
            db.rollback()
            print("CHẠY THỬ: chưa ghi gì. Thêm --apply để ghi.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dept-id", type=int, required=True, help="id phòng ban cần chuyển (Dego Lab = 6)")
    parser.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    args = parser.parse_args()
    main(args.apply, args.dept_id)
