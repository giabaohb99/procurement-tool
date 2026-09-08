"""KẾT SỔ CUỐI NĂM — số dư đi đâu, và bao giờ thì nó mất.

Trước 07/09/2026 ba ô *«Cho chuyển phép sang năm sau · Chuyển tối đa · Hết hạn
cuối tháng»* trên màn Loại nghỉ là **cột chết**: lưu được, hiện được, và không
chỗ nào trong mã đọc tới. Người khai danh mục bật công tắc lên rồi tin là 31/12
máy sẽ chuyển phép — 31/12 không có gì xảy ra cả. Tệp này là phần việc thật
đứng sau ba ô đó.

Hai nhịp, cố ý tách rời vì chúng chạy ở hai thời điểm khác nhau:

    31/12 (người bấm)   →  close_year()     dư → mang sang / quy đổi
    31/03 (tự, lúc chạm) →  expire_carried() phần mang sang chưa dùng thì mất

**Vì sao kết sổ là NÚT BẤM chứ không phải việc chạy nền.** Hệ này không có bộ
chạy nền, và một việc nền hỏng lặng lẽ vào đêm 31/12 thì tới tháng Ba mới có
người phát hiện — lúc đó cả công ty đã nghỉ theo một con số sai. Nút bấm thì
hỏng là thấy ngay, và bấm được lại. Cùng lý lẽ với `ensure_balance` (cấp phát
lúc chạm) và với nút *Cấp quỹ* của màn Quỹ phép.

**Chạy lại được, và LƯỢT SAU VÉT NỐT phần vừa quay lại.** Mỗi lượt chỉ mang đi
phần `remaining_days` còn lại, cộng dồn vào `carried_out_days` — bấm hai lần
liền nhau thì lượt hai không mang gì (số dư đã bằng 0), nhưng nếu giữa hai lượt
có đơn năm cũ bị **từ chối** hoặc đơn đã duyệt bị **hủy** thì mấy ngày quay lại
đó được đẩy sang tiếp. Bản đầu bỏ qua hẳn dòng đã kết sổ, nên số ngày ấy kẹt
vĩnh viễn ở năm cũ — năm cũ không ai tiêu được nữa, năm mới thì không thấy.
"""
import calendar
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from . import balance_service
from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .constants import (YEAR_END_CARRY, YEAR_END_CONVERT, YEAR_END_MOVING_MODES)

log = logging.getLogger(__name__)


def expiry_date(year: int, expire_month: int) -> date | None:
    """Ngày cuối cùng còn dùng được phần mang sang. `None` = không hết hạn.

    `year` là năm của dòng quỹ NHẬN (năm sau), `expire_month` là tháng chốt của
    chính năm đó — thông lệ tháng 3, tức hết 31/03.
    """
    if not expire_month:
        return None
    month = min(12, max(1, int(expire_month)))
    return date(year, month, calendar.monthrange(year, month)[1])


def expire_carried(row: LeaveBalance, leave_type: LeaveType,
                   today: date | None = None) -> float:
    """Thu hồi phần MANG SANG chưa dùng khi đã quá hạn. Trả về số ngày vừa mất.

    Luật ngầm ở đây phải nói ra: **phần mang sang được coi là tiêu TRƯỚC**. Sổ
    chỉ có một cục `used_days`, không biết ngày nào tiêu vào quỹ nào, nên phải
    chọn một phía — và chọn phía có lợi cho người lao động là phía đúng: phép
    mang sang là phép sắp hết hạn, ai cũng tiêu nó trước.

    Không đụng tới `carried_days` khi chưa quá hạn, và không bao giờ đụng lần
    hai: sau khi thu hồi, `carried_days` bằng đúng phần đã tiêu nên lần chạy sau
    không còn gì để mất.
    """
    if row.carried_days <= 0:
        return 0.0
    deadline = expiry_date(row.year, leave_type.carry_over_expire_month)
    if deadline is None or (today or date.today()) <= deadline:
        return 0.0

    consumed = row.used_days + row.pending_days
    keep = min(row.carried_days, consumed)
    lost = round(row.carried_days - keep, 2)
    if lost <= 0:
        return 0.0

    row.carried_days = round(keep, 2)
    row.carried_expired_days = round(row.carried_expired_days + lost, 2)
    return lost


def expire_rows(db: Session, rows: list[LeaveBalance],
                today: date | None = None) -> float:
    """`expire_carried` cho một mớ dòng — dùng ở các màn ĐỌC. Trả tổng ngày mất.

    Nơi gọi tự `commit`. Một truy vấn lấy hết loại nghỉ liên quan, không hỏi
    từng dòng: màn Quỹ phép trả về hàng trăm dòng một trang.
    """
    rows = [r for r in rows if r.carried_days > 0]
    if not rows:
        return 0.0
    types = {t.id: t for t in db.query(LeaveType)
             .filter(LeaveType.id.in_({r.leave_type_id for r in rows})).all()}
    total = 0.0
    for row in rows:
        leave_type = types.get(row.leave_type_id)
        if leave_type is not None:
            total += expire_carried(row, leave_type, today)
    return round(total, 2)


def _moved_days(row: LeaveBalance, leave_type: LeaveType) -> float:
    """Số ngày dư được phép mang đi LƯỢT NÀY. `0` = không có gì để mang.

    ⚠️ **Vét thêm chứ không bỏ qua dòng đã kết sổ** (ép tải 07/09/2026). Số dư
    năm cũ có thể TĂNG LẠI sau khi đã kết sổ, và cả hai đường đều là chuyện
    thường:

      · đơn của năm cũ còn treo lúc kết sổ, sau đó bị **từ chối** → trả lại phần
        giữ chỗ;
      · đơn đã duyệt của năm cũ bị **hủy** → hoàn lại phần đã trừ.

    Bản đầu chốt "dòng nào có `carried_out_days` thì bỏ qua", nên mấy ngày quay
    lại đó **kẹt vĩnh viễn ở năm cũ**: năm cũ không ai tiêu được nữa, mà năm mới
    thì không thấy chúng. Người lao động mất ngày phép do một thao tác hành
    chính họ không biết.

    Vét theo phần CÒN LẠI nên vẫn chạy lại được: kết sổ xong `remaining_days`
    bằng 0, bấm lần hai không mang thêm gì.
    """
    leftover = row.remaining_days
    if leftover <= 0:
        return 0.0
    cap = leave_type.carry_over_max_days or 0.0
    if cap <= 0:
        return round(leftover, 2)
    #  Trần tính trên TỔNG đã mang đi, không phải trên từng lượt — nếu không thì
    #  chạy lại đủ số lần là vượt trần.
    room = round(cap - row.carried_out_days, 2)
    return round(min(leftover, room), 2) if room > 0 else 0.0


def _target_type(db: Session, leave_type: LeaveType) -> LeaveType | None:
    """Loại nghỉ NHẬN. `None` = cấu hình hỏng, dòng đó phải bỏ qua chứ không đoán.

    Quy đổi vào một loại KHÔNG trừ quỹ là vô nghĩa — quỹ của loại đó không ai
    đọc, số ngày rơi vào đấy coi như mất mà lại báo là đã chuyển.
    """
    if leave_type.year_end_mode == YEAR_END_CARRY:
        return leave_type
    target = db.get(LeaveType, leave_type.convert_to_type_id or 0)
    if target is None or not target.counts_balance:
        return None
    return target


def close_year(db: Session, year: int, rows: list[LeaveBalance],
               actor: int = 0, *, today: date | None = None) -> dict:
    """Kết sổ `year` cho các dòng quỹ đã lọc sẵn (phạm vi do nơi gọi lo).

    Trả về bảng đếm để màn hình nói được chuyện gì vừa xảy ra: bao nhiêu dòng
    chuyển, bao nhiêu ngày, và **bao nhiêu dòng bị bỏ vì cấu hình hỏng** — con
    số cuối là con số hay bị nuốt nhất, mà nó chính là thứ cần sửa.
    """
    types = {t.id: t for t in db.query(LeaveType)
             .filter(LeaveType.id.in_({r.leave_type_id for r in rows})).all()} if rows else {}
    employees = {e.id: e for e in db.query(Employee)
                 .filter(Employee.id.in_({r.employee_id for r in rows})).all()} if rows else {}

    moved_rows, moved_days, credited_days, skipped_config = 0, 0.0, 0.0, 0
    for row in rows:
        leave_type = types.get(row.leave_type_id)
        if leave_type is None or leave_type.year_end_mode not in YEAR_END_MOVING_MODES:
            continue

        moved = _moved_days(row, leave_type)
        if moved <= 0:
            continue

        target_type = _target_type(db, leave_type)
        employee = employees.get(row.employee_id)
        if target_type is None or employee is None:
            skipped_config += 1
            log.warning("Kết sổ %s: bỏ dòng quỹ %s — loại đích hoặc hồ sơ nhân sự không dùng được",
                        year, row.id)
            continue

        ratio = leave_type.convert_ratio if leave_type.year_end_mode == YEAR_END_CONVERT else 1.0
        credit = round(moved * (ratio if ratio > 0 else 0.0), 2)
        if credit <= 0:
            skipped_config += 1
            continue

        target = balance_service.ensure_balance(db, employee, year + 1, target_type, actor)
        target.carried_days = round(target.carried_days + credit, 2)
        target.updated_by = actor
        #  CỘNG DỒN, không gán đè: lượt kết sổ sau chỉ vét phần vừa quay lại.
        row.carried_out_days = round(row.carried_out_days + moved, 2)
        row.updated_by = actor

        moved_rows += 1
        moved_days = round(moved_days + moved, 2)
        credited_days = round(credited_days + credit, 2)

    db.flush()
    return {
        "year": year,
        "row_count": len(rows),
        "moved_rows": moved_rows,
        "moved_days": moved_days,
        "credited_days": credited_days,
        "skipped_config": skipped_config,
    }
