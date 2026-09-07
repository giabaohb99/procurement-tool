"""BỘ MÃ RIÊNG CỦA YÊU CẦU MUA HÀNG — số nguyên, theo R2/QĐ-11.

⚠️ Đây KHÔNG phải chỗ khai trạng thái phiếu/dòng YCMH. Hai bộ đó là **mã chuỗi**
(`draft|submitted|approved…` và `no_po|not_ordered|ordered…`), sống ở
`app/core/status_codes.py` theo ngoại lệ QĐ-9 của phân hệ Thu mua — đừng dời
sang đây, và cũng đừng lấy chúng làm cớ để khai cột MỚI bằng chuỗi.

Cột mới thì theo luật chung: `SMALLINT` + hằng số ở tệp này, tiếng Việt chỉ
sống trong các `*_LABELS` và ở tầng hiển thị. Cùng khuôn `leave/constants.py`.
"""

# --------------------------------------------------------------------------
# Nguồn của PHƯƠNG ÁN gắn lên dòng YCMH (bao-CR-310)
# --------------------------------------------------------------------------
#  Vì sao phải phân biệt: phương án lấy từ kho Phiếu khảo sát sản phẩm đã duyệt
#  thì truy ngược được về phiếu gốc (`product_survey_line_id`) — giá có nguồn.
#  Phương án NSTM gõ tay thì KHÔNG truy được, nên phải đánh dấu để sau này lọc
#  ra mà soát, và để báo cáo không trộn hai loại làm một.
PR_OPT_SURVEY = 1   # chọn từ kho khảo sát sản phẩm đã duyệt (tab_survey_product_line)
PR_OPT_MANUAL = 2   # NSTM gõ thẳng NCC + giá, không đi qua phiếu khảo sát

PR_OPTION_SOURCE_LABELS = {
    PR_OPT_SURVEY: "Từ khảo sát",
    PR_OPT_MANUAL: "Nhập tay",
}
