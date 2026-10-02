"""`/api/report-access` — màn cấu hình tab «Báo cáo» của Phân quyền tài khoản.

Gác bằng `role.read`/`role.write` (B-07: không thêm entity mới — đây là cấu
hình QUYỀN, không phải dữ liệu nghiệp vụ của một phân hệ cụ thể). Controller
này được MIỄN TRỪ ở `test_pham_vi_luat_bat_bien.py` (BB-4) với đúng lý do đó.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.response import success

from . import grant_service
from .schema import ReportAccessGrantIn, ReportAccessRevokeIn

router = APIRouter(prefix="/api/report-access", tags=["report_access"])


def _parse_key(key: int) -> ReportKey:
    try:
        return ReportKey(key)
    except ValueError:
        raise HTTPException(404, f"Không có báo cáo nào mang khóa {key}")


@router.get("")
def list_report_access(db: Session = Depends(get_db), user=Depends(require("role", "read"))):
    """13 báo cáo theo đúng thứ tự khóa, mỗi báo cáo kèm danh sách dòng CÒN SỐNG."""
    return success(grant_service.list_grants(db))


@router.post("/{key}/grants")
def grant_report_access(key: int, data: ReportAccessGrantIn, db: Session = Depends(get_db),
                        user=Depends(require("role", "write"))):
    report_key = _parse_key(key)
    #  `actor=user` (ORM đầy đủ, không phải `user.id`) — `grant_service.grant` cần
    #  `.id`/`.employee_id` cho hai chốt chống tự nâng quyền (M3, `privilege_escalation.py`).
    result = grant_service.grant(db, report_key, data, actor=user)
    return success(result, "Đã lưu phân quyền báo cáo")


@router.delete("/grants/{access_id}")
def revoke_report_access(access_id: int, data: ReportAccessRevokeIn,
                         db: Session = Depends(get_db), user=Depends(require("role", "write"))):
    grant_service.revoke(db, access_id, data.reason, actor=user)
    return success(None, "Đã thu hồi phân quyền báo cáo")
