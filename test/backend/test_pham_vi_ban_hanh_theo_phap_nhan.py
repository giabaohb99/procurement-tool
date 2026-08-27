"""Phạm vi người xem sau BAN HÀNH — văn bản gốc và bản clone.

Bốn ca nghiệp vụ phải chạy giống nhau ở hai pháp nhân:

1. bao gồm một pháp nhân                     → mọi thành viên được áp dụng;
2. bao gồm pháp nhân, loại trừ vài cá nhân   → chỉ những người đó không thấy;
3. bao gồm pháp nhân, loại trừ một phòng     → cả phòng đó không thấy;
4. loại trừ phòng, cho phép lại một cá nhân  → cá nhân ngoại lệ vẫn thấy.

Nhóm thứ hai xóa phạm vi được chép từ bản gốc rồi khai lại trực tiếp trên bản
clone trước khi ban hành. Nhờ vậy bài kiểm chứng minh pháp nhân nhận tự quyết
định phạm vi của bản mình, không phụ thuộc cấu hình của pháp nhân gốc.
"""
import pytest

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import clone_service, scope_service, service
from app.modules.document.schema import DocumentCreate
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              DIM_EMPLOYEE, MODE_EXCLUDE,
                                              MODE_INCLUDE, DocumentScope)
from app.modules.employee.model import Employee

ACTOR_GOC = 1
ACTOR_CON = 2


@pytest.fixture()
def to_chuc(db, seed):
    origin = db.get(Company, seed.company_id)
    origin.issue_code = "GOC"
    con = Company(code="CON", name="Pháp nhân con", issue_code="CON",
                  level=2, is_active=True)

    phong_khac_goc = Department(code="PB-GOC-2", name="Phòng khác gốc",
                                company_id=origin.id, is_active=True)
    phong_chinh_con = Department(code="PB-CON-1", name="Phòng chính con",
                                 company_id=0, is_active=True)
    phong_khac_con = Department(code="PB-CON-2", name="Phòng khác con",
                                company_id=0, is_active=True)
    kind = DocType(code="QCPV", name="Quy chế phạm vi", id_scheme=1, number_when=2)
    db.add_all([con, phong_khac_goc, phong_chinh_con, phong_khac_con, kind])
    db.flush()
    phong_chinh_con.company_id = con.id
    phong_khac_con.company_id = con.id

    nguoi_khac_goc = Employee(code="NV-GOC-3", full_name="Người phòng khác gốc",
                              company_id=origin.id, department_id=phong_khac_goc.id,
                              is_active=True)
    nguoi_mot_con = Employee(code="NV-CON-1", full_name="Người một pháp nhân con",
                             company_id=con.id, department_id=phong_chinh_con.id,
                             is_active=True)
    nguoi_hai_con = Employee(code="NV-CON-2", full_name="Người hai pháp nhân con",
                             company_id=con.id, department_id=phong_chinh_con.id,
                             is_active=True)
    nguoi_khac_con = Employee(code="NV-CON-3", full_name="Người phòng khác con",
                              company_id=con.id, department_id=phong_khac_con.id,
                              is_active=True)
    db.add_all([nguoi_khac_goc, nguoi_mot_con, nguoi_hai_con, nguoi_khac_con])
    db.commit()

    return {
        "goc": origin,
        "con": con,
        "loai": kind,
        "phong_goc": db.get(Department, seed.dept_id),
        "phong_con": phong_chinh_con,
        "nguoi_goc": [
            db.get(Employee, seed.emp_tp_id),
            db.get(Employee, seed.emp_nstm_id),
            nguoi_khac_goc,
        ],
        "nguoi_con": [nguoi_mot_con, nguoi_hai_con, nguoi_khac_con],
    }


def _tao_nhap(db, to_chuc, title: str):
    return service.create_document(db, DocumentCreate(
        doc_type_id=to_chuc["loai"].id,
        company_id=to_chuc["goc"].id,
        department_id=to_chuc["phong_goc"].id,
        owner_employee_id=to_chuc["nguoi_goc"][0].id,
        title=title,
        content_html="<p>Nội dung áp dụng.</p>",
    ), ACTOR_GOC)


def _them_pham_vi(db, doc_id: int, *, dim: int, mode: int,
                  company_id: int | None = None,
                  department_id: int | None = None,
                  employee_id: int | None = None):
    db.add(DocumentScope(
        document_id=doc_id,
        dim=dim,
        mode=mode,
        company_id=company_id,
        department_id=department_id,
        employee_id=employee_id,
        created_by=ACTOR_GOC,
        updated_by=ACTOR_GOC,
    ))


def _khai_case(db, doc_id: int, case: str, company: Company,
               department: Department, employees: list[Employee]):
    # Nền của cả bốn ca: ban hành cho đúng MỘT pháp nhân.
    _them_pham_vi(db, doc_id, dim=DIM_COMPANY, mode=MODE_INCLUDE,
                  company_id=company.id)

    if case == "loai_ca_nhan":
        for employee in employees[:2]:
            _them_pham_vi(db, doc_id, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
                          employee_id=employee.id)
    elif case in {"loai_phong", "ngoai_le_ca_nhan"}:
        _them_pham_vi(db, doc_id, dim=DIM_DEPARTMENT, mode=MODE_EXCLUDE,
                      company_id=company.id, department_id=department.id)
        if case == "ngoai_le_ca_nhan":
            _them_pham_vi(db, doc_id, dim=DIM_EMPLOYEE, mode=MODE_INCLUDE,
                          employee_id=employees[0].id)
    db.commit()


def _ban_hanh(db, doc, actor: int):
    service.submit(db, doc, actor)
    service.approve(db, doc, actor)
    db.refresh(doc)


CASES = [
    pytest.param("ca_phap_nhan", (True, True, True), id="ca-phap-nhan"),
    pytest.param("loai_ca_nhan", (False, False, True), id="loai-vai-ca-nhan"),
    pytest.param("loai_phong", (False, False, True), id="loai-mot-phong-ban"),
    pytest.param("ngoai_le_ca_nhan", (True, False, True),
                 id="loai-phong-nhung-cho-mot-nguoi"),
]


def _assert_pham_vi(db, doc_id: int, employees: list[Employee], expected: tuple[bool, ...]):
    for employee, should_see in zip(employees, expected, strict=True):
        assert scope_service.applies_to(db, doc_id, employee) is should_see
        assert (doc_id in scope_service.document_ids_for(db, employee)) is should_see


@pytest.mark.parametrize(("case", "expected"), CASES)
def test_van_ban_goc_ban_hanh_cho_mot_phap_nhan(db, to_chuc, case, expected):
    doc = _tao_nhap(db, to_chuc, f"Văn bản gốc — {case}")
    _khai_case(db, doc.id, case, to_chuc["goc"], to_chuc["phong_goc"],
               to_chuc["nguoi_goc"])

    _ban_hanh(db, doc, ACTOR_GOC)

    assert clone_service.clones_of(db, doc.id) == []
    _assert_pham_vi(db, doc.id, to_chuc["nguoi_goc"], expected)


@pytest.mark.parametrize(("case", "expected"), CASES)
def test_phap_nhan_con_tu_chon_pham_vi_khi_ban_hanh_clone(
    db, to_chuc, case, expected,
):
    origin = _tao_nhap(db, to_chuc, f"Văn bản sinh clone — {case}")
    _them_pham_vi(db, origin.id, dim=DIM_COMPANY, mode=MODE_INCLUDE,
                  company_id=to_chuc["con"].id)
    db.commit()
    _ban_hanh(db, origin, ACTOR_GOC)

    clones = clone_service.clones_of(db, origin.id)
    assert len(clones) == 1
    clone = clones[0]
    assert clone.company_id == to_chuc["con"].id

    # Pháp nhân con bỏ phạm vi được chép từ gốc và tự khai lại cho bản của mình.
    db.query(DocumentScope).filter(DocumentScope.document_id == clone.id).delete()
    clone.department_id = to_chuc["phong_con"].id
    clone.owner_employee_id = to_chuc["nguoi_con"][2].id
    _khai_case(db, clone.id, case, to_chuc["con"], to_chuc["phong_con"],
               to_chuc["nguoi_con"])

    _ban_hanh(db, clone, ACTOR_CON)

    _assert_pham_vi(db, clone.id, to_chuc["nguoi_con"], expected)
