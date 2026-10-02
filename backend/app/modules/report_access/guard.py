"""Gác KÉP `/summary` + `/summary/export` theo khóa báo cáo cụ thể.

Gắn bằng `dependencies=[Depends(require_report(ReportKey.X))]` trên decorator
của route — KHÔNG đụng `user=Depends(require(entity, action))` đang gác quyền
+ `apply_scope` của phân hệ gốc. Hai cửa độc lập: gán sai/thừa ở đây không mở
rộng được dữ liệu, vì cửa quyền + phạm vi cũ vẫn chạy nguyên như trước.
"""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import REPORT_META, ReportKey

from .service import can_view_report


def require_report(key: ReportKey):
    """Trả một dependency KHÔNG dùng giá trị trả về (gắn ở `dependencies=[...]`,
    không ở tham số `user=`) — chỉ việc của nó là chặn 403 khi người gọi chưa
    được GÁN xem báo cáo `key`. `dep.report_key` gắn thêm để test soi
    `app.routes` biết đường nào đang gác khóa nào (`test_phan_quyen_bao_cao_gac_duong.py`)."""

    def dep(user=Depends(get_current_user), db: Session = Depends(get_db)) -> None:
        if not can_view_report(db, user, key):
            label = REPORT_META[key][0]
            raise HTTPException(403, f"Chưa được giao xem báo cáo: {label}")

    dep.report_key = key
    return dep
