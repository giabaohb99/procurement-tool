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
