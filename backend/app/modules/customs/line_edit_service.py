"""Sửa / xóa tay MỘT dòng hàng trên màn «Giá thị trường» — bao-CR-608 (đại ca 07/10/2026).

Gác: sửa = `customs_price.write`, xóa = `customs_price.delete` (route ở `controller.py`).
`customs_price` là entity PUBLIC (`SCOPE_FIELDS`) nên không có phạm vi dữ liệu để kiểm thêm.

Mỗi lần sửa / xóa:
  1. chụp ĐỦ dòng vào `tab_customs_line_change` (nguồn MANUAL, `batch_id` = 0) — dấu vết «trước
     khi sửa là gì», cùng bảng với bản chụp của lô nạp (`line_change.py`);
  2. ghi; doanh nghiệp nhập khẩu đi qua mã số thuế + tên, đối tác qua tên → tra hoặc tạo
     `CustomsParty` đúng như bộ nạp (`importer.upsert_parties`);
  3. tính lại `row_hash` (chống trùng bao-CR-541 phải thấy nội dung MỚI);
  4. `record(...)` nhật ký thao tác với entity `customs_price`.

Hoạt chất / hàm lượng nhập tay → cờ `*_from_file` = 1: nghĩa của cờ là «giá trị do NGƯỜI nhập»
(tệp hoặc tay), `retag_all` không ghi đè. Gửi chuỗi rỗng = trả về cho hệ thống suy ra từ tên hàng.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from . import dedupe, line_change
from .constants import COLUMNS, OPTIONAL_LABELS, CustomsLineChangeAction, CustomsLineChangeSource, PartyType
from .importer import upsert_parties
from .ingredient import load_kind_tagger, load_tagger
from .model import CustomsLine, CustomsParty
from .reader import clean_party_name, hash_name
from .schema import CustomsLineUpdate

ENTITY = "customs_price"
#  Ô mã: viết hoa cho khớp ô lọc (bộ lọc so `== upper()`), giống dữ liệu nạp từ tệp.
_UPPER_KEYS = frozenset({"currency", "unit_code", "origin_country", "incoterm", "import_country", "formulation"})
_PARTY_INPUT_KEYS = frozenset({"importer_tax_code", "importer_name", "partner_name"})
_DERIVED_KEYS = frozenset({"active_ingredient", "formulation"})
_LABELS = dict(COLUMNS) | OPTIONAL_LABELS


def _get_line(db: Session, line_id: int) -> CustomsLine:
    line = db.get(CustomsLine, line_id)
    if not line:
        raise HTTPException(404, "Không tìm thấy dòng hàng — có thể vừa bị xóa hoặc lô nạp chứa nó vừa được hoàn tác")
    return line


def _party(db: Session, party_id: int) -> CustomsParty | None:
    return db.get(CustomsParty, party_id) if party_id else None


def _apply_parties(db: Session, line: CustomsLine, data: dict) -> None:
    if "importer_tax_code" in data or "importer_name" in data:
        current = _party(db, line.importer_id)
        tax = (data.get("importer_tax_code", current.tax_code if current else "") or "").strip().lstrip("'").strip()
        name = clean_party_name(data.get("importer_name", current.name if current else "") or "")
        if not tax and name:
            raise HTTPException(400, "Doanh nghiệp nhập khẩu cần có mã số thuế — hệ thống nhận diện doanh nghiệp theo mã số thuế")
        line.importer_id = upsert_parties(db, PartyType.DOMESTIC, [
            {"importer_tax_code": tax, "importer_name": name, "partner_name": ""}])[tax] if tax else 0
    if "partner_name" in data:
        name = clean_party_name(data["partner_name"] or "")
        line.partner_id = upsert_parties(db, PartyType.FOREIGN, [
            {"importer_tax_code": "", "importer_name": "", "partner_name": name}])[hash_name(name)] if name else 0


def _party_names(db: Session, line: CustomsLine) -> dict:
    imp, par = _party(db, line.importer_id), _party(db, line.partner_id)
    return {"importer_tax_code": imp.tax_code if imp else "", "importer_name": imp.name if imp else "",
            "partner_name": par.name if par else ""}


def update_line(db: Session, line_id: int, body: CustomsLineUpdate, user_id: int) -> CustomsLine:
    """Sửa một dòng (chỉ trường có gửi). → dòng sau khi sửa (đã commit)."""
    line = _get_line(db, line_id)
    data = body.model_dump(exclude_unset=True)
    if not data:
        return line
    before = line_change.snapshot_of(line) | _party_names(db, line)
    line_change.record_snapshots(db, [line], CustomsLineChangeAction.UPDATE, CustomsLineChangeSource.MANUAL,
                                 0, user_id)
    _apply_parties(db, line, data)
    for key, value in data.items():
        if key in _PARTY_INPUT_KEYS or key in _DERIVED_KEYS:
            continue
        if isinstance(value, str):
            value = value.strip().upper() if key in _UPPER_KEYS else value.strip()
        setattr(line, key, value)

    #  Hoạt chất / hàm lượng: chữ = do người nhập (cờ 1); rỗng = để hệ thống suy ra (cờ 0).
    for key in ("active_ingredient", "formulation"):
        if key in data:
            value = (data[key] or "").strip()
            value = value.upper() if key in _UPPER_KEYS else value
            setattr(line, key, value)
            setattr(line, f"{key}_from_file", bool(value))
    #  Suy lại khi tên hàng đổi (kèm nhãn Thành phẩm / Nguyên liệu) hoặc người dùng xóa trắng ô suy ra.
    if "product_name" in data or any(key in data and not getattr(line, f"{key}_from_file") for key in _DERIVED_KEYS):
        active, form = load_tagger(db).tag(line.product_name)
        line.product_kind = load_kind_tagger(db).tag(line.product_name)
        if not line.active_ingredient_from_file:
            line.active_ingredient = active
        if not line.formulation_from_file:
            line.formulation = form

    db.flush()
    line.row_hash = ""
    line.row_hash = dedupe.stored_hashes(db, [line])[line.id]
    after = line_change.snapshot_of(line) | _party_names(db, line)
    changed = [_LABELS.get(k, k) for k in _LABELS if before.get(k) != after.get(k)]
    record(db, user_id, ENTITY, line.id, "update",
           f"Sửa tay dòng giá thị trường ID {line.id}" + (f" — đổi: {', '.join(changed)}" if changed else ""))
    db.refresh(line)
    return line


def delete_line(db: Session, line_id: int, user_id: int) -> None:
    """Xóa một dòng — chụp trước, rồi xóa, rồi ghi nhật ký thao tác."""
    line = _get_line(db, line_id)
    name = line.product_name or ""
    line_change.record_snapshots(db, [line], CustomsLineChangeAction.DELETE, CustomsLineChangeSource.MANUAL,
                                 0, user_id)
    db.delete(line)
    db.flush()
    record(db, user_id, ENTITY, line_id, "delete", f"Xóa tay dòng giá thị trường ID {line_id} — {name[:120]}")
