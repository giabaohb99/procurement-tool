"""Hai khối «Sản phẩm khác cùng công ty» và «Thuốc cùng hoạt chất» của trang chi tiết thuốc BVTV
(01/10/2026 — bê theo trang nguồn danhmuc.thuocbvtv.com). Tính từ chính danh mục đã nạp, không cào
thêm.

«Cùng hoạt chất» = cùng TẬP tên hoạt chất sau khi bỏ hàm lượng: "Chitosan 2% + Oligo-Alginate 10%"
khớp "Oligo-Alginate 5% + Chitosan 3%" (thứ tự và hàm lượng khác nhau vẫn là cùng hoạt chất, đúng
như trang nguồn ghi "(Chitosan + Oligo-Alginate)"). Lọc thô bằng `LIKE` từng tên ở SQL rồi so tập
chính xác ở Python — danh mục ~7.000 thuốc, mỗi tên chỉ còn vài chục dòng phải so.
"""
import re

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .constants import PESTICIDE_STATUS_LABELS
from .model import CustomsPesticide

#  Số thuốc mỗi khối mặc định — bằng trang nguồn. «Xem tất cả» gọi lại với `limit` tới trần
#  `MAX_RELATED_LIMIT` (công ty nhiều thuốc nhất trong danh mục thật có 219 thuốc) và MỞ RỘNG ngay
#  trong khối — không chuyển sang danh sách vì ô tìm ở đó khớp chuỗi liền, «Chitosan +
#  Oligo-Alginate» sẽ không ra «Chitosan 2% + Oligo-Alginate 10%».
RELATED_LIMIT = 10
MAX_RELATED_LIMIT = 300
_PAREN = re.compile(r"\([^)]*\)")
#  Hàm lượng ĐỨNG CUỐI một hoạt chất: "2%", "400g/l", "200 g/kg", "0.398%", "12% w/w".
_TRAILING_AMOUNT = re.compile(
    r"\s+\d+(?:[.,]\d+)?\s*(?:%|[a-zµ]+\s*/\s*[a-z]+)?\s*(?:w/w|w/v)?\s*$", re.IGNORECASE)
_SPACES = re.compile(r"\s+")


def ingredient_names(active_ingredient: str) -> list[str]:
    """Tên hoạt chất (giữ chữ hoa/thường gốc, đúng thứ tự) sau khi bỏ hàm lượng và ngoặc."""
    names = []
    for part in (active_ingredient or "").split("+"):
        name = _PAREN.sub(" ", part)
        name = _TRAILING_AMOUNT.sub("", name)
        name = _SPACES.sub(" ", name).strip(" ,;")
        if name:
            names.append(name)
    return names


def ingredient_key(active_ingredient: str) -> tuple[str, ...]:
    """Khóa so khớp: tập tên (không phân biệt hoa/thường, thứ tự). Rỗng = không có gì để so."""
    return tuple(sorted({n.casefold() for n in ingredient_names(active_ingredient)}))


def _brief(p: CustomsPesticide) -> dict:
    return {"id": p.id, "trade_name": p.trade_name, "pest_group": p.pest_group,
            "active_ingredient": p.active_ingredient, "registrant": p.registrant,
            "status": p.status, "status_label": PESTICIDE_STATUS_LABELS.get(p.status, "")}


def _same_registrant(db: Session, p: CustomsPesticide, limit: int) -> dict:
    if not p.registrant.strip():
        return {"total": 0, "items": []}
    base = db.query(CustomsPesticide).filter(CustomsPesticide.registrant == p.registrant,
                                              CustomsPesticide.id != p.id)
    total = base.with_entities(func.count(CustomsPesticide.id)).scalar() or 0
    rows = base.order_by(CustomsPesticide.trade_name, CustomsPesticide.id).limit(limit).all()
    return {"total": total, "items": [_brief(r) for r in rows]}


def _same_ingredient(db: Session, p: CustomsPesticide, limit: int) -> dict:
    names = ingredient_names(p.active_ingredient)
    key = ingredient_key(p.active_ingredient)
    label = " + ".join(names)
    if not key:
        return {"label": label, "total": 0, "items": []}
    query = db.query(CustomsPesticide).filter(CustomsPesticide.id != p.id)
    for name in names:
        #  Lọc thô: chứa đủ mọi tên. Ký tự đại diện của LIKE trong tên hoạt chất (hiếm) chỉ làm
        #  lọc thô RỘNG hơn — bước so tập bên dưới vẫn loại đúng.
        query = query.filter(CustomsPesticide.active_ingredient.ilike(f"%{name}%"))
    rows = [r for r in query.order_by(CustomsPesticide.trade_name, CustomsPesticide.id).all()
            if ingredient_key(r.active_ingredient) == key]
    return {"label": label, "total": len(rows), "items": [_brief(r) for r in rows[:limit]]}


def related_pesticides(db: Session, pesticide_id: int, limit: int = RELATED_LIMIT) -> dict:
    p = db.get(CustomsPesticide, pesticide_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy thuốc BVTV")
    limit = max(1, min(limit, MAX_RELATED_LIMIT))
    return {"same_registrant": _same_registrant(db, p, limit),
            "same_ingredient": _same_ingredient(db, p, limit)}
