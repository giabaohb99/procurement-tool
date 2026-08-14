"""API SỔ VĂN BẢN.

Cố ý **không có endpoint "cấp một số"**. Số phải cấp trong cùng transaction với
việc ghi bản ghi mang số đó (xem `number_service`); mở một endpoint cấp số đứng
riêng là mời gọi đúng cái sai đó — gọi xong, ghi bản ghi lỗi, số biến mất khỏi
sổ mà không ai biết. Màn hình chỉ đọc `next_no` để xem trước.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import book_service as service
from .book_model import DocumentBook
from .book_schema import DocumentBookCreate, DocumentBookUpdate

router = APIRouter(prefix="/api/document-books", tags=["document_book"])

FILTERABLE = ["code", "name", "kind", "company_id", "department_id", "is_active"]


@router.get("")
def list_books(
    request: Request,
    year: int | None = Query(None, description="Năm tính số kế tiếp; mặc định năm nay"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("document_book", "read")),
):
    profile = get_perm_profile(db, user)
    q = apply_filters(db.query(DocumentBook), DocumentBook, request, FILTERABLE)
    q = apply_scope(q, DocumentBook, "document_book", user, profile)

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
    user=Depends(require("document_book", "read")),
):
    book = db.get(DocumentBook, book_id)
    if not book:
        raise HTTPException(404, "Không tìm thấy sổ")
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
    book = service.update_book(db, book_id, data, user.id)
    record(db, user.id, "document_book", book.id, "update")
    return success(service.serialize(db, book), "Đã cập nhật")


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("document_book", "delete")),
):
    service.delete_book(db, book_id)
    record(db, user.id, "document_book", book_id, "delete")
    return success(None, "Đã xóa sổ")


@router.get("/{book_id}/counter")
def get_counter(
    book_id: int,
    year: int | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(require("document_book", "read")),
):
    """Tình trạng bộ đếm của sổ trong một năm — dùng cho khối "Bộ đếm" trên trang chi tiết."""
    book = db.get(DocumentBook, book_id)
    if not book:
        raise HTTPException(404, "Không tìm thấy sổ")

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
