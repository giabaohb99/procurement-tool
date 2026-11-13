"""Nhập BÁO GIÁ NCC vào phiếu khảo sát đang mở hoặc YCBG đang khảo sát (ai-CR-238).

Luồng: người dùng gửi tệp báo giá (PDF / ảnh) cho ứng dụng AI (Claude / ChatGPT qua cổng MCP, Trợ lý web). AI tự đọc
NCC, số + ngày báo giá, các dòng (mã / tên hàng, đơn giá, VAT, ĐVT, MOQ, thời gian giao, hạn công nợ, ghi chú) rồi gọi
`draft_supplier_quote`: tool tìm phiếu khảo sát phù hợp, khớp từng dòng, KHÔNG ghi gì. Người dùng xem bảng khớp / không
khớp / GHI ĐÈ giá / ĐVT lệch rồi gật → `confirm_draft` kind=`supplier_quote` → `confirm_quote` ghi bằng ĐÚNG service
lưu phiếu khảo sát của màn web (`survey.service.update_survey` như nút Lưu; YCBG chưa có phiếu khảo sát thì
`create_survey` gắn YCBG như nút Lập phiếu khảo sát từ YCBG).

Giá NCC của YCBG nằm ở dòng SP của phiếu khảo sát gắn YCBG (`Survey.survey_request_id`); duyệt dòng xong mới thành
phương án của YCBG (`sync_options_from_surveys`) — nên "nhập vào YCBG" = nhập vào phiếu khảo sát Nháp của YCBG đó.

Chọn phiếu:
1. Có `survey_code` → đúng phiếu đó; có `survey_request_code` → phiếu khảo sát đang mở của YCBG (nhiều phiếu thì chọn
   phiếu có nhiều dòng khớp nhất), chưa có thì lập phiếu Nháp mới (YCBG phải Đã duyệt / Đang xử lý).
2. Không nêu phiếu → các phiếu khảo sát đang mở trong phạm vi GHI, phiếu có nhiều dòng khớp nhất (cùng NCC trước), cùng
   mức thì phiếu của chính người hỏi (người phụ trách). Không phiếu nào khớp → hỏi lại kèm phiếu mở + YCBG người hỏi đang
   phụ trách dòng.

Khớp dòng: cùng hàng (mã trùng mã SP theo NCC / mã VTBB đầu phiếu, hoặc tên trùng sau khi bỏ dấu) VÀ cùng NCC → sửa dòng
đó; cùng hàng mà NCC chưa có dòng → thêm dòng mới; không cùng hàng → không khớp, không ghi (phiếu người dùng tự nêu thì
thêm dòng mới, có cảnh báo). Dòng đã có giá khác → cảnh báo GHI ĐÈ; ĐVT báo giá khác ĐVT dòng / đầu phiếu → cảnh báo.

Quyền: cần `survey.write` + `supplier.read` (báo giá nêu tên NCC); lập phiếu mới cần thêm `survey.create` và YCBG trong
phạm vi đọc. Chỉ phiếu Nháp / Bị trả lại (đúng chốt của `update_survey`). Lúc xác nhận kiểm lại quyền, phạm vi `write`
(đúng action của `PATCH /api/surveys/{id}`), trạng thái, và chặn khi dòng của phiếu đã đổi sau lúc soạn (lưu phiếu trên
web dựng lại mọi dòng nên xác nhận hai lần không ghi đôi). Tệp báo giá không gửi qua AI: trả `attach_url` mở phiếu trên
web để người dùng tự đính.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal

from app.core.scoping import apply_scope
from app.modules.survey.model import Survey, SurveyProductLine
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

from .base import ToolContext, ToolSpec, denied
from .po_receipt_tool import _core_name, _fold, _text, parse_date, vn

KIND = "supplier_quote"
EDITABLE_STATUSES = ("draft", "rejected")          # = survey.service.update_survey
OPEN_REQUEST_STATUSES = ("approved", "processing")  # YCBG đang khảo sát (= lifecycle_service.TRANSFERABLE_STATUSES)
MAX_LINES = 50
MAX_CANDIDATES = 200
MAX_PRICE = 1e13
MIN_NAME_OVERLAP = 6
SURVEY_URL = "/procurement/surveys/{id}"
REQUEST_URL = "/procurement/survey-requests/{id}"
ATTACH_NOTE = ("Tệp báo giá không gửi được qua AI: đưa người dùng `attach_url` — bấm để mở phiếu khảo sát trên web và tự "
               "đính tệp báo giá.")
DEBT_OPTIONS = ("Tiền mặt", "Công nợ 30 ngày", "Công nợ 60 ngày", "Công nợ 90 ngày", "Trả trước")   # ô chọn trên web
_SURVEY_STATUS = {"draft": "Nháp", "rejected": "Bị trả lại", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
                  "cancelled": "Đã hủy"}
_REQUEST_STATUS = {"draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt", "processing": "Đang xử lý",
                   "survey_done": "Đã khảo sát", "pr_created": "Đã tạo YCMH", "done": "Hoàn thành",
                   "rejected": "Bị trả lại", "cancelled": "Đã hủy"}
_THOUSANDS = re.compile(r"^\d{1,3}([.,]\d{3})+$")
#  Trường giá của dòng SP mà báo giá ghi vào — (khóa, nhãn cho câu cảnh báo).
_FIELDS = (("price_by_volume", "đơn giá"), ("vat", "VAT"), ("quote_unit", "ĐVT"), ("moq", "MOQ"),
           ("delivery_time", "thời gian giao"), ("debt_policy", "công nợ"), ("note", "ghi chú"))
_NUMERIC = frozenset({"price_by_volume", "vat", "moq"})


# ── đọc tham số ──────────────────────────────────────────────────────────────────────────
def parse_number(v, high: float = MAX_PRICE) -> float | None:
    """Số trên báo giá: số, hoặc chuỗi kiểu Việt "1.150.000" / "1,150" (nghìn) / "12,5" (lẻ). Sai / âm → None."""
    if isinstance(v, bool) or v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        n = float(v)
    else:
        s = str(v).strip().replace(" ", "").replace("%", "")[:30]
        s = s.replace(".", "").replace(",", "") if _THOUSANDS.match(s) else s.replace(",", ".")
        try:
            n = float(s)
        except ValueError:
            return None
    return round(n, 4) if 0 <= n < high else None


def debt_option(raw) -> tuple[str, str]:
    """Hạn công nợ trên báo giá → giá trị ô chọn của web; không quy được thì giữ chữ báo giá + cảnh báo."""
    text = _text(raw, 100)
    if not text:
        return "", ""
    f = _fold(text)
    if hit := next((o for o in DEBT_OPTIONS if _fold(o) == f), None):
        return hit, ""
    if m := re.search(r"\b(30|60|90)\b", f):
        return f"Công nợ {m.group(1)} ngày", ""
    if re.search(r"tien mat|\bcod\b|thanh toan ngay|khi nhan hang", f):
        return "Tiền mặt", ""
    if re.search(r"tra truoc|tam ung|dat coc|chuyen khoan truoc", f):
        return "Trả trước", ""
    return text, f"công nợ **{text}** không có trong ô chọn của web ({', '.join(DEBT_OPTIONS)}) — giữ nguyên chữ báo giá"


def _parse_lines(args: dict) -> tuple[list[dict], list[str]]:
    raw = args.get("lines")
    if not isinstance(raw, list) or not raw:
        return [], ["Thiếu các dòng báo giá (`lines`: mỗi dòng mã hoặc tên hàng + đơn giá)."]
    if len(raw) > MAX_LINES:
        return [], [f"Một lần nhập tối đa {MAX_LINES} dòng báo giá — chia làm nhiều lượt."]
    out, errors = [], []
    for i, ln in enumerate(raw, 1):
        if not isinstance(ln, dict):
            errors.append(f"Dòng {i} không đúng dạng.")
            continue
        code, name = _text(ln.get("product_code"), 50).upper(), _text(ln.get("product_name"), 255)
        price = parse_number(ln.get("unit_price"))
        if not code and not name:
            errors.append(f"Dòng {i}: thiếu mã hoặc tên hàng.")
        if price is None or price <= 0:
            errors.append(f"Dòng {i} ({code or name or '?'}): đơn giá phải là số dương.")
        vat = None
        if ln.get("vat") not in (None, ""):
            vat = parse_number(ln.get("vat"), 100)
            if vat is None:
                errors.append(f"Dòng {i} ({code or name}): VAT phải từ 0 tới dưới 100 (%).")
            elif 0 < vat < 1:
                vat = round(vat * 100, 2)          # 0,08 → 8 (%)
        moq = parse_number(ln.get("moq"), 1e12) if ln.get("moq") not in (None, "") else None
        debt, debt_warn = debt_option(ln.get("debt_term"))
        out.append({"idx": i, "code": code, "name": name, "price": price, "vat": vat, "uom": _text(ln.get("uom"), 25),
                    "moq": moq, "delivery_time": _text(ln.get("delivery_time"), 100), "debt": debt,
                    "debt_warn": debt_warn, "note": _text(ln.get("note"), 2000)})
    return out, errors


def _label(q: dict) -> str:
    return q["code"] or q["name"]


# ── NCC ──────────────────────────────────────────────────────────────────────────────────
def _resolve_supplier(ctx: ToolContext, raw) -> tuple[tuple[str, str] | None, dict | None, str]:
    """NCC theo mã / MST / tên (bỏ dấu, bỏ chữ "Công ty TNHH"…) trong danh mục. Không có trong danh mục → ghi tên gõ tay
    như ô NCC gõ tay của form web, kèm cảnh báo."""
    from app.modules.supplier.model import Supplier

    want = _text(raw)
    if not want:
        return None, {"error": "Thiếu tên hoặc mã NCC (ghi trên báo giá)."}, ""
    rows = ctx.db.query(Supplier.code, Supplier.name, Supplier.tax_code).all()
    up, core = want.upper(), _core_name(want)
    hit = [(c, n) for c, n, t in rows if (c or "").upper() == up or (t or "").strip() == want]
    if not hit and len(core) >= 3:
        hit = [(c, n) for c, n, _t in rows
               if core == _core_name(n) or core in _core_name(n) or (len(_core_name(n)) >= 3 and _core_name(n) in core)]
    hit = list(dict.fromkeys(hit))
    if len(hit) == 1:
        return (hit[0][0], hit[0][1] or hit[0][0]), None, ""
    if hit:
        return None, {"need_choice": "nhà cung cấp", "options": [f"{n} ({c})" for c, n in sorted(hit)][:10],
                      "note": f"Có nhiều NCC khớp **{want}**. Hỏi người dùng MỘT câu, đưa danh sách đánh số, rồi gọi lại "
                              "tool với đúng mã NCC."}, ""
    typed = want[:50]
    return (typed, want), None, (f"NCC **{want}** chưa có trong danh mục NCC — dòng ghi tên gõ tay như ô NCC gõ tay trên "
                                 "web; nên tạo NCC trong danh mục rồi chọn lại trên phiếu.")


def _same_supplier(line_supplier: str, sup: tuple[str, str]) -> bool:
    have = (line_supplier or "").strip()
    if not have:
        return False
    if have.upper() == sup[0].upper():
        return True
    core = _core_name(have)
    return bool(core) and core in (_core_name(sup[0]), _core_name(sup[1]))


def _same_product(q: dict, code: str, name: str) -> bool:
    code = (code or "").strip().upper()
    if q["code"] and code and q["code"] == code:
        return True
    a, b = _fold(q["name"]), _fold(name)
    if not a or not b:
        return False
    return a == b or (min(len(a), len(b)) >= MIN_NAME_OVERLAP and (a in b or b in a))


# ── lập phương án ghi ────────────────────────────────────────────────────────────────────
def _num(v) -> float:
    return float(v) if isinstance(v, Decimal) else float(v or 0)


def _snapshot(p: SurveyProductLine) -> dict:
    return {k: (_num(getattr(p, k)) if k in _NUMERIC else (getattr(p, k) or "")) for k, _l in _FIELDS}


def _after(q: dict, ref_unit: str) -> dict:
    out = {"price_by_volume": q["price"]}
    if q["vat"] is not None:
        out["vat"] = q["vat"]
    if q["uom"] or ref_unit:
        out["quote_unit"] = q["uom"] or ref_unit
    if q["moq"] is not None:
        out["moq"] = q["moq"]
    for key, src in (("delivery_time", "delivery_time"), ("debt_policy", "debt"), ("note", "note")):
        if q[src]:
            out[key] = q[src]
    return out


def _fmt(key: str, value) -> str:
    if key == "vat":
        return f"{vn(value)}%"
    return vn(value) if key in _NUMERIC else (str(value) or "trống")


def _overwrites(before: dict, after: dict) -> list[str]:
    out = []
    for key, label in _FIELDS:
        if key not in after:
            continue
        old, new = before.get(key), after[key]
        empty = (old or 0) == 0 if key in _NUMERIC else not str(old or "").strip()
        same = abs(_num(old) - _num(new)) < 1e-6 if key in _NUMERIC else _fold(old) == _fold(new)
        if not empty and not same:
            out.append(f"{label} {_fmt(key, old)} → {_fmt(key, new)}")
    return out


def _uom_problem(q: dict, ref: str, where: str) -> str:
    if q["uom"] and ref and _fold(q["uom"]) != _fold(ref):
        return f"Dòng {q['idx']} ({_label(q)}): ĐVT báo giá **{q['uom']}** khác ĐVT {where} **{ref}** — đơn giá không so thẳng được."
    return ""


class _Plan:
    """Kết quả khớp một bộ dòng báo giá vào MỘT phiếu (có sẵn hoặc sắp lập)."""

    def __init__(self):
        self.rows: list[dict] = []
        self.matched: list[dict] = []
        self.unmatched: list[dict] = []
        self.overwrites: list[str] = []
        self.uom: list[str] = []
        self.warnings: list[str] = []

    @property
    def score(self) -> int:
        return sum(2 if r["op"] == "update" else 1 for r in self.rows if not r.get("new_item"))


def _plan_survey(s: Survey, plines: list[SurveyProductLine], sup: tuple[str, str], lines: list[dict],
                 explicit: bool, request_line: SurveyRequestLine | None = None) -> _Plan:
    plan, used = _Plan(), set()
    for q in lines:
        same = [p for p in plines if _same_product(q, p.internal_code, p.product_name)]
        header = _same_product(q, s.item_code, s.item_name) if (s.item_code or s.item_name) else False
        mine = [p for p in same if _same_supplier(p.supplier_code, sup) and p.id not in used]
        if mine:
            p = mine[0]
            used.add(p.id)
            before = _snapshot(p)
            row = {"op": "update", "line_id": p.id, "line_no": plines.index(p) + 1, "product": _label(q),
                   "product_name": p.product_name or "", "internal_code": p.internal_code or "",
                   "supplier_code": p.supplier_code or "", "before": before,
                   "after": _after(q, p.quote_unit or ""), "quote_idx": q["idx"]}
            if over := _overwrites(before, row["after"]):
                plan.overwrites.append(f"GHI ĐÈ dòng {row['line_no']} ({_label(q)}, {sup[1]}): " + "; ".join(over))
            if len(mine) > 1:
                plan.warnings.append(f"Dòng {q['idx']} ({_label(q)}): phiếu có {len(mine)} dòng cùng NCC cùng hàng — ghi "
                                     f"vào dòng {row['line_no']}.")
            ref, where = p.quote_unit or s.uom or "", "dòng khảo sát" if p.quote_unit else "đầu phiếu"
        elif same or header or explicit:
            base = same[0] if same else None
            #  Hàng đã có trên phiếu thì giữ đúng tên phiếu đang dùng (so phương án cho thẳng hàng), không lấy chữ báo giá.
            name = ((base.product_name if base else "") or (s.item_name if header else "") or q["name"]
                    or s.item_name or q["code"])
            row = {"op": "add", "line_id": 0, "line_no": 0, "product": _label(q), "product_name": name[:255],
                   "internal_code": q["code"] or (base.internal_code if base else "") or "",
                   "supplier_code": sup[0], "before": {}, "quote_idx": q["idx"],
                   "spec": (base.spec if base else "") or (request_line.requirement_detail if request_line else ""),
                   "origin": (base.origin if base else "") or "",
                   "request_qty": _num(s.request_qty) or (_num(request_line.request_qty) if request_line else 0)}
            ref = (base.quote_unit if base else "") or s.uom or (request_line.uom if request_line else "") or ""
            where = "dòng YCBG" if request_line and not s.id else ("dòng khảo sát" if base and base.quote_unit
                                                                      else "đầu phiếu")
            row["after"] = _after(q, ref)
            if not (same or header) and s.id:
                row["new_item"] = True
                plan.warnings.append(f"Dòng {q['idx']} ({_label(q)}): phiếu {s.code} chưa có hàng này — sẽ THÊM dòng mới.")
        else:
            plan.unmatched.append({"quote_line": q["idx"], "product": _label(q), "product_name": q["name"],
                                   "unit_price": q["price"], "reason": f"phiếu {s.code} không có hàng này — không ghi"})
            continue
        if problem := _uom_problem(q, ref, where):
            plan.uom.append(problem)
        if q["debt_warn"]:
            plan.warnings.append(f"Dòng {q['idx']} ({_label(q)}): {q['debt_warn']}.")
        if row["op"] == "add" and q["vat"] is None:
            plan.warnings.append(f"Dòng {q['idx']} ({_label(q)}): báo giá không ghi VAT — dòng mới để VAT 0%, hỏi lại "
                                 "người dùng nếu cần.")
        plan.rows.append(row)
        plan.matched.append({"quote_line": q["idx"], "product": _label(q), "op": row["op"],
                             "survey_line": row["line_no"] or "mới", "unit_price": q["price"]})
    return plan


# ── tìm phiếu ────────────────────────────────────────────────────────────────────────────
def _editable(ctx: ToolContext):
    q = apply_scope(ctx.db.query(Survey), Survey, "survey", ctx.user, ctx.profile, "write")
    return q.filter(Survey.status.in_(EDITABLE_STATUSES))


def _lines_of(db, ids: list[int]) -> dict[int, list[SurveyProductLine]]:
    out: dict[int, list[SurveyProductLine]] = {i: [] for i in ids}
    if ids:
        for p in (db.query(SurveyProductLine).filter(SurveyProductLine.survey_id.in_(ids))
                  .order_by(SurveyProductLine.id)):
            out[p.survey_id].append(p)
    return out


def _best(ctx: ToolContext, surveys: list[Survey], sup, lines, explicit: bool) -> tuple[Survey | None, _Plan | None, list]:
    """Phiếu có nhiều dòng khớp nhất; cùng mức thì phiếu của chính người hỏi. Trả (phiếu, kế hoạch, các phiếu hòa)."""
    by_id = _lines_of(ctx.db, [s.id for s in surveys])
    scored = []
    for s in surveys:
        plan = _plan_survey(s, by_id[s.id], sup, lines, explicit=False)
        scored.append(((plan.score, s.created_by == ctx.user.id), s, plan))
    scored = [x for x in scored if x[0][0] > 0]
    if not scored:
        if explicit and len(surveys) == 1:
            s = surveys[0]
            return s, _plan_survey(s, by_id[s.id], sup, lines, explicit=True), []
        return None, None, []
    scored.sort(key=lambda x: (x[0], x[1].id), reverse=True)
    top = scored[0]
    ties = [x[1] for x in scored if x[0] == top[0]]
    if len(ties) > 1:
        return None, None, ties
    plan = _plan_survey(top[1], by_id[top[1].id], sup, lines, explicit=explicit) if explicit else top[2]
    return top[1], plan, []


def _survey_option(s: Survey) -> str:
    what = s.item_name or s.item_code or s.item_group or s.main_content or ""
    return f"{s.code} · {_SURVEY_STATUS.get(s.status, s.status)}{' · ' + what[:80] if what else ''}"


def _choose(what: str, options: list[str], note: str) -> dict:
    return {"need_choice": what, "options": options[:10], "note": note}


def _request_candidates(ctx: ToolContext) -> list[str]:
    """YCBG đang khảo sát có dòng do chính người hỏi phụ trách (mã NSTM) — gợi ý khi không phiếu khảo sát nào khớp."""
    emp = (ctx.profile or {}).get("emp_code") or ""
    if not emp:
        return []
    q = apply_scope(ctx.db.query(SurveyRequest), SurveyRequest, "survey_request", ctx.user, ctx.profile, "read")
    sub = ctx.db.query(SurveyRequestLine.survey_request_id).filter(SurveyRequestLine.assignee == emp)
    rows = (q.filter(SurveyRequest.status.in_(OPEN_REQUEST_STATUSES), SurveyRequest.id.in_(sub))
            .order_by(SurveyRequest.id.desc()).limit(10).all())
    return [f"YCBG {r.code} · {_REQUEST_STATUS.get(r.status, r.status)} · {(r.purpose or '')[:80]}" for r in rows]


def _target_by_code(ctx: ToolContext, code: str, sup, lines):
    s = _editable(ctx).filter(Survey.code == code).first() if code else None
    if s is None:
        other = (apply_scope(ctx.db.query(Survey), Survey, "survey", ctx.user, ctx.profile, "write")
                 .filter(Survey.code == code).first())
        if other is not None:
            return None, None, {"error": f"Phiếu khảo sát {other.code} đang ở trạng thái "
                                         f"{_SURVEY_STATUS.get(other.status, other.status)} — chỉ nhập giá được khi phiếu ở "
                                         "Nháp hoặc Bị trả lại (như form web). Không ghi gì."}
        return None, None, {"error": f"Không thấy phiếu khảo sát {code} trong phạm vi bạn được ghi. Hỏi lại người dùng "
                                     "mã phiếu (KS…)."}
    s_, plan, _t = _best(ctx, [s], sup, lines, explicit=True)
    return s_, plan, None


def _request_target(ctx: ToolContext, code: str, item_group: str, sup, lines):
    """YCBG theo mã: phiếu khảo sát đang mở gắn YCBG, chưa có thì kế hoạch lập phiếu mới. Trả (phiếu, kế hoạch, mới, lỗi)."""
    if not ctx.can("survey_request"):
        return None, None, None, denied("yêu cầu báo giá (YCBG)")
    sr = (apply_scope(ctx.db.query(SurveyRequest), SurveyRequest, "survey_request", ctx.user, ctx.profile, "read")
          .filter(SurveyRequest.code == code).first())
    if sr is None:
        return None, None, None, {"error": f"Không thấy YCBG {code} trong phạm vi bạn được xem. Hỏi lại người dùng mã "
                                           "YCBG."}
    linked = _editable(ctx).filter(Survey.survey_request_id == sr.id)
    if item_group:
        linked = linked.filter(Survey.item_group == item_group)
    linked = linked.order_by(Survey.id.desc()).all()
    if linked:
        s, plan, ties = _best(ctx, linked, sup, lines, explicit=True)
        if s is None and not ties and len(linked) > 1:
            ties = linked
        if ties:
            return None, None, None, _choose("phiếu khảo sát", [_survey_option(x) for x in ties],
                                             f"YCBG {sr.code} có nhiều phiếu khảo sát đang mở. Hỏi người dùng nhập vào "
                                             "phiếu nào rồi gọi lại với survey_code.")
        return s, plan, None, None
    if sr.status not in OPEN_REQUEST_STATUSES:
        return None, None, None, {"error": f"YCBG {sr.code} đang ở trạng thái "
                                           f"{_REQUEST_STATUS.get(sr.status, sr.status)} và không có phiếu khảo sát nào "
                                           "đang mở — chỉ lập phiếu khảo sát cho YCBG Đã duyệt / Đang xử lý. Không ghi gì."}
    if not ctx.can("survey", "create"):
        return None, None, None, denied("lập phiếu khảo sát mới cho YCBG")
    req_lines = ctx.db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sr.id) \
        .order_by(SurveyRequestLine.id).all()
    pick = [x for x in req_lines if not item_group or _fold(x.item_group) == _fold(item_group)]
    groups = list(dict.fromkeys(x.item_group or "" for x in pick))
    if not pick:
        return None, None, None, {"error": f"YCBG {sr.code} không có dòng phân loại **{item_group}**."}
    if len(groups) > 1:
        return None, None, None, _choose("phân loại dòng YCBG", [g or "(trống)" for g in groups],
                                         f"YCBG {sr.code} có nhiều phân loại; mỗi phiếu khảo sát cho một phân loại. Hỏi "
                                         "người dùng báo giá này cho phân loại nào rồi gọi lại với item_group.")
    line = pick[0]
    fresh = Survey(id=0, code="(phiếu mới)", item_group=line.item_group or "", uom=line.uom or "",
                   request_qty=line.request_qty or 0)
    plan = _plan_survey(fresh, [], sup, lines, explicit=True, request_line=line)
    linked_ids = sorted(i for (i,) in ctx.db.query(Survey.id).filter(Survey.survey_request_id == sr.id,
                                                                     Survey.is_deleted.is_(False)))
    new = {"survey_request_id": sr.id, "survey_request_code": sr.code, "survey_request_line_id": line.id,
           "item_group": line.item_group or "", "linked_before": linked_ids}
    return None, plan, new, None


def _draft_ref(draft: dict) -> str:
    raw = json.dumps({k: draft.get(k) for k in ("supplier_code", "quote_no", "survey_id", "new_survey", "rows")},
                     sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(raw.encode()).hexdigest()[:10]


def draft_supplier_quote(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("survey", "write") or not ctx.can("supplier"):
        return denied("nhập báo giá NCC vào phiếu khảo sát")
    lines, errors = _parse_lines(args)
    quote_date = parse_date(args.get("quote_date")) if args.get("quote_date") else ""
    if args.get("quote_date") and not quote_date:
        errors.append("Ngày báo giá sai dạng (`quote_date` YYYY-MM-DD hoặc DD/MM/YYYY).")
    if errors:
        return {"error": " ".join(errors)}
    sup, problem, sup_warn = _resolve_supplier(ctx, args.get("supplier"))
    if problem:
        return problem
    survey_code = _text(args.get("survey_code"), 50).upper()
    request_code = _text(args.get("survey_request_code"), 50).upper()
    item_group = _text(args.get("item_group"), 100)
    new = None
    if survey_code:
        s, plan, err = _target_by_code(ctx, survey_code, sup, lines)
    elif request_code:
        s, plan, new, err = _request_target(ctx, request_code, item_group, sup, lines)
    else:
        cands = _editable(ctx).order_by(Survey.id.desc()).limit(MAX_CANDIDATES).all()
        s, plan, ties = _best(ctx, cands, sup, lines, explicit=False)
        err = None
        if ties:
            err = _choose("phiếu khảo sát", [_survey_option(x) for x in ties],
                          "Có nhiều phiếu khảo sát đang mở khớp báo giá ngang nhau. Hỏi người dùng MỘT câu nhập vào phiếu "
                          "nào rồi gọi lại với survey_code.")
        elif s is None:
            mine = [_survey_option(x) for x in cands if x.created_by == ctx.user.id][:5]
            err = _choose("phiếu khảo sát hoặc YCBG", mine + _request_candidates(ctx),
                          "Không thấy phiếu khảo sát đang mở (Nháp / Bị trả lại) nào trong phạm vi của bạn có hàng khớp báo "
                          "giá. Đưa người dùng danh sách (phiếu khảo sát đang mở của họ, YCBG họ đang phụ trách) hỏi nhập "
                          "vào đâu, rồi gọi lại với survey_code hoặc survey_request_code.")
    if err:
        return err
    if not plan.rows:
        return {"error": "Không dòng báo giá nào khớp hàng của phiếu — chưa soạn gì.", "unmatched": plan.unmatched}
    if s is not None:
        draft = {"survey_id": s.id, "survey_code": s.code,
                 "line_ids_before": sorted(p.id for p in _lines_of(ctx.db, [s.id])[s.id])}
        target = {"type": "survey", "code": s.code, "status": s.status,
                  "status_label": _SURVEY_STATUS.get(s.status, s.status), "url": SURVEY_URL.format(id=s.id)}
    else:
        draft = {"survey_id": 0, "survey_code": "", "new_survey": new}
        target = {"type": "new_survey", "code": "(phiếu khảo sát mới)", "status": "draft", "status_label": "Nháp",
                  "survey_request_code": new["survey_request_code"], "item_group": new["item_group"],
                  "url": REQUEST_URL.format(id=new["survey_request_id"])}
    draft.update({"supplier_code": sup[0], "supplier_name": sup[1], "quote_no": _text(args.get("quote_no"), 50),
                  "quote_date": quote_date, "rows": plan.rows})
    draft["draft_ref"] = _draft_ref(draft)
    warnings = ([sup_warn] if sup_warn else []) + plan.warnings
    if new:
        warnings.append(f"YCBG {new['survey_request_code']} chưa có phiếu khảo sát đang mở — xác nhận sẽ LẬP phiếu khảo "
                        f"sát Nháp mới (phân loại {new['item_group'] or 'trống'}) gắn YCBG này.")
    return {"draft": draft, "kind": KIND, "target": target, "matched": plan.matched, "unmatched": plan.unmatched,
            "overwrites": plan.overwrites, "uom_mismatches": plan.uom, "warnings": list(dict.fromkeys(warnings)),
            "attach_url": target["url"],
            "note": ("Đã soạn nháp, CHƯA ghi gì. Trình người dùng: phiếu đích (`target`), bảng dòng khớp (`matched` — sửa dòng "
                     "nào / thêm dòng mới), dòng KHÔNG khớp (`unmatched` — không ghi), từng dòng GHI ĐÈ giá đã có "
                     "(`overwrites`) và ĐVT lệch (`uom_mismatches`), đọc nguyên các cảnh báo. Người dùng muốn nhập vào phiếu "
                     "khác thì gọi lại tool với survey_code / survey_request_code (đừng tự sửa `draft`). Họ đồng ý rõ thì "
                     "gọi confirm_draft với kind=supplier_quote và draft = đúng đối tượng `draft` này. Đừng tự báo là đã "
                     "ghi. " + ATTACH_NOTE)}


# ── xác nhận (chạy phía ERP: agent_hub.draft_create.create → kind supplier_quote) ─────────
def _err(msg: str):
    from app.modules.agent_hub.draft_create import DraftError

    return DraftError(msg)


def _validated_rows(draft: dict) -> list[dict]:
    rows = draft.get("rows") if isinstance(draft, dict) else None
    if not isinstance(rows, list) or not rows or len(rows) > MAX_LINES:
        raise _err("Bản nháp không có dòng nào để ghi — gọi lại draft_supplier_quote.")
    out = []
    for r in rows:
        after = r.get("after") if isinstance(r, dict) else None
        if not isinstance(r, dict) or r.get("op") not in ("update", "add") or not isinstance(after, dict):
            raise _err("Bản nháp hỏng (thao tác lạ) — gọi lại draft_supplier_quote, đừng tự sửa bản nháp.")
        price = parse_number(after.get("price_by_volume"))
        vat = parse_number(after.get("vat"), 100) if "vat" in after else None
        try:
            line_id = int(r.get("line_id") or 0)
        except (TypeError, ValueError):
            raise _err("Bản nháp hỏng (số không hợp lệ) — gọi lại draft_supplier_quote.") from None
        if not price or ("vat" in after and vat is None) or (r["op"] == "update" and line_id <= 0):
            raise _err("Bản nháp thiếu đơn giá / VAT sai / thiếu dòng — gọi lại draft_supplier_quote.")
        clean = {"price_by_volume": price}
        if vat is not None:
            clean["vat"] = vat
        if "moq" in after and (moq := parse_number(after.get("moq"), 1e12)) is not None:
            clean["moq"] = moq
        for key, limit in (("quote_unit", 25), ("delivery_time", 100), ("debt_policy", 100), ("note", 2000)):
            if key in after:
                clean[key] = _text(after.get(key), limit)
        before = r.get("before") if isinstance(r.get("before"), dict) else {}
        out.append({"op": r["op"], "line_id": line_id, "after": clean,
                    "before_price": parse_number(before.get("price_by_volume")) or 0,
                    "product_name": _text(r.get("product_name"), 255), "internal_code": _text(r.get("internal_code"), 50),
                    "spec": str(r.get("spec") or "")[:5000], "origin": _text(r.get("origin"), 100),
                    "request_qty": parse_number(r.get("request_qty"), 1e12) or 0})
    ids = [r["line_id"] for r in out if r["op"] == "update"]
    if len(set(ids)) != len(ids):
        raise _err("Bản nháp sửa một dòng hai lần — gọi lại draft_supplier_quote.")
    return out


def _quote_ref(draft: dict) -> str:
    no, when = _text(draft.get("quote_no"), 50), _text(draft.get("quote_date"), 10)
    return ("Báo giá" + (f" số {no}" if no else "") + (f" ngày {when}" if when else "") + " — nhập qua trợ lý AI")


def _apply(inp, after: dict, ref: str):
    """Dòng form sau khi ghi giá — thành tiền tính lại như form web (giá × MOQ × (1 + VAT)); MOQ 0 thì service tự tính
    theo SL yêu cầu."""
    data = {**inp.model_dump(), **after}
    data["amount"] = round(float(data["price_by_volume"]) * float(data.get("moq") or 0)
                           * (1 + float(data.get("vat") or 0) / 100), 2)
    if ref and ref not in (data.get("nspt_note") or ""):
        data["nspt_note"] = ((data.get("nspt_note") or "") + ("\n" if data.get("nspt_note") else "") + ref)[:5000]
    return type(inp)(**data)


def _new_line(r: dict, supplier_code: str, ref: str):
    from app.modules.survey.schema import ProductLineIn

    base = ProductLineIn(supplier_code=supplier_code[:50], internal_code=r["internal_code"],
                         product_name=r["product_name"], spec=r["spec"], origin=r["origin"],
                         request_qty=r["request_qty"], line_approve="Chờ duyệt")
    return _apply(base, r["after"], ref)


def _summary(code: str, supplier: str, rows: list[dict]) -> str:
    parts = [f"{r['internal_code'] or r['product_name']} {'+' if r['op'] == 'add' else '='} "
             f"{vn(r['after']['price_by_volume'])}" for r in rows]
    return f"{code} · {supplier}: " + "; ".join(parts)


def _log(db, user, survey: Survey, action, what: str, before, draft: dict, rows: list[dict], source: int) -> None:
    from app.core.audit import record as audit_record
    from app.modules.assistant import change_service

    summary = _summary(survey.code, draft.get("supplier_name") or draft.get("supplier_code") or "?", rows)
    audit_record(db, user.id, "survey", survey.id, "update",
                 f"{what} qua trợ lý AI (nháp {_text(draft.get('draft_ref'), 20) or '?'}): {summary}"[:1000],
                 doc_code=survey.code)
    change_service.record_change(db, user, entity="survey", entity_id=survey.id, doc_code=survey.code, action=action,
                                 summary=f"{what} {summary}", before=before,
                                 after={"draft_ref": draft.get("draft_ref"), "quote_no": draft.get("quote_no"),
                                        "rows": rows}, after_sig="", source=source)


def _confirm_existing(db, user, profile, draft: dict, rows: list[dict], source: int) -> tuple[str, int]:
    from fastapi import HTTPException
    from pydantic import ValidationError

    from app.modules.assistant.change_model import ChangeAction
    from app.modules.survey import service as survey_service
    from app.modules.survey.schema import ProductLineIn, SurveyUpdate

    from .update_tool import _row_to_input

    try:
        sid = int(draft.get("survey_id") or 0)
    except (TypeError, ValueError):
        sid = 0
    s = apply_scope(db.query(Survey).filter(Survey.id == sid), Survey, "survey", user, profile, "write").first()
    if s is None:
        raise _err(f"Không tìm thấy phiếu khảo sát #{sid} trong phạm vi bạn được ghi — chưa ghi gì.")
    if s.status not in EDITABLE_STATUSES:
        raise _err(f"Phiếu khảo sát {s.code} đang ở trạng thái {_SURVEY_STATUS.get(s.status, s.status)} — chỉ nhập giá "
                   "được khi phiếu ở Nháp hoặc Bị trả lại. Chưa ghi gì.")
    plines = _lines_of(db, [s.id])[s.id]
    if sorted(p.id for p in plines) != sorted(int(i) for i in draft.get("line_ids_before") or [] if str(i).isdigit()):
        raise _err(f"Dòng của phiếu {s.code} đã đổi sau lúc soạn nháp — gọi lại draft_supplier_quote. Chưa ghi gì.")
    updates = {r["line_id"]: r for r in rows if r["op"] == "update"}
    by_id = {p.id: p for p in plines}
    for lid, r in updates.items():
        p = by_id.get(lid)
        if p is None or abs(_num(p.price_by_volume) - r["before_price"]) > 1e-6:
            raise _err(f"Giá dòng #{lid} của phiếu {s.code} đã đổi sau lúc soạn nháp — gọi lại draft_supplier_quote. "
                       "Chưa ghi gì.")
        if not _same_supplier(p.supplier_code, (_text(draft.get("supplier_code"), 50), _text(draft.get("supplier_name")))):
            raise _err(f"Dòng #{lid} của phiếu {s.code} không phải của NCC trên báo giá — chưa ghi gì.")
    ref = _quote_ref(draft)
    supplier_code = _text(draft.get("supplier_code"), 50)
    before = {"lines": [{"line_id": lid, **_snapshot(by_id[lid])} for lid in updates]}
    try:
        lines_in = [_apply(_row_to_input(ProductLineIn, p), updates[p.id]["after"], ref) if p.id in updates
                    else _row_to_input(ProductLineIn, p) for p in plines]
        lines_in += [_new_line(r, supplier_code, ref) for r in rows if r["op"] == "add"]
    except ValidationError as e:
        raise _err(f"Phiếu {s.code} có dữ liệu cũ không hợp lệ ({str(e)[:200]}) — nhập giá trên màn phiếu khảo sát.") \
            from None
    try:
        survey_service.update_survey(db, s.id, SurveyUpdate(product_lines=lines_in), user.id)
    except HTTPException as e:
        db.rollback()
        raise _err(f"Phiếu {s.code} chưa ghi: {e.detail}") from None
    _log(db, user, s, ChangeAction.UPDATE, "Nhập báo giá NCC", before, draft, rows, source)
    return s.code, s.id


def _confirm_new(db, user, profile, draft: dict, rows: list[dict], source: int) -> tuple[str, int]:
    from fastapi import HTTPException

    from app.core.auth import user_has_permission
    from app.modules.assistant.change_model import ChangeAction
    from app.modules.survey import service as survey_service
    from app.modules.survey.schema import SurveyCreate

    new = draft.get("new_survey") if isinstance(draft.get("new_survey"), dict) else {}
    if not user_has_permission(db, user, "survey", "create"):
        raise _err("Tài khoản này không có quyền tạo phiếu khảo sát nên không lập được phiếu cho YCBG.")
    try:
        rid, lid = int(new.get("survey_request_id") or 0), int(new.get("survey_request_line_id") or 0)
    except (TypeError, ValueError):
        rid = lid = 0
    sr = apply_scope(db.query(SurveyRequest).filter(SurveyRequest.id == rid), SurveyRequest, "survey_request", user,
                     profile, "read").first()
    if sr is None:
        raise _err(f"Không tìm thấy YCBG #{rid} trong phạm vi bạn được xem — chưa ghi gì.")
    if sr.status not in OPEN_REQUEST_STATUSES:
        raise _err(f"YCBG {sr.code} đang ở trạng thái {_REQUEST_STATUS.get(sr.status, sr.status)} — chỉ lập phiếu khảo "
                   "sát cho YCBG Đã duyệt / Đang xử lý. Chưa ghi gì.")
    linked = sorted(i for (i,) in db.query(Survey.id).filter(Survey.survey_request_id == sr.id,
                                                             Survey.is_deleted.is_(False)))
    if linked != sorted(int(i) for i in new.get("linked_before") or [] if str(i).isdigit()):
        raise _err(f"YCBG {sr.code} đã có phiếu khảo sát mới sau lúc soạn nháp — gọi lại draft_supplier_quote để nhập vào "
                   "phiếu đó. Chưa ghi gì.")
    line = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == lid,
                                              SurveyRequestLine.survey_request_id == sr.id).first()
    if line is None:
        raise _err(f"Dòng YCBG của {sr.code} không còn — gọi lại draft_supplier_quote. Chưa ghi gì.")
    ref = _quote_ref(draft)
    supplier_code = _text(draft.get("supplier_code"), 50)
    data = SurveyCreate(survey_request_id=sr.id, sr_code=sr.code, item_group=(line.item_group or "")[:100],
                        main_content=(sr.purpose or "")[:600], requirement_detail=line.requirement_detail or "",
                        request_qty=float(line.request_qty or 0), uom=(line.uom or "")[:25],
                        received_date=line.received_date or "", result_due_date=line.result_due_date or "",
                        product_lines=[_new_line(r, supplier_code, ref) for r in rows])
    try:
        s = survey_service.create_survey(db, data, user.id)
    except HTTPException as e:
        db.rollback()
        raise _err(f"Chưa lập được phiếu khảo sát: {e.detail}") from None
    _log(db, user, s, ChangeAction.CREATE, f"Lập phiếu khảo sát cho YCBG {sr.code} từ báo giá NCC", None, draft, rows,
         source)
    return s.code, s.id


def confirm_quote(db, user, draft: dict, source: int = 0) -> tuple[str, int]:
    """Ghi thật. Kiểm lại quyền + phạm vi write, trạng thái, dòng chưa đổi TRƯỚC khi ghi; ghi bằng service lưu phiếu khảo
    sát của màn web (một lần bấm Lưu)."""
    from app.core.auth import get_perm_profile, user_has_permission

    if not user_has_permission(db, user, "survey", "write") or not user_has_permission(db, user, "supplier", "read"):
        raise _err("Tài khoản này không có quyền sửa phiếu khảo sát nên không nhập được báo giá.")
    if not isinstance(draft, dict):
        raise _err("Bản nháp hỏng — gọi lại draft_supplier_quote.")
    rows = _validated_rows(draft)
    profile = get_perm_profile(db, user)
    if draft.get("new_survey"):
        return _confirm_new(db, user, profile, draft, rows, source)
    return _confirm_existing(db, user, profile, draft, rows, source)


def created_details(db, survey_id: int) -> list[str]:
    """Các dòng SP của phiếu sau khi ghi (NCC, đơn giá, VAT, ĐVT), đọc lại từ DB."""
    s = db.get(Survey, int(survey_id or 0))
    if s is None:
        return []
    out = [f"{s.code} · {_SURVEY_STATUS.get(s.status, s.status)}" + (f" · YCBG {s.sr_code}" if s.sr_code else "")]
    for p in _lines_of(db, [s.id])[s.id][:30]:
        out.append(f"- {p.internal_code or p.product_name} · {p.supplier_code}: {vn(_num(p.price_by_volume))} VND"
                   f"{'/' + p.quote_unit if p.quote_unit else ''}, VAT {vn(_num(p.vat))}% (trước VAT)")
    return out


def summary_lines(draft: dict) -> list[str]:
    """Tóm tắt nháp cho bot (draft_create.summarize)."""
    new = draft.get("new_survey") or {}
    where = draft.get("survey_code") or f"phiếu khảo sát mới cho YCBG {new.get('survey_request_code', '?')}"
    out = [f"NCC: {draft.get('supplier_name') or draft.get('supplier_code') or '?'}", f"Phiếu: {where}",
           f"Báo giá: {draft.get('quote_no') or '(không số)'} · ngày {draft.get('quote_date') or '?'}"]
    for r in (draft.get("rows") or [])[:12]:
        how = "thêm dòng" if r.get("op") == "add" else f"sửa dòng {r.get('line_no')}"
        out.append(f"- {r.get('internal_code') or r.get('product_name')}: {vn((r.get('after') or {}).get('price_by_volume'))}"
                   f" ({how})")
    return out


DRAFT_SUPPLIER_QUOTE_SPEC = ToolSpec(
    name="draft_supplier_quote",
    description=("SOẠN NHÁP nhập BÁO GIÁ NHÀ CUNG CẤP vào phiếu khảo sát đang mở (Nháp / Bị trả lại) hoặc YCBG đang khảo "
                 "sát. Người dùng gửi TỆP báo giá (PDF / ảnh): tự đọc NCC, số + ngày báo giá, từng dòng (mã hoặc tên hàng, "
                 "đơn giá TRƯỚC VAT, VAT %, ĐVT, MOQ, thời gian giao, hạn công nợ, ghi chú). Tool tự tìm phiếu (nêu "
                 "survey_code KS… hoặc survey_request_code YCBG… nếu người dùng nói; không thì chọn phiếu có nhiều dòng "
                 "khớp nhất của người hỏi), khớp từng dòng theo NCC + hàng, báo dòng KHÔNG khớp, dòng GHI ĐÈ giá đã có, "
                 "ĐVT lệch. YCBG chưa có phiếu khảo sát thì xác nhận sẽ lập phiếu khảo sát Nháp gắn YCBG. KHÔNG ghi gì. "
                 "Quy trình: đọc tệp → gọi tool → trình bảng + cảnh báo → người dùng đồng ý rõ thì "
                 "confirm_draft(kind=supplier_quote, draft=đúng `draft`). Không đoán số liệu không có trên báo giá. Tệp "
                 "báo giá không gửi qua AI: đưa người dùng `attach_url` để tự đính trên web."),
    parameters={"type": "object", "properties": {
        "supplier": {"type": "string", "description": "Tên NCC đúng như trên báo giá, hoặc mã NCC / MST (khớp mờ, bỏ dấu)."},
        "quote_no": {"type": "string", "description": "Số báo giá (nếu có)."},
        "quote_date": {"type": "string", "description": "Ngày báo giá YYYY-MM-DD (nếu có)."},
        "survey_code": {"type": "string", "description": "Mã phiếu khảo sát (KS…) người dùng chỉ định — tùy chọn."},
        "survey_request_code": {"type": "string", "description": "Mã YCBG người dùng chỉ định — tùy chọn."},
        "item_group": {"type": "string", "description": "Phân loại dòng YCBG khi YCBG có nhiều phân loại — tùy chọn."},
        "lines": {"type": "array", "maxItems": MAX_LINES, "items": {"type": "object", "properties": {
            "product_code": {"type": "string", "description": "Mã hàng trên báo giá (mã VTBB hoặc mã SP của NCC)."},
            "product_name": {"type": "string", "description": "Tên hàng trên báo giá."},
            "unit_price": {"type": "number", "description": "Đơn giá TRƯỚC VAT theo ĐVT báo giá (1.150.000 = 1150000)."},
            "vat": {"type": "number", "description": "VAT % (8 = 8%). Báo giá không ghi thì bỏ trống."},
            "uom": {"type": "string", "description": "ĐVT của đơn giá."},
            "moq": {"type": "number", "description": "Số lượng đặt tối thiểu (nếu có)."},
            "delivery_time": {"type": "string", "description": "Thời gian giao hàng, vd 7 ngày."},
            "debt_term": {"type": "string", "description": "Hạn công nợ / thanh toán, vd Công nợ 30 ngày, Tiền mặt."},
            "note": {"type": "string", "description": "Ghi chú của dòng trên báo giá."}},
            "required": ["unit_price"]}}},
        "required": ["supplier", "lines"]},
    handler=draft_supplier_quote,
)

SUPPLIER_QUOTE_SPECS = [DRAFT_SUPPLIER_QUOTE_SPEC]
