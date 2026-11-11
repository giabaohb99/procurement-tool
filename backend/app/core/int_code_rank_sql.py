"""Biểu thức SQL xếp một cột MÃ SỐ trạng thái theo thứ tự DÒNG ĐỜI (duoc-CR-748).

Cùng ý với `code_rank_sql.py` nhưng cho cột `SMALLINT` (luật R2): các phiếu nội bộ chạy qua bộ máy duyệt
(đơn nghỉ phép, phiếu nghỉ bù, phiếu thanh toán phép, phiếu đặt phòng họp) đánh số theo THỨ TỰ KHAI —
1 Nháp, 2 Chờ duyệt, 3 Đã duyệt, 4 Từ chối, 5 Trả về, 6 Đã hủy — còn dòng đời đọc là
Nháp → Chờ duyệt → Trả về chỉnh sửa → Đã duyệt → Từ chối → Đã hủy. Xếp thẳng theo số là đặt "Trả về"
sau "Từ chối", người dùng thấy bảng xếp lộn.

Không dùng được `build_value_rank_expression` vì hàm đó so cột với chuỗi (`coalesce(cột, "")`); cột số so
với chuỗi trên SQLite không khớp, còn MySQL thì ép kiểu ngầm. Ở đây so số với số.
"""
from sqlalchemy import case


def build_int_rank_expression(column, ordered_values):
    """Số thứ tự (từ 1) của giá trị trong `column` theo `ordered_values`; mã lạ đứng cuối cùng.

    Ô NULL ra NULL để `sort_order.build_blank_last_order` đẩy xuống CUỐI như mọi ô trống khác.
    """
    whens = [(column == code, rank) for rank, code in enumerate(ordered_values, start=1)]
    return case((column.is_(None), None), *whens, else_=len(ordered_values) + 1)
