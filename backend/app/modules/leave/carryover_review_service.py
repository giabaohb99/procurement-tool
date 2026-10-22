"""BẢNG ĐỐI CHIẾU TRƯỚC / SAU KẾT SỔ PHÉP CUỐI NĂM (kh-HR2-3, duoc-CR-664).

Hỏi: *"kết sổ năm N xong, mỗi người từ bao nhiêu ngày còn lại → còn bao nhiêu, và
bao nhiêu ngày sang năm N+1?"*

**Không có bảng snapshot, và đó là chủ ý.** `carryover_service.close_year` đã lưu
vết đủ trong chính dòng quỹ năm N: cột `carried_out_days` là TỔNG ngày đã đẩy đi
(cộng dồn qua các lượt, xem docstring `close_year`). `remaining_days` đã trừ
`carried_out_days`, nên số TRƯỚC kết sổ dựng lại được:

    số cũ (trước)  = remaining_days + carried_out_days
    số mới (sau)   = remaining_days
    chênh          = số mới - số cũ  = -carried_out_days
    sang năm N+1   = carried_out_days x tỷ lệ quy đổi của loại nghỉ

Thêm bảng snapshot là nuôi hai nguồn sự thật cho cùng một con số, mà nó chỉ chụp
được lúc bấm nút; cách dựng lại này luôn khớp với sổ quỹ thật và không cần migration.

⚠️ Hai giới hạn, nói ra để người đọc bảng không hiểu nhầm:
  · "Số cũ" được dựng lại TẠI THỜI ĐIỂM XEM: đơn năm cũ được duyệt/hủy SAU kết sổ
    làm `used_days` đổi nên số cũ đổi theo (và lượt kết sổ sau sẽ vét phần đó).
  · Tỷ lệ và loại nhận lấy theo cấu hình loại nghỉ HIỆN HÀNH; sửa cấu hình sau khi
    kết sổ thì cột "cộng vào năm sau" là số ước theo cấu hình mới. Cột "mang sang
    hiện có" ở năm sau là số THẬT trong sổ (gồm mọi nguồn, đã trừ phần hết hạn).

Số truy vấn CỐ ĐỊNH tối đa 4 bất kể số dòng: dòng quỹ năm N · loại nghỉ · nhân sự ·
dòng quỹ năm N+1 của các cặp (người, loại nhận). Không truy vấn trong vòng lặp.
"""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee

from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .constants import YEAR_END_CONVERT, YEAR_END_MOVING_MODES

#  Trần số dòng trả về — 100 người x 8 loại còn xa mới chạm; vượt là dữ liệu bất thường.
MAX_ROWS = 5000

EXPORT_COLUMNS = [
    Col("employee_code", "Mã nhân sự", width=14),
    Col("employee_name", "Họ tên", width=28),
    Col("source_type_name", "Loại nghỉ (năm cũ)", width=24),
    Col("before_days", "Số cũ - trước kết sổ (ngày)", "decimal", 18),
    Col("after_days", "Số mới - sau kết sổ (ngày)", "decimal", 18),
    Col("diff_days", "Chênh lệch (ngày)", "decimal", 16),
    Col("dest_type_name", "Loại nhận (năm sau)", width=24),
    Col("ratio", "Tỷ lệ quy đổi", "decimal", 12),
    Col("credited_days", "Cộng vào năm sau (ngày)", "decimal", 18),
    Col("dest_carried_days", "Mang sang hiện có ở năm sau (ngày)", "decimal", 22),
]


def build_review(db: Session, user, prof: dict, year: int, action: str = "read") -> dict:
    """Dòng đối chiếu của kết sổ năm `year` trong phạm vi `leave_balance` của người xem.

    `action` là quyền dùng để LỌC phạm vi: đường xuất Excel truyền `"export"` để lọc
    theo grant có `export` (phạm vi xuất có thể hẹp hơn phạm vi xem), như mọi đường
    xuất khác (`employee`, `product`, `export_log`).
    """
    query = apply_scope(db.query(LeaveBalance), LeaveBalance, "leave_balance", user, prof, action)
    #  Chỉ dòng ĐÃ có ngày chuyển đi: dòng chưa kết sổ thì chưa có gì để đối chiếu.
    rows = (query.filter(LeaveBalance.year == year, LeaveBalance.carried_out_days > 0)
            .order_by(LeaveBalance.employee_id, LeaveBalance.leave_type_id)
            .limit(MAX_ROWS).all())
    if not rows:
        return _pack(year, [])

    types = {t.id: t for t in db.query(LeaveType).all()}
    employees = {e.id: e for e in db.query(Employee)
                 .filter(Employee.id.in_({r.employee_id for r in rows})).all()}

    plan = []  # (dòng quỹ, loại nguồn, loại nhận, tỷ lệ)
    for row in rows:
        source = types.get(row.leave_type_id)
        if source is None or source.year_end_mode not in YEAR_END_MOVING_MODES:
            continue  # loại đã đổi sang "hết năm là mất" sau khi kết sổ — không còn là dòng chuyển
        if source.year_end_mode == YEAR_END_CONVERT:
            dest = types.get(source.convert_to_type_id or 0)
            ratio = source.convert_ratio if source.convert_ratio and source.convert_ratio > 0 else 0.0
        else:
            dest, ratio = source, 1.0
        plan.append((row, source, dest, ratio))

    dest_ids = {d.id for _, _, d, _ in plan if d is not None}
    next_year: dict[tuple[int, int], float] = {}
    if dest_ids:
        for b in (db.query(LeaveBalance)
                  .filter(LeaveBalance.year == year + 1,
                          LeaveBalance.employee_id.in_({r.employee_id for r, *_ in plan}),
                          LeaveBalance.leave_type_id.in_(dest_ids)).all()):
            next_year[(b.employee_id, b.leave_type_id)] = b.carried_days

    items = []
    for row, source, dest, ratio in plan:
        employee = employees.get(row.employee_id)
        moved = round(row.carried_out_days, 2)
        after = round(row.remaining_days, 2)
        before = round(after + moved, 2)
        items.append({
            "employee_id": row.employee_id,
            "employee_code": employee.code if employee else "",
            "employee_name": employee.full_name if employee else "",
            "source_type_id": source.id,
            "source_type_name": source.name,
            "dest_type_id": dest.id if dest else 0,
            "dest_type_name": dest.name if dest else "",
            "ratio": ratio,
            "before_days": before,
            "after_days": after,
            "diff_days": round(after - before, 2),
            "credited_days": round(moved * ratio, 2) if dest else 0.0,
            "dest_carried_days": round(next_year.get((row.employee_id, dest.id), 0.0), 2)
            if dest else 0.0,
        })
    items.sort(key=lambda i: (i["employee_name"], i["source_type_name"]))
    return _pack(year, items)


def _pack(year: int, items: list[dict]) -> dict:
    def total(key: str) -> float:
        return round(sum(i[key] for i in items), 2)

    return {
        "year": year,
        "next_year": year + 1,
        "items": items,
        "totals": {
            "row_count": len(items),
            "before_days": total("before_days"),
            "after_days": total("after_days"),
            "diff_days": total("diff_days"),
            "credited_days": total("credited_days"),
        },
    }
