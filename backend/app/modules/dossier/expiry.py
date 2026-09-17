"""TÌNH TRẠNG HIỆU LỰC của một hồ sơ — suy ra từ ngày, không lưu cột nào.

Tách thành tệp riêng vì **ba nơi** cùng cần nó và hai trong số đó không được
phép nhìn thấy nhau: `model.py` (thuộc tính để xuất CSV và bản in đọc thẳng
ORM), `schema.py` (phong bì trả về API) và `service.py`. Để hàm này trong
`service.py` thì `model.py` phải import ngược lại chính tệp đang import nó.

⚠️ Đây là nơi DUY NHẤT của luật «hết hạn / sắp hết hạn». Đừng chép sang
TypeScript để khỏi gọi API — hai bản luật ngày tháng sẽ lệch nhau vào đúng một
ngày không ai để ý, và bên lệch là bên người dùng nhìn.
"""
from datetime import date

from .constants import (EXPIRY_NEAR, EXPIRY_NONE, EXPIRY_OVER, EXPIRY_VALID,
                        EXPIRY_WARN_DAYS)


def expiry_state(expiry: date | None, today: date | None = None) -> tuple[int, int | None]:
    """(mã tình trạng hiệu lực, số ngày còn lại).

    `today` truyền vào được để bài kiểm khỏi phụ thuộc ngày chạy máy — bài kiểm
    khẳng định "hôm nay" là bài kiểm sẽ đỏ vào một sáng nào đó mà không ai đụng
    gì vào mã nguồn.

    Số ngày còn lại trả `None` khi vô thời hạn: `0` ở đó đọc ra «hết hạn hôm
    nay», tức đúng ngược với sự thật.
    """
    if not expiry:
        return EXPIRY_NONE, None
    days = (expiry - (today or date.today())).days
    if days < 0:
        return EXPIRY_OVER, days
    if days <= EXPIRY_WARN_DAYS:
        return EXPIRY_NEAR, days
    return EXPIRY_VALID, days
