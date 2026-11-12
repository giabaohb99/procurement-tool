# -*- coding: utf-8 -*-
"""Nạp bài HDSD hệ thống cho duoc-CR-671 (thêm bài điện thoại ở duoc-CR-752) — MỘT LỆNH: thêm/cập nhật bài
rồi nạp luôn kho vector.

Hai thẻ cha "Bắt đầu" và "Quản trị Hệ thống" được dựng TAY trên giao diện (không có script seed sở
hữu), nên script này chỉ thêm / ghi đè đúng ba bài cùng tiêu đề, không xóa hay dựng lại cây — khuôn
chung ở `help_seed_common.upsert_articles`. Chạy lại vô hại.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_he_thong_cap_nhat.py
    docker compose exec -T api python scripts/seed_help_he_thong_cap_nhat.py --dry-run

⚠️ Nội dung phải khớp `core/concurrency_gate.py` (câu báo, 30 giây, `/api/health` miễn) và cờ
`--purge-orphans` của `scripts/reindex_help_rag.py`. Bài điện thoại khớp ngưỡng 768px của
`frontend-v2/src/shared/hooks/use-mobile.ts` + prop `mobileCard` của `DataTable` (duoc-CR-720/721/722),
`frontend-v2/src/shared/ui/route-error-page.tsx` (màn "Có bản cập nhật mới") và PWA của bản cũ
`frontend/src/components/PwaReloadPrompt.tsx` + `frontend/public/sw-update-old-clients.js` (duoc-CR-685:
dò bản mới mỗi giờ, tự tải lại lúc 0h, hộp báo không lọt vào bản in). frontend-v2 KHÔNG có PWA.
"""
from help_seed_common import ref, run_article_upsert

START_ROOT = "Bắt đầu"
ADMIN_ROOT = "Quản trị Hệ thống"

BUSY_TITLE = 'Gặp thông báo "Hệ thống đang bận" thì làm gì'
BUSY_OLD_TITLES = ["Gặp thông báo «Hệ thống đang bận» thì làm gì", "Gặp thông báo 'Hệ thống đang bận' thì làm gì"]
OPS_TITLE = "Vận hành: giới hạn lượt gọi cùng lúc và dọn kho tìm kiếm của Trợ lý AI"
MOBILE_TITLE = "Dùng ERP trên điện thoại: bảng dạng thẻ và cập nhật bản mới"  # duoc-CR-752
SORT_TITLE = "Sắp xếp bảng danh sách bằng cách bấm tiêu đề cột"  # bài dựng tay đang có dưới "Bắt đầu"

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

MOBILE_ARTICLE = (
    START_ROOT, MOBILE_TITLE,
    "Trên điện thoại, nhiều bảng danh sách của Thu mua, Nhân sự và Đặt xe tự hiện thành thẻ xếp dọc; cách mở phiếu, "
    "chỗ còn giữ bảng, và cách ứng dụng báo khi có bản mới (bản cài đặt Thu mua tự tải lại lúc 0h, hộp báo không bị in ra).",
    f"""<h2>Dùng ERP trên điện thoại</h2>
<p>ERP mở bằng trình duyệt của điện thoại như trên máy tính, cùng tài khoản và cùng quyền. Khi màn hình hẹp hơn <strong>768 điểm ảnh</strong>
(gần như mọi điện thoại cầm dọc), các bảng nhiều cột tự đổi sang <strong>thẻ xếp dọc</strong> để khỏi phải vuốt ngang. Máy tính bảng, điện
thoại xoay ngang đủ rộng, hay máy tính thì vẫn là bảng như cũ.</p>

<h3>1. Bảng hiện thành thẻ</h3>
<ul>
<li>Mỗi dòng của bảng là một thẻ; các thông tin chính nằm trên đầu thẻ. <strong>Chạm vào thẻ</strong> là mở phiếu hoặc mở hộp chi tiết, giống bấm vào dòng trên máy tính.</li>
<li>Ô tìm, bộ lọc và chuyển trang vẫn ở chỗ cũ, dùng như trên bảng.</li>
<li>Ở dạng thẻ không có nút <strong>Cột</strong> (không còn cột để ẩn hay hiện) và không bấm tiêu đề cột để xếp được. Cần xem đủ cột hay xếp lại thì mở
trên màn rộng, xem bài {ref(SORT_TITLE, SORT_TITLE)}.</li>
<li>Màn nào chưa đổi thì vẫn là bảng: vuốt ngang trong bảng để xem các cột còn lại. Trang in, lưới lịch trực, lịch tháng đặt xe và hai bảng thống kê đội xe cố ý giữ bảng.</li>
</ul>

<h3>2. Những phân hệ đã đổi</h3>
<table>
<thead><tr><th>Phân hệ</th><th>Bảng đã thành thẻ</th><th>Lưu ý</th></tr></thead>
<tbody>
<tr><td><strong>Thu mua</strong></td><td>Chi tiết đơn mua hàng: dòng hàng, các lần giao, chi phí thu mua, chi phí theo dòng, thanh toán theo NCC, YCTT của đơn, hộp tạo YCTT. Yêu cầu mua hàng và yêu cầu báo giá: phương án và kết quả khảo sát, chứng từ liên quan, lịch sử mua hàng. Báo cáo: chi phí vận chuyển, chi phí theo ngày, tiến độ theo dòng hàng, hồ sơ của Báo cáo thực hiện, tab Giá vốn nhập khẩu của Báo cáo mua hàng. Các bảng của Tra cứu thị trường.</td><td>Dòng hàng đơn mua hàng còn sửa được thì chọn hàng, nhập số lượng đặt, đơn giá, VAT ngay trên thẻ; các ô khác chạm thẻ để mở hộp chi tiết dòng. Báo cáo thực hiện ở dạng xem <strong>Bảng</strong> tự chuyển về <strong>Xem tổng</strong> trên điện thoại.</td></tr>
<tr><td><strong>Nhân sự</strong></td><td>Hồ sơ nhân sự: tab Hợp đồng, quá trình công tác và quyết định bổ nhiệm, so sánh hộ gia đình, duyệt sửa hồ sơ. Quyền mặc định của chức vụ, mẫu hợp đồng, biến mẫu hợp đồng. Nghỉ phép: phiếu nghỉ bù, đối chiếu kết sổ năm, tab Đang phân bổ, xem trước phân bổ hàng loạt, Thanh toán nghỉ phép. Lịch Sắp tới / Đã qua của phòng họp.</td><td>Cột lương trên thẻ hợp đồng vẫn ẩn hay hiện theo quyền như trên bảng. Xem trước phân bổ hàng loạt vẫn có ô chọn và chọn tất cả. Thẻ thanh toán nghỉ phép không ghi số tiền, phiếu bị kế toán từ chối thì nổi rõ <strong>Kế toán từ chối chi</strong>.</td></tr>
<tr><td><strong>Đặt xe</strong></td><td>Danh sách <strong>Yêu cầu đặt xe</strong> và các khối hàng chờ ở <strong>Tổng quan</strong>: mỗi phiếu một thẻ gồm mục đích, loại và mã phiếu, thời gian, lộ trình kèm điểm dừng, người tạo, xe và tài xế (ghi rõ <em>Tự lái</em> hoặc <em>Chưa bố trí xe</em>), ghi chú chặng duyệt.</td><td>Thẻ không có nút <strong>Nhân bản</strong>: mở phiếu rồi bấm <strong>Nhân bản</strong> ở đầu trang chi tiết. Trên điện thoại, đầu trang chi tiết gom mọi nút lên thanh trên cùng: nút quay lại, các nút quyết định (như <strong>Duyệt</strong>), nút ba chấm cho các việc khác, rồi biểu tượng <strong>In phiếu</strong> và <strong>Nhân bản</strong>.</td></tr>
</tbody>
</table>

<h3>3. Khi hệ thống vừa có bản mới</h3>
<p><strong>ERP</strong> (giao diện mới) không có bản cài đặt; cứ mở bằng trình duyệt. Nếu hệ thống vừa cập nhật trong lúc bạn đang mở một trang, có lúc
màn hiện <strong>Có bản cập nhật mới</strong> với câu <em>Hệ thống vừa được cập nhật nên trang đang mở đã cũ</em>. Bấm <strong>Tải lại trang</strong> là xong; dữ liệu đã lưu không mất.</p>
<p><strong>Ứng dụng Thu mua</strong> (bản cũ) cài được lên màn hình chính điện thoại hoặc máy tính như một ứng dụng. Bản cài đặt này tự lo việc cập nhật:</p>
<ul>
<li>Ứng dụng tự dò bản mới <strong>mỗi giờ</strong> khi có mạng, không cần đóng mở lại.</li>
<li>Có bản mới thì góc dưới bên phải hiện hộp <strong>Đã có phiên bản mới của ứng dụng.</strong> kèm dòng <em>Nếu chưa tải lại, ứng dụng sẽ tự tải lại lúc 0h đêm nay.</em>
Bấm <strong>Tải lại</strong> để lên bản mới ngay, hoặc <strong>Để sau</strong> để tắt hộp.</li>
<li>Dù đã bấm <strong>Để sau</strong>, ứng dụng vẫn <strong>tự tải lại lúc 0h</strong> (theo giờ của máy). Máy đang ngủ lúc 0h thì mở máy lên là ứng dụng tải lại trong vòng một phút.
Tải lại sẽ mất phần đang gõ dở chưa lưu, nên lưu phiếu trước khi rời máy cuối ngày.</li>
<li>Hộp báo bản mới <strong>không bị in ra</strong>: đang hiện hộp mà bấm in phiếu thì bản in vẫn sạch, không cần tắt hộp trước.</li>
<li>Trang đang mở từ một bản quá cũ (chưa biết tự hiện hộp này) sẽ được tải lại ngay một lần khi ứng dụng nhận bản mới.</li>
</ul>""",
)

ARTICLES.append(MOBILE_ARTICLE)

#  Hai bài trỏ chéo nhau: chèn liên kết sau khi đã có đủ hai tiêu đề.

ARTICLES = [
    (parent, title, summary, body.replace("{ops}", ref(OPS_TITLE, OPS_TITLE)).replace("{busy}", ref(BUSY_TITLE, BUSY_TITLE)),
     BUSY_OLD_TITLES if title == BUSY_TITLE else [])
    for parent, title, summary, body in ARTICLES
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD hệ thống đợt duoc-CR-671 + kho vector")
