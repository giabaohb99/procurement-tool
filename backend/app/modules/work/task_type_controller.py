"""Danh mục loại việc — `/api/work/task-types` (duoc-CR-656, D1b).

Đọc: ai dùng Dự án cũng chọn được loại (`work_task.read`). Ghi: chỉ quản trị (`setting.write`, Q3).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import schema
from . import task_type_service as svc

router = APIRouter(prefix="/api/work/task-types", tags=["work"])


@router.get("")
def list_task_types(company_id: int | None = Query(None, ge=0), is_active: bool | None = None,
                    q: str = Query("", max_length=100), page: int = Query(1, ge=1, le=100000),
                    page_size: int = Query(200, ge=1, le=svc.MAX_PAGE_SIZE),
                    sort_by: str = Query("", max_length=30), sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
                    db: Session = Depends(get_db), user=Depends(require("work_task", "read"))):
    """`{total, items}`. Không truyền `is_active` = cả loại đã ngừng (màn quản trị); ô chọn của task truyền `is_active=true`."""
    return success(svc.list_types(db, company_id=company_id, is_active=is_active, q=q, page=page,
                                  page_size=page_size, sort_by=sort_by, sort_dir=sort_dir))


@router.post("")
def create_task_type(data: schema.TaskTypeCreate, db: Session = Depends(get_db),
                     user=Depends(require("setting", "write"))):
    return success(svc.create_type(db, user.id, data), "Đã tạo loại việc")


@router.patch("/{type_id}")
def update_task_type(type_id: int, data: schema.TaskTypeUpdate, db: Session = Depends(get_db),
                     user=Depends(require("setting", "write"))):
    return success(svc.update_type(db, user.id, type_id, data), "Đã lưu")


@router.delete("/{type_id}")
def delete_task_type(type_id: int, db: Session = Depends(get_db),
                     user=Depends(require("setting", "write"))):
    """Chưa ai dùng thì xóa hẳn; đã có task dùng thì chỉ ngừng dùng."""
    return success(svc.delete_type(db, user.id, type_id), "Đã xử lý")
