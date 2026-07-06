from pydantic import BaseModel


class SurveyRequestLineIn(BaseModel):
    received_date: str = ""
    result_due_date: str = ""
    department_requester: str = ""
    item_group: str = ""
    requirement_detail: str = ""
    other_requirement: str = ""
    request_qty: float = 0
    uom: str = ""
    proposed_price: float = 0
    image_file: str = ""


class _Header(BaseModel):
    company_id: int = 0
    requester: str = ""
    requester_position: str = ""
    department: str = ""
    head_of_dept: str = ""
    purpose: str = ""
    request_date: str = ""
    note: str = ""


class SurveyRequestCreate(_Header):
    code: str | None = None
    lines: list[SurveyRequestLineIn] = []


class SurveyRequestUpdate(BaseModel):
    company_id: int | None = None
    requester: str | None = None
    requester_position: str | None = None
    department: str | None = None
    head_of_dept: str | None = None
    purpose: str | None = None
    request_date: str | None = None
    note: str | None = None
    lines: list[SurveyRequestLineIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""
