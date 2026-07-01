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
    
    FRONTEND_URL: str = "https://thumuatool.degoholding.vn"
    
    GOOGLE_CLIENT_ID: str = ""

    R2_ENDPOINT: str = ""
    R2_PUBLIC_URL: str = ""
    R2_BUCKET: str = "nexterp-storage"
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

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
