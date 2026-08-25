"""API SỔ VĂN BẢN.

Cố ý **không có endpoint "cấp một số"**. Số phải cấp trong cùng transaction với
việc ghi bản ghi mang số đó (xem `number_service`); mở một endpoint cấp số đứng
riêng là mời gọi đúng cái sai đó — gọi xong, ghi bản ghi lỗi, số biến mất khỏi
sổ mà không ai biết. Màn hình chỉ đọc `next_no` để xem trước.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import book_service as service
from .book_model import DocumentBook
from .book_schema import DocumentBookCreate, DocumentBookUpdate

router = APIRouter(prefix="/api/document-books", tags=["document_book"])

FILTERABLE = ["code", "name", "kind", "company_id", "is_active"]


def nguoi_doc_so(user=Depends(get_current_user)):
    """Cổng vào của BA endpoint ĐỌC sổ — chỉ cần đăng nhập.

    Cố ý bỏ `require("document_book", "read")` và giao toàn bộ việc gác cho lớp
    dưới (`dieu_kien_xem_so` / `so_xem_duoc_hoac_404`), vì lớp đó hỏi sai câu:
    nó hỏi *"vai trò của anh có được đụng vào danh mục Sổ văn bản không"*, trong
    khi **quyền xem sổ còn tới từ chính bảng thành viên** — văn thư thêm ai đó
    vào ô «Người xem sổ» là đã quyết định cho người ấy xem.

    Hệ quả của việc hỏi sai câu, khách báo 25/08/2026: chia sổ cho một người
    xong họ **không thấy sổ đó ở trang của mình** — mà không phải vì bộ lọc, mà
    vì họ ăn **403 ngay ở cửa**, trước khi bộ lọc kịp chạy. Người được chia sổ
    thường là nhân sự nghiệp vụ, không có vai trò nào trên danh mục Sổ văn bản.
    Cùng một cái bẫy và cùng cách chữa với `document/controller.doc_reader`.

    ⚠️ CHỈ ba cửa ĐỌC. Tạo · sửa · xóa vẫn giữ nguyên `require(...)`: được cho
    xem một quyển sổ không có nghĩa là được khai sổ mới hay xóa sổ của người khác.
    """
    return user


@router.get("")
def list_books(
    request: Request,
    year: int | None = Query(None, description="Năm tính số kế tiếp; mặc định năm nay"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(nguoi_doc_so),
):
    profile = get_perm_profile(db, user)
    q = apply_filters(db.query(DocumentBook), DocumentBook, request, FILTERABLE)
    #  KHÔNG dùng `apply_scope`: phạm vi vai trò chỉ biết thu hẹp, mà sổ còn được
    #  chia ĐÍCH DANH qua `tab_document_book_member` — nguồn quyền cộng thêm đó
    #  phải OR vào, xem `service.dieu_kien_xem_so`.
    dieu_kien = service.dieu_kien_xem_so(user, profile)
    if dieu_kien is not None:
        q = q.filter(dieu_kien)

    total = q.count()
    items = (
        q.order_by(DocumentBook.kind, DocumentBook.code)
        .offset(pg["offset"]).limit(pg["limit"]).all()
    )
    return success({
        "total": total,
        "items": [service.serialize(db, book, year) for book in items],
    })


@router.get("/{book_id}")
def get_book(
    book_id: int,
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(nguoi_doc_so),
):
    book = service.so_xem_duoc_hoac_404(db, book_id, user, get_perm_profile(db, user))
    return success(service.serialize(db, book, year))


@router.post("")
def create_book(
    data: DocumentBookCreate,
    db: Session = Depends(get_db),
    user=Depends(require("document_book", "create")),
):
    book = service.create_book(db, data, user.id)
    record(db, user.id, "document_book", book.id, "create", f"Mở sổ {book.code}")
    return success(service.serialize(db, book), "Đã tạo sổ văn bản", 201)


@router.patch("/{book_id}")
def update_book(
    book_id: int,
    data: DocumentBookUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("document_book", "write")),
):
    #  Kiểm QUYỂN NÀO trước khi sửa: quyền vai trò `write` chỉ nói "được sửa sổ",
    #  không nói "được sửa sổ của pháp nhân khác". Xem `service.dieu_kien_sua_so`.
    service.so_sua_duoc_hoac_404(db, book_id, user, get_perm_profile(db, user))
    book = service.update_book(db, book_id, data, user.id)
    record(db, user.id, "document_book", book.id, "update")
    return success(service.serialize(db, book), "Đã cập nhật")


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document_book", "delete")),
):
    service.so_sua_duoc_hoac_404(db, book_id, user, get_perm_profile(db, user), "delete")
    service.delete_book(db, book_id)
    record(db, user.id, "document_book", book_id, "delete")
    return success(None, "Đã xóa sổ")


@router.get("/{book_id}/counter")
def get_counter(
    book_id: int,
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(nguoi_doc_so),
):
    """Tình trạng bộ đếm của sổ trong một năm — dùng cho khối "Bộ đếm" trên trang chi tiết."""
    book = service.so_xem_duoc_hoac_404(db, book_id, user, get_perm_profile(db, user))

    year = year or date.today().year
    data = service.serialize(db, book, year)
    return success({
        "year": year,
        "start_no": book.start_no,
        "issued_count": data["issued_count"],
        "next_no": data["next_no"],
        "next_number_display": data["next_number_display"],
        "reset_yearly": book.reset_yearly,
    })
