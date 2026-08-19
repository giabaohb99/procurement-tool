from pydantic import BaseModel, Field
from app.core.base_schema import BaseResponse

class SealTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field("", max_length=255)
    is_active: bool = True

class SealTypeResponse(SealTypeBase):
    id: int
    class Config:
        from_attributes = True

class SealRequestBase(BaseModel):
    title: str = Field(..., max_length=255)
    purpose: str
    seal_type_id: int
    department_id: int
    company_id: int
    first_approver_id: int
    note: str = ""

class SealRequestCreate(SealRequestBase):
    pass

class SealRequestUpdate(BaseModel):
    title: str | None = None
    purpose: str | None = None
    seal_type_id: int | None = None
    department_id: int | None = None
    company_id: int | None = None
    first_approver_id: int | None = None
    note: str | None = None

class SealRequestResponse(SealRequestBase):
    id: int
    code: str
    requester: str
    requester_id: int
    status: str
    created_at: str | None = None
    class Config:
        from_attributes = True
