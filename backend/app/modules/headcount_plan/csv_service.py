"""Xuất / nhập CSV kế hoạch nhân sự. Cột: year, company_code, department_code (rỗng = toàn pháp nhân),
planned_headcount, planned_payroll_monthly, note. Nhập là UPSERT theo (năm, pháp nhân, phòng) và
NGUYÊN KHỐI: một dòng lỗi thì không ghi dòng nào, báo mọi lỗi kèm số dòng."""
import csv
from io import StringIO

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.crud import commit_or_conflict
from app.core.export_xlsx import _FORMULA_TRIGGER_CHARS
from app.core.scoping import apply_scope
from app.core.text_limits import describe_validation_errors
from app.modules.company.model import Company
from app.modules.department.model import Department

from .model import HeadcountPlan
from .schema import HeadcountPlanCreate
from .serializer import can_see_payroll
from .service import PAYROLL_DENIED

HEADERS = ["year", "company_code", "department_code", "planned_headcount", "planned_payroll_monthly", "note"]
MAX_BYTES = 1_000_000
MAX_ROWS = 2000


def _safe_cell(text: str) -> str:
    """Chống chèn công thức khi mở CSV bằng Excel: ô chữ mở đầu `= + - @` / tab / CR thì thêm dấu nháy đơn."""
    return "'" + text if text[:1] in _FORMULA_TRIGGER_CHARS else text


def _unsafe_cell(text: str) -> str:
    """Ngược của `_safe_cell` để xuất rồi nhập lại không dồn dấu nháy."""
    return text[1:] if text[:1] == "'" and text[1:2] in _FORMULA_TRIGGER_CHARS and text[1:2] != "" else text


def export_rows(db: Session, plans: list[HeadcountPlan], profile: dict) -> list[list]:
    comp = dict(db.query(Company.id, Company.code).filter(Company.id.in_({p.company_id for p in plans} or {0})).all())
    dept = dict(db.query(Department.id, Department.code).filter(
        Department.id.in_({p.department_id for p in plans if p.department_id} or {0})).all())
    return [[int(p.year), comp.get(p.company_id, ""), dept.get(p.department_id, "") if p.department_id else "",
             int(p.planned_headcount or 0), int(p.planned_payroll_monthly or 0) if can_see_payroll(profile, p.company_id) else "",
             _safe_cell(p.note or "")]
            for p in plans]


def to_csv(rows: list[list]) -> bytes:
    out = StringIO()
    w = csv.writer(out)
    w.writerow(HEADERS)
    w.writerows(rows)
    return out.getvalue().encode("utf-8-sig")


def _parse(raw: bytes) -> list[dict]:
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, f"Tệp CSV tối đa {MAX_BYTES // 1000} KB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "Tệp CSV phải mã hóa UTF-8")
    reader = csv.DictReader(StringIO(text))
    missing = [h for h in HEADERS[:4] if h not in (reader.fieldnames or [])]
    if missing:
        raise HTTPException(400, f"Tệp CSV thiếu cột: {', '.join(missing)}")
    rows = [r for r in reader if any((v or "").strip() for v in r.values())]
    if len(rows) > MAX_ROWS:
        raise HTTPException(422, f"Tệp CSV tối đa {MAX_ROWS} dòng")
    return rows


def import_rows(db: Session, raw: bytes, user, profile: dict) -> dict:
    """Trả `{created, updated}`. Lỗi → HTTPException 422, `message` liệt kê «Dòng n: ...» (tối đa 20).
    Phạm vi `write`/`create` kiểm SAU khi ghi (flush) — ngoài phạm vi thì rollback cả khối, 403."""
    rows = _parse(raw)
    companies = {c.code: c.id for c in db.query(Company.id, Company.code).all()}
    #  Phòng ban DÙNG CHUNG mọi pháp nhân (company_id = 0 trên dữ liệu thật) và `code` duy nhất toàn cục
    #  → tra theo mã, KHÔNG theo (pháp nhân, mã).
    depts = {d.code: d.id for d in db.query(Department.id, Department.code).all()}
    errors, parsed, seen = [], [], set()
    for n, r in enumerate(rows, start=2):
        try:
            cid = companies.get((r.get("company_code") or "").strip())
            dcode = (r.get("department_code") or "").strip()
            did = depts.get(dcode) if dcode else 0
            if not cid:
                raise ValueError("mã pháp nhân không tồn tại")
            if did is None:
                raise ValueError("mã phòng ban không tồn tại")
            pay = (r.get("planned_payroll_monthly") or "").strip()
            if pay and not can_see_payroll(profile, cid):
                raise ValueError(PAYROLL_DENIED)
            data = HeadcountPlanCreate(year=(r.get("year") or "").strip(), company_id=cid, department_id=did,
                                       planned_headcount=(r.get("planned_headcount") or "0").strip() or 0,
                                       planned_payroll_monthly=pay or None, note=_unsafe_cell(r.get("note") or ""))
            key = (data.year, cid, did)
            if key in seen:
                raise ValueError("trùng (năm, pháp nhân, phòng) với dòng trước trong tệp")
            seen.add(key)
            parsed.append(data)
        except ValidationError as e:
            errors.append(f"Dòng {n}: " + describe_validation_errors(e.errors(), [HeadcountPlanCreate]))
        except ValueError as e:
            errors.append(f"Dòng {n}: {e}")
    if errors:
        more = f" (và {len(errors) - 20} lỗi khác)" if len(errors) > 20 else ""
        raise HTTPException(422, "Tệp CSV có lỗi, chưa ghi dòng nào: " + " | ".join(errors[:20]) + more)
    existing = {(p.year, p.company_id, p.department_id): p for p in db.query(HeadcountPlan).filter(
        HeadcountPlan.year.in_({d.year for d in parsed}), HeadcountPlan.company_id.in_({d.company_id for d in parsed})).all()}
    created = updated = 0
    touched = []
    for d in parsed:
        cur = existing.get((d.year, d.company_id, d.department_id))
        if cur is None:
            cur = HeadcountPlan(year=d.year, company_id=d.company_id, department_id=d.department_id,
                                created_by=user.id, updated_by=user.id)
            db.add(cur)
            created += 1
        else:
            updated += 1
        cur.planned_headcount = d.planned_headcount
        if d.planned_payroll_monthly is not None:
            cur.planned_payroll_monthly = d.planned_payroll_monthly
        elif cur.planned_payroll_monthly is None:
            cur.planned_payroll_monthly = 0
        cur.note = d.note
        cur.updated_by = user.id
        touched.append(cur)
    db.flush()
    ids = [c.id for c in touched]
    for action in ("create", "write"):   # MỘT truy vấn phạm vi cho mỗi hành động, không theo số dòng
        q = apply_scope(db.query(HeadcountPlan.id).filter(HeadcountPlan.id.in_(ids)), HeadcountPlan,
                        "headcount_plan", user, profile, action)
        if q.count() != len(ids):
            db.rollback()
            raise HTTPException(403, "Tệp có dòng ngoài phạm vi dữ liệu của bạn — không ghi gì")
    commit_or_conflict(db, "Có người nhập kế hoạch trùng cùng lúc — hãy nhập lại")
    return {"created": created, "updated": updated}
