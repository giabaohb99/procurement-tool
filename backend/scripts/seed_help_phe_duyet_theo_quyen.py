# -*- coding: utf-8 -*-
"""Nạp bài HDSD duoc-CR-680 — bước duyệt "Người có quyền duyệt (theo phân quyền)". MỘT LỆNH: thêm/cập nhật
bài rồi nạp luôn kho vector (khuôn `help_seed_common.upsert_articles`, chỉ ghi đè đúng bài cùng tiêu đề).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_phe_duyet_theo_quyen.py
    docker compose exec -T api python scripts/seed_help_phe_duyet_theo_quyen.py --dry-run

⚠️ Nội dung phải khớp `app/modules/approval/permission_approvers.py` (bốn điều kiện: ô Duyệt phạm vi
Phòng ban/Công ty/Tất cả, không tính admin, tài khoản mở + có hồ sơ, phạm vi phủ phiếu; ba loại chứng từ mở).
"""
from help_seed_common import run_article_upsert

ADMIN_ROOT = "Quản trị Hệ thống"
TITLE = "Phê duyệt: giao bước duyệt cho 'Người có quyền duyệt (theo phân quyền)'"

ARTICLES = [
    (ADMIN_ROOT, TITLE,
     "Khai một bước duyệt lấy người từ màn Phân quyền — ai được tick 'Duyệt' trên loại chứng từ (vd Đặt xe) "
     "thì người đó duyệt, trong phạm vi dữ liệu của họ.",
     """<h2>Giao bước duyệt cho "Người có quyền duyệt (theo phân quyền)"</h2>
<p>Ở <strong>Phê duyệt ▸ Luồng duyệt</strong>, mỗi bước có ô <strong>Ai duyệt bước này</strong>. Lựa chọn
<strong>Người có quyền duyệt (theo phân quyền)</strong> lấy người duyệt thẳng từ màn
<strong>Nhân sự ▸ Phân quyền tài khoản</strong>: ai giữ vai trò được tick ô <strong>Duyệt</strong> trên chính loại chứng từ
của luồng thì người đó nhận việc. Ví dụ luồng <em>Đặt xe</em>: ai có quyền Duyệt phiếu đặt xe (thường là Điều phối viên,
Quản lý điều phối) sẽ được giao.</p>
<p>Khác <strong>Theo vai trò</strong> ở chỗ <strong>không phải chọn vai trò nào</strong>: thêm hay bớt ô Duyệt cho một vai trò ở màn
Phân quyền là luồng tự đi theo, không phải sửa luồng.</p>

<p>⚠️ Hiện mở cho <strong>Đặt xe</strong>, <strong>Nghỉ phép</strong> và <strong>Đặt phòng họp</strong>. Luồng Văn bản và
Duyệt dấu chưa có lựa chọn này: Văn bản còn có quyền đọc theo thư mục và luật cấm riêng, còn phạm vi <strong>Công ty</strong> của Duyệt dấu
chỉ thấy phiếu đã qua trưởng bộ phận — hai chỗ đó dùng <strong>Theo vai trò</strong> hoặc <strong>Người cụ thể</strong>.</p>

<h3>1. Cách khai</h3>
<ol>
<li>Mở luồng của loại chứng từ cần, bấm <strong>Thêm bước duyệt</strong> hoặc bấm vào bước có sẵn.</li>
<li>Ở <strong>Ai duyệt bước này</strong> chọn <strong>Người có quyền duyệt (theo phân quyền)</strong>.</li>
<li>Ngay dưới ô chọn hiện <strong>danh sách người đang giữ quyền</strong>, kèm vai trò và phạm vi của từng người. Danh sách
rỗng (khung vàng <em>Chưa ai giữ quyền này</em>) nghĩa là bước sẽ không tìm được người duyệt — vào Phân quyền tick ô Duyệt cho vai
trò phù hợp trước.</li>
<li>Chọn <strong>Nhiều người thì</strong> (thường để <em>Một người duyệt là đủ</em>) rồi bấm <strong>Thêm bước</strong> / <strong>Lưu bước</strong>.</li>
</ol>

<h3>2. Ai được giao — bốn điều kiện</h3>
<table>
<thead><tr><th>Điều kiện</th><th>Giải thích</th></tr></thead>
<tbody>
<tr><td>Giữ vai trò có ô <strong>Duyệt</strong> trên loại chứng từ</td><td>Tick ở Nhân sự ▸ Phân quyền tài khoản, cột Duyệt.</td></tr>
<tr><td>Phạm vi của vai trò đó là <strong>Phòng ban, Công ty hoặc Tất cả</strong></td><td><strong>Của mình</strong>, <strong>Được giao</strong> và các bậc <em>… đã duyệt</em> chỉ với tới phiếu do chính người đó tạo hoặc đã qua duyệt, không bao giờ phủ phiếu mới của người khác — nên không tính.</td></tr>
<tr><td>Không tính vai trò <strong>Quản trị hệ thống</strong></td><td>Quản trị có đủ mọi quyền; tính vào là mọi phiếu đổ về tài khoản quản trị. Quản trị giữ thêm một vai trò có quyền Duyệt thì vẫn được tính.</td></tr>
<tr><td>Phạm vi dữ liệu <strong>phủ được chính phiếu đó</strong></td><td>Phạm vi <strong>Công ty</strong> chỉ nhận phiếu của công ty mình; <strong>Phòng ban</strong> chỉ nhận phiếu của phòng mình; <strong>Tất cả</strong> nhận mọi phiếu. Chỉ xét phạm vi của chính các vai trò có quyền Duyệt — vai trò khác của người đó (kể cả Quản trị) không mở rộng thêm.</td></tr>
</tbody>
</table>
<p>Ngoài ra tài khoản phải <strong>đang mở</strong> và đã <strong>gắn hồ sơ nhân sự</strong>; hồ sơ đã nghỉ việc thì bỏ. Người nộp phiếu luôn bị loại khỏi bước của chính phiếu mình.</p>

<h3>3. Lưu ý</h3>
<ul>
<li>Đổi phân quyền thì <strong>phiếu gửi duyệt sau đó</strong> tự theo. Phiếu đang chờ ở bước này giữ người đã được giao lúc mở bước (giống cách <strong>Theo vai trò</strong>).</li>
<li><strong>Phiếu đặt xe</strong> có ô chọn <em>Người duyệt</em> (danh sách chính là những người giữ quyền ở trên). Phiếu đã chọn người thì bước <strong>Người có quyền duyệt</strong> chỉ giao cho đúng người đó, bất kể công ty trên phiếu (hai ô độc lập); người đó mất quyền trước lúc mở bước thì bước tính như phiếu chưa chọn.</li>
<li>Không ai thỏa cả bốn điều kiện thì bước xử lý theo ô <strong>Không tìm được người duyệt thì</strong> trong <strong>Tùy chỉnh thêm</strong> — nên khai người dự phòng.</li>
<li>Danh sách hiện trong lúc khai luồng là <strong>chưa lọc theo phiếu</strong> (lúc đó chưa có phiếu nào); khi chạy thật hệ mới lọc theo phạm vi của từng người.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD phê duyệt theo quyền duoc-CR-680 + kho vector")
