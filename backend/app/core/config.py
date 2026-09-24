from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DB_HOST: str = "db"
    DB_PORT: int = 3306
    DB_NAME: str = "procurement"
    DB_USER: str = "app"
    DB_PASSWORD: str = "app_password"

    JWT_SECRET: str = "change_me_please"
    JWT_ALG: str = "HS256"
    ACCESS_EXPIRE_MIN: int = 60          # access token sống ngắn
    REFRESH_EXPIRE_DAYS: int = 7         # refresh token sống dài

    CORS_ORIGINS: str = "http://localhost:8080,http://localhost:5173"
    LOGIN_RATE_LIMIT: str = "10/minute"  # chống brute-force đăng nhập
    # bao-CR-394 / BM-014: chỉ tin `CF-Connecting-IP` / `X-Forwarded-For` khi đầu TCP đối
    # diện (`request.client.host`) nằm trong các dải này — mặc định = mạng Docker + loopback,
    # nơi nginx và cloudflared đứng. Gọi thẳng cổng 8000 từ ngoài thì header tự khai bị bỏ,
    # lấy IP TCP thật. Ngăn cách bằng dấu phẩy; dải sai cú pháp bị bỏ qua (xem `core/client_ip`).
    TRUSTED_PROXY_CIDRS: str = "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,127.0.0.0/8"

    ADMIN_CODE: str = "degoadmin"
    ADMIN_PASSWORD: str = "dego2026"

    DEV_MODE: bool = False   # bật ở .env local (=true) để mở các API dev-only (vd xóa data test)
    
    FRONTEND_URL: str = "https://thumuatool.degoholding.vn"
    
    GOOGLE_CLIENT_ID: str = ""

    R2_ENDPOINT: str = ""
    R2_PUBLIC_URL: str = ""
    R2_BUCKET: str = "nexterp-storage"
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    # Thư mục gốc trên R2/storage để TÁCH môi trường (prod dùng chung bucket với dev).
    # prod = "prod", dev đặt STORAGE_PREFIX=dev trong .env.dev → file/backup không lẫn nhau.
    STORAGE_PREFIX: str = "prod"

    # Kho R2 của APP CŨ (đặt xe / duyệt dấu). 1488 tệp đính kèm nạp về 16/09/2026 mới có
    # MÔ TẢ, byte vẫn nằm nguyên bucket bên đó — xem `core/legacy_files.py`. Cùng một tài
    # khoản Cloudflare với kho ERP, chỉ khác bucket, nên chỉ cần một khóa CHỈ-ĐỌC.
    # CỐ Ý không đi qua `tab_setting`: đây là khóa bí mật, không phải tùy chọn trên UI.
    LEGACY_R2_ENDPOINT: str = ""
    LEGACY_R2_BUCKET: str = ""
    LEGACY_R2_ACCESS_KEY_ID: str = ""
    LEGACY_R2_SECRET_ACCESS_KEY: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    EMAIL_ENABLED: bool = False   # Tắt gửi email (thông báo/reset...) — bật lại khi làm phần email
    EMAIL_TEST_OVERRIDE: str = ""  # Nếu đặt: MỌI email gửi ra chuyển hướng tới địa chỉ này (an toàn khi test)
    # Chặn CỨNG mọi email ở môi trường này, kể cả email force (reset mật khẩu, cấp tài khoản).
    # Đọc từ .env (không qua tab_setting dùng chung) → dev đặt =true để không bao giờ gửi mail thật.
    EMAIL_HARD_OFF: bool = False
    # Bật gửi EMAIL cho luồng duyệt (workflow). Mặc định TẮT — prod chỉ báo chuông + web push.
    # Dev/UAT đặt =true để test nội dung email thông báo (dùng template HTML_LAYOUT).
    EMAIL_WORKFLOW_ENABLED: bool = False
    # Định tuyến email workflow theo NHÓM VAI TRÒ về hộp thư test (chỉ khi có giá trị):
    #   nhóm quản lý/duyệt (quản lý/admin thu mua, trưởng phòng duyệt, admin) → EMAIL_TEST_MANAGER
    #   nhóm nhân viên (nhân viên yêu cầu, nhân viên thu mua)                  → EMAIL_TEST_STAFF
    # Để trống cả hai → gửi tới email THẬT của người nhận (không định tuyến).
    EMAIL_TEST_MANAGER: str = ""
    EMAIL_TEST_STAFF: str = ""

    # Tạo cụm tài khoản DEMO_* (dùng cho E2E test ở local/dev). Mặc định BẬT để local/dev
    # không đổi hành vi. PROD đặt =false (trong .env) để KHÔNG seed lại tài khoản demo.
    SEED_DEMO_ACCOUNTS: bool = True

    # Cho phép seed GHI ĐÈ dữ liệu đã có: ma trận quyền của các vai trò chuẩn (STD_ROLES),
    # phạm vi (scope) và hình thức thanh toán mặc định của NCC.
    # Mặc định TẮT — seed chạy mỗi lần khởi động container, nếu bật thì mọi chỉnh sửa phân quyền
    # làm tay trên màn "Phân quyền" sẽ bị xóa và ghi lại theo app/seed.py sau mỗi lần deploy.
    # Cách dùng: khi CỐ Ý áp lại phân quyền chuẩn -> đặt SEED_FORCE_SYNC=true, restart api 1 lần,
    # rồi trả về false (hoặc bỏ dòng đó) trước lần deploy sau.
    SEED_FORCE_SYNC: bool = False

    # --- Quy trình duyệt YCMH (CR-034) ---
    # BẬT (mặc định): trưởng bộ phận duyệt xong phiếu dừng ở "Đã duyệt", phải có Admin/Quản lý
    # thu mua bấm Duyệt lần 2 thì hệ thống mới phân bổ nhân sự phụ trách (→ "Đã điều phối").
    # TẮT: quay về luồng cũ — trưởng bộ phận duyệt là phân bổ nhân sự luôn, không cần bước thứ 2.
    # Đây chỉ là giá trị DỰ PHÒNG; công tắc thật nằm ở màn "Cấu hình hệ thống" (key
    # `pr_dispatch_enabled`, lưu DB, đổi có hiệu lực ngay, không cần deploy).
    PR_DISPATCH_ENABLED: bool = True

    # --- Cảnh báo mở/tải tệp đính kèm văn bản (xem `document/file_access_log.py`) ---
    #  Bao nhiêu lượt mở/tải của CÙNG một người trong cửa sổ thì coi là bất
    #  thường. **0 = tắt hẳn phần cảnh báo**, vẫn ghi nhật ký như thường.
    #  20 lượt / 10 phút: người làm việc bình thường mở vài tệp một lúc; hai chục
    #  tệp trong mười phút là dấu hiệu đang gom tài liệu, không phải đang đọc.
    DOC_FILE_ALERT_THRESHOLD: int = 20
    DOC_FILE_ALERT_WINDOW_MIN: int = 10
    #  Ai nhận cảnh báo — email hoặc mã nhân viên, ngăn cách bằng dấu phẩy.
    #  Bỏ trống = tự suy ra người có quyền đọc văn bản ở phạm vi TOÀN HỆ.
    DOC_FILE_ALERT_RECIPIENTS: str = ""

    # --- Sao lưu CSDL ---
    BACKUP_KEEP: int = 30   # số bản backup giữ lại (2 lần/ngày -> ~15 ngày)
    # Prod chạy 2 lần/ngày (01:00 + 13:00). Dev đặt =true để chỉ chạy 1 lần/ngày
    # (01:00) — dữ liệu dev đồng bộ từ prod nên không cần dày.
    BACKUP_ONCE_DAILY: bool = False

    # --- Dọn dẹp ---
    NOTIFICATION_KEEP_DAYS: int = 10   # thông báo cũ hơn N ngày sẽ tự xóa

    # --- Trợ lý AI (Phase 0: nền lớp provider) ---
    # Tắt mặc định — bật ở .env môi trường muốn dùng. Off thì endpoint /api/assistant trả 403.
    AI_ENABLED: bool = False
    # Key nhà cung cấp model. Để trống = nhà đó coi như CHƯA cấu hình.
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    # Nhà mặc định khi request không chỉ định (claude | gemini).
    AI_DEFAULT_PROVIDER: str = "claude"
    # Model mặc định mỗi nhà. Lưu ý Gemini "-latest" là ALIAS tự nhảy version —
    # chạy thật nên ghim bản cụ thể (vd gemini-3.7-flash).
    AI_CLAUDE_MODEL: str = "claude-sonnet-5"
    AI_GEMINI_MODEL: str = "gemini-flash-latest"

    # --- Guard chi phí Trợ lý AI (Phase 4) ---
    # Trần số câu hỏi mỗi người mỗi ngày. Chặn một tài khoản đốt token vô hạn
    # (mỗi lượt nhồi cả gói tri thức + lịch sử). 0 = không giới hạn.
    AI_DAILY_MSG_LIMIT: int = 50
    # Model RẺ cho câu tra cứu/mặc định (kind lookup|general). Rỗng = dùng model
    # mặc định của nhà cung cấp. Câu tư vấn (kind=advice) luôn giữ model mặc định.
    # Lưu ý: phải là model CÙNG nhà với AI_DEFAULT_PROVIDER đang dùng.
    AI_LOOKUP_MODEL: str = ""

    # --- Tìm kiếm vector loại B: HDSD + FAQ (Phase 3) ---
    # Tắt mặc định. Bật thì tool `search_docs` mới hiện ra cho bot và hook nạp lại chỉ mục mới
    # chạy khi sửa HDSD/FAQ. Bật ở môi trường ĐÃ dựng service qdrant.
    AI_RAG_ENABLED: bool = False
    QDRANT_URL: str = "http://qdrant:6333"
    # Model nhúng của Gemini. Đổi model => vector cũ vô nghĩa, PHẢI reindex toàn bộ.
    AI_EMBED_MODEL: str = "gemini-embedding-001"
    # Số chiều vector. Gemini cho cắt chiều (Matryoshka); 768 đủ chính xác mà nhẹ RAM Qdrant.
    # Phải khớp với size collection đã tạo — đổi số này cũng buộc dựng lại collection.
    AI_EMBED_DIM: int = 768

    # --- Điểm cà phê × POS365 (doc/erp/diem-ca-phe/) ---
    # Cầu dao an toàn A1: MẶC ĐỊNH BẬT — dev/UAT chạy cả ngày không một call nào ra
    # quán thật. CHỈ prod đặt =false trong .env. Client kiểm cờ này TRƯỚC mọi request.
    POS365_HARD_OFF: bool = True
    # Cửa hàng: https://<tên-cửa-hàng>.pos365.vn — rỗng thì client coi như HARD_OFF.
    POS365_BASE_URL: str = ""
    # Tài khoản API RIÊNG (không dùng tài khoản của người — người đổi mật khẩu là
    # tác vụ nền chết im lặng). Không vào mã nguồn, chỉ ở .env.
    POS365_USERNAME: str = ""
    POS365_PASSWORD: str = ""
    # AccountId của tài khoản thanh toán "Trừ điểm" (N-04) — hằng số nhận diện của
    # TOÀN BỘ tích hợp, đổi nó là đơn cũ hết lọc được. Đọc từ AccountList lúc POC.
    POS365_PAYMENT_ACCOUNT_ID: int = 0
    # Chu kỳ kéo đơn (phút) — siết sau POC P6 (giới hạn gọi của POS365).
    POS365_PULL_MINUTES: int = 5

    # --- Đồng bộ với app đặt xe / duyệt dấu CŨ (Firebase) ---
    # Mặc định TẮT: bật là mở một đường máy-gọi-máy ra ngoài, phải cố ý bật ở .env.
    SYNC_DATXE_ENABLED: bool = False
    # Khóa ký chung hai bên (mục 6 của mo-ta-ky-thuat.md). KHÔNG commit, KHÁC NHAU
    # giữa dev và prod. Rỗng = coi như chưa cấu hình, mọi lời gọi sang app cũ dừng.
    SYNC_SHARED_SECRET: str = ""
    # Gốc API của app cũ, vd https://api.degoholding.vn (không có dấu / cuối).
    SYNC_LEGACY_API_BASE: str = ""
    # Công ty mặc định cho bản ghi nhập từ app cũ khi không suy ra được.
    SYNC_DEFAULT_COMPANY_ID: int = 1
    # Có bắn chuông/email khi nạp dữ liệu từ app cũ không. Mặc định TẮT — đợt nạp
    # lịch sử 1313 phiếu mà bật là hàng chục nghìn thông báo cho việc của năm ngoái.
    SYNC_NOTIFY_ON_IMPORT: bool = False
    # Realtime Database của app cũ — ERP ĐỌC trực tiếp để tra danh mục (xe, tài xế)
    # và để vòng quét lưới an toàn kéo phiếu đã sửa. Chỉ đọc, không bao giờ ghi:
    # chiều ghi ngược phải đi qua API của Worker (§5.3).
    # ⚠️ HAI DỰ ÁN FIREBASE RIÊNG BIỆT, ĐỪNG LẪN:
    #   dev  = api-degoholding-default-rtdb.asia-southeast1.firebasedatabase.app
    #   prod = api-degoholding-com-default-rtdb...  (nguồn của 1313 phiếu đã nạp)
    # Dev KHÔNG phải bản sao của prod, và KHÓA ĐỌC KHÁC NHAU theo từng dự án.
    LEGACY_FIREBASE_DB_URL: str = ""
    LEGACY_FIREBASE_SECRET: str = ""
    # Chu kỳ vòng quét lưới an toàn (phút): kéo phiếu có `updatedAt` mới hơn con trỏ
    # lần trước. Cái móc bên app cũ mới là đường chính; vòng này chỉ vá lúc móc trượt.
    SYNC_DATXE_PULL_MINUTES: int = 5
    # Nấc 3 của bộ tra danh mục: tra trượt thì có được TỰ TẠO xe / tài xế không.
    # Mặc định TẮT — bật là để một hệ ngoài đẻ hàng vào danh mục ERP. Chỉ xe và
    # tài xế, không bao giờ phòng ban / công ty / nhân sự / tài khoản (§9.6).
    SYNC_DATXE_AUTO_CREATE: bool = False

    # --- Agent Hub (doc/agent-hub/) ---
    # Bậc 1: nhận việc qua Telegram, Gemini gom + tóm tắt + đề xuất cách sửa, in ra
    # Telegram và ghi vào sổ. KHÔNG sửa mã. Mọi cờ mặc định TẮT — chưa bật thì không
    # một lời gọi nào đi ra ngoài, đúng nếp `legacy_datxe` / `pos365`.
    AGENT_HUB_ENABLED: bool = False
    AGENT_TELEGRAM_BOT_TOKEN: str = ""
    # CHỈ chat_id này được ra lệnh. Rỗng = không ai ra lệnh được (chốt chặn, không
    # phải "cho tất cả") — xem `telegram.is_allowed_chat`.
    AGENT_TELEGRAM_CHAT_ID: str = ""
    # Khóa Gemini RIÊNG của bot (QĐ-AI-7). CỐ Ý không lùi về GEMINI_API_KEY: bot chạy
    # nền gọi liên tục, đốt hết hạn mức thì Trợ lý AI đang phục vụ người thật chết
    # theo, mà lúc đó không ai biết vì sao.
    AGENT_GEMINI_API_KEY: str = ""
    AGENT_MANAGER_MODEL: str = "gemini-flash-latest"
    # Trần số task mỗi ngày. Trần này bảo vệ ĐẠI CA chứ không phải bảo vệ máy — hạn
    # mức dùng chung với người, bot ngốn hết thì người ngồi gõ tay cũng hết lượt.
    AGENT_DAILY_TASK_CAP: int = 5
    # Khoảng lặng trước khi gom: tin nhắn phải nằm yên bấy nhiêu giây mới đem đi
    # phân loại. Không có nó thì mỗi tin một task và bot KHÔNG BAO GIỜ gom được gì —
    # mà "gom được không" lại đúng là câu bậc 1 phải trả lời.
    AGENT_TRIAGE_DELAY_SEC: int = 90
    # Trần tin nhắn gom trong MỘT lời gọi Gemini. Vượt thì để lượt sau.
    AGENT_TRIAGE_BATCH: int = 20
    # Email tài khoản ERP mà lệnh `/hoi` chạy DƯỚI QUYỀN người đó.
    # ⚠️ Trợ lý AI lọc dữ liệu theo người đăng nhập, mà Telegram thì không đăng nhập —
    # nên phải chỉ đích danh một tài khoản. Để trống = tắt hẳn lệnh `/hoi`. ĐỪNG khai
    # tài khoản quản trị: ai nhắn được cho bot sẽ đọc được đúng những gì tài khoản này
    # đọc được. Hàng rào duy nhất còn lại là `AGENT_TELEGRAM_CHAT_ID`.
    AGENT_ASSISTANT_USER: str = ""
    # true = tiến trình `agent-poller` riêng đang giữ kết nối chờ tin Telegram (ai-CR-008),
    # nên vòng beat `agent.poll_telegram` 10 giây PHẢI tắt — hai bên cùng đọc một con trỏ
    # là xử trùng một tin. Stack thử `docker-compose.agent.yml` đặt cờ này ngay trong
    # `environment` của celery-beat/celery-worker, không cần khai ở `.env`.
    AGENT_LONG_POLL: bool = False
    # --- Bậc 2 (ai-CR-011): bot sửa mã bằng Claude Code CLI trong service `agent-runner` ---
    # Cầu dao riêng của bậc 2. TẮT thì bấm Duyệt chỉ ghi sổ như bậc 1, không giao việc đi đâu.
    AGENT_CODER_ENABLED: bool = False
    AGENT_CODER_CMD: str = "claude"
    # Số lượt tối đa một phiên `claude -p` được đi (mỗi lượt = một lần gọi model + tool).
    # 80 -> 120 (ai-CR-023): AI-0007 hết 80 lượt khi mới sửa xong một nửa hai màn giao diện.
    AGENT_CODER_MAX_TURNS: int = 120
    # Thư mục chứa worktree của từng task TRONG container runner (volume `agent_worktrees`).
    AGENT_WORKTREE_ROOT: str = "/worktrees"
    # Kho git nguồn, mount CHỈ ĐỌC vào runner; runner clone một bản `base` rồi cắt worktree
    # của từng task từ `origin/<AGENT_BASE_BRANCH>` của bản đó (luật C2).
    AGENT_REPO_SOURCE: str = "/src-repo"
    AGENT_BASE_BRANCH: str = "erp-v2"
    # Tài khoản hệ điều hành chạy `git` / `claude` / `pytest` trong runner. Worker Celery chạy
    # root, tiến trình con hạ xuống người dùng này để KHÔNG đọc được môi trường của cha
    # (`/proc/<pid>/environ` chứa khóa Telegram, Gemini, DB). Rỗng, hoặc tiến trình cha không
    # phải root (chạy ngoài Docker), thì không hạ.
    AGENT_RUNNER_USER: str = "runner"
    # Hết giờ thì giết tiến trình, ghi FAILED, nhắn Telegram; không tự thử lại (§8 thiết kế).
    AGENT_RUN_TIMEOUT_SEC: int = 1800
    # Trần số tệp một task được đụng (luật C1). Vượt = dừng, không commit, leo thang.
    AGENT_MAX_FILES_TOUCHED: int = 25
    # CỐ Ý KHÔNG khai `CLAUDE_CODE_OAUTH_TOKEN` ở đây: `coder.build_env` đọc thẳng `os.environ`
    # đúng lúc spawn, để khóa không bao giờ nằm trong đối tượng settings (dump/log/`/hoi`).
    # Cũng không có `AGENT_MAX_CONCURRENT_RUNS`: một việc một lúc do runner chạy `-c 1`.
    # --- Bậc 2, giai đoạn 2a (ai-CR-012): runner đẩy nhánh lên GitHub + mở PR vào nhánh nền ---
    # TẮT thì nhánh chỉ nằm trong volume runner như GĐ1; thẻ kết quả có nút «Đẩy GitHub + mở PR»
    # để đẩy tay từng việc. BẬT thì runner tự đẩy + mở PR ngay sau khi commit.
    AGENT_PR_ENABLED: bool = False
    AGENT_GITHUB_REPO: str = "giabaohb99/procurement-tool"
    AGENT_GITHUB_API_URL: str = "https://api.github.com"
    # CỐ Ý KHÔNG khai `AGENT_GITHUB_TOKEN` (PAT chi tiết, chỉ Contents + Pull requests của một
    # kho): `coder.github_token()` đọc thẳng `os.environ` lúc đẩy, và khóa chỉ đi vào tiến trình
    # `git push` (qua biến GIT_CONFIG_*, không nằm trên dòng lệnh) + lượt gọi API GitHub —
    # KHÔNG BAO GIỜ vào tiến trình `claude`.
    # --- Bậc 2, giai đoạn 2b·2 (ai-CR-014): gộp vào nhánh nền + deploy thử lên dev VPS ---
    # Đại ca chốt 22/09/2026: bot đẩy nhánh của mình xong thì HỎI; đại ca bấm đồng ý (ngay hoặc hẹn
    # giờ) mới được gộp thẳng vào AGENT_BASE_BRANCH rồi SSH lên VPS deploy dev. TẮT = thẻ kết quả
    # không có nút gộp, chỉ còn đường PR như GĐ2a.
    AGENT_DEPLOY_ENABLED: bool = False
    # Sổ quyết định của đại ca (ai-CR-015): `doc/agent-hub/` mount vào container ở /agent-docs.
    # Không có tệp thì bot chạy như trước (không tra sổ), không lỗi.
    AGENT_PLAYBOOK_PATH: str = "/agent-docs/03-so-quyet-dinh.md"
    # ai-CR-018: nhánh chạy thật, lượt rà soát so với nhánh nền để biết lỗi đã sửa ở đây chưa gộp.
    AGENT_MAIN_BRANCH: str = "main"
    # ai-CR-027: đại ca 23/09 — thẻ gọn (logic đã sửa, đã kiểm gì, đánh giá), KHÔNG nút dưới tin nhắn,
    # ra lệnh bằng chữ («gộp AI-0007», «duyệt», «xong»…), không gửi kèm tệp .diff. false = như cũ.
    AGENT_TG_COMPACT: bool = True
    # ai-CR-035: ảnh chụp lỗi đại ca gửi kèm. Poller ghi vào volume `agent_files`, runner đọc
    # (chỉ đọc) và mở cho Claude Code bằng --add-dir. Trần 20 MB là trần tải về của Bot API.
    AGENT_FILES_DIR: str = "/agent-files"
    # ai-CR-037: phiếu hỗ trợ ERP làm nguồn việc. Hai cửa, cửa nào trống là tắt cửa đó:
    #  - AGENT_TICKET_ASSIGNEE = email tài khoản ERP của bot: nhóm hỗ trợ GIAO phiếu cho tài khoản
    #    này là bot nhận (cửa chính — có người chủ động chọn);
    #  - AGENT_TICKET_DEPARTMENTS = danh sách nhãn «Bộ phận / Nhóm», cách nhau dấu phẩy: phiếu MỚI
    #    mang nhãn đó tự vào hàng việc của bot.
    AGENT_TICKET_ASSIGNEE: str = ""
    # ai-CR-038: mỗi người tự đăng nhập ERP trong Telegram bằng mã một lần lấy ở trang cá nhân.
    # Người đã liên kết chỉ hỏi được Trợ lý AI dưới quyền của chính họ.
    AGENT_LINK_ENABLED: bool = True
    AGENT_LINK_DAYS: int = 30
    AGENT_LINK_CODE_MINUTES: int = 10
    # Tên bot (không có @) để trang cá nhân dựng link mở thẳng bot; trống thì chỉ hướng dẫn chữ.
    AGENT_TELEGRAM_BOT_USERNAME: str = ""
    # ai-CR-043: tỷ giá TẠM để báo chi phí bot kèm tiền Việt. Chỉ để đọc cho dễ, không phải số kế toán.
    AGENT_USD_VND: int = 26000
    # ai-CR-049: gốc giao diện ERP chứa phiếu bot tạo (link «Mở phiếu»). Trống = FRONTEND_URL. Stack bot
    # local tạo phiếu vào DB riêng nên phải trỏ giao diện của stack đó (agent-erp, cổng 8084).
    AGENT_ERP_URL: str = ""
    AGENT_TICKET_DEPARTMENTS: str = ""
    AGENT_FILE_MAX_MB: int = 20
    # ai-CR-018: `doc/` trên máy đại ca (gồm phần CHƯA commit) mount chỉ đọc vào runner. Rỗng =
    # không có; compose của stack bot đặt `/local-docs` cho agent-runner.
    AGENT_LOCAL_DOCS_DIR: str = ""
    AGENT_VPS_HOST: str = ""
    AGENT_VPS_PORT: int = 22
    AGENT_VPS_USER: str = ""
    # Thư mục kho dev trên VPS và phần đuôi lệnh compose của stack dev (quy trình deploy §C: quên
    # `-f docker-compose.dev.yml` là devthumua 502).
    AGENT_VPS_DEV_DIR: str = "~/procurement-tool-dev"
    AGENT_VPS_DEV_COMPOSE_ARGS: str = "--env-file .env.dev -f docker-compose.dev.yml"
    # Đường dẫn khóa SSH TRONG container runner. Khóa thật mount chỉ đọc từ máy đại ca
    # (`AGENT_VPS_SSH_KEY_FILE` trong .env, chỉ compose đọc) vào dưới /root — thư mục 0700 nên tiến
    # trình `claude` (uid 1000) không với tới; `coder.run_ssh` chép ra bản 0600 tạm rồi xóa.
    AGENT_VPS_SSH_KEY_PATH: str = "/root/vps_ssh_key"
    # Sau deploy, chờ địa chỉ này trả 200 rồi mới báo xanh; rỗng = không kiểm.
    AGENT_DEV_HEALTH_URL: str = "https://devthumua.degoholding.vn/api/health"
    AGENT_DEV_UI_URL: str = "https://deverp.degoholding.vn"

    # --- Celery / Redis ---
    # Broker + result backend dùng chung 1 Redis (đủ cho quy mô ~20-100 user).
    REDIS_URL: str = "redis://redis:6379/0"

    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


settings = Settings()
