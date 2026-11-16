"""Phần dùng chung của hai tool CA LÀM VIỆC (duoc-CR-761): đọc khoảng ngày, dựng ngày cho nhiều người, bày gọn cho model.

* **Không phân giải lại lịch ở đây.** Ngày của MỘT hay NHIỀU người lấy thẳng `work_schedule.shift_view.build_days_many`
  (cùng chỗ dựng với thẻ Ca làm việc ở Trang cá nhân; `build_my_days` chỉ là bản một người của nó), số truy vấn cố định.
* **Tổng giờ** = giờ của các ngày phải đi làm: ngày xếp ca (kể cả ngày lễ — người xếp ca đã chủ động xếp) + ngày theo
  mẫu tuần KHÔNG trùng ngày lễ.
"""
from datetime import date, timedelta

from app.core.vn_time import vn_today
from app.modules.work_schedule.shift_view import build_days_many  # noqa: F401 (tái xuất cho work_shift_tool)

from .leave_taken_schedule import WEEKDAY_LABELS

SOURCE_SHIFT = "Xếp ca theo ngày"
SOURCE_TEMPLATE = "Mẫu lịch tuần"
SHORT_WEEKDAYS = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")

RANGE_PARAMS = {
    "from_date": {"type": "string", "description": "Từ ngày YYYY-MM-DD. Bỏ trống = thứ Hai của tuần (theo week_offset)."},
    "to_date": {"type": "string", "description": "Đến ngày YYYY-MM-DD. Bỏ trống = 6 ngày sau Từ ngày (hết tuần)."},
    "week_offset": {"type": "integer", "description": "Chỉ dùng khi bỏ trống from_date: 0 = tuần này (mặc định), "
                                                     "1 = tuần sau, -1 = tuần trước."},
}


def _parse_date(raw) -> date | None:
    try:
        value = date.fromisoformat(str(raw).strip()[:10])
    except (TypeError, ValueError):
        return None
    return value if 2000 <= value.year <= 2100 else None


def _offset(raw) -> int:
    try:
        return max(-52, min(int(raw), 52))
    except (TypeError, ValueError):
        return 0


def parse_range(args: dict, max_days: int) -> tuple[date, date] | str:
    """`(từ, đến)` theo tham số; mặc định tuần này T2–CN giờ VN. Sai → câu lỗi tiếng Việt (chuỗi)."""
    raw_from, raw_to = args.get("from_date"), args.get("to_date")
    if raw_from:
        start = _parse_date(raw_from)
        if start is None:
            return "Từ ngày không hợp lệ — dùng dạng YYYY-MM-DD (ví dụ 2026-11-16)."
    else:
        today = vn_today()
        start = today - timedelta(days=today.weekday()) + timedelta(weeks=_offset(args.get("week_offset")))
    if raw_to:
        end = _parse_date(raw_to)
        if end is None:
            return "Đến ngày không hợp lệ — dùng dạng YYYY-MM-DD."
    else:
        end = start + timedelta(days=min(6, max_days - 1))
    if end < start:
        return "Đến ngày phải sau hoặc bằng Từ ngày."
    if (end - start).days + 1 > max_days:
        return f"Chỉ xem tối đa {max_days} ngày một lần — chia nhỏ khoảng ngày."
    return start, end


def counts_as_work(day: dict) -> bool:
    """Ngày phải đi làm: có khung giờ, và không phải ngày lễ theo mẫu tuần (ca xếp vào ngày lễ vẫn tính)."""
    return bool(day["segments"]) and (day["is_shift"] or not day["is_holiday"])


def compact_day(day: dict) -> dict:
    """Một ngày của CHÍNH người hỏi, bày gọn cho model: ngày, thứ, nguồn, khung giờ, số giờ; cờ chỉ hiện khi đúng."""
    out = {"date": day["date"], "weekday": WEEKDAY_LABELS[day["weekday"]],
           "source": SOURCE_SHIFT if day["is_shift"] else SOURCE_TEMPLATE,
           "segments": day["segments"], "hours": day["hours"] if counts_as_work(day) else 0}
    if day["is_day_off"]:
        out["is_day_off"] = True
    if day["is_holiday"]:
        out["holiday_name"] = day["holiday_name"] or "Ngày lễ"
    if day["note"]:
        out["note"] = day["note"]
    if not day["is_shift"]:
        out["schedule_name"] = day["schedule_name"]
    return out


def compact_team_day(day: dict) -> dict:
    """Một ô người × ngày cho bản NHIỀU người — khóa ngắn, chỉ cờ đúng mới hiện (đo local: ~120 ký tự / ô kể cả phần đầu
    mỗi người, so với ~170 của khuôn đủ; kết quả phải vừa một lượt trả cho app AI ngoài, ai-CR-228)."""
    out = {"date": day["date"], "weekday": SHORT_WEEKDAYS[day["weekday"]], "segments": day["segments"],
           "hours": day["hours"] if counts_as_work(day) else 0}
    if day["is_shift"]:
        out["shift"] = True
    if day["is_day_off"]:
        out["off"] = True
    if day["is_holiday"]:
        out["holiday"] = day["holiday_name"] or "Ngày lễ"
    if day["note"]:
        out["note"] = day["note"]
    return out


def summarize_days(days: list[dict]) -> dict:
    """Tổng giờ, số ngày phải đi làm, các ngày xếp ca riêng (để model nói ngày nào khác mẫu tuần)."""
    work = [d for d in days if counts_as_work(d)]
    return {"total_hours": round(sum(d["hours"] for d in work), 2), "work_days": len(work),
            "shift_dates": [d["date"] for d in days if d["is_shift"]]}
