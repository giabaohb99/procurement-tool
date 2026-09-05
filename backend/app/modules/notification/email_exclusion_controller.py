"""API loại trừ email — dùng ở Cấu hình hệ thống (/system/settings).

Gác bằng entity `setting` (một mục của Cấu hình). Cho phép liệt kê / thêm / xóa
luật loại trừ email theo cá nhân · phòng ban · công ty.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import email_exclusion_service as svc

router = APIRouter(prefix="/api/email-exclusions", tags=["email-exclusion"])


class ExclusionIn(BaseModel):
    scope: str          # employee | department | company
    ref_id: int
    label: str = ""
    event: str = ""     # "" = mọi mẫu; hoặc mã event của một mẫu email


@router.get("")
def list_exclusions(db: Session = Depends(get_db),
                    user=Depends(require("setting", "read"))):
    return success(svc.list_all(db))


@router.post("")
def add_exclusion(data: ExclusionIn, db: Session = Depends(get_db),
                  user=Depends(require("setting", "write"))):
    row = svc.add(db, data.scope, data.ref_id, data.label, data.event, user)
    return success(row, "Đã thêm loại trừ email")


@router.delete("/{exclusion_id}")
def remove_exclusion(exclusion_id: int, db: Session = Depends(get_db),
                     user=Depends(require("setting", "write"))):
    svc.remove(db, exclusion_id)
    return success(None, "Đã bỏ loại trừ")
