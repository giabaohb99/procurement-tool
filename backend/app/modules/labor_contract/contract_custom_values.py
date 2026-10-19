"""Giá trị biến TÙY CHỈNH theo từng hợp đồng (duoc-CR-630): gộp + kiểm, và chốt «bắt buộc».

Lưu ở cột JSON `tab_labor_contract.custom_values` = `{mã biến: chuỗi CHUẨN của kiểu}`. Mọi hàm trả dict MỚI
(không sửa tại chỗ) — SQLAlchemy không theo dõi sửa tại chỗ cột JSON. Thông báo lỗi chỉ nêu MÃ / NHÃN biến,
không bao giờ nêu GIÁ TRỊ (có thể nhạy cảm như lương).
"""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import variable_registry as reg, variable_rules as rules


def merge_custom_values(db: Session, old: dict | None, incoming: dict | None, *,
                        fill_defaults: bool = False) -> dict[str, str]:
    """Gộp giá trị gửi lên vào giá trị cũ.

    - Khóa không gửi → giữ nguyên (kể cả biến đã ngừng dùng). Gửi rỗng / null → XÓA khóa.
    - Mã không phải biến tùy chỉnh (lạ hoặc biến hệ thống) → 422.
    - Biến ngừng dùng: chỉ nhận giá trị y như đang lưu (chặn ghi MỚI).
    - `fill_defaults` (lúc LẬP hợp đồng): biến đang dùng mà không được gửi thì SAO giá trị mặc định vào hợp
      đồng — sau đó đổi mặc định không làm đổi hợp đồng đã lập.
    """
    result = {k: str(v) for k, v in (old or {}).items()}
    rows = {r.code: r for r in reg.custom_rows(db)}
    sent = incoming or {}
    bad = sorted(c for c in sent if c not in rows)
    if bad:
        raise HTTPException(422, "Biến không tồn tại hoặc không nhập tay được: " + ", ".join(bad))
    for code, raw in sent.items():
        row = rows[code]
        try:
            value = rules.normalize_value(row.value_type, raw)
        except ValueError as exc:
            raise HTTPException(422, f"Biến «{row.label}»: {exc}") from None
        if not row.is_active:
            if value != result.get(code, ""):
                raise HTTPException(422, f"Biến «{row.label}» đã ngừng dùng — không nhập giá trị mới được")
            continue
        if value:
            result[code] = value
        else:
            result.pop(code, None)
    if fill_defaults:
        for code, row in rows.items():
            if row.is_active and code not in sent and row.default_value:
                result[code] = row.default_value
    if len(json.dumps(result, ensure_ascii=False)) > rules.MAX_CUSTOM_VALUES_CHARS:
        raise HTTPException(422, f"Tổng giá trị các biến bổ sung tối đa {rules.MAX_CUSTOM_VALUES_CHARS} ký tự")
    return result


def ensure_required_filled(db: Session, values: dict | None, template_placeholders, action: str) -> None:
    """Biến BẮT BUỘC (đang dùng) còn trống → 422 nêu NHÃN. `template_placeholders=None` = chưa biết mẫu."""
    missing = reg.missing_required(reg.custom_rows(db), values, template_placeholders)
    if missing:
        raise HTTPException(422, f"Hợp đồng còn thiếu: {', '.join(missing)} — mở «Sửa hợp đồng» để nhập "
                                 f"trước khi {action}")


def placeholders_for_signing(db: Session, row) -> list[str]:
    """Biến mà hợp đồng này SẼ dùng khi ký — để chốt «bắt buộc» ở bước chuyển sang Đã ký.

    Hợp đồng đã sinh tệp (còn `template_id`) → biến của đúng mẫu đó. Chưa có mẫu (chưa sinh, sinh xong bị
    sửa nên `template_id` về 0, hoặc ký bằng bản scan) → hợp các biến của MẪU ĐANG DÙNG của CHÍNH pháp
    nhân hợp đồng, ưu tiên cùng loại hợp đồng; không mẫu nào cùng loại thì lấy mọi loại của pháp nhân.
    Không có mẫu nào → [] (không biết biến nào được dùng nên không ép biến nào; không lấy biến của pháp
    nhân khác)."""
    from .template_model import LaborContractTemplate as T

    if row.template_id:
        tpl = db.get(T, row.template_id)
        if tpl is not None:
            return list(tpl.placeholders or [])
    base = db.query(T.placeholders, T.contract_type).filter(T.company_id == row.company_id, T.is_active.is_(True)).all()
    same = [ph for ph, ctype in base if int(ctype) == int(row.contract_type)]
    chosen = same or [ph for ph, _ in base]
    return sorted({k for ph in chosen for k in (ph or [])})
