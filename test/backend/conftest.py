"""
conftest.py — SQLite in-memory fixtures cho backend pytest.

Điểm mấu chốt:
- BigInteger PK không autoincrement trên SQLite → compile hook chuyển thành INTEGER.
- import app.main để đăng ký toàn bộ model vào Base.metadata.
- Fixture db (function-scope): SQLite in-memory, create_all, sessionmaker.
- Fixture seed(db): dữ liệu tối thiểu, trả về namespace với các id cần thiết.
"""
import types
from types import SimpleNamespace

import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Fix BigInteger trên SQLite (không hỗ trợ BIGINT AUTOINCREMENT) ──────────────
@compiles(BigInteger, "sqlite")
def _bigint_sqlite(el, comp, **kw):
    return "INTEGER"


# ── Import toàn bộ model vào Base.metadata ──────────────────────────────────────
import app.main  # noqa: F401 — side-effect: đăng ký tất cả router + model

from app.core.base_model import Base


# ── Fixture db ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ── Fixture seed ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def seed(db):
    """Tạo data tối thiểu, trả về SimpleNamespace chứa các id cần dùng trong test."""
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    from app.modules.catalog.model import ItemGroup
    from app.modules.supplier.model import Supplier
    from app.modules.category_assignee.model import CategoryAssignee
    from app.modules.survey.model import Survey, SurveyProductLine

    # ── Company ──────────────────────────────────────────────────────────────────
    company = Company(name="Cty Test", code="CT01", is_active=True)
    db.add(company)
    db.flush()

    # ── Department ───────────────────────────────────────────────────────────────
    dept = Department(code="DEPT01", name="Phòng Test", company_id=company.id, is_active=True)
    db.add(dept)
    db.flush()

    # ── Employees: req / tp / nstm / backup ──────────────────────────────────────
    emp_req = Employee(code="TESTREQ", full_name="Người YC", company_id=company.id,
                       department_id=dept.id, is_active=True)
    emp_tp = Employee(code="DEMOTP", full_name="Trưởng Phòng", company_id=company.id,
                      department_id=dept.id, is_active=True)
    emp_nstm = Employee(code="DEMONV", full_name="NSTM Chính", company_id=company.id,
                        department_id=dept.id, is_active=True)
    emp_backup = Employee(code="BACKUP01", full_name="NSTM Dự Phòng", company_id=company.id,
                          department_id=dept.id, is_active=True)
    db.add_all([emp_req, emp_tp, emp_nstm, emp_backup])
    db.flush()

    # ── Users ────────────────────────────────────────────────────────────────────
    u_req = User(email="TESTREQ", employee_id=emp_req.id, password_hash="x", is_active=True)
    u_tp = User(email="DEMOTP", employee_id=emp_tp.id, password_hash="x", is_active=True)
    u_nstm = User(email="DEMONV", employee_id=emp_nstm.id, password_hash="x", is_active=True)
    u_backup = User(email="BACKUP01", employee_id=emp_backup.id, password_hash="x", is_active=True)
    db.add_all([u_req, u_tp, u_nstm, u_backup])
    db.flush()

    # ── ItemGroups ───────────────────────────────────────────────────────────────
    ig_nhan = ItemGroup(code="NHAN", name="Nhãn", is_active=True)
    ig_thung = ItemGroup(code="THUNG", name="Thùng", is_active=True)
    db.add_all([ig_nhan, ig_thung])
    db.flush()

    # ── Supplier ─────────────────────────────────────────────────────────────────
    sup = Supplier(
        code="NX",
        name="Nhà Xuất NX",
        supplier_type="goods",
        is_active=True,
        tax_code="0123456789",
        contact_person="Người LH NX",
    )
    db.add(sup)
    db.flush()

    # ── CategoryAssignee: Nhãn + Thùng → primary=nstm, backup=backup ─────────────
    ca_nhan = CategoryAssignee(
        item_group_id=ig_nhan.id,
        primary_employee_id=emp_nstm.id,
        backup_employee_id=emp_backup.id,
    )
    ca_thung = CategoryAssignee(
        item_group_id=ig_thung.id,
        primary_employee_id=emp_nstm.id,
        backup_employee_id=emp_backup.id,
    )
    db.add_all([ca_nhan, ca_thung])
    db.flush()

    # ── Survey "Nhãn" ─────────────────────────────────────────────────────────────
    sv_nhan = Survey(
        code="KS-NHAN-001",
        survey_type="product",
        status="approved",
        item_group="Nhãn",
    )
    db.add(sv_nhan)
    db.flush()

    psl_nhan_1 = SurveyProductLine(
        survey_id=sv_nhan.id,
        supplier_code="NX",
        line_approve="Đã duyệt",
        product_name="Nhãn Sản Phẩm A",
        spec="100x50mm",
        origin="VN",
        quote_unit="cuộn",
        moq=100,
        price_by_volume=5000,
        volume_range="100-1000",
        vat=8,
        delivery_time="7 ngày",
        delivery_place="Kho HN",
        shipping_cost=0,
        sample_ready=True,
        lab_result="Đạt",
        internal_code="NX-NHAN-A",
        nspt_reason="OK",
    )
    psl_nhan_2 = SurveyProductLine(
        survey_id=sv_nhan.id,
        supplier_code="NX",
        line_approve="Đã duyệt",
        product_name="Nhãn Sản Phẩm B",
        spec="80x40mm",
        origin="VN",
        quote_unit="cuộn",
        moq=200,
        price_by_volume=4500,
        volume_range="200-2000",
        vat=8,
        delivery_time="5 ngày",
        delivery_place="Kho HN",
        shipping_cost=0,
        sample_ready=False,
        lab_result="",
        internal_code="NX-NHAN-B",
        nspt_reason="",
    )
    db.add_all([psl_nhan_1, psl_nhan_2])
    db.flush()

    # ── Survey "Thùng" ────────────────────────────────────────────────────────────
    sv_thung = Survey(
        code="KS-THUNG-001",
        survey_type="product",
        status="approved",
        item_group="Thùng",
    )
    db.add(sv_thung)
    db.flush()

    psl_thung_1 = SurveyProductLine(
        survey_id=sv_thung.id,
        supplier_code="NX",
        line_approve="Đã duyệt",
        product_name="Thùng Carton A",
        spec="30x20x15cm",
        origin="VN",
        quote_unit="cái",
        moq=500,
        price_by_volume=8000,
        volume_range="500-5000",
        vat=8,
        delivery_time="10 ngày",
        delivery_place="Kho HN",
        shipping_cost=0,
        sample_ready=True,
        lab_result="Đạt",
        internal_code="NX-THUNG-A",
        nspt_reason="OK",
    )
    psl_thung_2 = SurveyProductLine(
        survey_id=sv_thung.id,
        supplier_code="NX",
        line_approve="Đã duyệt",
        product_name="Thùng Carton B",
        spec="25x20x10cm",
        origin="VN",
        quote_unit="cái",
        moq=1000,
        price_by_volume=6500,
        volume_range="1000-10000",
        vat=8,
        delivery_time="7 ngày",
        delivery_place="Kho HN",
        shipping_cost=0,
        sample_ready=False,
        lab_result="",
        internal_code="NX-THUNG-B",
        nspt_reason="",
    )
    db.add_all([psl_thung_1, psl_thung_2])
    db.commit()

    return SimpleNamespace(
        company_id=company.id,
        dept_id=dept.id,
        emp_req_id=emp_req.id,
        emp_req_code=emp_req.code,
        emp_tp_id=emp_tp.id,
        emp_nstm_id=emp_nstm.id,
        emp_nstm_code=emp_nstm.code,
        emp_backup_id=emp_backup.id,
        emp_backup_code=emp_backup.code,
        u_req_id=u_req.id,
        u_nstm_id=u_nstm.id,
        ig_nhan_id=ig_nhan.id,
        ig_thung_id=ig_thung.id,
        sv_nhan_id=sv_nhan.id,
        sv_thung_id=sv_thung.id,
        psl_nhan_1_id=psl_nhan_1.id,
        psl_nhan_2_id=psl_nhan_2.id,
        psl_thung_1_id=psl_thung_1.id,
        psl_thung_2_id=psl_thung_2.id,
        sup_id=sup.id,
        sup_name=sup.name,
    )
