from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import generate_code

from .model import Supplier
from .schema import SupplierCreate, SupplierUpdate

FILTERABLE = ["code", "name", "tax_code", "supplier_type", "is_active"]
ENTITY = "supplier"


def list_suppliers(db: Session, base_query, pg: dict):
    total = base_query.count()
    if not base_query._order_by_clauses:
        base_query = base_query.order_by(Supplier.id.desc())
    items = base_query.offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_supplier(db: Session, sid: int) -> Supplier:
    obj = db.get(Supplier, sid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy nhà cung cấp")
    return obj


def create_supplier(db: Session, data: SupplierCreate, user_id: int) -> Supplier:
    if not data.code:
        data.code = generate_code(db, Supplier, "NCC")
    elif db.query(Supplier).filter(Supplier.code == data.code).first():
        raise HTTPException(400, "Mã NCC đã tồn tại")
    obj = Supplier(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_supplier(db: Session, sid: int, data: SupplierUpdate, user_id: int) -> Supplier:
    obj = get_supplier(db, sid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def count_references(db: Session, code: str) -> list[tuple[str, int]]:
    """ai-CR-169: số chứng từ đang trỏ tới NCC theo chuỗi `supplier_code` (không có FK nào).

    ⚠️ KHÔNG lọc theo phạm vi dữ liệu, cố ý: đây là chốt TOÀN VẸN, người chỉ thấy phòng mình
    vẫn không được xóa NCC mà phòng khác đang có đơn.
    """
    from app.modules.contract.model import Contract
    from app.modules.payable.model import Payable
    from app.modules.payment_request.model import PaymentRequest
    from app.modules.purchase_history.model import PurchaseHistory
    from app.modules.purchase_order.model import POCost, PurchaseOrder
    from app.modules.purchase_request.model import PurchaseRequestItemOption
    from app.modules.survey.model import SurveyProductLine, SurveySupplierLine
    from app.modules.survey_request.model import SurveyRequestOption

    if not code:
        return []
    checks = [
        ("đơn mua hàng", db.query(PurchaseOrder).filter(PurchaseOrder.supplier_code == code)),
        ("dòng chi phí đơn mua hàng", db.query(POCost).filter(POCost.supplier_code == code)),
        ("khoản công nợ", db.query(Payable).filter(Payable.supplier_code == code)),
        ("yêu cầu thanh toán", db.query(PaymentRequest).filter(PaymentRequest.supplier_code == code)),
        ("lịch sử mua hàng", db.query(PurchaseHistory).filter(PurchaseHistory.supplier_code == code)),
        ("phương án yêu cầu mua hàng",
         db.query(PurchaseRequestItemOption).filter(PurchaseRequestItemOption.supplier_code == code)),
        ("phương án yêu cầu báo giá",
         db.query(SurveyRequestOption).filter(SurveyRequestOption.supplier_code == code)),
        ("dòng khảo sát", db.query(SurveySupplierLine).filter(SurveySupplierLine.supplier_code == code)),
        ("dòng khảo sát sản phẩm", db.query(SurveyProductLine).filter(SurveyProductLine.supplier_code == code)),
        ("hợp đồng", db.query(Contract).filter(Contract.party_type == "supplier", Contract.party_code == code)),
    ]
    return [(label, n) for label, q in checks if (n := q.count())]


def ensure_deletable(db: Session, obj: Supplier) -> None:
    """Còn chứng từ tham chiếu thì KHÔNG xóa — chỉ có thể bỏ tick «Đang dùng» (`is_active`)."""
    refs = count_references(db, obj.code)
    if refs:
        total = sum(n for _, n in refs)
        detail = ", ".join(f"{n} {label}" for label, n in refs)
        raise HTTPException(
            400, f"Nhà cung cấp «{obj.code}» đang được dùng ở {total} chứng từ ({detail}), "
                 "chỉ có thể ngưng dùng (bỏ tick «Đang dùng») chứ không xóa được.")


def delete_supplier(db: Session, sid: int, user_id: int) -> None:
    obj = get_supplier(db, sid)
    ensure_deletable(db, obj)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, sid, "delete")
