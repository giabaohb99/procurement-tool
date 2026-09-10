from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import CLERK_STATUS_LABELS, SealClerk
from .schema import SealClerkBulk, SealClerkCreate, SealClerkOut, SealClerkSync, SealClerkUpdate

#  Quản lý phân công văn thư là CẤU HÌNH Duyệt dấu — dùng chung khóa quyền
#  `seal_type` (Quản trị con dấu quản, mọi người chỉ đọc), không đẻ entity mới.
_ENT = "seal_type"

router = APIRouter(prefix="/api/seal-clerks", tags=["seal_clerk"])


def _out(db: Session, obj: SealClerk) -> dict:
    from app.modules.company.model import Company
    from app.modules.employee.model import Employee

    d = SealClerkOut.model_validate(obj).model_dump()
    emp = db.get(Employee, obj.employee_id) if obj.employee_id else None
    com = db.get(Company, obj.company_id) if obj.company_id else None
    d["employee_name"] = emp.full_name if emp else None
    d["employee_code"] = emp.code if emp else None
    d["company_name"] = com.name if com else None
    d["status_label"] = CLERK_STATUS_LABELS.get(obj.status, str(obj.status))
    return d


@router.get("")
def list_(
    search: str = Query(""),
    company_id: int = Query(0, description="Lọc: chỉ văn thư phụ trách công ty này"),
    sort_by: str = Query("employee_name"),
    sort_dir: str = Query("asc"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require(_ENT, "read")),
):
    """Danh sách phân công văn thư — GỘP THEO VĂN THƯ (mỗi người một dòng).

    `search` tìm theo GIÁ TRỊ HIỂN THỊ (tên/mã văn thư, tên công ty); `company_id`
    lọc theo công ty phụ trách. Bảng nối vẫn một dòng/công ty ở DB; đây chỉ gộp lại.
    """
    total, items = service.list_grouped(
        db, search, pg["offset"], pg["limit"], sort_by, sort_dir, company_id)
    return success({"total": total, "items": items})


@router.get("/by-employee/{eid}")
def by_employee(eid: int, db: Session = Depends(get_db), user=Depends(require(_ENT, "read"))):
    """Gộp phân công của một văn thư (danh sách công ty + cờ tổng) — cho màn chi tiết."""
    return success(service.list_for_employee(db, eid))


@router.post("/sync")
def sync_(data: SealClerkSync, db: Session = Depends(get_db),
          user=Depends(require(_ENT, "create"))):
    """Đặt lại toàn bộ công ty một văn thư phụ trách = đúng danh sách gửi lên."""
    n = service.sync(db, data.employee_id, data.company_ids, data.is_head, user.id,
                     data.anchor_id, data.status)
    return success({"count": n}, "Đã cập nhật phân công")


@router.get("/{cid}")
def get_(cid: int, db: Session = Depends(get_db), user=Depends(require(_ENT, "read"))):
    return success(_out(db, service.get(db, cid)))


@router.post("")
def create_(data: SealClerkCreate, db: Session = Depends(get_db),
            user=Depends(require(_ENT, "create"))):
    return success(_out(db, service.create(db, data, user.id)), "Đã phân công văn thư", 201)


@router.post("/bulk")
def bulk_(data: SealClerkBulk, db: Session = Depends(get_db),
          user=Depends(require(_ENT, "create"))):
    n = service.bulk_upsert(db, data.employee_id, data.company_ids, data.is_head, user.id)
    return success({"count": n}, f"Đã phân công {n} mục")


@router.patch("/{cid}")
def update_(cid: int, data: SealClerkUpdate, db: Session = Depends(get_db),
            user=Depends(require(_ENT, "write"))):
    return success(_out(db, service.update(db, cid, data, user.id)), "Đã cập nhật")


@router.delete("/{cid}")
def delete_(cid: int, db: Session = Depends(get_db),
            user=Depends(require(_ENT, "delete"))):
    service.delete(db, cid, user.id)
    return success(None, "Đã xóa")
