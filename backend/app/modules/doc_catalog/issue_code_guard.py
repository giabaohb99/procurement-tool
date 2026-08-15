"""Khóa MÃ SỐ HIỆU sau khi đã cấp số (`van-thu` D07).

Mã của pháp nhân / phòng ban / loại văn bản đi thẳng vào số hiệu đã ban hành
(`08/2026/TB-NS-DEGO`). Đổi mã sau đó thì số cũ và số mới cùng tồn tại trong một
sổ mà không có gì nối chúng lại — giấy tờ đã gửi ra ngoài mang mã cũ, tra trong
hệ thống ra mã mới.

Vì thế chặn ở **tầng dịch vụ**, kèm câu báo nói rõ vì sao, chứ không phải khóa ô
nhập trên giao diện.

Đặt ở `doc_catalog` chứ không ở `core` vì đây là quy tắc của phân hệ Văn thư;
`company` và `department` gọi vào bằng import muộn để khỏi vòng phụ thuộc.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .book_model import NumberSequence


def _has_sequence(db: Session, pattern: str) -> bool:
    return db.query(NumberSequence.id).filter(NumberSequence.scope_key.like(pattern)).first() is not None


def ensure_company_issue_code_free(db: Session, old_code: str, new_code: str):
    """Mã pháp nhân nằm ở giữa khóa bộ đếm: `doc:DEGO:QC`, `out:DEGO:2026:TB`."""
    if not old_code or old_code == new_code:
        return
    if _has_sequence(db, f"doc:{old_code}:%") or _has_sequence(db, f"out:{old_code}:%"):
        raise HTTPException(
            400, f"Pháp nhân đã cấp số văn bản với mã {old_code}, không đổi được mã số hiệu.")


def ensure_doc_type_code_free(db: Session, old_code: str, new_code: str):
    """Mã loại nằm ở cuối khóa: `doc:DEGO:QC`, `out:DEGO:2026:TB`."""
    if not old_code or old_code == new_code:
        return
    if _has_sequence(db, f"doc:%:{old_code}") or _has_sequence(db, f"out:%:{old_code}"):
        raise HTTPException(
            400, f"Loại văn bản {old_code} đã cấp số, không đổi được mã.")


def ensure_department_issue_code_free(db: Session, department_id: int,
                                      old_code: str, new_code: str):
    """Mã phòng ban KHÔNG nằm trong khóa bộ đếm — nó chỉ có trong chuỗi số hiệu.

    Nên ở đây phải hỏi ngược lại: phòng này đã có văn bản nào mang số chưa.
    """
    if not old_code or old_code == new_code:
        return
    if _department_has_issued_document(db, department_id):
        raise HTTPException(
            400, f"Phòng ban đã có văn bản cấp số với mã {old_code}, không đổi được mã số hiệu.")


def ensure_department_kind_free(db: Session, department_id: int, old_kind: int, new_kind: int):
    """Đổi loại phòng có thể làm mã phòng xuất hiện/biến mất khỏi số hiệu."""
    if old_kind == new_kind:
        return
    if _department_has_issued_document(db, department_id):
        raise HTTPException(
            400, "Phòng ban đã có văn bản cấp số, không đổi được loại đơn vị.")


def ensure_department_company_issue_code_free(
    db: Session,
    department_id: int,
    company_id: int,
    old_code: str,
    new_code: str,
):
    """Khóa mã ghi đè A06 sau khi cặp phòng ban/pháp nhân đã phát hành văn bản."""
    if old_code == new_code:
        return
    if _department_has_issued_document(db, department_id, company_id):
        raise HTTPException(
            400,
            "Phòng ban đã cấp số văn bản tại pháp nhân này, không đổi được mã số hiệu riêng.",
        )


def _department_has_issued_document(
    db: Session,
    department_id: int,
    company_id: int | None = None,
) -> bool:
    from app.modules.document.model import Document

    query = db.query(Document.id).filter(
        Document.department_id == department_id,
        (Document.issue_number != "") | (Document.doc_code.isnot(None)),
    )
    if company_id is not None:
        query = query.filter(Document.company_id == company_id)
    return query.first() is not None
