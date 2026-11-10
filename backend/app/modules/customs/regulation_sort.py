"""Sắp xếp bảng "Tra cứu hóa chất" (duoc-CR-744) — duyệt danh mục hóa chất theo văn bản.

Khóa = `key` cột bên giao diện (`customs-regulation-columns.tsx`), xếp theo đúng giá trị ô hiển thị:

  · `seq_no` (STT) là CHỮ trong DB nhưng hiển thị như số -> xếp theo số trước ("2" đứng trước "10"), rồi mới
    theo chữ để dòng con ("5.1") đi liền dòng cha.
  · `list_label` xếp theo MÃ danh sách (thứ tự phụ lục I..IV, TT 75, TT 01), không theo chữ cái của nhãn.
  · `limit` (Ngưỡng / Mức cấm) là cột GHÉP: dòng cấm (theo năm) -> ngưỡng kg -> ngưỡng hỗn hợp % -> không có;
    nhóm luôn theo thứ tự đó (khóa nhóm không đảo chiều), chỉ giá trị trong nhóm đảo theo chiều sắp. Khác đơn vị
    nên KHÔNG so lẫn kg với %.
  · `obligation` (Lưu ý) là câu suy ra (`service._obligation`): xếp theo loại câu (cấm / ngưỡng kg / công bố /
    còn lại) rồi theo căn cứ và phân loại.
  · `pesticide_count` (Thuốc BVTV chứa) không nằm trong DB — tính bằng bộ khớp tên (`banned_ingredient_match`)
    nên dựng bản đồ id -> số thuốc cho CẢ danh sách cấm rồi xếp bằng CASE; dòng không có số xuống cuối.
"""
from sqlalchemy import Integer, case, cast, func, null
from sqlalchemy.orm import Session

from . import banned_ingredient_match as banned_match
from .constants import RegulationList
from .list_sort import SortExpression, build_order, group_col, text_col
from .model import CustomsPesticide, CustomsRegulation

R = CustomsRegulation
_BANNED = int(RegulationList.BANNED_TT75)
_PL4 = int(RegulationList.ND24_PL4)
_PUBLISH = int(RegulationList.PUBLISH_TT01)

#  Khóa xếp được; bài kiểm canh khớp các cột bên giao diện.
REGULATION_SORT_KEYS = frozenset({"seq_no", "list_label", "name", "name_vi", "cas_no", "formula", "limit",
                                  "obligation", "pesticide_count"})


def _pesticide_count_expression(db: Session) -> SortExpression:
    """id hoạt chất cấm -> số thuốc BVTV chứa nó (cùng luật `regulation_browse_service._pesticide_counts`)."""
    banned = db.query(R).filter(R.is_active.is_(True), R.list_code == _BANNED).all()
    if not banned or not db.query(CustomsPesticide.id).first():
        return null()
    index = banned_match.build_index(db)
    counts = {r.id: len(index.get(r.id, ())) for r in banned if banned_match.regulation_keys(r.name)}
    if not counts:
        return null()
    return case(counts, value=R.id, else_=None)


def build_regulation_sort_map(db: Session, key: str) -> dict[str, SortExpression]:
    """Chỉ dựng biểu thức tốn kém (số thuốc) khi chính cột đó được bấm."""
    limit_tier = case((R.list_code == _BANNED, 0), (R.threshold_kg.is_not(None), 1),
                      (R.mixture_pct.is_not(None), 2), else_=None)
    limit_value = case((R.list_code == _BANNED, R.banned_year),
                       else_=case((R.threshold_kg.is_not(None), R.threshold_kg), else_=R.mixture_pct))
    obligation_kind = case((R.list_code == _BANNED, 0),
                           ((R.list_code == _PL4) & R.threshold_kg.is_not(None), 1),
                           (R.list_code == _PUBLISH, 2), else_=3)
    sort_map: dict[str, SortExpression] = {
        "seq_no": [cast(func.nullif(func.trim(R.seq_no), ""), Integer), text_col(R.seq_no)],
        "list_label": R.list_code,
        "name": text_col(R.name),
        "name_vi": text_col(R.name_vi),
        "cas_no": text_col(R.cas_no),
        "formula": text_col(R.formula),
        "limit": [group_col(limit_tier), limit_value],
        "obligation": [obligation_kind, text_col(R.legal_basis), text_col(R.category)],
    }
    if key == "pesticide_count":
        sort_map["pesticide_count"] = _pesticide_count_expression(db)
    return sort_map


def regulation_order(db: Session, sort_by: str | None, sort_dir: str | None):
    """ORDER BY theo cột; `None` khi khóa rỗng / lạ (nơi gọi dùng thứ tự phụ lục mặc định)."""
    key = (sort_by or "").strip()
    if key not in REGULATION_SORT_KEYS:
        return None
    return build_order(key, sort_dir, build_regulation_sort_map(db, key), R.id)
