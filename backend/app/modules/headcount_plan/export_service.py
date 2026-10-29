"""Xuất xlsx MỘT kế hoạch: sheet «Định biên» (dòng vị trí) và sheet «Bảng tính» (số hệ thống tự tính theo kỳ con).
Người không xem được tiền của pháp nhân chỉ nhận định biên — cột tiền và bảng tính bị bỏ (cùng luật che ở API)."""
from io import BytesIO

from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy.orm import Session

from app.core.export_xlsx import _FORMULA_TRIGGER_CHARS

from .costing import period_label
from .detail_serializer import line_out, load_children, position_names_of
from .model import HeadcountPlan
from .serializer import can_see_payroll, compute_from

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_MONEY_FORMAT = "#,##0"


def _write(ws, rows: list[list]) -> None:
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=val)
            if isinstance(val, str) and val[:1] in _FORMULA_TRIGGER_CHARS:
                cell.data_type = "s"   # chuỗi người dùng gõ bắt đầu bằng = + - @ không được chạy như công thức
            if isinstance(val, int) and not isinstance(val, bool) and abs(val) >= 1000:
                cell.number_format = _MONEY_FORMAT
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDEBF7")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18


def build_plan_xlsx(db: Session, plan: HeadcountPlan, profile: dict) -> bytes:
    see = can_see_payroll(profile, plan.company_id, plan.department_id or 0)
    items, lines = load_children(db, plan.id)
    computed = compute_from(db, plan.year, plan.period_type, plan.period_no, items, lines)
    periods = computed["periods"]
    names = position_names_of(db, lines)
    per_head = [i for i in items if int(i.calc_method) == 1] if see else []

    wb = Workbook()
    ws = wb.active
    ws.title = "Số người"
    rows = [["Vị trí"] + [f"Số người {p['label']}" for p in periods] + [i.name for i in per_head]]
    for ln in lines:
        out = line_out(ln, names, see)
        rows.append([out["position_name"]] + out["headcounts"]
                    + [(out["amounts"] or {}).get(i.code, 0) for i in per_head])
    rows.append(["Tổng"] + computed["headcount"])
    _write(ws, rows)

    if see:
        body = [["Khoản"] + [p["label"] for p in periods] + ["Tổng kỳ"]]
        for g in computed["groups"]:
            body.append([g["name"] or "(Chưa phân nhóm)"] + g["values"] + [g["total"]])
            body += [["    " + it["name"]] + it["values"] + [it["total"]]
                     for it in computed["items"] if it["group_id"] == g["group_id"]]
        body.append(["TỔNG CHI PHÍ NHÂN SỰ"] + computed["total"]["values"] + [computed["total"]["total"]])
        body.append(["Số người cuối kỳ con"] + computed["headcount"])
        body.append(["Bình quân / người cả kỳ", computed["avg_per_head"] if computed["avg_per_head"] is not None else ""])
        ws2 = wb.create_sheet("Bảng tính")
        _write(ws2, body)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def xlsx_response(db: Session, plan: HeadcountPlan, profile: dict) -> Response:
    label = period_label(int(plan.year), int(plan.period_type), int(plan.period_no)).replace("/", "-")
    return Response(content=build_plan_xlsx(db, plan, profile), media_type=XLSX_TYPE,
                    headers={"Content-Disposition": f"attachment; filename=ke-hoach-nhan-su-{label}.xlsx"})
