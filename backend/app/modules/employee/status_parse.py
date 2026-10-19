"""Đổi ô trạng thái nhân sự (mã / nhãn / gõ lệch dấu) thành MÃ — dùng chung cho nhập Excel."""


def status_code_from_text(raw: str) -> str:
    """Đổi ô "Trạng thái NS" trong tệp CSV thành MÃ (B-03).

    Đây là NGOẠI LỆ có chủ đích của luật "không tự dịch nhãn thành mã": tệp CSV do người
    dùng gõ tay trong Excel, không phải giao diện mình viết ra — bắt họ gõ `maternity_leave`
    là vô lý, mà chặn 422 giữa chừng thì hỏng cả lần nhập. Ở tầng API thì vẫn chặn thẳng.

    Nhận cả ba dạng: mã sẵn (`official`), nhãn đúng (`Nghỉ thai sản`) và nhãn gõ lệch dấu /
    lệch hoa thường (`nghi thai san`). Không nhận ra thì trả rỗng để nơi gọi tự quyết —
    KHÔNG đoán bừa thành "Chính thức", vì đoán sai ở đây là ghi đè trạng thái thật của
    một con người.
    """
    import unicodedata

    from app.core.status_codes import EMPLOYEE_STATUS

    v = (raw or "").strip()
    if not v:
        return ""
    if v in EMPLOYEE_STATUS.values:
        return v

    def norm(s: str) -> str:
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return " ".join(s.replace("đ", "d").replace("Đ", "D").lower().split())

    can = norm(v)
    for code, label in EMPLOYEE_STATUS.labels.items():
        if norm(label) == can:
            return code
    return ""
