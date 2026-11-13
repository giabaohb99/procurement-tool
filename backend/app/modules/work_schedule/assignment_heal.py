"""Mở lại lịch cũ khi XÓA dòng gán đã từng tự đóng / tự nối nó (M4, chốt 05/10/2026).

Tạo dòng gán mới C trên dòng "không thời hạn" P thì P bị đóng ở `from − 1` (và, nếu C có hạn,
sinh dòng nối lại R từ `to + 1`). Cả P lẫn R mang `linked_assignment_id = C.id`. Xóa nhầm C mà
không mở lại thì khoảng của C thành LỖ HỔNG: nhân sự tụt xuống lịch phòng ban/hệ thống và số ngày
nghỉ đổi âm thầm. Nên khi xóa C ta gộp lại — nhưng CHỈ khi hình dạng ban đầu còn nguyên.
"""
from datetime import date, timedelta

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


def find_replaced_and_resume(db: Session, row: A) -> tuple[A | None, A | None]:
    """`(dòng bị `row` tự đóng, dòng nối lại sau `row`)` — cùng cách nhận diện với `heal_before_delete`.

    Chỉ trả khi hình dạng ban đầu còn nguyên: dòng bị đóng có `effective_to = row.from − 1`; dòng nối lại bắt đầu ở
    `row.to + 1` và cùng mẫu lịch với dòng bị đóng. Không có dòng bị đóng → `(None, None)`.
    """
    linked = db.query(A).filter(A.linked_assignment_id == row.id, A.target_level == row.target_level,
                                A.target_id == row.target_id).all()
    one_day = timedelta(days=1)
    prev = next((a for a in linked if a.effective_to == row.effective_from - one_day), None)
    if prev is None:
        return None, None
    resume = None
    if row.effective_to is not None:
        want = row.effective_to + one_day
        resume = next((a for a in linked if a is not prev and a.effective_from == want
                       and a.schedule_id == prev.schedule_id), None)
    return prev, resume


def move_resume(db: Session, row: A, prev: A, resume: A | None, new_end: date | None,
                user_id: int) -> list[tuple[int, str]]:
    """Đổi `row.effective_to` thành `new_end` mà dòng bị đóng (`prev`) vẫn nối lại liền mạch.

    * `new_end` None (mở không thời hạn): dòng nối lại hết chỗ đứng → xóa;
    * chưa có dòng nối lại (`row` đang không thời hạn) → tạo bản sao của `prev` từ `new_end + 1`, GIỮ người gán gốc;
    * có rồi → dời ngày bắt đầu của nó về `new_end + 1` (kéo dài hay rút ngắn đều không để hở, không chồng).
    Nơi gọi đã kiểm chồng ngày; chỉ `flush`, không commit. Trả danh sách (id, mô tả) để ghi sổ sau commit.
    """
    audits: list[tuple[int, str]] = []
    if new_end is None:
        if resume is not None:
            audits.append((resume.id, f"Xóa dòng nối lại do dòng gán #{row.id} được mở không thời hạn"))
            db.delete(resume)
        return audits
    new_from = new_end + timedelta(days=1)
    if resume is None:
        resume = A(target_level=prev.target_level, target_id=prev.target_id, schedule_id=prev.schedule_id,
                   effective_from=new_from, effective_to=None, note=prev.note or "",
                   created_by=prev.created_by, updated_by=user_id, linked_assignment_id=row.id)
        db.add(resume)
        db.flush()
        audits.append((resume.id, f"Tự nối lại lịch cũ từ {new_from:%d/%m/%Y} do đặt ngày kết thúc dòng gán #{row.id}"))
    else:
        resume.effective_from = new_from
        resume.updated_by = user_id
        audits.append((resume.id, f"Dời ngày nối lại lịch cũ về {new_from:%d/%m/%Y} do đổi ngày kết thúc dòng gán #{row.id}"))
    return audits


def closed_link_ids(db: Session, assignment_ids: list[int]) -> set[int]:
    """Trong `assignment_ids`, những dòng ĐÃ tự đóng / nối một dòng khác lúc tạo (có dòng trỏ `linked_assignment_id` về nó).

    MỘT truy vấn cho cả danh sách — dùng cho cờ `replaces_previous` ở `serialize_many` lẫn chốt `has_closed_link`.
    """
    if not assignment_ids:
        return set()
    rows = db.query(A.linked_assignment_id).filter(A.linked_assignment_id.in_(assignment_ids)).distinct().all()
    return {r[0] for r in rows}
