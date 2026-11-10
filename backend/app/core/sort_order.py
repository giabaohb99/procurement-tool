"""Mệnh đề ORDER BY dùng chung cho mọi bảng danh sách xếp tại server (duoc-CR-744).

Hai luật áp cho MỌI màn, để bấm tiêu đề cột ở đâu cũng ra cùng một kiểu:

1. **Ô trống luôn xuống CUỐI, cả hai chiều** (như Excel). Mặc định của MySQL đặt NULL lên đầu
   khi xếp tăng, còn chuỗi rỗng thì lên đầu như một giá trị nhỏ nhất — xếp tăng cột "Mã YCBG"
   của Phiếu khảo sát là ~54 trang đầu toàn ô trống, người dùng tưởng bấm không ăn.
2. **Luôn có khóa phụ là `id`** để thứ tự ỔN ĐỊNH. Xếp theo một cột có nhiều dòng trùng giá trị
   (Trạng thái, Loại…) mà không có khóa phụ thì MySQL trả các dòng trùng theo thứ tự tùy hứng,
   mỗi trang một kiểu: dòng lặp lại ở trang sau, dòng khác KHÔNG BAO GIỜ hiện ra (đo 10/11/2026:
   Đặt xe xếp theo Loại lặp 192/637 dòng). Khóa phụ do nơi gọi tự gắn vì mỗi màn có thứ tự mặc
   định riêng — xem `with_stable_tiebreak`.
"""
from sqlalchemy import String, case, func


def build_blank_last_order(expr, sort_dir: str, is_text: bool | None = None) -> list:
    """Hai mệnh đề ORDER BY: [ô trống xuống cuối, giá trị theo chiều `sort_dir`].

    `is_text`: cột chữ thì chuỗi rỗng / chỉ khoảng trắng cũng là ô trống; cột số thì CHỈ NULL —
    so cột số với `''` trong MySQL là ép `''` thành 0, tức số 0 bị coi là ô trống. Bỏ trống thì
    đoán theo kiểu của biểu thức.
    """
    if is_text is None:
        is_text = isinstance(getattr(expr, "type", None), String)
    blank = expr.is_(None)
    if is_text:
        blank = blank | (func.trim(expr) == "")
    blank_flag = case((blank, 1), else_=0)
    #  Trong nhóm ô trống, mọi ô coi như BẰNG nhau (NULL) để khóa phụ `id` quyết định —
    #  không thì `''` và `'   '` vẫn tự xếp với nhau theo giá trị thô.
    value = case((blank, None), else_=expr) if is_text else expr
    return [blank_flag.asc(), value.desc() if sort_dir == "desc" else value.asc()]


def with_stable_tiebreak(order: list, id_column) -> list:
    """Gắn khóa phụ `id` giảm dần (bản ghi mới hơn đứng trước trong nhóm trùng giá trị)."""
    return [*order, id_column.desc()]
