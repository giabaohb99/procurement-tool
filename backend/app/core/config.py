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
