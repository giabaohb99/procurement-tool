"""Tính TẬP KHÓA báo cáo mà một người dùng được xem — một truy vấn cố định.

Dùng ở hai nơi: `guard.require_report` (gác `/summary` + `/summary/export`) và
`/api/auth/me` (trường `report_keys`, FE dùng để gác menu/route/Tổng quan —
xem `auth/controller.py::_me_payload`). MỘT nguồn, không tính theo hai luật
khác nhau ở hai nơi.

Số truy vấn CỐ ĐỊNH = 1 (đúng luật «API báo cáo nhanh nhất» —
`doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md` không áp ở đây, nhưng cùng
tinh thần với mọi API báo cáo khác trong repo: không N+1 theo số dòng).
"""
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.report_keys import ReportKey
from app.core.subject_match import (EFFECT_ALLOW, EFFECT_DENY, subject_match_condition,
                                    still_live_condition)

from .model import ReportAccess


def viewable_keys(db: Session, user, profile: dict | None = None) -> set[int]:
    """`{report_key}` người này được xem — CẤM thắng CHO PHÉP (đúng luật
    `tab_document_access`/`tab_doc_folder_access`). Người chưa gắn hồ sơ nhân
    sự và không mang vai trò nào -> `set()`, không nổ (`subject_match_condition`
    trả `None` khi hết chủ thể để khớp).

    ĐÚNG MỘT truy vấn: điều kiện chủ thể + còn hiệu lực gộp sẵn ở WHERE,
    không lọc lại bằng Python sau khi đã tải hết bảng.
    """
    prof = profile if profile is not None else get_perm_profile(db, user)
    cond = subject_match_condition(ReportAccess, prof)
    if cond is None:
        return set()

    rows = (
        db.query(ReportAccess.report_key, ReportAccess.effect)
        .filter(cond, still_live_condition(ReportAccess))
        .all()
    )
    allow = {k for k, e in rows if e == EFFECT_ALLOW}
    deny = {k for k, e in rows if e == EFFECT_DENY}
    return allow - deny


def can_view_report(db: Session, user, key: ReportKey, profile: dict | None = None) -> bool:
    """Có được xem báo cáo `key` không — dùng trong `report_access.guard.require_report`."""
    return int(key) in viewable_keys(db, user, profile)
