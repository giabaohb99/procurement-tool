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
#  Đang gộp vào nhánh nền + deploy dev (ai-CR-014). Trạm tạm, chỉ sống trong một lượt
#  `agent.deploy_task`; xong thì sang ST_PROD (đã lên dev, chờ lệnh prod), hỏng thì về REVIEW.
ST_DEPLOYING = 12
#  Đang rà soát mã thật trước khi lập kế hoạch (ai-CR-017): Claude Code chỉ đọc, trên erp-v2 mới
#  nhất. Trạm tạm giữa TRIAGE và PLAN; rà soát hỏng hay quá hạn thì vẫn lập kế hoạch theo tài liệu.
ST_SCANNING = 13

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
    ST_DEPLOYING: "Đang gộp + deploy dev",
    ST_SCANNING: "Đang rà soát mã",
}

#  Trạng thái ĐÃ ĐÓNG: không nhận thêm thao tác nào, và tin nhắn gắn vào nó được
#  thả ra cho lượt gom sau. Nguồn DUY NHẤT — đừng rải `status in (9, 10)`.
CLOSED_STATUSES = (ST_DONE, ST_CANCELLED, ST_FAILED)

#  Trần của bậc 1. Bậc 1 không có bot code nên không task nào được vượt qua PLAN.
#  Từ ai-CR-011 bot code ĐÃ có (`coder.py`, service `agent-runner`), nhưng chỉ khi cờ
#  `AGENT_CODER_ENABLED` bật; cờ tắt thì trần này vẫn đúng nguyên nghĩa.
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

#  ai-CR-057: LÀN của một việc. Việc nhỏ và rõ (đổi chữ/nhãn/màu/thứ tự trên giao diện, mục tiêu nêu rõ,
#  risk 1) đi ĐƯỜNG TẮT: không rà soát riêng, không chờ «duyệt» — lập kế hoạch gọn rồi sửa luôn, xong
#  mới báo một dòng. Việc khác đi làn đầy đủ như trước. Đại ca ép bằng chữ: «làm kỹ» → đầy đủ, «làm luôn» → tắt.
LANE_FULL = 0
LANE_QUICK = 1
QUICK_MAX_FILES = 3
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
STAGE_CODE = ST_CODE   # một lượt `claude -p` của runner (bậc 2, ai-CR-011)
#  Phân loại ý định chạy TRƯỚC khi có task nên không mượn được số trạm nào; đánh số
#  ngoài dải trạng thái task để không ai đọc nhầm nó thành một trạng thái của việc.
STAGE_INTENT = 20
#  Hỏi thêm về bản vá (ai-CR-013): một lượt `claude -p --resume` vào đúng phiên đã sửa việc.
#  Cũng ngoài dải trạng thái, cùng lý do với STAGE_INTENT.
STAGE_ASK = 21
#  Gộp vào nhánh nền + deploy dev (ai-CR-014): một lượt merge --no-ff + push + ssh deploy. Dòng
#  sổ này được tạo NGAY lúc đại ca đồng ý (hoặc hẹn giờ) và đóng khi deploy xong/hỏng; artifact
#  giữ `merge_sha` — thứ lượt thu hồi cần. STAGE_REVERT = lượt `git revert -m 1` + deploy lại.
STAGE_DEPLOY = 22
STAGE_REVERT = 23
#  Nháp một mục cho sổ quyết định (ai-CR-015): một lượt Gemini đọc câu bot hỏi + câu đại ca
#  trả lời. `artifact.state` = `cho_duyet` (thẻ đang chờ bấm) · `da_ghi` · `bo` · `khong_ap`.
STAGE_RULE = 24
#  Rà soát mã trước kế hoạch (ai-CR-017): một lượt `claude -p` chỉ đọc. artifact giữ `message`
#  (đoạn phân tích đã nhắn đại ca), `info` (JSON: files, root_cause, already_fixed…), `head`.
STAGE_SCAN = 25
#  Nghiên cứu (ai-CR-044): một lượt tìm web / kiểm chứng / hỏi tài liệu nội bộ. artifact giữ `chat_id`,
#  `mode`, `question`, `text`, `sources` — để «/word» xuất lại đúng bản của chat đó.
STAGE_RESEARCH = 26
#  Nhãn bước cho màn Việc của bot (ai-CR-036).
STAGE_LABELS = {
    STAGE_TRIAGE: "Gom việc",
    STAGE_PLAN: "Lập kế hoạch",
    STAGE_CODE: "Sửa mã",
    STAGE_INTENT: "Đọc ý định",
    STAGE_ASK: "Hỏi thêm về bản vá",
    STAGE_DEPLOY: "Gộp / deploy dev",
    STAGE_REVERT: "Thu hồi",
    STAGE_RULE: "Đề xuất ghi sổ",
    STAGE_SCAN: "Rà soát mã",
    STAGE_RESEARCH: "Nghiên cứu",
}

# ---------------------------------------------------------------------------
# Dấu đã xử của một tin nhắn ĐẾN (`tab_agent_message.action`)
# ---------------------------------------------------------------------------
#  Vòng gom chỉ nhặt tin `action` RỖNG. Nên mọi tin đã được xử theo đường khác đều
#  phải đóng một dấu ở đây, không thì nó vừa được trả lời vừa biến thành một đầu việc.
ACT_COMMAND = "lenh"      # Tin bắt đầu bằng `/` — lệnh, không bao giờ là việc
ACT_ASKED = "hoi"         # Đã chuyển cho Trợ lý AI trả lời tại chỗ
#  Bot đoán được thao tác nhưng chưa chắc, đang chờ «đúng»/«không» (ai-CR-028). Dấu thật là
#  `cho_xn:<thao tác>` — chép luôn tên thao tác vào dấu để câu «đúng» chạy đúng thứ đã hỏi, khỏi
#  hỏi lại model lần hai.
ACT_WAIT_CONFIRM = "cho_xn:"
ACT_WAIT_CHOICE = "cho_y"  # Chưa rõ hỏi hay giao việc, đang chờ đại ca bấm nút
ACT_ANSWER = "tra_loi"    # Tin bot gửi = câu trả lời của Trợ lý AI (để nối mạch hội thoại)
#  Kết quả tool của Trợ lý AI đưa ra Telegram (ai-CR-009). Tin CHIỀU RA, không vào mạch
#  hội thoại — `_recent_turns` chỉ lấy `hoi` / `tra_loi`.
ACT_FILE = "tep"               # Bot đã gửi một tệp (báo cáo Excel/Word do tool xuất)
ACT_PROPOSAL = "de_xuat"       # Thẻ đề xuất sửa phiếu đang chờ bấm; `body` = JSON khối proposal
ACT_PROPOSAL_DONE = "da_sua"   # Đại ca bấm Xác nhận và phiếu đã ghi
ACT_PROPOSAL_DROPPED = "bo_sua"  # Đại ca bấm Không sửa, hoặc xác nhận hỏng (hết hạn, mất quyền)
#  Hỏi thêm về bản vá (ai-CR-013). Ba dấu nối thành một mạch riêng, tách khỏi mạch Trợ lý AI:
#  bot mời hỏi -> đại ca hỏi -> Claude Code (đúng phiên đã sửa) trả lời. Tin kế tiếp trong
#  `service.FOLLOW_UP_WINDOW` sau bất kỳ dấu nào trong ba dấu này là hỏi tiếp, không đi phân loại.
ACT_WAIT_PATCH_Q = "cho_hoi_va"   # Tin bot: đã bấm «Hỏi thêm», đang chờ câu hỏi
ACT_PATCH_Q = "hoi_va"            # Tin đại ca: câu hỏi về bản vá, đã giao cho runner
ACT_PATCH_ANSWER = "tra_loi_va"   # Tin bot: câu trả lời của Claude Code về bản vá
#  Hẹn giờ gộp + deploy dev (ai-CR-014): bot mời nhắn giờ; tin kế tiếp trong FOLLOW_UP_WINDOW là
#  giờ hẹn, không đi phân loại. Chỉ một dấu vì câu trả lời của bot là câu thường (đã hẹn/không hiểu).
ACT_WAIT_DEPLOY_TIME = "cho_hen_gio"
#  Trả lời câu hỏi lại của trạm kế hoạch (ai-CR-015): trước đây câu trả lời rơi vào INBOX và
#  đẻ thành VIỆC MỚI, việc cũ treo ở «Đang hỏi lại». Nay tin kế sau dấu chờ gắn thẳng vào việc.
ACT_WAIT_PLAN_ANSWER = "cho_tra_loi_kh"   # Tin bot: thẻ kế hoạch đang hỏi lại / mời nói rõ thêm
ACT_PLAN_ANSWER = "tra_loi_kh"            # Tin đại ca: câu trả lời, đã gắn vào việc + lập lại kế hoạch
ACT_DEPLOY_TIME = "hen_gio"       # Tin đại ca: giờ hẹn gộp + deploy, đã ghi vào sổ lượt chạy
#  ai-CR-021: tin bot báo đã nhận việc, và tin báo việc đang chạy (bot sửa lại chính tin đó để
#  cập nhật số phút). Hai loại này KHÔNG phải một lượt hội thoại: các mạch nối tin «ngay trước»
#  (hẹn giờ gộp, hỏi thêm bản vá) phải bỏ qua chúng, không thì một tin báo của việc khác chen
#  vào là đứt mạch.
#  ai-CR-035: ảnh gửi không kèm chữ nằm chờ câu mô tả; ảnh đã ghép vào một tin khác; câu báo nhận ảnh.
ACT_PHOTO_WAIT = "cho_chu_anh"
ACT_PHOTO_USED = "anh_da_ghep"
ACT_PHOTO_ACK = "da_nhan_anh"
ACT_ACK = "da_nhan"
ACT_HEARTBEAT = "dang_chay"
#  Ảnh và câu báo nhận ảnh cũng là «nhiễu» với các mạch hỏi-đáp: gửi kèm ảnh giữa lúc bot đang chờ
#  giờ hẹn / câu trả lời kế hoạch không được làm đứt mạch đó (ai-CR-035).
#  ai-CR-046: bản nháp chứng từ chờ «tạo». Dòng sổ ẩn (không gửi Telegram), `body` = JSON
#  {tool, kind, user_id, draft}; dùng xong đổi sang `da_tao` / `bo_tao`.
ACT_DRAFT_WAIT = "cho_tao"
ACT_DRAFT_DONE = "da_tao"
ACT_DRAFT_DROPPED = "bo_tao"
#  ai-CR-051: thẻ hỏi lại «cấp cho X cấp Y?» của đại ca; `body` = JSON {op, user_id, level}.
ACT_GRANT_WAIT = "cho_cap_quyen"
ACT_GRANT_DONE = "da_cap_quyen"
ACT_GRANT_DROPPED = "bo_cap_quyen"
#  Tin người khác (không phải đại ca) ra lệnh trên việc mà không đủ cấp — sổ để đại ca tra lại.
ACT_DENIED = "tu_choi"
#  ai-CR-054: thẻ hỏi lại «thêm / tắt máy sửa mã?» của đại ca; `body` = JSON {op, name, owner_user_id, runner_id}.
ACT_RUNNER_WAIT = "cho_may"
ACT_RUNNER_DONE = "da_may"
ACT_RUNNER_DROPPED = "bo_may"
NOISE_ACTIONS = (ACT_ACK, ACT_HEARTBEAT, ACT_PHOTO_WAIT, ACT_PHOTO_USED, ACT_PHOTO_ACK,
                 ACT_DRAFT_WAIT, ACT_DRAFT_DONE, ACT_DRAFT_DROPPED,
                 ACT_GRANT_WAIT, ACT_GRANT_DONE, ACT_GRANT_DROPPED,
                 ACT_RUNNER_WAIT, ACT_RUNNER_DONE, ACT_RUNNER_DROPPED)

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
    #  `gemini-flash-latest` là bí danh; Google trả về tên thật của bản nó trỏ tới (23/09/2026:
    #  gemini-3.8-flash) nên phải khai cả tên đó, không thì cột chi phí của bot toàn 0 (ai-CR-022).
    #  Giá ước theo đúng bí danh — trang thanh toán của Google mới là số thật.
    "gemini-3.8-flash": (0.30, 2.50),
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


# ---------------------------------------------------------------------------
# Tên của bot trên Telegram (ai-CR-016, đại ca đặt 23/09/2026)
# ---------------------------------------------------------------------------
#  Chỉ là cách bot TỰ XƯNG trong câu chữ. Tên hiển thị của tài khoản Telegram đổi ở BotFather
#  (`/setname`), không nằm trong mã. Trợ lý AI trên web KHÔNG đổi tên: persona chỉ chèn thêm
#  vào lời nhắc khi câu hỏi đi từ Telegram (`service.answer_question`).
from app.core.config import settings as _settings  # noqa: E402 — chỉ để lấy tên bot

BOT_NAME = _settings.AGENT_BOT_NAME or "Đậu Đậu"
BOT_PERSONA = (
    f"Trong kênh Telegram này bạn tên là {BOT_NAME}, trợ lý của DEGO Holding trên Telegram. "
    f"Tự xưng «em», gọi người đang nhắn là «đại ca». Khi được hỏi tên hay được bảo giới thiệu "
    f"thì nói em là {BOT_NAME}. Không gọi mình là «Trợ lý AI» trong kênh này."
)
#  ai-CR-040: bot từng BỊA cách đổi tài khoản («quét mã QR», «token phiên») khi đại ca hỏi. Đây là cơ chế
#  thật (ai-CR-038), nói rõ để model không phải đoán.
#  ai-CR-046: trên Telegram không có nút mở form — bot tự gửi bản tóm tắt và chờ «tạo».
BOT_DRAFT_FACTS = (
    "Trên Telegram KHÔNG có nút mở form. Khi đã soạn nháp chứng từ bằng công cụ, đừng bảo người dùng bấm "
    "nút hay mở form trên web; chỉ nói ngắn là đã soạn xong, bot gửi bản tóm tắt ngay bên dưới và họ nhắn "
    "«tạo» để lưu Nháp, «tạo và gửi duyệt» để gửi duyệt luôn, «thôi» để bỏ. Có cảnh báo (quỹ phép không đủ, trùng "
    "ngày…) thì vẫn nói rõ cảnh báo đó. Khi GỌI công cụ soạn nháp, mọi chữ tiếng Việt điền vào (lý do, mục "
    "đích, chủ đề, nội dung, tên hàng) phải viết CÓ DẤU đầy đủ như người dùng gõ — không bỏ dấu."
)
BOT_LOGIN_FACTS = (
    "Chỉ dùng đoạn này khi người dùng hỏi CÁCH đăng nhập / đổi tài khoản (ai-CR-042). "
    "Cách đăng nhập tài khoản ERP trong Telegram (chỉ có đúng cách này, không có quét QR, không hỏi mật "
    "khẩu): tài khoản của một chat Telegram KHÔNG đổi theo trang web — đăng nhập tài khoản khác trên web "
    "không làm chat này đổi theo. Muốn đổi: đăng nhập ERP bằng tài khoản muốn dùng, vào Trang cá nhân → "
    "tab «Telegram» → «Lấy mã liên kết», rồi nhắn cho bot «/dangnhap <mã 6 số>» (mã dùng một lần, hết "
    "hạn sau vài phút). «/dangxuat» để bỏ liên kết, «/taikhoan» để xem chat đang dùng tài khoản nào."
)
