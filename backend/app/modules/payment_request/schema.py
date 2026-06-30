from pydantic import BaseModel


class LineIn(BaseModel):
    payable_id: int
    amount: float = 0


class PRequestCreate(BaseModel):
    request_date: str = ""
    note: str = ""
    lines: list[LineIn] = []   # có thể gồm nhiều NCC -> server tự tách mỗi NCC 1 phiếu


class PRequestUpdate(BaseModel):
    request_date: str | None = None
    note: str | None = None
    lines: list[LineIn] | None = None
