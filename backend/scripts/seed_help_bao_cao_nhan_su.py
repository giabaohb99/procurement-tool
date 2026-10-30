# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho nhóm báo cáo NHÂN SỰ của phân hệ Báo cáo — duoc-CR-686, mở rộng duoc-CR-687,
duoc-CR-688 (27/10/2026), duoc-CR-689 (28/10/2026); duoc-CR-692 (29/10/2026) bỏ hẳn phần kế hoạch.

Dựng 1 thẻ phân hệ + 19 bài theo TÁC VỤ cho mười lăm báo cáo ở menu Báo cáo ▸ nhóm "Nhân sự":
Biến động nhân sự · Tình hình nghỉ phép · Quỹ phép năm (đã có, mở rộng) · Hợp đồng lao động ·
Hồ sơ & tài khoản còn thiếu (CR-686) · Sổ quản lý lao động · Báo cáo sử dụng lao động (01/PLI) (CR-687) ·
Quỹ lương theo pháp nhân · Phúc lợi & sự kiện · Cơ cấu quản lý · Điều chuyển & bổ nhiệm (CR-688) ·
Có mặt theo ngày · Yêu cầu sửa hồ sơ · Sử dụng phòng họp · Đối tượng cần chú ý theo luật (CR-689), cộng ô
"Lịch nhắc trong tháng" ở Tổng quan Nhân sự (CR-689).
Phần chung: ô lọc "Phòng ban" và ngăn "Danh sách" mở từ nút "Xem danh sách" ở thẻ số / nút "Xem" ở
bảng "Xem theo"; biểu đồ linh hoạt ("Vẽ theo", kiểu, Top N, Tải ảnh PNG — CR-688, mọi báo cáo dùng
khung chung). CR-687 thêm 4 chiều cơ cấu vào Biến động nhân sự (Nhóm tuổi · Trình độ · Địa điểm làm
việc · Nhóm vị trí việc làm) và khóa 19/20 vào bài giao quyền; CR-688 thêm khóa 21–24; CR-689 thêm
khóa 26–29.

CR-689: nhãn chép từ màn local 28/10/2026 (`/report/attendance`, Tổng quan Nhân sự, Phân quyền tài khoản) và từ
`meta` / `notes` của các đường `/summary` mới.

Lịch sử: CR-689 / CR-690 từng có màn lập kế hoạch nhân sự theo kỳ, báo cáo khóa 25 so số người kế hoạch với thực tế
và phần so kế hoạch ở Quỹ lương. duoc-CR-692 (29/10/2026) đại ca bỏ hẳn tính năng đó: xóa hai bài, bỏ khóa quyền và
báo cáo khóa 25 khỏi bài giao quyền; bài Quỹ lương viết lại chỉ còn lương cơ bản + phụ cấp trên HĐLĐ đang hiệu lực,
có ghi chú số người đang làm chưa có HĐ. Nhãn A5 đối chiếu bằng đọc mã `labor_contract/payroll_report_service.py`,
`payroll_report_no_contract.py`, `payroll_report_controller.py` và `report/pages/payroll-fund-report-page.tsx`.

duoc-CR-693 (29/10/2026): Quỹ lương đổi nguồn sang ô Lương + Phụ cấp nhập ở hồ sơ nhân sự (tab Chung ▸ mục Công
việc ▸ nhóm Lương), không đọc hợp đồng nữa; số hiện tại, không xu hướng / so kỳ; chỉ TỔNG, danh sách bấm số không có
tiền; gác `employee.read|export` + khóa 21. Viết lại bài PAYROLL_TITLE và các dòng Quỹ lương ở bài giao quyền. Nhãn
đối chiếu bằng đọc `labor_contract/payroll_report_service.py`, `payroll_report_data.py`, `payroll_report_controller.py`,
`report/pages/payroll-fund-report-page.tsx`, `payroll-fund-missing-salary-notice.tsx` và ảnh
`plans/reports/screenshots-cr693/07-*.png`. Bài nhập lương ở hồ sơ nằm ở `seed_help_nhan_su.py`.

Nhãn nút và tên chỉ số chép từ mã màn (`frontend-v2/src/modules/report/`) và từ `meta.metrics` /
`meta.dimensions` / `notes` của các đường `/summary` gọi trên local (27/10/2026); đổi nhãn ở màn hay ở
backend thì soát lại bài tương ứng. Nhãn tiêu đề cột của tệp 01/PLI chưa đối chiếu được từng chữ với bản
mẫu chính thức (xem báo cáo phase 07 của CR-687): bài dặn Nhân sự so lại trước khi nộp. Bài biểu đồ linh
hoạt viết khi màn còn đang hoàn thiện (CR-688): soát lại nhãn trên màn thật trước đợt lên dev.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_bao_cao_nhan_su.py
    docker compose exec -T api python scripts/reindex_help_rag.py --purge-orphans

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (xem `help_seed_common.py`).

⚠️ Phải KHỚP với `doc/erp/hrm/05-bao-cao-nhan-su.md` (mục A1–A5, B1–B4, C1–C3, D1, E1–E3, F1, H1, §3.4).
Nội dung ở đây và ở tài liệu đó phải khớp nhau.
"""
from help_seed_common import SessionLocal, HelpArticle, _descendants, rebuild_tree, ref, slugify

ROOT_TITLE = "Hướng dẫn sử dụng Báo cáo Nhân sự"
COMMON_TITLE = "Báo cáo Nhân sự — Lọc theo phòng ban và xem danh sách sau mỗi con số"
HEADCOUNT_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Biến động nhân sự"
LEAVE_USAGE_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Tình hình nghỉ phép"
LEAVE_BALANCE_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Quỹ phép năm"
LABOR_CONTRACT_TITLE = "Báo cáo Nhân sự — Theo dõi hợp đồng lao động sắp hết hạn"
PROFILE_GAPS_TITLE = "Báo cáo Nhân sự — Tìm hồ sơ và tài khoản còn thiếu"
LABOR_BOOK_TITLE = "Báo cáo Nhân sự — Xuất Sổ quản lý lao động"
LABOR_USAGE_TITLE = "Báo cáo Nhân sự — Lập báo cáo sử dụng lao động mẫu 01/PLI nộp Sở Nội vụ"
ADMIN_ACCESS_TITLE = "Báo cáo Nhân sự — Dành cho quản trị: giao quyền xem báo cáo"
CHART_TITLE = "Báo cáo Nhân sự — Đổi kiểu biểu đồ, chọn nhóm để vẽ và tải ảnh biểu đồ"
PAYROLL_TITLE = "Báo cáo Nhân sự — Đọc báo cáo Quỹ lương theo pháp nhân"
#  Bài nhập lương ở hồ sơ thuộc cây Nhân sự — Hồ sơ và tổ chức (`seed_help_nhan_su.py`, duoc-CR-693).
SALARY_TITLE = "Nhân sự — Nhập lương ở hồ sơ và xem lương của mình"
BENEFIT_TITLE = "Báo cáo Nhân sự — Lập danh sách nhận quà và dự trù kinh phí theo dịp"
SPAN_TITLE = "Báo cáo Nhân sự — Rà cơ cấu quản lý và người chưa gán quản lý trực tiếp"
MOVES_TITLE = "Báo cáo Nhân sự — Theo dõi điều chuyển, bổ nhiệm và kiêm nhiệm"
#  duoc-CR-689. Hai bài lập kế hoạch và so số người kế hoạch đã BỎ ở duoc-CR-692 (rebuild_tree xóa cây cũ nên tự mất).
ATTENDANCE_TITLE = "Báo cáo Nhân sự — Xem số người có mặt theo ngày ở từng phòng"
PROFILE_CHANGES_TITLE = "Báo cáo Nhân sự — Theo dõi tốc độ duyệt yêu cầu sửa hồ sơ"
ROOM_USAGE_TITLE = "Báo cáo Nhân sự — Đo mức sử dụng phòng họp và giờ cao điểm"
LEGAL_WATCH_TITLE = "Báo cáo Nhân sự — Rà người sắp nghỉ hưu, đang nghỉ thai sản và nuôi con nhỏ"
REMINDERS_TITLE = "Báo cáo Nhân sự — Xem lịch nhắc sinh nhật, kỷ niệm và hợp đồng hết hạn trong tháng"
#  Bài của cây khác, dùng để nối chéo (tiêu đề phải khớp từng chữ).
REVIEW_CHANGE_TITLE = "Nhân sự — Duyệt đề nghị sửa hồ sơ của nhân viên"
ROOM_ROOT_TITLE = "Hướng dẫn sử dụng Đặt phòng họp"

TREE = {
    "title": ROOT_TITLE,
    "icon": "bar-chart",
    "summary": "Mười lăm báo cáo Nhân sự (biến động, nghỉ phép, hợp đồng, sổ lao động, quỹ lương, có mặt, sửa hồ sơ, phòng họp, đối tượng theo luật…) và ô Lịch nhắc trong tháng",
    "content": f"""<h2>Báo cáo Nhân sự dùng để làm gì</h2>
<p>Nhóm <strong>Nhân sự</strong> trong phân hệ <strong>Báo cáo</strong> giúp phòng Nhân sự và Ban Giám đốc trả lời nhanh những câu hỏi hằng tuần, hằng tháng mà không phải lọc tay từng danh sách:</p>
<table>
<thead><tr><th>Báo cáo</th><th>Trả lời câu hỏi</th><th>Bài hướng dẫn</th></tr></thead>
<tbody>
<tr><td><strong>Biến động nhân sự</strong></td><td>Công ty đang có bao nhiêu người, kỳ này vào bao nhiêu, nghỉ bao nhiêu; đội ngũ chia theo tuổi, trình độ, nơi làm việc ra sao</td><td>{ref(HEADCOUNT_TITLE, "Đọc báo cáo Biến động nhân sự")}</td></tr>
<tr><td><strong>Tình hình nghỉ phép</strong></td><td>Kỳ này nghỉ bao nhiêu ngày, ai nghỉ, đơn có được duyệt nhanh không</td><td>{ref(LEAVE_USAGE_TITLE, "Đọc báo cáo Tình hình nghỉ phép")}</td></tr>
<tr><td><strong>Quỹ phép năm</strong></td><td>Mỗi người còn bao nhiêu phép, ai chưa được cấp quỹ, ai dùng vượt</td><td>{ref(LEAVE_BALANCE_TITLE, "Đọc báo cáo Quỹ phép năm")}</td></tr>
<tr><td><strong>Hợp đồng lao động</strong></td><td>Tuần này phải xử lý hợp đồng nào, có chỗ nào đang sai luật không</td><td>{ref(LABOR_CONTRACT_TITLE, "Theo dõi hợp đồng lao động sắp hết hạn")}</td></tr>
<tr><td><strong>Hồ sơ &amp; tài khoản còn thiếu</strong></td><td>Hồ sơ của ai chưa đủ, phòng nào khai kém, tài khoản nào đang để hở</td><td>{ref(PROFILE_GAPS_TITLE, "Tìm hồ sơ và tài khoản còn thiếu")}</td></tr>
<tr><td><strong>Sổ quản lý lao động</strong></td><td>Thanh tra lao động hỏi thì đưa ngay được sổ, mỗi pháp nhân một bản</td><td>{ref(LABOR_BOOK_TITLE, "Xuất Sổ quản lý lao động")}</td></tr>
<tr><td><strong>Báo cáo sử dụng lao động (01/PLI)</strong></td><td>Lập báo cáo 6 tháng và báo cáo năm nộp Sở Nội vụ</td><td>{ref(LABOR_USAGE_TITLE, "Lập báo cáo sử dụng lao động mẫu 01/PLI")}</td></tr>
<tr><td><strong>Quỹ lương theo pháp nhân</strong></td><td>Hiện mỗi công ty, mỗi phòng đang gánh tổng bao nhiêu tiền lương mỗi tháng, theo số lương nhập ở hồ sơ từng người</td><td>{ref(PAYROLL_TITLE, "Đọc báo cáo Quỹ lương theo pháp nhân")}</td></tr>
<tr><td><strong>Phúc lợi &amp; sự kiện</strong></td><td>Dịp 8/3, 1/6, Tết… phát quà cho ai, bao nhiêu người, mỗi công ty chi bao nhiêu tiền</td><td>{ref(BENEFIT_TITLE, "Lập danh sách nhận quà và dự trù kinh phí theo dịp")}</td></tr>
<tr><td><strong>Cơ cấu quản lý</strong></td><td>Mỗi quản lý đang phụ trách bao nhiêu người, ai chưa có quản lý trực tiếp</td><td>{ref(SPAN_TITLE, "Rà cơ cấu quản lý và người chưa gán quản lý trực tiếp")}</td></tr>
<tr><td><strong>Điều chuyển &amp; bổ nhiệm</strong></td><td>Kỳ này ai chuyển phòng, ai được bổ nhiệm, kiêm nhiệm nào sắp hết</td><td>{ref(MOVES_TITLE, "Theo dõi điều chuyển, bổ nhiệm và kiêm nhiệm")}</td></tr>
<tr><td><strong>Có mặt theo ngày</strong></td><td>Hôm nay, tuần này mỗi phòng có bao nhiêu người đi làm, bao nhiêu người nghỉ</td><td>{ref(ATTENDANCE_TITLE, "Xem số người có mặt theo ngày ở từng phòng")}</td></tr>
<tr><td><strong>Yêu cầu sửa hồ sơ</strong></td><td>Phòng Nhân sự duyệt đề nghị sửa hồ sơ có kịp không, trường nào hay bị xin sửa</td><td>{ref(PROFILE_CHANGES_TITLE, "Theo dõi tốc độ duyệt yêu cầu sửa hồ sơ")}</td></tr>
<tr><td><strong>Sử dụng phòng họp</strong></td><td>Phòng họp nào quá tải, phòng nào bỏ không, giờ nào đông</td><td>{ref(ROOM_USAGE_TITLE, "Đo mức sử dụng phòng họp và giờ cao điểm")}</td></tr>
<tr><td><strong>Đối tượng cần chú ý theo luật</strong></td><td>Ai sắp đến tuổi nghỉ hưu, ai đang nghỉ thai sản, ai đang nuôi con dưới 12 tháng</td><td>{ref(LEGAL_WATCH_TITLE, "Rà người sắp nghỉ hưu, đang nghỉ thai sản và nuôi con nhỏ")}</td></tr>
</tbody>
</table>
<p>Đi cùng nhóm báo cáo này còn ô <strong>Lịch nhắc trong tháng</strong> ở trang <strong>Tổng quan</strong> của phân hệ Nhân sự: sinh nhật, kỷ niệm năm làm việc, hợp đồng và thử việc hết hạn trong tháng. Xem bài {ref(REMINDERS_TITLE, "Xem lịch nhắc sinh nhật, kỷ niệm và hợp đồng hết hạn trong tháng")}.</p>

<h2>Mở báo cáo ở đâu</h2>
<p>Vào phân hệ <strong>Báo cáo</strong>, menu bên trái có nhóm <strong>Nhân sự</strong> với mười lăm mục trên. Bạn chỉ thấy mục nào mình đã được giao quyền xem. Không thấy báo cáo cần dùng thì nhờ quản trị giao quyền theo bài {ref(ADMIN_ACCESS_TITLE, "Dành cho quản trị: giao quyền xem báo cáo")}.</p>

<h2>Điểm chung của mọi báo cáo</h2>
<ul>
<li>Lọc theo <strong>Phòng ban</strong>, <strong>Công ty</strong> và kỳ báo cáo ngay trên đầu trang.</li>
<li>Bấm <strong>Xem danh sách</strong> dưới một thẻ số, hoặc nút <strong>Xem</strong> ở một dòng của bảng, để ra đúng những người hay những phiếu làm nên con số đó.</li>
<li>Biểu đồ dưới các thẻ số đổi được: vẽ theo thời gian hay theo nhóm, kiểu đường, cột hay vành khuyên, và tải về thành ảnh.</li>
<li>Mở nút <strong>Cách tính số liệu</strong> để đọc các lưu ý về cách đếm của từng báo cáo.</li>
</ul>
<p>Chi tiết ở bài {ref(COMMON_TITLE, "Lọc theo phòng ban và xem danh sách sau mỗi con số")} và bài {ref(CHART_TITLE, "Đổi kiểu biểu đồ, chọn nhóm để vẽ và tải ảnh biểu đồ")}.</p>""",
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
<tr><td>Nút kỳ (ví dụ <strong>Tháng này</strong> kèm khoảng ngày)</td><td>Chọn kỳ báo cáo. Dòng <em>So với …</em> bên cạnh cho biết kỳ đang được đem ra so sánh. Báo cáo <em>Hồ sơ &amp; tài khoản còn thiếu</em> không có nút này vì nó luôn cho biết tình trạng hiện tại. Báo cáo <em>Phúc lợi &amp; sự kiện</em> cũng không có nút này: bạn chọn ngày ở ô <strong>Ngày dịp</strong>. Báo cáo <em>Có mặt theo ngày</em> chỉ nhận kỳ tối đa 92 ngày.</td></tr>
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
<p>Cách thứ ba: bấm thẳng vào một cột hay một lát của biểu đồ khi biểu đồ đang vẽ theo nhóm. Xem bài {ref(CHART_TITLE, "Đổi kiểu biểu đồ, chọn nhóm để vẽ và tải ảnh biểu đồ")}.</p>

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
            "title": CHART_TITLE,
            "icon": "bar-chart",
            "summary": "Biểu đồ dưới thẻ số của mọi báo cáo: bấm thẻ để đổi chỉ số, Vẽ theo thời gian hay theo nhóm, kiểu Đường / Cột / Cột ngang / Vành khuyên, Top 5–20 gộp 'Khác', bấm cột ra danh sách người, Tải ảnh PNG, gửi đường dẫn giữ nguyên biểu đồ",
            "content": f"""<h2>Biểu đồ nằm ở đâu</h2>
<p>Mọi báo cáo trong phân hệ <strong>Báo cáo</strong> (nhóm Nhân sự và các nhóm khác) có một biểu đồ ngay dưới hàng thẻ số. Mở báo cáo lần đầu, biểu đồ trông như trước:</p>
<ul>
<li>báo cáo có số theo thời gian: đường <strong>Xu hướng …</strong> của chỉ số đang chọn, kèm đường xám của kỳ đem ra so sánh;</li>
<li>báo cáo chụp tình hình tại một ngày (ví dụ <em>Cơ cấu quản lý</em>, <em>Phúc lợi &amp; sự kiện</em>, <em>Quỹ phép năm</em>): cột ngang theo nhóm đang chọn ở ô <strong>Xem theo</strong>, xếp từ lớn tới nhỏ.</li>
</ul>
<p>Muốn vẽ chỉ số khác, <strong>bấm vào thẻ số</strong> của chỉ số đó ở phía trên. Tên biểu đồ đổi theo, ví dụ <em>Vào mới theo Phòng ban</em>.</p>

<h2>Đổi cách vẽ</h2>
<p>Hàng nút trên biểu đồ có:</p>
<table>
<thead><tr><th>Nút</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Vẽ theo</strong></td><td>Chọn <strong>Thời gian</strong> (mỗi mốc của kỳ một điểm) hoặc tên chiều đang chọn ở ô <strong>Xem theo</strong> (ví dụ <em>Phòng ban</em>). Muốn vẽ theo chiều khác, đổi ô <strong>Xem theo</strong> của bảng bên dưới. Ô này chỉ hiện khi báo cáo vẽ được cả hai cách</td></tr>
<tr><td>Kiểu biểu đồ</td><td>Vẽ theo thời gian: <strong>Đường</strong> hoặc <strong>Cột</strong>. Vẽ theo nhóm: <strong>Cột ngang</strong>, <strong>Cột</strong> hoặc <strong>Vành khuyên</strong></td></tr>
<tr><td>Số nhóm hiện</td><td>Khi vẽ theo nhóm: <strong>Top 5</strong>, <strong>Top 10</strong> (mặc định), <strong>Top 20</strong> hoặc <strong>Tất cả</strong>. Các nhóm nhỏ còn lại gộp thành một cột xám <em>Khác (… nhóm)</em></td></tr>
<tr><td><strong>Tải ảnh PNG</strong></td><td>Tải biểu đồ đang xem về máy thành ảnh, có sẵn tên biểu đồ và khoảng ngày của kỳ, để dán vào báo cáo gửi Ban Giám đốc. Trên điện thoại nút chỉ còn biểu tượng</td></tr>
</tbody>
</table>
<p>Lưu ý khi chọn kiểu:</p>
<ul>
<li><strong>Vành khuyên</strong> chỉ bấm được khi có tối đa <strong>6 nhóm</strong> có số, không có số âm, và chỉ số cộng dồn được. Với tỷ lệ hay số bình quân, nút bị mờ (rê chuột lên nút để đọc lý do).</li>
<li>Chỉ số không cộng dồn được (tỷ lệ, bình quân, thấp nhất, cao nhất) thì các nhóm ngoài Top <strong>không</strong> gộp thành <em>Khác</em>; dòng dưới biểu đồ ghi <em>Còn … nhóm nhỏ hơn không vẽ</em>.</li>
<li>Nhóm bị che số (ví dụ nhóm dưới 3 người ở báo cáo quỹ lương) và nhóm bằng 0 không được vẽ. Dòng nhỏ dưới biểu đồ đếm số nhóm bị bỏ, ví dụ <em>2 nhóm bị che không vẽ.</em></li>
<li>Một số chỉ số chỉ có ở dòng Tổng (ví dụ <em>Kiêm nhiệm đang hiệu lực</em>) nên không chia theo nhóm được; biểu đồ báo rõ thay vì vẽ.</li>
</ul>

<h2>Bấm vào biểu đồ để xem danh sách người</h2>
<p>Khi biểu đồ vẽ theo nhóm và chỉ số đang vẽ có danh sách (thẻ số của nó có nút <strong>Xem danh sách</strong>), dòng dưới tên biểu đồ ghi <em>Bấm vào một nhóm trên biểu đồ để xem danh sách người của nhóm đó.</em> Bấm một cột hay một lát vành khuyên là mở ngăn <strong>Danh sách</strong> của đúng nhóm đó, giống bấm nút <strong>Xem</strong> ở dòng tương ứng của bảng. Cột <em>Khác</em> không bấm được vì gồm nhiều nhóm; muốn xem thì chọn <strong>Tất cả</strong> ở ô số nhóm.</p>
<p>Cách dùng ngăn danh sách xem bài {ref(COMMON_TITLE, "Lọc theo phòng ban và xem danh sách sau mỗi con số")}.</p>

<h2>Gửi đồng nghiệp đúng biểu đồ đang xem</h2>
<p>Chỉ số, cách vẽ, kiểu biểu đồ và số nhóm đều nằm trên địa chỉ trang, cùng với bộ lọc. Chép địa chỉ gửi đồng nghiệp thì họ mở ra đúng biểu đồ bạn đang xem (nếu họ cũng có quyền xem báo cáo đó). Đổi kiểu biểu đồ không làm báo cáo tính lại, nên đổi bao nhiêu lần cũng nhanh.</p>

<h2>Chưa làm được</h2>
<p>Biểu đồ chưa tách màu theo một chiều thứ hai (ví dụ số người theo phòng, tô màu nam / nữ), chưa có bảng nhiệt, tháp tuổi, chưa lưu riêng hay ghim biểu đồ lên Trang chủ, và tệp <strong>Xuất Excel</strong> chưa kèm biểu đồ. Cần ảnh thì dùng nút <strong>Tải ảnh PNG</strong>.</p>""",
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
<p>Ô <strong>Xem theo</strong> cho chia số theo Công ty, Phòng ban (mặc định), Cấp bậc, Loại hình, Giới tính, Chức vụ, Thâm niên, Nhóm tuổi, Trình độ, Địa điểm làm việc hoặc Nhóm vị trí việc làm. Kỳ không có ai vào, ai nghỉ thì bảng vẫn hiện định biên theo từng nhóm, riêng biểu đồ ghi <em>Kỳ này chưa có phát sinh</em>; chọn kỳ dài hơn (ví dụ <strong>Năm nay</strong>) để thấy biến động.</p>

<h2>Xem cơ cấu đội ngũ: tuổi, trình độ, nơi làm việc</h2>
<p>Bốn cách chia ở cuối ô <strong>Xem theo</strong> cho biết đội ngũ đang trông như thế nào:</p>
<table>
<thead><tr><th>Xem theo</th><th>Chia thành</th><th>Lấy từ hồ sơ</th></tr></thead>
<tbody>
<tr><td><strong>Nhóm tuổi</strong></td><td>Dưới 25 · 25–34 · 35–44 · 45–54 · 55 trở lên</td><td>Ngày sinh. Tuổi tính tại ngày cuối kỳ với <em>Định biên</em>, tại ngày vào làm với <em>Vào mới</em>, tại ngày nghỉ với <em>Nghỉ việc</em></td></tr>
<tr><td><strong>Trình độ</strong></td><td>Phổ thông · Trung cấp · Cao đẳng · Đại học · Sau đại học</td><td>Ô Trình độ học vấn</td></tr>
<tr><td><strong>Địa điểm làm việc</strong></td><td>Từng nơi làm việc khai trong hồ sơ (văn phòng, kho, xưởng…)</td><td>Ô Nơi làm việc. Chữ hoa, chữ thường và khoảng trắng thừa được coi là một</td></tr>
<tr><td><strong>Nhóm vị trí việc làm</strong></td><td>Nhà quản lý · Chuyên môn kỹ thuật bậc cao · Chuyên môn kỹ thuật bậc trung · Khác</td><td>Tự suy từ cấp bậc và trình độ, cùng cách chia với mẫu 01/PLI (xem bài {ref(LABOR_USAGE_TITLE, "Lập báo cáo sử dụng lao động mẫu 01/PLI")})</td></tr>
</tbody>
</table>
<p>Hồ sơ chưa khai ô tương ứng nằm ở dòng <em>(Chưa gắn)</em>. Dòng này lớn thì nên bổ sung hồ sơ trước khi đọc tỷ lệ.</p>
<p><strong>Che số nhóm tuổi nhỏ.</strong> Nhóm tuổi có dưới 3 người có thể làm lộ tuổi của từng người, nhất là khi lọc thêm một phòng ban. Vì vậy, với người <strong>không có quyền xem thông tin nhạy cảm của nhân sự</strong>:</p>
<ul>
<li>nhóm tuổi có 1–2 người (ở kỳ đang xem hoặc kỳ so sánh, tính cả số vào mới, nghỉ việc) hiện <strong>—</strong> thay cho số. Nếu chỉ một nhóm bị che, hệ thống che thêm nhóm nhỏ kế tiếp để không lấy Tổng trừ các nhóm khác mà ra được. Cột <strong>Danh sách</strong> của dòng đó cũng là <strong>—</strong> (không có nút <strong>Xem</strong>), và mục <strong>Cách tính số liệu</strong> có thêm lưu ý <em>Nhóm tuổi dưới 3 người được che số…</em>. Dòng <em>Tổng</em> vẫn hiện đủ. Tệp <strong>Xuất Excel</strong> để trống các ô bị che;</li>
<li>không mở được danh sách người của bất kỳ nhóm tuổi nào: bấm <strong>Xem</strong> thì ngăn báo <em>Danh sách theo nhóm tuổi cần quyền xem thông tin nhạy cảm của nhân sự</em>. Danh sách ở thẻ số trên đầu trang vẫn mở được bình thường.</li>
</ul>
<p>Người có quyền xem thông tin nhạy cảm thấy đủ số và mở được danh sách như các cách chia khác.</p>

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
<p>Báo cáo <strong>Quỹ phép năm</strong> cho biết mỗi người được cấp bao nhiêu ngày phép, đã dùng bao nhiêu, còn bao nhiêu. Kỳ của báo cáo này là <strong>năm</strong>: mở lần đầu ở năm nay, chọn khoảng ngày nào trong năm cũng ra cùng một kết quả. Báo cáo không có biểu đồ theo thời gian; biểu đồ vẽ theo nhóm đang chọn ở ô <strong>Xem theo</strong>.</p>
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
            "title": LABOR_BOOK_TITLE,
            "icon": "book-open",
            "summary": "Sổ theo luật: ai có trong sổ, bốn thẻ số, nút Xuất sổ (Excel) mỗi pháp nhân một sheet, cột Nhân sự điền tay, dòng tô vàng thiếu thông tin bắt buộc, quyền cần có",
            "content": f"""<h2>Sổ quản lý lao động là gì</h2>
<p>Luật lao động buộc mỗi đơn vị sử dụng lao động lập <strong>sổ quản lý lao động</strong> trong vòng <strong>30 ngày</strong> kể từ ngày bắt đầu hoạt động, bằng giấy hoặc bản điện tử, và đưa ra được khi thanh tra lao động hỏi. Báo cáo <strong>Sổ quản lý lao động</strong> dựng sẵn sổ đó từ hồ sơ nhân sự, hợp đồng lao động và đơn nghỉ phép: mỗi người một dòng, mỗi pháp nhân một sheet, đủ các cột luật yêu cầu.</p>

<h2>Ai có trong sổ</h2>
<p>Sổ gồm <strong>mọi người đã làm việc ở bất kỳ lúc nào trong kỳ</strong> bạn chọn, kể cả người đã nghỉ giữa kỳ. Kỳ mặc định là <strong>Năm nay</strong>.</p>
<table>
<thead><tr><th>Thẻ số</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Người trong sổ</strong></td><td>Số người làm việc ở bất kỳ lúc nào trong kỳ</td></tr>
<tr><td><strong>Đang làm cuối kỳ</strong></td><td>Số người vẫn đang làm tại ngày cuối kỳ</td></tr>
<tr><td><strong>Nghỉ việc trong kỳ</strong></td><td>Số người có ngày nghỉ việc nằm trong kỳ</td></tr>
<tr><td><strong>Thiếu thông tin bắt buộc</strong></td><td>Số người còn thiếu một trong: ngày sinh, CCCD, địa chỉ thường trú, trình độ, ngày vào làm, loại hợp đồng</td></tr>
</tbody>
</table>
<p>Người có tình trạng <em>Đã nghỉ</em> mà hồ sơ không ghi ngày nghỉ việc thì <strong>không có trong sổ</strong>, vì không biết họ nghỉ lúc nào. Hãy bổ sung ngày nghỉ việc cho các hồ sơ đó.</p>
<p>Ô <strong>Xem theo</strong> cho chia theo Công ty, Phòng ban (mặc định) hoặc Nhóm vị trí việc làm. Bấm <strong>Xem danh sách</strong> ở thẻ số, hoặc <strong>Xem</strong> ở một dòng, để ra danh sách người với mã nhân viên, họ tên, công ty, phòng ban, chức vụ, nhóm vị trí việc làm, loại hợp đồng, ngày bắt đầu và kết thúc hợp đồng, ngày vào làm, ngày nghỉ việc và cột <strong>Thiếu</strong> ghi rõ thiếu mục nào. Danh sách trên màn <strong>không hiện</strong> số CCCD, số BHXH, ngày sinh, địa chỉ hay lương; các giá trị đó chỉ có trong tệp Excel.</p>

<h2>Xuất sổ ra Excel</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Sổ quản lý lao động</strong>.</li>
<li>Chọn kỳ: để <strong>Năm nay</strong> cho sổ của năm, hoặc chọn <strong>Tùy chọn khoảng ngày</strong> rồi bấm <strong>Áp dụng</strong>. Để <em>Tất cả phòng ban</em> và <em>Tất cả công ty</em> nếu cần sổ đầy đủ; tệp xuất theo đúng bộ lọc đang chọn.</li>
<li>Bấm <strong>Xuất sổ (Excel)</strong>. Tệp tải về có <strong>mỗi pháp nhân một sheet</strong>, đầu sheet ghi tên đơn vị, mã số thuế, địa chỉ và kỳ.</li>
<li>Mở tệp, lọc các dòng <strong>tô vàng</strong> ở cột STT và Họ và tên: đó là người còn thiếu thông tin bắt buộc, cột cuối <strong>Thiếu thông tin bắt buộc</strong> ghi rõ thiếu gì. Bổ sung trong hồ sơ nhân sự rồi xuất lại.</li>
<li>Điền tay các cột hệ thống chưa có dữ liệu (bảng dưới), rồi lưu hoặc in sổ theo quy định của đơn vị.</li>
</ol>

<h2>Các cột của sổ</h2>
<table>
<thead><tr><th>Nhóm cột</th><th>Các cột</th></tr></thead>
<tbody>
<tr><td>Hệ thống điền sẵn</td><td>STT · Mã NV · Họ và tên · Giới tính · Ngày sinh · Nơi cư trú · Số CCCD · Trình độ chuyên môn · Vị trí việc làm (chức vụ) · Loại hợp đồng lao động · Thời điểm bắt đầu làm việc · Số sổ BHXH · Tiền lương (theo HĐ) · Nâng lương · Số ngày nghỉ có lương trong năm · Số ngày nghỉ không lương trong năm · Thời điểm chấm dứt HĐLĐ · Lý do chấm dứt HĐLĐ</td></tr>
<tr><td><strong>Để trống, Nhân sự điền tay</strong></td><td>Quốc tịch · Bậc trình độ kỹ năng nghề · Số giờ làm thêm · Học nghề, đào tạo, bồi dưỡng · Kỷ luật lao động, trách nhiệm vật chất · Tai nạn lao động, bệnh nghề nghiệp</td></tr>
<tr><td>Cột đánh dấu</td><td>Thiếu thông tin bắt buộc</td></tr>
</tbody>
</table>
<ul>
<li><strong>Nâng lương</strong> ghi các lần mức lương đổi giữa những hợp đồng nối tiếp, dạng <em>ngày: mức cũ → ngày: mức mới</em>. Người chỉ có một mức lương thì để trống.</li>
<li>Số ngày nghỉ có lương và không lương lấy từ các đơn nghỉ <strong>đã duyệt</strong>, chỉ tính phần ngày nằm trong kỳ.</li>
<li>Hợp đồng dùng cho mỗi người là hợp đồng đã ký còn hiệu lực tại ngày cuối kỳ (hoặc hôm nay nếu kỳ chưa hết); không có thì lấy hợp đồng bắt đầu gần nhất trước đó.</li>
</ul>

<h2>Quyền cần có</h2>
<p>Sổ chứa CCCD, số BHXH, ngày sinh, địa chỉ và lương, nên ngoài việc được giao xem báo cáo, bạn cần thêm <strong>quyền xem thông tin nhạy cảm của nhân sự</strong> và <strong>quyền xem hợp đồng lao động</strong>. Thiếu quyền nào thì trang báo rõ còn thiếu quyền đó thay vì hiện số; nhờ quản trị cấp theo bài {ref(ADMIN_ACCESS_TITLE, "Dành cho quản trị: giao quyền xem báo cáo")}. Nút <strong>Xuất sổ (Excel)</strong> cần thêm quyền xuất hồ sơ nhân sự và quyền xuất hợp đồng lao động; tệp chỉ có những người nằm trong phạm vi bạn được xuất.</p>
<p>⚠️ Tệp Excel có dữ liệu cá nhân và lương. Không gửi tệp qua nhóm chat chung, xóa bản tải về khi không còn dùng.</p>""",
        },
        {
            "title": LABOR_USAGE_TITLE,
            "icon": "clipboard-list",
            "summary": "Mẫu số 01/PLI: thẻ Tổng lao động, Nữ, Nhà quản lý, Chuyên môn kỹ thuật bậc cao; nút Xuất mẫu 01/PLI; chọn kỳ 6 tháng / năm; cột phải điền tay; nộp Sở Nội vụ trước 05/6 và 05/12",
            "content": f"""<h2>Báo cáo này dùng để làm gì</h2>
<p>Mỗi năm hai lần, mỗi pháp nhân phải nộp <strong>Báo cáo tình hình sử dụng lao động</strong> theo <strong>Mẫu số 01/PLI</strong> (Phụ lục I Nghị định 145/2020). Trong ERP, mục <strong>Báo cáo sử dụng lao động (01/PLI)</strong> tổng hợp số liệu trên màn và xuất sẵn tệp Excel đúng khung của mẫu để Nhân sự hoàn thiện rồi nộp.</p>

<h2>Đọc số trên màn</h2>
<p>Người được tính giống Sổ quản lý lao động: mọi người đã làm việc ở bất kỳ lúc nào trong kỳ. Bảng mặc định <strong>Xem theo</strong> Công ty, vì mỗi pháp nhân nộp một bản riêng; có thể đổi sang Phòng ban hoặc Nhóm vị trí việc làm.</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Tổng lao động</strong></td><td>Số người trong báo cáo</td></tr>
<tr><td><strong>Nữ</strong></td><td>Số lao động nữ</td></tr>
<tr><td><strong>Nhà quản lý</strong>, <strong>Chuyên môn kỹ thuật bậc cao</strong></td><td>Hai nhóm đầu của cột <strong>Vị trí việc làm</strong> trong mẫu</td></tr>
<tr><td>Chuyên môn kỹ thuật bậc trung, Vị trí việc làm khác</td><td>Hai nhóm còn lại, có sẵn trên bảng</td></tr>
<tr><td>HĐ không xác định thời hạn, HĐ xác định thời hạn, HĐ khác (thử việc, chưa có HĐ)</td><td>Số người theo loại hợp đồng đang áp, có sẵn trên bảng</td></tr>
</tbody>
</table>
<p><strong>Không có trong mẫu:</strong> người ký <strong>hợp đồng khoán việc</strong> hoặc <strong>cộng tác viên</strong> — đây là hợp đồng dân sự, không phải hợp đồng lao động. Mục <strong>Cách tính số liệu</strong> ghi số người bị loại để bạn xem lại; vẫn có trong Sổ quản lý lao động.</p>

<h2>Nhóm vị trí việc làm được tính thế nào</h2>
<p>Hệ thống không có ô <strong>vị trí việc làm</strong> riêng mà <strong>tự suy</strong> từ hồ sơ, theo chú thích của mẫu:</p>
<table>
<thead><tr><th>Nhóm</th><th>Điều kiện</th></tr></thead>
<tbody>
<tr><td>Nhà quản lý</td><td>Cấp bậc từ <em>Phó phòng</em> trở lên</td></tr>
<tr><td>Chuyên môn kỹ thuật bậc cao</td><td>Không phải nhà quản lý, trình độ <em>Đại học</em> hoặc <em>Sau đại học</em></td></tr>
<tr><td>Chuyên môn kỹ thuật bậc trung</td><td>Không phải nhà quản lý, trình độ <em>Trung cấp</em> hoặc <em>Cao đẳng</em></td></tr>
<tr><td>Khác</td><td>Còn lại, kể cả hồ sơ chưa khai trình độ</td></tr>
</tbody>
</table>
<p>Vì vậy hãy giữ ô <strong>Cấp bậc</strong> và <strong>Trình độ học vấn</strong> trong hồ sơ nhân sự cho đúng. Số <em>Khác</em> lớn bất thường thường là do nhiều hồ sơ chưa khai trình độ: mở báo cáo {ref(HEADCOUNT_TITLE, "Biến động nhân sự")}, chọn <strong>Xem theo</strong> ▸ Trình độ để thấy dòng <em>(Chưa gắn)</em>.</p>

<h2>Xuất mẫu 01/PLI</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Báo cáo sử dụng lao động (01/PLI)</strong>.</li>
<li>Chọn kỳ:
<ul>
<li><strong>Báo cáo năm</strong>: để <strong>Năm nay</strong> (từ 01/01 đến hôm nay).</li>
<li><strong>Báo cáo 6 tháng</strong>: bấm nút kỳ, chọn <strong>Tùy chọn khoảng ngày</strong>, chọn từ 01/01 đến 30/06 rồi bấm <strong>Áp dụng</strong>.</li>
</ul></li>
<li>Để <em>Tất cả phòng ban</em> và <em>Tất cả công ty</em> (tệp xuất theo đúng bộ lọc đang chọn), rồi bấm <strong>Xuất mẫu 01/PLI</strong>.</li>
<li>Tệp tải về có <strong>mỗi pháp nhân một sheet</strong>: phần đầu (tên doanh nghiệp, quốc hiệu, tiêu đề, <em>Kính gửi: Sở Nội vụ</em>, thông tin chung), bảng 27 cột mỗi người một dòng, dòng <em>Tổng</em>, khối ký <em>Đại diện doanh nghiệp, cơ quan, tổ chức</em> và chú thích.</li>
</ol>

<h2>Việc phải làm trước khi nộp</h2>
<ol>
<li><strong>Điền tay các cột để trống</strong> (hệ thống chưa có dữ liệu):
<ul>
<li>cột 13–15 và 17: phụ cấp chức vụ, thâm niên vượt khung, thâm niên nghề, các khoản bổ sung (hệ thống chỉ có một ô phụ cấp tổng trên hợp đồng, đã ghi vào cột 16 <strong>Phụ cấp lương</strong>);</li>
<li>cột 18–19: ngành, nghề nặng nhọc, độc hại;</li>
<li>cột 25–26: thời điểm đơn vị bắt đầu và kết thúc đóng BHXH.</li>
</ul></li>
<li>Điền phần đầu còn chấm chấm: tên Sở Nội vụ, điện thoại, email, ngành nghề kinh doanh chính.</li>
<li><strong>So phần tiêu đề bảng với mẫu chính thức</strong> đang đăng trên Cổng Dịch vụ công trước khi nộp; thấy chữ nào khác thì báo bộ phận phần mềm để sửa mẫu.</li>
<li>Người nghỉ việc trong kỳ có ghi chú <em>Nghỉ việc ngày …</em> ở cột 27; kiểm lại cho khớp.</li>
<li>Trình ký, đóng dấu.</li>
</ol>

<h2>Nộp ở đâu, hạn nào</h2>
<table>
<thead><tr><th>Báo cáo</th><th>Hạn nộp</th></tr></thead>
<tbody>
<tr><td>Báo cáo 6 tháng đầu năm</td><td>Trước ngày <strong>05/6</strong></td></tr>
<tr><td>Báo cáo năm</td><td>Trước ngày <strong>05/12</strong></td></tr>
</tbody>
</table>
<p>Nộp cho <strong>Sở Nội vụ</strong> qua <strong>Cổng Dịch vụ công quốc gia</strong>, mỗi pháp nhân một bản, rồi báo cho <strong>cơ quan bảo hiểm xã hội khu vực</strong> nơi đặt trụ sở hoặc chi nhánh.</p>

<h2>Quyền cần có</h2>
<p>Giống Sổ quản lý lao động: được giao xem báo cáo, có thêm <strong>quyền xem thông tin nhạy cảm của nhân sự</strong> và <strong>quyền xem hợp đồng lao động</strong>; xuất tệp cần thêm quyền xuất hồ sơ nhân sự và quyền xuất hợp đồng lao động. Xem bài {ref(LABOR_BOOK_TITLE, "Xuất Sổ quản lý lao động")} và {ref(ADMIN_ACCESS_TITLE, "Dành cho quản trị: giao quyền xem báo cáo")}.</p>""",
        },
        {
            "title": PAYROLL_TITLE,
            "icon": "banknote",
            "summary": "Quỹ lương = Lương + Phụ cấp nhập ở hồ sơ từng người (số hiện tại); xem theo pháp nhân, phòng ban, chức vụ, nhóm vị trí; chỉ có tổng, nhóm dưới 3 người bị che; danh sách bấm số không có tiền",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Quỹ lương theo pháp nhân</strong> cho Ban Giám đốc biết mỗi công ty, mỗi phòng đang gánh tổng bao nhiêu tiền lương mỗi tháng.</p>
<p><strong>Quỹ lương = Lương + Phụ cấp</strong> nhập ở <strong>hồ sơ nhân sự</strong> của từng người: tab <strong>Chung</strong> ▸ mục <strong>Công việc</strong> ▸ nhóm <strong>Lương</strong>. Báo cáo không đọc số lương trên hợp đồng lao động. Khi một hợp đồng lao động được đánh dấu đã ký, hệ thống tự chép lương và phụ cấp của hợp đồng đó sang hồ sơ, nên số trong báo cáo vẫn theo kịp hợp đồng mới. Cách nhập xem bài {ref(SALARY_TITLE, "Nhập lương ở hồ sơ và xem lương của mình")}.</p>
<p>⚠️ Đây là <strong>số hiện tại</strong> trên hồ sơ, không có lịch sử: báo cáo không có nút chọn kỳ, không có biểu đồ xu hướng theo tháng và không so với kỳ trước. Đây cũng là lương thỏa thuận, không phải lương thực trả: ERP không có chấm công và bảng lương, nên báo cáo không tính làm thêm giờ, thưởng hay khấu trừ. Chỉ người đang làm (chưa nghỉ việc) mới được cộng.</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Quỹ lương (lương + phụ cấp)</strong></td><td>Tổng Lương cộng Phụ cấp của mọi người trong nhóm, tính cho một tháng</td></tr>
<tr><td><strong>Lương</strong></td><td>Tổng ô Lương trên hồ sơ</td></tr>
<tr><td><strong>Phụ cấp</strong></td><td>Tổng ô Phụ cấp trên hồ sơ</td></tr>
<tr><td><strong>Số người có lương</strong></td><td>Số người đang làm đã được nhập lương hoặc phụ cấp</td></tr>
<tr><td><strong>Bình quân / người</strong></td><td>Quỹ lương chia cho số người có lương</td></tr>
</tbody>
</table>
<p>Hai ô lọc ở đầu trang là <strong>phòng ban</strong> và <strong>công ty</strong>. Ô <strong>Xem theo</strong> của bảng chia theo <strong>Pháp nhân</strong> (mặc định), <strong>Phòng ban</strong>, <strong>Chức vụ</strong> hoặc <strong>Nhóm vị trí việc làm</strong>. Dòng <em>Tổng</em> là <strong>toàn công ty trong phạm vi bạn được xem</strong>; các dòng phía trên chỉ chia nhỏ đúng số đó.</p>

<h2>Người đang làm mà chưa nhập lương</h2>
<p>Người đang làm mà chưa được nhập lương thì không có số, nên <strong>không nằm trong quỹ lương</strong>. Ngay dưới hàng thẻ số có dòng nhắc, ví dụ <em>265 người đang làm chưa nhập lương — quỹ lương chưa gồm họ.</em> Mục <strong>Cách tính số liệu</strong> cũng ghi con số này. Dòng nhắc chỉ đếm người trong phạm vi bạn được xem và không hiện khi mọi người đã có lương.</p>
<p>Muốn quỹ lương đủ, nhờ người sửa được hồ sơ nhân sự nhập lương cho những người đó (bài {ref(SALARY_TITLE, "Nhập lương ở hồ sơ và xem lương của mình")}).</p>

<h2>Chỉ có tổng, nhóm dưới 3 người bị che số</h2>
<p>Báo cáo <strong>không hiện lương của bất kỳ ai</strong>, kể cả với quản trị. Nhìn tổng của một nhóm chỉ 1–2 người là đoán ra lương từng người, vì vậy với mọi người xem:</p>
<ul>
<li>nhóm có 1–2 người có lương hiện <strong>—</strong> ở các cột tiền. Nếu chỉ một nhóm bị che, hệ thống che thêm nhóm nhỏ kế tiếp để không lấy Tổng trừ các nhóm khác mà ra được;</li>
<li>nếu cả phạm vi đang xem (dòng <em>Tổng</em>) chỉ có 1–2 người có lương thì các thẻ tiền và dòng Tổng cũng hiện <strong>—</strong>. Bỏ bớt bộ lọc phòng ban, công ty để xem;</li>
<li>khi che xong mà vẫn có thể suy ra lương từng người, bảng <strong>Xem theo</strong> bị bỏ hẳn và mục <strong>Cách tính số liệu</strong> ghi lý do, ví dụ <em>Không đủ người để xem theo Phòng ban mà không lộ thông tin từng người — bỏ bớt bộ lọc để xem</em>;</li>
<li>nhóm bị che không được vẽ trên biểu đồ.</li>
</ul>

<h2>Xem ai được tính vào quỹ lương</h2>
<p>Bấm <strong>Xem danh sách</strong> ở thẻ <strong>Số người có lương</strong>, hoặc nút <strong>Xem</strong> ở một dòng không bị che. Danh sách chỉ có <strong>Mã NV, Họ tên, Pháp nhân, Phòng ban, Chức vụ</strong>, <strong>không có cột tiền nào</strong>. Bấm một dòng để mở hồ sơ người đó. Nhóm bị che không mở được danh sách: ngăn báo <em>Nhóm dưới 3 người: không xem danh sách để tránh lộ lương từng người</em>. Các thẻ tiền không có nút <strong>Xem danh sách</strong>.</p>
<p>Nút <strong>Xuất Excel</strong> chỉ xuất bảng tổng đã che như trên màn, không có lương từng người.</p>

<h2>Ai mở được báo cáo</h2>
<ul>
<li>Cần hai thứ: được giao xem báo cáo <em>Quỹ lương theo pháp nhân</em> ở tab <strong>Báo cáo</strong> của Phân quyền tài khoản, và có <strong>quyền xem hồ sơ nhân sự</strong>. Không còn cần quyền xem hợp đồng lao động. Nút <strong>Xuất Excel</strong> cần thêm quyền xuất hồ sơ nhân sự. Xem bài {ref(ADMIN_ACCESS_TITLE, "Dành cho quản trị: giao quyền xem báo cáo")}.</li>
<li>Số liệu chỉ gồm những người nằm trong phạm vi hồ sơ nhân sự bạn được xem.</li>
<li><strong>Trợ lý AI không đọc được số lương</strong>, kể cả khi bạn có quyền xem báo cáo. Báo cáo không hiện ở trang Tổng quan của phân hệ Báo cáo.</li>
<li>Báo cáo chưa có khoản BHXH công ty phải đóng.</li>
</ul>""",
        },
        {
            "title": BENEFIT_TITLE,
            "icon": "coins",
            "summary": "Báo cáo mới: chọn dịp có sẵn (8/3, 20/10, 1/6, Trung thu, Tết, Sinh nhật tháng, Kỷ niệm năm làm việc) hoặc tự lọc, nhập mức quà nhân viên / quản lý, ra số người và tổng kinh phí từng pháp nhân, Xuất danh sách ký nhận mỗi pháp nhân một sheet",
            "content": f"""<h2>Báo cáo dùng để làm gì</h2>
<p>Báo cáo <strong>Phúc lợi &amp; sự kiện</strong> trả lời: dịp này phát quà cho ai, bao nhiêu người, ở công ty và phòng nào, tổng tiền bao nhiêu và mỗi công ty chịu bao nhiêu. Xong thì xuất luôn danh sách ký nhận.</p>
<p>Người được tính là người <strong>đang làm vào đúng ngày dịp</strong>: đã vào làm từ ngày đó trở về trước và chưa nghỉ việc, hoặc nghỉ sau ngày đó. Hồ sơ đã chuyển <em>Đã nghỉ</em> mà không ghi ngày nghỉ việc thì không được tính.</p>

<h2>Ví dụ: quà 8/3 cho chị em, nhân viên 300.000đ, quản lý 500.000đ</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Phúc lợi &amp; sự kiện</strong>.</li>
<li>Ở hàng <strong>Dịp có sẵn</strong>, bấm <strong>8/3</strong>. Hệ thống tự đặt <strong>Ngày dịp</strong> là ngày 8/3 sắp tới, <strong>Giới tính</strong> là <em>Nữ</em> và <strong>Tên dịp (tiêu đề danh sách ký nhận)</strong> là <em>Quốc tế Phụ nữ 8/3</em>. Lập muộn cho dịp đã qua thì chọn lại ngày ở ô <strong>Ngày dịp</strong>.</li>
<li>Gõ <strong>300000</strong> vào ô <strong>Mức quà nhân viên (đ)</strong> và <strong>500000</strong> vào ô <strong>Mức quà quản lý — từ Phó phòng (đ)</strong>.</li>
<li>Đọc các thẻ <strong>Số người</strong>, <strong>Tổng kinh phí</strong> và <strong>Quản lý</strong>. Bảng mặc định <strong>Xem theo</strong> <em>Pháp nhân</em>, mỗi công ty một dòng với tổng kinh phí riêng để hạch toán. Ví dụ một công ty có 20 chị em, trong đó 4 người từ Phó phòng trở lên: 16 × 300.000 + 4 × 500.000 = <strong>6.800.000đ</strong>.</li>
<li>Bấm <strong>Xuất danh sách ký nhận</strong> để tải tệp Excel (xem mục cuối bài).</li>
</ol>

<h2>Các dịp có sẵn</h2>
<p>Bấm một nút là có sẵn bộ lọc của dịp đó; bạn vẫn sửa thêm được các ô khác. Nút đang bật có nền đậm.</p>
<table>
<thead><tr><th>Nút</th><th>Ai được tính</th><th>Ngày dịp</th></tr></thead>
<tbody>
<tr><td><strong>8/3</strong>, <strong>20/10</strong></td><td>Nữ đang làm</td><td>Tự đặt ngày 8/3 hoặc 20/10 sắp tới (đúng hôm đó thì lấy hôm đó)</td></tr>
<tr><td><strong>1/6</strong></td><td>Tính theo con: con đến <strong>14 tuổi</strong></td><td>Tự đặt ngày 1/6 sắp tới</td></tr>
<tr><td><strong>Trung thu</strong></td><td>Tính theo con: con đến <strong>15 tuổi</strong></td><td>Tết Trung thu theo âm lịch, mỗi năm một ngày dương khác: <strong>tự chọn</strong> ở ô <strong>Ngày dịp</strong></td></tr>
<tr><td><strong>Tết</strong></td><td>Mọi người đang làm</td><td>Tự chọn ở ô <strong>Ngày dịp</strong></td></tr>
<tr><td><strong>Sinh nhật tháng</strong></td><td>Người sinh trong tháng của ngày dịp</td><td>Giữ ngày đang chọn. Đổi ngày sang tháng khác thì tháng sinh đổi theo</td></tr>
<tr><td><strong>Kỷ niệm năm làm việc</strong></td><td>Người vào làm cùng tháng với ngày dịp và tròn <strong>1, 3, 5 hoặc 10 năm</strong></td><td>Giữ ngày đang chọn</td></tr>
</tbody>
</table>
<p>Điều kiện do nút đặt hiện ở dải <strong>Đang lọc:</strong>, ví dụ <em>Tính theo con, con ≤ 14 tuổi</em>, <em>Sinh tháng 10</em>, <em>Tròn 1, 3, 5, 10 năm làm việc</em>. Bấm dấu ✕ để bỏ từng điều kiện, hoặc <strong>Bỏ hết điều kiện</strong> để về ban đầu. Bấm dịp khác thì điều kiện của dịp cũ được thay hết; ô tuổi, mức quà và công tắc người đang nghỉ giữ nguyên.</p>

<h2>Các ô lọc khác</h2>
<table>
<thead><tr><th>Ô</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Ngày dịp</strong></td><td>Ngày diễn ra dịp. Mở trang lần đầu là hôm nay</td></tr>
<tr><td><strong>Tên dịp (tiêu đề danh sách ký nhận)</strong></td><td>In thành tiêu đề <em>DANH SÁCH NHẬN QUÀ …</em> của tệp Excel, tối đa 100 ký tự</td></tr>
<tr><td><strong>Giới tính</strong></td><td><em>Mọi giới tính</em>, Nam hoặc Nữ</td></tr>
<tr><td><strong>Tuổi tại ngày dịp (từ – đến)</strong></td><td>Chỉ tính người trong khoảng tuổi đó. Hồ sơ chưa khai ngày sinh thì không được tính</td></tr>
<tr><td><strong>Mức quà nhân viên (đ)</strong>, <strong>Mức quà quản lý — từ Phó phòng (đ)</strong></td><td>Mức quà mỗi suất. <em>Quản lý</em> là người có cấp bậc từ Phó phòng trở lên</td></tr>
<tr><td><strong>Tính người đang nghỉ</strong></td><td>Bật sẵn: vẫn tính người có đơn nghỉ đã duyệt rơi vào ngày dịp (nghỉ dài ngày, nghỉ thai sản…). Tắt để bỏ họ ra</td></tr>
<tr><td><strong>Phòng ban</strong>, <strong>Công ty</strong></td><td>Chỉ lập cho một phòng hay một pháp nhân</td></tr>
</tbody>
</table>
<ul>
<li>Người ký <strong>hợp đồng khoán việc</strong> hoặc <strong>cộng tác viên</strong> không được tính. Màn chưa có ô để tính thêm họ.</li>
<li>Dịp tính theo con (1/6, Trung thu): thẻ <strong>Số con</strong> hiện thêm, mỗi con là một suất quà, người không có con trong độ tuổi thì không có trong danh sách. Số con lấy từ hồ sơ người thân, nên chỉ đúng khi nhân viên đã khai đủ ngày sinh của con.</li>
<li>Ô <strong>Xem theo</strong> cho chia theo Pháp nhân (mặc định), Phòng ban, Chức vụ hoặc Cấp bậc.</li>
<li>Mức quà và danh sách <strong>không được lưu</strong>. Muốn mở lại, chép địa chỉ trang: mọi ô lọc và mức quà nằm trên địa chỉ đó.</li>
</ul>

<h2>Quyền cần có để lọc theo tuổi, sinh nhật, con</h2>
<p>Lọc theo tuổi, tháng sinh và tuổi con cần <strong>quyền xem thông tin nhạy cảm của nhân sự</strong> (ngày sinh, người thân). Thiếu quyền này thì ô tuổi và ba nút <strong>1/6</strong>, <strong>Trung thu</strong>, <strong>Sinh nhật tháng</strong> bị khóa, dưới khung lọc có dòng <em>Lọc theo tuổi, tháng sinh và tuổi con cần quyền xem ngày sinh và người thân của nhân sự.</em> Mở đường dẫn người khác gửi mà có các bộ lọc đó thì trang báo <em>Bạn chưa có quyền xem ngày sinh và người thân của nhân sự…</em>; bấm <strong>Bỏ hết điều kiện</strong> để xem tiếp. Ngày sinh và người thân chỉ dùng để lọc, không in ra danh sách.</p>

<h2>Xuất danh sách ký nhận</h2>
<p>Nút <strong>Xuất danh sách ký nhận</strong> (cần quyền xuất hồ sơ nhân sự) tải về tệp Excel theo đúng bộ lọc đang chọn, <strong>mỗi pháp nhân một sheet</strong>:</p>
<ul>
<li>tên pháp nhân, tiêu đề <em>DANH SÁCH NHẬN QUÀ</em> kèm tên dịp;</li>
<li>các cột STT, Mã NV, Họ tên, Phòng ban, Chức vụ, (Số con với dịp tính theo con), Mức quà (đồng) và cột <strong>Ký nhận</strong> để trống cho người nhận ký;</li>
<li>dòng <strong>Tổng tiền</strong> của pháp nhân, khối ký <em>Người lập</em> và <em>Người duyệt</em>.</li>
</ul>
<p>Không có ai thuộc diện nhận quà thì tệp chỉ có câu <em>Không có ai thuộc diện nhận quà theo các điều kiện đã chọn.</em> Muốn phát tận phòng, chọn ô <strong>Phòng ban</strong> rồi xuất lại cho từng phòng.</p>
<p>Chưa làm: lập luôn Yêu cầu thanh toán từ tổng kinh phí, quà hiếu hỉ theo đơn nghỉ, và đăng ký người thân đi du lịch.</p>""",
        },
        {
            "title": SPAN_TITLE,
            "icon": "building",
            "summary": "Báo cáo mới: số quản lý, số cấp dưới bình quân, người chưa gán quản lý trực tiếp, quản lý chỉ 1 hoặc trên 10 cấp dưới, người nghỉ việc dưới quyền từng quản lý; Xem theo Quản lý cho mỗi quản lý một dòng",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Cơ cấu quản lý</strong> cho biết ai đang quản lý ai, dựa trên ô <strong>Quản lý trực tiếp</strong> trong hồ sơ nhân sự. Báo cáo chụp tình hình tại <strong>ngày cuối kỳ</strong> (hoặc hôm nay nếu kỳ chưa hết); kỳ chỉ dùng để đếm người nghỉ việc. Báo cáo không có xu hướng theo thời gian và không so với kỳ trước.</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Người có cấp dưới</strong></td><td>Số người đang được ít nhất một người khác ghi là quản lý trực tiếp</td></tr>
<tr><td><strong>Số cấp dưới bình quân</strong></td><td>Trung bình mỗi quản lý có bao nhiêu cấp dưới trực tiếp</td></tr>
<tr><td><strong>Chưa gán quản lý trực tiếp</strong></td><td>Người đang làm mà hồ sơ để trống ô Quản lý trực tiếp</td></tr>
<tr><td><strong>Quản lý trên 10 cấp dưới</strong></td><td>Quản lý phụ trách quá nhiều người, nên xem có cần thêm một cấp tổ trưởng không</td></tr>
<tr><td>Quản lý chỉ 1 cấp dưới</td><td>Quản lý chỉ có một người dưới quyền, nên xem có cần cấp này không</td></tr>
<tr><td>Nghỉ việc trong kỳ (theo quản lý hiện tại)</td><td>Số người nghỉ việc trong kỳ, gom theo người quản lý đang ghi trên hồ sơ của họ</td></tr>
<tr><td>Nhân sự đang làm, Tổng cấp dưới trực tiếp</td><td>Có trên bảng; cột nào chưa hiện thì bật ở nút <strong>Cột</strong></td></tr>
</tbody>
</table>
<p>Ô <strong>Xem theo</strong> cho chia theo Phòng ban (mặc định), Công ty, Cấp bậc hoặc <strong>Quản lý</strong>.</p>

<h2>Xem từng quản lý đang phụ trách bao nhiêu người</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Cơ cấu quản lý</strong>, chọn <strong>Xem theo</strong> ▸ <strong>Quản lý</strong>.</li>
<li>Mỗi quản lý một dòng: cột <strong>Nhân sự đang làm</strong> của dòng đó chính là số cấp dưới trực tiếp. Dòng <em>(Chưa gắn)</em> là những người chưa gán quản lý.</li>
<li>Biểu đồ cột ngang xếp quản lý từ nhiều cấp dưới nhất tới ít nhất; chọn <strong>Top 20</strong> hay <strong>Tất cả</strong> để xem thêm.</li>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <em>Quản lý trên 10 cấp dưới</em>, hoặc đổi ô <strong>Chỉ số</strong> trong ngăn sang <em>Quản lý chỉ 1 cấp dưới</em>: danh sách có Mã NV, Họ tên, Phòng ban, Chức vụ và <strong>Số cấp dưới</strong>.</li>
</ol>

<h2>Gán quản lý cho người còn thiếu</h2>
<p>Người chưa có quản lý trực tiếp làm hỏng các luồng duyệt đi theo quản lý (ví dụ đơn nghỉ phép không biết gửi ai duyệt), và không hiện đúng chỗ trên sơ đồ tổ chức.</p>
<ol>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <strong>Chưa gán quản lý trực tiếp</strong>. Danh sách có Mã NV, Họ tên, Phòng ban và Chức vụ.</li>
<li>Bấm một dòng để mở hồ sơ, điền ô <strong>Quản lý trực tiếp</strong> rồi lưu.</li>
<li>Quay lại báo cáo, bấm <strong>Tải lại dữ liệu</strong> để thấy số giảm.</li>
</ol>
<p>Xem lại toàn bộ cây quản lý ở bài {ref("Nhân sự — Xem Sơ đồ tổ chức", "Xem Sơ đồ tổ chức")}.</p>

<h2>Người nghỉ việc dưới quyền từng quản lý</h2>
<p>Chọn kỳ (ví dụ <strong>Năm nay</strong>), <strong>Xem theo</strong> ▸ <strong>Quản lý</strong>, rồi đọc cột <em>Nghỉ việc trong kỳ (theo quản lý hiện tại)</em>. Danh sách của chỉ số này có thêm <strong>Ngày nghỉ việc</strong> và <strong>Quản lý hiện tại</strong>. Số tính theo quản lý đang ghi trên hồ sơ người đã nghỉ, nên nếu người đó đổi quản lý ngay trước khi nghỉ thì được tính cho quản lý mới.</p>

<h2>Lưu ý</h2>
<ul>
<li>Báo cáo chỉ đếm người trong phạm vi bạn được xem. Quản lý nằm ngoài phạm vi hay ngoài bộ lọc thì không được tính vào <em>Người có cấp dưới</em>.</li>
<li>Quản lý lấy theo hồ sơ <strong>hiện tại</strong>: chọn một kỳ đã qua không cho biết ngày đó ai quản lý ai.</li>
</ul>""",
        },
        {
            "title": MOVES_TITLE,
            "icon": "workflow",
            "summary": "Báo cáo mới: số lượt điều chuyển, bổ nhiệm, kiêm nhiệm, miễn nhiệm trong kỳ theo quá trình công tác; số người có biến động; số tháng từ lúc vào làm tới lần bổ nhiệm; kiêm nhiệm đang hiệu lực và hết trong 30 ngày; Xem theo Phòng đi → Phòng đến",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Điều chuyển &amp; bổ nhiệm</strong> đếm các dòng ở tab <strong>Quá trình công tác</strong> của hồ sơ nhân sự có <em>Từ ngày</em> (ngày hiệu lực) nằm trong kỳ, kể cả dòng đã áp và dòng chưa áp vào hồ sơ. Báo cáo trả lời: người đi đâu, ai được lên, đề bạt nội bộ có nhiều không.</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Điều chuyển</strong>, <strong>Bổ nhiệm</strong></td><td>Số lượt điều chuyển, bổ nhiệm trong kỳ</td></tr>
<tr><td><strong>Số người có biến động</strong></td><td>Số người có ít nhất một dòng trong kỳ (một người chuyển hai lần vẫn đếm một)</td></tr>
<tr><td><strong>Kiêm nhiệm đang hiệu lực</strong></td><td>Số kiêm nhiệm còn hiệu lực tại cuối kỳ (hoặc hôm nay nếu kỳ chưa hết). Chỉ có ở dòng Tổng</td></tr>
<tr><td>Tuyển dụng, Kiêm nhiệm, Miễn nhiệm, Thôi việc, Sự kiện khác</td><td>Số lượt của các loại còn lại</td></tr>
<tr><td>Kiêm nhiệm hết trong 30 ngày</td><td>Kiêm nhiệm sẽ hết hạn trong 30 ngày tới, để chuẩn bị quyết định gia hạn hay thôi. Chỉ có ở dòng Tổng</td></tr>
<tr><td>Số tháng từ lúc vào làm tới lần bổ nhiệm</td><td>Trung bình một người vào làm bao lâu thì được bổ nhiệm. Bỏ qua người thiếu ngày vào làm</td></tr>
</tbody>
</table>
<p>Cột nào chưa hiện trên bảng thì bật ở nút <strong>Cột</strong>. Ô <strong>Xem theo</strong> cho chia theo <strong>Loại sự kiện</strong> (mặc định), Phòng đến, Công ty hoặc <strong>Phòng đi → Phòng đến</strong>.</p>

<h2>Xem dòng người giữa các phòng</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Điều chuyển &amp; bổ nhiệm</strong>, chọn kỳ, ví dụ <strong>Năm nay</strong>.</li>
<li>Chọn <strong>Xem theo</strong> ▸ <strong>Phòng đi → Phòng đến</strong>. Mỗi dòng là một cặp, ví dụ <em>Kinh doanh → Marketing</em>, kèm số lượt.</li>
<li>Bấm <strong>Xem</strong> ở một dòng để ra danh sách người của cặp đó.</li>
</ol>
<p><em>Phòng đi</em> lấy từ dòng quá trình công tác liền trước của cùng người. Dòng đầu tiên chưa rõ phòng đi thì hiện <em>(Chưa rõ)</em>.</p>

<h2>Danh sách và số quyết định</h2>
<p>Bấm <strong>Xem danh sách</strong> ở một thẻ số, hoặc <strong>Xem</strong> ở một dòng của bảng. Danh sách có Mã NV, Họ tên, Loại, Từ ngày, Đến ngày, Phòng đi, Phòng đến, Chức vụ và <strong>Số quyết định</strong>. Danh sách chỉ ghi số quyết định, không mở tệp quyết định; bấm một dòng để mở hồ sơ người đó rồi xem ở tab <strong>Quá trình công tác</strong>.</p>
<p>Muốn biết kiêm nhiệm nào sắp hết: bấm <strong>Xem danh sách</strong> ở thẻ <strong>Kiêm nhiệm đang hiệu lực</strong>, rồi đổi ô <strong>Chỉ số</strong> trong ngăn sang <em>Kiêm nhiệm hết trong 30 ngày</em>.</p>

<h2>Lưu ý</h2>
<ul>
<li>Bộ lọc <strong>Phòng ban</strong> và <strong>Công ty</strong> lọc theo hồ sơ <strong>hiện tại</strong> của người có dòng đó, không theo phòng đi hay phòng đến của dòng.</li>
<li>Số liệu chỉ đúng khi phòng Nhân sự ghi đủ các lần điều chuyển, bổ nhiệm vào tab <strong>Quá trình công tác</strong>.</li>
</ul>""",
        },
        {
            "title": ATTENDANCE_TITLE,
            "icon": "calendar",
            "summary": "Báo cáo mới: người-ngày phải làm theo lịch làm việc riêng (trừ ngày lễ), nghỉ theo đơn đã duyệt (nửa buổi 0,5), có mặt, tỷ lệ có mặt / vắng theo phòng; chỉ tính tới hôm nay; kỳ tối đa 92 ngày; cần quyền xem đơn nghỉ",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Có mặt theo ngày</strong> trả lời: hôm nay, tuần này mỗi phòng có bao nhiêu người đi làm. Số được tính từ <strong>lịch làm việc</strong> và <strong>đơn nghỉ phép đã duyệt</strong>, không phải từ máy chấm công: đi trễ hay vắng không phép chưa có dữ liệu nên không có trong báo cáo.</p>
<p>Đơn vị đếm là <strong>người-ngày</strong>: một người phải làm một ngày là 1 người-ngày. Ví dụ phòng có 10 người, tuần làm 5 ngày thì có 50 người-ngày phải làm.</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Người-ngày phải làm</strong></td><td>Mỗi người × mỗi ngày họ có lịch làm theo <strong>lịch làm việc riêng của họ</strong>, trừ ngày lễ, ngày chưa vào làm và ngày đã nghỉ việc. Ngày làm nửa buổi tính 0,5</td></tr>
<tr><td><strong>Người-ngày nghỉ (đã duyệt)</strong></td><td>Phần ngày phải làm bị phủ bởi đơn nghỉ đã duyệt. Nghỉ nửa buổi tính 0,5; nghỉ theo giờ tính theo tỷ lệ giờ</td></tr>
<tr><td><strong>Người-ngày có mặt</strong></td><td>Phải làm trừ nghỉ</td></tr>
<tr><td><strong>Tỷ lệ có mặt</strong></td><td>Có mặt chia cho phải làm</td></tr>
<tr><td>Tỷ lệ vắng</td><td>Nghỉ chia cho phải làm, có trên bảng</td></tr>
</tbody>
</table>
<p>Ô <strong>Xem theo</strong> cho chia theo <strong>Phòng ban</strong> (mặc định) hoặc <strong>Pháp nhân</strong>; phòng ban và pháp nhân lấy theo hồ sơ hiện tại. Biểu đồ mặc định vẽ <em>Tỷ lệ có mặt</em> theo ngày.</p>

<h2>Xem tình hình tuần này của từng phòng</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Có mặt theo ngày</strong>. Kỳ mở sẵn là <strong>Tháng này</strong>.</li>
<li>Bấm nút kỳ, chọn <strong>Hôm nay</strong>, <strong>7 ngày qua</strong>, <strong>Quý này</strong>…, hoặc <strong>Tùy chọn khoảng ngày</strong> để chọn đúng tuần cần xem rồi bấm <strong>Áp dụng</strong>.</li>
<li>Đọc bảng <strong>Chi tiết theo Phòng ban</strong>: phòng nào tỷ lệ vắng cao là phòng đang thiếu người.</li>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <strong>Người-ngày nghỉ (đã duyệt)</strong>, hoặc <strong>Xem</strong> ở dòng một phòng, để ra danh sách ai nghỉ: Mã NV, Họ tên, Phòng ban, Ngày, Loại nghỉ, Buổi. Bấm một dòng để mở hồ sơ.</li>
</ol>

<h2>Giới hạn của kỳ</h2>
<ul>
<li>Mỗi lần xem tối đa <strong>92 ngày</strong> (một quý vẫn xem được), vì mỗi người × mỗi ngày là một dòng tính. Chọn <strong>Năm nay</strong> thì trang báo <em>Báo cáo <strong>Có mặt theo ngày</strong> chỉ xem được tối đa 92 ngày một lần…</em>; chọn kỳ ngắn hơn rồi xem lại.</li>
<li>Báo cáo <strong>chỉ tính tới hết hôm nay</strong>. Kỳ kéo sang ngày chưa tới thì phần đó chưa tính, và mục <strong>Cách tính số liệu</strong> ghi rõ.</li>
<li>Vì kỳ có giới hạn nên báo cáo này không lên trang Tổng quan của phân hệ Báo cáo.</li>
</ul>

<h2>Không thấy số nghỉ</h2>
<p>Các cột nghỉ, có mặt và tỷ lệ cần thêm <strong>quyền xem đơn nghỉ phép</strong>. Thiếu quyền thì các cột đó để trống, chỉ còn <em>Người-ngày phải làm</em>, mục <strong>Cách tính số liệu</strong> báo <em>Bạn chưa có quyền xem đơn nghỉ phép…</em> và danh sách người nghỉ không mở được. Có quyền nhưng chỉ trong phạm vi hẹp (ví dụ phòng mình) thì báo cáo chỉ đếm những đơn bạn được xem.</p>
<p>Số người-ngày phải làm sai thường là do lịch làm việc của người đó chưa đúng. Xem lại lịch ở phân hệ <strong>Nhân sự</strong> ▸ <strong>Lịch làm việc</strong>.</p>""",
        },
        {
            "title": PROFILE_CHANGES_TITLE,
            "icon": "file-text",
            "summary": "Báo cáo mới: số yêu cầu sửa hồ sơ trong kỳ, đang chờ, chờ quá 2 ngày, đã duyệt, từ chối, tỷ lệ từ chối, giờ xử lý bình quân; xem theo phòng, trường bị xin sửa, trạng thái; không hiện giá trị cũ / mới",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Nhân viên tự gửi đề nghị sửa hồ sơ (số điện thoại, địa chỉ, tài khoản ngân hàng…) và phòng Nhân sự duyệt ở màn <strong>Duyệt sửa hồ sơ</strong> (bài {ref(REVIEW_CHANGE_TITLE, "Duyệt đề nghị sửa hồ sơ của nhân viên")}). Báo cáo <strong>Yêu cầu sửa hồ sơ</strong> cho biết việc duyệt đó có kịp không và trường nào hay bị xin sửa.</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Số yêu cầu</strong></td><td>Số đề nghị có <strong>ngày gửi</strong> nằm trong kỳ</td></tr>
<tr><td><strong>Đang chờ</strong></td><td>Đề nghị chưa được duyệt hay từ chối</td></tr>
<tr><td><strong>Chờ quá 2 ngày</strong></td><td>Đề nghị đã gửi hơn 2 ngày mà vẫn chờ. Số này tính tới hôm nay, không theo kỳ đang chọn</td></tr>
<tr><td><strong>Giờ xử lý bình quân</strong></td><td>Trung bình từ lúc gửi tới lúc được duyệt hay từ chối, tính bằng giờ. Không tính đề nghị bị rút lại</td></tr>
<tr><td>Đã duyệt, Từ chối, Tỷ lệ từ chối</td><td>Kết quả xử lý, có trên bảng</td></tr>
</tbody>
</table>
<p>Ô <strong>Xem theo</strong> cho chia theo <strong>Phòng ban</strong> (mặc định), <strong>Công ty</strong>, <strong>Trường bị xin sửa</strong> hoặc <strong>Trạng thái</strong> (Chờ duyệt, Đã duyệt, Từ chối, Đã rút lại).</p>

<h2>Tìm đề nghị đang bị treo</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Yêu cầu sửa hồ sơ</strong>.</li>
<li>Bấm <strong>Xem danh sách</strong> ở thẻ <strong>Chờ quá 2 ngày</strong>. Danh sách có Mã NV, Họ tên, Phòng ban, Ngày gửi, Trạng thái, Số trường, Người duyệt và Ngày duyệt.</li>
<li>Bấm một dòng để mở hồ sơ người đó, rồi sang màn <strong>Duyệt sửa hồ sơ</strong> để xử lý.</li>
</ol>
<p>Trong ngăn, đổi ô <strong>Chỉ số</strong> sang <em>Đang chờ</em>, <em>Đã duyệt</em> hay <em>Từ chối</em> để xem các nhóm còn lại.</p>

<h2>Trường nào hay bị xin sửa</h2>
<p>Chọn <strong>Xem theo</strong> ▸ <strong>Trường bị xin sửa</strong>. Mỗi dòng là một trường của hồ sơ (ví dụ <em>Tình trạng hôn nhân</em>). Một đề nghị xin sửa nhiều trường được đếm ở nhiều dòng, nên cộng các dòng có thể lớn hơn tổng số yêu cầu. Trường nào bị xin sửa nhiều thường là trường khai sai ngay từ đầu: nên nhắc khi nhận hồ sơ người mới.</p>

<h2>Bảo mật</h2>
<p>Báo cáo và danh sách <strong>không bao giờ hiện giá trị cũ hay giá trị mới</strong> của trường được xin sửa (có thể là số CCCD, tài khoản ngân hàng), chỉ đếm và nêu số trường. Muốn xem nội dung, mở đề nghị ở màn <strong>Duyệt sửa hồ sơ</strong> với quyền của bạn.</p>""",
        },
        {
            "title": ROOM_USAGE_TITLE,
            "icon": "building",
            "summary": "Báo cáo mới: lượt đặt, giờ đã đặt, tỷ lệ lấp đầy so với giờ làm việc, tỷ lệ hủy / từ chối, người dự bình quân, % sức chứa; xem theo phòng họp, pháp nhân, phòng ban đặt, khung giờ, thứ trong tuần",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Sử dụng phòng họp</strong> trả lời: phòng nào quá tải, phòng nào bỏ không, giờ nào đông. Số lấy từ các phiếu đặt phòng ở phân hệ <strong>Nhân sự</strong> ▸ <strong>Đặt phòng họp</strong> (bài {ref(ROOM_ROOT_TITLE, "Hướng dẫn sử dụng Đặt phòng họp")}).</p>
<table>
<thead><tr><th>Thẻ số / cột</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Lượt đặt</strong></td><td>Số phiếu <strong>đã duyệt</strong>, tính vào ngày bắt đầu của phiếu</td></tr>
<tr><td><strong>Giờ đã đặt</strong></td><td>Tổng số giờ của các phiếu đã duyệt</td></tr>
<tr><td><strong>Tỷ lệ lấp đầy</strong></td><td>Giờ đã đặt chia cho giờ làm việc của phòng. Họp ngoài giờ vẫn tính vào giờ đã đặt nên tỷ lệ có thể vượt 100%</td></tr>
<tr><td><strong>Tỷ lệ hủy / từ chối</strong></td><td>Phần phiếu đã hủy hoặc bị từ chối trong các phiếu đã chốt</td></tr>
<tr><td>Đặt rồi hủy / bị từ chối</td><td>Số phiếu đã hủy hoặc bị từ chối</td></tr>
<tr><td>Người dự bình quân</td><td>Trung bình mỗi cuộc họp có bao nhiêu người dự</td></tr>
<tr><td>% sức chứa</td><td>Số người dự so với sức chứa của phòng (chỉ tính phòng đã khai sức chứa). Thấp là đang đặt phòng to cho cuộc họp nhỏ</td></tr>
</tbody>
</table>
<p>Phiếu nháp, chờ duyệt hay bị trả về chưa được tính. <strong>Giờ làm việc</strong> của phòng là giờ công theo lịch làm việc chung của hệ thống mỗi ngày, trừ nghỉ trưa và ngày lễ của pháp nhân sở hữu phòng.</p>

<h2>Tìm phòng quá tải và giờ cao điểm</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Sử dụng phòng họp</strong>. Kỳ mở sẵn là <strong>Tháng này</strong>, bảng mặc định <strong>Xem theo</strong> <em>Phòng họp</em>.</li>
<li>Đọc cột <strong>Tỷ lệ lấp đầy</strong>: phòng gần hoặc trên 100% là phòng quá tải, phòng rất thấp là phòng ít dùng.</li>
<li>Chọn <strong>Xem theo</strong> ▸ <strong>Khung giờ</strong> (8h, 9h… tới 23h; một lượt đặt kéo dài nhiều giờ được chia giờ cho từng khung nó phủ) hoặc <strong>Thứ trong tuần</strong> để thấy giờ và ngày đông nhất.</li>
<li>Chọn <strong>Xem theo</strong> ▸ <strong>Phòng ban đặt</strong> để biết phòng ban nào đặt nhiều, hoặc <strong>Pháp nhân sở hữu phòng</strong> để so giữa các công ty.</li>
</ol>
<p>Xem theo <em>Phòng ban đặt</em>, hoặc lọc ô <strong>Phòng ban</strong>, thì không có giờ làm việc nên <strong>Tỷ lệ lấp đầy</strong> để trống. Ô <strong>Phòng ban</strong> lọc theo phòng ban của <strong>người đặt</strong>.</p>

<h2>Xem các phiếu đặt</h2>
<p>Bấm <strong>Xem danh sách</strong> ở thẻ <strong>Lượt đặt</strong> hoặc <strong>Giờ đã đặt</strong>, hoặc <strong>Xem</strong> ở một dòng. Danh sách có Mã phiếu, Phòng, Tiêu đề, Người đặt, Phòng ban, Bắt đầu, Kết thúc, Số người và Trạng thái. Đổi ô <strong>Chỉ số</strong> sang <em>Đặt rồi hủy / bị từ chối</em> để xem các phiếu bị hủy. Bấm một dòng để mở phiếu.</p>
<p>Bạn chỉ thấy các phiếu nằm trong phạm vi xem phiếu đặt phòng của mình, còn giờ làm việc vẫn tính cho mọi phòng; nên người có phạm vi hẹp sẽ thấy tỷ lệ lấp đầy thấp hơn thực tế.</p>""",
        },
        {
            "title": LEGAL_WATCH_TITLE,
            "icon": "shield-check",
            "summary": "Báo cáo mới: người đến tuổi nghỉ hưu trong 12 tháng theo lộ trình Nghị định 135/2020 và người đã quá tuổi vẫn đang làm, đang nghỉ thai sản và ngày đi làm lại, lao động nữ nuôi con dưới 12 tháng; cần quyền xem thông tin nhạy cảm; không in ngày sinh",
            "content": f"""<h2>Báo cáo cho biết gì</h2>
<p>Báo cáo <strong>Đối tượng cần chú ý theo luật</strong> liệt kê những người đang được hưởng, hoặc sắp phải xử lý, chế độ riêng theo luật lao động. Tình trạng tính tại <strong>ngày cuối kỳ</strong> hoặc <strong>hôm nay</strong>, lấy ngày sớm hơn; báo cáo không có xu hướng theo thời gian.</p>
<table>
<thead><tr><th>Thẻ số</th><th>Ai được tính</th><th>Cột <strong>Mốc</strong> trong danh sách</th></tr></thead>
<tbody>
<tr><td><strong>Đến tuổi nghỉ hưu trong 12 tháng</strong></td><td>Người sẽ tới thời điểm nghỉ hưu trong 12 tháng tới</td><td>Thời điểm nghỉ hưu</td></tr>
<tr><td><strong>Đã quá tuổi nghỉ hưu, vẫn đang làm</strong></td><td>Người đã qua thời điểm nghỉ hưu mà vẫn đang làm (cần làm hợp đồng mới hoặc chốt nghỉ)</td><td>Thời điểm nghỉ hưu</td></tr>
<tr><td><strong>Đang nghỉ thai sản</strong></td><td>Người có đơn <em>Nghỉ thai sản</em> đã duyệt phủ ngày đang xét, <strong>hoặc</strong> hồ sơ nhân sự đang ở trạng thái <em>Nghỉ thai sản</em> (mỗi người chỉ đếm một lần)</td><td>Ngày đi làm lại (để trống nếu người đó không có đơn)</td></tr>
<tr><td><strong>Lao động nữ nuôi con dưới 12 tháng</strong></td><td>Nhân sự nữ có con trai hoặc con gái sinh trong 12 tháng gần nhất</td><td>Ngày con đủ 12 tháng</td></tr>
</tbody>
</table>
<p>Ô <strong>Xem theo</strong> cho chia theo <strong>Phòng ban</strong> (mặc định), <strong>Công ty</strong> hoặc <strong>Loại đối tượng</strong>. Một người có thể thuộc hai loại cùng lúc (ví dụ đang nghỉ thai sản và có con nhỏ).</p>

<h2>Tuổi nghỉ hưu được tính thế nào</h2>
<p>Báo cáo theo lộ trình của <strong>Nghị định 135/2020/NĐ-CP</strong> cho người làm việc trong điều kiện bình thường:</p>
<ul>
<li><strong>Nam</strong>: 60 tuổi 3 tháng vào năm 2021, mỗi năm tăng thêm 3 tháng, tới <strong>62 tuổi</strong> từ năm 2028. Ví dụ năm 2026 là 61 tuổi 6 tháng, năm 2027 là 61 tuổi 9 tháng.</li>
<li><strong>Nữ</strong>: 55 tuổi 4 tháng vào năm 2021, mỗi năm tăng thêm 4 tháng, tới <strong>60 tuổi</strong> từ năm 2035. Ví dụ năm 2026 là 57 tuổi, năm 2027 là 57 tuổi 4 tháng.</li>
</ul>
<p><strong>Thời điểm nghỉ hưu</strong> là hết ngày cuối của tháng người đó đủ tuổi nghỉ hưu. Ví dụ đủ tuổi ngày 10/3 thì thời điểm nghỉ hưu là 31/3.</p>
<p>Chỉ tính người đã khai ngày sinh và giới tính. Báo cáo không xét trường hợp được nghỉ hưu sớm vì làm nghề nặng nhọc, độc hại; những người này phòng Nhân sự tự rà thêm.</p>

<h2>Dùng danh sách</h2>
<ol>
<li>Mở <strong>Báo cáo</strong> ▸ <strong>Đối tượng cần chú ý theo luật</strong>.</li>
<li>Bấm <strong>Xem danh sách</strong> ở một thẻ số. Danh sách có Mã NV, Họ tên, Phòng ban, Loại và <strong>Mốc</strong>.</li>
<li>Với người sắp nghỉ hưu: báo trước cho người đó và lên kế hoạch người thay. Với người nuôi con dưới 12 tháng: luật cho nghỉ 60 phút mỗi ngày trong giờ làm, báo cho quản lý trực tiếp để xếp việc.</li>
<li>Bấm một dòng để mở hồ sơ người đó.</li>
</ol>

<h2>Lưu ý và quyền</h2>
<ul>
<li>Báo cáo cần thêm <strong>quyền xem thông tin nhạy cảm của nhân sự</strong> (ngày sinh, người thân). Thiếu quyền thì trang báo <em>Báo cáo này dùng ngày sinh và thông tin con của nhân sự nên cần quyền xem dữ liệu nhạy cảm…</em>. Vì vậy báo cáo không lên trang Tổng quan của phân hệ Báo cáo.</li>
<li>Danh sách <strong>không in ngày sinh</strong> của nhân viên hay của con, chỉ in ngày mốc.</li>
<li>Con nhỏ lấy từ danh sách người thân trong hồ sơ, nên chỉ đúng khi nhân viên đã khai con kèm ngày sinh. Nghỉ thai sản nhận đơn thuộc loại nghỉ <em>Nghỉ thai sản</em> trong phạm vi bạn được xem đơn nghỉ, cộng với hồ sơ đang ở trạng thái <em>Nghỉ thai sản</em>. Trạng thái hồ sơ là trạng thái hiện tại, nên khi xem kỳ đã qua thì chỉ tính theo đơn.</li>
<li>Chưa có danh sách lao động nước ngoài và giấy phép lao động sắp hết hạn.</li>
</ul>""",
        },
        {
            "title": REMINDERS_TITLE,
            "icon": "bell",
            "summary": "Ô Lịch nhắc trong tháng ở Tổng quan Nhân sự: chọn tháng; Sinh nhật (chỉ ngày / tháng), Kỷ niệm 1, 3, 5, 10 năm làm việc, HĐ / thử việc hết hạn; bấm dòng mở hồ sơ; nhóm nào thiếu quyền thì ẩn",
            "content": f"""<h2>Ô này ở đâu</h2>
<p>Mở phân hệ <strong>Nhân sự</strong>, trang <strong>Tổng quan</strong>. Ô <strong>Lịch nhắc trong tháng</strong> nằm trọn một hàng, cho biết tháng này có việc gì cần nhớ: sinh nhật, kỷ niệm năm làm việc, hợp đồng và thử việc hết hạn. Đây chỉ là danh sách để liếc nhanh; muốn phát quà và dự trù tiền thì dùng báo cáo <strong>Phúc lợi &amp; sự kiện</strong> (bài {ref(BENEFIT_TITLE, "Lập danh sách nhận quà và dự trù kinh phí theo dịp")}).</p>

<h2>Đổi tháng</h2>
<p>Ô mở sẵn ở tháng hiện tại, tên tháng hiện trên đầu ô (ví dụ <em>Tháng 10/2026</em>). Bấm mũi tên trái (<strong>Tháng trước</strong>) hoặc mũi tên phải (<strong>Tháng sau</strong>), hoặc bấm vào tên tháng để chọn thẳng một tháng.</p>

<h2>Ba nhóm trong ô</h2>
<table>
<thead><tr><th>Nhóm</th><th>Ai có trong nhóm</th><th>Dòng ghi</th></tr></thead>
<tbody>
<tr><td><strong>Sinh nhật</strong></td><td>Người có sinh nhật trong tháng</td><td>Ví dụ <em>Sinh nhật 04/10 · Kế toán</em>. Chỉ có ngày và tháng, không có năm sinh hay tuổi</td></tr>
<tr><td><strong>Kỷ niệm năm làm việc</strong></td><td>Người vào làm đúng tháng này và tròn 1, 3, 5 hoặc 10 năm</td><td>Ví dụ <em>Tròn 5 năm làm việc · 15/10</em></td></tr>
<tr><td><strong>HĐ / thử việc hết hạn</strong></td><td>Hợp đồng lao động hoặc hợp đồng thử việc đã ký, kết thúc trong tháng, chưa có hợp đồng nối tiếp, của người còn làm</td><td>Ví dụ <em>Hợp đồng hết hạn 15/11</em> hoặc <em>Thử việc hết hạn 20/11</em>. Dòng chữ đỏ là việc gấp</td></tr>
</tbody>
</table>
<p>Số cạnh tên nhóm là tổng số người. Bấm một dòng để mở hồ sơ người đó; dòng hợp đồng mở thẳng tab hợp đồng để lập hợp đồng mới hoặc chấm dứt. Tháng không có ai thì nhóm ghi <em>Không có ai trong tháng này.</em></p>
<ul>
<li>Mỗi nhóm hiện tối đa 200 người. Nhiều hơn thì dưới nhóm có dòng <em>Chỉ hiện … trên … người — còn người khác chưa hiện.</em></li>
<li>Nhóm hợp đồng chỉ nhìn trước <strong>180 ngày</strong> tính từ hôm nay. Chọn tháng xa hơn thì dưới nhóm có dòng <em>Chỉ thấy hợp đồng hết hạn trong 180 ngày tới — tháng này có thể còn thiếu.</em> Muốn soát hợp đồng đã quá hạn, dùng báo cáo {ref(LABOR_CONTRACT_TITLE, "Hợp đồng lao động")}.</li>
</ul>

<h2>Ai thấy nhóm nào</h2>
<ul>
<li>Ô chỉ hiện với người được xem hồ sơ nhân sự, và chỉ gồm người trong phạm vi bạn được xem.</li>
<li>Nhóm <strong>Sinh nhật</strong> cần thêm quyền xem thông tin nhạy cảm của nhân sự.</li>
<li>Nhóm <strong>HĐ / thử việc hết hạn</strong> cần thêm quyền xem hợp đồng lao động.</li>
<li>Nhóm nào thiếu quyền thì không hiện, thay vì hiện số 0.</li>
</ul>""",
        },
        {
            "title": ADMIN_ACCESS_TITLE,
            "icon": "shield-check",
            "summary": "Mười hai báo cáo mới lúc đầu chỉ admin thấy; giao ở Phân quyền tài khoản ▸ tab Báo cáo; vẫn cần quyền ở phân hệ gốc; báo cáo quỹ lương chỉ giao đúng từng người",
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
<tr><td>Sổ quản lý lao động · Báo cáo sử dụng lao động (01/PLI)</td><td>Xem hồ sơ nhân sự, <strong>và thêm</strong> xem thông tin nhạy cảm của nhân sự, xem hợp đồng lao động. Thiếu một trong hai quyền thêm thì trang báo rõ thiếu quyền nào</td></tr>
<tr><td>Quỹ lương theo pháp nhân</td><td>Xem hồ sơ nhân sự (không cần quyền xem hợp đồng lao động). Số liệu chỉ gồm người trong phạm vi hồ sơ bạn được xem</td></tr>
<tr><td>Phúc lợi &amp; sự kiện</td><td>Xem hồ sơ nhân sự. Lọc theo tuổi, tháng sinh, tuổi con cần thêm quyền xem thông tin nhạy cảm của nhân sự</td></tr>
<tr><td>Cơ cấu quản lý · Điều chuyển &amp; bổ nhiệm</td><td>Xem hồ sơ nhân sự</td></tr>
<tr><td>Có mặt theo ngày</td><td>Xem hồ sơ nhân sự. Các cột nghỉ, có mặt và tỷ lệ cần thêm quyền xem đơn nghỉ phép; thiếu thì chỉ còn <em>Người-ngày phải làm</em></td></tr>
<tr><td>Yêu cầu sửa hồ sơ</td><td><strong>Sửa</strong> hồ sơ nhân sự (cùng quyền của màn Duyệt sửa hồ sơ); xuất Excel cần thêm quyền xuất hồ sơ nhân sự</td></tr>
<tr><td>Sử dụng phòng họp</td><td>Xem phiếu đặt phòng họp</td></tr>
<tr><td>Đối tượng cần chú ý theo luật</td><td>Xem hồ sơ nhân sự, <strong>và thêm</strong> xem thông tin nhạy cảm của nhân sự (ngày sinh, người thân). Thiếu thì trang báo không tải được kèm lý do</td></tr>
</tbody>
</table>
<p>Nút <strong>Xuất Excel</strong> trên báo cáo cần thêm quyền xuất của phân hệ gốc. Hai nút <strong>Xuất sổ (Excel)</strong> và <strong>Xuất mẫu 01/PLI</strong> cần quyền xuất hồ sơ nhân sự và quyền xuất hợp đồng lao động. Nút <strong>Xuất danh sách ký nhận</strong> của báo cáo Phúc lợi &amp; sự kiện và nút <strong>Xuất Excel</strong> của báo cáo Quỹ lương theo pháp nhân cần quyền xuất hồ sơ nhân sự. Báo cáo <em>Hồ sơ &amp; tài khoản còn thiếu</em> hiện thêm nhóm giấy tờ cá nhân với người có quyền xem thông tin nhạy cảm, và nhóm tài khoản với người có quyền xem tài khoản. Ở báo cáo <em>Biến động nhân sự</em>, người không có quyền xem thông tin nhạy cảm thấy nhóm tuổi dưới 3 người bị che số và không mở được danh sách theo nhóm tuổi.</p>

<h2>Giao các báo cáo mới cho trưởng phòng Nhân sự và Ban Giám đốc</h2>
<p>Mười hai báo cáo mới lúc mới lên <strong>chỉ quản trị hệ thống thấy</strong>:</p>
<table>
<thead><tr><th>Báo cáo</th><th>Nên giao cho</th></tr></thead>
<tbody>
<tr><td>Hợp đồng lao động</td><td>Trưởng phòng Nhân sự, Ban Giám đốc (danh sách có cột lương)</td></tr>
<tr><td>Hồ sơ &amp; tài khoản còn thiếu</td><td>Phòng Nhân sự</td></tr>
<tr><td>Sổ quản lý lao động</td><td>Chỉ trưởng phòng Nhân sự, Ban Giám đốc</td></tr>
<tr><td>Báo cáo sử dụng lao động (01/PLI)</td><td>Chỉ trưởng phòng Nhân sự, Ban Giám đốc</td></tr>
<tr><td><strong>Quỹ lương theo pháp nhân</strong></td><td>Chỉ người được phép biết tổng lương, thường là Ban Giám đốc</td></tr>
<tr><td>Phúc lợi &amp; sự kiện</td><td>Phòng Nhân sự, Hành chính, người lo quà và sự kiện</td></tr>
<tr><td>Cơ cấu quản lý</td><td>Trưởng phòng Nhân sự, Ban Giám đốc</td></tr>
<tr><td>Điều chuyển &amp; bổ nhiệm</td><td>Trưởng phòng Nhân sự, Ban Giám đốc</td></tr>
<tr><td>Có mặt theo ngày</td><td>Phòng Nhân sự, trưởng các phòng (mỗi người chỉ thấy phòng trong phạm vi của mình)</td></tr>
<tr><td>Yêu cầu sửa hồ sơ</td><td>Trưởng phòng Nhân sự</td></tr>
<tr><td>Sử dụng phòng họp</td><td>Hành chính, người quản lý phòng họp</td></tr>
<tr><td>Đối tượng cần chú ý theo luật</td><td>Chỉ trưởng phòng Nhân sự, Ban Giám đốc (báo cáo dựa trên ngày sinh và thông tin con nhỏ)</td></tr>
</tbody>
</table>
<p>Quản trị giao cho người cần dùng như sau:</p>
<ol>
<li>Vào màn <strong>Phân quyền tài khoản</strong>, chọn tab <strong>Báo cáo</strong>. Bảng liệt kê mọi báo cáo theo phân hệ, kèm cột <strong>Được xem</strong> và <strong>Bị cấm</strong>.</li>
<li>Ở dòng <em>Hợp đồng lao động</em>, bấm nút bút chì ở cột <strong>Sửa</strong>. Hộp <strong>Quyền xem Hợp đồng lao động</strong> mở ra.</li>
<li>Ở ô <strong>Thêm người · phòng ban · pháp nhân · vai trò</strong>, chọn người (ví dụ trưởng phòng Nhân sự) hoặc vai trò (ví dụ Ban Giám đốc).</li>
<li>Để <strong>Chiều tác động</strong> là <strong>Cho phép</strong>. Ghi <strong>Lý do</strong> nếu muốn (không bắt buộc).</li>
<li>Bấm <strong>Thêm</strong>, rồi <strong>Đóng</strong>. Làm lại cho từng dòng báo cáo còn lại trong bảng trên.</li>
</ol>
<p>Muốn chặn riêng một người dù vai trò của họ được xem, thêm người đó với chiều <strong>Cấm</strong>: cấm luôn thắng cho phép. Người được giao tải lại trang (hoặc đăng nhập lại) thì menu hiện báo cáo mới.</p>
<p>⚠️ Báo cáo Hợp đồng lao động có cột lương. Chỉ giao cho người được phép xem lương.</p>
<p>⚠️ <strong>Sổ quản lý lao động</strong> và <strong>Báo cáo sử dụng lao động (01/PLI)</strong> xuất ra tệp có <strong>số CCCD, mã số BHXH, ngày sinh, địa chỉ và lương</strong> của từng người. Chỉ giao hai báo cáo này cho <strong>trưởng phòng Nhân sự</strong> và <strong>Ban Giám đốc</strong>, không giao theo cả phòng ban hay pháp nhân. Người được giao cũng phải có sẵn quyền xem thông tin nhạy cảm và quyền xem hợp đồng lao động thì mới mở được (xem bảng ở trên).</p>
<p>⚠️ <strong>Quỹ lương theo pháp nhân là số tiền lương.</strong> Báo cáo chỉ có tổng theo nhóm và không bao giờ hiện lương từng người: nhóm dưới 3 người bị che với mọi người xem, danh sách bấm số không có cột tiền. Dù vậy, tổng lương của một pháp nhân hay một phòng vẫn là số nhạy cảm, nên chỉ giao từng người cụ thể, không giao theo phòng ban, pháp nhân hay vai trò đông người. Số lương của từng người chỉ chính người đó xem được ở Trang cá nhân (bài {ref(SALARY_TITLE, "Nhập lương ở hồ sơ và xem lương của mình")}). Trợ lý AI không đọc số lương, và báo cáo không lên trang Tổng quan.</p>
<p>Quyền ở tab này chỉ quyết định ai mở được trang báo cáo trong phân hệ Báo cáo. Màn danh sách gốc ở từng phân hệ (hồ sơ nhân sự, đơn nghỉ…) vẫn theo quyền vai trò như cũ.</p>""",
        },
    ],
}

EXPECTED_ARTICLES = 20


def check_unique_titles() -> None:
    """Slug trùng bài khác (ngoài cây này) là liên kết chéo nhảy nhầm trên portal — chặn trước khi ghi."""
    titles = [TREE["title"]] + [c["title"] for c in TREE["children"]]
    assert len(titles) == EXPECTED_ARTICLES, titles
    #  Cột `summary` là String(255): dài hơn thì MySQL từ chối giữa chừng lúc chèn.
    too_long = [n["title"] for n in [TREE, *TREE["children"]] if len(n.get("summary") or "") > 255]
    assert not too_long, f"Tóm tắt quá 255 ký tự: {too_long}"
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
