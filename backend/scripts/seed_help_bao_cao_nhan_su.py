# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho nhóm báo cáo NHÂN SỰ của phân hệ Báo cáo — duoc-CR-686 (27/10/2026).

Dựng 1 thẻ phân hệ + 7 bài theo TÁC VỤ cho năm báo cáo ở menu Báo cáo ▸ nhóm «Nhân sự»:
Biến động nhân sự · Tình hình nghỉ phép · Quỹ phép năm (đã có, mở rộng) · Hợp đồng lao động ·
Hồ sơ & tài khoản còn thiếu (mới). Phần chung: ô lọc «Phòng ban» và ngăn «Danh sách» mở từ nút
«Xem danh sách» ở thẻ số / nút «Xem» ở bảng «Xem theo».

Nhãn nút và tên chỉ số chép từ màn thật (localhost:8083, 27/10/2026) và từ `meta.metrics` của năm đường
`/summary`; đổi nhãn ở màn hay ở backend thì soát lại bài tương ứng.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_bao_cao_nhan_su.py
    docker compose exec -T api python scripts/reindex_help_rag.py --purge-orphans

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (xem `help_seed_common.py`).

⚠️ Phải KHỚP với `doc/erp/hrm/05-bao-cao-nhan-su.md` (mục A1, B1, C1, C2, E1). Nội dung ở đây và ở tài liệu
đó phải khớp nhau.
"""
from help_seed_common import SessionLocal, HelpArticle, _descendants, rebuild_tree, ref, slugify

ROOT_TITLE = "Hướng dẫn sử dụng Báo cáo Nhân sự"
COMMON_TITLE = "Báo cáo Nhân sự — Lọc theo phòng ban và xem danh sách sau mỗi con số"
HEADCOUNT_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Biến động nhân sự"
LEAVE_USAGE_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Tình hình nghỉ phép"
LEAVE_BALANCE_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Quỹ phép năm"
LABOR_CONTRACT_TITLE = "Báo cáo Nhân sự — Theo dõi hợp đồng lao động sắp hết hạn"
PROFILE_GAPS_TITLE = "Báo cáo Nhân sự — Tìm hồ sơ và tài khoản còn thiếu"
ADMIN_ACCESS_TITLE = "Báo cáo Nhân sự — Dành cho quản trị: giao quyền xem báo cáo"

TREE = {
    "title": ROOT_TITLE,
    "icon": "bar-chart",
    "summary": "Năm báo cáo Nhân sự: biến động, nghỉ phép, quỹ phép, hợp đồng lao động, hồ sơ còn thiếu — lọc phòng ban và bấm ra danh sách người sau mỗi con số",
    "content": f"""<h2>Báo cáo Nhân sự dùng để làm gì</h2>
<p>Nhóm <strong>Nhân sự</strong> trong phân hệ <strong>Báo cáo</strong> giúp phòng Nhân sự và Ban Giám đốc trả lời nhanh những câu hỏi hằng tuần, hằng tháng mà không phải lọc tay từng danh sách:</p>
<table>
<thead><tr><th>Báo cáo</th><th>Trả lời câu hỏi</th><th>Bài hướng dẫn</th></tr></thead>
<tbody>
<tr><td><strong>Biến động nhân sự</strong></td><td>Công ty đang có bao nhiêu người, kỳ này vào bao nhiêu, nghỉ bao nhiêu</td><td>{ref(HEADCOUNT_TITLE, "Đọc báo cáo Biến động nhân sự")}</td></tr>
<tr><td><strong>Tình hình nghỉ phép</strong></td><td>Kỳ này nghỉ bao nhiêu ngày, ai nghỉ, đơn có được duyệt nhanh không</td><td>{ref(LEAVE_USAGE_TITLE, "Đọc báo cáo Tình hình nghỉ phép")}</td></tr>
<tr><td><strong>Quỹ phép năm</strong></td><td>Mỗi người còn bao nhiêu phép, ai chưa được cấp quỹ, ai dùng vượt</td><td>{ref(LEAVE_BALANCE_TITLE, "Đọc báo cáo Quỹ phép năm")}</td></tr>
<tr><td><strong>Hợp đồng lao động</strong></td><td>Tuần này phải xử lý hợp đồng nào, có chỗ nào đang sai luật không</td><td>{ref(LABOR_CONTRACT_TITLE, "Theo dõi hợp đồng lao động sắp hết hạn")}</td></tr>
<tr><td><strong>Hồ sơ &amp; tài khoản còn thiếu</strong></td><td>Hồ sơ của ai chưa đủ, phòng nào khai kém, tài khoản nào đang để hở</td><td>{ref(PROFILE_GAPS_TITLE, "Tìm hồ sơ và tài khoản còn thiếu")}</td></tr>
</tbody>
</table>

<h2>Mở báo cáo ở đâu</h2>
<p>Vào phân hệ <strong>Báo cáo</strong>, menu bên trái có nhóm <strong>Nhân sự</strong> với năm mục trên. Bạn chỉ thấy mục nào mình đã được giao quyền xem. Không thấy báo cáo cần dùng thì nhờ quản trị giao quyền theo bài {ref(ADMIN_ACCESS_TITLE, "Dành cho quản trị: giao quyền xem báo cáo")}.</p>

<h2>Điểm chung của cả năm báo cáo</h2>
<ul>
<li>Lọc theo <strong>Phòng ban</strong>, <strong>Công ty</strong> và kỳ báo cáo ngay trên đầu trang.</li>
<li>Bấm <strong>Xem danh sách</strong> dưới một thẻ số, hoặc nút <strong>Xem</strong> ở một dòng của bảng, để ra đúng những người hay những phiếu làm nên con số đó.</li>
<li>Mở nút <strong>Cách tính số liệu</strong> để đọc các lưu ý về cách đếm của từng báo cáo.</li>
</ul>
<p>Chi tiết ở bài {ref(COMMON_TITLE, "Lọc theo phòng ban và xem danh sách sau mỗi con số")}.</p>""",
    "children": [
        {
            "title": COMMON_TITLE,
            "icon": "pie-chart",
            "summary": "Ô lọc Phòng ban, kỳ, Công ty; nút Xem danh sách ở thẻ số và nút Xem ở bảng Xem theo mở ngăn Danh sách; bấm dòng để mở hồ sơ",
            "content": f"""<h2>Lọc báo cáo</h2>
<p>Trên đầu mỗi báo cáo Nhân sự có các ô lọc sau. Đổi ô nào thì mọi thẻ số, bảng và danh sách bên dưới tính lại theo ô đó.</p>
<table>
<thead><tr><th>Ô lọc</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Phòng ban</strong></td><td>Chỉ xem một phòng. Mặc định là <em>Tất cả phòng ban</em>. Ô này chỉ hiện với người được xem danh mục phòng ban.</td></tr>
<tr><td>Nút kỳ (ví dụ <strong>Tháng này</strong> kèm khoảng ngày)</td><td>Chọn kỳ báo cáo. Dòng <em>So với …</em> bên cạnh cho biết kỳ đang được đem ra so sánh. Báo cáo <em>Hồ sơ &amp; tài khoản còn thiếu</em> không có nút này vì nó luôn cho biết tình trạng hiện tại.</td></tr>
<tr><td><strong>Công ty</strong></td><td>Chỉ xem một pháp nhân. Mặc định là <em>Tất cả công ty</em>.</td></tr>
</tbody>
</table>
<p>Bộ lọc nằm luôn trên địa chỉ trang, nên bạn chép địa chỉ gửi đồng nghiệp thì họ mở ra đúng phòng, đúng kỳ bạn đang xem (nếu họ cũng có quyền xem).</p>
<p>Muốn biết một con số được đếm thế nào, bấm nút <strong>Cách tính số liệu</strong> (nút ghi kèm số lưu ý) để đọc giải thích của chính báo cáo đó.</p>

<h2>Xem ai đứng sau một con số</h2>
<p>Có hai cách mở danh sách:</p>
<ol>
<li>Bấm <strong>Xem danh sách</strong> ở dưới một thẻ số trên đầu trang: ra danh sách của <strong>toàn bộ báo cáo</strong> theo bộ lọc đang chọn.</li>
<li>Ở bảng <strong>Chi tiết theo …</strong> (chọn chiều xem ở ô <strong>Xem theo</strong>), bấm nút <strong>Xem</strong> ở cột <strong>Danh sách</strong> của một dòng: ra danh sách <strong>riêng dòng đó</strong>, ví dụ riêng phòng Kế toán. Dòng <em>Tổng</em> cũng có nút <strong>Xem</strong>.</li>
</ol>
<p>Ngăn <strong>Danh sách</strong> mở ra bên phải. Dòng dưới tiêu đề nhắc bạn đang xem phần nào (ví dụ <em>Phòng ban: Hành chính</em> hoặc <em>Toàn bộ báo cáo</em>) và danh sách dùng cùng bộ lọc đang xem trên trang.</p>
<ul>
<li>Ô <strong>Chỉ số</strong> ở đầu ngăn cho đổi sang chỉ số khác mà không phải đóng ngăn, ví dụ đang xem <em>Đang hiệu lực</em> thì đổi sang <em>Hết hạn trong 30 ngày</em>. Cạnh ô có số dòng tìm được.</li>
<li>Bấm vào một dòng để mở đúng hồ sơ nhân sự hay đơn nghỉ đó. Riêng báo cáo hợp đồng mở thẳng tab hợp đồng của hồ sơ.</li>
<li>Ngăn hiện tối đa <strong>500 dòng</strong>. Nhiều hơn thì có dòng vàng báo <em>Chỉ hiện 500 dòng đầu trên tổng …</em>; hãy thu hẹp bộ lọc (phòng ban, công ty, kỳ) để xem đủ.</li>
<li>Nút <strong>Cột</strong> trong ngăn cho ẩn hay hiện cột, giống mọi bảng khác.</li>
</ul>
<p>Không phải con số nào cũng có danh sách. Thẻ nào không có nút <strong>Xem danh sách</strong> (ví dụ các tỷ lệ) là số tính từ các số khác; hãy mở danh sách của số gốc.</p>

<h2>Khi con số trông lạ</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Không thấy ô <strong>Phòng ban</strong></td><td>Bạn chưa được xem danh mục phòng ban</td><td>Dùng ô <strong>Xem theo</strong> ▸ Phòng ban để dò từng dòng, hoặc nhờ quản trị cấp quyền xem phòng ban</td></tr>
<tr><td>Con số ít hơn đồng nghiệp thấy</td><td>Mỗi người chỉ thấy dữ liệu trong phạm vi mình được giao (ví dụ chỉ phòng mình)</td><td>Bình thường, không phải lỗi. Cần xem rộng hơn thì nhờ quản trị mở phạm vi</td></tr>
<tr><td>Số người trong danh sách khác số trên bảng</td><td>Bạn đang xem một chỉ số khác, hoặc danh sách bị cắt ở 500 dòng</td><td>Kiểm ô <strong>Chỉ số</strong> trong ngăn và dòng vàng báo cắt</td></tr>
<tr><td>Phòng ban của người đã chuyển phòng hiện theo phòng mới</td><td>Báo cáo lấy phòng ban theo hồ sơ hiện tại</td><td>Đọc lưu ý trong <strong>Cách tính số liệu</strong> của báo cáo</td></tr>
</tbody>
</table>""",
        },
        {
            "title": HEADCOUNT_TITLE,
            "icon": "users",
            "summary": "Định biên cuối kỳ, vào mới, nghỉ việc, tỷ lệ nghỉ việc; xem ai vào ai nghỉ; lưu ý hồ sơ thiếu ngày vào làm",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Biến động nhân sự</strong> cho biết công ty có bao nhiêu người ở đầu và cuối kỳ, trong kỳ có bao nhiêu người vào và bao nhiêu người nghỉ.</p>
<table>
<thead><tr><th>Chỉ số</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Định biên cuối kỳ</strong></td><td>Số người đang làm tại ngày cuối kỳ</td></tr>
<tr><td><strong>Vào mới</strong></td><td>Số người có ngày vào làm nằm trong kỳ</td></tr>
<tr><td><strong>Nghỉ việc</strong></td><td>Số người có ngày nghỉ việc nằm trong kỳ</td></tr>
<tr><td><strong>Tỷ lệ nghỉ việc</strong></td><td>Số người nghỉ chia cho số người bình quân trong kỳ</td></tr>
<tr><td>Định biên đầu kỳ, Thay đổi ròng</td><td>Có trong bảng bên dưới</td></tr>
</tbody>
</table>
<p>Ô <strong>Xem theo</strong> cho chia số theo Công ty, Phòng ban (mặc định), Cấp bậc, Loại hình, Giới tính, Chức vụ hoặc Thâm niên.</p>

<h2>Xem ai vào, ai nghỉ</h2>
<ol>
<li>Chọn kỳ, và nếu cần thì chọn <strong>Phòng ban</strong> hay <strong>Công ty</strong>.</li>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <em>Vào mới</em>, <em>Nghỉ việc</em> hoặc <em>Định biên cuối kỳ</em>.</li>
<li>Danh sách có mã nhân viên, họ tên, công ty, phòng ban, chức vụ, ngày vào làm, ngày nghỉ việc và trạng thái. Bấm một dòng để mở hồ sơ.</li>
</ol>
<p>Cách mở danh sách và đổi chỉ số trong ngăn xem bài {ref(COMMON_TITLE, "Lọc theo phòng ban và xem danh sách sau mỗi con số")}.</p>

<h2>Lưu ý về hồ sơ thiếu ngày</h2>
<ul>
<li>Hồ sơ đang làm mà <strong>thiếu ngày vào làm</strong> thì báo cáo tạm lấy ngày tạo hồ sơ làm ngày vào, nên số <em>Vào mới</em>, <em>Định biên</em> và nhóm <em>Thâm niên</em> có thể lệch. Khi có hồ sơ như vậy, mục <strong>Cách tính số liệu</strong> ghi rõ có bao nhiêu hồ sơ để phòng Nhân sự bổ sung.</li>
<li>Hồ sơ đánh dấu nghỉ việc mà <strong>thiếu ngày nghỉ việc</strong> thì không được đếm vào <em>Nghỉ việc</em> và cũng không được coi là đang làm. Mục <strong>Cách tính số liệu</strong> cũng báo số hồ sơ này.</li>
</ul>
<p>Muốn lấy danh sách những hồ sơ thiếu ngày vào làm để sửa: mở báo cáo {ref(PROFILE_GAPS_TITLE, "Hồ sơ và tài khoản còn thiếu")}, bấm <strong>Xem danh sách</strong> ở thẻ <em>Thiếu ngày vào làm</em>.</p>""",
        },
        {
            "title": LEAVE_USAGE_TITLE,
            "icon": "calendar",
            "summary": "Số đơn, ngày nghỉ đã duyệt, ngày không lương, đơn chờ duyệt quá 3 ngày, ngày nghỉ bình quân mỗi người; ngày nghỉ chia theo ngày thật trong kỳ",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Tình hình nghỉ phép</strong> cho biết trong kỳ nghỉ bao nhiêu, ai nghỉ và đơn có được xử lý nhanh không.</p>
<table>
<thead><tr><th>Chỉ số</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Số đơn</strong></td><td>Số đơn nghỉ có ngày bắt đầu nằm trong kỳ</td></tr>
<tr><td><strong>Ngày nghỉ đã duyệt</strong></td><td>Số ngày nghỉ của các đơn đã duyệt, chỉ tính phần ngày rơi vào kỳ</td></tr>
<tr><td><strong>Ngày đang chờ duyệt</strong></td><td>Số ngày của các đơn còn chờ duyệt, cũng chỉ tính phần trong kỳ</td></tr>
<tr><td><strong>Ngày nghỉ không lương</strong></td><td>Phần ngày nghỉ thuộc loại nghỉ không hưởng lương</td></tr>
<tr><td><strong>Đơn chờ duyệt quá 3 ngày</strong></td><td>Đơn đã nộp hơn 3 ngày mà vẫn đang chờ duyệt</td></tr>
<tr><td><strong>Số người nghỉ</strong></td><td>Số người có đơn bắt đầu trong kỳ</td></tr>
<tr><td><strong>Ngày nghỉ TB/người</strong></td><td>Ngày nghỉ đã duyệt chia cho số người nghỉ</td></tr>
<tr><td><strong>Tỷ lệ từ chối/trả về</strong>, <strong>Thời gian duyệt TB</strong></td><td>Đơn bị từ chối hay trả về chiếm bao nhiêu phần, và trung bình mất bao nhiêu giờ để duyệt</td></tr>
</tbody>
</table>
<p>Các cột mới (ngày không lương, đơn chờ quá 3 ngày, ngày nghỉ bình quân) nằm ở bảng bên dưới; nếu không thấy thì bấm <strong>Cột</strong> để bật lên. Ô <strong>Xem theo</strong> cho chia theo Loại nghỉ (mặc định), Phòng ban, Công ty, Nhân sự hoặc Trạng thái.</p>

<h2>Ngày nghỉ được chia theo ngày thật trong kỳ</h2>
<p>Đơn kéo qua hai tháng được chia đúng theo từng ngày. Ví dụ đơn nghỉ từ 28/10 đến 05/11: các ngày của tháng 10 tính vào tháng 10, các ngày của tháng 11 tính vào tháng 11. Đơn khai nhiều khoảng ngày cũng được chia theo từng khoảng.</p>
<ul>
<li>Mỗi ngày tính theo lịch làm việc của người nghỉ: ngày lễ không tính, nghỉ nửa buổi tính 0,5 ngày.</li>
<li><strong>Số đơn</strong>, số người nghỉ, tỷ lệ từ chối và thời gian duyệt vẫn đếm theo <strong>ngày bắt đầu</strong> của đơn. Vì vậy một đơn vắt qua kỳ chỉ đếm một lần, ở kỳ có ngày bắt đầu.</li>
<li>Vì hai cách đếm khác nhau, <em>Ngày nghỉ TB/người</em> chỉ là số ước lượng khi có đơn vắt qua kỳ.</li>
</ul>

<h2>Tìm đơn đang bị treo</h2>
<ol>
<li>Bấm <strong>Xem danh sách</strong> ở một thẻ số rồi đổi ô <strong>Chỉ số</strong> trong ngăn sang <em>Đơn chờ duyệt quá 3 ngày</em>.</li>
<li>Danh sách có mã đơn, người nghỉ, phòng ban, loại nghỉ chính, từ ngày, đến ngày, số ngày trong kỳ và trạng thái.</li>
<li>Bấm một dòng để mở đơn, xem đơn đang chờ ai duyệt rồi nhắc người đó.</li>
</ol>
<p>Ngăn danh sách cũng có các chỉ số <em>Số đơn</em>, <em>Ngày nghỉ đã duyệt</em> và <em>Ngày đang chờ duyệt</em>. Cách dùng ngăn xem bài {ref(COMMON_TITLE, "Lọc theo phòng ban và xem danh sách sau mỗi con số")}.</p>""",
        },
        {
            "title": LEAVE_BALANCE_TITLE,
            "icon": "wallet",
            "summary": "Lọc Trạng thái nhân sự, thẻ Chưa được cấp quỹ, tách phép cơ bản / thâm niên / chuyển năm trước / điều chỉnh, người vượt quỹ, người chưa nghỉ ngày nào",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Quỹ phép năm</strong> cho biết mỗi người được cấp bao nhiêu ngày phép, đã dùng bao nhiêu, còn bao nhiêu. Kỳ của báo cáo này là <strong>năm</strong>: mở lần đầu ở năm nay, chọn khoảng ngày nào trong năm cũng ra cùng một kết quả. Báo cáo không có biểu đồ xu hướng.</p>
<table>
<thead><tr><th>Chỉ số</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Được cấp</strong></td><td>Tổng số ngày phép được cấp trong năm. Bảng bên dưới tách thành <strong>Phép năm cơ bản</strong>, <strong>Phép thâm niên</strong>, <strong>Chuyển từ năm trước</strong> và <strong>Điều chỉnh</strong> (cộng trừ tay)</td></tr>
<tr><td><strong>Đã dùng</strong>, <strong>Đang giữ chỗ</strong>, <strong>Còn lại</strong></td><td>Đã nghỉ, đang chờ duyệt (đã trừ tạm vào quỹ), và số còn được nghỉ</td></tr>
<tr><td><strong>Tỷ lệ sử dụng</strong></td><td>Phần đã dùng so với số được cấp</td></tr>
<tr><td><strong>Chưa được cấp quỹ</strong></td><td>Số người đang làm chưa có dòng quỹ năm nay cho loại nghỉ nào tính quỹ. Số này chỉ có ở thẻ trên đầu, không chia theo dòng</td></tr>
<tr><td><strong>Phép chuyển đã hết hạn</strong></td><td>Phép mang từ năm trước sang nhưng đã quá hạn dùng</td></tr>
<tr><td><strong>Số người vượt quỹ</strong></td><td>Người có số còn lại bị âm</td></tr>
<tr><td><strong>Chưa nghỉ ngày nào</strong></td><td>Người được cấp phép mà cả năm chưa dùng ngày nào, nên nhắc nghỉ trước khi mất phép</td></tr>
</tbody>
</table>

<h2>Lọc theo trạng thái nhân sự</h2>
<p>Ngoài <strong>Phòng ban</strong> và <strong>Công ty</strong>, báo cáo này có thêm ô <strong>Trạng thái nhân sự</strong>:</p>
<ul>
<li><strong>Đang làm</strong> (mặc định): chỉ tính người còn làm, để số <em>Còn lại</em> không bị cộng thêm phép của người đã nghỉ.</li>
<li><strong>Đã nghỉ</strong>: xem phép còn tồn của người đã nghỉ việc, ví dụ để kế toán tính tiền phép chưa nghỉ.</li>
<li><strong>Tất cả nhân sự</strong>: gộp cả hai.</li>
</ul>

<h2>Tìm người chưa được cấp quỹ hoặc dùng vượt</h2>
<ol>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <em>Chưa được cấp quỹ</em> để ra danh sách người cần cấp quỹ. Cách cấp quỹ xem bài {ref("Nhân sự — Cấp và điều chỉnh quỹ phép", "Cấp và điều chỉnh quỹ phép")}.</li>
<li>Trong ngăn, đổi ô <strong>Chỉ số</strong> sang <em>Số người vượt quỹ</em>, <em>Chưa nghỉ ngày nào</em> hoặc <em>Phép chuyển đã hết hạn</em> để xem các nhóm còn lại.</li>
<li>Danh sách <em>Còn lại</em> có các cột Cơ bản, Thâm niên, Chuyển sang, Điều chỉnh, Đã dùng, Giữ chỗ và Còn lại cho từng người, từng loại nghỉ. Bấm một dòng để mở hồ sơ người đó.</li>
</ol>
<p>Nhân viên thắc mắc số phép của mình được tính thế nào thì gửi họ bài {ref("Hiểu số ngày phép còn lại", "Hiểu số ngày phép còn lại")}.</p>""",
        },
        {
            "title": LABOR_CONTRACT_TITLE,
            "icon": "file-text",
            "summary": "Báo cáo mới: HĐ đang hiệu lực, hết hạn trong 30/60/90 ngày, quá hạn vẫn đi làm, chưa có HĐ, chưa tải bản scan, đã ký 2 HĐ có thời hạn",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Hợp đồng lao động</strong> là danh sách việc phải xử lý về hợp đồng: hợp đồng nào sắp hết hạn, ai đang đi làm mà không có hợp đồng còn hiệu lực, hợp đồng nào còn thiếu giấy tờ.</p>
<p>Bốn thẻ trên đầu trang:</p>
<ul>
<li><strong>Đang hiệu lực</strong>: số hợp đồng còn hiệu lực của người còn đang làm.</li>
<li><strong>Hết hạn trong 30 ngày</strong>: hợp đồng sẽ hết hạn trong 30 ngày tới mà người đó chưa có hợp đồng nối tiếp.</li>
<li><strong>Đã quá hạn, vẫn đi làm</strong>: hợp đồng đã hết hạn nhưng người vẫn đang làm. Cần ký tiếp ngay.</li>
<li><strong>Đang làm, chưa có HĐ</strong>: người đang làm mà không có hợp đồng nào còn hiệu lực.</li>
</ul>
<p>Bảng bên dưới có thêm các cột:</p>
<table>
<thead><tr><th>Cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td>Hết hạn trong 60 ngày, Hết hạn trong 90 ngày</td><td>Cộng dồn: số 90 ngày đã gồm cả số 60 và 30 ngày</td></tr>
<tr><td>Thử việc hết trong 30 ngày</td><td>Người sắp hết thử việc, cần quyết định ký hợp đồng chính thức hay không</td></tr>
<tr><td>Đã ký, chưa tải bản scan</td><td>Hợp đồng đã ký nhưng chưa có bản scan đính kèm</td></tr>
<tr><td>Đã ký 2 HĐ có thời hạn</td><td>Người đã ký hai hợp đồng có thời hạn: lần ký sau phải là hợp đồng không xác định thời hạn</td></tr>
<tr><td>Ký mới trong kỳ, Chấm dứt trong kỳ</td><td>Số hợp đồng bắt đầu hoặc chấm dứt trong kỳ đang chọn</td></tr>
<tr><td>Người đã nghỉ, HĐ chưa chấm dứt</td><td>Người đã nghỉ việc mà hợp đồng vẫn đang để còn hạn. Cần ghi ngày chấm dứt cho hợp đồng</td></tr>
</tbody>
</table>
<p>Ô <strong>Xem theo</strong> cho chia theo Phòng ban (mặc định), Công ty hoặc Loại hợp đồng. Biểu đồ <em>Theo loại hợp đồng</em> cho thấy cơ cấu thử việc, có thời hạn, không xác định thời hạn…</p>

<h2>Lấy danh sách hợp đồng cần xử lý tuần này</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Hợp đồng lao động</strong>. Để kỳ ở tháng hiện tại.</li>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <em>Hết hạn trong 30 ngày</em>. Danh sách có mã nhân viên, họ tên, phòng ban, mã hợp đồng, loại hợp đồng, ngày bắt đầu, ngày kết thúc và số ngày còn lại.</li>
<li>Đổi ô <strong>Chỉ số</strong> trong ngăn sang <em>Đã quá hạn, vẫn đi làm</em>, <em>Thử việc hết trong 30 ngày</em> hay <em>Đã ký, chưa tải bản scan</em> để làm tiếp từng nhóm.</li>
<li>Bấm một dòng để mở thẳng tab hợp đồng trong hồ sơ người đó, gia hạn hoặc tải bản scan lên.</li>
</ol>
<p>Luật lao động buộc báo người lao động trước khi hợp đồng hết hạn ít nhất 15 ngày, vì vậy nên xem danh sách 30 ngày mỗi tuần.</p>

<h2>Lưu ý</h2>
<ul>
<li>Trạng thái hợp đồng tính tại <strong>ngày cuối kỳ</strong>, hoặc hôm nay nếu kỳ chưa kết thúc. Chọn một tháng đã qua là xem lại tình hình tại cuối tháng đó.</li>
<li><em>Đang làm, chưa có HĐ</em> tính theo tình trạng nhân sự hiện tại.</li>
<li>⚠️ Danh sách có cả <strong>Lương cơ bản</strong>, <strong>Lương đóng BHXH</strong> và <strong>Phụ cấp</strong>, giống tab hợp đồng của hồ sơ. Ai mở được báo cáo này là xem được các cột lương, nên chỉ giao báo cáo cho người được phép xem lương.</li>
</ul>""",
        },
        {
            "title": PROFILE_GAPS_TITLE,
            "icon": "database",
            "summary": "Báo cáo mới: tỷ lệ hồ sơ đủ, thiếu ngày vào làm / chức vụ / quản lý / phòng ban / giấy tờ, CCCD sắp hết hạn, tài khoản còn mở sau khi nghỉ",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Hồ sơ &amp; tài khoản còn thiếu</strong> giúp phòng Nhân sự dọn dữ liệu: hồ sơ của ai chưa đủ, phòng nào khai kém, tài khoản nào đang để hở. Báo cáo luôn cho biết <strong>tình trạng hiện tại</strong>, nên trang này không có nút chọn kỳ.</p>
<p>Bốn thẻ trên đầu trang:</p>
<ul>
<li><strong>Đang làm</strong>: số người đang làm trong phạm vi bạn xem.</li>
<li><strong>Tỷ lệ hồ sơ đủ</strong>: phần người đang làm không thiếu thông tin nào trong các mục đang được đếm cho bạn.</li>
<li><strong>Thiếu ngày vào làm</strong>: hồ sơ thiếu ngày này làm sai báo cáo Biến động nhân sự và cách tính thâm niên, nên sửa trước.</li>
<li><strong>Đã nghỉ, tài khoản còn mở</strong>: người đã nghỉ việc mà tài khoản ERP vẫn đăng nhập được. Đây là lỗ hổng bảo mật, cần khóa ngay.</li>
</ul>

<h2>Các mục được đếm</h2>
<table>
<thead><tr><th>Nhóm</th><th>Mục</th><th>Ai thấy</th></tr></thead>
<tbody>
<tr><td>Gán trong tổ chức</td><td>Thiếu ngày vào làm · Chưa gán chức vụ · Chưa gán quản lý trực tiếp · Chưa gán phòng ban</td><td>Mọi người mở được báo cáo</td></tr>
<tr><td>Giấy tờ cá nhân</td><td>Thiếu ngày sinh · Thiếu số CCCD · Thiếu mã số thuế · Thiếu số BHXH · Thiếu tài khoản ngân hàng · CCCD hết hạn trong 90 ngày (kể cả đã hết)</td><td>Chỉ người có quyền xem thông tin nhạy cảm của nhân sự</td></tr>
<tr><td>Tài khoản ERP</td><td>Đang làm, chưa có tài khoản đang mở · Có tài khoản, chưa có vai trò · Đã nghỉ, tài khoản còn mở</td><td>Chỉ người có quyền xem tài khoản</td></tr>
</tbody>
</table>
<p>Thiếu quyền thì nhóm đó không hiện, và mục <strong>Cách tính số liệu</strong> ghi rõ vì sao. Báo cáo chỉ đếm và nêu tên người, không bao giờ hiện số CCCD hay số tài khoản.</p>
<p>Lưu ý: <em>Tỷ lệ hồ sơ đủ</em> chỉ xét các mục bạn đang thấy, không xét tài khoản và CCCD sắp hết hạn. Hai người có quyền khác nhau có thể thấy hai tỷ lệ khác nhau. <em>Đang làm, chưa có tài khoản đang mở</em> tính cả người có tài khoản nhưng tài khoản đã bị khóa.</p>

<h2>Dọn hồ sơ theo từng phòng</h2>
<ol>
<li>Để ô <strong>Xem theo</strong> ở Phòng ban (mặc định). Dòng nào nhiều số thiếu là phòng cần nhắc trước.</li>
<li>Bấm nút <strong>Xem</strong> ở dòng của phòng đó, rồi chọn mục thiếu ở ô <strong>Chỉ số</strong> trong ngăn, ví dụ <em>Thiếu số BHXH</em>.</li>
<li>Danh sách có mã nhân viên, họ tên, công ty, phòng ban, chức vụ và ngày vào làm. Bấm một dòng để mở hồ sơ và bổ sung.</li>
<li>Sửa xong, bấm <strong>Tải lại dữ liệu</strong> để thấy số giảm.</li>
</ol>
<p>Với người đã nghỉ mà tài khoản còn mở, mở hồ sơ rồi khóa tài khoản theo bài {ref("Nhân sự — Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo", "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}.</p>""",
        },
        {
            "title": ADMIN_ACCESS_TITLE,
            "icon": "shield-check",
            "summary": "Hai báo cáo mới chỉ admin thấy; giao cho trưởng phòng Nhân sự, Ban Giám đốc ở Phân quyền tài khoản ▸ tab Báo cáo; quyền phân hệ gốc vẫn cần",
            "content": f"""<h2>Ai xem được báo cáo nào</h2>
<p>Muốn mở một báo cáo Nhân sự, người dùng cần đủ <strong>hai lớp quyền</strong>:</p>
<ol>
<li><strong>Được giao xem báo cáo đó</strong> ở tab <strong>Báo cáo</strong> của màn Phân quyền tài khoản. Báo cáo chưa giao cho ai thì không ai mở được trong phân hệ Báo cáo.</li>
<li><strong>Có quyền xem ở phân hệ gốc</strong>, và số liệu chỉ gồm phần người đó được xem:</li>
</ol>
<table>
<thead><tr><th>Báo cáo</th><th>Quyền ở phân hệ gốc</th></tr></thead>
<tbody>
<tr><td>Biến động nhân sự · Hồ sơ &amp; tài khoản còn thiếu</td><td>Xem hồ sơ nhân sự</td></tr>
<tr><td>Tình hình nghỉ phép</td><td>Xem đơn nghỉ phép</td></tr>
<tr><td>Quỹ phép năm</td><td>Xem quỹ phép năm</td></tr>
<tr><td>Hợp đồng lao động</td><td>Xem hợp đồng lao động (người có quyền này xem được cả các cột lương)</td></tr>
</tbody>
</table>
<p>Nút <strong>Xuất Excel</strong> trên báo cáo cần thêm quyền xuất của phân hệ gốc. Báo cáo <em>Hồ sơ &amp; tài khoản còn thiếu</em> hiện thêm nhóm giấy tờ cá nhân với người có quyền xem thông tin nhạy cảm, và nhóm tài khoản với người có quyền xem tài khoản.</p>

<h2>Giao hai báo cáo mới cho trưởng phòng Nhân sự và Ban Giám đốc</h2>
<p>Hai báo cáo <strong>Hợp đồng lao động</strong> và <strong>Hồ sơ &amp; tài khoản còn thiếu</strong> lúc mới lên <strong>chỉ quản trị hệ thống thấy</strong>. Quản trị giao cho người cần dùng như sau:</p>
<ol>
<li>Vào màn <strong>Phân quyền tài khoản</strong>, chọn tab <strong>Báo cáo</strong>. Bảng liệt kê mọi báo cáo theo phân hệ, kèm cột <strong>Được xem</strong> và <strong>Bị cấm</strong>.</li>
<li>Ở dòng <em>Hợp đồng lao động</em>, bấm nút bút chì ở cột <strong>Sửa</strong>. Hộp <strong>Quyền xem «Hợp đồng lao động»</strong> mở ra.</li>
<li>Ở ô <strong>Thêm người · phòng ban · pháp nhân · vai trò</strong>, chọn người (ví dụ trưởng phòng Nhân sự) hoặc vai trò (ví dụ Ban Giám đốc).</li>
<li>Để <strong>Chiều tác động</strong> là <strong>Cho phép</strong>. Ghi <strong>Lý do</strong> nếu muốn (không bắt buộc).</li>
<li>Bấm <strong>Thêm</strong>, rồi <strong>Đóng</strong>. Làm lại cho dòng <em>Hồ sơ &amp; tài khoản còn thiếu</em>.</li>
</ol>
<p>Muốn chặn riêng một người dù vai trò của họ được xem, thêm người đó với chiều <strong>Cấm</strong>: cấm luôn thắng cho phép. Người được giao tải lại trang (hoặc đăng nhập lại) thì menu hiện báo cáo mới.</p>
<p>⚠️ Báo cáo Hợp đồng lao động có cột lương. Chỉ giao cho người được phép xem lương.</p>
<p>Quyền ở tab này chỉ quyết định ai mở được trang báo cáo trong phân hệ Báo cáo. Màn danh sách gốc ở từng phân hệ (hồ sơ nhân sự, đơn nghỉ…) vẫn theo quyền vai trò như cũ.</p>""",
        },
    ],
}

EXPECTED_ARTICLES = 8


def check_unique_titles() -> None:
    """Slug trùng bài khác (ngoài cây này) là liên kết chéo nhảy nhầm trên portal — chặn trước khi ghi."""
    titles = [TREE["title"]] + [c["title"] for c in TREE["children"]]
    assert len(titles) == EXPECTED_ARTICLES, titles
    slugs = {slugify(t): t for t in titles}
    assert len(slugs) == len(titles), "Hai bài trong cây trùng slug"
    db = SessionLocal()
    try:
        own = (db.query(HelpArticle.id)
               .filter(HelpArticle.title == ROOT_TITLE, HelpArticle.parent_id.is_(None)).first())
        own_ids = {nid for nid, _ in _descendants(db, own[0])} if own else set()
        clash = [a.title for a in db.query(HelpArticle.id, HelpArticle.title).all()
                 if a.id not in own_ids and slugify(a.title) in slugs]
    finally:
        db.close()
    if clash:
        raise SystemExit(f"Tiêu đề đã có bài khác dùng, đổi tiêu đề trước: {clash}")


if __name__ == "__main__":
    check_unique_titles()
    rebuild_tree(TREE)
