from pydantic import BaseModel


class DepartmentBase(BaseModel):
    code: str = ""
    name: str
    company_id: int = 0
    parent: int = 0
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    company_id: int | None = None
    parent: int | None = None
    is_active: bool | None = None


class DepartmentOut(DepartmentBase):
    id: int
    manager_name: str | None = None
    manager_id: int | None = None
    model_config = {"from_attributes": True}
