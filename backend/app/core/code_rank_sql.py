"""Biểu thức SQL xếp một cột MÃ trạng thái theo thứ tự TIẾN TRÌNH (duoc-CR-744).

Cột trạng thái lưu mã tiếng Anh (`not_ordered`, `doc_sent`…) còn màn hình bày nhãn tiếng Việt.
Xếp thẳng theo cột là xếp theo chữ cái của MÃ — người dùng thấy "Hoàn thành" kẹp giữa
"Đã gửi ĐMH cho KT" và "Đã nhận hàng", tưởng bảng xếp lộn. Xếp theo thứ tự tiến trình thì ra
đúng dòng đời; các mã ngoại lệ (Tạm ngưng, Hủy) đứng sau chuỗi.
"""
from sqlalchemy import case, func

from app.core.status_catalog import CodeSet


def build_value_rank_expression(column, ordered_values, blank_value: str | None = None):
    """Số thứ tự của giá trị trong `column` theo `ordered_values`; giá trị lạ đứng cuối cùng.

    Ô rỗng / NULL ra NULL để `sort_order.build_blank_last_order` đẩy nó xuống CUỐI như mọi ô
    trống khác — TRỪ khi màn hình không bày nó là ô trống: truyền `blank_value` là mã mà ô
    rỗng đang được hiển thị thành (vd dòng cũ chưa có tiến độ hiện "Chưa đặt hàng" thì truyền
    `not_ordered`).
    """
    ranks = {value: i + 1 for i, value in enumerate(v for v in ordered_values if v)}
    value = func.coalesce(column, "")
    whens = [(value == code, rank) for code, rank in ranks.items()]
    whens.append((value == "", ranks.get(blank_value) if blank_value else None))
    return case(*whens, else_=len(ranks) + 1)


def build_code_rank_expression(column, code_set: CodeSet, blank_value: str | None = None):
    """Như `build_value_rank_expression`, thứ tự lấy từ bộ mã: chuỗi tiến trình theo
    `sort_order` trước, mã ngoại lệ sau theo thứ tự khai."""
    chain = list(code_set.ordered_values)
    exceptions = [c.value for c in code_set.codes if c.value not in chain]
    return build_value_rank_expression(column, chain + exceptions, blank_value)
