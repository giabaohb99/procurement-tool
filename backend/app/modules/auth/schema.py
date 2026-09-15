from pydantic import BaseModel


class LoginInput(BaseModel):
    username: str  # mã nhân viên hoặc email
    password: str


class RefreshInput(BaseModel):
    refresh_token: str

class GoogleLoginInput(BaseModel):
    credential: str

class ForgotPasswordInput(BaseModel):
    email: str

class ResetPasswordInput(BaseModel):
    token: str
    new_password: str


class ChangePasswordInput(BaseModel):
    """Người dùng tự đổi mật khẩu. bao-CR-405: trước đây cửa này nhận `dict` trần —
    thiếu trường thì `.get()` trả `None` và lỗi hiện ra dưới dạng "mật khẩu hiện tại
    không đúng", sai hẳn nguyên nhân. Độ mạnh vẫn do `core/password_policy` gác."""

    old_password: str
    new_password: str


class NotifyEmailInput(BaseModel):
    """Người dùng tự bật/tắt email thông báo của chính mình (bao-CR-349)."""

    notify_email: bool
