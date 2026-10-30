"""CẢNH BÁO HỢP ĐỒNG LAO ĐỘNG SẮP HẾT HẠN / ĐÃ HẾT HẠN (duoc-CR-620).

Một nguồn cho BA chỗ đọc: chuông cảnh báo (`alert.controller.build`), tab Việc cần làm
(`dashboard.controller.build_my_tasks` — chỗ DUY NHẤT ẩn được dòng chuông, nên phải là tập cha
của chuông) và thẻ "Hợp đồng sắp hết hạn" ở Tổng quan Nhân sự (`GET /api/labor-contracts/expiring`).
Ba chỗ mà tự lọc riêng thì sớm muộn sẽ lệch nhau — chuông báo một số, thẻ đếm một số.

Tính tại chỗ mỗi lần đọc, không có job, không ghi DB — cùng lối với trạng thái "Hết hạn"
suy ra ở `rules.effective_status`.

Hợp đồng NÀO bị báo:
  - Đã ký (SIGNED), có ngày kết thúc, chưa xóa mềm, nằm trong phạm vi người xem;
  - ngày kết thúc ≤ hôm nay + `WARN_DAYS` — kể cả đã qua: hết hạn mà người ta vẫn đi làm
    là đang làm việc không có hợp đồng, phải báo tới khi Nhân sự lập HĐ mới hoặc chấm dứt.
Hợp đồng KHÔNG bị báo dù sắp hết:
  - Đã có HĐ NỐI TIẾP của cùng người (bắt đầu sau HĐ này) — Nhân sự đã xử rồi, báo tiếp chỉ
    là tiếng ồn khiến người ta tắt chuông. HĐ nối tiếp ĐÃ KÝ thì luôn che; bản NHÁP chỉ che
    khi HĐ cũ CHƯA hết hạn: nháp là "đang soạn gia hạn", nhưng hết hạn rồi mà nháp vẫn nằm
    đó thì người ta đang đi làm không có HĐ nào có hiệu lực — nháp bị quên không được che;
  - Nhân sự đã nghỉ việc (`status = resigned` hoặc `is_active` tắt) — HĐ của người đã đi
    không cần gia hạn; quên bấm "Chấm dứt" thì là việc dọn sổ, không phải việc gấp.

Mức: còn ≤ `DANGER_DAYS` ngày hoặc đã quá hạn → `danger`; còn lại → `warn`.
`DANGER_DAYS = 15` vì Bộ luật Lao động 2019 Điều 45 buộc báo người lao động ít nhất 15 ngày
trước khi HĐ xác định thời hạn hết hạn — qua mốc đó là đã trễ hạn báo.

Số truy vấn CỐ ĐỊNH (3) bất kể bao nhiêu hợp đồng: HĐ trong cửa sổ · HĐ nối tiếp · hồ sơ.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.scoping import apply_scope, not_deleted_cond
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED

from .model import LaborContract

ENTITY = "labor_contract"
#: Báo trước bao nhiêu ngày (mức vàng).
WARN_DAYS = 30
#: Còn từng này ngày trở xuống là mức đỏ — mốc báo trước 15 ngày của Điều 45 BLLĐ 2019.
DANGER_DAYS = 15
#: Trần cửa sổ của đường API — người gọi xin dài hơn thì cắt về đây.
MAX_WINDOW_DAYS = 180


@dataclass(frozen=True)
class ExpiringContract:
    id: int
    code: str
    contract_no: str
    contract_type: int
    employee_id: int
    employee_code: str
    employee_name: str
    end_date: date
    days_left: int        # âm = đã quá hạn bấy nhiêu ngày
    level: str            # "danger" | "warn"

    def alert_title(self) -> str:
        """Dòng chữ trên chuông. Tên người đi trước mã HĐ — Nhân sự nhớ người, không nhớ mã."""
        who = f"{self.employee_name} ({self.employee_code})" if self.employee_code else self.employee_name
        end = self.end_date.strftime("%d/%m/%Y")
        if self.days_left < 0:
            return f"HĐLĐ ĐÃ HẾT HẠN {-self.days_left} ngày: {who} · {self.code} (hết {end})"
        if self.days_left == 0:
            return f"HĐLĐ hết hạn HÔM NAY: {who} · {self.code}"
        return f"HĐLĐ còn {self.days_left} ngày: {who} · {self.code} (hết {end})"

    def alert_link(self) -> str:
        #  Đường v1 `/employees/...`: chuông v2 tự đổi sang `/hr/employees/...` (`toAppPath`),
        #  bản v1 mở được hồ sơ (bỏ qua `?tab`) — một link chạy cả hai giao diện.
        return f"/employees/{self.employee_id}?tab=labor-contracts"


def level_of(days_left: int) -> str:
    return "danger" if days_left <= DANGER_DAYS else "warn"


def _has_successor(rows, start_date: date, *, overdue: bool) -> bool:
    """Có HĐ nối tiếp (bắt đầu SAU HĐ đang xét) đủ để coi là Nhân sự đã xử chưa — xem docstring tệp."""
    for start, status in rows:
        if start <= start_date:
            continue
        if status == int(S.SIGNED) or not overdue:
            return True
    return False


def find_expiring(db: Session, today: date, *, user=None, profile: dict | None = None,
                  within_days: int = WARN_DAYS) -> list[ExpiringContract]:
    """HĐLĐ cần báo, xếp hết hạn sớm nhất lên đầu. `user=None` (worker / kiểm) = không lọc phạm vi.

    Có `user` thì LUÔN lọc phạm vi — thiếu `profile` thì tự dựng, không lặng lẽ trả hết."""
    within_days = max(0, min(int(within_days), MAX_WINDOW_DAYS))
    query = db.query(LaborContract).filter(
        LaborContract.status == int(S.SIGNED),
        LaborContract.end_date.isnot(None),
        LaborContract.end_date <= today + timedelta(days=within_days),
    )
    if user is not None:
        profile = profile if profile is not None else get_perm_profile(db, user)
        query = apply_scope(query, LaborContract, ENTITY, user, profile)
    else:
        cond = not_deleted_cond(LaborContract)
        if cond is not None:
            query = query.filter(cond)
    rows = query.all()
    if not rows:
        return []

    emp_ids = {r.employee_id for r in rows}
    #  HĐ nối tiếp đọc KHÔNG qua phạm vi: người xem chỉ thấy HĐ pháp nhân A nhưng HĐ mới lập ở
    #  pháp nhân B (điều chuyển) vẫn là bằng chứng Nhân sự đã xử — chỉ dùng để LOẠI, không lộ gì ra.
    later = db.query(LaborContract.employee_id, LaborContract.start_date, LaborContract.status).filter(
        LaborContract.employee_id.in_(emp_ids),
        LaborContract.status.in_((int(S.DRAFT), int(S.SIGNED))),
    )
    cond = not_deleted_cond(LaborContract)
    if cond is not None:
        later = later.filter(cond)
    successors: dict[int, list[tuple[date, int]]] = {}
    for emp_id, start, status in later.all():
        successors.setdefault(emp_id, []).append((start, int(status)))

    employees = {e.id: e for e in db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}

    out: list[ExpiringContract] = []
    for r in rows:
        emp = employees.get(r.employee_id)
        if emp is None or not emp.is_active or (emp.status or "") == STATUS_RESIGNED:
            continue
        days_left = (r.end_date - today).days
        if _has_successor(successors.get(r.employee_id, ()), r.start_date, overdue=days_left < 0):
            continue
        out.append(ExpiringContract(
            id=r.id, code=r.code, contract_no=r.contract_no or "", contract_type=int(r.contract_type),
            employee_id=r.employee_id, employee_code=emp.code or "", employee_name=emp.full_name or "",
            end_date=r.end_date, days_left=days_left, level=level_of(days_left),
        ))
    out.sort(key=lambda c: (c.end_date, c.id))
    return out
