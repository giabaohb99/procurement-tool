from pydantic import BaseModel


class CategoryAssigneeBase(BaseModel):
    item_group_id: int
    primary_employee_id: int = 0
    backup_employee_id: int = 0


class CategoryAssigneeCreate(CategoryAssigneeBase):
    pass


class CategoryAssigneeUpdate(BaseModel):
    item_group_id: int | None = None
    primary_employee_id: int | None = None
    backup_employee_id: int | None = None


class CategoryAssigneeBulk(BaseModel):
    item_group_ids: list[int] = []
    primary_employee_id: int = 0
    backup_employee_id: int = 0


class CategoryAssigneeOut(CategoryAssigneeBase):
    id: int
    item_group_name: str | None = None
    primary_name: str | None = None
    backup_name: str | None = None
    model_config = {"from_attributes": True}
