"""Sinh tệp .docx của HĐ từ mẫu + tệp scan đã ký. Dữ liệu NLĐ lấy từ model THÔ (không qua che
`employee_sensitive`): người có `labor_contract.print` cầm bản HĐ có CCCD / STK — đó là bản chất của HĐLĐ.
"""
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from .context_builder import build_context
from .contract_custom_values import ensure_required_filled
from .variable_registry import custom_context, custom_rows
from .docx_engine import TemplateRejected, render
from .file_response import (delete_files_after_commit, discard_new_file, load_bytes,
                            safe_filename, store_bytes)
from .model import LaborContract
from .template_model import LaborContractTemplate

log = logging.getLogger("app.labor_contract")
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
    # Tường minh qua lớp con STI (chỉ kind=2) — id của mẫu văn bản thường ra None.
    tpl = (db.query(LaborContractTemplate)
           .filter(LaborContractTemplate.id == template_id).first())
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


def _with_custom_variables(db: Session, row: LaborContract, tpl: LaborContractTemplate,
                           ctx: dict[str, str]) -> dict[str, str]:
    """duoc-CR-630: ghép biến TÙY CHỈNH vào ngữ cảnh + hai lưới an toàn trước khi render.

    1) Mẫu dùng biến đã bị XÓA khỏi danh mục (đua xóa / tải mẫu) → 422 rõ ràng (render StrictUndefined
       sẽ nổ khó hiểu). 2) Biến BẮT BUỘC mà mẫu dùng còn trống → 422 nêu NHÃN (không nêu giá trị)."""
    rows = custom_rows(db)
    custom = custom_context(rows, row.custom_values)
    clash = sorted(set(ctx) & set(custom))
    if clash:   # dữ liệu lệch (dòng DB tùy chỉnh trùng mã hệ thống): giá trị hệ thống THẮNG, không làm hỏng việc sinh
        log.error("Biến tùy chỉnh trùng biến hệ thống, bỏ qua giá trị tùy chỉnh: %s", ", ".join(clash))
        custom = {k: v for k, v in custom.items() if k not in clash}
    merged = {**ctx, **custom}
    placeholders = tpl.placeholders or []
    gone = sorted(set(placeholders) - set(merged))
    if gone:
        raise HTTPException(422, "Mẫu dùng biến đã bị xóa khỏi danh mục: " + ", ".join(gone)
                                 + " — hãy sửa lại mẫu")
    ensure_required_filled(db, row.custom_values, placeholders, "sinh tệp")
    return merged


def generate(db: Session, user, contract_id: int, template_id: int) -> tuple[LaborContract, str]:
    """Sinh (hoặc sinh lại) tệp. Khóa dòng HĐ để hai người bấm cùng lúc không đè nhau."""
    row = db.query(LaborContract).filter(LaborContract.id == contract_id).with_for_update().first()
    if row is None or row.is_deleted:   # ai-CR-177: HĐ đã xóa mềm coi như không có
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
    ctx = _with_custom_variables(db, row, tpl, ctx)
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
