"""PHA 1 — Import Khảo sát từ sheet 3 (NCC) + sheet 4 (SP).

- Gom 1 phiếu = (Phân loại F + NCC O). import_key = "phanloai::ncc".
- Resolve NCC: sheet3 theo MST (Q), sheet4 theo tên viết tắt (O); xung đột -> text-only + log.
- Upsert Supplier (từ sheet 3). Upsert Survey + supplier_line/product_line theo khoá.
- dry_run: tính toán + ghi log NHƯNG rollback thay đổi nghiệp vụ (không tạo phiếu).
"""
import json
from datetime import datetime

from openpyxl.utils import column_index_from_string
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.modules.supplier.model import Supplier
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine

from .model import ImportBatch, ImportStatus, LogLevel

HEADER_ROW = 5
DATA_START = 6


# ---------- chuẩn hoá ô ----------
def _cell(ws, row, letter):
    return ws.cell(row=row, column=column_index_from_string(letter)).value


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _d(v) -> str:
    """Ngày -> 'YYYY-MM-DD'. Lỗi/serial rác -> ''."""
    if v is None or v == "":
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def _n(v) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(" ", "")
    # "20.500" (ngăn nghìn) vs "20.5": nếu có cả . và , -> . là nghìn; nếu chỉ . -> thập phân
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float("".join(ch for ch in s if ch.isdigit() or ch in ".-") or 0)
    except ValueError:
        return 0.0


def _b(v) -> bool:
    return _s(v).lower() in ("true", "1", "x", "có", "co", "yes")


def _find_sheet(wb, prefix: str):
    for ws in wb.worksheets:
        if ws.title.strip().startswith(prefix):
            return ws
    return None


def _last_row(ws) -> int:
    last = HEADER_ROW
    for r in range(DATA_START, (ws.max_row or DATA_START) + 1):
        if _s(_cell(ws, r, "A")) or _s(_cell(ws, r, "E")) or _s(_cell(ws, r, "F")):
            last = r
    return last


def _norm_key(item_group: str, supplier_code: str) -> str:
    return f"{' '.join(item_group.split()).upper()}::{' '.join(supplier_code.split()).upper()}"


_LEN_CACHE: dict = {}


def _fit(model, data: dict):
    """Cắt string cho vừa độ dài cột (data cũ nhiều field free-text dài hơn cột). Trả (data, [field bị cắt])."""
    if model not in _LEN_CACHE:
        _LEN_CACHE[model] = {c.key: getattr(c.type, "length", None) for c in sa_inspect(model).columns}
    lens = _LEN_CACHE[model]
    out, trunc = {}, []
    for k, v in data.items():
        L = lens.get(k)
        if isinstance(v, str) and L and len(v) > L:
            out[k] = v[:L]; trunc.append(k)
        else:
            out[k] = v
    return out, trunc


# ---------- chạy import ----------
def run(db: Session, batch: ImportBatch, wb, apply: bool) -> None:
    ws3 = _find_sheet(wb, "3.")
    ws4 = _find_sheet(wb, "4.")
    counts = {"created": 0, "updated": 0, "skipped": 0, "warning": 0, "review": 0, "error": 0}
    logs: list[dict] = []

    def log(sheet, row_no, level, category, message, ref_key="", target_code=""):
        logs.append({"sheet": sheet, "row_no": row_no, "level": int(level), "category": category,
                     "message": message, "ref_key": ref_key, "target_code": target_code})
        if level == LogLevel.WARNING:
            counts["warning"] += 1
        elif level == LogLevel.REVIEW:
            counts["review"] += 1
        elif level == LogLevel.ERROR:
            counts["error"] += 1

    survey_cache: dict[str, Survey] = {}
    n3 = _last_row(ws3) - HEADER_ROW if ws3 else 0
    n4 = _last_row(ws4) - HEADER_ROW if ws4 else 0
    batch.sheet_info = json.dumps({"sheet_ncc": ws3.title if ws3 else None, "rows_ncc": n3,
                                   "sheet_sp": ws4.title if ws4 else None, "rows_sp": n4}, ensure_ascii=False)

    def get_survey(item_group, supplier_code, hdr):
        key = _norm_key(item_group, supplier_code)
        if key in survey_cache:
            return survey_cache[key]
        s = db.query(Survey).filter(Survey.import_key == key).first()
        if not s:
            s = Survey(import_key=key, survey_type="supplier", status="approved",
                       approve_status="Duyệt", item_group=item_group,
                       received_date=hdr["received"], result_due_date=hdr["due"],
                       requirement_detail=hdr["detail"], main_content=hdr["bp"],
                       request_qty=hdr["qty"], uom=hdr["uom"], proposed_rate=hdr["rate"],
                       nspt=hdr["nspt"], pr_code=hdr["req_code"],
                       created_by=batch.created_by, updated_by=batch.created_by)
            db.add(s); db.flush()
            s.code = f"KS{s.id:05d}"
        survey_cache[key] = s
        return s

    # ----- Pass 1: sheet 3 (NCC) -----
    if ws3:
        for r in range(DATA_START, _last_row(ws3) + 1):
            ig, code, tax = _s(_cell(ws3, r, "F")), _s(_cell(ws3, r, "O")), _s(_cell(ws3, r, "Q"))
            if not ig or not code:
                if _s(_cell(ws3, r, "A")):
                    log("3.KS-NCC", r, LogLevel.ERROR, "missing_key", "Thiếu Phân loại hoặc NCC", ref_key=code)
                    counts["skipped"] += 1
                continue
            hdr = {"received": _d(_cell(ws3, r, "B")), "due": _d(_cell(ws3, r, "C")), "bp": _s(_cell(ws3, r, "D")),
                   "req_code": _s(_cell(ws3, r, "E")), "detail": _s(_cell(ws3, r, "G")), "qty": _n(_cell(ws3, r, "H")),
                   "uom": _s(_cell(ws3, r, "I")), "rate": _n(_cell(ws3, r, "J")), "nspt": _s(_cell(ws3, r, "K"))}
            # upsert Supplier + phát hiện MST xung đột
            _upsert_supplier(db, batch, code, tax, ws3, r, log)
            s = get_survey(ig, code, hdr)
            row_key = tax or code
            line = None
            for ln in db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == s.id).all():
                if (tax and ln.tax_code == tax) or (ln.supplier_code == code):
                    line = ln; break
            data = dict(
                contact_date=_d(_cell(ws3, r, "L")), reply_date=_d(_cell(ws3, r, "M")), result_date=_d(_cell(ws3, r, "N")),
                supplier_code=code, supplier_name=_s(_cell(ws3, r, "P")), tax_code=tax,
                reg_address=_s(_cell(ws3, r, "R")), warehouse_address=_s(_cell(ws3, r, "S")), google_maps=_s(_cell(ws3, r, "T")),
                contact_person=_s(_cell(ws3, r, "U")), contact_phone=_s(_cell(ws3, r, "V")), supply_group=_s(_cell(ws3, r, "W")),
                quote_folder=_s(_cell(ws3, r, "X")), source_of_information=_s(_cell(ws3, r, "Y")),
                production_tech=_s(_cell(ws3, r, "Z")), production_time=_s(_cell(ws3, r, "AA")), nvkd_eval=_s(_cell(ws3, r, "AB")),
                invoice_policy=_s(_cell(ws3, r, "AC")), reliability=_s(_cell(ws3, r, "AD")), delivery_policy=_s(_cell(ws3, r, "AE")),
                debt_policy=_s(_cell(ws3, r, "AF")), defect_return=_s(_cell(ws3, r, "AG")), nspt_reason=_s(_cell(ws3, r, "AH")),
                line_approve=_s(_cell(ws3, r, "AI")), line_approve_note=_s(_cell(ws3, r, "AJ")))
            data, trunc = _fit(SurveySupplierLine, data)
            if trunc:
                log("3.KS-NCC", r, LogLevel.WARNING, "value_truncated", f"Cắt bớt do quá dài: {', '.join(trunc)}", ref_key=code)
            if line:
                for k, v in data.items():
                    setattr(line, k, v)
                counts["updated"] += 1
            else:
                db.add(SurveySupplierLine(survey_id=s.id, created_by=batch.created_by, updated_by=batch.created_by, **data))
                counts["created"] += 1

    # ----- Pass 2: sheet 4 (SP) -----
    if ws4:
        for r in range(DATA_START, _last_row(ws4) + 1):
            ig, code = _s(_cell(ws4, r, "F")), _s(_cell(ws4, r, "O"))
            if not ig or not code:
                if _s(_cell(ws4, r, "A")):
                    log("4.KS-SP", r, LogLevel.ERROR, "missing_key", "Thiếu Phân loại hoặc NCC", ref_key=code)
                    counts["skipped"] += 1
                continue
            hdr = {"received": _d(_cell(ws4, r, "B")), "due": _d(_cell(ws4, r, "C")), "bp": _s(_cell(ws4, r, "D")),
                   "req_code": _s(_cell(ws4, r, "E")), "detail": _s(_cell(ws4, r, "G")), "qty": _n(_cell(ws4, r, "H")),
                   "uom": _s(_cell(ws4, r, "I")), "rate": _n(_cell(ws4, r, "J")), "nspt": _s(_cell(ws4, r, "K"))}
            if not db.query(Supplier).filter(Supplier.code == code).first():
                log("4.KS-SP", r, LogLevel.REVIEW, "ncc_text_only",
                    f"NCC '{code}' không có trong danh mục (KS SP không có MST) — giữ text", ref_key=code)
            s = get_survey(ig, code, hdr)
            internal = _s(_cell(ws4, r, "P"))
            pname = _s(_cell(ws4, r, "Q")) or _s(_cell(ws4, r, "R"))
            line = None
            for ln in db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == s.id).all():
                if ln.supplier_code == code and ((internal and ln.internal_code == internal) or ln.product_name == pname):
                    line = ln; break
            data = dict(
                contact_date=_d(_cell(ws4, r, "L")), reply_date=_d(_cell(ws4, r, "M")), result_date=_d(_cell(ws4, r, "N")),
                supplier_code=code, internal_code=internal, product_name=pname, spec=_s(_cell(ws4, r, "S")),
                origin=_s(_cell(ws4, r, "T")), quote_unit=_s(_cell(ws4, r, "U")), moq=_n(_cell(ws4, r, "V")),
                price_by_volume=_n(_cell(ws4, r, "W")), volume_range=_s(_cell(ws4, r, "X")), vat=_n(_cell(ws4, r, "Y")),
                amount=_n(_cell(ws4, r, "Z")), internal_unit=_s(_cell(ws4, r, "AA")), amount_converted=_n(_cell(ws4, r, "AB")),
                shipping_cost=_n(_cell(ws4, r, "AC")), delivery_time=_s(_cell(ws4, r, "AD")), delivery_place=_s(_cell(ws4, r, "AE")),
                quote_file=_s(_cell(ws4, r, "AF")), sample_ready=_b(_cell(ws4, r, "AG")), sample_date=_d(_cell(ws4, r, "AH")),
                sample_qty=_n(_cell(ws4, r, "AI")), lab_result=_s(_cell(ws4, r, "AJ")), nspt_note=_s(_cell(ws4, r, "AK")),
                line_approve=_s(_cell(ws4, r, "AL")), line_approve_note=_s(_cell(ws4, r, "AM")))
            data, trunc = _fit(SurveyProductLine, data)
            if trunc:
                log("4.KS-SP", r, LogLevel.WARNING, "value_truncated", f"Cắt bớt do quá dài: {', '.join(trunc)}", ref_key=code)
            if line:
                for k, v in data.items():
                    setattr(line, k, v)
                counts["updated"] += 1
            else:
                db.add(SurveyProductLine(survey_id=s.id, created_by=batch.created_by, updated_by=batch.created_by, **data))
                counts["created"] += 1

    # ----- kết thúc: apply commit, dry-run rollback; rồi persist batch + logs -----
    if apply:
        db.commit()
    else:
        db.rollback()
    _persist(db, batch, counts, logs, n3 + n4)


def _upsert_supplier(db, batch, code, tax, ws, r, log):
    """Tạo/điền NCC theo code; MST khớp NCC khác code -> log review (không đè catalog)."""
    if tax:
        by_tax = db.query(Supplier).filter(Supplier.tax_code == tax).first()
        if by_tax and by_tax.code != code:
            log("3.KS-NCC", r, LogLevel.REVIEW, "mst_conflict",
                f"MST {tax} đang thuộc NCC '{by_tax.code}' khác tên viết tắt '{code}' — giữ text", ref_key=code)
            return
    sup = db.query(Supplier).filter(Supplier.code == code).first()
    if sup:
        # điền field còn trống, không đè data đang dùng
        for attr, val in (("name", _s(_cell(ws, r, "P"))), ("tax_code", tax),
                          ("address", _s(_cell(ws, r, "R"))), ("payment_terms", _s(_cell(ws, r, "AF"))),
                          ("phone", _s(_cell(ws, r, "V"))), ("contact_person", _s(_cell(ws, r, "U")))):
            if val and not (getattr(sup, attr) or "").strip():
                setattr(sup, attr, val)
    else:
        db.add(Supplier(code=code, name=_s(_cell(ws, r, "P")), tax_code=tax,
                        address=_s(_cell(ws, r, "R")), payment_terms=_s(_cell(ws, r, "AF")),
                        phone=_s(_cell(ws, r, "V")), contact_person=_s(_cell(ws, r, "U")),
                        supplier_type="goods", is_active=True,
                        created_by=batch.created_by, updated_by=batch.created_by))
        log("3.KS-NCC", r, LogLevel.INFO, "ncc_created", f"Tạo NCC mới '{code}'", ref_key=code)


def _persist(db, batch, counts, logs, total_rows):
    """Ghi kết quả vào batch + import_log (transaction riêng, không bị rollback dry-run)."""
    from .model import ImportLog
    b = db.get(ImportBatch, batch.id)
    b.total_rows = total_rows
    b.created_count = counts["created"]; b.updated_count = counts["updated"]; b.skipped_count = counts["skipped"]
    b.warning_count = counts["warning"]; b.review_count = counts["review"]; b.error_count = counts["error"]
    for lg in logs:
        db.add(ImportLog(batch_id=b.id, sheet=lg["sheet"], row_no=lg["row_no"], level=lg["level"],
                         category=lg["category"], message=lg["message"][:60000], ref_key=lg["ref_key"][:120],
                         target_code=lg["target_code"][:50], created_by=b.created_by))
    b.status = ImportStatus.DONE
    b.finished_at = datetime.utcnow()
    db.commit()
