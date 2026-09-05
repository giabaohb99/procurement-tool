from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, has_global_scope

from . import service
from .model import Inventory, InventoryMove
from .schema import AdjustIn

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _out(r: Inventory) -> dict:
    return {"id": r.id, "company_id": r.company_id, "warehouse_code": r.warehouse_code,
            "product_code": r.product_code, "product_name": r.product_name,
            "unit": r.unit, "qty": float(r.qty or 0),
            "avg_cost": float(r.avg_cost or 0), "value": float(r.value or 0)}


@router.get("")
def list_inventory(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                   user=Depends(require("inventory", "read"))):
    q = apply_filters(db.query(Inventory), Inventory, request, service.FILTERABLE)
    q = apply_scope(q, Inventory, "inventory", user, get_perm_profile(db, user))
    company_id = request.query_params.get("company_id")
    if company_id:
        q = q.filter(Inventory.company_id == int(company_id))
    
    item_group = request.query_params.get("item_group")
    if item_group:
        from app.modules.product.model import Product
        q = q.join(Product, Product.code == Inventory.product_code).filter(Product.item_group == item_group)
        
    qty_status = request.query_params.get("qty_status")
    if qty_status:
        if qty_status == "in_stock":
            q = q.filter(Inventory.qty > 0)
        elif qty_status == "out_of_stock":
            q = q.filter(Inventory.qty == 0)
        elif qty_status == "negative_stock":
            q = q.filter(Inventory.qty < 0)

    total = q.count()
    items = q.order_by(Inventory.product_code.asc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_out(i) for i in items]})


@router.get("/moves")
def list_moves(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
               user=Depends(require("inventory", "read"))):
    from app.modules.user.model import User
    from app.modules.employee.model import Employee

    q = db.query(InventoryMove, Employee.full_name).\
        outerjoin(User, User.id == InventoryMove.created_by).\
        outerjoin(Employee, Employee.id == User.employee_id)
    # Cùng khóa `inventory.read` với màn Tồn kho ngay trên, nên phải cùng phạm vi:
    # nhật ký nhập/xuất mang mã hàng, ĐƠN GIÁ NHẬP và tên người thao tác, tức là
    # chi tiết hơn cả bảng tồn kho mà nó đứng cạnh. `tab_inventory_move` có
    # `company_id` nên chiều `company` của entity `inventory` áp thẳng được.
    q = apply_scope(q, InventoryMove, "inventory", user, get_perm_profile(db, user))

    for k in ("warehouse_code", "product_code", "company_id"):
        v = request.query_params.get(k)
        if v:
            if k == "company_id":
                q = q.filter(InventoryMove.company_id == int(v))
            else:
                q = q.filter(getattr(InventoryMove, k) == v)

    total = q.count()
    rows = q.order_by(InventoryMove.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    items = []
    for m, emp_name in rows:
        items.append({
            "id": m.id,
            "company_id": m.company_id,
            "warehouse_code": m.warehouse_code,
            "product_code": m.product_code,
            "qty": float(m.qty or 0),
            "unit_price": float(m.unit_price or 0),
            "ref_type": m.ref_type,
            "ref_id": m.ref_id,
            "note": m.note,
            "at": m.created_at,
            "operator_name": emp_name or "Hệ thống"
        })
    return success({"total": total, "items": items})


def _writable_company(db: Session, data: AdjustIn, user) -> int:
    """Pháp nhân được phép GHI tồn kho — lấy từ hồ sơ quyền, không tin body.

    `company_id` trong body là đường ghi đè tồn kho của pháp nhân người gửi không được
    xem: `service.adjust` upsert theo `(company, kho, sp)` nên gõ id lạ vào là sửa thẳng
    số tồn bên đó, lại có `record(...)` nên nhật ký nhìn vẫn hợp lệ.

    Không dùng `get_scoped` được vì điều chỉnh có thể TẠO MỚI dòng tồn (mặt hàng chưa có
    trong kho đó) — chưa có bản ghi nào để soi. Nên chốt đặt trên GIÁ TRỊ pháp nhân:

    * bỏ trống ⇒ lấy pháp nhân của chính người thao tác;
    * khác pháp nhân của mình ⇒ chỉ người có phạm vi **tất cả** trên `inventory.write`
      mới được (quản trị đa pháp nhân vẫn làm việc bình thường);
    * người chưa gắn pháp nhân (`company_id = 0`) thì chặn — cùng luật với
      `_role_scope_cond` ở bậc `company`, chứ không ghi vào "pháp nhân số 0".
    """
    prof = get_perm_profile(db, user)
    mine = prof.get("company_id") or 0
    company_id = int(data.company_id or 0) or mine
    if not company_id:
        raise HTTPException(400, "Tài khoản chưa gắn pháp nhân — không điều chỉnh tồn kho được")
    if company_id != mine and not has_global_scope(prof, "inventory", "write"):
        raise HTTPException(403, "Ngoài phạm vi được phép điều chỉnh tồn kho")
    return company_id


@router.post("/adjust")
def adjust(data: AdjustIn, db: Session = Depends(get_db), user=Depends(require("inventory", "write"))):
    row = service.adjust(db, company_id=_writable_company(db, data, user),
                         warehouse_code=data.warehouse_code,
                         product_code=data.product_code, product_name=data.product_name,
                         unit=data.unit, qty=data.qty, note=data.note, user_id=user.id,
                         unit_price=data.unit_price)
    record(db, user.id, "inventory", row.id, "adjust", data.note)
    return success(_out(row), "Đã điều chỉnh tồn kho")
