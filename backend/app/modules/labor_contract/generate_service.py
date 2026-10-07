"""Sinh tệp .docx của HĐ từ mẫu + tệp scan đã ký. Dữ liệu NLĐ lấy từ model THÔ (không qua che
`employee_sensitive`): người có `labor_contract.print` cầm bản HĐ có CCCD / STK — đó là bản chất của HĐLĐ.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from .context_builder import build_context
from .docx_engine import TemplateRejected, render
from .file_response import (delete_files_after_commit, discard_new_file, load_bytes,
                            safe_filename, store_bytes)
from .model import LaborContract
from .template_model import LaborContractTemplate

DOCX_KIND, SIGNED_KIND, CATEGORY = "labor_contract_docx", "labor_contract_signed", "labor-contract"


def document_filename(db: Session, row: LaborContract) -> str:
    """`HDLD-{số}-{họ tên}.docx` — chỉ từ dữ liệu DB, đã làm sạch.

    Số đã mở đầu bằng «HDLD» (mã hệ thống `HDLD005`, hay số tự gõ `HDLD-12`) thì không thêm tiền tố
    nữa — trước đây ra `HDLD-HDLD005-…` (test Chrome 06/10/2026)."""
    emp = db.get(Employee, row.employee_id)
    number = row.contract_no or row.code
    prefix = "" if number.upper().startswith("HDLD") else "HDLD-"
    return safe_filename(f"{prefix}{number}-{emp.full_name if emp else ''}") + ".docx"


def _pick_template(db: Session, row: LaborContract, template_id: int) -> LaborContractTemplate:
    tpl = db.get(LaborContractTemplate, template_id)
    if tpl is None:
        raise HTTPException(400, "Mẫu hợp đồng không tồn tại")
    if not tpl.is_active:
        raise HTTPException(400, "Mẫu hợp đồng đã ngừng dùng")
    #  Mẫu phải CÙNG pháp nhân của HĐ (snapshot lúc tạo, không phải pháp nhân hiện tại của NV)
    #  — tránh HĐ của pháp nhân A in tiêu đề pháp nhân B.
    if tpl.company_id != row.company_id:
        raise HTTPException(400, "Mẫu thuộc pháp nhân khác với pháp nhân của hợp đồng")
    if int(tpl.contract_type) != int(row.contract_type):
        raise HTTPException(400, "Loại hợp đồng của mẫu không khớp với hợp đồng")
    return tpl


def generate(db: Session, user, contract_id: int, template_id: int) -> tuple[LaborContract, str]:
    """Sinh (hoặc sinh lại) tệp. Khóa dòng HĐ để hai người bấm cùng lúc không đè nhau."""
    row = db.query(LaborContract).filter(LaborContract.id == contract_id).with_for_update().first()
    if row is None:
        raise HTTPException(404, "Không tìm thấy hợp đồng")
    if int(row.status) != int(S.DRAFT):
        raise HTTPException(409, "Chỉ sinh được tệp khi hợp đồng ở trạng thái Nháp")
    tpl = _pick_template(db, row, template_id)
    emp = db.get(Employee, row.employee_id)
    if emp is None:
        raise HTTPException(404, "Không tìm thấy nhân viên của hợp đồng")

    _, template_bytes = load_bytes(db, tpl.file_id)
    ctx = build_context(row, emp, db.get(Company, row.company_id),
                        db.get(Department, row.department_id) if row.department_id else None, vn_today())
    try:
        out = render(template_bytes, ctx)
    except TemplateRejected as exc:
        raise HTTPException(422, f"Mẫu không sinh được: {exc.message}")

    old_id, sf = row.generated_file_id, None
    try:
        sf = store_bytes(db, out, document_filename(db, row), DOCX_KIND, CATEGORY, user.id)
        row.generated_file_id, row.generated_at, row.generated_by = sf.id, datetime.now(), user.id
        row.template_id, row.updated_by = tpl.id, user.id
        db.commit()
    except Exception:
        db.rollback()
        discard_new_file(sf)
        raise
    db.refresh(row)
    if old_id:
        delete_files_after_commit(db, old_id)
    return row, tpl.name


def save_signed_file(db: Session, user, row: LaborContract, fileobj, filename: str) -> LaborContract:
    """Bản scan đã ký (pdf/jpg/png — `guard_upload` đọc byte đầu). Chỉ DRAFT/SIGNED."""
    if int(row.status) not in (int(S.DRAFT), int(S.SIGNED)):
        raise HTTPException(409, "Chỉ tải bản đã ký lên khi hợp đồng ở trạng thái Nháp hoặc Đã ký")
    from app.modules.attachment.service import create_stored_file

    old_id, sf = row.signed_file_id, None
    try:
        sf = create_stored_file(db, fileobj=fileobj, filename=safe_filename(filename, "ban-scan"),
                                kind=SIGNED_KIND, category=CATEGORY, actor_id=user.id)
        row.signed_file_id, row.updated_by = sf.id, user.id
        db.commit()
    except Exception:
        db.rollback()
        discard_new_file(sf)
        raise
    db.refresh(row)
    if old_id:
        delete_files_after_commit(db, old_id)
    return row
