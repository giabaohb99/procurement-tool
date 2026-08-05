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

    # --- Sao lưu CSDL ---
    BACKUP_KEEP: int = 30   # số bản backup giữ lại (2 lần/ngày -> ~15 ngày)

    # --- Dọn dẹp ---
    NOTIFICATION_KEEP_DAYS: int = 10   # thông báo cũ hơn N ngày sẽ tự xóa

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
