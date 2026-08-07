from pydantic import BaseModel


class LineIn(BaseModel):
    payable_id: int
    amount: float = 0


class PRequestCreate(BaseModel):
    request_date: str = ""
    note: str = ""
    payment_method: str = "transfer"   # transfer = Chuyển khoản | cash = Tiền mặt (CR-035)
    lines: list[LineIn] = []   # có thể gồm nhiều NCC -> server tự tách mỗi NCC 1 phiếu


class PRequestUpdate(BaseModel):
    request_date: str | None = None
    note: str | None = None
    payment_method: str | None = None
    lines: list[LineIn] | None = None
