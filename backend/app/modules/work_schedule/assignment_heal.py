"""Mở lại lịch cũ khi XÓA dòng gán đã từng tự đóng / tự nối nó (M4, chốt 05/10/2026).

Tạo dòng gán mới C trên dòng «không thời hạn» P thì P bị đóng ở `from − 1` (và, nếu C có hạn,
sinh dòng nối lại R từ `to + 1`). Cả P lẫn R mang `linked_assignment_id = C.id`. Xóa nhầm C mà
không mở lại thì khoảng của C thành LỖ HỔNG: nhân sự tụt xuống lịch phòng ban/hệ thống và số ngày
nghỉ đổi âm thầm. Nên khi xóa C ta gộp lại — nhưng CHỈ khi hình dạng ban đầu còn nguyên.
"""
from datetime import timedelta

from sqlalchemy.orm import Session

from .model import WorkScheduleAssignment as A


def clear_links(db: Session, assignment_id: int) -> None:
    """Gỡ liên kết khỏi mọi dòng trỏ vào `assignment_id` (sửa ngày/đích → mở lại không còn an toàn)."""
    db.query(A).filter(A.linked_assignment_id == assignment_id).update(
        {A.linked_assignment_id: None}, synchronize_session="fetch")


def _overlaps_other(db: Session, deleted: A, start, end, exclude: set[int]) -> bool:
    q = db.query(A.id).filter(A.target_level == deleted.target_level,
                              A.target_id == deleted.target_id,
                              A.id != deleted.id)
    if exclude:
        q = q.filter(A.id.notin_(exclude))
    q = q.filter((A.effective_to.is_(None)) | (A.effective_to >= start))
    if end is not None:
        q = q.filter(A.effective_from <= end)
    return q.first() is not None


def heal_before_delete(db: Session, deleted: A, user_id: int) -> list[tuple[int, str]]:
    """Chạy TRƯỚC `db.delete(deleted)`/commit. Trả danh sách (id, mô tả audit) cho nơi gọi ghi sổ.

    Không bao giờ ném lỗi nghiệp vụ: không mở lại được thì thôi (chỉ gỡ liên kết).
    """
    linked = db.query(A).filter(A.linked_assignment_id == deleted.id,
                                A.target_level == deleted.target_level,
                                A.target_id == deleted.target_id).all()
    audits: list[tuple[int, str]] = []
    one_day = timedelta(days=1)
    prev = next((a for a in linked if a.effective_to == deleted.effective_from - one_day), None)
    if prev is not None:
        resume = None
        if deleted.effective_to is not None:
            want = deleted.effective_to + one_day
            resume = next((a for a in linked if a is not prev and a.effective_from == want
                           and a.schedule_id == prev.schedule_id), None)
        can_heal = deleted.effective_to is None or resume is not None
        new_end = resume.effective_to if resume is not None else None
        exclude = {prev.id} | ({resume.id} if resume is not None else set())
        if can_heal and not _overlaps_other(db, deleted, deleted.effective_from, new_end, exclude):
            prev.effective_to = new_end
            prev.updated_by = user_id
            audits.append((prev.id, f"Tự mở lại lịch cũ do xóa dòng gán #{deleted.id}"))
            if resume is not None:
                audits.append((resume.id, f"Xóa dòng nối lại do xóa dòng gán #{deleted.id}"))
                linked.remove(resume)
                db.delete(resume)
    for a in linked:
        a.linked_assignment_id = None
    return audits
