"""Import CHỨNG TỪ nhiều dòng: 1 phiếu = 1 header + N dòng, gộp theo MÃ PHIẾU.

Dùng cho Yêu cầu báo giá (survey_request) và Yêu cầu mua hàng (purchase_request)
— hai loại chưa có importer. (Khảo sát và Đơn mua hàng đã có importer Misa riêng
ở `survey_import`/`po_import`.)

Cùng khung batch: dry-run rollback + apply commit + snapshot `ImportChange` để revert.
**v1 chỉ TẠO MỚI** — mã phiếu đã tồn tại thì bỏ qua cả phiếu + cảnh báo (không sửa
đè phiếu cũ, vì hoà dòng của chứng từ đã có là rủi ro cao).

Cấu trúc file mẫu: MỘT sheet, mỗi dòng là một DÒNG HÀNG; cột **Mã phiếu** gộp các
dòng vào cùng một phiếu, các cột ĐẦU PHIẾU lấy từ dòng ĐẦU TIÊN của mỗi mã.
"""
import json
from collections import OrderedDict
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.seal_request.model import SEAL_STATUS_LABELS, SealRequest
from app.modules.survey.model import Survey, SurveySupplierLine
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User
from app.modules.vehicle_booking.model import (BOOKING_STATUS_LABELS,
                                               DRIVER_STATUS_LABELS,
                                               REQUEST_TYPE_LABELS, TYPE_CAR,
                                               TYPE_DELIVERY, Driver, Vehicle,
                                               VehicleBooking)

from . import catalog_import
from .catalog_import import _norm, _s, _to_bool, _to_float, _to_int
from .model import ImportModule, LogLevel

HEADER_ROW = 1
DATA_START = 2

_REF_MODEL = {"company": Company, "department": Department, "employee": Employee}
_REF_NAME = {"company": "name", "department": "name", "employee": "full_name"}


def _df(header, attr, kind="str", required=False, ref=None, name_attr=None,
        default=None, labels=None, aliases=None):
    """Field khai báo.

    - `name_attr`: khi ref resolve, ghi thêm TÊN vào cột này (bản chụp).
    - `labels`: bộ mã→nhãn (dùng cho kind 'coded' — nhận cả SỐ lẫn NHÃN tiếng Việt).
    - `aliases`: tiêu đề thay thế để khớp file xuất của hệ thống cũ (vd 'Thời gian
      lấy hàng' ≡ 'Thời gian đi' cho phiếu giao hàng)."""
    return {"header": header, "attr": attr, "kind": kind, "required": required,
            "ref": ref, "name_attr": name_attr, "default": default,
            "labels": labels or {}, "aliases": aliases or []}


def _to_date_str(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    return _s(v)[:10]


def _cap_strings(model, data: dict) -> None:
    """Cắt chuỗi vượt độ dài cột (String(n)) trước khi ghi — dữ liệu tự do của hệ cũ
    (vd 'SĐT người tham gia' = '0939… - Ngọc Trâm' dài hơn 20) không được làm sập cả lô."""
    cols = model.__table__.columns
    for k, v in list(data.items()):
        if isinstance(v, str) and k in cols:
            length = getattr(cols[k].type, "length", None)
            if length and len(v) > length:
                data[k] = v[:length]


#  Định dạng ngày-giờ trong bản xuất hệ thống cũ ("06:30:00 3/3/2026") + ISO.
_DT_FORMATS = ("%H:%M:%S %d/%m/%Y", "%H:%M %d/%m/%Y", "%d/%m/%Y %H:%M:%S",
               "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S",
               "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def _parse_dt(v):
    """Chuỗi ngày-giờ nhiều định dạng (kể cả kiểu hệ cũ) -> datetime, hỏng -> None."""
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    s = _s(v)
    if not s:
        return None
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _to_isodt(v) -> str:
    """Ngày-giờ -> chuỗi ISO (cho các cột thời gian kiểu String của phiếu)."""
    dt = _parse_dt(v)
    return dt.isoformat(timespec="seconds") if dt else ""


def _to_coded(v, labels: dict, default) -> int:
    """Ô nhận SỐ (mã) HOẶC NHÃN tiếng Việt -> mã số. Không khớp -> default."""
    s = _s(v)
    if not s:
        return default
    #  Số trực tiếp (kể cả '4.0' từ Excel) và đúng là một mã hợp lệ.
    n = _to_int(s, -999)
    if n in labels:
        return n
    norm = _norm(s)
    for code, label in labels.items():
        if _norm(label) == norm and label:
            return code
    return default


def _resolve_ref_obj(db: Session, ref: str, value):
    """Tìm bản ghi tham chiếu theo MÃ hoặc TÊN. Danh mục nền dùng chung bộ đối chiếu
    ở `catalog_import`; Xe/Tài xế/Người duyệt có khoá riêng."""
    v = _s(value)
    if not v:
        return None
    if ref in ("company", "department", "employee"):
        return catalog_import.resolve_ref_obj(db, ref, v)
    if ref == "vehicle":  # đối chiếu theo BIỂN SỐ (hoặc tên xe lưu ở license_plate)
        return db.query(Vehicle).filter(Vehicle.license_plate == v).first()
    if ref == "driver":  # theo SĐT trước, rồi tới TÊN
        return (db.query(Driver).filter(Driver.phone == v).first()
                or db.query(Driver).filter(Driver.name == v).first())
    return None


def _resolve_approver_id(db: Session, value) -> int:
    """«Người duyệt cấp 1» ghi bằng TÊN nhân sự -> id TÀI KHOẢN (khớp first_approver_id).
    Hai chặng: Nhân sự theo họ tên -> Tài khoản có employee_id đó."""
    emp = catalog_import.resolve_ref_obj(db, "employee", value)
    if not emp:
        return 0
    u = db.query(User).filter(User.employee_id == emp.id).first()
    return u.id if u else 0


def _create_attachment_placeholders(db, entity: str, entity_id: int, raw, doc_type: str,
                                    user_id: int) -> int:
    """Ghi nhận TỆP ĐÍNH KÈM từ import: bản xuất chỉ có TÊN tệp (không có nội dung),
    nên tạo dòng `tab_file` GIỮ CHỖ (file_key/url rỗng) + liên kết, để phiếu vẫn thấy
    tên tệp đã đính; tải nội dung thật thì upload lại sau. Nhiều tệp cách nhau ',' '|'
    ';' hoặc xuống dòng."""
    names = [n.strip() for n in _s(raw).replace("\n", ",").replace("|", ",").replace(";", ",").split(",")
             if n.strip()]
    made = 0
    for name in names:
        sf = StoredFile(filename=name[:255], file_key="", url="", content_type="", size=0,
                        created_by=user_id, updated_by=user_id)
        db.add(sf)
        db.flush()
        db.add(FileLink(file_id=sf.id, entity=entity, entity_id=entity_id, doc_type=doc_type,
                        created_by=user_id, updated_by=user_id))
        made += 1
    return made


# ── Suy diễn nhiều cột từ MỘT ô (đặt xe) ────────────────────────────────────
def _derive_vehicle_type(raw, target: dict) -> None:
    """«Loại yêu cầu» ('Đi công tác' / 'Giao hàng' / '… tự lái') -> request_type + is_self_drive."""
    low = _s(raw).lower()
    if not low:
        return
    target["request_type"] = TYPE_DELIVERY if "giao" in low else TYPE_CAR
    target["is_self_drive"] = ("tự lái" in low) or ("tu lai" in low)


def _derive_route(raw, target: dict) -> None:
    """«Lộ trình» 'A -> B -> C' -> điểm đi / điểm đến / điểm dừng (JSON)."""
    s = _s(raw)
    if not s:
        return
    parts = [p.strip() for p in s.replace("→", "->").split("->") if p.strip()]
    if not parts:
        return
    target["start_location"] = parts[0][:255]
    if len(parts) >= 2:
        target["end_location"] = parts[-1][:255]
    if len(parts) > 2:
        target["stops"] = json.dumps(parts[1:-1], ensure_ascii=False)


def _seal_set_companies(db: Session, header, header_data: dict) -> None:
    """Duyệt dấu: một phiếu gắn NHIỀU công ty qua bảng nối; import v1 nhận CÔNG TY
    CHÍNH (cột 'Công ty (mã/tên)') và ghi 1 dòng bảng nối cho đúng phạm vi Văn thư."""
    from app.modules.seal_request.service import set_companies
    cid = int(getattr(header, "company_id", 0) or 0)
    set_companies(db, header.id, [cid] if cid else [])


DOC_ADAPTERS: dict[int, dict] = {
    ImportModule.SURVEY_REQUEST: {
        "label": "Yêu cầu báo giá",
        "sheet": "YCBG",
        "header_model": SurveyRequest,
        "line_model": SurveyRequestLine,
        "line_fk": "survey_request_id",
        "code": _df("Mã phiếu *", "code", required=True),
        "header_fields": [
            _df("Công ty (mã)", "company_id", kind="ref", ref="company"),
            _df("Người yêu cầu", "requester"),
            _df("Phòng ban (mã)", "department_id", kind="ref", ref="department", name_attr="department"),
            _df("Mục đích", "purpose"),
            _df("Ngày yêu cầu", "request_date", kind="date"),
        ],
        "line_fields": [
            _df("Phân loại", "item_group"),
            _df("Yêu cầu kỹ thuật *", "requirement_detail", required=True),
            _df("Số lượng", "request_qty", kind="float"),
            _df("ĐVT", "uom"),
            _df("Giá đề xuất", "proposed_price", kind="float"),
        ],
    },
    ImportModule.PURCHASE_REQUEST: {
        "label": "Yêu cầu mua hàng",
        "sheet": "YCMH",
        "header_model": PurchaseRequest,
        "line_model": PurchaseRequestItem,
        "line_fk": "pr_id",
        "code": _df("Mã phiếu *", "code", required=True),
        "header_fields": [
            _df("Công ty (mã)", "company_id", kind="ref", ref="company"),
            _df("Người yêu cầu", "requester"),
            _df("Phòng ban (mã)", "department_id", kind="ref", ref="department", name_attr="department"),
            _df("Mục đích", "purpose"),
            _df("Ngày yêu cầu", "request_date", kind="date"),
            _df("Ngày cần hàng", "need_date", kind="date"),
        ],
        "line_fields": [
            _df("Mã sản phẩm", "product_code"),
            _df("Tên sản phẩm *", "product_name", required=True),
            _df("Phân loại", "item_group"),
            _df("Số lượng", "qty", kind="float"),
            _df("ĐVT", "unit"),
            _df("Giá đề xuất", "price", kind="float"),
        ],
    },
    # Khảo sát + Đơn mua hàng chuyển sang MẪU CHUẨN (CR-176), thay importer Misa.
    # Revert vẫn qua `_revert_survey`/`_revert_po` (dọn đủ 2 loại dòng / side-effect).
    ImportModule.SURVEY: {
        "label": "Khảo sát",
        "sheet": "Khao sat",
        "header_model": Survey,
        "line_model": SurveySupplierLine,
        "line_fk": "survey_id",
        "code": _df("Mã phiếu *", "code", required=True),
        "header_defaults": {"survey_type": "supplier"},
        "header_fields": [
            _df("Loại (supplier/product)", "survey_type", default="supplier"),
            _df("Phân loại", "item_group"),
            _df("Nội dung chính", "main_content"),
            _df("Yêu cầu kỹ thuật", "requirement_detail"),
            _df("SL dự kiến", "request_qty", kind="float"),
        ],
        "line_fields": [
            _df("Mã NCC", "supplier_code"),
            _df("Tên NCC *", "supplier_name", required=True),
            _df("MST", "tax_code"),
            _df("Người liên hệ", "contact_person"),
            _df("SĐT", "contact_phone"),
            _df("Chính sách hóa đơn", "invoice_policy"),
            _df("Chính sách công nợ", "debt_policy"),
        ],
    },
    ImportModule.PURCHASE_ORDER: {
        "label": "Đơn mua hàng",
        "sheet": "Don mua hang",
        "header_model": PurchaseOrder,
        "line_model": POItem,
        "line_fk": "po_id",
        "code": _df("Mã phiếu *", "code", required=True),
        "header_fields": [
            _df("Mã Misa", "misa_code"),
            _df("Mã YCMH", "pr_code"),
            _df("Công ty (mã)", "company_id", kind="ref", ref="company"),
            _df("Mã NCC", "supplier_code"),
            _df("Tên NCC", "supplier_name"),
            _df("Ngày đặt", "order_date", kind="date"),
        ],
        "line_fields": [
            _df("Mã sản phẩm", "product_code"),
            _df("Tên sản phẩm *", "product_name", required=True),
            _df("Phân loại", "item_group"),
            _df("ĐVT", "unit"),
            _df("SL đặt", "qty_order", kind="float"),
            _df("Đơn giá", "price", kind="float"),
        ],
    },
    # ── Chứng từ KHÔNG có dòng (header-only) — Đặt xe & Duyệt dấu ─────────────
    #  Cột đặt theo NHÃN của bản xuất hệ thống cũ (khớp 3 sheet trong file mẫu),
    #  Công ty/Phòng ban nhận MÃ hoặc TÊN, Trạng thái/Loại nhận MÃ hoặc NHÃN.
    #  Một adapter dùng chung cho cả ĐẶT XE CÔNG TÁC lẫn GIAO HÀNG (bộ cột hợp
    #  nhất; cột nào vắng trong file thì bỏ qua).
    ImportModule.VEHICLE_BOOKING: {
        "label": "Yêu cầu đặt xe",
        "sheet": "Yeu cau dat xe",
        "header_model": VehicleBooking,
        # Không có bảng dòng — mỗi mã phiếu = một phiếu, lấy đúng dòng đầu.
        "code": _df("Mã yêu cầu *", "code", required=True, aliases=["Mã phiếu", "STT phiếu"]),
        "header_fields": [
            _df("Tiêu đề", "purpose", aliases=["Mục đích"]),
            _df("Trạng thái chung", "status", kind="coded", labels=BOOKING_STATUS_LABELS,
                default=5, aliases=["Trạng thái", "Trạng thái (mã)"]),
            _df("Tên người tạo", "requester", aliases=["Người tạo"]),
            _df("Công ty", "company_id", kind="ref", ref="company",
                aliases=["Công ty (mã)", "Công ty (mã/tên)"]),
            _df("Phòng ban người tạo", "department_id", kind="ref", ref="department",
                aliases=["Phòng ban", "Phòng ban (mã)"]),
            _df("Thời gian đi", "start_time", kind="isodt", aliases=["Thời gian lấy hàng"]),
            _df("Thời gian về", "end_time", kind="isodt",
                aliases=["Thời gian giao (dự kiến)", "Thời gian giao"]),
            _df("Điểm đi", "start_location"),
            _df("Điểm đến", "end_location"),
            # --- Riêng ĐẶT XE CÔNG TÁC ---
            _df("Số hành khách", "passenger_count", kind="int", default=1),
            _df("Người tham gia", "attendees"),
            _df("SĐT người tham gia", "contact_phone"),
            _df("Khứ hồi", "is_round_trip", kind="bool", default=False),
            _df("Ghi chú", "note"),
            # --- Riêng ĐẶT XE GIAO HÀNG ---
            _df("Tên hàng hóa", "goods_name"),
            _df("Kích thước/KL", "goods_size", aliases=["Kích thước / KL", "Kích thước"]),
            _df("Tên người gửi", "sender_name"),
            _df("SĐT người gửi", "sender_phone"),
            _df("Tên người nhận", "receiver_name"),
            _df("SĐT người nhận", "receiver_phone"),
            _df("Chỉ dẫn đặc biệt", "special_instructions", aliases=["Chi dẫn đặc biệt"]),
            # --- Điều phối / chạy thực tế (dữ liệu lịch sử) ---
            _df("Thời gian điều phối", "dispatched_at", kind="isodt"),
            _df("Biển số xe", "assigned_vehicle_id", kind="ref", ref="vehicle", aliases=["Tên xe"]),
            _df("SĐT tài xế", "assigned_driver_id", kind="ref", ref="driver", aliases=["Tên tài xế"]),
            _df("Trạng thái tài xế", "driver_status", kind="coded",
                labels=DRIVER_STATUS_LABELS, default=0),
            _df("Bắt đầu thực tế", "actual_start_time", kind="isodt"),
            _df("Kết thúc thực tế", "actual_end_time", kind="isodt"),
        ],
        # Suy diễn nhiều cột từ một ô: Loại yêu cầu (→ loại + tự lái), Lộ trình (→ đi/đến/dừng).
        "derive": [
            {"header": "Loại yêu cầu", "apply": _derive_vehicle_type},
            {"header": "Lộ trình", "apply": _derive_route},
        ],
        # Tệp đính kèm: tạo dòng file giữ chỗ + liên kết vào phiếu.
        "attachment": {"header": "Tệp đính kèm", "entity": "vehicle_booking", "doc_type": "attachment"},
    },
    ImportModule.SEAL_REQUEST: {
        "label": "Yêu cầu đóng dấu",
        "sheet": "Yeu cau dong dau",
        "header_model": SealRequest,
        "code": _df("Mã yêu cầu *", "code", required=True, aliases=["Mã phiếu"]),
        "header_fields": [
            _df("Tiêu đề", "title", aliases=["Tiêu đề phiếu"]),
            _df("Chi tiết loại", "purpose", aliases=["Mục đích sử dụng", "Mục đích"]),
            _df("Trạng thái chung", "status", kind="coded", labels=SEAL_STATUS_LABELS,
                default=4, aliases=["Trạng thái", "Trạng thái (mã)"]),
            _df("Tên người tạo", "requester", aliases=["Người tạo"]),
            _df("Phòng ban người tạo", "department_id", kind="ref", ref="department",
                aliases=["Phòng ban", "Phòng ban (mã)"]),
            _df("Công ty", "company_id", kind="ref", ref="company",
                aliases=["Công ty chính (mã)", "Công ty (mã/tên)"]),
            _df("Người duyệt cấp 1", "first_approver_id", kind="approver",
                aliases=["Người duyệt", "TBP phê duyệt"]),
            _df("Ghi chú", "note"),
            _df("Ngày tạo", "created_at", kind="datetime"),
        ],
        # Ghi bảng nối công ty sau khi tạo header (đúng phạm vi Văn thư/Giám đốc).
        "post_apply": _seal_set_companies,
        "attachment": {"header": "Tệp đính kèm", "entity": "seal_request", "doc_type": "signed_doc"},
    },
}


def is_doc_module(module: int) -> bool:
    return module in DOC_ADAPTERS


def run(db: Session, batch, wb, apply: bool) -> None:
    adapter = DOC_ADAPTERS[batch.module]
    header_model = adapter["header_model"]
    line_model = adapter.get("line_model")   # None = chứng từ KHÔNG có dòng (Đặt xe / Duyệt dấu)
    line_fk = adapter.get("line_fk")
    line_fields = adapter.get("line_fields", [])
    ws = wb[adapter["sheet"]] if adapter["sheet"] in wb.sheetnames else wb.worksheets[0]

    all_fields = [adapter["code"], *adapter["header_fields"], *line_fields]
    header_col: dict[str, int] = {}
    for col in range(1, (ws.max_column or 0) + 1):
        key = _norm(ws.cell(row=HEADER_ROW, column=col).value)
        if key:
            header_col[key] = col
    #  Khớp cột theo tiêu đề CHÍNH hoặc ALIAS (bản xuất hệ cũ ghi nhãn hơi khác).
    field_col = {f["attr"]: catalog_import._match_col(header_col, f) for f in all_fields}
    catalog_import.ensure_file_matches(adapter["sheet"], all_fields, field_col)

    #  Cột suy diễn (Loại yêu cầu, Lộ trình) + cột Tệp đính kèm: dò riêng theo tiêu đề.
    def _find_col(header: str, aliases=()):
        for n in (_norm(header), *(_norm(a) for a in aliases)):
            if n in header_col:
                return header_col[n]
        return None

    derive_specs = [{**d, "col": _find_col(d["header"], d.get("aliases", []))}
                    for d in adapter.get("derive", [])]
    attach = adapter.get("attachment")
    attach_col = _find_col(attach["header"], attach.get("aliases", [])) if attach else None

    counts = {"created": 0, "updated": 0, "skipped": 0, "warning": 0, "review": 0, "error": 0}
    logs: list[dict] = []
    changes: list[dict] = []

    def log(row_no, level, category, message, ref_key="", target_code=""):
        logs.append({"sheet": adapter["sheet"], "row_no": row_no, "level": int(level),
                     "category": category, "message": message, "ref_key": ref_key,
                     "target_code": target_code})
        if level == LogLevel.WARNING:
            counts["warning"] += 1
        elif level == LogLevel.REVIEW:
            counts["review"] += 1
        elif level == LogLevel.ERROR:
            counts["error"] += 1

    def read(row, attr):
        col = field_col.get(attr)
        return ws.cell(row=row, column=col).value if col else None

    def build(fields, row, target: dict, code_for_log: str):
        """Đổ giá trị các field vào dict target theo kiểu; ref set id + tên snapshot."""
        for f in fields:
            if field_col.get(f["attr"]) is None:
                continue
            raw = read(row, f["attr"])
            kind = f["kind"]
            if kind == "int":
                target[f["attr"]] = _to_int(raw, f["default"] or 0)
            elif kind == "float":
                target[f["attr"]] = _to_float(raw, f["default"] or 0.0)
            elif kind == "bool":
                target[f["attr"]] = _to_bool(raw, bool(f["default"]))
            elif kind == "date":
                target[f["attr"]] = _to_date_str(raw)
            elif kind == "coded":  # nhận MÃ số hoặc NHÃN tiếng Việt (trạng thái, loại…)
                target[f["attr"]] = _to_coded(raw, f["labels"], f["default"])
            elif kind == "isodt":  # cột thời gian kiểu chuỗi -> ISO ('' nếu trống/hỏng)
                target[f["attr"]] = _to_isodt(raw)
            elif kind == "datetime":  # cột DateTime thật (vd created_at) — bỏ nếu không đọc được
                dt = _parse_dt(raw)
                if dt:
                    target[f["attr"]] = dt
            elif kind == "approver":  # tên nhân sự -> id tài khoản duyệt (first_approver_id)
                target[f["attr"]] = _resolve_approver_id(db, _s(raw)) if _s(raw) else 0
            elif kind == "ref":
                target[f["attr"]] = _resolve_ref(db, f, _s(raw), row, code_for_log, log)
                obj = _resolve_ref_obj(db, f["ref"], _s(raw))
                if obj and f.get("name_attr"):
                    target[f["name_attr"]] = getattr(obj, _REF_NAME[f["ref"]], "") or ""
            else:
                val = _s(raw)
                if not val and f["default"] is not None:
                    val = f["default"]
                target[f["attr"]] = val

    # Gộp dòng theo mã phiếu (giữ thứ tự).
    groups: "OrderedDict[str, list[int]]" = OrderedDict()
    total = 0
    max_row = ws.max_row or 0
    for r in range(DATA_START, max_row + 1):
        code = _s(read(r, "code"))
        if not code and not any(_s(read(r, f["attr"])) for f in all_fields):
            continue
        total += 1
        if not code:
            counts["skipped"] += 1
            log(r, LogLevel.ERROR, "missing_code", "Dòng thiếu Mã phiếu — bỏ qua")
            continue
        groups.setdefault(code, []).append(r)

    for code, rows in groups.items():
        if db.query(header_model).filter(header_model.code == code).first():
            counts["skipped"] += len(rows)
            log(rows[0], LogLevel.WARNING, "doc_exists",
                f"Mã phiếu '{code}' đã tồn tại — bỏ qua cả phiếu", ref_key=code)
            continue

        header_data: dict = {"code": code}
        build(adapter["header_fields"], rows[0], header_data, code)
        #  Suy diễn nhiều cột từ MỘT ô (Loại yêu cầu → loại + tự lái, Lộ trình → đi/đến/dừng).
        for spec in derive_specs:
            if spec["col"]:
                spec["apply"](ws.cell(row=rows[0], column=spec["col"]).value, header_data)
        # Cột đầu phiếu vắng trong file nhưng model đòi non-null (vd Survey.survey_type).
        for k, v in adapter.get("header_defaults", {}).items():
            header_data.setdefault(k, v)
        _cap_strings(header_model, header_data)
        header = header_model(created_by=batch.created_by, updated_by=batch.created_by, **header_data)
        db.add(header)
        db.flush()

        nlines = 0
        if line_model is not None:
            for r in rows:
                missing = [f["header"].replace(" *", "") for f in line_fields
                           if f["required"] and not _s(read(r, f["attr"]))]
                if missing:
                    log(r, LogLevel.ERROR, "line_missing",
                        f"Dòng thiếu: {', '.join(missing)} — bỏ dòng", ref_key=code, target_code=code)
                    continue
                line_data: dict = {line_fk: header.id}
                build(line_fields, r, line_data, code)
                # Bỏ dòng rỗng (không có nội dung nào ngoài khoá ngoại).
                if not any(_s(v) for k, v in line_data.items() if k != line_fk):
                    continue
                _cap_strings(line_model, line_data)
                db.add(line_model(created_by=batch.created_by, updated_by=batch.created_by, **line_data))
                nlines += 1
            db.flush()
            # Phiếu không có DÒNG hợp lệ nào -> không tạo phiếu rỗng, gỡ header vừa thêm.
            if nlines == 0:
                db.delete(header)
                db.flush()
                counts["skipped"] += len(rows)
                log(rows[0], LogLevel.WARNING, "doc_no_line",
                    f"Phiếu '{code}' không có dòng hợp lệ — bỏ qua", ref_key=code)
                continue

        #  Hook sau khi tạo header (vd Duyệt dấu: ghi bảng nối công ty từ company_id).
        if adapter.get("post_apply"):
            adapter["post_apply"](db, header, header_data)
            db.flush()

        #  Tệp đính kèm: tạo dòng file giữ chỗ + liên kết vào phiếu (bản xuất chỉ có TÊN tệp).
        if attach and attach_col:
            n_att = _create_attachment_placeholders(
                db, attach["entity"], header.id,
                ws.cell(row=rows[0], column=attach_col).value,
                attach["doc_type"], batch.created_by)
            if n_att:
                db.flush()

        counts["created"] += 1
        changes.append({"target_id": header.id, "was_new": True, "snapshot": ""})
        line_note = f" với {nlines} dòng" if line_model is not None else ""
        log(rows[0], LogLevel.INFO, "doc_created",
            f"Tạo {adapter['label']} '{code}'{line_note}", ref_key=code, target_code=code)

    if apply:
        db.commit()
    else:
        db.rollback()
    catalog_import._persist(db, batch, counts, logs, changes if apply else [], total, adapter["sheet"])


def _resolve_ref(db, f, code, row_no, code_for_log, log) -> int:
    """Mã HOẶC tên -> id (dùng `_resolve_ref_obj` đa khoá). Không thấy -> REVIEW, trả 0."""
    if not code:
        return 0
    obj = _resolve_ref_obj(db, f["ref"], code)
    if obj:
        return obj.id
    log(row_no, LogLevel.REVIEW, "ref_not_found",
        f"«{f['header']}» = '{code}' không có trong danh mục — để trống", ref_key=code_for_log)
    return 0


def revert(db: Session, module: int, changes, user_id: int) -> tuple[int, int]:
    """Hoàn tác: xoá phiếu do batch tạo (kèm dòng / bảng nối công ty / tệp giữ chỗ).
    v1 create-only nên không có khôi phục."""
    from app.modules.seal_request.model import SealRequestCompany
    adapter = DOC_ADAPTERS[module]
    header_model = adapter["header_model"]
    line_model = adapter.get("line_model")
    line_fk = adapter.get("line_fk")
    attach = adapter.get("attachment")
    is_seal = header_model is SealRequest
    deleted = 0
    for ch in changes:
        if not ch.was_new:
            continue
        h = db.get(header_model, ch.survey_id)   # survey_id dùng chung = header id
        if not h:
            continue
        if line_model is not None:
            db.query(line_model).filter(getattr(line_model, line_fk) == h.id).delete(synchronize_session=False)
        if is_seal:
            db.query(SealRequestCompany).filter(
                SealRequestCompany.seal_request_id == h.id).delete(synchronize_session=False)
        #  Gỡ tệp đính kèm giữ chỗ đã tạo cùng phiếu (dòng tab_file + liên kết).
        if attach:
            links = db.query(FileLink).filter(
                FileLink.entity == attach["entity"], FileLink.entity_id == h.id).all()
            for lk in links:
                sf = db.get(StoredFile, lk.file_id)
                db.delete(lk)
                #  File giữ chỗ (không có nội dung thật) chỉ dùng cho phiếu này -> xoá luôn.
                if sf and not sf.file_key:
                    db.delete(sf)
        db.delete(h)
        deleted += 1
    return deleted, 0


def build_template(module: int) -> bytes:
    """File .xlsx mẫu: một sheet, cột Mã phiếu + đầu phiếu + (dòng hàng) + suy diễn + tệp."""
    import openpyxl
    from io import BytesIO
    adapter = DOC_ADAPTERS[module]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = adapter["sheet"]
    headers = [adapter["code"]["header"],
               *(f["header"] for f in adapter["header_fields"]),
               *(f["header"] for f in adapter.get("line_fields", [])),
               *(d["header"] for d in adapter.get("derive", []))]
    if adapter.get("attachment"):
        headers.append(adapter["attachment"]["header"])
    for i, h in enumerate(headers, start=1):
        ws.cell(row=1, column=i, value=h)
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(14, len(h) + 2)
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()
