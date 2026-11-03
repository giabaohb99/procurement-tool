"""YCBG — đổi trạng thái, trả về người yêu cầu, chuyển phòng xử lý, chốt báo cáo, hoàn thành phiếu (bao-CR-715 tách
từ service.py).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import normalize_handler_dept_id

from .model import LS_COMPLETED, LS_RESURVEY, SurveyRequest, SurveyRequestOption, SurveyRequestPr
from .base_service import ENTITY, _stamp_result_date, get_sr, lines_of, options_of
from .line_service import _has_scope_all, can_process_line


def set_status(db: Session, sid: int, status: str, user_id: int, reason: str = "") -> SurveyRequest:
    s = get_sr(db, sid)
    s.status = status
    s.updated_by = user_id
    if status in ("rejected", "cancelled"):
        s.reject_reason = reason
    db.commit()
    record(db, user_id, ENTITY, sid, status, reason)
    db.refresh(s)
    return s


# ───────────── bao-CR-414 GĐ5: chuyển phòng xử lý / trả về phòng lập ─────────────

TRANSFERABLE_STATUSES = ("approved", "processing")


def can_transfer_dept(db: Session, s: SurveyRequest) -> bool:
    """Việc khảo sát CHƯA thật sự bắt đầu: phiếu đang duyệt/xử lý (chưa `survey_done`), chưa
    dòng nào Hoàn thành, chưa phương án nào được CHỌN, chưa sinh YCMH nào từ phiếu này.
    Phương án đã nhập nhưng chưa chọn không chặn (giữ nguyên); dòng "khảo sát lại" vẫn cho."""
    if s.status not in TRANSFERABLE_STATUSES:
        return False
    lines = lines_of(db, s.id)
    line_ids = [ln.id for ln in lines]
    for ln in lines:
        if ln.is_completed or ln.line_status == LS_COMPLETED:
            return False
    if line_ids and db.query(SurveyRequestOption.id).filter(
            SurveyRequestOption.survey_request_line_id.in_(line_ids),
            SurveyRequestOption.is_chosen == True).first():  # noqa: E712
        return False
    return not db.query(SurveyRequestPr.id).filter(SurveyRequestPr.survey_request_id == s.id).first()


#  bao-CR-554 — "Trả về" cho người yêu cầu sửa: từ Chờ duyệt như cũ, và từ Đã duyệt / Đang xử lý
#  (đại ca chốt 02/10/2026: quản lý hủy duyệt để nhân viên sửa rồi gửi lại) với cùng chốt chặn
#  của chuyển phòng — việc khảo sát chưa thật sự bắt đầu.
def can_return_requester(db: Session, s: SurveyRequest) -> bool:
    if s.status == "submitted":
        return True
    return can_transfer_dept(db, s)


def return_to_requester(db: Session, sid: int, reason: str, user_id: int) -> SurveyRequest:
    """Trả phiếu về "Bị trả lại" (rejected). Phiếu đã duyệt thì gỡ NSTM + ngày tiếp nhận mọi
    dòng (duyệt lại sẽ tự gán lại), như chuyển phòng."""
    s = get_sr(db, sid)
    if not can_return_requester(db, s):
        raise HTTPException(400, "Chỉ trả về được phiếu đang chờ duyệt, hoặc đã duyệt mà chưa dòng nào "
                                 "hoàn thành, chưa chọn phương án và chưa sinh YCMH")
    if s.status != "submitted":
        for ln in lines_of(db, sid):
            ln.assignee = ""
            ln.received_date = ""
            ln.updated_by = user_id
        db.flush()
    return set_status(db, sid, "rejected", user_id, reason)


def transfer_handler_dept(db: Session, sid: int, handler_dept_id: int, reason: str,
                          user_id: int) -> SurveyRequest:
    """Đẩy YCBG sang phòng xử lý khác (hoặc TRẢ VỀ THU MUA khi `handler_dept_id` = 0 — bao-CR-524:
    đích là phòng thu mua mặc định, ghi id thật).

    YCBG không có bước điều phối riêng (duyệt là tự gán rồi sang `processing`), nên ở đây chỉ
    gỡ NSTM + ngày tiếp nhận của mọi dòng và đổi phòng; trạng thái giữ nguyên. Phòng nhận
    gán lại bằng tay ở từng dòng (hoặc bấm tự gán). Không chuyển một phần dòng."""
    from app.modules.purchase_request.service import dept_name_of, validate_transfer_target
    s = get_sr(db, sid)
    if not can_transfer_dept(db, s):
        raise HTTPException(400, "Chỉ chuyển được khi phiếu đang xử lý, chưa dòng nào hoàn thành, "
                                 "chưa chọn phương án và chưa sinh YCMH")
    validate_transfer_target(db, s, handler_dept_id, reason)
    old_id = int(s.handler_dept_id or 0)
    new_id = normalize_handler_dept_id(db, handler_dept_id)
    for ln in lines_of(db, sid):
        ln.assignee = ""
        ln.received_date = ""
        ln.updated_by = user_id
    s.handler_dept_id = new_id
    s.updated_by = user_id
    db.commit()
    action = "return_dept" if not int(handler_dept_id or 0) else "transfer_dept"
    old_name = dept_name_of(db, old_id, s.department)
    new_name = dept_name_of(db, new_id, s.department)
    record(db, user_id, ENTITY, sid, action, f"{reason.strip()} · {old_name} -> {new_name}")
    db.refresh(s)
    return s


def _require_report_ready(db: Session, sid: int) -> None:
    """Chặn đóng phiếu khi còn hồ sơ báo cáo thực hiện BẮT BUỘC chưa hoàn tất.

    Báo cáo là tùy chọn — phiếu không khai báo cáo thì qua ngay. Nhưng đã khai hồ
    sơ bắt buộc thì phải hoàn tất trước, đây là điều kiện đóng phiếu (yêu cầu KH).
    """
    from . import report_service
    pending = report_service.required_docs_pending_of(db, ENTITY, sid)
    if pending:
        titles = ", ".join(d.title for d in pending[:3])
        more = f" và {len(pending) - 3} hồ sơ khác" if len(pending) > 3 else ""
        raise HTTPException(
            400, f"Còn {len(pending)} hồ sơ báo cáo thực hiện bắt buộc chưa hoàn tất "
                 f"({titles}{more}). Hoàn tất chúng trước khi chuyển Hoàn thành.")


def finalize_sr(db: Session, sid: int, user_id: int) -> SurveyRequest:
    """Admin/QL chuyển Hoàn thành (dừng hẳn). Cho phép từ 'Đã khảo sát' hoặc 'Đã tạo YCMH'."""
    s = get_sr(db, sid)
    if s.status not in ("survey_done", "pr_created"):
        raise HTTPException(400, "Chỉ hoàn thành phiếu ở trạng thái Đã khảo sát hoặc Đã tạo Yêu cầu mua hàng")
    _require_report_ready(db, sid)
    return set_status(db, sid, "done", user_id)


def complete_sr(db: Session, sid: int, user, profile: dict = None, empty_line_ids=None):
    """Chốt PHẦN KHẢO SÁT CỦA NGƯỜI GỌI. Dòng phụ trách phải có option HOẶC được 'chốt rỗng'
    (no_option, không có NCC phù hợp). Phiếu -> 'survey_done' khi MỌI dòng có option hoặc chốt rỗng.
    empty_line_ids: các dòng (mình phụ trách, chưa option) tick chốt rỗng. Trả (phiếu, fully_done)."""
    empty_ids = {int(x) for x in (empty_line_ids or [])}
    s = get_sr(db, sid)
    if s.status not in ("processing", "survey_done"):
        raise HTTPException(400, "Chỉ chốt được phiếu đang xử lý hoặc đã khảo sát")
    lns = lines_of(db, sid)
    if not lns:
        raise HTTPException(400, "Phiếu không có dòng nào")
    # Quản lý/Admin TM (scope all) & người tạo -> chốt cả phiếu; NSTM -> chỉ dòng mình phụ trách
    see_all = _has_scope_all(profile) or getattr(user, "id", 0) == s.created_by
    my_lines = lns if see_all else [ln for ln in lns if can_process_line(db, ln, profile)]
    # Cập nhật cờ chốt rỗng: có option -> bỏ cờ; không option + được tick -> chốt rỗng.
    # Đồng thời: dòng đang "Cần khảo sát lại" mà NSTM đã khảo sát lại xong (nay có option)
    # -> GỠ cờ, dòng về "Đã khảo sát". (Trước đây cờ chỉ gỡ khi người YC bấm chọn PA.)
    resurveyed = 0
    for ln in my_lines:
        if options_of(db, ln.id):
            ln.no_option = False
            if ln.line_status == LS_RESURVEY:
                ln.line_status = ""
                ln.updated_by = getattr(user, "id", 0)
                resurveyed += 1
            _stamp_result_date(ln)
        elif ln.id in empty_ids:
            ln.no_option = True
            ln.updated_by = getattr(user, "id", 0)
            _stamp_result_date(ln)   # chốt rỗng cũng là trả kết quả — "khảo sát rồi, không có NCC phù hợp"
    db.flush()
    missing_mine = [ln.internal_line_code or str(ln.id) for ln in my_lines
                    if not options_of(db, ln.id) and not ln.no_option]
    if missing_mine:
        raise HTTPException(400, f"Còn {len(missing_mine)} dòng chưa có phương án — hãy khảo sát hoặc chốt rỗng")
    all_done = all(options_of(db, ln.id) or ln.no_option for ln in lns)   # đủ mọi dòng của mọi NSTM?
    if all_done:
        if s.status != "survey_done":
            s = set_status(db, sid, "survey_done", getattr(user, "id", 0))
        return s, True, resurveyed
    db.refresh(s)
    return s, False, resurveyed   # phần của mình xong, còn dòng NSTM khác
