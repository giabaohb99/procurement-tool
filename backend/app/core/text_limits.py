"""Lớp bảo vệ độ dài ô chữ + câu báo lỗi nói thành lời — bao-CR-538 (phần 2, 3, 4).

Sự cố D30D24DF (30/09/2026): lưu phiếu khảo sát, ô «Ghi chú NSPT» dài hơn cột, schema không
chặn nên xuống tới MySQL mới bị từ chối «Data too long for column 'nspt_note'» → người dùng
thấy «Hệ thống gặp lỗi không lường trước». Đại ca chốt: phải validate kỹ, KHÔNG để model trả
lỗi lên rồi SQL trả lên. Tệp này gom ba lớp:

  1. `describe_validation_errors` — biến danh sách lỗi Pydantic (tiếng Anh) thành MỘT câu
     tiếng Việt: «Ô "Mục đích" tối đa 355 ký tự (đang nhập 412)». Lỗi đầu tiên + «và n lỗi
     khác». `main.validation_exception_handler` dùng câu này làm `message`, `details` giữ y.
  2. `ensure_max_length` / `ensure_model_fits` — cho những đường ghi KHÔNG đi qua schema
     (Body `dict`, Form, gán thẳng trong service): kiểm trước khi gán, sai thì 422 cùng một
     kiểu câu.
  3. `describe_data_error` — LƯỚI CUỐI: lọt hết hai lớp trên mà MySQL vẫn báo 1406 thì đổi
     thành 422 «Ô X dài quá, tối đa n ký tự» (n tra từ model theo bảng/cột), không ra 500.
"""
import re
import typing
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

#  Nhãn hiển thị theo TÊN TRƯỜNG — dùng khi schema không khai `Field(title=...)` (gần như
#  toàn bộ schema hiện có). Không có trong bảng thì rơi về tên trường.
FIELD_LABELS: dict[str, str] = {
    "active_ingredient": "Hoạt chất", "allocation_target": "Đối tượng phân bổ",
    "assignee": "Người phụ trách", "bank_account": "Số tài khoản", "bank_account_name": "Tên chủ tài khoản",
    "bank_name": "Ngân hàng", "carrier_code": "Mã đơn vị vận chuyển", "carrier_name": "Đơn vị vận chuyển",
    "code": "Mã", "contact_date": "Ngày liên hệ", "contact_person": "Người liên hệ",
    "contact_phone": "Số điện thoại liên hệ", "currency": "Đồng tiền", "customs_decl_date": "Ngày tờ khai",
    "customs_decl_no": "Số tờ khai hải quan", "debt_policy": "Chính sách công nợ",
    "defect_return": "Chính sách đổi trả hàng lỗi", "delivery_place": "Nơi giao hàng",
    "delivery_policy": "Chính sách giao hàng", "delivery_time": "Thời gian giao hàng",
    "department": "Bộ phận", "department_requester": "Bộ phận yêu cầu", "description": "Mô tả",
    "dimension": "Quy cách / kích thước", "document_delivery_date": "Ngày giao chứng từ",
    "document_status": "Tình trạng chứng từ", "etd_date": "Ngày ETD", "expected_date": "Ngày dự kiến",
    "fg_code": "Mã HH (thành phẩm)", "fg_name": "Tên HH (thành phẩm)", "google_maps": "Google Maps",
    "group_desc": "Mô tả nhóm", "head_of_dept": "Trưởng bộ phận", "image_file": "Tệp hình ảnh",
    "internal_code": "Mã nội bộ", "internal_unit": "ĐVT nội bộ", "invoice_date": "Ngày hóa đơn",
    "invoice_deadline": "Hạn xuất hóa đơn", "invoice_name": "Tên trên hóa đơn", "invoice_no": "Số hóa đơn",
    "invoice_policy": "Chính sách hóa đơn", "issue_code": "Mã phát hành", "item_code": "Mã hàng",
    "item_group": "Phân loại", "item_name": "Tên hàng", "lab_result": "Kết quả kiểm nghiệm",
    "legal_type": "Loại hình pháp lý", "line_approve": "Duyệt dòng", "line_approve_note": "Ghi chú duyệt dòng",
    "line_status": "Tình trạng dòng", "main_content": "Nội dung chính", "misa_code": "Số hóa đơn (MISA)",
    "name": "Tên", "need_date": "Ngày cần hàng", "note": "Ghi chú", "nspt": "NSPT phụ trách",
    "nspt_note": "Ghi chú NSPT", "nspt_reason": "Lý do NSPT", "nstm_note": "Ghi chú NSTM",
    "nvkd_eval": "Đánh giá của NVKD", "order_date": "Ngày đặt hàng", "origin": "Xuất xứ",
    "pause_reason": "Lý do tạm ngưng / hủy", "payment_due_date": "Hạn thanh toán",
    "payment_method": "Hình thức thanh toán", "payment_terms": "Điều khoản thanh toán",
    "phone": "Số điện thoại", "po_code": "Mã đơn hàng", "pr_code": "Mã YCMH",
    "product_code": "Mã hàng", "product_name": "Tên hàng", "production_tech": "Công nghệ sản xuất",
    "production_time": "Thời gian sản xuất", "promised_date": "Ngày NCC hẹn giao", "purpose": "Mục đích",
    "qc_result": "Kết quả QC", "quote_file": "Tệp báo giá", "quote_file_url": "Đường dẫn tệp báo giá",
    "quote_filename": "Tên tệp báo giá", "quote_folder": "Thư mục báo giá", "quote_unit": "Đơn vị báo giá",
    "reason": "Lý do", "received_date": "Ngày tiếp nhận", "reg_address": "Địa chỉ đăng ký",
    "registered_on": "Ngày cấp", "expires_on": "Ngày hết hạn", "status": "Tình trạng",
    "trade_name": "Tên thương mại",
    "reliability": "Độ tin cậy", "reply_date": "Ngày phản hồi", "request_date": "Ngày yêu cầu",
    "requester": "Người yêu cầu", "requester_position": "Chức vụ người yêu cầu",
    "required_date": "Ngày yêu cầu có hàng", "requirement_detail": "Yêu cầu chi tiết",
    "result_date": "Ngày có kết quả", "result_due_date": "Hạn trả kết quả", "sample_date": "Ngày gửi mẫu",
    "ship_unit": "Đơn vị vận chuyển", "shipping_policy": "Chính sách vận chuyển",
    "snap_delivery_place": "Nơi giao hàng", "snap_delivery_time": "Thời gian giao hàng",
    "snap_internal_code": "Mã nội bộ", "snap_origin": "Xuất xứ", "snap_product_name": "Tên hàng",
    "snap_quote_unit": "Đơn vị báo giá", "snap_volume_range": "Khoảng sản lượng",
    "source_of_information": "Nguồn thông tin", "source_type": "Loại nguồn", "source_url": "Đường dẫn nguồn", "spec": "Xuất xứ / TSKT / chất liệu",
    "sr_code": "Mã YCBG", "suggested_supplier": "NCC đề xuất",
    "suggested_supplier_contact": "Liên hệ NCC đề xuất", "suggested_supplier_tax_code": "MST NCC đề xuất",
    "supplier_code": "Mã NCC", "supplier_name": "Tên NCC", "supplier_type": "Loại NCC",
    "supply_group": "Nhóm cung ứng", "survey_code": "Mã phiếu khảo sát",
    "system_product_code": "Mã sản phẩm hệ thống", "tax_code": "Mã số thuế", "unit": "ĐVT",
    "uom": "ĐVT", "volume_range": "Khoảng sản lượng", "warehouse": "Kho", "warehouse_address": "Địa chỉ kho",
    "warehouse_code": "Mã kho",
}

#  Nhóm mã lỗi Pydantic v2 → một kiểu câu.
_NUMBER_TYPES = {"int_parsing", "int_type", "int_from_float", "float_parsing", "float_type",
                 "decimal_parsing", "decimal_type", "finite_number", "bool_parsing", "bool_type"}
_DATE_TYPES = {"date_parsing", "date_type", "date_from_datetime_parsing", "date_from_datetime_inexact",
               "datetime_parsing", "datetime_type", "datetime_from_date_parsing", "time_parsing", "time_type"}
_BOUND_WORDS = {"greater_than": "lớn hơn", "greater_than_equal": "từ", "less_than": "nhỏ hơn",
                "less_than_equal": "không quá"}
_BOUND_KEYS = {"greater_than": "gt", "greater_than_equal": "ge", "less_than": "lt", "less_than_equal": "le"}


def label_of(field_name: str) -> str:
    """Nhãn hiển thị của một trường theo bảng chung; không có thì trả lại tên trường."""
    return FIELD_LABELS.get(field_name, field_name)


def too_long_message(label: str, limit: int, actual: int, row: int | None = None) -> str:
    """Câu chuẩn cho ô chữ quá dài — dùng chung cho schema, helper và lưới cuối."""
    return f'Ô "{label}"{_row_suffix(row)} tối đa {limit} ký tự (đang nhập {actual})'


def ensure_max_length(value: Any, limit: int, label: str) -> Any:
    """Chặn chuỗi dài quá `limit` TRƯỚC khi gán xuống cột `String(limit)` → 422.

    Dùng ở đường ghi không đi qua schema (Body `dict`, Form, service tự gán). Giá trị không
    phải chuỗi thì trả nguyên — kiểu sai là việc của chỗ gọi, hàm này chỉ canh độ dài."""
    if isinstance(value, str) and len(value) > limit:
        raise HTTPException(422, too_long_message(label, limit, len(value)))
    return value


def column_limit(model: type, column: str) -> int | None:
    """Độ dài `String(n)` của cột trên model ORM; cột không giới hạn (Text, số...) → None."""
    table = getattr(model, "__table__", None)
    if table is None or column not in table.c:
        return None
    return getattr(table.c[column].type, "length", None)


def ensure_model_fits(model: type, values: dict, labels: dict[str, str] | None = None) -> None:
    """Soi MỌI ô chữ trong `values` với độ dài cột `String(n)` của `model` → 422 ở ô đầu tiên
    vượt. Dùng khi service gán cả một dict vào bản ghi (vd `setattr` theo khóa)."""
    for key, value in (values or {}).items():
        limit = column_limit(model, key)
        if limit:
            ensure_max_length(value, limit, (labels or {}).get(key) or label_of(key))


# ── Phần 3: lỗi Pydantic → câu tiếng Việt ─────────────────────────────────

def _row_suffix(row: int | None) -> str:
    return f" ở dòng thứ {row}" if row else ""


def _unwrap_model(annotation: Any) -> type[BaseModel] | None:
    """Lấy lớp schema con nằm trong chú thích kiểu: `X`, `list[X]`, `X | None`, `Annotated[X, ...]`."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    for arg in typing.get_args(annotation):
        found = _unwrap_model(arg)
        if found is not None:
            return found
    return None


def _schema_title(models: list[type[BaseModel]], path: list) -> str | None:
    """Đi theo `loc` trong schema để lấy `Field(title=...)` của trường cuối. Không thấy → None."""
    for model in models:
        current: type[BaseModel] | None = model
        title = None
        steps = [p for p in path if isinstance(p, str)]
        #  Nhiều tham số body (embed) thì `loc` mở đầu bằng TÊN tham số, không phải tên trường.
        if steps and current is not None and steps[0] not in current.model_fields:
            steps = steps[1:]
        for step in steps:
            if current is None or step not in current.model_fields:
                current, title = None, None
                break
            info = current.model_fields[step]
            title = info.title
            current = _unwrap_model(info.annotation)
        if title:
            return title
    return None


def body_models_of(route: Any) -> list[type[BaseModel]]:
    """Các lớp schema nhận body của route FastAPI (rỗng khi không đọc được)."""
    dependant = getattr(route, "dependant", None)
    models = []
    for param in getattr(dependant, "body_params", None) or []:
        annotation = getattr(getattr(param, "field_info", None), "annotation", None) or getattr(param, "type_", None)
        model = _unwrap_model(annotation)
        if model is not None:
            models.append(model)
    return models


def _describe_one(err: dict, models: list[type[BaseModel]]) -> str:
    loc = list(err.get("loc") or [])
    path = loc[1:] if loc and loc[0] in ("body", "query", "path", "header", "cookie", "form") else loc
    kind = err.get("type") or ""
    ctx = err.get("ctx") or {}
    if kind == "json_invalid":
        return "Dữ liệu gửi lên không đúng định dạng JSON"

    names = [p for p in path if isinstance(p, str)]
    indexes = [p for p in path if isinstance(p, int)]
    row = indexes[-1] + 1 if indexes else None
    #  Validator tự viết thường đã có câu tiếng Việt — giữ câu đó, bỏ tiền tố của Pydantic.
    custom = str(err.get("msg") or "").removeprefix("Value error, ").strip() if kind == "value_error" else ""
    if not names:
        #  Lỗi cấp cả phiếu (`model_validator`) không gắn ô nào — câu của validator là đủ.
        return custom or f"Dữ liệu gửi lên không hợp lệ{_row_suffix(row)}"
    label = _schema_title(models, path) or label_of(names[-1])
    where = f'Ô "{label}"{_row_suffix(row)}'

    if kind == "string_too_long":
        given = err.get("input")
        actual = len(given) if isinstance(given, str) else None
        limit = ctx.get("max_length")
        return (too_long_message(label, limit, actual, row) if actual is not None
                else f"{where} tối đa {limit} ký tự")
    if kind == "string_too_short":
        return f"{where} cần ít nhất {ctx.get('min_length')} ký tự"
    if kind == "missing":
        return f"{where} bắt buộc nhập"
    if kind in _NUMBER_TYPES:
        return f"{where} phải là số" if not kind.startswith("bool") else f"{where} phải là Có/Không"
    if kind in _DATE_TYPES:
        return f"{where} không phải ngày hợp lệ (định dạng NĂM-THÁNG-NGÀY)"
    if kind in _BOUND_WORDS:
        return f"{where} phải {_BOUND_WORDS[kind]} {ctx.get(_BOUND_KEYS[kind])}"
    if kind in ("string_type", "str_type"):
        return f"{where} phải là chữ"
    if kind in ("list_type", "dict_type", "model_type", "model_attributes_type"):
        return f"{where} sai cấu trúc dữ liệu"
    if kind == "value_error":
        return f"{where}: {custom}" if custom else f"{where} không hợp lệ"
    return f"{where} không hợp lệ"


def describe_validation_errors(errors: list[dict], models: list[type[BaseModel]] | None = None) -> str:
    """MỘT câu tiếng Việt cho cả danh sách lỗi: lỗi đầu + «và n lỗi khác»."""
    if not errors:
        return "Dữ liệu không hợp lệ"
    first = _describe_one(errors[0], models or [])
    rest = len(errors) - 1
    return f"{first} và {rest} lỗi khác" if rest > 0 else first


# ── Phần 4: lưới cuối cho lỗi MySQL ───────────────────────────────────────

_TOO_LONG_RE = re.compile(r"Data too long for column '([^']+)'")
_COLUMN_RE = re.compile(r"for column '([^']+)'")
_TABLE_RE = re.compile(r"^\s*(?:INSERT\s+(?:IGNORE\s+)?INTO|UPDATE)\s+`?(\w+)`?", re.IGNORECASE)


def _limit_from_metadata(table: str | None, column: str) -> int | None:
    """Tra độ dài cột theo bảng; không rõ bảng thì lấy được khi MỌI bảng có cột đó cùng một độ dài."""
    from app.core.base_model import Base
    tables = Base.metadata.tables
    if table and table in tables and column in tables[table].c:
        return getattr(tables[table].c[column].type, "length", None)
    lengths = {getattr(t.c[column].type, "length", None) for t in tables.values() if column in t.c}
    lengths.discard(None)
    return lengths.pop() if len(lengths) == 1 else None


def describe_data_error(exc: Exception) -> tuple[str, str]:
    """(câu báo lỗi, tên cột) cho một `sqlalchemy.exc.DataError`. Tên cột rỗng khi không đọc được."""
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", None) or ()
    code = args[0] if args and isinstance(args[0], int) else None
    text = str(args[1]) if len(args) > 1 else str(orig or exc)
    statement = getattr(exc, "statement", "") or ""
    table_match = _TABLE_RE.match(statement)
    table = table_match.group(1) if table_match else None

    too_long = _TOO_LONG_RE.search(text)
    if code == 1406 or too_long:
        column = too_long.group(1) if too_long else ""
        label = label_of(column) if column else "chữ"
        limit = _limit_from_metadata(table, column) if column else None
        tail = f", tối đa {limit} ký tự" if limit else ""
        return f'Ô "{label}" dài quá{tail}', column
    column_match = _COLUMN_RE.search(text)
    column = column_match.group(1) if column_match else ""
    if column:
        return f'Ô "{label_of(column)}" có giá trị không hợp lệ', column
    return "Dữ liệu không hợp lệ — có ô vượt giới hạn cho phép", ""
