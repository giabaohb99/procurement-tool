"""Đọc DANH SÁCH BIẾN TÙY CHỈNH từ DB và đổi thành thứ bộ máy mẫu cần (duoc-CR-630).

Dùng chung cho: API quản lý biến, kiểm mẫu lúc tải/thay/soạn, giá trị theo hợp đồng, sinh tệp.
Biến HỆ THỐNG không đi qua đây — hợp lệ theo MÃ NGUỒN (`placeholder_catalog.KNOWN_KEYS`).
Không có cache phía server: mỗi lần gọi đọc DB (bảng ≤ 100 dòng tùy chỉnh).
"""
from collections.abc import Iterable

from sqlalchemy import bindparam, func
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractVariableSource as Src, LaborContractVariableType as T
from app.core.vn_number_words import read_amount_vi

from .model import LaborContract
from .placeholder_catalog import KNOWN_KEYS, sample_context
from .template_model import LaborContractTemplate
from .variable_model import LaborContractVariable
from .variable_rules import format_value, money_word_key


def custom_rows(db: Session, active_only: bool = False) -> list[LaborContractVariable]:
    q = db.query(LaborContractVariable).filter(LaborContractVariable.source == int(Src.CUSTOM))
    if active_only:
        q = q.filter(LaborContractVariable.is_active.is_(True))
    return q.order_by(LaborContractVariable.sort_order, LaborContractVariable.code).all()


def _is_money(row: LaborContractVariable) -> bool:
    return int(row.value_type) == int(T.MONEY)


def allowed_template_keys(db: Session, keep: Iterable[str] = ()) -> tuple[frozenset[str], frozenset[str]]:
    """(`allowed`, `inactive`) cho `docx_engine.inspect_template`.

    `allowed` = biến hệ thống ∪ biến tùy chỉnh ĐANG DÙNG ∪ `<mã>_bang_chu` của biến tiền đang dùng
    ∪ biến ngừng dùng mà `keep` (tập biến mẫu CŨ đã chứa) còn giữ. `inactive` = biến ngừng dùng
    ngoài `keep` — chỉ để báo câu riêng «đã ngừng dùng» thay vì «ngoài danh mục»."""
    keep_set = set(keep)
    allowed = set(KNOWN_KEYS)
    inactive: set[str] = set()
    for row in custom_rows(db):
        keys = {row.code} | ({money_word_key(row.code)} if _is_money(row) else set())
        if row.is_active:
            allowed |= keys
        else:
            kept = keys & keep_set
            allowed |= kept
            inactive |= keys - kept
    return frozenset(allowed), frozenset(inactive)


def sample_context_for(rows: Iterable[LaborContractVariable]) -> dict[str, str]:
    """Dữ liệu mẫu để render thử lúc tải mẫu: biến hệ thống ∪ biến tùy chỉnh (ví dụ hoặc nhãn)."""
    ctx = sample_context()
    for row in rows:
        ctx[row.code] = row.example or row.label
        if _is_money(row):
            ctx[money_word_key(row.code)] = row.example or row.label
    return ctx


def custom_context(rows: Iterable[LaborContractVariable], values: dict | None) -> dict[str, str]:
    """Ngữ cảnh của MỌI biến tùy chỉnh (kể cả ngừng dùng — mẫu cũ còn chứa): giá trị của hợp đồng,
    đã định dạng theo kiểu; chưa có → «». Mặc định KHÔNG áp ở đây (đã SAO vào hợp đồng lúc lập)."""
    values = values or {}
    ctx: dict[str, str] = {}
    for row in rows:
        stored = str(values.get(row.code) or "")
        ctx[row.code] = format_value(row.value_type, stored)
        if _is_money(row):
            ctx[money_word_key(row.code)] = read_amount_vi(int(stored)) if stored.isdigit() else ""
    return ctx


def missing_required(rows: Iterable[LaborContractVariable], values: dict | None,
                     template_placeholders: Iterable[str] | None = None) -> list[str]:
    """NHÃN các biến BẮT BUỘC (đang dùng) mà hợp đồng chưa có giá trị.

    `template_placeholders` có → chỉ xét biến mà mẫu thật sự dùng (mã hoặc `_bang_chu` của nó);
    `None` (chưa biết mẫu) → xét mọi biến bắt buộc đang dùng."""
    values = values or {}
    used = None if template_placeholders is None else set(template_placeholders)
    out = []
    for row in rows:
        if not (row.is_active and row.is_required) or values.get(row.code):
            continue
        if used is None or row.code in used or (_is_money(row) and money_word_key(row.code) in used):
            out.append(row.label)
    return out


def template_usage(db: Session, code: str) -> list[tuple[int, str, int]]:
    """(id, tên, pháp nhân) các mẫu có chứa biến `code` (hoặc `<code>_bang_chu`) — mọi pháp nhân.

    Quét bằng Python trên cột JSON `placeholders` (bảng mẫu nhỏ; thao tác hiếm: sửa/xóa biến)."""
    keys = {code, money_word_key(code)}
    rows = db.query(LaborContractTemplate.id, LaborContractTemplate.name, LaborContractTemplate.company_id,
                    LaborContractTemplate.placeholders).order_by(LaborContractTemplate.id).all()
    return [(i, n, c) for i, n, c, ph in rows if keys & set(ph or [])]


def contract_value_count(db: Session, code: str) -> int:
    """Số hợp đồng (KỂ CẢ xóa mềm — dữ liệu vẫn còn) đang giữ giá trị của biến `code`.

    ⚠️ Dùng `json_extract` tường minh, KHÔNG `LaborContract.custom_values[code]`: trên SQLite
    SQLAlchemy biên dịch cái sau thành `JSON_QUOTE(JSON_EXTRACT(..))` nên khóa vắng ra chuỗi
    'null' chứ không ra NULL → đếm sai. `code` đã qua `check_code` nên đưa vào đường dẫn an toàn."""
    path = bindparam("path", f'$."{code}"')
    return (db.query(func.count(LaborContract.id))
            .filter(func.json_extract(LaborContract.custom_values, path).isnot(None)).scalar() or 0)
