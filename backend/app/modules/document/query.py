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
from sqlalchemy import func, or_, select
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


def an_ban_rieng_co_goc_xem_duoc(query: Query) -> Query:
    """Bỏ BẢN RIÊNG ra khỏi danh sách khi bản gốc của nó cũng nằm trong danh sách.

    Một văn bản clone cho mười hai pháp nhân sinh ra mười hai bản ghi mang cùng
    tiêu đề. Để chúng đứng ngang hàng bản gốc thì danh sách thành mười ba dòng
    gần như giống hệt nhau, và người đọc không đếm nổi có bao nhiêu văn bản
    thật. Giao diện bày chúng thành nhánh bung ra từ dòng bản gốc.

    ⚠️ Chỉ giấu khi bản gốc **cũng xem được**: người ở pháp nhân con không xem
    được bản gốc thì bản riêng chính là văn bản của họ — giấu đi là danh sách
    của họ trống trơn. Vì vậy điều kiện dựa trên chính `query` đang lọc theo
    quyền của người đang xem, không phải trên toàn bảng.
    """
    goc_xem_duoc = query.with_entities(Document.id).subquery()
    return query.filter(or_(
        Document.source_document_id.is_(None),
        Document.source_document_id == 0,
        Document.source_document_id.not_in(select(goc_xem_duoc.c.id)),
    ))


def dem_ban_rieng(query: Query, document_ids: list[int]) -> dict[int, int]:
    """Mỗi văn bản có bao nhiêu bản riêng **mà người này xem được**.

    Nhận một `query` ĐÃ lọc quyền chứ không nhận `db`: đếm trên toàn bảng thì
    người ở pháp nhân mẹ thấy con số 3 và một mũi tên bung — bấm vào chỉ nhận
    về danh sách rỗng, vì ba bản riêng đó nằm ở ba pháp nhân họ không xem được.
    Mũi tên chỉ nên hiện khi thật sự có gì để bung.
    """
    if not document_ids:
        return {}
    return dict(
        query.with_entities(Document.source_document_id, func.count(Document.id))
        .filter(Document.source_document_id.in_(document_ids))
        .group_by(Document.source_document_id).all()
    )
