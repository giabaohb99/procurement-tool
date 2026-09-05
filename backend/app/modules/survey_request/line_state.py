"""Tiến độ của MỘT DÒNG khảo sát — nguồn sự thật DUY NHẤT cho cả hai màn.

Trước CR-077 mỗi màn tự suy một kiểu: chi tiết Yêu cầu báo giá có 5 nhãn (FE tự tính),
màn Tiến độ báo giá có 9 nhãn (BE tính) — cùng một dòng lại hiện hai chữ khác nhau.
Nay chỉ còn bộ 9 nhãn này; FE đọc thẳng `progress_state` backend trả về.

Trạng thái KHÔNG lưu cột riêng, luôn suy từ dữ liệu đang có.
"""
from .model import LS_COMPLETED, LS_CONFIRMED, LS_RESURVEY, SurveyRequestLine

# Nhãn cột "Tiến độ dòng". Thứ tự dưới đây là thứ tự DÒNG ĐỜI (đầu -> cuối),
# không phải thứ tự ưu tiên khi suy — xem `progress_state`.
STATE_NOT_RECEIVED = "Chưa tiếp nhận"
STATE_RECEIVED = "Đã tiếp nhận"
STATE_SURVEYING = "Đang khảo sát"
STATE_ANSWERED = "Đã trả kết quả"
STATE_NO_OPTION = "Chốt rỗng"
STATE_CHOSEN = "Đã chọn phương án"
STATE_CONFIRMED = "Đã chốt phương án"     # P6-3: người YC khóa lựa chọn, chờ thu mua lên đơn
STATE_RESURVEY = "Cần khảo sát lại"
STATE_PR_CREATED = "Đã tạo YCMH"
STATE_PO_CREATED = "Đã lên đơn"           # P6-3: thu mua đã tạo thẳng ĐMH từ dòng (bỏ bước YCMH)
STATE_DONE = "Hoàn thành"

STATES = [STATE_NOT_RECEIVED, STATE_RECEIVED, STATE_SURVEYING, STATE_ANSWERED,
          STATE_NO_OPTION, STATE_CHOSEN, STATE_CONFIRMED, STATE_RESURVEY,
          STATE_PR_CREATED, STATE_PO_CREATED, STATE_DONE]

# Màu badge trên giao diện — để ở backend cho hai màn khỏi lệch màu nhau.
STATE_TONE = {
    STATE_NOT_RECEIVED: "gray", STATE_RECEIVED: "gray", STATE_SURVEYING: "warn",
    STATE_ANSWERED: "info", STATE_NO_OPTION: "warn", STATE_CHOSEN: "ok",
    STATE_CONFIRMED: "ok", STATE_RESURVEY: "err", STATE_PR_CREATED: "info",
    STATE_PO_CREATED: "info", STATE_DONE: "ok",
}


def progress_state(ln: SurveyRequestLine, has_chosen: bool, option_count: int) -> str:
    """Suy tiến độ của dòng: xét từ mốc XA nhất về gần, khớp cái nào trả cái đó.

    HOÀN THÀNH LÀ ĐIỂM CUỐI (CR-077) — đứng trên "Đã tạo YCMH". Một dòng có thể tạo YCMH
    nhiều lần (mua lại) nên `pr_code` không phải mốc đóng; chỉ khi người YC chốt hoàn thành
    thì dòng mới thật sự khép lại.
    """
    if ln.line_status == LS_COMPLETED:
        return STATE_DONE
    # P6-3: luồng v2 lên đơn thẳng ghi po_code — xét TRƯỚC pr_code vì dòng nào đi cả hai
    # đường (YCMH cũ rồi ĐMH mới) thì mốc ĐMH là mốc muộn hơn.
    if getattr(ln, "po_code", ""):
        return STATE_PO_CREATED
    if ln.pr_code:
        return STATE_PR_CREATED
    if ln.line_status == LS_RESURVEY:
        return STATE_RESURVEY
    if ln.line_status == LS_CONFIRMED:
        return STATE_CONFIRMED
    if has_chosen:
        return STATE_CHOSEN
    if ln.no_option:
        return STATE_NO_OPTION
    if (ln.result_date or "").strip():
        return STATE_ANSWERED
    if option_count:
        return STATE_SURVEYING
    return STATE_RECEIVED if ln.assignee else STATE_NOT_RECEIVED
