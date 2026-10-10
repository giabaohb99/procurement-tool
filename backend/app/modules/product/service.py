from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Product
from .schema import ProductCreate, ProductUpdate

FILTERABLE = ["code", "name", "item_group", "unit", "hh_code", "hh_name", "is_active"]
ENTITY = "product"


def list_products(db: Session, base_query, pg: dict):
    total = base_query.count()
    if not base_query._order_by_clauses:
        base_query = base_query.order_by(Product.id.desc())
    items = base_query.offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_product(db: Session, pid: int) -> Product:
    obj = db.get(Product, pid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy sản phẩm")
    return obj


def create_product(db: Session, data: ProductCreate, user_id: int) -> Product:
    if db.query(Product).filter(Product.code == data.code).first():
        raise HTTPException(400, "Mã sản phẩm đã tồn tại")
    obj = Product(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_product(db: Session, pid: int, data: ProductUpdate, user_id: int) -> Product:
    obj = get_product(db, pid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def count_references(db: Session, code: str) -> list[tuple[str, int]]:
    """ai-CR-169: số chứng từ đang trỏ tới sản phẩm theo chuỗi `product_code`.

    `tab_product` là bảng SKU, không có FK nào trỏ vào — 7 bảng nối bằng chuỗi mã (xem
    `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`). ⚠️ KHÔNG lọc theo phạm vi dữ liệu,
    cố ý: chốt toàn vẹn phải đếm hết.
    """
    from app.modules.goods_receipt.model import GoodsReceipt
    from app.modules.inventory.model import Inventory, InventoryMove
    from app.modules.purchase_history.model import PurchaseHistory
    from app.modules.purchase_order.model import POItem
    from app.modules.purchase_request.model import PurchaseRequestItem
    from app.modules.survey_request.model import SurveyRequestOption

    if not code:
        return []
    checks = [
        ("dòng yêu cầu mua hàng", db.query(PurchaseRequestItem).filter(PurchaseRequestItem.product_code == code)),
        ("dòng đơn mua hàng", db.query(POItem).filter(POItem.product_code == code)),
        ("phiếu nhập kho", db.query(GoodsReceipt).filter(GoodsReceipt.product_code == code)),
        ("dòng tồn kho", db.query(Inventory).filter(Inventory.product_code == code)),
        ("phát sinh kho", db.query(InventoryMove).filter(InventoryMove.product_code == code)),
        ("lịch sử mua hàng", db.query(PurchaseHistory).filter(PurchaseHistory.product_code == code)),
        ("phương án yêu cầu báo giá",
         db.query(SurveyRequestOption).filter(SurveyRequestOption.system_product_code == code)),
    ]
    return [(label, n) for label, q in checks if (n := q.count())]


def ensure_deletable(db: Session, obj: Product) -> None:
    """Còn chứng từ tham chiếu thì KHÔNG xóa — chỉ có thể bỏ tick «Đang dùng» (`is_active`)."""
    refs = count_references(db, obj.code)
    if refs:
        total = sum(n for _, n in refs)
        detail = ", ".join(f"{n} {label}" for label, n in refs)
        raise HTTPException(
            400, f"Sản phẩm «{obj.code}» đang được dùng ở {total} chứng từ ({detail}), "
                 "chỉ có thể ngưng dùng (bỏ tick «Đang dùng») chứ không xóa được.")


def delete_product(db: Session, pid: int, user_id: int) -> None:
    obj = get_product(db, pid)
    ensure_deletable(db, obj)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")
