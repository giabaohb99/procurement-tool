"""API MÃ ĐƯA VÀO SỐ HIỆU — sửa tại chỗ từ trang Quy tắc đánh số (CR-118).

Gác bằng `doc_type` (quyền đang mở chính trang Quy tắc đánh số) chứ không phải
`company` / `department`: người khai quy tắc là văn thư, họ cần sửa **đúng cột
mã** mà không phải có quyền vào hồ sơ nhân sự. Đường này cũng chỉ ghi được đúng
cột đó — xem `issue_code_service`.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import issue_code_service as service

router = APIRouter(prefix="/api/issue-codes", tags=["issue-code"])


class IssueCodeUpdate(BaseModel):
    """Sửa một mã. `kind` là một trong `issue_code_service.KIND_*`."""

    kind: str
    id: int
    #  Chỉ dùng cho `department_company` — mã riêng của phòng TẠI một pháp nhân.
    company_id: int | None = None
    issue_code: str = Field(default="", max_length=20)
    #  Người dùng đã đọc cảnh báo "đơn vị này đã cấp số" và vẫn muốn đổi.
    #  Mặc định `False`: chốt D07 phải là thứ có sẵn, không phải thứ phải bật.
    force: bool = False


@router.get("")
def list_issue_codes(db: Session = Depends(get_db),
                     user=Depends(require("doc_numbering_rule", "read"))):
    """Mọi mã đang đi vào số hiệu, gom theo bốn thẻ của mẫu."""
    return success(service.danh_sach(db))


@router.patch("")
def update_issue_code(data: IssueCodeUpdate, db: Session = Depends(get_db),
                      user=Depends(require("doc_numbering_rule", "write"))):
    ket_qua = service.sua(db, data.kind, data.id, data.issue_code,
                          company_id=data.company_id, force=data.force)

    #  Ghi đè chốt D07 là chuyện phải để lại dấu vết: sổ sẽ có hai kiểu mã cạnh
    #  nhau, và ba tháng sau phải trả lời được "ai đổi, lúc nào".
    ghi_chu = f"Đổi mã số hiệu {data.kind}#{data.id}: {ket_qua['cu'] or '(trống)'} → {ket_qua['moi'] or '(trống)'}"
    if data.force and ket_qua["da_cap_so"]:
        ghi_chu += " — GHI ĐÈ dù đơn vị này đã cấp số"
    record(db, user.id, "doc_type", data.id, "update", ghi_chu)

    return success(ket_qua, "Đã lưu mã")
