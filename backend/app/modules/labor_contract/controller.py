"""API Hợp đồng lao động. Hai nhóm đường: theo nhân sự (`/api/employees/{eid}/...`) và theo id HĐ
(`/api/labor-contracts/{id}/...`), khóa quyền `labor_contract` (lương = nhạy cảm, tách khỏi `employee`).

⚠️ Router này PHẢI include TRƯỚC `employee_router` trong `main.py` (chung tiền tố `/api/employees`).
Mọi đường `{id}` đi qua `get_scoped`; tải bản sinh đòi thêm `print`; không trả `url`/`file_key`.
"""
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.database import get_db
from app.core.labor_contract_codes import LABOR_CONTRACT_STATUS_LABELS, LaborContractStatus
from app.core.response import success

from . import access, generate_service, service
from .file_response import DOCX_MIME, download_response, load_bytes
from .model import LaborContract
from .schema import GenerateIn, LaborContractCreate, LaborContractUpdate, TransitionIn
from .serializer import serialize_contracts

router = APIRouter(tags=["labor-contract"])
ENTITY = service.ENTITY


def _scoped(db: Session, cid: int, user, profile: dict, action: str, lock: bool = False) -> LaborContract:
    return access.get_or_404_scoped(db, LaborContract, ENTITY, cid, user, profile, action,
                                    "Không tìm thấy hợp đồng lao động", lock=lock)


def _item(db: Session, row: LaborContract, user, profile: dict) -> dict:
    return serialize_contracts(db, [row], user, profile)[0]


def _audit(db: Session, user, row: LaborContract, action: str, message: str) -> None:
    audit_record(db, user.id, ENTITY, row.id, action, message, doc_code=row.code)


# ---- Theo nhân sự ---------------------------------------------------------------------------
@router.get("/api/employees/{eid}/labor-contracts")
def list_employee_contracts(eid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    profile = get_perm_profile(db, user)
    emp = service.get_employee_or_404(db, eid)
    rows = service.list_for_employee(db, user, profile, eid)
    #  `can_create` chỉ là gợi ý nút bấm (quyền + hồ sơ có pháp nhân); chốt thật ở POST (403 theo phạm vi).
    return success({"items": serialize_contracts(db, rows, user, profile),
                    "can_create": access.has_perm(profile, ENTITY, "create") and bool(emp.company_id)})


@router.get("/api/employees/{eid}/labor-contract-templates")
def list_employee_templates(eid: int, contract_type: int | None = None, db: Session = Depends(get_db),
                            user=Depends(get_current_user)):
    profile = get_perm_profile(db, user)
    if not (access.has_perm(profile, ENTITY, "create") or access.has_perm(profile, ENTITY, "write")):
        raise HTTPException(403, "Không có quyền: create/write labor_contract")
    emp = service.get_employee_or_404(db, eid)
    #  Cùng luật phạm vi với POST lập HĐ: nhân sự ngoài phạm vi thì không lộ tên mẫu của pháp nhân đó.
    probe = LaborContract(code=f"_probe_{eid}", employee_id=emp.id, company_id=emp.company_id or 0,
                          department_id=emp.department_id or 0, contract_type=0,
                          start_date=date.today(), created_by=user.id, updated_by=user.id)
    #  Chỉ có `write` (sinh lại HĐ nháp) thì đủ khi nhân sự này có ít nhất một HĐ trong phạm vi `write`.
    ok = (access.has_perm(profile, ENTITY, "create") and profile.get("employee_id") != emp.id
          and access.can_create_for(db, LaborContract, ENTITY, probe, user, profile))
    if not ok and access.has_perm(profile, ENTITY, "write"):
        ids = [i for (i,) in db.query(LaborContract.id).filter(LaborContract.employee_id == emp.id).all()]
        ok = bool(access.ids_allowed(db, LaborContract, ENTITY, ids, user, profile, "write"))
    if not ok:
        raise HTTPException(403, service.OUT_OF_SCOPE)
    rows = service.templates_for_employee(db, emp, contract_type)
    return success([{"id": r.id, "name": r.name, "contract_type": r.contract_type} for r in rows])


@router.post("/api/employees/{eid}/labor-contracts")
def create_contract(eid: int, data: LaborContractCreate, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "create"))):
    profile = get_perm_profile(db, user)
    emp = service.get_employee_or_404(db, eid)
    row, warnings = service.create(db, user, profile, emp, data)
    _audit(db, user, row, "create", f"Lập hợp đồng lao động cho {emp.full_name}")
    return success({"item": _item(db, row, user, profile), "warnings": warnings},
                   "Đã lập hợp đồng lao động", 201)


# ---- Theo id HĐ -----------------------------------------------------------------------------
@router.get("/api/labor-contracts/{cid}")
def get_contract(cid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    profile = get_perm_profile(db, user)
    return success(_item(db, _scoped(db, cid, user, profile, "read"), user, profile))


@router.patch("/api/labor-contracts/{cid}")
def update_contract(cid: int, data: LaborContractUpdate, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "write"))):
    profile = get_perm_profile(db, user)
    row, warnings = service.update(db, user, _scoped(db, cid, user, profile, "write", lock=True), data)
    _audit(db, user, row, "update", "Sửa hợp đồng lao động")
    return success({"item": _item(db, row, user, profile), "warnings": warnings}, "Đã cập nhật")


@router.get("/api/labor-contracts/{cid}/templates")
def list_contract_templates(cid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Ô chọn mẫu của hộp «Sinh tệp»: mẫu theo pháp nhân + loại CỦA HĐ (không theo NV hiện tại)."""
    row = _scoped(db, cid, user, get_perm_profile(db, user), "write")
    return success([{"id": r.id, "name": r.name, "contract_type": r.contract_type}
                    for r in service.templates_for_contract(db, row)])


@router.delete("/api/labor-contracts/{cid}")
def delete_contract(cid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    profile = get_perm_profile(db, user)
    row = _scoped(db, cid, user, profile, "delete", lock=True)
    code = row.code
    service.delete(db, row)
    audit_record(db, user.id, ENTITY, cid, "delete", "Xóa hợp đồng lao động", doc_code=code)
    return success(None, "Đã xóa hợp đồng lao động")


@router.post("/api/labor-contracts/{cid}/generate")
def generate_document(cid: int, data: GenerateIn, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "write"))):
    profile = get_perm_profile(db, user)
    _scoped(db, cid, user, profile, "write")
    row, template_name = generate_service.generate(db, user, cid, data.template_id)
    _audit(db, user, row, "update", f"Sinh tệp hợp đồng từ mẫu «{template_name}»")
    return success(_item(db, row, user, profile), "Đã sinh tệp hợp đồng")


@router.get("/api/labor-contracts/{cid}/document")
def download_document(cid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "print"))):
    profile = get_perm_profile(db, user)
    row = _scoped(db, cid, user, profile, "print")
    if not row.generated_file_id:
        raise HTTPException(404, "Hợp đồng chưa có tệp — hãy sinh tệp từ mẫu trước")
    _, data = load_bytes(db, row.generated_file_id)
    return download_response(data, generate_service.document_filename(db, row), DOCX_MIME)


@router.put("/api/labor-contracts/{cid}/signed-file")
def upload_signed_file(cid: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                       user=Depends(require(ENTITY, "write"))):
    profile = get_perm_profile(db, user)
    row = generate_service.save_signed_file(db, user, _scoped(db, cid, user, profile, "write", lock=True),
                                            file.file, file.filename or "")
    _audit(db, user, row, "update", "Tải bản hợp đồng đã ký")
    return success(_item(db, row, user, profile), "Đã lưu bản đã ký")


@router.get("/api/labor-contracts/{cid}/signed-file")
def download_signed_file(cid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    row = _scoped(db, cid, user, get_perm_profile(db, user), "read")
    if not row.signed_file_id:
        raise HTTPException(404, "Hợp đồng chưa có bản đã ký")
    sf, data = load_bytes(db, row.signed_file_id)
    return download_response(data, sf.filename, sf.content_type or "application/octet-stream")


@router.post("/api/labor-contracts/{cid}/transition")
def transition_contract(cid: int, data: TransitionIn, db: Session = Depends(get_db),
                        user=Depends(require(ENTITY, "write"))):
    profile = get_perm_profile(db, user)
    row = service.transition(db, user, _scoped(db, cid, user, profile, "write", lock=True), data)
    _audit(db, user, row, "document_status", f"Chuyển trạng thái hợp đồng sang «{LABOR_CONTRACT_STATUS_LABELS[LaborContractStatus(int(row.status))]}»")
    return success(_item(db, row, user, profile), "Đã chuyển trạng thái")
