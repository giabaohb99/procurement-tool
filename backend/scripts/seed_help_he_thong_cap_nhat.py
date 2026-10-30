# -*- coding: utf-8 -*-
"""Nạp bài HDSD hệ thống cho duoc-CR-671 — MỘT LỆNH: thêm/cập nhật bài rồi nạp luôn kho vector.

Hai thẻ cha "Bắt đầu" và "Quản trị Hệ thống" được dựng TAY trên giao diện (không có script seed sở
hữu), nên script này chỉ thêm / ghi đè đúng hai bài cùng tiêu đề, không xóa hay dựng lại cây — khuôn
chung ở `help_seed_common.upsert_articles`. Chạy lại vô hại.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_he_thong_cap_nhat.py
    docker compose exec -T api python scripts/seed_help_he_thong_cap_nhat.py --dry-run

⚠️ Nội dung phải khớp `core/concurrency_gate.py` (câu báo, 30 giây, `/api/health` miễn) và cờ
`--purge-orphans` của `scripts/reindex_help_rag.py`.
"""
from help_seed_common import ref, run_article_upsert

START_ROOT = "Bắt đầu"
ADMIN_ROOT = "Quản trị Hệ thống"

BUSY_TITLE = "Gặp thông báo 'Hệ thống đang bận' thì làm gì"
OPS_TITLE = "Vận hành: giới hạn lượt gọi cùng lúc và dọn kho tìm kiếm của Trợ lý AI"

ARTICLES = [
    (START_ROOT, BUSY_TITLE,
     "Vì sao đôi khi hệ thống báo 'Hệ thống đang bận, vui lòng thử lại sau ít giây', dữ liệu có mất không, và nên làm gì.",
     """<h2>Gặp thông báo "Hệ thống đang bận" thì làm gì</h2>
<p>Vào giờ cao điểm, khi rất nhiều người cùng bấm cùng lúc, hệ thống <strong>xếp hàng</strong> các thao tác để xử lý lần lượt thay vì để cả hệ thống bị treo. Nếu thao tác của bạn phải chờ quá <strong>30 giây</strong> mà vẫn chưa tới lượt, màn hình hiện câu:</p>
<blockquote><strong>Hệ thống đang bận, vui lòng thử lại sau ít giây.</strong></blockquote>
<h3>1. Dữ liệu của tôi có bị mất hay lưu dở không?</h3>
<p><strong>Không.</strong> Thao tác bị báo bận là thao tác <strong>chưa được thực hiện</strong>: hệ thống trả lời ngay từ cửa, chưa đụng vào dữ liệu. Phiếu bạn đang soạn vẫn còn nguyên trên màn hình, nhưng <strong>chưa được lưu</strong>.</p>
<h3>2. Nên làm gì</h3>
<ol>
<li>Đợi khoảng <strong>5 giây</strong>.</li>
<li>Bấm lại đúng nút vừa bấm (ví dụ <strong>Lưu</strong>, <strong>Gửi duyệt</strong>). Đừng tải lại trang trước khi bấm lại nếu đang soạn dở, kẻo mất phần vừa gõ.</li>
<li>Nếu đang xem báo cáo hoặc trang tổng quan mà một vài khối báo lỗi, chỉ cần tải lại trang sau vài giây.</li>
</ol>
<h3>3. Khi nào cần báo quản trị</h3>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Thỉnh thoảng gặp một lần, bấm lại là được</td><td>Giờ cao điểm, hệ thống đang xếp hàng đúng như thiết kế</td><td>Không cần báo</td></tr>
<tr><td>Bấm lại nhiều lần trong vài phút vẫn báo bận</td><td>Hệ thống đang quá tải kéo dài hoặc có thao tác nặng chạy lâu</td><td>Báo quản trị, ghi rõ <strong>giờ</strong> và <strong>màn hình</strong> đang dùng</td></tr>
<tr><td>Báo <em>Có lỗi xảy ra</em> hoặc kèm mã sự cố</td><td>Đây là lỗi khác, không phải báo bận</td><td>Chụp màn hình kèm mã sự cố gửi quản trị</td></tr>
</tbody>
</table>
<p>Quản trị xem cách chỉnh ngưỡng ở bài {ops}.</p>"""),
    (ADMIN_ROOT, OPS_TITLE,
     "Dành cho quản trị và vận hành: cổng giới hạn số lượt gọi chạy cùng lúc, hai biến cấu hình, và lệnh dọn kho tìm kiếm của Trợ lý AI sau khi nạp bài hướng dẫn.",
     """<h2>Vận hành: giới hạn lượt gọi cùng lúc và dọn kho tìm kiếm của Trợ lý AI</h2>
<p>Bài dành cho <strong>quản trị và bộ phận kỹ thuật</strong>. Người dùng thường chỉ cần đọc bài {busy}.</p>
<h3>1. Cổng giới hạn lượt gọi cùng lúc</h3>
<p>Mỗi tiến trình máy chủ chỉ cho một số lượt gọi chạy <strong>cùng lúc</strong>, luôn nhỏ hơn số kết nối cơ sở dữ liệu nó có. Lượt dư phải <strong>xếp hàng</strong>; chờ quá hạn thì người dùng nhận câu "Hệ thống đang bận" (mã HTTP 503, mã lỗi <code>server_busy</code>). Riêng đường kiểm sức khỏe <code>/api/health</code> không bị giới hạn.</p>
<p>Lý do: trước khi có cổng này, khi khoảng 150 lượt gọi dồn vào cùng lúc, các lượt gọi giữ chỗ kết nối của nhau và máy chủ có thể <strong>treo hẳn</strong> tới khi khởi động lại. Nay quá tải chỉ làm chậm hoặc báo bận, không treo.</p>
<h3>2. Hai biến cấu hình trong tệp <code>.env</code></h3>
<table>
<thead><tr><th>Biến</th><th>Mặc định</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><code>MAX_CONCURRENT_REQUESTS</code></td><td><code>0</code> (tự tính = <code>DB_POOL_SIZE</code> + <code>DB_MAX_OVERFLOW</code> − 5, hiện là 20)</td><td>Số lượt gọi chạy cùng lúc trong MỘT tiến trình. Khai số lớn hơn số kết nối thì hệ thống tự hạ xuống dưới số kết nối.</td></tr>
<tr><td><code>REQUEST_QUEUE_TIMEOUT</code></td><td><code>30</code> giây</td><td>Thời gian tối đa một lượt gọi được xếp hàng trước khi báo bận.</td></tr>
</tbody>
</table>
<p>Muốn tăng sức chứa thì tăng <code>DB_POOL_SIZE</code> / <code>DB_MAX_OVERFLOW</code> (cổng tự tăng theo), nhưng phải nâng <code>max_connections</code> của MySQL song song. Đổi biến xong thì khởi động lại dịch vụ <code>api</code>.</p>
<h3>3. Dọn kho tìm kiếm của Trợ lý AI sau khi nạp bài hướng dẫn</h3>
<p>Các script nạp bài hướng dẫn dựng lại cả cây bài nên bài cũ bị xóa và tạo bài mới. Phần tìm kiếm của bài cũ vẫn còn trong kho của Trợ lý AI, nên trợ lý có thể trích <strong>nội dung bản cũ kèm liên kết chết</strong>. Sau khi chạy các script nạp bài, chạy:</p>
<pre><code>docker compose exec -T api python scripts/reindex_help_rag.py --purge-orphans</code></pre>
<p>Lệnh này xóa phần tìm kiếm của bài không còn trong hệ thống rồi nạp bù phần còn thiếu. Thêm <code>--dry-run</code> để xem trước sẽ xóa và nạp những gì. Dòng đầu tiên lệnh in ra cho biết kho đang thừa bao nhiêu nguồn đã xóa.</p>"""),
]

#  Hai bài trỏ chéo nhau: chèn liên kết sau khi đã có đủ hai tiêu đề.

ARTICLES = [
    (parent, title, summary, body.replace("{ops}", ref(OPS_TITLE, OPS_TITLE)).replace("{busy}", ref(BUSY_TITLE, BUSY_TITLE)))
    for parent, title, summary, body in ARTICLES
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD hệ thống đợt duoc-CR-671 + kho vector")
