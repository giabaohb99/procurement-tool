"""Gộp `LaborContractOut` cho một DANH SÁCH. Tên pháp nhân/phòng/mẫu/người tạo gom mỗi loại MỘT
truy vấn; cờ `can_*` do BACKEND tính (A9) — mỗi hành động MỘT truy vấn phạm vi cho cả trang."""
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department

from . import access, rules
from .lookup import names_map, user_names
from .model import LaborContract
from .schema import LaborContractOut
from .template_model import LaborContractTemplate

ENTITY = "labor_contract"
_EDITABLE = {int(S.DRAFT)}


def serialize_contracts(db: Session, rows: list[LaborContract], user, profile: dict) -> list[dict]:
    if not rows:
        return []
    today = vn_today()
    ids = [r.id for r in rows]
    can = {a: access.ids_allowed(db, LaborContract, ENTITY, ids, user, profile, a)
           for a in ("write", "delete", "print")}
    companies = names_map(db, Company, {r.company_id for r in rows})
    departments = names_map(db, Department, {r.department_id for r in rows})
    templates = names_map(db, LaborContractTemplate, {r.template_id for r in rows})
    creators = user_names(db, {r.created_by for r in rows})

    out: list[dict] = []
    for r in rows:
        writable = r.id in can["write"]
        draft = int(r.status) in _EDITABLE
        out.append(LaborContractOut(
            id=r.id, code=r.code, contract_no=r.contract_no or "", employee_id=r.employee_id,
            company_id=r.company_id, company_name=companies.get(r.company_id, ""),
            department_id=r.department_id, department_name=departments.get(r.department_id, ""),
            template_id=r.template_id, template_name=templates.get(r.template_id, ""),
            contract_type=r.contract_type, status=r.status,
            effective_status=rules.effective_status(r.status, r.end_date, today),
            sign_date=r.sign_date, start_date=r.start_date, end_date=r.end_date,
            job_title=r.job_title or "", work_location=r.work_location or "",
            base_salary=int(r.base_salary or 0), insurance_salary=int(r.insurance_salary or 0),
            allowance=int(r.allowance or 0), allowance_note=r.allowance_note or "", note=r.note or "",
            has_generated_file=bool(r.generated_file_id), generated_at=r.generated_at,
            has_signed_file=bool(r.signed_file_id),
            terminated_date=r.terminated_date, terminate_reason=r.terminate_reason or "",
            created_at=r.created_at, created_by_name=creators.get(r.created_by, ""),
            can_edit=writable and draft,
            can_delete=r.id in can["delete"] and int(r.status) in (int(S.DRAFT), int(S.CANCELLED)),
            can_generate=writable and draft,
            can_print=r.id in can["print"] and bool(r.generated_file_id),
            can_upload_signed=writable and int(r.status) in (int(S.DRAFT), int(S.SIGNED)),
            transitions=list(rules.allowed_transitions(r.status)) if writable else [],
        ).model_dump())
    return out
