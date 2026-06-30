from pydantic import BaseModel


class AdjustIn(BaseModel):
    company_id: int = 0
    warehouse_code: str = ""
    product_code: str = ""
    product_name: str = ""
    unit: str = ""
    qty: float = 0          # delta: dương = tăng, âm = giảm
    note: str = ""
