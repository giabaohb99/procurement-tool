"""BỘ MÃ CỦA AGENT HUB — số nguyên, theo R2/QĐ-11.

Phân hệ này MỚI và không thuộc Thu mua, nên mọi cột mang nghĩa *trạm · nguồn ·
chiều · mức* lưu `SMALLINT` và so với hằng số ở đây. Tiếng Việt chỉ sống trong các
`*_LABELS` bên dưới và ở tầng gửi Telegram. Cùng khuôn `vehicle_booking/model.py`
và `leave/constants.py`.

⚠️ Đừng khai mấy bộ này vào `core/status_catalog.py` — khung đó dành cho bộ mã
CHUỖI (QĐ-9), và `scripts/gen_status_ts.py` cũng chỉ sinh TypeScript cho mã chuỗi.
Bậc 1 không có màn hình nào nên cũng chưa cần bản TypeScript.
"""

# ---------------------------------------------------------------------------
# Trạm — chính là `tab_agent_task.status`
# ---------------------------------------------------------------------------
#  Số 1..7 bám đúng bảy trạm ở §4 bản thiết kế, và mang nghĩa "task đang ĐỨNG ở
#  trạm nào", không phải "trạm nào đã chạy xong". Task vừa phân loại xong thì đứng
#  ở TRIAGE chờ đại ca bấm nút, chứ không nhảy sang PLAN.
ST_INBOX = 1        # Mới vào sổ, chưa ai đọc
ST_TRIAGE = 2       # Đã gom + tóm tắt, chờ đại ca cho lập kế hoạch
ST_PLAN = 3         # Đã có bản đề xuất, chờ đại ca duyệt
ST_CODE = 4         # Bot code đang sửa          (BẬC 2 — bậc 1 không bao giờ tới đây)
ST_CI = 5           # GitHub Actions đang chạy   (BẬC 2)
ST_REVIEW = 6       # Đã có kết quả, chờ đại ca đọc (BẬC 3)
ST_PROD = 7         # Chờ lệnh lên prod          (BẬC 4)
ST_DONE = 8         # Xong
ST_CANCELLED = 9    # Đại ca bỏ
ST_FAILED = 10      # Bot chịu thua, đã leo thang
ST_NEEDS_INPUT = 11 # Đang hỏi lại đại ca, chờ câu trả lời

TASK_STATUS_LABELS = {
    ST_INBOX: "Mới vào sổ",
    ST_TRIAGE: "Đã phân loại",
    ST_PLAN: "Đã có đề xuất",
    ST_CODE: "Đang sửa mã",
    ST_CI: "Đang chạy CI",
    ST_REVIEW: "Chờ đại ca xem",
    ST_PROD: "Chờ lệnh lên prod",
    ST_DONE: "Xong",
    ST_CANCELLED: "Đã bỏ",
    ST_FAILED: "Thất bại",
    ST_NEEDS_INPUT: "Đang hỏi lại",
}

#  Trạng thái ĐÃ ĐÓNG: không nhận thêm thao tác nào, và tin nhắn gắn vào nó được
#  thả ra cho lượt gom sau. Nguồn DUY NHẤT — đừng rải `status in (9, 10)`.
CLOSED_STATUSES = (ST_DONE, ST_CANCELLED, ST_FAILED)

#  Trần của bậc 1. Bậc 1 không có bot code nên không task nào được vượt qua PLAN.
#  Chốt này là chỗ DUY NHẤT diễn đạt điều đó — bỏ nó đi thì phải có bot code thật.
TIER1_MAX_STATUS = ST_PLAN

# ---------------------------------------------------------------------------
# Nguồn việc
# ---------------------------------------------------------------------------
SRC_ERP_TICKET = 1  # Phiếu hỗ trợ trong ERP (`tab_ticket`) — BẬC SAU, xem AN-005
SRC_TELEGRAM = 2    # Tin nhắn Telegram của đại ca — nguồn DUY NHẤT của bậc 1
SOURCE_LABELS = {
    SRC_ERP_TICKET: "Phiếu hỗ trợ ERP",
    SRC_TELEGRAM: "Telegram",
}

# ---------------------------------------------------------------------------
# Ai gom việc lại với nhau
# ---------------------------------------------------------------------------
MERGED_BY_BOT = 1
MERGED_BY_HUMAN = 2
MERGED_BY_LABELS = {
    MERGED_BY_BOT: "Bot tự gom",
    MERGED_BY_HUMAN: "Đại ca gom tay",
}

# ---------------------------------------------------------------------------
# Chiều tin nhắn Telegram
# ---------------------------------------------------------------------------
DIR_OUT = 1  # Bot gửi đi
DIR_IN = 2   # Đại ca gửi tới
DIRECTION_LABELS = {
    DIR_OUT: "Bot gửi",
    DIR_IN: "Đại ca gửi",
}

# ---------------------------------------------------------------------------
# Mức rủi ro
# ---------------------------------------------------------------------------
RISK_LOW = 1
RISK_MEDIUM = 2
RISK_HIGH = 3  # Đụng tiền, phân quyền, migration, hoặc nhánh `main` (luật B6)
RISK_LABELS = {
    RISK_LOW: "Thấp",
    RISK_MEDIUM: "Vừa",
    RISK_HIGH: "CAO",
}

# ---------------------------------------------------------------------------
# Một lượt gọi model / chạy bot (`tab_agent_run`)
# ---------------------------------------------------------------------------
RUN_RUNNING = 1
RUN_OK = 2
RUN_ERROR = 3
RUN_STATUS_LABELS = {
    RUN_RUNNING: "Đang chạy",
    RUN_OK: "Xong",
    RUN_ERROR: "Lỗi",
}

# Trạm nào sinh ra lượt gọi này — dùng lại chính bộ số trạm ở trên.
STAGE_TRIAGE = ST_TRIAGE
STAGE_PLAN = ST_PLAN

# ---------------------------------------------------------------------------
# Đơn giá model, USD / 1 triệu token
# ---------------------------------------------------------------------------
#  ƯỚC LƯỢNG để soi chi phí, KHÔNG phải hóa đơn. Google đổi giá lúc nào thì bảng
#  này sai lúc đó — con số thật luôn là trang thanh toán của Google. Ở đây chỉ cần
#  đủ chính xác để trả lời "bot đốt nhiều hay ít".
#  Model lạ không có trong bảng thì tính 0 và `tab_agent_run.cost_usd` ra 0 — cố ý,
#  thà ghi 0 rõ ràng còn hơn đoán một con số rồi có người tin.
MODEL_PRICES_USD = {
    "gemini-flash-latest": (0.30, 2.50),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-flash-lite-latest": (0.10, 0.40),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Ước chi phí một lượt gọi. Model lạ -> 0.0 (xem ghi chú ở MODEL_PRICES_USD).

    Token "suy nghĩ" tính giá như output, nên nơi gọi phải cộng nó vào
    `output_tokens` trước khi truyền vào đây.
    """
    price = MODEL_PRICES_USD.get(model or "")
    if not price:
        # Gemini trả về tên đầy đủ kèm bản (vd "gemini-flash-latest-002") — thử khớp
        # theo tiền tố trước khi bỏ cuộc.
        for name, p in MODEL_PRICES_USD.items():
            if model and model.startswith(name):
                price = p
                break
    if not price:
        return 0.0
    in_rate, out_rate = price
    return round(
        (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000,
        6,
    )
