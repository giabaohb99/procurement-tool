"""ai-CR-191 — sổ tham chiếu của bốn danh mục nền Thu mua (kho / đơn vị tính / nhóm hàng / thương hiệu).

Khai một lần ở đây, `catalog/controller.py` import lúc khởi động; `core/crud.make_crud_router` tự gọi
`reference_guard.ensure_deletable(db, entity, obj)` ở nút xóa và dòng CSV «xóa» nên danh mục CRUD chung
không cần `before_delete`.

Ba danh mục này KHÔNG có khóa ngoại — chứng từ chép CHUỖI:
  · kho: dòng ĐMH / giao hàng / nhập kho / tồn kho ghi `warehouse_code` = MÃ kho; riêng dòng YCMH ghi
    `warehouse` = TÊN kho (màn v2 chọn theo `warehouse.name`, xem `purchase-request-items-table.tsx`);
  · đơn vị tính: mọi dòng ghi `unit` = TÊN đơn vị (màn chọn `unit.name`, không phải mã DVTxxx);
  · nhóm hàng: dòng ghi `item_group` = TÊN nhóm (`ItemGroup.name` là khóa duy nhất); phân công NSTM
    trỏ bằng `item_group_id`.
Thương hiệu (`tab_brand`): không bảng nào trỏ tới (rà 13/10/2026) — xóa tự do, không đăng ký.

Đếm KHÔNG lọc phạm vi và vẫn tính bản ghi đã xóa mềm (cố ý — xem `core/reference_guard.py`).
"""
from app.core.reference_guard import Reference, register
from app.modules.category_assignee.model import CategoryAssignee
from app.modules.goods_receipt.model import GoodsReceipt
from app.modules.inventory.model import Inventory, InventoryMove
from app.modules.product.model import Product
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import PODelivery, POItem
from app.modules.purchase_request.model import PurchaseRequestItem
from app.modules.survey.model import Survey
from app.modules.survey_request.model import SurveyRequestLine

register("warehouse", "Kho", [
    Reference(POItem, "warehouse_code", "dòng đơn mua hàng", key_attr="code"),
    Reference(PODelivery, "warehouse_code", "dòng giao hàng", key_attr="code"),
    Reference(GoodsReceipt, "warehouse_code", "phiếu nhập kho", key_attr="code"),
    Reference(Inventory, "warehouse_code", "dòng tồn kho", key_attr="code"),
    Reference(InventoryMove, "warehouse_code", "phát sinh nhập xuất kho", key_attr="code"),
    Reference(PurchaseRequestItem, "warehouse", "dòng yêu cầu mua hàng", key_attr="name"),
])

register("unit", "Đơn vị tính", [
    Reference(Product, "unit", "sản phẩm", key_attr="name"),
    Reference(PurchaseRequestItem, "unit", "dòng yêu cầu mua hàng", key_attr="name"),
    Reference(POItem, "unit", "dòng đơn mua hàng", key_attr="name"),
    Reference(GoodsReceipt, "unit", "phiếu nhập kho", key_attr="name"),
    Reference(Inventory, "unit", "dòng tồn kho", key_attr="name"),
    Reference(PurchaseHistory, "unit", "dòng lịch sử mua hàng", key_attr="name"),
])

register("item_group", "Nhóm hàng", [
    Reference(Product, "item_group", "sản phẩm", key_attr="name"),
    Reference(PurchaseRequestItem, "item_group", "dòng yêu cầu mua hàng", key_attr="name"),
    Reference(POItem, "item_group", "dòng đơn mua hàng", key_attr="name"),
    Reference(Survey, "item_group", "phiếu khảo sát", key_attr="name"),
    Reference(SurveyRequestLine, "item_group", "dòng yêu cầu báo giá", key_attr="name"),
    Reference(CategoryAssignee, "item_group_id", "phân công nhóm hàng"),
])
