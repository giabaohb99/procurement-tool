# -*- coding: utf-8 -*-
"""Bài HDSD Thu mua cho duoc-CR-780 (18/11/2026): gập / mở từng thẻ ở các màn Thu mua (giao diện ERP mới).

Cây trợ giúp Thu mua được dựng TAY trên giao diện (không có script sở hữu), nên script này KHÔNG xóa / dựng lại cây.
Nó chỉ thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Dành cho Nhân viên Mua hàng*, rồi nạp lại kho
vector cho đúng bài đó (`help_seed_common.run_article_upsert`).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_gap_mo_the_cr780.py --dry-run
    docker compose exec -T api python scripts/seed_help_thu_mua_gap_mo_the_cr780.py
"""
from help_seed_common import run_article_upsert

STAFF_ROOT = "Dành cho Nhân viên Mua hàng"

ARTICLES = [
    (STAFF_ROOT, "Gập / mở từng thẻ ở các màn Thu mua",
     "Mỗi thẻ ở màn chi tiết YCMH, YCBG, ĐMH, phiếu khảo sát, màn xử lý, Tổng quan và Báo cáo Thu mua gập / mở được và được nhớ.",
     """<h2>Gập / mở từng thẻ ở các màn Thu mua</h2>
<p>Từ ngày 18/11/2026, trên giao diện ERP mới, mỗi thẻ ở các màn Thu mua có <strong>nút mũi tên</strong> ở góc phải tiêu đề: mũi tên lên là <strong>Thu gọn</strong>, mũi tên xuống là <strong>Mở</strong>. Thẻ gập chỉ còn dòng tiêu đề, giúp trang ngắn lại để tới nhanh phần đang cần.</p>
<table>
<thead><tr><th>Màn</th><th>Thẻ gập được</th></tr></thead>
<tbody>
<tr><td><strong>Chi tiết Yêu cầu mua hàng</strong></td><td>Thông tin chung, Danh sách Sản phẩm Yêu cầu, Nhà cung cấp, Phương án, Chứng từ liên quan, Chứng từ và tài liệu đính kèm, Trao đổi, Lịch sử thao tác</td></tr>
<tr><td><strong>Chi tiết Yêu cầu báo giá</strong></td><td>Thông tin chung, Danh sách Sản phẩm cần Khảo sát, Kết quả khảo sát, Báo cáo thực hiện, Trao đổi, Lịch sử thao tác</td></tr>
<tr><td><strong>Chi tiết Đơn mua hàng</strong></td><td>Thông tin chung, Dòng hàng, Báo cáo thực hiện, Chi phí thu mua, Chi phí theo dòng hàng, Yêu cầu thanh toán của đơn này, Chứng từ và tài liệu đính kèm, Trao đổi, Lịch sử thao tác</td></tr>
<tr><td><strong>Chi tiết Phiếu khảo sát</strong></td><td>Thông tin chung, Khảo sát nhà cung cấp, Khảo sát sản phẩm, Chứng từ và tài liệu đính kèm, Trao đổi, Lịch sử thao tác</td></tr>
<tr><td><strong>Xử lý phương án / Xử lý khảo sát</strong></td><td>Thẻ xử lý</td></tr>
<tr><td><strong>Chứng từ của đơn</strong> (Xem cả chuỗi chứng từ)</td><td>Từng nấc: Đơn mua hàng, Yêu cầu mua hàng, Phiếu khảo sát, Yêu cầu báo giá</td></tr>
<tr><td><strong>Tổng quan Thu mua</strong>, tab <strong>Tổng quan</strong> của Báo cáo mua hàng</td><td>Các thẻ biểu đồ</td></tr>
</tbody>
</table>
<ul>
<li>Hệ thống <strong>nhớ</strong> thẻ nào đã gập theo từng loại chứng từ trên máy đang dùng: gập thẻ Nhà cung cấp ở một YCMH thì các YCMH khác mở ra cũng gập sẵn thẻ đó, còn thẻ cùng tên ở Đơn mua hàng không bị ảnh hưởng.</li>
<li>Khi <strong>lập chứng từ mới</strong>, mọi thẻ luôn mở và không có nút gập, để không sót ô bắt buộc.</li>
<li>Ở Yêu cầu báo giá, bấm Lưu mà thẻ Thông tin chung còn ô bắt buộc chưa điền thì thẻ tự mở ra để thấy ô tô đỏ.</li>
<li>Nút trên tiêu đề thẻ (Upload chứng từ, Thêm dòng, Thêm chi phí...) vẫn bấm được khi thẻ đang gập.</li>
<li>Thẻ <strong>Báo cáo thực hiện</strong> (YCBG, ĐMH) cũng dùng nút mũi tên ở góc phải như các thẻ khác, thay cho mũi tên bên trái tiêu đề trước đây; thẻ này mặc định gập khi mở trang.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD Thu mua duoc-CR-780: gập / mở từng thẻ ở các màn Thu mua")
