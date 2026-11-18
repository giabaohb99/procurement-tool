"""Phân hệ Dự án — PHẠM VI số liệu của màn Tổng quan (duoc-CR-782).

Mặc định phân hệ lấy ranh giới là TƯ CÁCH THÀNH VIÊN (`visible_list_ids`): ai không được mời vào dự án / nhóm thì
không thấy việc nào. Đúng cho màn làm việc, nhưng màn Tổng quan của người QUẢN LÝ vì vậy ra toàn số 0 — xếp không
phải thành viên của từng dự án (anh Được báo 18/11/2026: "xáo rỗng").

Luật anh chốt: ai **xem được báo cáo Công việc & Dự án** (`ReportKey.WORK`, gán ở tab Báo cáo của Phân quyền tài khoản;
admin được gán sẵn bởi migration + `ensure_report_access_defaults`) thì Tổng quan tính trên MỌI dự án; còn lại giữ
nguyên luật thành viên. Dùng lại ĐÚNG khóa đã gác báo cáo Công việc ở phân hệ Báo cáo — một quyền "xem số liệu toàn
bộ dự án", không đẻ thêm khóa thứ hai cho cùng một ý.

Chỉ nới phạm vi ĐỌC SỐ LIỆU của màn Tổng quan: không mở dự án, không sửa được việc ở dự án mình không tham gia.
"""
from sqlalchemy.orm import Session

from app.core.report_keys import ReportKey
from app.modules.report_access.service import can_view_report
from app.modules.work.membership_service import Actor, visible_list_ids
from app.modules.work.model import WorkList

SCOPE_MEMBER = "member"
SCOPE_ALL = "all"


def overview_list_ids(db: Session, actor: Actor, user=None) -> tuple[set[int], str]:
    """`(tập list_id được đếm, phạm vi)`. `user = None` (lời gọi nội bộ, bài kiểm cũ) = luật thành viên."""
    if user is not None and can_view_report(db, user, ReportKey.WORK):
        return {i for (i,) in db.query(WorkList.id).all()}, SCOPE_ALL
    return visible_list_ids(db, actor.employee_id), SCOPE_MEMBER


def openable_list_ids(db: Session, actor: Actor, scope: str, list_ids: set[int]) -> set[int]:
    """Dự án người xem MỞ được (là thành viên). Phạm vi `member` thì mọi dự án đang đếm đều mở được; phạm vi `all` thì
    chỉ phần mình tham gia — dòng của dự án khác vẫn hiện số liệu nhưng giao diện không dẫn link (mở là 403)."""
    if scope != SCOPE_ALL:
        return set(list_ids)
    return visible_list_ids(db, actor.employee_id) & set(list_ids)
