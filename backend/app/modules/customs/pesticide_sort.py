"""Sắp xếp bảng "Tra cứu Thuốc BVTV" (duoc-CR-744) — xếp theo ĐÚNG giá trị ô hiển thị, trên cả danh mục đã lọc.

Khóa = `key` cột bên giao diện (`customs-pesticide-columns.tsx`):

  · Cột chữ: chuỗi rỗng coi là trống, xuống cuối (cả hai chiều).
  · `status` xếp theo thứ tự vòng đời của mã (Còn hiệu lực -> Hết hiệu lực -> Đang sử dụng), không theo chữ cái
    của nhãn; tình trạng chưa rõ (mã 0, ô trống) xuống cuối.
  · `use_count` (Phạm vi sử dụng) đếm dòng phạm vi bằng truy vấn con; thuốc không có dòng nào hiện ô trống nên
    cũng xuống cuối thay vì lẫn với số 0 thật.
  · `banned` (Hoạt chất cấm) không nằm trong DB: là kết quả khớp tên với danh sách cấm TT 75/2025. Dựng
    bản đồ id thuốc -> tên hoạt chất cấm ĐẦU TIÊN (đúng nhãn đầu tiên ô đang hiện) bằng MỘT lượt quét danh mục,
    chỉ khi chính cột này được bấm; thuốc không dính hoạt chất cấm (đa số) xuống cuối.
"""
from sqlalchemy import case, func, null, select
from sqlalchemy.orm import Session

from . import banned_ingredient_match as banned_match
from .constants import PESTICIDE_STATUS_LABELS
from .list_sort import SortExpression, build_order, text_col
from .model import CustomsPesticide, CustomsPesticideUse

P = CustomsPesticide

#  Khóa xếp được; bài kiểm canh khớp các cột bên giao diện.
PESTICIDE_SORT_KEYS = frozenset({"trade_name", "active_ingredient", "banned", "concentration", "pest_group",
                                 "registrant", "registration_no", "expires_on", "status", "use_count", "sector"})


def _first_banned_name_expression(db: Session) -> SortExpression:
    """id thuốc -> tên hoạt chất cấm đầu tiên ô "Hoạt chất cấm" hiển thị; không dính cấm -> trống."""
    matcher = banned_match.load_matcher(db)
    if not matcher.by_key:
        return null()
    names: dict[int, str] = {}
    for pid, active in db.query(P.id, P.active_ingredient):
        hits = matcher.match(active)
        if hits:
            names[pid] = (hits[0].name or "").strip()
    return case(names, value=P.id, else_=None) if names else null()


def build_pesticide_sort_map(db: Session, key: str) -> dict[str, SortExpression]:
    status_rank = {int(code): int(code) for code, label in PESTICIDE_STATUS_LABELS.items() if label}
    use_count = (select(func.count(CustomsPesticideUse.id))
                 .where(CustomsPesticideUse.pesticide_id == P.id).scalar_subquery())
    sort_map: dict[str, SortExpression] = {
        "trade_name": text_col(P.trade_name),
        "active_ingredient": text_col(P.active_ingredient),
        "concentration": text_col(P.concentration),
        "pest_group": text_col(P.pest_group),
        "registrant": text_col(P.registrant),
        "registration_no": text_col(P.registration_no),
        "expires_on": P.expires_on,
        "sector": text_col(P.sector),
        "status": case(status_rank, value=P.status, else_=None),   # số: chỉ NULL là ô trống
        "use_count": func.nullif(use_count, 0),
    }
    if key == "banned":
        sort_map["banned"] = _first_banned_name_expression(db)
    return sort_map


def pesticide_order(db: Session, sort_by: str | None, sort_dir: str | None):
    """ORDER BY theo cột; `None` khi khóa rỗng / lạ (nơi gọi dùng thứ tự mặc định theo tên thuốc)."""
    key = (sort_by or "").strip()
    if key not in PESTICIDE_SORT_KEYS:
        return None
    return build_order(key, sort_dir, build_pesticide_sort_map(db, key), P.id)
