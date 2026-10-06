"""Mục «Pháp lý» của Tra cứu thị trường (29/09/2026) — DUYỆT toàn bộ danh mục hóa chất theo văn bản.

Khác `service.lookup_regulations` (tra một từ, tối đa 50 dòng, cho ô tra nhanh): đây là bảng có
phân trang + lọc theo văn bản, để người thu mua đọc cả danh sách cấm / có ngưỡng / phải công bố.
Chỉ đọc dòng đang dùng (`is_active`); sửa danh mục vẫn ở mục «Cấu hình» (khóa `customs_regulation`).
"""
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from . import banned_ingredient_match as banned_match
from .constants import FORMULA_CAS, REGULATION_LIST_LABELS, RegulationList
from .model import CustomsPesticide, CustomsRegulation
from .service import _regulation_out


def _filtered(query, q: str, list_code: int | None):
    query = query.filter(CustomsRegulation.is_active.is_(True))
    t = (q or "").strip()
    if t:
        like = f"%{t}%"
        conds = [CustomsRegulation.name.ilike(like), CustomsRegulation.name_vi.ilike(like),
                 CustomsRegulation.cas_no.ilike(like), CustomsRegulation.formula.ilike(like)]
        cas = FORMULA_CAS.get(t.upper().replace(" ", ""), "")   # «H2SO4» → CAS 7664-93-9
        if cas:
            conds.append(CustomsRegulation.cas_no == cas)
        query = query.filter(or_(*conds))
    if list_code is not None:
        query = query.filter(CustomsRegulation.list_code == list_code)
    return query


def list_regulations(db: Session, q: str, list_code: int | None, offset: int,
                     limit: int) -> tuple[int, list[dict]]:
    total = _filtered(db.query(func.count(CustomsRegulation.id)), q, list_code).scalar() or 0
    rows = (_filtered(db.query(CustomsRegulation), q, list_code)
            #  duoc-CR-598 — đúng thứ tự dòng của phụ lục; dòng thêm tay (`sort_order = 0`) xếp sau.
            .order_by(CustomsRegulation.list_code, CustomsRegulation.sort_order == 0,
                      CustomsRegulation.sort_order, CustomsRegulation.name, CustomsRegulation.id)
            .offset(offset).limit(limit).all())
    counts = _pesticide_counts(db, rows)
    return total, [_regulation_out(r) | {"pesticide_count": counts.get(r.id),
                                         "pesticide_matchable": bool(banned_match.regulation_keys(r.name))}
                   for r in rows]


def _pesticide_counts(db: Session, rows: list[CustomsRegulation]) -> dict[int, int]:
    """Hoạt chất CẤM trên trang → số thuốc trong danh mục BVTV đang chứa nó (khớp tên, tham khảo).

    Dòng không phải TT 75 không có khóa; danh mục thuốc CHƯA nạp thì cũng không có khóa (`None`
    lên màn thành «Chưa nạp danh mục thuốc»), vì «0 thuốc» lúc đó là nói sai: chưa đối chiếu gì.
    Tên cấm không rút ra được khóa nào (`pesticide_matchable` sai) cũng không có số, cùng lý do.

    Dựng bộ khớp từ CẢ danh sách cấm, không riêng các dòng trên trang — y hệt danh sách thuốc
    mở ra từ con số này (`pesticide_service._banned_ids`), nên hai bên luôn bằng nhau.
    """
    banned = [r for r in rows if r.list_code == int(RegulationList.BANNED_TT75)]
    if not banned or not db.query(CustomsPesticide.id).first():
        return {}
    index = banned_match.build_index(db)
    return {r.id: len(index.get(r.id, ())) for r in banned if banned_match.regulation_keys(r.name)}


def regulation_options(db: Session) -> dict:
    """Số hóa chất đang dùng theo từng văn bản — đủ MỌI văn bản, kể cả văn bản chưa nạp dòng nào."""
    counts = dict(db.query(CustomsRegulation.list_code, func.count(CustomsRegulation.id))
                  .filter(CustomsRegulation.is_active.is_(True))
                  .group_by(CustomsRegulation.list_code).all())
    return {"total": sum(counts.values()),
            "lists": [{"value": int(code), "label": REGULATION_LIST_LABELS.get(code, ""),
                       "count": counts.get(int(code), 0)} for code in RegulationList]}
