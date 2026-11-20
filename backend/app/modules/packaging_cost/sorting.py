"""Xếp có ô trống xuống CUỐI cả hai chiều + khóa phụ ổn định — luật §8 (`chung-dat-ten-va-quy-uoc.md`), dùng chung cho Bảng
giá, Giá mua gần nhất và bảng sản phẩm của Tác động giá (duoc-CR-784)."""
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def is_blank(value) -> bool:
    return value is None or value == ""


def sort_blank_last(items: list[T], key: Callable[[T], object], tie: Callable[[T], object], *, desc: bool = False) -> list[T]:
    """Xếp `items` theo `key` (tăng / giảm); mục có `key` trống xuống cuối ở cả hai chiều, hòa thì theo `tie` TĂNG dần.

    Xếp ổn định hai lượt (khóa phụ tăng trước, khóa chính sau): `reverse=True` của Python giữ nguyên thứ tự gặp của các mục
    bằng nhau nên khóa phụ vẫn tăng dần khi khóa chính giảm.
    """
    keyed = [(key(it), it) for it in sorted(items, key=tie)]       # mỗi khóa tính MỘT lần (khóa có thể tốn: bỏ dấu chữ)
    filled = [pair for pair in keyed if not is_blank(pair[0])]
    blank = [it for value, it in keyed if is_blank(value)]
    filled.sort(key=lambda pair: pair[0], reverse=desc)
    return [it for _, it in filled] + blank
