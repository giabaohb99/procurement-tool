"""KIÊM NHIỆM loại CÔNG TY — nhật ký MỞ / ĐÓNG phạm vi (duoc-CR-756, người chủ chốt ở N3 của rà mã).

Một dòng loại Công ty đang bật công tắc `counts_scope` mở CẢ công ty B cho mọi entity bậc `company` / `dept` của
người đó (`core/auth.get_perm_profile` → `concurrent_companies`), mà người gán chỉ cần `employee.write` ở B, không cần
quyền Phân quyền tài khoản. Người chủ giữ luật gán đó nhưng đòi dấu vết riêng, dễ lọc ở nhật ký thao tác:

* `concurrent_scope_open`  — dòng loại Công ty BẮT ĐẦU mở phạm vi (tạo với công tắc bật, sửa tắt → bật, đổi sang công
  ty khác thì mở công ty mới, Áp quá trình công tác tạo dòng, giữ ghế công ty cũ khi đổi pháp nhân, hoàn tác lô trả lại dòng);
* `concurrent_scope_close` — dòng ĐÓNG phạm vi (sửa bật → tắt, xóa dòng đang bật, kết thúc do đổi pháp nhân, đổi sang công ty khác).

Dòng loại Phòng ban KHÔNG ghi (phòng của chính công ty chính, không mở thêm công ty nào). Đối tượng nhật ký là nhân sự
được gán (`entity = "employee"`). Ghi bằng `record(..., commit=False)`: đi CHUNG giao dịch với thay đổi gây ra nó,
rollback thì dòng nhật ký cũng mất — không ghi ma.

⚠️ "Mở" ở đây là mở theo CẤU HÌNH (dòng + công tắc), không đợi tới `from_date`: câu nhật ký nêu ngày bắt đầu để người đọc
biết lúc nào có hiệu lực thật. Xóa cả hồ sơ cha (`delete_all_of`) không ghi từng dòng — hồ sơ không còn để mở phạm vi.
"""
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.hr_concurrent_codes import ConcurrentKind

from .concurrent_model import EmployeeConcurrent
from .model import Employee

#  Mã hành động. `record(...)` bên dưới truyền CHỮ NGUYÊN VĂN (bài canh `test_bo_ma_hanh_dong_cr358` quét chữ, không đọc hằng).
ACTION_SCOPE_OPEN = "concurrent_scope_open"
ACTION_SCOPE_CLOSE = "concurrent_scope_close"


def scope_state(row: EmployeeConcurrent | None) -> int | None:
    """Công ty mà dòng này ĐANG mở phạm vi (id), hoặc `None`: chỉ loại Công ty + công tắc bật + có công ty."""
    if row is None or int(row.kind or 0) != int(ConcurrentKind.COMPANY) or not row.counts_scope:
        return None
    return int(row.company_id or 0) or None


def _who(emp: Employee) -> str:
    return f"{emp.code or ''} {emp.full_name or ''}".strip() or f"nhân sự #{emp.id}"


def _company_name(db: Session, company_id: int) -> str:
    from app.modules.company.model import Company

    return (db.query(Company.name).filter(Company.id == company_id).scalar()) or f"#{company_id}"


def _day(value) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def log_open(db: Session, actor_id: int, emp: Employee, row: EmployeeConcurrent) -> None:
    """Ghi `concurrent_scope_open` cho dòng `row` (đã qua `scope_state`)."""
    since = _day(row.from_date)
    note = f"kiêm nhiệm từ {since}" if since else "kiêm nhiệm không ghi ngày bắt đầu"
    record(db, actor_id, "employee", emp.id, "concurrent_scope_open",
           f"Mở phạm vi công ty {_company_name(db, int(row.company_id))} cho {_who(emp)} ({note})",
           doc_code=emp.code or "", commit=False)


def log_close(db: Session, actor_id: int, emp: Employee, company_id: int, reason: str) -> None:
    """Ghi `concurrent_scope_close` cho công ty `company_id` (id lấy từ `scope_state` TRƯỚC khi đổi)."""
    record(db, actor_id, "employee", emp.id, "concurrent_scope_close",
           f"Đóng phạm vi công ty {_company_name(db, company_id)} của {_who(emp)} ({reason})",
           doc_code=emp.code or "", commit=False)


def log_transition(db: Session, actor_id: int, emp: Employee, before: int | None, row: EmployeeConcurrent | None,
                   close_reason: str = "tắt công tắc phạm vi") -> None:
    """So trạng thái mở phạm vi TRƯỚC (`before` = `scope_state` chụp trước khi đổi) với SAU (dòng `row`, `None` = đã xóa).

    Khác nhau thì ghi đóng công ty cũ và/hoặc mở công ty mới; giống nhau (kể cả cùng tắt) thì không ghi gì.
    `close_reason` nêu vì sao đóng khi KHÔNG có công ty mới thay thế (còn nếu đổi sang công ty khác thì lý do là vậy).
    """
    after = scope_state(row)
    if before == after:
        return
    if before:
        log_close(db, actor_id, emp, before, "đổi sang công ty khác" if after else close_reason)
    if after:
        log_open(db, actor_id, emp, row)
