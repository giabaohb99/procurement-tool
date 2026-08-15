"""Hàm dựng truy vấn dùng chung cho VĂN BẢN.

⚠️ **Mọi endpoint đọc `tab_document` phải đi qua đây**, không ai được gọi thẳng
`db.query(Document)`.

Lý do: bảng chứa ba loại bản ghi (`origin` 1 nội bộ · 2 văn bản pháp luật ngoài
· 3 văn bản đến) mà chỉ loại 1 được hiện ở danh sách / tìm kiếm / thống kê của
phân hệ. Để mỗi controller tự nhớ thêm `filter(origin == 1)` thì sớm muộn cũng
sót một chỗ — và chỗ sót đó là một trang lộ ra bản ghi không thuộc về nó
(`van-thu/02` chỗ dễ sai số 12). Bài kiểm `test_document_origin_filter.py` gọi
hết các endpoint danh sách để canh việc này.
"""
from sqlalchemy.orm import Query, Session

from .model import ORIGIN_INTERNAL, Document


def documents_query(db: Session, origin: int = ORIGIN_INTERNAL) -> Query:
    """Truy vấn văn bản đã lọc sẵn `origin`. Truyền `origin=None` để lấy tất cả.

    `origin=None` chỉ dành cho việc quản trị nội bộ (dọn dữ liệu, thống kê toàn
    bảng) — **không dùng cho endpoint nào người dùng gọi được.**
    """
    q = db.query(Document)
    if origin is not None:
        q = q.filter(Document.origin == origin)
    return q
