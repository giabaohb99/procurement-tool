"""Chính sách mật khẩu dùng chung cho MỌI cửa đặt mật khẩu (BM-016 — bao-CR-405).

Trước bản này hệ thống **không có chính sách nào**: ba cửa khai `password: str` trần
(`auth/schema.py` đặt lại qua token · `user/schema.py` cấp tài khoản + quản trị đặt lại),
cửa thứ tư `/auth/change-password` có kiểm nhưng chỉ đếm đủ 6 ký tự, cửa thứ năm
`/employees/{id}/set-password` chỉ đòi 4 ký tự. Đặt mật khẩu `1` là hệ thống nhận.

Điều làm nó nguy hơn vẻ ngoài: **tên đăng nhập chính là mã nhân viên** (`authenticate`
tra `Employee.code`), mà mã nhân viên thì ai cầm danh bạ cũng đọc được — nên luật đáng
giá nhất ở đây không phải "đủ dài" mà là **cấm lấy đúng tên đăng nhập làm mật khẩu**.

Vì sao luật nằm ở đây chứ không nằm trong Pydantic schema:
  1. Luật cấm-trùng-tên-đăng-nhập cần biết mã nhân viên + email của **chính tài khoản
     đang đặt**; schema chỉ nhìn thấy đúng chuỗi mật khẩu nên không kiểm được.
  2. Gom một chỗ thì thêm luật mới sửa một tệp, không phải đi lùng lại đủ năm cửa —
     đúng cái đã làm BM-016 sống sót lâu như vậy.
  3. Một hình lỗi duy nhất: 400 kèm câu tiếng Việt đọc được. Ném từ schema là 422 kèm
     mảng `detail` của Pydantic, màn hình cũ hiện ra khó đọc.

CỐ Ý **không** gọi trong `hash_password`: các script seed (`seed.py`, `seed_van_thu.py`,
`seed_tai_khoan_test.py`, ...) đặt mật khẩu demo bằng đúng mã tài khoản để dựng dữ liệu
thử. Siết ở tầng băm là chết seed mà không thêm một chút an toàn nào cho hệ thật — hệ
thật chỉ vào được qua năm cửa kể trên.
"""
import unicodedata

from fastapi import HTTPException

#  Tám ký tự: hệ nội bộ, tài khoản do quản trị cấp, và trần tần suất đăng nhập theo IP
#  (BM-004) đã chặn dò tự động — nên chọn mức đủ chặn đoán tay chứ không đua theo
#  khuyến nghị 12+ của hệ mở cho người ngoài.
MIN_LENGTH = 8

#  bcrypt băm tối đa 72 BYTE và **cắt âm thầm** phần dư: mật khẩu 80 ký tự với mật khẩu
#  72 ký tự đầu giống hệt sẽ đăng nhập được vào nhau. Chặn thẳng thay vì để người dùng
#  tin mình có một mật khẩu dài mà thật ra không phải.
MAX_BYTES = 72

#  Chuỗi ngắn hơn 3 ký tự mà đem đi cấm-chứa thì bắt nhầm gần hết: email `a@x.vn` sẽ
#  cấm mọi mật khẩu có chữ `a`.
MIN_CONTEXT_LENGTH = 3

#  Danh sách ngắn, cố ý chỉ giữ thứ thật sự hay gặp ở đây (gồm cả kiểu gõ tiếng Việt
#  không dấu). Đây KHÔNG phải bộ lọc từ điển — bộ lọc thật là luật cấm-trùng-tên-đăng-nhập.
COMMON_PASSWORDS = {
    "12345678", "123456789", "1234567890", "87654321", "11111111", "00000000",
    "password", "password1", "passw0rd", "matkhau1", "matkhau123", "abc12345",
    "qwertyui", "qwerty123", "1q2w3e4r", "iloveyou", "sunshine", "admin123",
    "administrator", "degoholding", "dego1234", "dego2026",
}


def _strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp — `Nguyễn` và `nguyen` là cùng một chuỗi."""
    return "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")


def _context_tokens(username: str, email: str) -> list[str]:
    """Những chuỗi mật khẩu KHÔNG được chứa: mã nhân viên, email, phần trước @ của email."""
    raw = [username or "", email or ""]
    if "@" in (email or ""):
        raw.append(email.split("@", 1)[0])
    out = []
    for token in raw:
        token = _strip_accents(token.strip().lower())
        if len(token) >= MIN_CONTEXT_LENGTH and token not in out:
            out.append(token)
    return out


def validate_password(raw: str, *, username: str = "", email: str = "") -> str:
    """Kiểm một mật khẩu MỚI trước khi băm. Trả lại chính chuỗi đó, hoặc ném 400.

    `username` là **mã nhân viên** (`Employee.code`) và `email` là email đăng nhập của
    đúng tài khoản đang được đặt mật khẩu — để trống thì bỏ qua luật cấm-trùng, chứ
    không bao giờ nới các luật còn lại.
    """
    raw = raw or ""
    if not raw.strip():
        raise HTTPException(400, "Mật khẩu không được để trống")

    #  Cửa `/auth/change-password` vốn `.strip()` âm thầm: người dùng gõ dư một dấu cách
    #  cuối sẽ nhận một mật khẩu khác cái họ nghĩ, rồi lần sau dán lại y hệt là sai.
    if raw != raw.strip():
        raise HTTPException(400, "Mật khẩu không được bắt đầu hoặc kết thúc bằng khoảng trắng")

    if len(raw) < MIN_LENGTH:
        raise HTTPException(400, f"Mật khẩu phải từ {MIN_LENGTH} ký tự trở lên")

    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise HTTPException(
            400, f"Mật khẩu quá dài — tối đa {MAX_BYTES} byte "
                 f"(khoảng {MAX_BYTES} ký tự không dấu, hoặc {MAX_BYTES // 3} ký tự tiếng Việt có dấu)")

    if not any(c.isalpha() for c in raw) or not any(c.isdigit() for c in raw):
        raise HTTPException(400, "Mật khẩu phải có cả chữ và số")

    if _strip_accents(raw.lower()) in COMMON_PASSWORDS:
        raise HTTPException(400, "Mật khẩu này nằm trong danh sách mật khẩu phổ biến — hãy chọn mật khẩu khác")

    haystack = _strip_accents(raw.lower())
    for token in _context_tokens(username, email):
        if token in haystack:
            raise HTTPException(
                400, "Mật khẩu không được chứa tên đăng nhập (mã nhân viên) hoặc email của tài khoản")

    return raw
