"""Tạo bảng + seed dữ liệu khởi tạo (idempotent). Chạy: python -m app.seed"""
import json
import os

from app.core.auth import hash_password
from app.core.base_model import Base
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.permissions import ENTITIES

# Import tất cả model để metadata biết các bảng
from app.modules.attachment.model import Attachment  # noqa: F401
from app.modules.audit.model import AuditLog  # noqa: F401
from app.modules.catalog.model import (Brand, ItemGroup,  # noqa: F401
                                       Unit, Warehouse)
from app.modules.company.model import Company
from app.modules.department.model import Department  # noqa: F401
from app.modules.employee.model import Employee
from app.modules.product.model import Product
from app.modules.purchase_request.model import (PurchaseRequest,  # noqa: F401
                                                PurchaseRequestItem)
from app.modules.purchase_order.model import (PurchaseOrder,  # noqa: F401
                                              POItem, PODelivery)
from app.modules.goods_receipt.model import GoodsReceipt  # noqa: F401
from app.modules.inventory.model import Inventory, InventoryMove  # noqa: F401
from app.modules.payable.model import Payable  # noqa: F401
from app.modules.payment_request.model import (PaymentRequest,  # noqa: F401
                                               PaymentRequestLine)
from app.modules.role.model import Permission, Role
from app.modules.supplier.model import Supplier
from app.modules.survey.model import (Survey, SurveyProductLine,  # noqa: F401
                                      SurveySupplierLine)
from app.modules.user.model import User, UserRole
from app.modules.notification.model import Notification, EmailLog  # noqa: F401


SAMPLE_COMPANIES = [
    ("DEGO", "CÔNG TY TNHH DEGO HOLDING", "1801722464"),
    ("IDA", "CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL", "0314562909"),
    ("ABA", "CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA", "0316342296"),
]

SAMPLE_SUPPLIERS = [
    ("Cẩm Hùng", "CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG", "1801778241", "goods", "Công nợ 60 ngày", 0.08),
    ("Đông Tây", "CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG TÂY", "0316254811", "goods", "Công nợ 30 ngày", 0.08),
    ("Mộc Ấn", "CÔNG TY TNHH QUẢNG CÁO MỘC ẤN", "0312214688", "goods", "Thanh toán 100% khi nhận hàng", 0.10),
    ("Mekong Logistics", "Mekong Logistics", "", "transport", "Công nợ theo chuyến", 0.08),
    ("Sang Giàu", "Vận chuyển Sang Giàu", "", "transport", "Tiền mặt", 0.0),
]

SAMPLE_PRODUCTS = [
    ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Thùng", "Cái"),
    ("THC0003", "Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen", "Thùng", "Cái"),
    ("THC0004", "Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng", "Thùng", "Cái"),
    ("NL0001", "Nguyên liệu Vi lượng AV4", "Nguyên liệu", "Kg"),
]


def seed_demo_accounts(db, company_id):
    from app.modules.role.model import Role, Permission
    from app.modules.user.model import User, UserRole
    from app.modules.employee.model import Employee
    from app.core.auth import hash_password
    
    roles_def = {
        "staff": {
            "name": "Nhân viên (Demo)",
            "perms": {
                "purchase_request": {"read": True, "create": True, "write": True, "delete": True},
                "report": {"read": True},
            }
        },
        "manager": {
            "name": "Trưởng bộ phận (Demo)",
            "perms": {
                "purchase_request": {"read": True, "create": True, "write": True, "delete": True, "approve": True},
                "report": {"read": True},
            }
        },
        "manager_purchase": {
            "name": "Trưởng phòng Thu mua (Demo)",
            "perms": {
                "purchase_request": {"read": True, "create": True, "write": True, "delete": True, "approve": True},
                "report": {"read": True},
                "survey": {"read": True, "create": True, "write": True, "approve": True},
                "purchase_order": {"read": True, "create": True, "write": True, "approve": True},
                "inventory": {"read": True},
                "payable": {"read": True},
                "payment_request": {"read": True},
                "warehouse": {"read": True},
                "unit": {"read": True},
                "item_group": {"read": True},
                "brand": {"read": True},
                "supplier": {"read": True},
                "product": {"read": True},
                "contract": {"read": True},
                "department": {"read": True},
            }
        },
        "purchaser": {
            "name": "Nhân viên Thu mua (Demo)",
            "perms": {
                "purchase_request": {"read": True, "create": True, "write": True, "delete": True},
                "report": {"read": True},
                "survey": {"read": True, "create": True, "write": True, "delete": True},
                "purchase_order": {"read": True, "create": True, "write": True, "delete": True},
                "inventory": {"read": True},
                "payable": {"read": True},
                "payment_request": {"read": True, "create": True, "write": True},
                "warehouse": {"read": True},
                "unit": {"read": True},
                "item_group": {"read": True},
                "brand": {"read": True},
                "supplier": {"read": True},
                "product": {"read": True},
                "contract": {"read": True},
                "department": {"read": True},
            }
        }
    }
    
    for code, r_info in roles_def.items():
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=r_info["name"])
            db.add(role)
            db.commit()
            db.refresh(role)
            
        existing_perms = {p.entity: p for p in db.query(Permission).filter(Permission.role_id == role.id).all()}
        for entity, actions in r_info["perms"].items():
            if entity not in existing_perms:
                perm = Permission(
                    role_id=role.id,
                    entity=entity,
                    can_read=actions.get("read", False),
                    can_create=actions.get("create", False),
                    can_write=actions.get("write", False),
                    can_delete=actions.get("delete", False),
                    can_approve=actions.get("approve", False),
                    scope="all"
                )
                db.add(perm)
        db.commit()

        emp_code = f"DEMO_{code.upper()}"
        emp = db.query(Employee).filter(Employee.code == emp_code).first()
        if not emp:
            emp = Employee(code=emp_code, full_name=r_info["name"], company_id=company_id, position=r_info["name"], is_active=True)
            db.add(emp)
            db.commit()
            db.refresh(emp)
            
        email = f"{code}@demo.com"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, employee_id=emp.id, password_hash=hash_password("demo123"), is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Xoá role cũ (nếu có)
            db.query(UserRole).filter(UserRole.user_id == user.id).delete()
            db.add(UserRole(user_id=user.id, role_id=role.id))
            db.commit()


# Vai trò chuẩn theo phân quyền DEGO. Mỗi entity: (danh sách hành động, phạm vi).
# Phạm vi: own | dept | company | all. Xem doc/Thiet_Ke_Phan_Quyen.md.
# employee KHÔNG nằm ở đây: danh sách nhân sự phải giới hạn theo phạm vi từng vai trò
# (phòng ban của mình) — cấu hình riêng bên dưới.
_CATALOG_READ = {e: (["read"], "all") for e in
                 ["supplier", "product", "warehouse", "unit", "item_group", "contract", "department", "company"]}

STD_ROLES = {
    "employee": {"name": "Nhân sự (cơ bản)", "perms": {
        # chỉ các danh mục cần cho form tạo yêu cầu (không có Hợp đồng/NCC)
        "product": (["read"], "all"), "unit": (["read"], "all"),
        "item_group": (["read"], "all"), "warehouse": (["read"], "all"),
        "department": (["read"], "all"), "company": (["read"], "all"),
        "purchase_request": (["read", "create"], "own"),
    }},
    "dept_head": {"name": "Trưởng phòng (duyệt PYC)", "perms": {
        **_CATALOG_READ,
        "employee": (["read"], "dept"),
        "purchase_request": (["read", "approve"], "dept"),
        "report": (["read"], "dept"),
    }},
    "company_head": {"name": "Quản lý công ty", "perms": {
        **_CATALOG_READ,
        "employee": (["read"], "company"),
        "purchase_request": (["read"], "company"),
        "purchase_order": (["read"], "company"),
        "report": (["read"], "company"),
    }},
    "pur_staff": {"name": "Nhân viên thu mua", "perms": {
        **_CATALOG_READ,
        "employee": (["read"], "dept"),
        "purchase_request": (["read", "create", "write"], "assigned"),
        "survey": (["read", "create", "write"], "all"),
        "purchase_order": (["read", "create", "write", "print"], "dept"),
        "inventory": (["read"], "company"),
        "payable": (["read"], "company"),
        "payment_request": (["read", "create", "write", "print"], "company"),
        "report": (["read"], "company"),
    }},
    "pur_manager": {"name": "Quản lý thu mua", "perms": {
        **_CATALOG_READ,
        "employee": (["read"], "dept"),
        "purchase_request": (["read", "approve", "cancel"], "all"),
        "survey": (["read", "approve"], "all"),
        "purchase_order": (["read", "write", "approve", "cancel", "print", "export"], "all"),
        "inventory": (["read"], "all"),
        "payable": (["read"], "all"),
        "payment_request": (["read", "approve", "print", "export"], "all"),
        "report": (["read", "export"], "all"),
    }},
    "pur_admin": {"name": "Admin thu mua", "perms": {
        "purchase_request": (["read", "create", "write", "delete", "approve", "cancel", "print", "export"], "all"),
        "purchase_order": (["read", "create", "write", "delete", "approve", "cancel", "print", "export"], "all"),
        "survey": (["read", "create", "write", "delete", "approve"], "all"),
        "inventory": (["read", "write"], "all"),
        "payable": (["read", "write"], "all"),
        "payment_request": (["read", "create", "write", "delete", "approve", "print", "export"], "all"),
        "report": (["read", "export"], "all"),
        "supplier": (["read", "create", "write", "delete"], "all"),
        "product": (["read", "create", "write", "delete"], "all"),
        "contract": (["read", "create", "write", "delete"], "all"),
        "warehouse": (["read", "create", "write"], "all"),
        "unit": (["read", "create", "write"], "all"),
        "item_group": (["read", "create", "write"], "all"),
        "department": (["read"], "all"),
        "company": (["read", "create", "write"], "all"),
        "employee": (["read"], "all"),
    }},
}


def seed_standard_roles(db):
    """Tạo các vai trò chuẩn + ma trận quyền (idempotent). Không tạo user; gán cho nhân sự ở màn Phân quyền."""
    for code, info in STD_ROLES.items():
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=info["name"])
            db.add(role)
            db.commit()
            db.refresh(role)
        existing = {p.entity for p in db.query(Permission).filter(Permission.role_id == role.id).all()}
        for entity, (actions, scope) in info["perms"].items():
            if entity in existing:
                continue
            db.add(Permission(
                role_id=role.id, entity=entity, scope=scope,
                can_read="read" in actions, can_create="create" in actions,
                can_write="write" in actions, can_delete="delete" in actions,
                can_approve="approve" in actions, can_cancel="cancel" in actions,
                can_print="print" in actions, can_export="export" in actions,
            ))
        db.commit()


def assign_default_roles(db):
    """Tài khoản nào CHƯA có vai trò → gán 'Nhân sự' (employee) để ai cũng tạo/xem PYC của mình.
    Không đụng tài khoản đã có vai trò (admin, đã gán tay...)."""
    emp_role = db.query(Role).filter(Role.code == "employee").first()
    if not emp_role:
        return 0
    assigned = {ur.user_id for ur in db.query(UserRole).all()}
    n = 0
    for u in db.query(User).all():
        if u.id not in assigned:
            db.add(UserRole(user_id=u.id, role_id=emp_role.id))
            n += 1
    if n:
        db.commit()
    return n


def run():
    # Schema do Alembic quản lý (start.sh chạy `alembic upgrade head` trước). Seed chỉ nạp DATA.
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.code == "admin").first()
        if not admin_role:
            admin_role = Role(code="admin", name="Quản trị hệ thống")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        # Đảm bảo admin có quyền đầy đủ cho MỌI entity (thêm entity mới sẽ tự được cấp)
        existing = {p.entity for p in db.query(Permission).filter(Permission.role_id == admin_role.id).all()}
        for entity in ENTITIES:
            if entity not in existing:
                db.add(Permission(
                     role_id=admin_role.id, entity=entity, can_read=True, can_create=True,
                     can_write=True, can_delete=True, can_approve=True, can_cancel=True,
                     can_print=True, can_export=True, scope="all",
                ))
        # Bổ sung can_cancel cho các vai trò quản trị (admin, ADMINISTRATOR) tạo trước khi có action 'cancel'
        admin_role_ids = [r.id for r in db.query(Role).filter(Role.code.in_(["admin", "ADMINISTRATOR"])).all()]
        if admin_role_ids:
            db.query(Permission).filter(Permission.role_id.in_(admin_role_ids), Permission.can_cancel == False).update({"can_cancel": True}, synchronize_session=False)
        db.commit()

        # Sửa phạm vi employee-read cho các vai trò đã seed trước đây (khi còn để "all").
        # Danh sách nhân sự phải giới hạn theo phòng ban/công ty của người xem.
        _EMP_READ_SCOPE = {"dept_head": "dept", "company_head": "company",
                           "pur_staff": "dept", "pur_manager": "dept"}
        for rcode, sc in _EMP_READ_SCOPE.items():
            r = db.query(Role).filter(Role.code == rcode).first()
            if r:
                db.query(Permission).filter(
                    Permission.role_id == r.id, Permission.entity == "employee",
                    Permission.scope == "all",
                ).update({"scope": sc}, synchronize_session=False)
        db.commit()

        # Vai trò chuẩn (Nhân sự / Trưởng phòng / Quản lý cty / NV thu mua / QL thu mua / Admin thu mua)
        seed_standard_roles(db)

        # Deduplication tracking sets (using upper case for case-insensitivity)
        seen_companies = {c[0].upper() for c in db.query(Company.code).all()}
        seen_suppliers = {s[0].upper() for s in db.query(Supplier.code).all()}
        seen_products = {p[0].upper() for p in db.query(Product.code).all()}
        seen_warehouses = {w[0].upper() for w in db.query(Warehouse.code).all()}
        seen_units = {u[0].upper() for u in db.query(Unit.code).all()}
        seen_item_groups = {g[0].upper() for g in db.query(ItemGroup.name).all()}
        seen_brands = {b[0].upper() for b in db.query(Brand.code).all()}

        for code, name, mst in SAMPLE_COMPANIES:
            if code.upper() not in seen_companies:
                db.add(Company(code=code, name=name, tax_code=mst, is_active=True))
                seen_companies.add(code.upper())
        db.commit()
        company = db.query(Company).filter(Company.code == "DEGO").first()

        for code, name, mst, stype, terms, vat in SAMPLE_SUPPLIERS:
            if code.upper() not in seen_suppliers:
                db.add(Supplier(code=code, name=name, tax_code=mst, supplier_type=stype,
                                payment_terms=terms, vat=vat, is_active=True))
                seen_suppliers.add(code.upper())
        for code, name, group, unit in SAMPLE_PRODUCTS:
            if code.upper() not in seen_products:
                db.add(Product(code=code, name=name, item_group=group, unit=unit, is_active=True))
                seen_products.add(code.upper())
        db.commit()

        # Đồng bộ master data thật từ JSON (sinh từ doc/datamau)
        seed_dir = os.path.join(os.path.dirname(__file__), "seed_data")

        def _load(n):
            p = os.path.join(seed_dir, n)
            return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []

        for c in _load("companies.json"):
            code = (c.get("code") or "")[:25]
            if code and code.upper() not in seen_companies:
                db.add(Company(code=code, name=c.get("name", ""), address=c.get("address", ""),
                               tax_code=c.get("tax_code", ""), is_active=True))
                seen_companies.add(code.upper())
        for s in _load("suppliers.json"):
            code = (s.get("code") or "")[:25]
            if code and code.upper() not in seen_suppliers:
                db.add(Supplier(code=code, name=s.get("name", ""), address=s.get("address", ""),
                                tax_code=s.get("tax_code", ""), supplier_type=s.get("supplier_type", "goods"),
                                is_active=True))
                seen_suppliers.add(code.upper())
        db.commit()

        # Danh mục: kho, ĐVT, phân loại, thương hiệu
        for w in _load("warehouses.json"):
            code = (w.get("code") or "")[:25]
            if code and code.upper() not in seen_warehouses:
                db.add(Warehouse(code=code, name=w.get("name", ""), address=w.get("address", ""), is_active=True))
                seen_warehouses.add(code.upper())
        for u in _load("units.json"):
            nm = (u.get("name") or "").strip()
            code = nm[:25]
            if code and code.upper() not in seen_units:
                db.add(Unit(code=code, name=nm[:100], is_active=True))
                seen_units.add(code.upper())
        ig_seq = db.query(ItemGroup).count()
        for g in _load("item_groups.json"):
            nm = (g.get("name") or "").strip()
            if nm and nm[:100].upper() not in seen_item_groups:
                ig_seq += 1
                code = (g.get("code") or f"PL{ig_seq:03d}")[:25]
                db.add(ItemGroup(code=code, name=nm[:100], std_days=str(g.get("std_days", "")),
                                 std_days_unavail=str(g.get("std_days_unavail", "")),
                                 note=g.get("note", ""), apply_date=g.get("apply_date", ""), is_active=True))
                seen_item_groups.add(nm[:100].upper())
        for b in _load("brands.json"):
            code = (b.get("code") or "")[:25]
            if code and code.upper() not in seen_brands:
                db.add(Brand(code=code, department=b.get("department", ""), is_active=True))
                seen_brands.add(code.upper())
        db.commit()

        emp = db.query(Employee).filter(Employee.code == settings.ADMIN_CODE).first()
        if not emp:
            emp = Employee(code=settings.ADMIN_CODE, full_name="Quản trị viên",
                           company_id=company.id, position="Admin", is_active=True)
            db.add(emp)
            db.commit()
            db.refresh(emp)

        user = db.query(User).filter(User.employee_id == emp.id).first()
        if not user:
            user = User(email="hgbao.idagroup@gmail.com", employee_id=emp.id,
                        password_hash=hash_password(settings.ADMIN_PASSWORD), is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()

        # Seed second admin: DEGO0001 (username: admin, pass: admin, name: Dego Admin)
        emp2 = db.query(Employee).filter(Employee.code == "DEGO0001").first()
        if not emp2:
            emp2 = Employee(code="DEGO0001", full_name="Dego Admin",
                            company_id=company.id, position="Admin", is_active=True)
            db.add(emp2)
            db.commit()
            db.refresh(emp2)

        user2 = db.query(User).filter(User.employee_id == emp2.id).first()
        if not user2:
            user2 = User(email="admin", employee_id=emp2.id,
                         password_hash=hash_password("admin"), is_active=True)
            db.add(user2)
            db.commit()
            db.refresh(user2)
            db.add(UserRole(user_id=user2.id, role_id=admin_role.id))
            db.commit()

        # Seed demo accounts
        seed_demo_accounts(db, company.id)

        # Gán vai trò mặc định "Nhân sự" cho tài khoản chưa có vai trò
        n_default = assign_default_roles(db)
        if n_default:
            print(f"Gán vai trò 'Nhân sự' mặc định cho {n_default} tài khoản.")

        print(f"Seed done. Admin login: {settings.ADMIN_CODE} / (mật khẩu trong .env)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
