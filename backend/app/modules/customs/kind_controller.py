"""Hai danh mục admin của màn Tra cứu giá hải quan + đường dò từ khóa — bao-CR-494 / bao-CR-495.

  · `/api/customs-kind-keywords`   — từ khóa nhận diện Thành phẩm / Nguyên liệu (F04);
  · `/api/customs-search-synonyms` — từ đồng nghĩa cho ô tìm tên hàng (F02);
  · `POST /api/customs/kinds/retag` — gắn lại nhãn cho MỌI dòng sau khi sửa từ khóa;
  · `GET  /api/customs/search/explain?q=` — ô tìm sẽ khớp những cách viết nào.

Khóa quyền: dùng `customs_price` (đọc = ai xem được giá; sửa = `write`, tức người được nạp dữ
liệu). Cố ý KHÔNG mở khóa mới: hai bảng này không có màn hình nghiệp vụ riêng, chúng là cấu
hình của chính màn tra cứu (luật «một khóa = một màn hình», CR-157). Tách tệp khỏi
`controller.py` vì bao-CR-493 đang sửa tệp đó — gộp không đụng nhau.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success

from . import search_service
from .ingredient import retag_all
from .model import CustomsKindKeyword, CustomsSearchSynonym
from .schema import (KindKeywordCreate, KindKeywordOut, KindKeywordUpdate,
                     SearchSynonymCreate, SearchSynonymOut, SearchSynonymUpdate)

ENTITY = "customs_price"

kind_keyword_router = make_crud_router(
    "/api/customs-kind-keywords", ENTITY, CustomsKindKeyword,
    KindKeywordCreate, KindKeywordUpdate, KindKeywordOut,
    ["keyword", "kind", "is_active"], unique_field="keyword",
    csv_headers={"id": "ID", "keyword": "Từ khóa", "kind": "Loại (1 Thành phẩm · 2 Nguyên liệu)",
                 "note": "Ghi chú", "is_active": "Đang dùng"})

search_synonym_router = make_crud_router(
    "/api/customs-search-synonyms", ENTITY, CustomsSearchSynonym,
    SearchSynonymCreate, SearchSynonymUpdate, SearchSynonymOut,
    ["term", "is_active"], unique_field="term",
    csv_headers={"id": "ID", "term": "Từ gốc", "synonyms": "Từ đồng nghĩa (ngăn bằng ;)",
                 "note": "Ghi chú", "is_active": "Đang dùng"})

router = APIRouter(prefix="/api/customs", tags=["customs"])


@router.post("/kinds/retag")
def retag_kinds(db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Gắn lại hoạt chất + hàm lượng + nhãn Thành phẩm/Nguyên liệu cho MỌI dòng.

    Chạy sau khi sửa bộ từ khóa: dòng đã nạp không tự đổi nhãn. Vài chục nghìn dòng chạy
    trong vài giây, không cần tác vụ nền.
    """
    return success(retag_all(db), "Đã gắn lại nhãn cho toàn bộ dòng hàng")


@router.get("/search/explain")
def explain_search(q: str = "", db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Ô tìm đang hiểu thế nào: từ CÓ / KHÔNG CÓ và các cách viết sẽ khớp (đồng nghĩa + nồng độ)."""
    return success(search_service.explain_query(db, q))
