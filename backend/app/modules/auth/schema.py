from pydantic import BaseModel


class LoginInput(BaseModel):
    username: str  # mã nhân viên hoặc email
    password: str


class RefreshInput(BaseModel):
    refresh_token: str
