# -*- coding: utf-8 -*-
"""Sắp lại cây HDSD «Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI»: nối bằng đăng nhập ERP (OAuth) là CÁCH 1, ưu tiên;
khóa dán tay là CÁCH 2 (nâng cao). Đại ca chốt 26/10/2026 (kh-AI-ket-noi-hdsd); màn /connect-ai của giao diện v2 dùng cùng
câu chữ Cách 1 / Cách 2.

MỘT LỆNH, không dựng lại cây: ghi đè bài gốc + hai bài (tìm theo tiêu đề MỚI hoặc CŨ, đổi tên), đặt thứ tự Cách 1 → Cách 2
→ các bài còn lại giữ thứ tự cũ, sửa mọi liên kết trỏ tới tên cũ trong Trung tâm trợ giúp, rồi nạp kho vector cho các bài đã ghi.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_ket_noi_ai_cach_1.py --dry-run
    docker compose exec -T api python scripts/seed_help_ket_noi_ai_cach_1.py

`seed_help_ket_noi_ai_mcp.py` (dựng cả cây) lấy tiêu đề + nội dung ba bài này từ tệp đây — sửa một chỗ.
"""
from help_seed_common import ref, reindex_articles, slugify

ROOT_TITLE = "Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI"
OAUTH = "Cách 1 (khuyên dùng): nối bằng đăng nhập ERP"
TAO_KHOA = "Cách 2 (nâng cao): sửa tệp cấu hình bằng khóa riêng"
OLD_TITLES = {OAUTH: "Nối ChatGPT và claude.ai bằng đăng nhập ERP", TAO_KHOA: "Tạo khóa kết nối AI riêng ở Trang cá nhân"}
CLAUDE_DESKTOP = "Nối Claude Desktop với ERP"
CLIENT_KHAC = "Nối Claude Code, Cursor và Gemini CLI với ERP"
CONG_CU = "AI riêng của bạn làm được gì trong ERP: công cụ và skill"
QUAN_TRI = "Dành cho quản trị — Kho skill AI: bộ skill, xuất bản, ai được đọc"
NHAT_KY = "Nhật ký lượt gọi của AI riêng và lỗi thường gặp khi nối"
KEY = "&lt;KHÓA_CỦA_BẠN&gt;"
URL = "https://erp.degoholding.vn/api/mcp"

ROOT_SUMMARY = "Dùng ChatGPT, Claude… của chính bạn để hỏi dữ liệu ERP và đọc cẩm nang công ty — nên nối bằng đăng nhập ERP (Cách 1)"
ROOT_CONTENT = f"""<h2>Kết nối AI riêng là gì?</h2>
<p>Ứng dụng AI của riêng bạn (ChatGPT, claude.ai, Claude Desktop, Cursor…) vào ERP <strong>dưới đúng tài khoản của bạn</strong>: tra phiếu
của bạn, xem báo cáo bạn được giao, đọc cẩm nang công ty — trong phạm vi quyền bạn đang có, không hơn. Model chạy bằng gói AI của
chính bạn; ERP chỉ cung cấp dữ liệu và cẩm nang.</p>
<p><strong>Nên chọn Cách 1</strong> — {ref(OAUTH, "nối bằng đăng nhập ERP")}: dán địa chỉ cổng, đăng nhập ERP, bấm Cho phép, không phải
giữ khóa nào. Chỉ dùng {ref(TAO_KHOA, "Cách 2 — khóa riêng")} khi ứng dụng không có mục Connectors (Claude Code, Cursor, Gemini CLI).</p>

<h2>Hai cách nối</h2>
<table>
<thead><tr><th></th><th>Cách 1 (khuyên dùng)</th><th>Cách 2 (nâng cao)</th></tr></thead>
<tbody>
<tr><td>Ứng dụng</td><td>ChatGPT, claude.ai, Claude Desktop (mục Connectors)</td><td>Claude Code, Cursor, Gemini CLI, Claude Desktop sửa tệp cấu hình</td></tr>
<tr><td>Bạn làm</td><td>Dán địa chỉ cổng ▸ đăng nhập ERP ▸ bấm Cho phép</td><td>Tạo khóa ở Trang cá nhân ▸ dán đoạn cấu hình có khóa vào tệp của ứng dụng</td></tr>
<tr><td>Giữ bí mật</td><td>Không có khóa trên tay</td><td>Khóa <code>dego_mcp_…</code> là chìa vào dữ liệu của bạn — không gửi, không chụp</td></tr>
<tr><td>Hạn, gỡ</td><td colspan="2">90 ngày; gỡ hoặc tạm tắt ở Trang cá nhân ▸ Kết nối AI riêng ▸ Khóa của bạn</td></tr>
</tbody>
</table>
<p>Nối xong, hỏi thử: <em>Tôi còn bao nhiêu ngày phép?</em> — rồi quay lại màn Kết nối AI riêng bấm <strong>Kiểm tra lại</strong>, thấy
<em>Đã nối</em> là xong. Mọi lượt AI gọi vào ERP đều ghi nhật ký, kể cả lượt bị từ chối.</p>

<h2>Đọc theo việc bạn cần làm</h2>
<p><strong>Nhân sự:</strong> {ref(OAUTH, "Cách 1")} · {ref(TAO_KHOA, "Cách 2")} · {ref(CLAUDE_DESKTOP, "Claude Desktop")} ·
{ref(CLIENT_KHAC, "Claude Code, Cursor, Gemini CLI")} · {ref(CONG_CU, "AI làm được gì")} · {ref(NHAT_KY, "nhật ký và lỗi thường gặp")}.</p>
<p><strong>Quản trị, trưởng phòng:</strong> {ref(QUAN_TRI, "Kho skill AI: bộ skill, xuất bản, ai được đọc, phát khóa, ứng dụng đã kết nối, cấu hình")}.</p>"""

OAUTH_SUMMARY = "Dán địa chỉ cổng, đăng nhập ERP, đọc tên miền quay về rồi bấm Cho phép — không cần khóa; dùng cho ChatGPT, claude.ai, Claude Desktop"
OAUTH_CONTENT = f"""<h2>Cách 1 (khuyên dùng): nối bằng đăng nhập ERP</h2>
<p>Dùng cho <strong>ChatGPT, claude.ai và Claude Desktop</strong>. Không dán khóa: bạn đưa ứng dụng <strong>địa chỉ cổng</strong>, ứng dụng mở
trang ERP, bạn đăng nhập và bấm <strong>Cho phép</strong>. Lấy địa chỉ cổng ở <strong>Trang cá nhân ▸ Kết nối AI riêng</strong> (nút chép),
ví dụ <code>{URL}</code>.</p>

<h2>claude.ai và Claude Desktop</h2>
<p>Không cần cài Node.js, không cần khóa, không sửa tệp nào. Khoảng 2 phút.</p>
<ol>
<li>Mở Claude (Claude Desktop hoặc claude.ai trên trình duyệt). Bấm tên bạn ở góc dưới bên trái ▸ <strong>Settings ▸ Connectors</strong>.</li>
<li>Bấm <strong>Add custom connector</strong>. Tên: <em>DEGO ERP</em>; dán địa chỉ cổng vào <strong>Remote MCP server URL</strong> ▸ <strong>Add</strong>.</li>
<li>Bấm <strong>Connect</strong> ở dòng DEGO ERP. Trình duyệt mở trang ERP ▸ đăng nhập nếu được hỏi ▸ chọn mức ▸ <strong>Cho phép</strong>.</li>
<li>Quay lại Claude, mở cuộc trò chuyện mới. Bật <em>DEGO ERP</em> ở nút công cụ trong ô chat rồi hỏi.</li>
</ol>
<ul>
<li>Thêm ở claude.ai hay ở Claude Desktop đều được: cùng một tài khoản Claude thì hai nơi dùng chung kết nối.</li>
<li><strong>Muốn AI soạn phiếu hoặc xuất tệp Excel / Word thì chọn mức Được ghi</strong>. Mức Chỉ đọc chỉ tra cứu.</li>
<li>Trước đây đã nối bằng tệp cấu hình ({ref(TAO_KHOA, "Cách 2")})? Nối xong Cách 1 thì xóa khối <code>dego-erp</code> trong tệp <code>claude_desktop_config.json</code> và gỡ khóa cũ ở Khóa của bạn, kẻo Claude thấy hai bộ công cụ trùng nhau.</li>
<li>Gói Team / Enterprise: có thể chỉ chủ tổ chức mới thêm được kết nối (ở <em>Organization settings</em>), sau đó từng người bấm Connect.</li>
</ul>

<h2>ChatGPT (gói trả phí)</h2>
<ol>
<li>Mở <strong>Settings ▸ Connectors</strong> (hoặc <code>chatgpt.com/#settings/Connectors</code>). Chưa thấy nút tạo thì bật
<strong>Developer mode</strong> (Connectors ▸ Advanced settings).</li>
<li>Bấm <strong>Create</strong>: Name <em>DEGO ERP</em> · MCP Server URL dán địa chỉ cổng · Authentication <strong>OAuth</strong> · tick
<strong>I trust this application</strong> ▸ <strong>Create</strong>.</li>
<li>Trang ERP mở ra ▸ kiểm tên miền quay về là <em>chatgpt.com</em> / <em>openai.com</em> ▸ đăng nhập ▸ chọn mức ▸ <strong>Cho phép</strong>.</li>
<li>Trong ô chat bấm <strong>+</strong> (hoặc <em>Apps</em>) ▸ bật <em>DEGO ERP</em> rồi hỏi.</li>
</ol>
<p>Chữ <em>Beta intended for developer use only</em> là của ChatGPT, không phải lỗi.</p>

<h2>Màn Cho phép: đọc kỹ trước khi bấm</h2>
<ul>
<li><strong>Tên miền quay về mới là bằng chứng</strong>, tên ứng dụng thì ai cũng tự khai được. Tên miền lạ thì màn hiện hộp cảnh báo
đỏ — không phải chính bạn vừa thêm kết nối thì bấm <strong>Từ chối</strong> và báo quản trị.</li>
<li>Mức <strong>Chỉ đọc</strong>: tra cứu, không tạo / sửa gì. <strong>Được ghi</strong>: thêm soạn nháp và tạo phiếu, luôn hai bước xem
nháp rồi mới tạo ({ref(CONG_CU, "AI làm được gì")}).</li>
<li>Mỗi lượt Cho phép dùng được trong 10 phút; để lâu thì bấm Connect lại. Màn Cho phép không bao giờ nằm trong khung của trang khác.</li>
</ul>

<h2>Sau khi Cho phép</h2>
<ul>
<li>Trang cá nhân ▸ Kết nối AI riêng ▸ Khóa của bạn có thêm dòng <em>Qua ChatGPT</em> / <em>Qua Claude</em>: <strong>Gỡ</strong> là cắt ngay,
<strong>tạm tắt</strong> thì dừng tới khi bật lại.</li>
<li>Kết nối sống <strong>90 ngày</strong>; hết hạn thì bấm Connect lại. Không tính vào trần 5 khóa của Cách 2.</li>
</ul>

<h2>Hỏi thử</h2>
<p>Hỏi bằng lời thường, AI tự chọn công cụ. Vài câu mẫu:</p>
<ul>
<li><em>Liệt kê các skill công ty mà bạn đọc được.</em> Ra danh sách cẩm nang là đã nối đúng.</li>
<li><em>Nguyên liệu [tên] tháng này đã giao chưa? Các đơn mua hàng có nguyên liệu này đặt bao nhiêu, đã nhận bao nhiêu, còn bao nhiêu chưa giao? Trong kho còn bao nhiêu, ở kho nào?</em></li>
<li><em>Tra dữ liệu hải quan nhập khẩu [mặt hàng] 3 tháng gần nhất: giá trung bình, nhà nhập khẩu chính, nước xuất xứ. Rồi tìm trên web giá thị trường hiện tại và so sánh.</em> Phần tìm trên web là Claude tự tìm, cần bật tìm kiếm web trong khung chat.</li>
<li>Thêm <em>Xuất ra Excel giúp tôi</em> vào cuối câu: AI trả về đường tải tệp, tải được một lần trong 15 phút. Cần mức Được ghi.</li>
</ul>
<p>AI chỉ thấy dữ liệu trong phạm vi quyền của bạn. Dữ liệu hải quan chỉ tra được, không nạp thêm qua AI: nạp vẫn ở màn nhập tệp của ERP. Danh sách đủ: {ref(CONG_CU, "AI làm được gì")}.</p>

<h2>Không nối được?</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Bấm Connect không thấy trang ERP</td><td>Trình duyệt chặn cửa sổ bật lên — cho phép rồi bấm lại; địa chỉ phải kết thúc bằng <code>/api/mcp</code>.</td></tr>
<tr><td>Đăng nhập xong về trang chủ ERP</td><td>Bấm Connect lại trong ứng dụng (lượt cũ quá 10 phút).</td></tr>
<tr><td>Ứng dụng báo <em>access_denied</em></td><td>Đã bấm Từ chối — bấm Connect lại nếu đúng là bạn muốn nối.</td></tr>
<tr><td>Vài tuần sau AI báo mất kết nối</td><td>Hết 90 ngày, bị gỡ / tạm tắt, hoặc quản trị xóa ứng dụng — xem Khóa của bạn rồi Connect lại.</td></tr>
</tbody>
</table>
<p>Lỗi khác: {ref(NHAT_KY, "bài Nhật ký và lỗi thường gặp")}. Ứng dụng không có mục Connectors: {ref(TAO_KHOA, "Cách 2")}.</p>"""

TAO_KHOA_SUMMARY = "Dành cho Claude Code, Cursor, Gemini CLI: tạo khóa Chỉ đọc / Được ghi ở Trang cá nhân, dán đoạn cấu hình, xem lại, tạm tắt, gỡ khóa"
TAO_KHOA_CONTENT = f"""<h2>Cách 2 (nâng cao): sửa tệp cấu hình bằng khóa riêng</h2>
<p>Dùng cách này khi ứng dụng AI <strong>không có mục Connectors</strong> để nối bằng đăng nhập: Claude Code, Cursor, Gemini CLI, hoặc Claude Desktop khi muốn sửa tệp cấu hình. ChatGPT, claude.ai và Claude Desktop thì nên dùng {ref(OAUTH, "Cách 1: nối bằng đăng nhập ERP")} — không phải giữ khóa.</p>
<p>Vào <strong>Trang cá nhân</strong> (bấm tên bạn góc trên phải) ▸ thanh bên trái nhóm <strong>Trợ lý AI của tôi</strong> ▸ mục <strong>Kết nối AI riêng</strong>, làm theo ba bước đánh số.</p>

<h2>Bước 1 — Chọn ứng dụng AI bạn đang dùng</h2>
<p>Ô <strong>Ứng dụng AI</strong> liệt kê: Claude Desktop · Claude Code · Cursor · Gemini CLI · claude.ai (trình duyệt) · ChatGPT. Chọn một cái, màn hiện ngay <strong>từng bước cài, tệp cần sửa, điều kiện cần có và đoạn cấu hình mẫu</strong> của đúng ứng dụng đó. Hai kiểu nối:</p>
<ul>
<li><strong>Dán khóa</strong> (Claude Desktop qua tệp cấu hình, Claude Code, Cursor, Gemini CLI): đoạn mẫu còn chỗ giữ <code>{KEY}</code>; tạo khóa ở bước 2 xong, <strong>đoạn mẫu tự điền sẵn khóa</strong> để bạn chép.</li>
<li><strong>Đăng nhập ERP</strong> (ChatGPT, claude.ai, Claude Desktop qua Connectors): không cần khóa, chỉ dán <strong>địa chỉ cổng</strong> hiện ở đây rồi bấm Cho phép trên trang ERP — xem {ref(OAUTH, "Cách 1")}.</li>
</ul>

<h2>Bước 2 — Khóa của bạn</h2>
<h3>Tạo khóa mới</h3>
<ol>
<li>Ô <strong>Tên khóa</strong>: đặt tên theo máy / ứng dụng, ví dụ <em>«Claude máy công ty»</em>, để sau này biết khóa nào ở đâu mà gỡ.</li>
<li>Ô <strong>Mức</strong>: chọn <strong>Chỉ đọc</strong> hay <strong>Được ghi</strong> (bảng dưới).</li>
<li>Bấm <strong>Tạo khóa</strong>. Khóa <code>dego_mcp_…</code> hiện ra kèm nút chép; đoạn cấu hình ở bước 1 cũng đã điền sẵn khóa này.</li>
</ol>
<table>
<thead><tr><th>Mức</th><th>AI làm được</th><th>Dùng khi</th></tr></thead>
<tbody>
<tr><td><strong>Chỉ đọc</strong> (mặc định)</td><td>Tra cứu: phiếu của bạn, nghỉ phép, danh bạ, báo cáo được giao, đọc skill, báo lỗi.</td><td>Lần đầu nối; máy dùng chung; chỉ cần hỏi đáp.</td></tr>
<tr><td><strong>Được ghi</strong></td><td>Thêm: soạn nháp phiếu (yêu cầu báo giá, mua hàng, nghỉ phép, việc dự án…), lập phiếu hỗ trợ, ghi chú. Tạo phiếu luôn <strong>hai bước</strong>: AI soạn nháp đưa bạn xem, bạn gật thì AI mới gửi lệnh tạo. Đề nghị thanh toán vẫn chỉ tạo trên web.</td><td>Bạn muốn nhờ AI lập phiếu thay vì gõ trên web.</td></tr>
</tbody>
</table>
<ul>
<li>Khóa có hạn <strong>90 ngày</strong>; hết hạn thì tạo khóa mới rồi dán lại vào ứng dụng.</li>
<li>Mỗi tài khoản tối đa <strong>5 khóa dán tay còn hiệu lực</strong> (kể cả khóa đang tắt). Đủ 5 thì nút tạo báo lỗi — gỡ bớt khóa không dùng. Kết nối qua đăng nhập không tính vào trần này.</li>
<li>Mỗi lượt AI gọi, khóa ghi <em>dùng lần cuối</em>. Nghỉ việc thì mọi khóa đóng cùng tài khoản.</li>
</ul>

<h3>Xem lại khóa</h3>
<p>Quên chưa chép, hay cần dán sang máy thứ hai? Khóa dán tay <strong>xem lại được</strong> ngay trong khối Khóa của bạn — chỉ <strong>chính chủ khóa</strong>, đăng nhập web, mới xem được; quản trị ở màn Khóa nhân sự chỉ thấy bốn ký tự cuối; qua AI không có cách nào lấy. <strong>Mỗi lần xem lại ghi một dòng nhật ký</strong> (ứng dụng <em>ERP web</em>), nên bạn tra được ai đã xem lúc nào. Không xem lại được trong bốn trường hợp: khóa tạo trước ngày 19/10/2026 (tạo khóa mới để có bản xem lại), kết nối qua đăng nhập (ứng dụng tự giữ, bạn không cần khóa), khóa phát hộ chưa bấm Nhận, khóa đã hết hạn.</p>

<h3>Tạm tắt và bật lại</h3>
<p>Mỗi khóa và mỗi kết nối qua đăng nhập có công tắc <strong>tạm tắt</strong>: trạng thái chuyển sang <em>Đang tắt</em>, AI gọi bằng nó bị từ chối ngay (nhật ký ghi <em>Khóa đang tắt</em>), nhưng khóa không mất — <strong>bật lại là chạy tiếp</strong>, không phải dán lại gì. Dùng khi đi công tác, cho mượn máy, hay muốn tạm dừng AI mà chưa muốn gỡ. Khác với <strong>Gỡ khóa</strong>: gỡ là thu hồi hẳn, muốn dùng lại phải tạo khóa mới.</p>

<h3>Nhận khóa quản trị phát hộ</h3>
<p>Người quản lý khóa có thể phát hộ khóa cho bạn (hoặc cả phòng). Bạn nhận <strong>thông báo chuông</strong> <em>«Bạn có khóa kết nối AI chờ nhận»</em>; trong màn này khối <strong>Khóa quản trị phát cho bạn, chờ nhận</strong> có nút <strong>Nhận khóa</strong>. Bấm là khóa hiện đúng một lần, y như tự tạo. ⚠️ <strong>Chưa bấm Nhận khóa thì khóa đó chưa dùng được</strong> — AI gọi bằng nó bị từ chối. Khóa phát hộ luôn ở mức <em>Chỉ đọc</em>.</p>

<h3>Gỡ khóa</h3>
<p>Mỗi khóa đang dùng có nút <strong>Gỡ khóa</strong>. Gỡ có hiệu lực <strong>tức thì</strong>: ứng dụng AI còn giữ khóa cũ sẽ bị từ chối ở lượt gọi kế tiếp. Dùng khi đổi máy, nghi lộ khóa, hoặc thôi dùng.</p>

<h3>Kết nối qua đăng nhập cũng nằm ở đây</h3>
<p>Mỗi lần bạn bấm <strong>Cho phép</strong> cho ChatGPT, claude.ai hay Claude Desktop (Connectors) là một dòng mới trong khối Khóa của bạn, tên <em>Qua ChatGPT</em>, <em>Qua Claude</em>…, cùng mức, cùng hạn 90 ngày, cùng nút gỡ và công tắc tạm tắt. Gỡ ở đây là cắt kết nối đó ngay; muốn nối lại thì bấm Cho phép lần nữa. Cách nối: {ref(OAUTH, "Cách 1")}.</p>

<h2>Bước 3 — Kiểm tra kết nối</h2>
<p>Với mỗi khóa còn hiệu lực, màn hiện <em>Đã nối, lượt thành công gần nhất lúc…</em> hoặc <em>Chưa thấy AI gọi lần nào</em>. Dán cấu hình vào ứng dụng xong, hỏi AI một câu bất kỳ về ERP rồi quay lại bấm <strong>Kiểm tra lại</strong>. Vẫn <em>chưa thấy</em> thì xem {ref(NHAT_KY, "bài lỗi thường gặp")}.</p>

<h2>Hai khối dưới cùng</h2>
<ul>
<li><strong>Skill bạn được đọc</strong>: danh sách cẩm nang công ty mà AI của bạn tra được — do quản trị gán theo phòng ban, chức vụ. Thiếu cẩm nang bạn cần thì hỏi trưởng phòng, không phải lỗi kết nối.</li>
<li><strong>20 lượt AI tra cứu gần nhất</strong>: AI của bạn vừa gọi công cụ gì, lúc nào, thành công hay bị từ chối. Thấy lượt lạ (ứng dụng bạn không dùng, giờ bạn không ngồi máy) thì <strong>gỡ khóa ngay</strong>.</li>
</ul>
<p>Nút <strong>Xem cách hoạt động</strong> góc trên mở bản demo chín chương, dữ liệu trong demo là giả.</p>

<h2>Đừng nhầm với hai mục bên cạnh</h2>
<table>
<thead><tr><th>Mục</th><th>Dùng cho</th></tr></thead>
<tbody>
<tr><td><strong>Kết nối AI riêng</strong> (bài này)</td><td>AI <em>của bạn</em> vào ERP, bằng khóa dán tay hoặc kết nối qua đăng nhập. Bạn trả tiền model.</td></tr>
<tr><td><strong>Khóa model AI</strong></td><td>Khóa Gemini / Claude để <em>bot và Trợ lý AI của công ty</em> suy nghĩ. Không liên quan tới bài này.</td></tr>
<tr><td><strong>Liên kết Telegram</strong></td><td>Nhận bản tin, nhắc việc qua bot Telegram của công ty.</td></tr>
</tbody>
</table>"""


def _apply(dry_run: bool) -> list[int]:
    from help_seed_common import HelpArticle, SessionLocal

    db = SessionLocal()
    touched: list[int] = []
    try:
        root = db.query(HelpArticle).filter(HelpArticle.parent_id.is_(None), HelpArticle.title == ROOT_TITLE).first()
        if root is None:
            print(f"Không có cây «{ROOT_TITLE}» trên hệ này — chạy seed_help_ket_noi_ai_mcp.py để dựng cả cây.")
            return []
        print(f"  cập nhật bài gốc «{ROOT_TITLE}» (id={root.id})")
        if not dry_run:
            root.summary, root.content = ROOT_SUMMARY, ROOT_CONTENT
            touched.append(root.id)
        children = (db.query(HelpArticle).filter(HelpArticle.parent_id == root.id)
                    .order_by(HelpArticle.sort_order, HelpArticle.id).all())
        firsts = []
        for new_title, summary, content in ((OAUTH, OAUTH_SUMMARY, OAUTH_CONTENT),
                                            (TAO_KHOA, TAO_KHOA_SUMMARY, TAO_KHOA_CONTENT)):
            row = next((c for c in children if c.title in (new_title, OLD_TITLES[new_title])), None)
            print(f"  {'đổi tên + ghi đè' if row else 'thêm'}: «{row.title if row else ''}» → «{new_title}»")
            if dry_run:
                continue
            if row is None:
                row = HelpArticle(parent_id=root.id, title=new_title, sort_order=0)
                db.add(row)
            row.title, row.summary, row.content = new_title, summary, content
            db.flush()
            firsts.append(row)
            touched.append(row.id)
        if not dry_run:
            rest = [c for c in children if c.id not in {r.id for r in firsts}]
            for i, row in enumerate(firsts + rest):
                row.sort_order = i
            print("  thứ tự mới: " + " · ".join(r.title for r in firsts + rest))
            #  Liên kết trong Trung tâm trợ giúp đi theo slug của TIÊU ĐỀ — đổi tên thì sửa mọi chỗ trỏ tới tên cũ.
            for new_title, old_title in OLD_TITLES.items():
                old_href, new_href = f'href="/{slugify(old_title)}"', f'href="/{slugify(new_title)}"'
                for art in db.query(HelpArticle).filter(HelpArticle.content.like(f"%{old_href}%")).all():
                    art.content = art.content.replace(old_href, new_href)
                    touched.append(art.id)
                    print(f"  sửa liên kết trong «{art.title}»")
            db.commit()
        return sorted(set(touched))
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Sắp lại cây HDSD Kết nối AI riêng: Cách 1 đăng nhập ERP, Cách 2 khóa riêng")
    p.add_argument("--dry-run", action="store_true", help="chỉ in sẽ làm gì, không ghi")
    args = p.parse_args()
    ids = _apply(args.dry_run)
    if not args.dry_run:
        reindex_articles(ids)
    print("Thử xong, chưa ghi gì." if args.dry_run else f"Xong: {len(ids)} bài.")
