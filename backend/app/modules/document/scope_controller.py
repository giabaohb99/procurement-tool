"""API PHẠM VI ÁP DỤNG (F01–F05).

Cùng prefix `/api/documents` với `controller.py` — vẫn là việc của văn bản.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, require
from app.core.database import get_db
from app.core.response import success
from app.modules.company.model import Company
from app.modules.employee.model import Employee

from . import scope_service, serializer
from .controller import _load
from .model import Document
from .scope_model import (DIM_COMPANY, DIM_DEPARTMENT, DIM_EMPLOYEE,
                          DIM_LABELS, MODE_INCLUDE, MODE_LABELS, DocumentScope)

router = APIRouter(prefix="/api/documents", tags=["document-scope"])


class ScopeCreate(BaseModel):
    dim: int = Field(ge=1, le=3)
    mode: int = Field(default=MODE_INCLUDE, ge=1, le=2)
    company_id: int | None = None
    department_id: int | None = None
    employee_id: int | None = None
    include_children: bool = False

    @model_validator(mode="after")
    def _kiem_chieu(self):
        #  F03 — chặn ở đây để có câu báo nói rõ VÌ SAO, và chặn lần nữa bằng
        #  CHECK ở tầng dữ liệu để không đường vòng nào lọt.
        if self.dim == DIM_DEPARTMENT:
            if not self.department_id:
                raise ValueError("Chọn phòng ban thì phải chỉ ra phòng ban nào")
            if not self.company_id:
                raise ValueError(
                    "Chọn phòng ban thì bắt buộc kèm pháp nhân. Một phòng ban có "
                    "mặt ở 13 pháp nhân — khai trơ trọi là văn bản lan sang cả 13 công ty."
                )
        if self.dim == DIM_COMPANY and not self.company_id:
            raise ValueError("Chọn pháp nhân thì phải chỉ ra pháp nhân nào")
        if self.dim == DIM_EMPLOYEE and not self.employee_id:
            raise ValueError("Chọn cá nhân thì phải chỉ ra người nào")
        #  "Gồm đơn vị con" chỉ có nghĩa với pháp nhân.
        if self.include_children and self.dim != DIM_COMPANY:
            raise ValueError("Chỉ pháp nhân mới có tùy chọn gồm đơn vị con")
        return self


@router.get("/scope-options")
def scope_options(user=Depends(require("document", "read"))):
    """Nhãn tiếng Việt do backend cấp — giao diện không chép cứng."""
    return success({
        "dims": [{"value": v, "label": l} for v, l in DIM_LABELS.items()],
        "modes": [{"value": v, "label": l} for v, l in MODE_LABELS.items()],
    })


@router.get("/applies-to-me")
def applies_to_me(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """F05 — danh sách văn bản đang áp dụng cho chính người đang đăng nhập."""
    employee = db.get(Employee, user.employee_id) if user.employee_id else None
    if employee is None:
        #  Tài khoản chưa gắn hồ sơ nhân sự thì không tính được phạm vi. Trả rỗng
        #  chứ không báo lỗi — đây là màn ai cũng mở được.
        return success({"total": 0, "items": []})

    ids = scope_service.document_ids_for(db, employee)
    if not ids:
        return success({"total": 0, "items": []})

    docs = db.query(Document).filter(Document.id.in_(ids)).all()
    return success({"total": len(docs), "items": serializer.serialize_many(db, docs)})


@router.get("/{document_id}/scopes")
def list_scopes(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    doc = _load(db, document_id, user)
    rows = scope_service.scopes_of(db, doc.id)
    company = db.get(Company, doc.company_id) if doc.company_id else None
    return success({
        "items": [scope_service.serialize(db, row) for row in rows],
        #  Nói thẳng quy tắc 3 ra cho giao diện khỏi tự đoán: chưa khai dòng nào
        #  thì văn bản áp trong ĐÚNG pháp nhân ban hành, không phải "không tới
        #  ai" (luật cũ) mà cũng không phải "cả tập đoàn".
        "default_to_issuer": len(rows) == 0,
        "issuer_company_name": company.name if company else "",
    })


@router.post("/{document_id}/scopes")
def add_scope(
    document_id: int,
    data: ScopeCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    row = DocumentScope(
        document_id=doc.id, **data.model_dump(),
        created_by=user.id, updated_by=user.id,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Dòng phạm vi này đã khai rồi")
    db.refresh(row)
    record(db, user.id, "document", doc.id, "update")
    return success(scope_service.serialize(db, row), "Đã thêm phạm vi áp dụng", 201)


@router.delete("/{document_id}/scopes/{scope_id}")
def delete_scope(
    document_id: int,
    scope_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    doc = _load(db, document_id, user, "write")
    row = db.get(DocumentScope, scope_id)
    if not row or row.document_id != doc.id:
        raise HTTPException(404, "Không tìm thấy dòng phạm vi")
    db.delete(row)
    db.commit()
    record(db, user.id, "document", doc.id, "update")
    return success(None, "Đã gỡ dòng phạm vi")
