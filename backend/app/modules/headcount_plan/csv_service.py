"""CSV kế hoạch nhân sự (duoc-CR-690, làm lại theo khuôn kỳ).

- XUẤT danh sách kế hoạch: một dòng / kế hoạch (header + định biên cuối kỳ + tổng chi phí nếu được xem).
- NHẬP dòng vị trí vào MỘT kế hoạch: cột `position_code, hc_1..hc_n, <mã khoản nhập theo vị trí>…`; vị trí khớp thì thay,
  chưa có thì thêm, vị trí không nằm trong tệp giữ nguyên. NGUYÊN KHỐI: một dòng lỗi thì không ghi dòng nào, báo mọi lỗi
  kèm số dòng. Mã chức vụ lạ = lỗi dòng. Cột tiền của người không xem được tiền: ô trống / 0 bỏ qua, khác 0 → lỗi dòng.
"""
import csv
from io import StringIO

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.export_xlsx import _FORMULA_TRIGGER_CHARS
from app.core.text_limits import describe_validation_errors
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.position_model import JobPosition

from .constants import MAX_LINES, CostCalcMethod
from .costing import period_label, period_layout
from .cost_model import HeadcountPlanCostItem
from .model import HeadcountPlan, HeadcountPlanLine
from .schema import PlanLineIn
from .service import PAYROLL_DENIED
from .serializer import can_see_payroll

LIST_HEADERS = ["year", "period_type", "period_no", "period_label", "company_code", "department_code",
                "headcount_end", "total_cost", "basis_no", "basis_date", "note"]
MAX_BYTES = 1_000_000


def _safe_cell(text: str) -> str:
    """Chống chèn công thức khi mở CSV bằng Excel: ô chữ mở đầu `= + - @` / tab / CR thì thêm dấu nháy đơn."""
    return "'" + text if text[:1] in _FORMULA_TRIGGER_CHARS else text


def _unsafe_cell(text: str) -> str:
    """Ngược của `_safe_cell` để xuất rồi nhập lại không dồn dấu nháy."""
    return text[1:] if text[:1] == "'" and text[1:2] in _FORMULA_TRIGGER_CHARS and text[1:2] != "" else text


def export_rows(db: Session, plans_out: list[dict]) -> list[list]:
    """`plans_out` là kết quả `serializer.serialize_plans` (đã che tiền)."""
    comp = dict(db.query(Company.id, Company.code).filter(
        Company.id.in_({p["company_id"] for p in plans_out} or {0})).all())
    dept = dict(db.query(Department.id, Department.code).filter(
        Department.id.in_({p["department_id"] for p in plans_out if p["department_id"]} or {0})).all())
    return [[p["year"], p["period_type"], p["period_no"], p["period_label"], comp.get(p["company_id"], ""),
             dept.get(p["department_id"], "") if p["department_id"] else "", p["headcount_end"],
             "" if p["total_cost"] is None else p["total_cost"], _safe_cell(p["basis_no"]),
             p["basis_date"].isoformat() if p["basis_date"] else "", _safe_cell(p["note"])] for p in plans_out]


def to_csv(rows: list[list]) -> bytes:
    out = StringIO()
    w = csv.writer(out)
    w.writerow(LIST_HEADERS)
    w.writerows(rows)
    return out.getvalue().encode("utf-8-sig")


def _read(raw: bytes) -> csv.DictReader:
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"Tệp CSV tối đa {MAX_BYTES // 1000} KB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "Tệp CSV phải mã hóa UTF-8")
    return csv.DictReader(StringIO(text))


def _int_cell(value, what: str, row_errors: list) -> int:
    text = (value or "").strip()
    if not text:
        return 0
    try:
        return int(text.replace(".", "").replace(",", "")) if what == "money" else int(text)
    except ValueError:
        row_errors.append(f"«{text}» không phải số nguyên")
        return 0


def import_lines(db: Session, plan: HeadcountPlan, raw: bytes, profile: dict, actor_id: int) -> dict:
    """Trả `{created, updated}`. Lỗi → 422 «Dòng n: …» (tối đa 20). Chưa commit — bên gọi kiểm luật tính rồi commit."""
    reader = _read(raw)
    n_periods = len(period_layout(plan.period_type, plan.period_no))
    hc_cols = [f"hc_{i}" for i in range(1, n_periods + 1)]
    money_cols = [i.code for i in db.query(HeadcountPlanCostItem).filter(
        HeadcountPlanCostItem.plan_id == plan.id, HeadcountPlanCostItem.calc_method == int(CostCalcMethod.PER_HEAD_MONTH))]
    fields = reader.fieldnames or []
    missing = [h for h in ["position_code", *hc_cols] if h not in fields]
    if missing:
        raise HTTPException(400, f"Tệp CSV thiếu cột: {', '.join(missing)}")
    rows = [r for r in reader if any((v or "").strip() for v in r.values())]
    if len(rows) > MAX_LINES:
        raise HTTPException(422, f"Tệp CSV tối đa {MAX_LINES} dòng")
    positions = {c: i for c, i in db.query(JobPosition.code, JobPosition.id).all()}
    see = can_see_payroll(profile, plan.company_id, plan.department_id or 0)
    errors, parsed, seen = [], {}, set()
    for n, r in enumerate(rows, start=2):
        row_errors: list[str] = []
        code = (r.get("position_code") or "").strip()
        pid = positions.get(code) if code else 0
        if pid is None:
            row_errors.append(f"mã chức vụ «{code}» không tồn tại")
        if pid in seen:
            row_errors.append("trùng vị trí với dòng trước trong tệp")
        seen.add(pid)
        headcounts = [_int_cell(r.get(c), "count", row_errors) for c in hc_cols]
        amounts = {c: _int_cell(r.get(c), "money", row_errors) for c in money_cols if (r.get(c) or "").strip()}
        if amounts and not see and any(amounts.values()):
            row_errors.append(PAYROLL_DENIED)
        if not row_errors:
            try:
                parsed[pid] = PlanLineIn(position_id=pid, headcounts=headcounts, amounts=amounts or None,
                                         note=_unsafe_cell(r.get("note") or ""))
            except ValidationError as e:
                row_errors.append(describe_validation_errors(e.errors(), [PlanLineIn]))
        errors += [f"Dòng {n}: {m}" for m in row_errors]
    if errors:
        more = f" (và {len(errors) - 20} lỗi khác)" if len(errors) > 20 else ""
        raise HTTPException(422, "Tệp CSV có lỗi, chưa ghi dòng nào: " + " | ".join(errors[:20]) + more)

    existing = {ln.position_id: ln for ln in db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan.id)}
    created = updated = 0
    for pid, ln in parsed.items():
        cur = existing.get(pid)
        if cur is None:
            cur = HeadcountPlanLine(plan_id=plan.id, position_id=pid, created_by=actor_id, amounts={})
            db.add(cur)
            created += 1
        else:
            updated += 1
        cur.headcounts = list(ln.headcounts)
        if ln.amounts is not None and see:
            cur.amounts = {**(cur.amounts or {}), **ln.amounts}
        if "note" in fields:
            cur.note = ln.note
        cur.updated_by = actor_id
    if len(existing) + created > MAX_LINES:
        raise HTTPException(422, f"Kế hoạch tối đa {MAX_LINES} dòng vị trí")
    return {"created": created, "updated": updated}
