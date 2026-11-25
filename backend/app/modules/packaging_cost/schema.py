"""Schema ghi / đọc của định mức bao bì (duoc-CR-784). Mọi `String(n)` có `max_length` đúng n (backend-input-limits)."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.employee.field_limits import Str50, Str255

CARTON_QTY_MAX = 100000   # quy cách thùng: chai / thùng, 0 = chưa có


def _strip_required(v: Optional[str]) -> Optional[str]:
    if v is not None:
        v = v.strip()
        if not v:
            raise ValueError("Không được để trống")
    return v


class BomCreate(BaseModel):
    fg_code: Str50
    fg_name: Str255 = ""
    legal_name: Str255 = ""
    bottle_code: Str50
    cap_code: Str50 = ""
    label_code: Str50 = ""
    carton_label_code: Str50 = ""
    carton_code: Str50 = ""
    carton_qty: int = Field(0, ge=0, le=CARTON_QTY_MAX)

    _required = field_validator("fg_code", "bottle_code")(_strip_required)


class BomUpdate(BaseModel):
    fg_code: Optional[Str50] = None
    fg_name: Optional[Str255] = None
    legal_name: Optional[Str255] = None
    bottle_code: Optional[Str50] = None
    cap_code: Optional[Str50] = None
    label_code: Optional[Str50] = None
    carton_label_code: Optional[Str50] = None
    carton_code: Optional[Str50] = None
    carton_qty: Optional[int] = Field(None, ge=0, le=CARTON_QTY_MAX)

    _required = field_validator("fg_code", "bottle_code")(_strip_required)


class BomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fg_code: str
    fg_name: str
    legal_name: str
    bottle_code: str
    cap_code: str
    label_code: str
    carton_label_code: str
    carton_code: str
    carton_qty: int
