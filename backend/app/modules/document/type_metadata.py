"""HÌNH DẠNG `metadata` THEO TỪNG LOẠI VĂN BẢN — nguồn chân lý duy nhất.

`tab_document.metadata` là ô mở, và ô mở thì sáu tháng nữa không ai biết trong đó
có gì. Nên hình dạng của nó khai ở ĐÂY, backend kiểm trước khi ghi, và **khóa lạ
bị loại bỏ chứ không lưu**. Module Nghỉ phép sau này đọc thẳng từ đây mà không
phải đoán.

Khai theo **mã loại văn bản** (`tab_doc_type.code`) chứ không theo id: id khác
nhau giữa các môi trường, còn mã thì là thứ người ta gõ vào danh mục và giữ
nguyên.

⚠️ Đây là kiểm tra hình dạng, KHÔNG phải luật nghiệp vụ. "Ngày về phải sau ngày
đi" nằm ở đây vì nó thuộc về chính tờ đơn; còn "còn đủ ngày phép không" thì phải
chờ module chấm công, không đoán mò ở đây.
"""
from datetime import date

from fastapi import HTTPException

from app.core.leave_codes import (END_DAY_WORK_CREDIT, START_DAY_WORK_CREDIT,
                                  same_day_work_credit, LEAVE_SESSION_SET,
                                  LEAVE_TYPE_SET)

#  Mã loại văn bản — dùng ở nhiều nơi nên đặt hằng, đừng gõ chuỗi rải rác.
LEAVE_DOC_TYPE = "GNP"

#  Loại nghỉ và buổi khai ở `core/leave_codes.py` để `gen_status_ts.py` sinh bản
#  TypeScript — danh sách này tuyệt đối không gõ tay hai lần ở hai đầu.
SESSION_FULL_DAY = "full"
SESSION_MORNING = "morning"
SESSION_AFTERNOON = "afternoon"
ANNUAL_LEAVE = "annual"


def _string_in_set(value, allowed, name: str, default: str) -> str:
    """Giá trị phải nằm trong bộ mã đã khai. Bỏ trống thì lấy mặc định."""
    code = (str(value).strip() if value not in (None, "") else "") or default
    if code not in allowed.values:
        raise HTTPException(
            400, f"«{name}» không hợp lệ. Giá trị nhận: {', '.join(sorted(allowed.values))}")
    return code


def _number(value, name: str, *, required: bool) -> int:
    if value in (None, ""):
        if required:
            raise HTTPException(400, f"Thiếu «{name}»")
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"«{name}» phải là số")


def _date(value, name: str) -> str:
    """Nhận `YYYY-MM-DD`, trả lại đúng chuỗi đó. Ngày lưu dạng chuỗi trong JSON."""
    if not value:
        raise HTTPException(400, f"Thiếu «{name}»")
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        raise HTTPException(400, f"«{name}» không phải ngày hợp lệ (cần YYYY-MM-DD)")


def suggested_days(from_date: str, to_date: str, from_session: str, to_session: str) -> float:
    """Số ngày công GỢI Ý — đếm cả cuối tuần và ngày lễ.

    ⚠️ Cố ý KHÔNG trừ thứ Bảy / Chủ nhật / ngày lễ: hệ chưa có bảng lịch làm việc
    (mà mỗi pháp nhân lại làm việc khác nhau), nên đoán ra một con số trông có vẻ
    chính xác còn tệ hơn đưa ra con số thô để người ta sửa. Ô này người dùng sửa
    đè được, và người duyệt là chốt cuối.

    Hai đầu tra **hai bảng khác nhau** (vá 07/09/2026) — ô buổi nói MỐC bắt đầu /
    kết thúc, xem `core/leave_codes.START_DAY_WORK_CREDIT`.
    """
    d1, d2 = date.fromisoformat(from_date), date.fromisoformat(to_date)
    if d1 == d2:
        #  Trong CÙNG một ngày thì hai ô buổi cùng nói về ngày ấy — phải xét CẢ
        #  HAI. Lấy riêng `from_session` như bản cũ thì «Cả ngày → Sáng» ra
        #  nguyên một ngày trong khi người khai kết thúc lúc hết buổi sáng.
        return same_day_work_credit(from_session, to_session)
    full_days = (d2 - d1).days - 1
    return (max(0.0, full_days)
            + START_DAY_WORK_CREDIT.get(from_session, 1.0)
            + END_DAY_WORK_CREDIT.get(to_session, 1.0))


def _check_leave(payload: dict, creator_employee_id: int | None) -> dict:
    """Tám ô của Giấy nghỉ phép. Trả về dict ĐÃ LÀM SẠCH, đúng thứ được lưu."""
    from_date = _date(payload.get("from_date"), "Từ ngày")
    to_date = _date(payload.get("to_date"), "Đến ngày")
    if to_date < from_date:
        raise HTTPException(400, "«Đến ngày» phải bằng hoặc sau «Từ ngày»")

    from_session = _string_in_set(payload.get("from_session"), LEAVE_SESSION_SET,
                              "Buổi bắt đầu", SESSION_FULL_DAY)
    to_session = _string_in_set(payload.get("to_session"), LEAVE_SESSION_SET,
                              "Buổi kết thúc", SESSION_FULL_DAY)
    if from_date == to_date and from_session == SESSION_AFTERNOON and to_session == SESSION_MORNING:
        raise HTTPException(400, "Nghỉ từ buổi chiều đến buổi sáng cùng ngày là khoảng trống")

    #  Người nghỉ mặc định là người đang lập đơn. Lập hộ người khác vẫn được —
    #  trợ lý / hành chính lập hộ là việc có thật — nên cho khai tường minh.
    leave_taker = _number(payload.get("employee_id"), "Người nghỉ", required=False) \
        or (creator_employee_id or 0)
    if not leave_taker:
        raise HTTPException(400, "Chưa xác định được người nghỉ")

    reason = (payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Thiếu «Lý do nghỉ»")

    #  Số ngày: lấy của người dùng nếu họ sửa, không thì tự tính.
    raw = payload.get("total_days")
    try:
        day_count = float(raw) if raw not in (None, "") else suggested_days(
            from_date, to_date, from_session, to_session)
    except (TypeError, ValueError):
        raise HTTPException(400, "«Tổng số ngày» phải là số")
    if day_count <= 0:
        raise HTTPException(400, "«Tổng số ngày» phải lớn hơn 0")

    cleaned = {
        "employee_id": leave_taker,
        "leave_type": _string_in_set(payload.get("leave_type"), LEAVE_TYPE_SET,
                                      "Loại nghỉ", ANNUAL_LEAVE),
        "from_date": from_date,
        "from_session": from_session,
        "to_date": to_date,
        "to_session": to_session,
        "total_days": day_count,
        "reason": reason[:500],
        "handover_employee_id": _number(payload.get("handover_employee_id"),
                                    "Người bàn giao", required=False),
        "contact_phone": (payload.get("contact_phone") or "").strip()[:30],
    }
    lines = _leave_lines(payload.get("leave_lines"))
    if lines:
        cleaned["leave_lines"] = lines
    return cleaned


#  Trần số dòng ghi vào giấy — khớp `leave/request_service.MAX_LINES`. Lệch nhau
#  thì đơn lưu đủ mà giấy cắt bớt, và không ai thấy chỗ mất.
MAX_LEAVE_LINES = 10


def _leave_lines(raw) -> list[dict]:
    """Bản kê «loại nghỉ nào mấy ngày» của đơn khai NHIỀU loại (07/09/2026).

    Chỉ ghi khi có **từ hai dòng trở lên**: đơn một loại thì ô `leave_type` ở
    trên đã nói đủ, và thêm một danh sách một phần tử chỉ làm mọi chỗ đọc giấy
    phải xử lý hai hình dạng cho cùng một thứ.

    ⚠️ Mã loại nghỉ ở đây **không đối chiếu `LEAVE_TYPE_SET`**, khác ô
    `leave_type` phía trên. Đây là bản CHÉP LẠI của tờ đơn — nơi đã kiểm đủ và
    đã được người có thẩm quyền ký. Bắt nó qua bộ mã cố định nghĩa là một loại
    nghỉ do quản trị tự thêm sẽ làm hỏng việc sinh giấy cho một quyết định đã
    xong; giấy là hồ sơ lưu, chặn ở đó không cứu được gì.
    """
    if not isinstance(raw, list):
        return []
    lines = []
    for item in raw[:MAX_LEAVE_LINES]:
        if not isinstance(item, dict):
            continue
        try:
            days = float(item.get("days") or 0)
        except (TypeError, ValueError):
            continue
        if days <= 0:
            continue
        lines.append({
            "leave_type": str(item.get("leave_type") or "").strip()[:30],
            "name": str(item.get("name") or "").strip()[:100],
            "days": days,
        })
    return lines if len(lines) > 1 else []


#  mã loại → hàm kiểm. Loại không có mặt ở đây thì KHÔNG nhận metadata.
_VALIDATORS = {LEAVE_DOC_TYPE: _check_leave}


def sanitize(type_code: str, payload: dict | None,
             creator_employee_id: int | None = None) -> dict | None:
    """Lọc metadata gửi lên theo hình dạng của loại văn bản.

    * loại CHƯA khai hình dạng → trả `None`, tức là **không lưu gì**. Không im
      lặng nhận bừa: nhận bừa thì mỗi người gửi một hình dạng, và module đọc sau
      này phải đỡ hết mọi biến thể.
    * gửi rỗng cho loại CÓ khai → cũng trả `None`, để văn bản nháp chưa nhập đủ
      vẫn lưu được. Chốt "phải nhập đủ" đặt ở lúc GỬI DUYỆT, không phải lúc lưu
      nháp — cùng luật với `required-fields.ts` của Thu mua.
    """
    hook_fn = _VALIDATORS.get((type_code or "").strip().upper())
    if hook_fn is None or not payload:
        return None
    return hook_fn(payload, creator_employee_id)


def require_on_submit(type_code: str, stored: dict | None) -> None:
    """Gửi duyệt mà chưa khai phần riêng của loại thì chặn.

    Người duyệt mở đơn nghỉ phép ra mà không có ngày nghỉ lẫn lý do thì họ duyệt
    cái gì.
    """
    if (type_code or "").strip().upper() not in _VALIDATORS:
        return
    if not stored:
        raise HTTPException(
            400, "Chưa khai thông tin nghỉ phép — mở lại văn bản và nhập đủ "
                 "ngày nghỉ, loại nghỉ và lý do trước khi gửi duyệt.")
