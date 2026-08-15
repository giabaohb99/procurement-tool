import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.department.model import Department, DepartmentCompany
from app.modules.department.schema import DepartmentCompanyInput
from app.modules.department.service import replace_department_companies
from app.modules.document.numbering import _department_code
from app.modules.employee.model import Employee


def _item(company_id: int, manager_id: int | None = None, override: str = ""):
    return DepartmentCompanyInput(
        company_id=company_id,
        manager_employee_id=manager_id,
        issue_code_override=override,
        is_active=True,
    )


def test_department_company_keeps_manager_and_issue_code_per_legal_entity(db, seed):
    second_company = Company(code="CT02", name="Công ty Hai", issue_code="CTHAI")
    db.add(second_company)
    db.flush()
    second_manager = Employee(
        code="TP02",
        full_name="Trưởng Phòng Hai",
        company_id=second_company.id,
        department_id=seed.dept_id,
        is_active=True,
    )
    db.add(second_manager)
    db.commit()

    rows = replace_department_companies(
        db,
        seed.dept_id,
        [
            _item(seed.company_id, seed.emp_tp_id),
            _item(second_company.id, second_manager.id, "PBHAI"),
        ],
        user_id=1,
    )

    assert len(rows) == 2
    assert db.get(Department, seed.dept_id).manager_id == seed.emp_tp_id
    assert _department_code(db, seed.dept_id, second_company.id) == "PBHAI"

    department = db.get(Department, seed.dept_id)
    department.kind = 2
    db.commit()
    assert _department_code(db, seed.dept_id, second_company.id) == ""


def test_department_company_soft_disables_omitted_legal_entity(db, seed):
    second_company = Company(code="CT02", name="Công ty Hai")
    db.add(second_company)
    db.commit()

    replace_department_companies(
        db,
        seed.dept_id,
        [_item(seed.company_id), _item(second_company.id)],
        user_id=1,
    )
    replace_department_companies(
        db,
        seed.dept_id,
        [_item(seed.company_id)],
        user_id=1,
    )

    removed = (
        db.query(DepartmentCompany)
        .filter(
            DepartmentCompany.department_id == seed.dept_id,
            DepartmentCompany.company_id == second_company.id,
        )
        .one()
    )
    assert removed.is_active is False


def test_department_company_rejects_manager_from_another_legal_entity(db, seed):
    second_company = Company(code="CT02", name="Công ty Hai")
    db.add(second_company)
    db.commit()

    with pytest.raises(HTTPException, match="không thuộc pháp nhân"):
        replace_department_companies(
            db,
            seed.dept_id,
            [_item(seed.company_id), _item(second_company.id, seed.emp_tp_id)],
            user_id=1,
        )
