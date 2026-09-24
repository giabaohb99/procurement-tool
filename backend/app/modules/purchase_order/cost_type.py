"""API DANH MỤC LOẠI CHI PHÍ THU MUA — `/api/po-cost-types` (bao-CR-453).

Thay bộ mã cứng `ImportCostType` bằng bảng `tab_po_cost_type` để thu mua tự thêm
loại chi phí (phí kiểm định mới, phí lưu kho ngoại quan...) mà không phải chờ sửa
mã. Danh mục thuần nên dựng bằng `make_crud_router` (khóa quyền riêng
`purchase_cost_type`), thêm ba chốt mà bộ sinh không tự có:

* `before_create` — bỏ trống mã thì tự cấp SỐ kế tiếp từ 15 trở đi, không bao giờ
  cấp 99 (mã 1..14 và 99 là bộ cũ, đã nằm trong dữ liệu);
* `before_update` — mã 99 «Chi phí khác» là chỗ rơi mặc định của mã lạ nên không
  đổi tên, không ngừng dùng được;
* `before_delete` — chặn xóa mã 99 và mọi loại đang có dòng chi phí trỏ tới.

⚠️ Nằm TRONG module `purchase_order` chứ không thành module riêng: danh mục cần
`POCost` để đếm dòng đang dùng, còn `service._save_import_costs` cần `POCostType`
để kiểm mã — tách đôi là hai module import lẫn nhau (cùng lý do với
`employee/position_controller.py`).
"""
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.crud import make_crud_router
from app.modules.employee.field_limits import Str50, Str100, Str500

from .model import (AllocationMethod, CostTypeGroup, ImportCostType, POCost, POCostType)

#  Mã mới cấp từ đây trở đi; 1..14 là bộ cũ, 99 là «Chi phí khác».
FIRST_CUSTOM_CODE = 15
OTHER_CODE = int(ImportCostType.OTHER)
#  Cột `code` là SMALLINT — mã do người gõ cũng phải nằm trong dải này.
MAX_CODE = 32000


def _require_text(value: str, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} không được để trống")
    return text


class POCostTypeCreate(BaseModel):
    #  ⚠️ `code` để trống được: `before_create` tự cấp số kế tiếp. Gõ tay thì
    #  phải ≥ 1 và không được 99 (xem `_assign_code`).
    code: int | None = Field(None, ge=1, le=MAX_CODE)
    name: Str100
    group_kind: int = Field(int(CostTypeGroup.SERVICE), ge=1, le=2)
    creates_payable: bool = True
    default_supplier_code: Str50 = ""
    default_allocation_method: int = Field(int(AllocationMethod.BY_VALUE), ge=1, le=5)
    default_vat: float = Field(0, ge=0, lt=100)
    sort_order: int = 0
    is_active: bool = True
    note: Str500 = ""

    @field_validator("name")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        return _require_text(v, "Tên loại chi phí")


class POCostTypeUpdate(BaseModel):
    #  ⚠️ `code` KHÔNG sửa được — mã đã nằm trong cột `tab_po_cost.cost_type`.
    name: Str100 | None = None
    group_kind: int | None = Field(None, ge=1, le=2)
    creates_payable: bool | None = None
    default_supplier_code: Str50 | None = None
    default_allocation_method: int | None = Field(None, ge=1, le=5)
    default_vat: float | None = Field(None, ge=0, lt=100)
    sort_order: int | None = None
    is_active: bool | None = None
    note: Str500 | None = None

    @field_validator("name")
    @classmethod
    def _not_blank(cls, v: str | None) -> str | None:
        return None if v is None else _require_text(v, "Tên loại chi phí")


class POCostTypeResponse(BaseModel):
    id: int
    code: int = 0
    name: str = ""
    group_kind: int = int(CostTypeGroup.SERVICE)
    creates_payable: bool = True
    default_supplier_code: str = ""
    default_allocation_method: int = int(AllocationMethod.BY_VALUE)
    default_vat: float = 0
    sort_order: int = 0
    is_active: bool = True
    note: str = ""

    model_config = {"from_attributes": True}


def next_cost_type_code(db: Session) -> int:
    """Mã kế tiếp = max(mã hiện có, 14) + 1, nhảy qua 99.

    Mã 99 «Chi phí khác» luôn có trong danh mục nên phải BỎ nó ra khỏi phép max — không thì
    ngay mã tự cấp đầu tiên đã là 100, bỏ trống cả dải 15..98."""
    current = db.query(func.max(POCostType.code)).filter(POCostType.code != OTHER_CODE).scalar() or 0
    code = max(int(current), FIRST_CUSTOM_CODE - 1) + 1
    if code == OTHER_CODE:
        code += 1
    return code


def _assign_code(db: Session, data: POCostTypeCreate) -> None:
    """Chốt `before_create`: tự cấp mã khi bỏ trống; mã gõ tay không được là 99."""
    if not data.code:
        data.code = next_cost_type_code(db)
    elif int(data.code) == OTHER_CODE:
        raise HTTPException(400, "Mã 99 dành riêng cho «Chi phí khác», chọn mã khác")


def _protect_other(db: Session, obj: POCostType, values: dict) -> None:
    """Chốt `before_update`: mã 99 là chỗ rơi mặc định của mã lạ, phải luôn còn và luôn dùng được."""
    if int(obj.code) != OTHER_CODE:
        return
    if values.get("is_active") is False:
        raise HTTPException(400, "«Chi phí khác» (mã 99) không ngừng dùng được — mã lạ đều dồn về đây")
    if "name" in values and (values["name"] or "").strip() != (obj.name or "").strip():
        raise HTTPException(400, "«Chi phí khác» (mã 99) không đổi tên được")


def count_costs_using(db: Session, code: int) -> int:
    return db.query(func.count(POCost.id)).filter(POCost.cost_type == int(code)).scalar() or 0


def _block_delete_in_use(db: Session, obj: POCostType) -> None:
    """Chốt `before_delete`: còn dòng chi phí trỏ tới thì không xóa (bỏ tick «Đang dùng» thay vì xóa)."""
    if int(obj.code) == OTHER_CODE:
        raise HTTPException(400, "«Chi phí khác» (mã 99) không xóa được")
    used = count_costs_using(db, obj.code)
    if used:
        raise HTTPException(
            400, f"«{obj.name}» đang có {used} dòng chi phí trên các đơn mua hàng nên không xóa được. "
                 "Bỏ tick «Đang dùng» để ẩn khỏi ô chọn thay vì xóa.")


router = make_crud_router(
    "/api/po-cost-types", "purchase_cost_type", POCostType,
    POCostTypeCreate, POCostTypeUpdate, POCostTypeResponse,
    filterable=["code", "name", "group_kind", "is_active", "creates_payable", "note"],
    unique_field="code",
    csv_headers={"code": "Mã", "name": "Tên loại chi phí", "group_kind": "Nhóm (1 thuế / 2 dịch vụ)",
                 "creates_payable": "Sinh công nợ", "default_supplier_code": "NCC mặc định",
                 "default_allocation_method": "Cách chia mặc định", "default_vat": "VAT mặc định (%)",
                 "sort_order": "Thứ tự", "is_active": "Đang dùng", "note": "Ghi chú"},
    #  Đường nhập CSV đi vòng qua ba chốt trên (không gọi before_*) — chỉ xuất.
    csv_import=False,
    before_create=_assign_code,
    before_update=_protect_other,
    before_delete=_block_delete_in_use,
)
