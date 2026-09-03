"""QUỸ PHÉP — cấp phát, tính thâm niên, giữ chỗ và trừ thật.

Ràng buộc §6.1 của kế hoạch: *số phép còn lại phải hiện NGAY trên form lúc nộp*.
`remaining()` ở đây là hàm trả lời câu đó, và là hàm duy nhất — đừng cộng trừ
các cột của `tab_leave_balance` ở nơi khác.

Sổ quỹ chạy theo bốn nhịp, khớp với bốn kết cục của bộ máy duyệt:

    gửi duyệt   →  reserve()   pending_days += n     (giữ chỗ)
    duyệt xong  →  consume()   pending −= n, used += n
    từ chối/trả về/rút/hủy → release()  pending −= n

Thiếu nhịp GIỮ CHỖ thì nộp mười đơn liền tay đều lọt, vì đơn nào cũng thấy quỹ
còn nguyên. Đó là lỗi cổ điển của mọi hệ nghỉ phép và nó chỉ lộ ra khi đã có
người nghỉ thừa hai tuần.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .balance_model import LeaveBalance
from .catalog_model import LeaveType, LeaveTypeSeniority


def seniority_years(hire_date: date | None, at: date | None = None) -> int:
    """Số năm làm việc tính TRÒN, mốc mặc định là 01/01 của năm đang xét.

    Q4 của kế hoạch: hồ sơ chưa có `hire_date` thì coi như **0 năm** chứ không
    chặn — chặn thì cả công ty không cấp được quỹ cho tới khi Nhân sự nhập bù
    hàng trăm dòng. Màn Quỹ phép có trách nhiệm trưng cảnh báo ra.
    """
    if hire_date is None:
        return 0
    at = at or date(date.today().year, 1, 1)
    years = at.year - hire_date.year
    #  Chưa tới ngày kỷ niệm trong năm thì chưa đủ năm đó.
    if (at.month, at.day) < (hire_date.month, hire_date.day):
        years -= 1
    return max(0, years)


def seniority_days(db: Session, leave_type_id: int, years: int) -> float:
    """Số ngày CỘNG THÊM theo bậc thâm niên. `0.0` khi loại nghỉ không khai bậc nào.

    Lấy bậc **cao nhất** khớp được, không cộng dồn các bậc: bảng khai
    *"từ 5 năm: +1"* và *"từ 10 năm: +2"* nghĩa là người 10 năm được +2, không
    phải +3. Cộng dồn thì mỗi lần thêm một bậc là mọi người đang có thâm niên
    cao tự nhiên được thêm ngày — không ai chủ ý muốn thế.

    Khoảng nửa mở: khớp khi `years_from <= years` và (`years_to = 0` hoặc
    `years < years_to`). `years_to = 0` là bậc cuối, không có trần trên.
    """
    tiers = (db.query(LeaveTypeSeniority)
             .filter(LeaveTypeSeniority.leave_type_id == leave_type_id)
             .order_by(LeaveTypeSeniority.years_from.asc())
             .all())
    best = 0.0
    for tier in tiers:
        if years < tier.years_from:
            continue
        if tier.years_to and years >= tier.years_to:
            continue
        best = max(best, float(tier.extra_days or 0.0))
    return round(best, 2)


def get_balance(db: Session, employee_id: int, year: int,
                leave_type_id: int) -> LeaveBalance | None:
    """Dòng quỹ, hoặc `None` nếu chưa cấp phát. KHÔNG tự tạo — xem `ensure_balance`."""
    return (db.query(LeaveBalance)
            .filter(LeaveBalance.employee_id == employee_id,
                    LeaveBalance.year == year,
                    LeaveBalance.leave_type_id == leave_type_id)
            .first())


def ensure_balance(db: Session, employee, year: int, leave_type: LeaveType,
                   actor: int = 0) -> LeaveBalance:
    """Lấy dòng quỹ, tự cấp phát nếu chưa có. Không commit — nơi gọi tự chốt.

    Cấp phát tự động lúc chạm tới, thay vì một công việc nền chạy đêm 31/12:
    hệ này không có bộ chạy nền, và một công việc nền hỏng lặng lẽ thì tới tháng
    Hai mới có người phát hiện. Cấp lúc chạm thì sai cũng lộ ngay tại chỗ.

    Q1 của kế hoạch: cấp **một lần đầu năm**, cấn thâm niên tính tại 01/01 —
    không cộng dần theo tháng làm việc. Đổi được sau vì nằm gọn trong hàm này.
    """
    existing = get_balance(db, employee.id, year, leave_type.id)
    if existing is not None:
        return existing

    years = seniority_years(getattr(employee, "hire_date", None), date(year, 1, 1))
    row = LeaveBalance(
        employee_id=employee.id, year=year, leave_type_id=leave_type.id,
        company_id=getattr(employee, "company_id", 0) or 0,
        allocated_days=float(leave_type.annual_quota_days or 0.0),
        seniority_days=seniority_days(db, leave_type.id, years),
        created_by=actor, updated_by=actor,
    )
    db.add(row)
    db.flush()
    return row


def remaining(db: Session, employee_id: int, year: int, leave_type_id: int) -> float:
    """Số ngày còn nghỉ được. Chưa cấp phát thì trả `0.0`.

    `0.0` chứ không phải `None`: nơi gọi là form nhập và bản in, cả hai đều phải
    hiện một con số. Phân biệt "chưa cấp quỹ" hay "hết phép" là việc của màn Quỹ
    phép, nơi có chỗ để giải thích.
    """
    row = get_balance(db, employee_id, year, leave_type_id)
    return row.remaining_days if row else 0.0


def check_enough(db: Session, employee, year: int, leave_type: LeaveType,
                 days: float, *, exclude_days: float = 0.0) -> None:
    """Chặn nếu nghỉ vượt quỹ — QĐ-NP2: **không cho ứng phép**.

    Vượt thì đổi sang loại *Nghỉ không lương*, không ghi nợ. Ghi nợ nghe thì
    tiện nhưng kéo theo cả một sổ công nợ phép và luật trừ lương khi nghỉ việc;
    chủ đầu tư chốt là không làm.

    `exclude_days` là phần ĐANG giữ chỗ của chính tờ đơn này — dùng khi SỬA một
    đơn đã gửi duyệt, nếu không thì số ngày cũ bị tính hai lần và sửa từ 3 ngày
    xuống 2 ngày cũng báo hết phép.

    Loại nghỉ không trừ quỹ (`counts_balance = False`) thì bỏ qua, kể cả khi
    người ta chưa có dòng quỹ nào.
    """
    if not leave_type.counts_balance:
        return

    row = ensure_balance(db, employee, year, leave_type)
    available = round(row.remaining_days + exclude_days, 2)
    if days > available:
        raise HTTPException(
            400,
            f"Không đủ phép: «{leave_type.name}» còn {available} ngày, "
            f"đơn này xin {days} ngày. Muốn nghỉ tiếp thì chọn loại «Nghỉ không lương».")


def reserve(db: Session, employee, year: int, leave_type: LeaveType,
            days: float, actor: int = 0) -> None:
    """GIỮ CHỖ khi gửi duyệt. Xem đầu tệp về vì sao nhịp này bắt buộc."""
    if not leave_type.counts_balance or days <= 0:
        return
    row = ensure_balance(db, employee, year, leave_type, actor)
    row.pending_days = round(row.pending_days + days, 2)
    row.updated_by = actor


def release(db: Session, employee_id: int, year: int, leave_type_id: int,
            days: float, actor: int = 0) -> None:
    """Trả lại phần giữ chỗ — đơn bị từ chối / trả về / rút / hủy.

    Kẹp ở `0` chứ không cho âm: `pending_days` âm nghĩa là quỹ tự phình ra, và
    nó sẽ phình lặng lẽ. Rơi vào đây là sổ đã lệch từ trước — kẹp lại để nó
    không lệch thêm, phần điều tra thuộc về dữ liệu chứ không thuộc về hàm này.
    """
    row = get_balance(db, employee_id, year, leave_type_id)
    if row is None or days <= 0:
        return
    row.pending_days = round(max(0.0, row.pending_days - days), 2)
    row.updated_by = actor


def consume(db: Session, employee_id: int, year: int, leave_type_id: int,
            days: float, actor: int = 0) -> None:
    """Đơn được DUYỆT: chuyển từ giữ chỗ sang đã dùng.

    Trừ `pending` rồi cộng `used` trong cùng một nhịp — tách hai chỗ thì có một
    khoảnh khắc quỹ hiện thừa hoặc thiếu đúng số ngày đó, và người mở màn Quỹ
    phép đúng lúc ấy sẽ báo lỗi.
    """
    row = get_balance(db, employee_id, year, leave_type_id)
    if row is None or days <= 0:
        return
    row.pending_days = round(max(0.0, row.pending_days - days), 2)
    row.used_days = round(row.used_days + days, 2)
    row.updated_by = actor


def refund_used(db: Session, employee_id: int, year: int, leave_type_id: int,
                days: float, actor: int = 0) -> None:
    """Hoàn lại phần ĐÃ TRỪ — huỷ một đơn đã duyệt.

    Có thật: người xin nghỉ tuần sau, tuần này đổi ý. Không có nhịp này thì
    ngày phép của họ mất luôn và Nhân sự phải bù bằng cột «điều chỉnh tay», tức
    là sửa sổ bằng tay cho một việc lẽ ra tự chạy.
    """
    row = get_balance(db, employee_id, year, leave_type_id)
    if row is None or days <= 0:
        return
    row.used_days = round(max(0.0, row.used_days - days), 2)
    row.updated_by = actor
