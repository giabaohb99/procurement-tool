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
