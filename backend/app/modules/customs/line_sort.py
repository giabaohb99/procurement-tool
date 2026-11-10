"""Sắp xếp bảng dòng hàng hải quan theo cột (duoc-CR-744) — màn Giá thị trường và tệp Excel "Xuất ngay".

Mỗi khóa là tên trường trong dòng trả về của `service.serialize_lines` (cũng là `key` cột bên giao diện)
và xếp theo ĐÚNG giá trị ô hiển thị:

  · Tên / mã số thuế doanh nghiệp, tên đối tác nằm ở bảng `tab_customs_party` -> nối ngoài theo id (id 0 =
    chưa gắn = trống). Chỉ nối khi thật sự xếp theo các cột đó, trang mặc định không đổi gì.
  · Phương tiện vận chuyển và Phân loại hiển thị bằng NHÃN chữ nên xếp theo nhãn, không theo mã số.
  · Hai cột giá VND: giá của tệp nạp nếu có, không thì tính từ giá hiệu lực x tỷ giá (đúng
    `service.compute_vnd_prices`, làm tròn tới đồng) — nên xếp được cả khi tệp không có cột.

Khóa phụ khi nhiều dòng bằng nhau là id giảm dần (luật chung `core/sort_order.py`).

Thứ tự mặc định (không `sort_by`) giữ nguyên: ngày đăng ký giảm dần để MySQL đi ngược chỉ mục
`ix_customs_line_date`. Có `sort_by` thì phải quét hết tập đã lọc rồi mới lấy trang (không chỉ mục nào phủ
được cột bất kỳ); chấp nhận được vì bộ lọc thường đã thu hẹp tập, còn xếp theo cột là thao tác chủ động.
"""
from sqlalchemy import and_, case, func
from sqlalchemy.orm import aliased

from .constants import FLAT_IMPORT_TAX_RATE, PRODUCT_KIND_LABELS, TRANSPORT_LABELS
from .list_sort import SortExpression, SortKey, build_order, text_col
from .model import CustomsLine, CustomsParty

L = CustomsLine

#  Cột thật của `tab_customs_line` hiển thị đúng giá trị lưu.
_PLAIN_TEXT = ("office_code", "hs_code", "product_name", "currency", "unit_code", "origin_country",
               "contract_no", "incoterm", "import_country", "active_ingredient", "formulation")
_PLAIN_VALUE = ("id", "reg_date", "contract_date", "line_no", "price_usd", "price_nt", "adj_price_usd",
                "adj_price_nt", "fx_rate", "usd_rate", "quantity", "rate_import", "rate_excise", "rate_vat",
                "rate_safeguard", "tax_import", "tax_excise", "tax_vat", "tax_environment", "tax_safeguard")
#  Cột hiển thị lấy từ bảng đối tượng — cần nối.
PARTY_KEYS = frozenset({"importer_tax_code", "importer_name", "partner_name"})

#  Toàn bộ khóa xếp được; bài kiểm canh danh sách này khớp 38 cột bên giao diện.
LINE_SORT_KEYS = frozenset(
    {*_PLAIN_TEXT, *_PLAIN_VALUE, *PARTY_KEYS, "transport_mode", "product_kind", "price_vnd_flat",
     "price_vnd_line_tax"})


def _label_case(column, labels: dict) -> SortKey:
    """Mã số -> nhãn chữ đang hiển thị; mã không có nhãn (hay 0 = chưa gắn) ra trống."""
    mapping = {int(code): label for code, label in labels.items() if label}
    return text_col(case(mapping, value=column, else_=None))


def _vnd_expressions() -> tuple[SortExpression, SortExpression]:
    """Hai cột giá VND: của tệp nạp nếu có, không thì tính như `service.compute_vnd_prices`."""
    price = func.coalesce(L.adj_price_usd, L.price_usd)
    rate = case((L.usd_rate.is_not(None), L.usd_rate),
                (func.upper(L.currency) == "USD", L.fx_rate), else_=None)
    usable = and_(price.is_not(None), rate.is_not(None), rate > 0)
    base = price * rate
    flat = case((usable, func.round(base * (1 + FLAT_IMPORT_TAX_RATE), 0)), else_=None)
    line_tax = case((and_(usable, L.rate_import.is_not(None)),
                     func.round(base * (1 + L.rate_import / 100), 0)), else_=None)
    return func.coalesce(L.price_vnd_flat, flat), func.coalesce(L.price_vnd_line_tax, line_tax)


def build_line_sort_map(importer: CustomsParty | None = None, partner: CustomsParty | None = None
                        ) -> dict[str, SortExpression]:
    """Khóa cột -> biểu thức SQL. `importer`/`partner` là bí danh bảng đối tượng đã nối (None = khóa đó vắng)."""
    sort_map: dict[str, SortExpression] = {key: text_col(getattr(L, key)) for key in _PLAIN_TEXT}
    sort_map.update({key: getattr(L, key) for key in _PLAIN_VALUE})
    sort_map["transport_mode"] = _label_case(L.transport_mode, TRANSPORT_LABELS)
    sort_map["product_kind"] = _label_case(L.product_kind, PRODUCT_KIND_LABELS)
    sort_map["price_vnd_flat"], sort_map["price_vnd_line_tax"] = _vnd_expressions()
    if importer is not None:
        sort_map["importer_tax_code"] = text_col(importer.tax_code)
        sort_map["importer_name"] = text_col(importer.name)
    if partner is not None:
        sort_map["partner_name"] = text_col(partner.name)
    return sort_map


def apply_line_sort(query, sort_by: str | None, sort_dir: str | None):
    """Áp thứ tự theo cột lên truy vấn dòng hàng; khóa rỗng / lạ -> thứ tự mặc định (ngày giảm dần)."""
    key = (sort_by or "").strip()
    if key not in LINE_SORT_KEYS:
        return query.order_by(L.reg_date.desc(), L.id.desc())
    importer = partner = None
    if key in ("importer_tax_code", "importer_name"):
        importer = aliased(CustomsParty, name="sort_importer")
        query = query.outerjoin(importer, importer.id == L.importer_id)
    elif key == "partner_name":
        partner = aliased(CustomsParty, name="sort_partner")
        query = query.outerjoin(partner, partner.id == L.partner_id)
    return query.order_by(*build_order(key, sort_dir, build_line_sort_map(importer, partner), L.id))

