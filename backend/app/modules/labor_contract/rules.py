"""LUẬT THUẦN của HĐLĐ (không DB, không HTTP) — chuyển trạng thái, ràng buộc ngày, trạng thái hiệu lực.

Backend là chuẩn; FE chỉ hiển thị `effective_status` / `transitions` do serializer tính từ đây.

| Từ → Đến            | Điều kiện                                                          |
| DRAFT → SIGNED      | `date` = ngày ký (bắt buộc). KHÔNG đòi tệp (đại ca chốt 05/10/2026) |
| DRAFT → CANCELLED   | `reason` bắt buộc                                                   |
| SIGNED → TERMINATED | `date` = ngày chấm dứt ≥ start_date; `reason` bắt buộc              |
| khác                | 409                                                                 |
"""
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.labor_contract_codes import (FORBIDS_END_DATE, REQUIRES_END_DATE,
                                           LaborContractStatus as S, LaborContractType as T)

#  Từ trạng thái LƯU → các trạng thái được chuyển tới.
TRANSITIONS: dict[int, tuple[int, ...]] = {
    int(S.DRAFT): (int(S.SIGNED), int(S.CANCELLED)),
    int(S.SIGNED): (int(S.TERMINATED),),
}
#  Có thời hạn dài hơn mức này chỉ CẢNH BÁO (đại ca chốt), không chặn.
FIXED_TERM_WARN_MONTHS = 36


class RuleViolation(Exception):
    """Vi phạm luật nghiệp vụ. `status_code`: 400 thiếu/sai dữ liệu, 409 sai trạng thái."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class TransitionResult:
    """Các cột cần ghi khi chuyển trạng thái."""

    status: int
    changes: dict


def effective_status(status: int, end_date: date | None, today: date) -> int:
    """EXPIRED là SUY RA: SIGNED mà `end_date` đã qua. Không ghi DB, không cần job."""
    if int(status) == int(S.SIGNED) and end_date is not None and end_date < today:
        return int(S.EXPIRED)
    return int(status)


def allowed_transitions(status: int) -> tuple[int, ...]:
    return TRANSITIONS.get(int(status), ())


def check_dates(contract_type: int, start_date: date | None, end_date: date | None) -> None:
    """Ràng buộc ngày theo loại HĐ. Sai → ValueError (schema bọc thành 422, service bọc thành 400)."""
    if start_date is None:
        raise ValueError("Ngày bắt đầu là bắt buộc")
    if end_date is not None and end_date < start_date:
        raise ValueError("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")
    ctype = T(int(contract_type))
    if ctype in REQUIRES_END_DATE and end_date is None:
        raise ValueError("Loại hợp đồng này bắt buộc có ngày kết thúc")
    if ctype in FORBIDS_END_DATE and end_date is not None:
        raise ValueError("Hợp đồng không xác định thời hạn thì không có ngày kết thúc")


def duration_warnings(contract_type: int, start_date: date, end_date: date | None) -> list[str]:
    """Cảnh báo (không chặn): xác định thời hạn > 36 tháng."""
    if int(contract_type) != int(T.FIXED_TERM) or end_date is None:
        return []
    #  Thời hạn tính CẢ ngày kết thúc: 01/01/2026 → 31/12/2028 đúng 36 tháng, → 01/01/2029 đã là 36 tháng 1 ngày.
    last = end_date + timedelta(days=1)
    months = (last.year - start_date.year) * 12 + (last.month - start_date.month)
    if last.day > start_date.day:
        months += 1  # lẻ ngày tính tròn lên
    if months > FIXED_TERM_WARN_MONTHS:
        return [f"Hợp đồng xác định thời hạn nên không quá {FIXED_TERM_WARN_MONTHS} tháng "
                f"(đang là khoảng {months} tháng)."]
    return []


def plan_transition(*, status: int, start_date: date, to_status: int, on_date: date | None,
                    reason: str) -> TransitionResult:
    """Kiểm điều kiện chuyển và trả cột cần ghi. Sai → RuleViolation."""
    to_status = int(to_status)
    if to_status not in allowed_transitions(status):
        raise RuleViolation("Không thể chuyển hợp đồng sang trạng thái này từ trạng thái hiện tại.", 409)
    reason = (reason or "").strip()

    if to_status == int(S.SIGNED):
        if on_date is None:
            raise RuleViolation("Cần nhập ngày ký để chuyển sang Đã ký.")
        return TransitionResult(to_status, {"sign_date": on_date})
    if to_status == int(S.CANCELLED):
        if not reason:
            raise RuleViolation("Cần nhập lý do hủy hợp đồng.")
        return TransitionResult(to_status, {"terminate_reason": reason})
    # TERMINATED
    if on_date is None:
        raise RuleViolation("Cần nhập ngày chấm dứt hợp đồng.")
    if on_date < start_date:
        raise RuleViolation("Ngày chấm dứt không được trước ngày bắt đầu hợp đồng.")
    if not reason:
        raise RuleViolation("Cần nhập lý do chấm dứt hợp đồng.")
    return TransitionResult(to_status, {"terminated_date": on_date, "terminate_reason": reason})
