from pydantic import BaseModel
from app.modules.employee.field_limits import Str25, Str50, Str255


class AdjustIn(BaseModel):
    company_id: int = 0
    warehouse_code: Str50 = ""
    product_code: Str50 = ""
    product_name: Str255 = ""
    unit: Str25 = ""
    qty: float = 0          # delta: dương = tăng, âm = giảm
    unit_price: float = 0   # đơn giá điều chỉnh (nếu muốn ghi nhận giá)
    note: str = ""
