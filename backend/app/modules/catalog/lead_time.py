"""Số ngày quy định (QĐ) có hàng theo Phân loại VTBB/NL — dùng chung YCMH + ĐMH.

Danh mục Phân loại giữ 2 mốc: `std_days` (NCC CÓ sẵn hàng) và `std_days_unavail` (KHÔNG sẵn).
Luật chốt với khách (CR-065): mặc định LUÔN lấy mốc DÀI NHẤT — tức mốc "không sẵn hàng" — vì
lúc tạo phiếu/đơn chưa ai chắc NCC còn hàng; thiếu mốc đó thì lùi về mốc "có sẵn", thiếu cả hai
thì 15 ngày. Đây chỉ là GIÁ TRỊ KHỞI TẠO: người dùng sửa lại được và hệ thống không ép đồng bộ.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .model import ItemGroup

DEFAULT_STD_DAYS = 15   # phân loại chưa khai báo số ngày (vd "Vận chuyển") -> 15 ngày


def _int(x) -> int:
    """Số ngày trong danh mục là chuỗi tự do ("10", "10 ngày") -> lấy phần chữ số."""
    return int("".join(ch for ch in str(x or "") if ch.isdigit()) or 0)


def std_days_map(db: Session) -> dict[str, int]:
    """{tên phân loại: số ngày QĐ} — đã áp luật "lấy mốc dài nhất, thiếu thì 15 ngày"."""
    return {(g.name or "").strip():
            (_int(g.std_days_unavail) or _int(g.std_days) or DEFAULT_STD_DAYS)
            for g in db.query(ItemGroup).all()}


def std_days_of(m: dict[str, int], item_group: str) -> int:
    """Số ngày QĐ của 1 phân loại; phân loại lạ/để trống cũng ra mốc mặc định."""
    return m.get((item_group or "").strip(), DEFAULT_STD_DAYS) or DEFAULT_STD_DAYS


def add_days(base: str, days: int) -> str:
    """"YYYY-MM-DD" + số ngày -> "YYYY-MM-DD"; mốc gốc trống/sai định dạng thì trả về ""."""
    base = (base or "").strip()
    if not base or days <= 0:
        return ""
    try:
        return (date.fromisoformat(base[:10]) + timedelta(days=days)).isoformat()
    except ValueError:
        return ""


def regulated_date(m: dict[str, int], item_group: str, base: str) -> str:
    """Ngày QĐ có hàng = mốc gốc (ngày tiếp nhận YCMH / ngày đặt hàng ĐMH) + số ngày QĐ."""
    return add_days(base, std_days_of(m, item_group))
