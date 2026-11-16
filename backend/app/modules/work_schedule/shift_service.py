"""GHI CA XẾP THEO NGÀY (duoc-CR-761) — đặt / gỡ / áp hàng loạt / chép tuần. Quyền đã kiểm ở `shift_access`.

Mọi hàm ghi CHỈ `flush`, không commit: controller gom `record(commit=False)` nhật ký + commit MỘT lần để dòng nhật ký đi
cùng giao dịch với ca. Mỗi hàm trả `ShiftChange` (những ô thật sự đổi) để controller báo chuông + ghi nhật ký.
Số truy vấn: một truy vấn nạp (và KHÓA `FOR UPDATE`) các ô đã có, một lệnh xóa khung cũ, một lần ghi khung; riêng ô MỚI
thì MySQL phải INSERT từng dòng ngày để lấy id (nên tối đa theo số ô, và mỗi lượt bị chặn ≤ 500 ô ở schema).

Chống ghi đồng thời: hàng ca đã có bị khóa (theo khóa chính) khi nạp và LUÔN bị UPDATE (`updated_at`) khi đổi khung, nên hai lượt cùng sửa một
ô xếp hàng sau nhau chứ không xóa-chèn khung chồng lên nhau; hai lượt cùng TẠO một ô mới thì ràng buộc UNIQUE
`(employee_id, work_date)` làm lượt sau lỗi `IntegrityError` (hoặc deadlock / hết chờ khóa nếu hai lượt chạm nhau) — controller
đổi cả hai thành 409 (`_conflict_guard`).
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import delete, func
from sqlalchemy.orm import Session

from .model import WorkShiftDay, WorkShiftSegment
from .shift_loader import ShiftRecord, load_shift_records

#  Một ô cần ghi: (nhân sự, ngày, các khung (start_hour, end_hour) đã sắp, ghi chú).
ShiftItem = tuple[int, date, list[tuple[int, int]], str]


@dataclass
class ShiftChange:
    """Kết quả một lượt ghi: số ô đã ĐỔI (tạo / sửa / gỡ), số ô bỏ qua, và ngày đổi của từng nhân sự."""

    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    dates_by_employee: dict[int, set[date]] = field(default_factory=lambda: defaultdict(set))

    @property
    def changed(self) -> int:
        return self.created + self.updated + self.deleted

    def mark(self, employee_id: int, day: date) -> None:
        self.dates_by_employee[employee_id].add(day)


def _existing_days(db: Session, employee_ids, dates, *, lock: bool = True) -> dict[tuple[int, date], WorkShiftDay]:
    """Các dòng ngày xếp ca đã có trong khoảng của các ô — đọc không khóa MỘT truy vấn.

    `lock` = khóa riêng các hàng ĐÃ CÓ theo khóa chính (`FOR UPDATE` + làm tươi hàng) tới hết giao dịch. Cố ý KHÔNG
    `FOR UPDATE` theo khoảng `(employee_id, work_date)`: khoảng chưa có hàng thì InnoDB khóa khoảng trống (gap lock), và hai
    lượt cùng tạo một ô mới sẽ chờ nhau rồi deadlock 1213. Ô mới chỉ dựa vào UNIQUE để phân định (lượt sau lỗi 1062).
    """
    dates = list(dates)
    if not dates:
        return {}
    query = db.query(WorkShiftDay).filter(WorkShiftDay.employee_id.in_(list(employee_ids)),
                                          WorkShiftDay.work_date >= min(dates),
                                          WorkShiftDay.work_date <= max(dates))
    rows = query.all()
    if lock and rows:
        rows = (db.query(WorkShiftDay).filter(WorkShiftDay.id.in_([r.id for r in rows]))
                .with_for_update().populate_existing().all())
    return {(r.employee_id, r.work_date): r for r in rows}


def existing_cells(db: Session, cells) -> set[tuple[int, date]]:
    """Trong `cells`, những ô ĐANG có ca xếp riêng (không khóa hàng) — để chốt đơn nghỉ chỉ xét ô thật sự bị đổi."""
    keys = set(cells)
    found = _existing_days(db, {k[0] for k in keys}, {k[1] for k in keys}, lock=False)
    return keys & set(found)


def upsert_items(db: Session, user, items: list[ShiftItem]) -> ShiftChange:
    """Đặt khung + ghi chú cho từng ô; ô đã có ca thì THAY cả danh sách khung, chưa có thì tạo dòng mới."""
    change = ShiftChange()
    latest = {(emp, day): (pairs, note) for emp, day, pairs, note in items}   # trùng ô: lấy lần cuối
    existing = _existing_days(db, {k[0] for k in latest}, {k[1] for k in latest})
    rows: dict[tuple[int, date], WorkShiftDay] = {}
    old_ids: list[int] = []
    for key, (_pairs, note) in latest.items():
        row = existing.get(key)
        if row is not None:
            old_ids.append(row.id)
            #  `updated_at` luôn được đặt lại để câu UPDATE chắc chắn chạy (giữ khóa hàng) dù ghi chú không đổi; mốc này
            #  còn dùng ở `comp_request_service` (ngày nghỉ do xếp ca sau khi đã qua không dùng để xin nghỉ bù).
            row.note, row.updated_by, row.updated_at = note, user.id, func.now()
            change.updated += 1
        else:
            row = WorkShiftDay(employee_id=key[0], work_date=key[1], note=note,
                               created_by=user.id, updated_by=user.id)
            db.add(row)
            change.created += 1
        rows[key] = row
        change.mark(*key)
    db.flush()   # UPDATE các hàng đã khóa TRƯỚC khi đụng khung của chúng; đồng thời cấp id cho dòng mới
    if old_ids:
        db.execute(delete(WorkShiftSegment).where(WorkShiftSegment.shift_day_id.in_(old_ids)))
    #  Dòng mới đã có id sau lần flush trên → gắn khung cho cả ô cũ lẫn ô mới.
    for key, (pairs, _note) in latest.items():
        for order, (start, end) in enumerate(pairs):
            db.add(WorkShiftSegment(shift_day_id=rows[key].id, start_hour=start, end_hour=end, sort_order=order))
    db.flush()
    return change


def delete_cells(db: Session, cells) -> ShiftChange:
    """Gỡ ca của các ô về MẪU LỊCH TUẦN; ô không có ca riêng thì tính vào `skipped` (gỡ hai lần không lỗi)."""
    change = ShiftChange()
    keys = list(dict.fromkeys(cells))
    existing = _existing_days(db, {k[0] for k in keys}, {k[1] for k in keys})
    ids: list[int] = []
    for key in keys:
        row = existing.get(key)
        if row is None:
            change.skipped += 1
            continue
        ids.append(row.id)
        change.deleted += 1
        change.mark(*key)
    if ids:
        db.execute(delete(WorkShiftSegment).where(WorkShiftSegment.shift_day_id.in_(ids)))
        db.execute(delete(WorkShiftDay).where(WorkShiftDay.id.in_(ids)))
    db.flush()
    return change


def plan_copy_week(db: Session, employee_ids, source_start: date, dest_start: date,
                   overwrite: bool) -> tuple[list[tuple[ShiftRecord, date]], int]:
    """Lập kế hoạch chép tuần: `([(ca ở tuần nguồn, ngày ở tuần đích)], số ô bỏ qua vì tuần đích đã có ca mà không ghi đè)`.

    CHỈ chép ngày đã có ca riêng ở tuần nguồn (kể cả ngày nghỉ do xếp ca); ngày theo mẫu lịch không chép. Hai truy vấn
    cố định (ca tuần nguồn, ca tuần đích).
    """
    offset = dest_start - source_start
    source = load_shift_records(db, employee_ids, source_start, source_start + timedelta(days=6))
    dest = load_shift_records(db, employee_ids, dest_start, dest_start + timedelta(days=6))
    plan, skipped = [], 0
    for (emp, day), rec in sorted(source.items()):
        if not overwrite and (emp, day + offset) in dest:
            skipped += 1
            continue
        plan.append((rec, day + offset))
    return plan, skipped


def apply_copy_plan(db: Session, user, plan, skipped: int) -> ShiftChange:
    """Ghi kế hoạch chép tuần (một lần ghi gộp)."""
    change = upsert_items(db, user, [(rec.employee_id, day, list(rec.segments), rec.note) for rec, day in plan])
    change.skipped = skipped
    return change
