"""bao-CR-800 — tách NGUYÊN LIỆU khỏi vật tư bao bì trong cụm Giá nguyên vật liệu sản xuất.

Nguyên liệu = sản phẩm thuộc nhóm `NL` trong danh mục (`tab_product.item_group`). Chủ dự án 27/11/2026: giá nguyên liệu phải cấp
quyền RIÊNG — có bộ phận được xem, có bộ phận không. Trước đó mã nguyên liệu vẫn lọt ra ở các màn VTBB khi chọn phạm vi *Mọi mã
có giá* hoặc chọn thẳng mã, nên ai xem được Bảng giá VTBB cũng xem được giá nguyên liệu.

Luật sau bản này:
  - các màn VTBB (Bảng giá VTBB, Giá mua gần nhất, Lịch sử mua hàng, Tác động, Tổng hợp, ô chọn mã) KHÔNG còn mã nhóm NL;
  - màn Bảng giá nguyên liệu CHỈ có mã nhóm NL và gác bằng khóa riêng `packaging_material_price`.

Một chỗ quyết định: `last_prices_controller.view_scope` / `shared_view_scope` ghép điều kiện ở đây vào điều kiện phạm vi pháp nhân
trên sổ giá, nên mọi truy vấn sổ giá của cụm (kể cả công cụ trợ lý AI) tự theo.
"""
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.modules.product.model import Product
from app.modules.product_price.model import ProductPriceLedger as L

MATERIAL_GROUP = "NL"
MATERIAL_ENTITY = "packaging_material_price"
KIND_PACKAGING = "packaging"
KIND_MATERIAL = "material"


def kind_of_entity(entity: str) -> str:
    return KIND_MATERIAL if entity == MATERIAL_ENTITY else KIND_PACKAGING


def material_codes(db: Session) -> set[str]:
    """Mã các sản phẩm nhóm nguyên liệu (vài trăm mã) — dùng để lọc danh sách mã dựng ngoài sổ giá (định mức, báo giá, mã đã chọn)."""
    return {code for (code,) in db.query(Product.code).filter(Product.item_group == MATERIAL_GROUP).all()}


def split_codes(codes, materials: set[str], kind: str) -> set[str]:
    """Giữ đúng phần mã thuộc `kind`: màn nguyên liệu lấy mã nhóm NL, màn VTBB lấy phần còn lại."""
    codes = set(codes or ())
    return codes & materials if kind == KIND_MATERIAL else codes - materials


def kind_condition(kind: str):
    """Điều kiện trên dòng sổ giá: thuộc nguyên liệu (màn nguyên liệu) hoặc KHÔNG thuộc (các màn VTBB)."""
    in_material = L.product_code.in_(select(Product.code).where(Product.item_group == MATERIAL_GROUP))
    return in_material if kind == KIND_MATERIAL else ~in_material


def with_kind(scope_cond, kind: str):
    """Ghép điều kiện loại mã vào phạm vi pháp nhân (`None` = thấy mọi pháp nhân)."""
    cond = kind_condition(kind)
    return cond if scope_cond is None else and_(scope_cond, cond)
