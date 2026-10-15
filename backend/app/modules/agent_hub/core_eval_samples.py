"""20 hội thoại mẫu của lõi mới (doc/agent-hub/20 §7, ai-CR-203). Mỗi mẫu là một chat riêng, chạy trong lồng thử của
`core_eval` (không ghi gì thật). Thêm mẫu: thêm một `Sample` vào `SAMPLES`; mã mẫu không đổi / không tái dùng.

Phần lớn mẫu lấy từ lỗi đo được trên dev ngày 15/10 (run #222–#246) — mỗi lỗi đã sửa thành một mẫu để không tái phát.
"""
from .core_eval import Sample, Turn

DRAFT_TOOLS = ("draft_work_task",)
TASK = "tạo cho anh task nghiên cứu luồng agent, dự án ERP v2, giao Được, hạn thứ sáu"

SAMPLES: tuple[Sample, ...] = (
    Sample("01", "Chào hỏi", (
        Turn("hello em", "Chào lại ngắn (1–2 câu), tự nhiên như người, có thể hỏi cần giúp gì; không kể lể danh sách "
             "tính năng, không gọi công cụ ERP.",
             must_not_call=("draft_work_task", "my_work_tasks", "search_docs")),)),
    Sample("02", "Task thiếu thông tin", (
        Turn("tạo cho anh task nghiên cứu luồng agent",
             "Hỏi lại dự án / người được giao / hạn trong MỘT tin (có thể gợi ý lựa chọn), hoặc soạn nháp với giả định "
             "nói rõ. Chưa được tạo thật.", commit=False),)),
    Sample("03", "Soạn → đổi hạn → đồng ý", (
        Turn(TASK, "Soạn nháp việc trong chat: dự án ERP v2, giao Được, hạn thứ Sáu gần nhất; hỏi đổi gì / nhắn tạo.",
             must_call=DRAFT_TOOLS, commit=False, dates=("thứ sáu",)),
        Turn("đổi hạn thứ năm giúp anh", "Sửa nháp: hạn sang thứ Năm gần nhất tính từ mai, trình lại nháp.",
             must_call=("update_draft",), commit=False, dates=("thứ năm",)),
        Turn("ok", "Tạo theo nháp (đường cũ báo đã tạo).", commit=True))),
    Sample("04", "Đồng ý viết sai chính tả", (
        Turn(TASK, "Soạn nháp việc.", must_call=DRAFT_TOOLS, commit=False),
        Turn("tao task đó igups anh đi nhé", "Hiểu là đồng ý → tạo theo nháp.", commit=True))),
    Sample("05", "Gửi lại y câu khi nháp đang chờ (run #227)", (
        Turn(TASK, "Soạn nháp việc.", must_call=DRAFT_TOOLS, commit=False),
        Turn(TASK, "KHÔNG tạo thật. Hỏi tạo luôn nháp đang chờ hay soạn lại, hoặc soạn lại nháp.", commit=False))),
    Sample("06", "Bỏ nháp (run #232)", (
        Turn(TASK, "Soạn nháp việc.", must_call=DRAFT_TOOLS, commit=False),
        Turn("thôi bỏ nháp đó đi em", "Bỏ nháp, báo ngắn đã bỏ.", drop=True, commit=False))),
    Sample("07", "Hạn thứ sáu tuần sau", (
        Turn("tạo task viết hướng dẫn dùng bot, dự án ERP v2, giao Được, hạn thứ sáu tuần sau",
             "Soạn nháp với hạn là thứ Sáu của tuần sau (không phải thứ Sáu gần nhất).",
             must_call=DRAFT_TOOLS, commit=False, dates=("thứ sáu tuần sau",)),)),
    Sample("08", "Giá vàng hôm nay", (
        Turn("giá vàng hôm nay", "Đưa giá vàng cụ thể (số) kèm nguồn; không bịa; không gọi công cụ ERP.",
             must_not_call=("draft_work_task", "payable_lookup")),)),
    Sample("09", "Ngày phép còn (run #237/#240)", (
        Turn("anh off được thêm mấy hôm nữa", "Tra lượt này rồi nói số ngày phép còn lại + đơn đang chờ nếu có.",
             must_call=("my_leave_summary",)),)),
    Sample("10", "Đơn của anh tới đâu (run #243)", (
        Turn("đơn của anh tới đâu rồi",
             "Tra CẢ phiếu qua bộ máy duyệt lẫn đơn nghỉ phép; nêu đơn nào chờ ai, đơn nào bị trả về kèm lý do.",
             must_call=("my_requests_status", "my_leave_summary")),)),
    Sample("11", "Hồ sơ của chị Mi (run #242/#244)", (
        Turn("ai đang giữ hồ sơ của chị Mi",
             "Tìm đúng người tên Mi (bỏ xưng hô khi tra); câu mơ hồ thì hỏi lại muốn xem hồ sơ nhân sự hay phiếu chị trình "
             "đang chờ ai. Không xin lại nhóm công cụ đã có.", must_call=("employee_lookup",),
             must_not_call=("more_tools",)),)),
    Sample("12", "Lập YCMH (run #223)", (
        Turn("tạo YCMH mua 10 thùng giấy A4 cho phòng IT, cần trước thứ sáu",
             "Soạn nháp YCMH hoặc hỏi MỘT lượt các ô còn thiếu (mục đích, kho, quy cách). Không tạo phiếu hỗ trợ IT.",
             any_call=("draft_purchase_request", "product_search"), must_not_call=("ticket_create",), commit=False),)),
    Sample("13", "Bot vừa làm gì (lối tắt)", (
        Turn("bot vừa làm gì", "Liệt kê các lần bot ghi gần đây (hoặc nói chưa có), kèm cách hoàn tác.", no_model=True,
             commit=False),)),
    Sample("14", "Đặt lời nhắc", (
        Turn("3 giờ chiều nay nhắc anh gọi NCC giấy nhé", "Xác nhận đã đặt lời nhắc đúng giờ 15:00 với nội dung gọi NCC giấy.",
             contains=("15",)),)),
    Sample("15", "Kế hoạch việc", (
        Turn("lập kế hoạch thử bot, hạn 20/10, 2 việc giao Được",
             "Hỏi 1–2 câu làm rõ hoặc soạn nháp kế hoạch (tự chia việc con + tiêu chí, nói rõ phần tự nghĩ). Chưa tạo thật.",
             commit=False),)),
    Sample("16", "Công nợ phải trả", (
        Turn("công nợ phải trả cần trả trong tháng này bao nhiêu", "Tra công nợ theo HẠN TRẢ trong tháng; nêu tổng + vài "
             "NCC lớn; không bịa số.", must_call=("payable_lookup",)),)),
    Sample("17", "Việc hôm nay", (
        Turn("hôm nay anh có việc gì cần làm không", "Tra việc của người hỏi (hạn hôm nay / quá hạn) rồi liệt kê gọn.",
             any_call=("my_work_tasks",)),)),
    Sample("18", "Việc cá nhân không phải ERP", (
        Turn("lên giúp anh lịch trình đi Đà Lạt 2 ngày cuối tuần này",
             "Làm luôn lịch trình 2 ngày bằng chữ; KHÔNG gợi ý phiếu ERP, không soạn nháp nào.",
             must_not_call=("draft_work_task", "draft_purchase_request", "draft_work_plan"), commit=False),)),
    Sample("19", "Yêu cầu sửa phần mềm", (
        Turn("sửa giúp anh màn YCMH thêm cột ngày cần hàng ở danh sách",
             "Nhắc lại cách hiểu (màn nào, thêm gì) và hỏi xác nhận TRƯỚC; chưa ghi yêu cầu sửa phần mềm ở lượt này.",
             must_not_call=("create_code_task",)),)),
    Sample("20", "Chat chưa liên kết", (
        Turn("cho anh xem công nợ tháng này", "Hướng dẫn liên kết tài khoản (/dangnhap + mã ở Trang cá nhân), không im lặng.",
             contains=("dangnhap",)),), unlinked=True),
)
