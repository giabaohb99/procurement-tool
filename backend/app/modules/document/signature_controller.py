"""API CHỮ KÝ (J02, J03). Cùng prefix `/api/documents` với `controller.py`."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import signature_service
from .controller import _load
from .signature_model import (SIGN_KIND_LABELS, SIGN_KIND_NOTES,
                              DocumentSignature)

router = APIRouter(prefix="/api/documents", tags=["document-signature"])


class SignIn(BaseModel):
    version_id: int
    signer_employee_id: int
    sign_kind: int = Field(default=1, ge=1, le=3)
    cert_serial: str = ""
    cert_issuer: str = ""


@router.get("/sign-kinds")
def sign_kinds(user=Depends(require("document", "read"))):
    """Ba loại chữ ký kèm CÂU GIÁ TRỊ PHÁP LÝ của từng loại.

    Câu đó do backend cấp, không để giao diện tự viết: đây đúng là chỗ mà một
    câu chữ nhẹ tay hơn sẽ dẫn tới việc gửi ra ngoài một văn bản tưởng có giá
    trị pháp lý mà thật ra không (J03).
    """
    return success([
        {"value": value, "label": label, "legal_note": SIGN_KIND_NOTES.get(value, "")}
        for value, label in SIGN_KIND_LABELS.items()
    ])


@router.get("/{document_id}/signatures")
def list_signatures(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    doc = _load(db, document_id, user)
    rows = signature_service.signatures_of(db, doc.id)
    return success([signature_service.serialize(db, row) for row in rows])


@router.post("/{document_id}/signatures")
def sign_document(
    document_id: int,
    data: SignIn,
    request: Request,
    db: Session = Depends(get_db),
    #  Ký là hành vi PHÊ DUYỆT chứ không phải sửa nội dung — gác bằng `approve`.
    user=Depends(require("document", "approve")),
):
    doc = _load(db, document_id, user)
    signature = signature_service.sign(
        db, doc,
        version_id=data.version_id,
        signer_employee_id=data.signer_employee_id,
        sign_kind=data.sign_kind,
        cert_serial=data.cert_serial,
        cert_issuer=data.cert_issuer,
        #  Địa chỉ và trình duyệt là một phần của "đủ giá trị nội bộ" (J02):
        #  không có chúng thì chữ ký chỉ là một dòng ai cũng ghi được.
        ip=(request.client.host if request.client else ""),
        user_agent=request.headers.get("user-agent", ""),
        actor=user.id,
    )
    record(db, user.id, "document", doc.id, "approve",
           f"Ký {SIGN_KIND_LABELS.get(signature.sign_kind, '')}")
    return success(signature_service.serialize(db, signature), "Đã ghi nhận chữ ký", 201)


#  KHÔNG có endpoint xóa chữ ký — cố ý. Bảng chỉ ghi thêm; một chữ ký gỡ được
#  thì nó không còn là chữ ký. Ký nhầm thì mở phiên bản mới.
__all__ = ["router", "DocumentSignature"]
