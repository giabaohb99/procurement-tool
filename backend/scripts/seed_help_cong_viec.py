# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho phân hệ DỰ ÁN / CÔNG VIỆC — các tính năng ra ngày 22/10/2026 (duoc-CR-670).

CHỈ viết bài cho tính năng MỚI (chuông Công việc · việc dự án trong «Việc cần làm» · sửa bình luận · Thùng
rác · ghim dự án); KHÔNG viết lại toàn bộ phân hệ — phần còn lại của phân hệ chưa có bộ hướng dẫn riêng.
Dựng 1 thẻ phân hệ + 3 bài.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_cong_viec.py
    docker compose exec -T api python scripts/reindex_help_rag.py     # nạp vào kho tìm kiếm của trợ lý

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (xem `help_seed_common.py`).

⚠️ Phải KHỚP với cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/30-du-an-cong-viec.md` (đẩy lên hệ đang chạy
bằng `scripts/publish_handbook_update.py`) và `doc/erp/cong-viec/01-danh-sach-tinh-nang.md`.
"""
from help_seed_common import rebuild_tree, ref

CHUONG = "Dự án — Chuông báo giao việc và Việc cần làm"
BINH_LUAN = "Dự án — Sửa bình luận của mình"
THUNG_RAC = "Dự án — Thùng rác và ghim dự án"

TREE = {
    "title": "Hướng dẫn sử dụng Dự án và Công việc",
    "icon": "workflow",
    "summary": "Chuông báo giao việc, việc dự án trong «Việc cần làm», sửa bình luận, Thùng rác, ghim dự án",
    "content": f"""<h2>Dự án và Công việc</h2>
<p>Phân hệ <strong>Dự án</strong> (menu <strong>Dự án</strong>) để giao việc, theo dõi tiến độ theo cột kanban, bình luận và đính kèm tệp ngay trên từng công việc. Bộ hướng dẫn này hiện chỉ gom các tính năng <strong>mới</strong>, đọc theo việc bạn cần làm:</p>
<ul>
<li>Muốn biết khi nào mình nhận chuông và việc được giao nằm ở đâu: {ref(CHUONG, "Chuông báo giao việc và Việc cần làm")}.</li>
<li>Viết sai trong bình luận: {ref(BINH_LUAN, "Sửa bình luận của mình")}.</li>
<li>Lỡ xóa nhầm một công việc, hoặc muốn dự án hay dùng nằm trên cùng: {ref(THUNG_RAC, "Thùng rác và ghim dự án")}.</li>
</ul>
<p>Chưa có: <strong>nhắc hạn</strong> (đến hạn / quá hạn) tự động qua chuông.</p>""",
    "children": [
        {
            "title": CHUONG,
            "icon": "bell",
            "summary": "Khi nào có chuông (giao việc, đổi trạng thái, bình luận), ai nhận, và việc dự án nằm ở tab Việc cần làm",
            "content": f"""<h2>Chuông báo của Công việc</h2>
<p>Từ ngày 22/10/2026, chuông thông báo ở góc trên màn hình kêu khi có các sự việc sau trên công việc của dự án:</p>
<table>
<thead><tr><th>Sự việc</th><th>Dòng bạn thấy trên chuông</th><th>Ai nhận</th></tr></thead>
<tbody>
<tr><td><strong>Được giao việc</strong></td><td><em>«Bạn được giao việc: …»</em>, kèm tên người giao và hạn</td><td>Người <strong>mới được thêm</strong> làm người phụ trách</td></tr>
<tr><td><strong>Đổi trạng thái</strong></td><td><em>«Việc «…» đã hoàn thành»</em> (hoặc <em>mở lại</em>, <em>hủy</em>)</td><td>Người phụ trách và người theo dõi</td></tr>
<tr><td><strong>Bình luận mới</strong></td><td>Trích nội dung bình luận</td><td>Người phụ trách, người theo dõi, người đã bình luận trước đó</td></tr>
<tr><td><strong>@nhắc tên</strong> trong bình luận</td><td>Bạn được nhắc trong bình luận</td><td>Người được nhắc</td></tr>
</tbody>
</table>
<p>Bấm vào dòng trên chuông là mở thẳng công việc đó.</p>

<h2>Ba điều đáng biết</h2>
<ul>
<li><strong>Không báo cho chính người thao tác.</strong> Tự giao việc cho mình, tự bấm hoàn thành việc của mình thì không có chuông nào kêu.</li>
<li><strong>Chỉ báo cho người còn là thành viên của dự án.</strong> Người đã bị gỡ khỏi dự án không nhận chuông nữa, kể cả khi tên họ vẫn nằm trên công việc; họ cũng không đọc được nội dung việc.</li>
<li>Nhân sự <strong>chưa có tài khoản đăng nhập</strong> thì không có chuông để kêu.</li>
</ul>
<p>⚠️ <strong>Nhắc hạn chưa có.</strong> Đến hạn hay quá hạn, hệ không tự gửi chuông; hạn chỉ hiện trên công việc và trong «Việc cần làm».</p>

<h2>Việc được giao cho tôi nằm ở đâu</h2>
<p>Vào trang cá nhân của bạn, nhóm <strong>«Việc của tôi»</strong>, tab <strong>«Việc cần làm»</strong>. Công việc dự án giao cho bạn hiện chung với các việc khác (phiếu cần duyệt, công nợ…) thành từng dòng:</p>
<ul>
<li>nhãn <strong>«Việc được giao»</strong> (loại <em>Dự án</em>), hoặc <strong>«Việc quá hạn»</strong> nếu đã quá hạn;</li>
<li>dòng phụ ghi tên dự án và hạn; bấm vào mở thẳng công việc.</li>
</ul>
<p>Hệ chỉ liệt kê việc <strong>đang mở</strong> mà bạn là <strong>người phụ trách</strong>, thuộc dự án <strong>chưa lưu trữ</strong> và bạn <strong>còn là thành viên</strong>. Người theo dõi nhận chuông nhưng việc không vào danh sách này vì họ không phải người làm. Việc hoàn thành hay bị hủy thì biến khỏi danh sách.</p>
<p>Không thấy chuông hay không thấy việc? Kiểm ba thứ: bạn còn trong danh sách <em>Thành viên</em> của dự án không; bạn có đúng là người phụ trách không (không phải người theo dõi); và tài khoản của bạn có quyền xem Công việc không. Xem thêm {ref(THUNG_RAC, "Thùng rác và ghim dự án")}.</p>""",
        },
        {
            "title": BINH_LUAN,
            "icon": "mail",
            "summary": "Sửa bình luận do chính mình viết, nhãn «đã sửa», ai sửa được, chuông có kêu lại không",
            "content": f"""<h2>Sửa bình luận của mình</h2>
<p>Từ ngày 22/10/2026, bạn sửa được bình luận mình đã gửi trên công việc, không cần xóa đi viết lại.</p>

<h2>Cách làm</h2>
<ol>
<li>Mở công việc, tìm bình luận của bạn.</li>
<li>Bấm biểu tượng bút <strong>«Sửa bình luận»</strong> ở đầu bình luận.</li>
<li>Bình luận biến thành ô soạn. Chữa nội dung (người đã được @nhắc hiện thành <code>@Tên</code>, cứ giữ nguyên).</li>
<li>Bấm <strong>«Lưu»</strong> (hoặc <strong>Ctrl + Enter</strong>). Muốn bỏ thì bấm <strong>«Hủy»</strong> (hoặc <strong>Esc</strong>).</li>
</ol>
<p>Bình luận đã sửa mang nhãn <strong>«(đã sửa)»</strong> để mọi người biết nội dung đã khác lúc đầu. Nếu bạn lưu mà không đổi chữ nào thì không có gì thay đổi.</p>

<h2>Ai sửa được</h2>
<ul>
<li>Chỉ <strong>chính người viết</strong>. Chủ sở hữu hay Quản trị dự án cũng không sửa được lời người khác — muốn bỏ nội dung không phù hợp thì dùng nút <strong>xóa</strong>.</li>
<li><strong>Khách xem</strong> không sửa được. Người đã bị gỡ khỏi dự án thì không sửa được, dù trước đây là người viết.</li>
<li>Dự án đã lưu trữ thì khóa mọi thao tác ghi.</li>
</ul>

<h2>Sửa xong có chuông kêu lại không?</h2>
<p><strong>Không.</strong> Sửa chính tả không gửi lại thông báo cho những người đã nhận. Người đã được @nhắc từ trước giữ nguyên. Ô sửa <strong>không có bảng gợi ý @</strong>: muốn nhắc thêm một người, hãy viết một bình luận mới.</p>
<p>Khái quát về chuông: {ref(CHUONG, "Chuông báo giao việc và Việc cần làm")}.</p>""",
        },
        {
            "title": THUNG_RAC,
            "icon": "lightbulb",
            "summary": "Khôi phục công việc đã xóa, và ghim tối đa 20 dự án lên đầu thanh bên",
            "content": f"""<h2>Thùng rác của dự án</h2>
<p>Xóa một công việc chỉ là <strong>xóa mềm</strong>: dữ liệu vẫn còn và lấy lại được.</p>
<ol>
<li>Mở dự án, bấm nút <strong>«Quản lý dự án»</strong> ở góc trên bên phải.</li>
<li>Chọn <strong>«Thùng rác»</strong>. Hộp liệt kê các công việc đã xóa của dự án đó, mới xóa nằm trên cùng, kèm <em>thời điểm xóa</em> và <em>người xóa</em>.</li>
<li>Bấm <strong>«Khôi phục»</strong> cạnh công việc cần lấy lại. Công việc quay về dự án như cũ.</li>
</ol>
<p>Thùng rác đang trống thì hộp ghi <em>«Thùng rác đang trống.»</em></p>
<ul>
<li><strong>Việc cha và việc con:</strong> khôi phục việc cha thì các việc con bị xóa <em>cùng lúc</em> cũng quay lại. Việc con không khôi phục trước được việc cha — khôi phục việc cha trước.</li>
<li><strong>Ai khôi phục được:</strong> Chủ sở hữu và Quản trị khôi phục mọi việc; <strong>Thành viên</strong> chỉ khôi phục việc <strong>do mình tạo</strong>; <strong>Khách xem</strong> không thấy mục Thùng rác. Không đủ quyền thì nút «Khôi phục» không hiện.</li>
<li><strong>Dự án đã lưu trữ</strong> bị khóa, không khôi phục được cho tới khi mở lại dự án.</li>
</ul>

<h2>Ghim dự án lên đầu thanh bên</h2>
<p>Dự án bạn dùng hằng ngày có thể nằm trên cùng, khỏi phải cuộn tìm:</p>
<ol>
<li>Ở thanh bên trái, rê chuột vào tên dự án (hoặc di chuyển tới tên dự án bằng bàn phím).</li>
<li>Bấm biểu tượng ghim <strong>«Ghim lên đầu danh sách»</strong>.</li>
<li>Dự án chuyển lên khu <strong>«Đã ghim»</strong> ở đầu thanh bên, theo thứ tự bạn ghim. Dự án đã ghim luôn hiện biểu tượng ghim; bấm vào <strong>«Bỏ ghim»</strong> để gỡ.</li>
</ol>
<ul>
<li>Ghim <strong>tối đa 20 dự án</strong>. Đủ 20 thì không ghim thêm được cho tới khi bỏ bớt.</li>
<li>Ghim là <strong>của riêng bạn</strong> và đi theo tài khoản: đổi máy, đổi trình duyệt vẫn còn. Người khác không thấy dự án bạn ghim.</li>
<li>Dự án đã lưu trữ hoặc bạn bị gỡ khỏi dự án thì tự biến khỏi khu «Đã ghim».</li>
</ul>
<p>Xem thêm: {ref(CHUONG, "Chuông báo giao việc và Việc cần làm")} · {ref(BINH_LUAN, "Sửa bình luận của mình")}.</p>""",
        },
    ],
}

if __name__ == "__main__":
    rebuild_tree(TREE)
