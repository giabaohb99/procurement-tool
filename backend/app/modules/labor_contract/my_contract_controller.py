"""«Hợp đồng của tôi» (duoc-CR-652): nhân sự TỰ XEM hợp đồng lao động của chính mình, CHỈ ĐỌC.

Không dùng khóa quyền `labor_contract` — đây là ngoại lệ «của chính mình» cho mọi tài khoản có hồ sơ nhân sự
(cùng tinh thần `employee_sensitive` tự xem). Vì không có `apply_scope` che chắn nên BA luật sau là hàng rào duy nhất:

  1. Nhân sự suy ra CHỈ từ token (`user.employee_id`); không có tham số nào chọn người. `employee_id` rỗng/0 ⇒
     danh sách rỗng và KHÔNG truy vấn (tránh khớp nhầm các dòng `employee_id = 0`).
  2. Chỉ trạng thái LƯU `SELF_VIEW_STATUSES` (Đã ký / Đã chấm dứt; «Hết hạn» là SIGNED + hết ngày) và chưa xóa mềm.
     Nháp / Đã hủy ⇒ 404 như id không tồn tại (còn soạn, lương chưa chốt).
  3. Id của người khác ⇒ 404 (không phân biệt «không có» với «của người khác»).

Tải tệp dùng lại đúng hàm của HR (`file_response`, `generate_service.document_filename`) — logic tệp ở một chỗ.
Không ghi nhật ký kiểm toán khi xem (xem lương của chính mình); không trả id tệp / url / file_key.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.labor_contract_codes import SELF_VIEW_STATUSES
from app.core.response import success
from app.core.vn_time import vn_today
from app.modules.company.model import Company

from . import generate_service, rules
from .file_response import DOCX_MIME, download_response, load_bytes
from .lookup import names_map
from .model import LaborContract

router = APIRouter(prefix="/api/me/labor-contracts", tags=["labor-contract"])
NOT_FOUND = "Không tìm thấy hợp đồng lao động"


class MyLaborContractOut(BaseModel):
    """Hình dạng TRẢ RA cho chính chủ — không lẫn `custom_values`, ghi chú nội bộ, người tạo, id tệp."""

    id: int
    code: str
    contract_no: str = ""
    company_name: str = ""
    contract_type: int
    status: int
    effective_status: int
    sign_date: date | None = None
    start_date: date
    end_date: date | None = None
    terminated_date: date | None = None
    job_title: str = ""
    base_salary: int = 0
    has_generated_file: bool = False
    has_signed_file: bool = False


def _own_query(db: Session, user):
    """Truy vấn HĐ của CHÍNH người đăng nhập, đúng trạng thái được xem. `None` nếu tài khoản chưa gắn nhân sự."""
    employee_id = int(getattr(user, "employee_id", 0) or 0)
    if employee_id <= 0:
        return None
    return db.query(LaborContract).filter(
        LaborContract.employee_id == employee_id,
        LaborContract.status.in_(SELF_VIEW_STATUSES),
        LaborContract.is_deleted == False)  # noqa: E712


def _get_own_or_404(db: Session, user, cid: int) -> LaborContract:
    q = _own_query(db, user)
    row = q.filter(LaborContract.id == cid).first() if q is not None else None
    if row is None:
        raise HTTPException(404, NOT_FOUND)
    return row


@router.get("")
def list_my_contracts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = _own_query(db, user)
    rows = q.order_by(LaborContract.start_date.desc(), LaborContract.id.desc()).all() if q is not None else []
    today = vn_today()
    companies = names_map(db, Company, {r.company_id for r in rows})
    items = [MyLaborContractOut(
        id=r.id, code=r.code, contract_no=r.contract_no or "", company_name=companies.get(r.company_id, ""),
        contract_type=r.contract_type, status=r.status,
        effective_status=rules.effective_status(r.status, r.end_date, today),
        sign_date=r.sign_date, start_date=r.start_date, end_date=r.end_date, terminated_date=r.terminated_date,
        job_title=r.job_title or "", base_salary=int(r.base_salary or 0),
        has_generated_file=bool(r.generated_file_id), has_signed_file=bool(r.signed_file_id),
    ).model_dump(mode="json") for r in rows]
    return success({"items": items})


@router.get("/{cid}/document")
def download_my_document(cid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = _get_own_or_404(db, user, cid)
    if not row.generated_file_id:
        raise HTTPException(404, "Hợp đồng chưa có bản mềm")
    _, data = load_bytes(db, row.generated_file_id)
    return download_response(data, generate_service.document_filename(db, row), DOCX_MIME)


@router.get("/{cid}/signed-file")
def download_my_signed_file(cid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = _get_own_or_404(db, user, cid)
    if not row.signed_file_id:
        raise HTTPException(404, "Hợp đồng chưa có bản đã ký")
    sf, data = load_bytes(db, row.signed_file_id)
    return download_response(data, sf.filename, sf.content_type or "application/octet-stream")
