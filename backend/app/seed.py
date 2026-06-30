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
from app.modules.role.model import Permission, Role
from app.modules.supplier.model import Supplier
from app.modules.user.model import User, UserRole


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


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Schema verification: check if quote_file_url column exists in tab_purchase_request
        from sqlalchemy import text
        try:
            db.execute(text("SELECT quote_file_url FROM tab_purchase_request LIMIT 1"))
        except Exception:
            db.rollback()
            print("Database schema upgrade needed: recreating purchase request tables...")
            db.execute(text("DROP TABLE IF EXISTS tab_purchase_request_item"))
            db.execute(text("DROP TABLE IF EXISTS tab_purchase_request"))
            db.commit()
            Base.metadata.create_all(bind=engine)

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
                     can_write=True, can_delete=True, can_approve=True, can_print=True,
                     can_export=True, scope="all",
                ))
        db.commit()

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
        for g in _load("item_groups.json"):
            nm = (g.get("name") or "").strip()
            if nm and nm[:100].upper() not in seen_item_groups:
                db.add(ItemGroup(name=nm[:100], std_days=str(g.get("std_days", "")), note=g.get("note", ""),
                                 apply_date=g.get("apply_date", ""), is_active=True))
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
            user = User(email="admin@dego.local", employee_id=emp.id,
                        password_hash=hash_password(settings.ADMIN_PASSWORD), is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()

        print(f"Seed done. Admin login: {settings.ADMIN_CODE} / (mật khẩu trong .env)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
