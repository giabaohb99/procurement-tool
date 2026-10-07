"""Nghiệp vụ HĐLĐ: danh sách theo nhân sự, tạo, sửa, xóa, chuyển trạng thái, dọn khi xóa hồ sơ.

Đơn vị lập HĐ = pháp nhân/phòng của nhân sự LÚC TẠO (snapshot). Nhân sự đổi pháp nhân sau đó thì
HĐ cũ giữ pháp nhân cũ.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.scoping import apply_scope
from app.core.utils import generate_code
from app.modules.employee.model import Employee

from . import access, rules
from .file_response import delete_files_after_commit
from .model import LaborContract
from .schema import LaborContractCreate, LaborContractUpdate, TransitionIn
from .template_model import LaborContractTemplate

ENTITY = "labor_contract"
OUT_OF_SCOPE = "Nhân sự thuộc pháp nhân / phòng ngoài phạm vi của bạn"
SELF_CREATE = "Không được tự lập hợp đồng lao động cho chính mình"
_CLOSED = (int(S.DRAFT), int(S.CANCELLED))   # được xóa; các trạng thái khác là chứng từ pháp lý


def get_employee_or_404(db: Session, eid: int) -> Employee:
    emp = db.get(Employee, eid)
    if emp is None:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    return emp


def list_for_employee(db: Session, user, profile: dict, eid: int) -> list[LaborContract]:
    q = apply_scope(db.query(LaborContract).filter(LaborContract.employee_id == eid),
                    LaborContract, ENTITY, user, profile, "read")
    return q.order_by(LaborContract.start_date.desc(), LaborContract.id.desc()).all()


def templates_for_employee(db: Session, emp: Employee, contract_type: int | None):
    """Mẫu `is_active` của pháp nhân HIỆN TẠI của nhân sự (+ đúng loại) — để chọn mẫu lúc lập."""
    q = db.query(LaborContractTemplate).filter(
        LaborContractTemplate.company_id == (emp.company_id or 0),
        LaborContractTemplate.is_active.is_(True))
    if contract_type:
        q = q.filter(LaborContractTemplate.contract_type == contract_type)
    return q.order_by(LaborContractTemplate.name).all() if emp.company_id else []


def templates_for_contract(db: Session, row: LaborContract):
    """Mẫu `is_active` đúng pháp nhân + đúng loại của CHÍNH HĐ (snapshot lúc lập, không theo pháp
    nhân hiện tại của nhân sự) — khớp điều kiện `generate_service._pick_template`."""
    return (db.query(LaborContractTemplate)
            .filter(LaborContractTemplate.company_id == row.company_id,
                    LaborContractTemplate.contract_type == row.contract_type,
                    LaborContractTemplate.is_active.is_(True))
            .order_by(LaborContractTemplate.name).all())


def ensure_not_self(profile: dict, emp: Employee) -> None:
    """Không ai lập HĐLĐ cho CHÍNH MÌNH (tự đặt lương / tự soạn chứng từ pháp lý) → 403."""
    if emp.id and (profile or {}).get("employee_id") == emp.id:
        raise HTTPException(403, SELF_CREATE)


def _ensure_contract_no_unique(db: Session, company_id: int, contract_no: str,
                               exclude_id: int | None = None) -> None:
    if not contract_no:
        return
    q = db.query(LaborContract.id).filter(
        LaborContract.company_id == company_id, LaborContract.contract_no == contract_no,
        LaborContract.status != int(S.CANCELLED))
    if exclude_id:
        q = q.filter(LaborContract.id != exclude_id)
    if q.first():
        raise HTTPException(400, f"Số hợp đồng «{contract_no}» đã tồn tại trong pháp nhân này")


def create(db: Session, user, profile: dict, emp: Employee,
           data: LaborContractCreate) -> tuple[LaborContract, list[str]]:
    ensure_not_self(profile, emp)
    if not emp.company_id:
        raise HTTPException(400, "Nhân sự chưa gắn pháp nhân — cập nhật hồ sơ trước khi lập hợp đồng")
    _ensure_contract_no_unique(db, emp.company_id, data.contract_no)
    row = LaborContract(
        code=generate_code(db, LaborContract, "HDLD"), contract_no=data.contract_no,
        employee_id=emp.id, company_id=emp.company_id, department_id=emp.department_id or 0,
        contract_type=data.contract_type, status=int(S.DRAFT),
        start_date=data.start_date, end_date=data.end_date,
        job_title=data.job_title if data.job_title is not None else (emp.position or "")[:100],
        work_location=data.work_location if data.work_location is not None else (emp.work_location or ""),
        base_salary=data.base_salary, insurance_salary=data.insurance_salary,
        allowance=data.allowance, allowance_note=data.allowance_note, note=data.note,
        created_by=user.id, updated_by=user.id)
    db.add(row)
    access.ensure_created_in_scope(db, LaborContract, ENTITY, row, user, profile, OUT_OF_SCOPE)
    db.commit()
    db.refresh(row)
    return row, rules.duration_warnings(row.contract_type, row.start_date, row.end_date)


def update(db: Session, user, row: LaborContract,
           data: LaborContractUpdate) -> tuple[LaborContract, list[str]]:
    if int(row.status) != int(S.DRAFT):
        raise HTTPException(409, "Chỉ sửa được hợp đồng ở trạng thái Nháp")
    values = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None
              or k == "end_date"}   # end_date=None là hợp lệ (gỡ ngày kết thúc); cột khác không nhận null
    merged = {k: values.get(k, getattr(row, k)) for k in ("contract_type", "start_date", "end_date")}
    try:
        rules.check_dates(merged["contract_type"], merged["start_date"], merged["end_date"])
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if "contract_no" in values and values["contract_no"] != row.contract_no:
        _ensure_contract_no_unique(db, row.company_id, values["contract_no"], row.id)
    #  Mọi trường sửa được đều đi vào ngữ cảnh mẫu (số HĐ, ngày, chức danh, lương, phụ cấp, ghi chú):
    #  đổi giá trị thật sự thì tệp .docx đã sinh thành BẢN CŨ (in ra số liệu sai) → bỏ, buộc sinh lại.
    changed = any(getattr(row, k) != v for k, v in values.items())
    stale_file_id = row.generated_file_id if changed else 0
    for key, value in values.items():
        setattr(row, key, value)
    if stale_file_id:
        row.generated_file_id, row.generated_at, row.generated_by, row.template_id = 0, None, 0, 0
    row.updated_by = user.id
    db.commit()
    db.refresh(row)
    if stale_file_id:   # xóa tệp SAU commit (cùng khuôn `generate` khi sinh lại)
        delete_files_after_commit(db, stale_file_id)
    return row, rules.duration_warnings(row.contract_type, row.start_date, row.end_date)


def delete(db: Session, row: LaborContract) -> None:
    if int(row.status) not in _CLOSED:
        raise HTTPException(409, "Chỉ xóa được hợp đồng Nháp hoặc Đã hủy")
    file_ids = [row.generated_file_id, row.signed_file_id]
    db.delete(row)
    db.commit()
    delete_files_after_commit(db, *[f for f in file_ids if f])


def transition(db: Session, user, row: LaborContract, data: TransitionIn) -> LaborContract:
    try:
        plan = rules.plan_transition(status=row.status, start_date=row.start_date,
                                     to_status=data.to_status, on_date=data.date, reason=data.reason)
    except rules.RuleViolation as exc:
        raise HTTPException(exc.status_code, exc.message)
    row.status = plan.status
    for key, value in plan.changes.items():
        setattr(row, key, value)
    row.updated_by = user.id
    db.commit()
    db.refresh(row)
    return row


# ---- Xóa hồ sơ nhân sự (`employee.service.delete_employee` gọi) --------------------------------
def ensure_employee_deletable(db: Session, eid: int) -> None:
    """Còn HĐ Đã ký / Đã chấm dứt thì CHẶN xóa hồ sơ (chứng từ pháp lý, 409)."""
    blocking = (db.query(LaborContract.id).filter(
        LaborContract.employee_id == eid, LaborContract.status.notin_(_CLOSED)).count())
    if blocking:
        raise HTTPException(
            409, f"Nhân sự còn {blocking} hợp đồng lao động đã ký / đã chấm dứt — không xóa được hồ sơ. "
                 "Hãy chuyển nhân sự sang «nghỉ việc» thay vì xóa.")


def delete_all_of(db: Session, eid: int) -> None:
    """Dọn HĐ Nháp/Đã hủy + tệp của người này. KHÔNG commit — chung giao dịch với nơi gọi."""
    from app.modules.attachment.service import delete_stored_file

    rows = db.query(LaborContract).filter(LaborContract.employee_id == eid,
                                          LaborContract.status.in_(_CLOSED)).all()
    for r in rows:
        for fid in (r.generated_file_id, r.signed_file_id):
            if fid:
                delete_stored_file(db, fid)
        db.delete(r)

