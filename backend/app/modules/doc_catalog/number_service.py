"""Cấp số cho sổ văn bản.

⚠️ **Đọc trước khi gọi.** Số hiệu văn bản là số sổ sách: trùng số nghĩa là hai
văn bản cùng một số hiệu, còn nhảy cóc nghĩa là sổ thủng lỗ không giải thích
được khi thanh tra. Cả hai đều không sửa được sau khi đã ban hành.

Vì thế có đúng MỘT đường cấp số: `next_number()` dưới đây, và nó **bắt buộc chạy
trong cùng transaction với việc ghi bản ghi mang số đó**. Cấp số ở transaction
riêng rồi mới ghi bản ghi thì giữa hai bước có một khoảng trống — ghi hỏng là
mất số vĩnh viễn.

Ba lớp chặn trùng, phải có đủ cả ba:
  1. khóa dòng bộ đếm khi cấp (`SELECT ... FOR UPDATE`) — ở đây;
  2. ràng buộc `UNIQUE(scope_key)` ở tầng dữ liệu;
  3. cùng một transaction với việc ghi bản ghi — trách nhiệm của nơi gọi.
"""
from sqlalchemy.orm import Session

from .book_model import DocumentBook, NumberSequence


def book_scope_key(book_code: str, year: int, reset_yearly: bool = True) -> str:
    """Khóa bộ đếm của một sổ.

    Sổ không đếm lại theo năm thì dùng chung một dòng cho mọi năm — nếu vẫn kèm
    năm vào khóa thì sang năm mới nó lặng lẽ đếm lại từ 1, đúng cái mà người
    khai sổ đã tắt.
    """
    return f"book:{book_code}:{year}" if reset_yearly else f"book:{book_code}"


def next_number(db: Session, scope_key: str, year: int, start_no: int = 1) -> int:
    """Cấp số kế tiếp của một bộ đếm. PHẢI gọi trong transaction đang ghi bản ghi.

    `start_no` chỉ dùng lúc bộ đếm chưa tồn tại — dành cho trường hợp chuyển từ
    sổ giấy đang dở sang (sổ giấy đã tới số 47 thì sổ điện tử bắt đầu từ 48).
    """
    row = (
        db.query(NumberSequence)
        .filter(NumberSequence.scope_key == scope_key)
        .with_for_update()  # khóa dòng: người thứ hai phải xếp hàng chờ
        .one_or_none()
    )

    if row is None:
        # `flush` chứ không `commit`: vẫn nằm trong transaction của nơi gọi.
        row = NumberSequence(scope_key=scope_key, year=year, current_no=start_no - 1)
        db.add(row)
        db.flush()

    if row.year != year:  # sang năm mới thì đếm lại từ đầu
        row.year, row.current_no = year, start_no - 1

    row.current_no += 1
    return row.current_no


def next_book_number(db: Session, book: DocumentBook, year: int) -> int:
    """Cấp số kế tiếp cho một quyển sổ. Xem cảnh báo ở đầu tệp."""
    key = book_scope_key(book.code, year, book.reset_yearly)
    return next_number(db, key, year, book.start_no)


def peek_book_number(db: Session, book: DocumentBook, year: int) -> int:
    """Số kế tiếp SẼ là bao nhiêu — chỉ để hiển thị, **không chiếm số**.

    Con số này có thể lệch nếu có người cấp số ngay sau khi màn hình đọc xong.
    Đó là chấp nhận được với một dòng xem trước; tuyệt đối không dùng giá trị
    này để ghi xuống bản ghi.
    """
    key = book_scope_key(book.code, year, book.reset_yearly)
    row = db.query(NumberSequence).filter(NumberSequence.scope_key == key).one_or_none()
    if row is None or row.year != year:
        return book.start_no
    return row.current_no + 1


def format_book_number(book: DocumentBook, seq: int, year: int) -> str:
    """Chuỗi số hiển thị trên sổ: `CVĐ 08/2026`, hoặc `08/2026` khi không có tiền tố."""
    body = f"{seq:02d}/{year}"
    return f"{book.number_prefix} {body}".strip()
