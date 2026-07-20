"""Import Khảo sát (bản chốt) — tái tạo Mã yêu cầu, gom 2 loại phiếu, phân phối dòng NCC.

- Mã yêu cầu (khoá) = chuẩn_hoá(viết_tắt(BP) + ngày + Phân_loại + Chi_tiết). viết_tắt theo bảng, fallback KC.
- Phiếu: Mã VTBB có trong danh mục -> gom theo VTBB (loại 1); không -> theo Mã yêu cầu (loại 2).
- Dòng NCC/SP: khoá = (Mã yêu cầu + MST). Dòng NCC phân phối vào phiếu theo (MST + Mã yêu cầu).
- Ghi snapshot phiếu (trước khi sửa) để revert. Dry-run: tính + log rồi rollback.
"""
import json
import re
from datetime import datetime

from openpyxl.utils import column_index_from_string
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.modules.catalog.model import ItemGroup, Unit
from app.modules.product.model import Product
from app.modules.supplier.model import Supplier
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine

from .model import ImportBatch, ImportChange, ImportStatus, LogLevel

HEADER_ROW = 5
DATA_START = 6

# Bảng viết tắt thương hiệu (từ cột BP/Người YC). Không khớp -> "KC".
_ABBREV = {
    "NHÀ MÁY DEGO": "NM", "SX - MS LY": "SX", "LAB": "LAB", "KD ABA": "AB",
    "KD ICARE": "IC", "KD DR XANH": "DR", "KD IDA": "ID", "SX - MS HƯƠNG": "SX",
    "TM - MS QUYÊN": "TM", "KD N2SBIO": "N2", "QLTM_MS NGÂN": "QLTM_MS NGÂN",
}


# ---------- chuẩn hoá ----------
def _cell(ws, row, letter):
    return ws.cell(row=row, column=column_index_from_string(letter)).value


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _ncode(s: str) -> str:
    return " ".join((s or "").split()).upper()


def _d(v) -> str:
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
    """Parse số kiểu Việt Nam: '.' = phân cách nghìn, ',' = thập phân.
    Vd '20.600'->20600, '1.000.000'->1000000, '20,6'->20.6, '20.600,50'->20600.5, '20.6'->20.6.
    """
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    neg = s.startswith("-")
    s = "".join(ch for ch in s if ch.isdigit() or ch in ".,")
    if not s:
        return 0.0
    if "," in s and "." in s:                       # có cả 2: dấu xuất hiện sau cùng là thập phân
        if s.rfind(",") > s.rfind("."):             # VN: 1.234.567,89
            s = s.replace(".", "").replace(",", ".")
        else:                                        # EN: 1,234,567.89
            s = s.replace(",", "")
    elif "," in s:                                    # chỉ phẩy
        if s.count(",") > 1:                          # nhiều phẩy -> nhóm nghìn kiểu EN
            s = s.replace(",", "")
        else:                                         # VN: 1 phẩy là thập phân
            s = s.replace(",", ".")
    elif "." in s:                                    # chỉ chấm
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):    # nhóm nghìn (20.600 / 1.000.000)
            s = s.replace(".", "")
        # còn lại (20.6 / 12.34) giữ nguyên là thập phân
    try:
        return -float(s) if neg else float(s)
    except ValueError:
        return 0.0


def _b(v) -> bool:
    return _s(v).lower() in ("true", "1", "x", "có", "co", "yes")


def _vat(v) -> float:
    x = _n(v)
    return round(x * 100, 2) if 0 < x <= 1 else x


def _approve(v):
    s = _s(v); low = s.lower()
    if not s:
        return "Chờ duyệt", ""
    if "không" in low or "ko duyệt" in low:
        return "Không duyệt", ""
    if low in ("duyệt", "đã duyệt", "đạt", "duyet", "ok"):
        return "Đã duyệt", ""
    return "Thiếu thông tin", s


def _abbrev(bp: str) -> str:
    return _ABBREV.get(_ncode(bp), "KC")


def _ddmmyyyy(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d%m%Y") if iso else ""
    except ValueError:
        return ""


def _req_key(bp, iso_date, item_group, detail) -> str:
    """Khoá yêu cầu (so khớp) = viết_tắt + ngày + Phân_loại + Chi_tiết (chuẩn hoá)."""
    return f"{_abbrev(bp)}|{_ddmmyyyy(iso_date)}|{_ncode(item_group)}|{_ncode(detail)}"


def _find_sheet(wb, prefix: str):
    for ws in wb.worksheets:
        if ws.title.strip().startswith(prefix):
            return ws
    return None


def _last_row(ws) -> int:
    last = HEADER_ROW
    for r in range(DATA_START, (ws.max_row or DATA_START) + 1):
        if _s(_cell(ws, r, "A")) or _s(_cell(ws, r, "F")) or _s(_cell(ws, r, "O")):
            last = r
    return last


_LEN_CACHE: dict = {}


def _fit(model, data: dict):
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


def _snap(db, s: Survey) -> str:
    """Ảnh chụp phiếu + dòng (JSON) để revert."""
    def cols(obj):
        return {c.key: getattr(obj, c.key) for c in sa_inspect(obj).mapper.column_attrs
                if c.key not in ("created_at", "updated_at")}
    sup = [cols(x) for x in db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == s.id).all()]
    prod = [cols(x) for x in db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == s.id).all()]
    return json.dumps({"survey": cols(s), "sup": sup, "prod": prod}, ensure_ascii=False, default=str)


# ---------- chạy import ----------
def run(db: Session, batch: ImportBatch, wb, apply: bool) -> None:
    ws3 = _find_sheet(wb, "3.")
    ws4 = _find_sheet(wb, "4.")
    counts = {"created": 0, "updated": 0, "skipped": 0, "warning": 0, "review": 0, "error": 0}
    logs: list[dict] = []
    changes: list[dict] = []

    def log(sheet, row_no, level, category, message, ref_key="", target_code=""):
        logs.append({"sheet": sheet, "row_no": row_no, "level": int(level), "category": category,
                     "message": message, "ref_key": ref_key, "target_code": target_code})
        if level == LogLevel.WARNING:
            counts["warning"] += 1
        elif level == LogLevel.REVIEW:
            counts["review"] += 1
        elif level == LogLevel.ERROR:
            counts["error"] += 1

    if ws3 is None:
        log("-", 0, LogLevel.WARNING, "missing_sheet", "Không thấy sheet '3. KHẢO SÁT ... N'")
    if ws4 is None:
        log("-", 0, LogLevel.WARNING, "missing_sheet", "Không thấy sheet '4. KHẢO SÁT ... S'")

    ig_map = {_ncode(g.name): g.name for g in db.query(ItemGroup).all()}
    unit_map = {_ncode(u.name): u.name for u in db.query(Unit).all()}
    prod_map = {_ncode(p.code): p for p in db.query(Product).all() if (p.code or "").strip()}
    prod_codes = set(prod_map)
    _seen_unmatched: set = set()

    def cat(value, cmap, label, sheet, row_no):
        v = _s(value)
        if not v:
            return ""
        canon = cmap.get(_ncode(v))
        if canon:
            return canon
        key = (label, _ncode(v))
        if key not in _seen_unmatched:
            _seen_unmatched.add(key)
            log(sheet, row_no, LogLevel.REVIEW, "value_unmatched", f"{label} '{v}' không có trong danh mục — giữ text", ref_key=v)
        return v

    def canon_code(code, tax):
        if tax:
            st = db.query(Supplier).filter(Supplier.tax_code == tax).first()
            if st and (st.code or "").strip():
                return st.code
        if code:
            sc = db.query(Supplier).filter(Supplier.code == code).first()
            if sc and (sc.code or "").strip():
                return sc.code
        return code

    def sup_mst(code):
        sc = db.query(Supplier).filter(Supplier.code == code).first()
        return (sc.tax_code or "").strip() if sc else ""

    # Sheet SP (4) KHÔNG có cột MST -> suy MST từ tên viết tắt NCC. Map viết tắt -> MST
    # dựng từ sheet NCC (3) để 2 sheet dùng chung 1 nguồn MST (khoá dòng khớp nhau).
    abbr_mst: dict[str, str] = {}

    def resolve_mst(raw_abbr: str, tax: str = "") -> str:
        """MST của dòng: ưu tiên MST trực tiếp (sheet 3) -> map viết tắt -> danh mục -> tên."""
        m = tax or abbr_mst.get(_ncode(raw_abbr)) or sup_mst(canon_code(raw_abbr, tax)) or raw_abbr
        return _ncode(m)

    survey_cache: dict[str, Survey] = {}
    snapshotted: set = set()
    prodkey_full: dict[tuple, int] = {}    # (reqk, mst) -> survey_id (khớp đúng cả ngày, cho loại 2)
    prodkey_loose: dict[tuple, int] = {}   # (ig, detail, mst) -> survey_id (bỏ ngày, cho loại 1 VTBB)
    seen_lk: set = set()                    # ("P"/"S", line_key) đã gặp trong LẦN import này -> phát hiện trùng trong file

    def snapshot(s: Survey, was_new: bool):
        if s.id in snapshotted:
            return
        snapshotted.add(s.id)
        changes.append({"survey_id": s.id, "was_new": was_new, "snapshot": "" if was_new else _snap(db, s)})

    # Sinh Mã yêu cầu PYC.<viết tắt>.<ddmmyyyy>.<stt> khi ô "Mã yêu cầu" (E) trống.
    req_seq: dict = {}
    reqcode_cache: dict = {}

    def gen_reqcode(bp, received, reqk, sheet_code) -> str:
        if sheet_code:
            return sheet_code
        if reqk in reqcode_cache:
            return reqcode_cache[reqk]
        ab, dd = _abbrev(bp), (_ddmmyyyy(received) or "NA")
        req_seq[(ab, dd)] = req_seq.get((ab, dd), 0) + 1
        code = f"PYC.{ab}.{dd}.{req_seq[(ab, dd)]:02d}"
        reqcode_cache[reqk] = code
        return code

    def get_survey(survey_key: str, hdr: dict) -> Survey:
        if survey_key in survey_cache:
            return survey_cache[survey_key]
        s = db.query(Survey).filter(Survey.import_key == survey_key).first()
        was_new = s is None
        if not s:
            s = Survey(import_key=survey_key, survey_type="combined", status="approved", approve_status="Duyệt",
                       item_group=hdr["ig"], received_date=hdr["received"], result_due_date=hdr["due"],
                       requirement_detail=hdr["detail"], main_content=(hdr["detail"] or hdr["ig"])[:500],
                       request_qty=hdr["qty"], uom=hdr["uom"], proposed_rate=hdr["rate"], nspt=hdr["nspt"],
                       pr_code=hdr["reqcode"], created_by=batch.created_by, updated_by=batch.created_by)
            db.add(s); db.flush(); s.code = f"KS{s.id:05d}"
            log("-", 0, LogLevel.INFO, "survey_new", f"Tạo phiếu mới {s.code}", ref_key=hdr["reqcode"], target_code=s.code)
        snapshot(s, was_new)
        if not was_new:
            s.main_content = (hdr["detail"] or hdr["ig"] or s.main_content)[:500]
            s.updated_by = batch.created_by
            log("-", 0, LogLevel.INFO, "survey_update", f"Cập nhật phiếu đã có {s.code}", ref_key=hdr["reqcode"], target_code=s.code)
        survey_cache[survey_key] = s
        return s

    def read_hdr(ws, r, sheet):
        bp, received = _s(_cell(ws, r, "D")), _d(_cell(ws, r, "B"))
        ig = cat(_cell(ws, r, "F"), ig_map, "Phân loại", sheet, r)
        detail = _s(_cell(ws, r, "G"))
        reqk = _req_key(bp, received, ig, detail)
        return {"ig": ig, "received": received, "due": _d(_cell(ws, r, "C")), "bp": bp, "detail": detail, "reqk": reqk,
                "reqcode": gen_reqcode(bp, received, reqk, _s(_cell(ws, r, "E"))), "qty": _n(_cell(ws, r, "H")),
                "uom": cat(_cell(ws, r, "I"), unit_map, "ĐVT", sheet, r), "rate": _n(_cell(ws, r, "J")),
                "nspt": _s(_cell(ws, r, "K"))}

    n3 = _last_row(ws3) - HEADER_ROW if ws3 else 0
    n4 = _last_row(ws4) - HEADER_ROW if ws4 else 0
    batch.sheet_info = json.dumps({"rows_ncc": n3, "rows_sp": n4}, ensure_ascii=False)

    # ---- PRE-PASS: upsert NCC danh mục + dựng map viết tắt -> MST ----
    if ws3:
        for r in range(DATA_START, _last_row(ws3) + 1):
            raw, tax = _s(_cell(ws3, r, "O")), _s(_cell(ws3, r, "Q"))
            if raw and tax:
                abbr_mst.setdefault(_ncode(raw), tax)
            if raw:
                _upsert_supplier(db, batch, raw, canon_code(raw, tax), tax, ws3, r, log)

    # ---- PASS A: sheet 4 (SP) -> tạo phiếu + dòng SP ----
    if ws4:
        for r in range(DATA_START, _last_row(ws4) + 1):
            hdr = read_hdr(ws4, r, "4.KS-SP")
            raw = _s(_cell(ws4, r, "O"))
            code = canon_code(raw, resolve_mst(raw))
            if not hdr["ig"] or not raw:
                if _s(_cell(ws4, r, "A")):
                    log("4.KS-SP", r, LogLevel.ERROR, "missing_key", "Thiếu Phân loại hoặc NCC"); counts["skipped"] += 1
                continue
            mst = resolve_mst(raw)
            reqk = hdr["reqk"]
            vtbb = _s(_cell(ws4, r, "P"))
            is_vtbb = _ncode(vtbb) in prod_codes
            survey_key = f"VTBB::{_ncode(vtbb)}" if is_vtbb else f"REQ::{reqk}"
            s = get_survey(survey_key, hdr)
            if is_vtbb and not s.has_product_code:  # loại 1: đánh dấu phiếu đã có mã SP trong hệ thống
                p = prod_map.get(_ncode(vtbb))
                s.has_product_code = True
                s.item_code = p.code if p else vtbb
                s.item_name = p.name if p else ""
                if p and p.name and not (s.main_content or "").strip():
                    s.main_content = p.name[:500]
            prodkey_full.setdefault((reqk, mst), s.id)
            if is_vtbb:  # loại 1: cho khớp dòng NCC không cần trùng ngày tiếp nhận
                prodkey_loose.setdefault((_ncode(hdr["ig"]), _ncode(hdr["detail"]), mst), s.id)
            lk = f"{reqk}|{mst}"
            line = db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == s.id,
                                                      SurveyProductLine.import_line_key == lk).first()
            pname = _s(_cell(ws4, r, "Q")) or _s(_cell(ws4, r, "R"))
            data = dict(
                import_line_key=lk, request_qty=hdr["qty"], contact_date=_d(_cell(ws4, r, "L")), reply_date=_d(_cell(ws4, r, "M")),
                result_date=_d(_cell(ws4, r, "N")), supplier_code=code, internal_code=vtbb, product_name=pname,
                spec=_s(_cell(ws4, r, "S")), origin=_s(_cell(ws4, r, "T")),
                quote_unit=cat(_cell(ws4, r, "U"), unit_map, "ĐVT", "4.KS-SP", r), moq=_n(_cell(ws4, r, "V")),
                price_by_volume=_n(_cell(ws4, r, "W")), volume_range=_s(_cell(ws4, r, "X")), vat=_vat(_cell(ws4, r, "Y")),
                amount=_n(_cell(ws4, r, "Z")), internal_unit=cat(_cell(ws4, r, "AA"), unit_map, "ĐVT", "4.KS-SP", r),
                amount_converted=_n(_cell(ws4, r, "AB")), shipping_cost=_n(_cell(ws4, r, "AC")),
                delivery_time=_s(_cell(ws4, r, "AD")), delivery_place=_s(_cell(ws4, r, "AE")), quote_file=_s(_cell(ws4, r, "AF")),
                sample_ready=_b(_cell(ws4, r, "AG")), sample_date=_d(_cell(ws4, r, "AH")), sample_qty=_n(_cell(ws4, r, "AI")),
                lab_result=_s(_cell(ws4, r, "AJ")), nspt_note=_s(_cell(ws4, r, "AK")))
            data, _t = _fit(SurveyProductLine, data)
            appr, appr_note = _approve(_cell(ws4, r, "AL"))
            data["line_approve"] = appr
            data["line_approve_note"] = _s(_cell(ws4, r, "AM")) or appr_note
            dup = ("P", lk) in seen_lk
            seen_lk.add(("P", lk))
            if line:
                for k, v in data.items():
                    setattr(line, k, v)
                counts["updated"] += 1
                if dup:
                    log("4.KS-SP", r, LogLevel.WARNING, "duplicate_line",
                        f"Dòng SP trùng khoá (Mã YC {hdr['reqcode']} + MST {mst}) — gộp, ghi đè dòng trước", ref_key=code, target_code=s.code)
            else:
                db.add(SurveyProductLine(survey_id=s.id, created_by=batch.created_by, updated_by=batch.created_by, **data))
                db.flush(); counts["created"] += 1

    # ---- PASS B: sheet 3 (NCC) -> phân phối dòng NCC ----
    if ws3:
        for r in range(DATA_START, _last_row(ws3) + 1):
            hdr = read_hdr(ws3, r, "3.KS-NCC")
            raw, tax = _s(_cell(ws3, r, "O")), _s(_cell(ws3, r, "Q"))
            code = canon_code(raw, tax)
            if not hdr["ig"] or not raw:
                if _s(_cell(ws3, r, "A")):
                    log("3.KS-NCC", r, LogLevel.ERROR, "missing_key", "Thiếu Phân loại hoặc NCC"); counts["skipped"] += 1
                continue
            mst = resolve_mst(raw, tax)
            reqk = hdr["reqk"]
            sid = (prodkey_full.get((reqk, mst))
                   or prodkey_loose.get((_ncode(hdr["ig"]), _ncode(hdr["detail"]), mst)))
            if sid:
                s = db.get(Survey, sid)
            else:
                log("3.KS-NCC", r, LogLevel.REVIEW, "no_product_match",
                    f"NCC (MST {mst}) không khớp dòng SP nào của yêu cầu — tạo phiếu trống", ref_key=code)
                s = get_survey(f"REQ::{reqk}", hdr)
            lk = f"{reqk}|{mst}"
            line = db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == s.id,
                                                       SurveySupplierLine.import_line_key == lk).first()
            catsup = db.query(Supplier).filter(Supplier.code == code).first()
            data = dict(
                import_line_key=lk, contact_date=_d(_cell(ws3, r, "L")), reply_date=_d(_cell(ws3, r, "M")),
                result_date=_d(_cell(ws3, r, "N")), supplier_code=code,
                supplier_name=_s(_cell(ws3, r, "P")) or (catsup.name if catsup else ""), tax_code=mst,
                reg_address=_s(_cell(ws3, r, "R")) or (catsup.address if catsup else ""),
                warehouse_address=_s(_cell(ws3, r, "S")), google_maps=_s(_cell(ws3, r, "T")),
                contact_person=_s(_cell(ws3, r, "U")), contact_phone=_s(_cell(ws3, r, "V")), supply_group=_s(_cell(ws3, r, "W")),
                quote_folder=_s(_cell(ws3, r, "X")), source_of_information=_s(_cell(ws3, r, "Y")),
                production_tech=_s(_cell(ws3, r, "Z")), production_time=_s(_cell(ws3, r, "AA")), nvkd_eval=_s(_cell(ws3, r, "AB")),
                invoice_policy=_s(_cell(ws3, r, "AC")), reliability=_s(_cell(ws3, r, "AD")), delivery_policy=_s(_cell(ws3, r, "AE")),
                debt_policy=_s(_cell(ws3, r, "AF")), defect_return=_s(_cell(ws3, r, "AG")), nspt_reason=_s(_cell(ws3, r, "AH")))
            data, _t = _fit(SurveySupplierLine, data)
            appr, appr_note = _approve(_cell(ws3, r, "AI"))
            data["line_approve"] = appr
            data["line_approve_note"] = _s(_cell(ws3, r, "AJ")) or appr_note
            dup = ("S", lk) in seen_lk
            seen_lk.add(("S", lk))
            if line:
                for k, v in data.items():
                    setattr(line, k, v)
                counts["updated"] += 1
                if dup:
                    log("3.KS-NCC", r, LogLevel.WARNING, "duplicate_line",
                        f"Dòng NCC trùng khoá (Mã YC {hdr['reqcode']} + MST {mst}) — gộp, ghi đè dòng trước", ref_key=code, target_code=s.code)
            else:
                db.add(SurveySupplierLine(survey_id=s.id, created_by=batch.created_by, updated_by=batch.created_by, **data))
                db.flush(); counts["created"] += 1

    if apply:
        db.commit()
    else:
        db.rollback()
    _persist(db, batch, counts, logs, changes if apply else [], n3 + n4)


def _upsert_supplier(db, batch, raw, code, tax, ws, r, log):
    # raw = tên viết tắt gốc trong file; code = mã danh mục sau canon.
    # MST đã có NCC trong hệ thống nhưng file ghi tên viết tắt khác -> LẤY NCC HỆ THỐNG làm chuẩn (ghi đè).
    if tax:
        by_tax = db.query(Supplier).filter(Supplier.tax_code == tax).first()
        if by_tax and _ncode(by_tax.code) != _ncode(raw):
            log("3.KS-NCC", r, LogLevel.INFO, "ncc_by_mst",
                f"MST {tax} khớp NCC hệ thống '{by_tax.code}' — dùng NCC hệ thống, bỏ tên viết tắt '{raw}' trong file", ref_key=by_tax.code)
            return
    sup = db.query(Supplier).filter(Supplier.code == code).first()
    if sup:
        for attr, val in (("name", _s(_cell(ws, r, "P"))), ("tax_code", tax),
                          ("address", _s(_cell(ws, r, "R"))), ("payment_terms", _s(_cell(ws, r, "AF"))),
                          ("phone", _s(_cell(ws, r, "V"))), ("contact_person", _s(_cell(ws, r, "U")))):
            if val and not (getattr(sup, attr) or "").strip():
                setattr(sup, attr, val)
    else:
        db.add(Supplier(code=code, name=_s(_cell(ws, r, "P")), tax_code=tax, address=_s(_cell(ws, r, "R")),
                        payment_terms=_s(_cell(ws, r, "AF")), phone=_s(_cell(ws, r, "V")),
                        contact_person=_s(_cell(ws, r, "U")), supplier_type="goods", is_active=True,
                        created_by=batch.created_by, updated_by=batch.created_by))
        db.flush()
        log("3.KS-NCC", r, LogLevel.INFO, "ncc_created", f"Tạo NCC mới '{code}'", ref_key=code)


def _persist(db, batch, counts, logs, changes, total_rows):
    from .model import ImportLog
    b = db.get(ImportBatch, batch.id)
    b.total_rows = total_rows
    b.created_count = counts["created"]; b.updated_count = counts["updated"]; b.skipped_count = counts["skipped"]
    b.warning_count = counts["warning"]; b.review_count = counts["review"]; b.error_count = counts["error"]
    for lg in logs:
        db.add(ImportLog(batch_id=b.id, sheet=lg["sheet"], row_no=lg["row_no"], level=lg["level"],
                         category=lg["category"], message=lg["message"][:60000], ref_key=lg["ref_key"][:120],
                         target_code=lg["target_code"][:50], created_by=b.created_by))
    for ch in changes:
        db.add(ImportChange(batch_id=b.id, survey_id=ch["survey_id"], was_new=1 if ch["was_new"] else 0,
                            snapshot=ch["snapshot"], created_by=b.created_by))
    b.status = ImportStatus.DONE
    b.finished_at = datetime.utcnow()
    db.commit()
