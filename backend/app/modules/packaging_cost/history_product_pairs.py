"""Cặp (sản phẩm x thành phần) của Lịch sử mua hàng chế độ "Theo mã sản phẩm" (duoc-CR-784, bản mẫu `renderHistBySP`).

Bản mẫu: với mỗi sản phẩm đã chọn (rỗng = mọi sản phẩm có định mức), lấy từng MÃ thành phần của định mức (chai, nắp, nhãn, nhãn
thùng, thùng); một mã xuất hiện ở hai vai trò trong CÙNG sản phẩm chỉ tính MỘT lần, vai trò nhỏ nhất thắng (thứ tự chai -> thùng).
Mỗi lần mua của mã đó cho ra MỘT dòng cho MỖI sản phẩm dùng nó — mã CPT0075 dùng ở 275 sản phẩm thì một lần mua thành 275 dòng.

Ở đây dựng cặp đó thành MỘT truy vấn con để nối với sổ giá trong SQL (lọc / xếp / phân trang tại máy chủ, không kéo về Python):
`pairs(hh_code, hh_name, code, role)`.

Số gộp (thẻ tóm tắt, ô chọn nhà cung cấp) KHÔNG nối 55 nghìn dòng đã nhân: mỗi dòng sổ giá nhân với số cặp của mã (`pair_counts`:
`n` = số cặp, `m` = số cặp khớp chữ tìm) rồi cộng có trọng số — cùng kết quả, chỉ đọc ~11 nghìn dòng sổ giá.
"""
from sqlalchemy import Subquery, case, func, literal, or_, select, union_all

from app.core.packaging_price_codes import PACKAGING_ROLE_LABELS, PackagingRole
from app.modules.packaging_cost.cost_service import fold_text
from app.modules.packaging_cost.impact_service import PART_COLUMNS
from app.modules.packaging_cost.model import PackagingBom

_ROLES = list(PackagingRole)          # cùng thứ tự với PART_COLUMNS


def build_bom_pairs(hh_codes: list[str]) -> Subquery:
    """Truy vấn con `(hh_code, hh_name, code, role)`: mỗi (sản phẩm, mã thành phần) đúng một dòng, `role` = mã `PackagingRole`
    nhỏ nhất mà mã đó đóng trong sản phẩm. `hh_codes` rỗng = mọi sản phẩm có định mức."""
    parts = []
    for column, role in zip(PART_COLUMNS, _ROLES):
        code = getattr(PackagingBom, column)
        part = select(PackagingBom.hh_code.label("hh_code"), PackagingBom.hh_name.label("hh_name"), code.label("code"),
                      literal(int(role)).label("role")).where(code != "")
        parts.append(part.where(PackagingBom.hh_code.in_(hh_codes)) if hh_codes else part)
    merged = union_all(*parts).subquery()
    return (select(merged.c.hh_code, merged.c.hh_name, merged.c.code, func.min(merged.c.role).label("role"))
            .group_by(merged.c.hh_code, merged.c.hh_name, merged.c.code).subquery())


def count_bom_products(hh_codes: list[str]):
    """Truy vấn con vô hướng: số sản phẩm có định mức trong phạm vi chọn (thẻ "Số sản phẩm" của bản mẫu)."""
    query = select(func.count(func.distinct(PackagingBom.hh_code)))
    return (query.where(PackagingBom.hh_code.in_(hh_codes)) if hh_codes else query).scalar_subquery()


def matching_roles(needle: str) -> list[int]:
    """Mã vai trò có nhãn chứa `needle` (không phân biệt dấu / hoa thường) — ô tìm chữ khớp cả cột "Thành phần"."""
    folded = fold_text(needle)
    return [int(role) for role, label in PACKAGING_ROLE_LABELS.items() if folded and folded in fold_text(label)]


def pair_text_conds(source, needle: str) -> list:
    """Điều kiện tìm chữ ở CẤP CẶP: mã / tên sản phẩm và tên thành phần (Chai, Nắp...). `source` có cột hh_code, hh_name, role."""
    conds = [source.c.hh_code.contains(needle, autoescape=True), source.c.hh_name.contains(needle, autoescape=True)]
    if roles := matching_roles(needle):
        conds.append(source.c.role.in_(roles))
    return conds


def build_pair_counts(pairs: Subquery, needle: str = "") -> Subquery:
    """Truy vấn con `(code, n, m)`: mỗi mã thành phần một dòng, `n` = số cặp (sản phẩm, vai trò) dùng mã đó, `m` = số cặp khớp
    chữ tìm `needle` (không có chữ tìm thì `m` = `n`)."""
    matched = (func.sum(case((or_(*pair_text_conds(pairs, needle)), 1), else_=0)) if needle
               else func.count())
    return select(pairs.c.code, func.count().label("n"), matched.label("m")).group_by(pairs.c.code).subquery()
