# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho phân hệ NHÂN SỰ — các tính năng hồ sơ ra từ 22/10/2026.

CHỈ viết bài cho tính năng MỚI, KHÔNG viết lại toàn bộ phân hệ hồ sơ nhân sự. Dựng 1 thẻ phân hệ + 7 bài:
  * duoc-CR-670 (22/10): Sơ đồ tổ chức (CR-669) và hộp "kiểm việc đang giữ" trước khi khóa tài khoản /
    cho nghỉ việc (CR-665);
  * duoc-CR-676 (23/10, HR2-2): in Phiếu thông tin nhân viên BM00../QT01/NS, nhân viên tự đề nghị sửa hồ sơ ở
    Trang cá nhân, phòng Nhân sự duyệt ở menu "Duyệt sửa hồ sơ";
  * duoc-CR-693 (29/10): nhập Lương / Phụ cấp ở hồ sơ (tab Chung ▸ Công việc ▸ nhóm Lương), chỉ chính chủ xem số ở
    Trang cá nhân ▸ thẻ "Lương của tôi", ký HĐLĐ tự cập nhật. Nhãn đối chiếu bằng đọc
    `hr/components/employee-salary-section.tsx`, `app/components/profile/profile-salary-card.tsx`,
    `labor_contract/salary_sync.py` và ảnh `plans/reports/screenshots-cr693/0[1-6,9]-*.png`;
  * duoc-CR-694 (29/10): nhiều số điện thoại (1 số chính + tối đa 4 số khác, mỗi số một nhãn), hàng hai ô địa chỉ
    + nút "Giống địa chỉ thường trú", tự sửa ở Trang cá nhân, tìm theo số khác, cột Excel "Nhãn số chính" /
    "Số điện thoại khác". Nhãn đối chiếu bằng đọc `hr/components/phone-list-editor.tsx`,
    `hr/schemas/extra-phones-schema.ts`, `employee/phone_rules.py`, `import_tool/employee_import_fields.py` và ảnh
    `plans/reports/screenshots-cr694/1,4,5-*.png` (ảnh 4 chụp trước khi ô nhãn số chính được thêm — theo mã hiện tại
    dòng đầu có ô nhãn, huy hiệu "Số chính" nằm cuối dòng như ảnh 1). Màn danh sách Nhân sự ở ERP v2 chưa có nút
    xuất Excel (đường `/api/employees/export/*` có, bản cũ dùng) nên bài chỉ nói "tệp xuất danh sách nhân sự".
(Nghỉ phép đã có bộ riêng: `seed_help_nghi_phep.py`.)

⚠️ Bố cục Phiếu thông tin nhân viên dựng theo bảng trường của tài liệu HRM vì tệp mẫu gốc BM00 chưa có
(`frontend-v2/.../config/employee-info-print-sections.ts`). Có mẫu gốc mà thứ tự mục đổi thì soát lại bài PRINT_INFO.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_nhan_su.py
    docker compose exec -T api python scripts/reindex_help_rag.py     # nạp vào kho tìm kiếm của trợ lý

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (xem `help_seed_common.py`).

⚠️ Phải KHỚP với cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/60-nhan-su-ho-so.md` (đẩy lên hệ đang chạy
bằng `scripts/publish_handbook_update.py`) và `doc/erp/hrm/01-ho-so-nhan-su.md`.
"""
from help_seed_common import rebuild_tree, ref

SO_DO = "Nhân sự — Xem Sơ đồ tổ chức"
KHOA = "Nhân sự — Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo"
PRINT_INFO = "Nhân sự — In Phiếu thông tin nhân viên"
SELF_CHANGE = "Nhân sự — Tự đề nghị sửa hồ sơ ở Trang cá nhân"
REVIEW_CHANGE = "Nhân sự — Duyệt đề nghị sửa hồ sơ của nhân viên"
SALARY = "Nhân sự — Nhập lương ở hồ sơ và xem lương của mình"
PHONES = "Nhân sự — Khai nhiều số điện thoại và địa chỉ liên hệ"
#  Bài thuộc cây Báo cáo Nhân sự (`seed_help_bao_cao_nhan_su.py`) — chỉ để nối liên kết.
PAYROLL = "Báo cáo Nhân sự — Đọc báo cáo Quỹ lương theo pháp nhân"

TREE = {
    "title": "Hướng dẫn sử dụng Nhân sự — Hồ sơ và tổ chức",
    "icon": "users",
    "summary": "In phiếu thông tin nhân viên; tự đề nghị sửa hồ sơ và phòng Nhân sự duyệt; nhập lương ở hồ sơ và xem lương của mình; nhiều số điện thoại; sơ đồ tổ chức; chuyển việc duyệt treo trước khi khóa tài khoản",
    "content": f"""<h2>Nhân sự — Hồ sơ và tổ chức</h2>
<p>Phân hệ <strong>Nhân sự</strong> giữ hồ sơ nhân viên, phòng ban, chức vụ và (ở bộ hướng dẫn riêng) nghỉ phép. Bộ hướng dẫn này gom các tính năng <strong>mới</strong> về hồ sơ và tổ chức:</p>
<ul>
<li>Cần in tờ khai thông tin của một người (hay của chính mình) để ký nộp: {ref(PRINT_INFO, "In Phiếu thông tin nhân viên")}.</li>
<li>Bạn thấy hồ sơ của mình sai ngày sinh, đổi tài khoản ngân hàng, làm lại CCCD hay có thêm người trong hộ gia đình: {ref(SELF_CHANGE, "Tự đề nghị sửa hồ sơ ở Trang cá nhân")}.</li>
<li>Bạn ở phòng Nhân sự và cần xem, duyệt hay từ chối các đề nghị đó: {ref(REVIEW_CHANGE, "Duyệt đề nghị sửa hồ sơ của nhân viên")}.</li>
<li>Bạn ở phòng Nhân sự cần nhập lương cho một người, hoặc muốn xem lương của chính mình: {ref(SALARY, "Nhập lương ở hồ sơ và xem lương của mình")}.</li>
<li>Một người dùng nhiều số điện thoại (số cá nhân, số công việc, Zalo…) hay cần sửa địa chỉ liên hệ: {ref(PHONES, "Khai nhiều số điện thoại và địa chỉ liên hệ")}.</li>
<li>Muốn xem ai thuộc phòng nào, ai quản lý ai: {ref(SO_DO, "Xem Sơ đồ tổ chức")}.</li>
<li>Sắp khóa tài khoản hay cho một người nghỉ việc mà người đó còn phiếu cần duyệt: {ref(KHOA, "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}.</li>
</ul>
<p>Nghỉ phép có bộ hướng dẫn riêng ở thẻ <strong>Hướng dẫn sử dụng Nghỉ phép</strong>.</p>""",
    "children": [
        {
            "title": PRINT_INFO,
            "icon": "printer",
            "summary": "Nút 'In phiếu thông tin' ở hồ sơ nhân sự và ở Trang cá nhân: phiếu A4 bảy mục BM00../QT01/NS, ô nhạy cảm để trống khi thiếu quyền",
            "content": f"""<h2>In Phiếu thông tin nhân viên</h2>
<p>Phiếu thông tin nhân viên (mẫu <strong>BM00../QT01/NS</strong>) là tờ khai một trang A4 mà nhân viên ký nộp phòng Nhân sự. Hệ thống tự điền phiếu từ hồ sơ đang có, nên bạn không phải chép tay lại từng ô.</p>

<h2>In từ đâu</h2>
<table>
<thead><tr><th>Bạn là</th><th>Bấm ở đâu</th><th>Cần quyền gì</th></tr></thead>
<tbody>
<tr><td>Phòng Nhân sự, in phiếu của một nhân viên</td><td><strong>Nhân sự ▸ Nhân sự</strong> ▸ mở hồ sơ người đó ▸ nút <strong>In phiếu thông tin</strong> ở góc phải, cạnh nút <strong>Lưu</strong></td><td>Quyền xem hồ sơ nhân sự, và hồ sơ đó nằm trong phạm vi bạn được xem</td></tr>
<tr><td>Nhân viên, in phiếu của chính mình</td><td>Menu tài khoản ở góc phải ▸ <strong>Trang cá nhân</strong> ▸ mục <strong>Thông tin cá nhân</strong> ▸ nút <strong>In phiếu thông tin</strong> ngay trên khối hồ sơ nhân sự</td><td>Chỉ cần đăng nhập; tài khoản phải gắn với hồ sơ nhân sự</td></tr>
</tbody>
</table>
<p>Bấm nút là mở trang xem trước tờ A4. Ở thanh trên cùng, bấm <strong>In phiếu / Lưu PDF</strong> để mở hộp in của trình duyệt: chọn máy in, hoặc chọn lưu thành tệp PDF. Bấm <strong>Quay lại</strong> để trở về hồ sơ hoặc Trang cá nhân.</p>

<h2>Trên phiếu có gì</h2>
<ol>
<li><strong>Thông tin cá nhân</strong>: họ tên, giới tính, ngày sinh, nơi sinh, dân tộc, tôn giáo, tình trạng hôn nhân, số con, trình độ học vấn, chuyên ngành, email cá nhân.</li>
<li><strong>Công việc</strong>: mã nhân viên, pháp nhân, phòng ban, chức vụ, quản lý trực tiếp, hình thức nhân viên, cấp bậc, nơi làm việc, ngày vào làm, email công việc.</li>
<li><strong>Liên hệ</strong>: số điện thoại, địa chỉ thường trú, địa chỉ hiện nay.</li>
<li><strong>Ngân hàng</strong>: số tài khoản, tên chủ tài khoản, ngân hàng, chi nhánh.</li>
<li><strong>Giấy tờ và BHXH/BHYT</strong>: CCCD (số, ngày cấp, nơi cấp, ngày hết hạn), mã số thuế cá nhân, số sổ BHXH, nơi và mã nơi khám chữa bệnh BHYT.</li>
<li><strong>Người báo tin khi cần thiết</strong>: bảng người liên hệ khẩn cấp (bắt buộc khai ít nhất một người).</li>
<li><strong>Thành viên hộ gia đình</strong>: bảng dùng để kê khai BHXH, quan hệ ghi theo chủ hộ.</li>
</ol>
<p>Hai bảng người luôn in tối thiểu ba dòng; hồ sơ chưa khai đủ thì các dòng trống để điền tay. Cuối phiếu có hai ô ký <strong>Người khai</strong> (in sẵn họ tên) và <strong>Phòng Nhân sự</strong>. Phiếu <strong>không có ô lương nào</strong>.</p>

<h2>Vì sao có ô in ra để trống</h2>
<ul>
<li>Ô nào hồ sơ chưa nhập thì in thành ô trống để người khai điền tay rồi ký.</li>
<li>⚠️ Phòng Nhân sự in phiếu của người khác mà <strong>chưa có quyền xem thông tin nhạy cảm</strong> thì các ô ngày sinh, mã số thuế, địa chỉ, ngân hàng, CCCD, số sổ BHXH và hai bảng người báo tin, hộ gia đình <strong>đều in trống</strong>, dù hồ sơ có thể đã có dữ liệu. Trang xem trước báo rõ việc này bằng một dòng ghi chú phía trên tờ phiếu (dòng ghi chú không in ra giấy). Cần phiếu đủ thông tin thì nhờ người có quyền đó in, hoặc để nhân viên tự in từ Trang cá nhân.</li>
<li>Nhân viên in phiếu <strong>của chính mình</strong> thì thấy đủ mọi ô, kể cả nhóm nhạy cảm.</li>
</ul>
<p>Thấy thông tin trên phiếu sai: nhân viên làm theo {ref(SELF_CHANGE, "Tự đề nghị sửa hồ sơ ở Trang cá nhân")}, sửa xong in lại. Trang báo <em>Không có hồ sơ để in</em> nghĩa là hồ sơ không tồn tại, bạn không có quyền xem, hoặc tài khoản chưa gắn hồ sơ nhân sự.</p>""",
        },
        {
            "title": SELF_CHANGE,
            "icon": "clipboard-list",
            "summary": "Trang cá nhân ▸ thẻ 'Đề nghị sửa hồ sơ': sửa thông tin cá nhân, ngân hàng, giấy tờ, hộ gia đình rồi gửi; phòng Nhân sự duyệt mới vào hồ sơ; rút đề nghị",
            "content": f"""<h2>Tự đề nghị sửa hồ sơ ở Trang cá nhân</h2>
<p>Hồ sơ nhân sự của bạn có chỗ sai hoặc đã cũ (đổi tài khoản nhận lương, làm lại CCCD, có thêm con…)? Bạn không phải nhắn phòng Nhân sự nữa: gửi <strong>đề nghị sửa</strong> ngay trên ERP, phòng Nhân sự đối chiếu và duyệt, duyệt xong thông tin mới được ghi vào hồ sơ.</p>

<h2>Thông tin nào sửa theo cách nào</h2>
<table>
<thead><tr><th>Nhóm thông tin</th><th>Cách sửa</th></tr></thead>
<tbody>
<tr><td>Số điện thoại, địa chỉ thường trú, địa chỉ hiện nay, người báo tin</td><td><strong>Tự sửa và lưu ngay</strong> ở thẻ <strong>Liên hệ</strong> và bảng người báo tin trên Trang cá nhân, như trước đây — không phải chờ duyệt (khai được nhiều số, xem {ref(PHONES, "Khai nhiều số điện thoại và địa chỉ liên hệ")})</td></tr>
<tr><td>Cá nhân: giới tính, ngày sinh, nơi sinh, dân tộc, tôn giáo, tình trạng hôn nhân, số con, email cá nhân, trình độ học vấn, chuyên ngành</td><td rowspan="4"><strong>Gửi đề nghị</strong>, phòng Nhân sự duyệt rồi mới vào hồ sơ</td></tr>
<tr><td>Ngân hàng: số tài khoản, tên chủ tài khoản, ngân hàng, chi nhánh</td></tr>
<tr><td>Giấy tờ: CCCD (số, ngày cấp, nơi cấp, ngày hết hạn), mã số thuế cá nhân, số sổ BHXH, nơi và mã nơi khám chữa bệnh BHYT</td></tr>
<tr><td>Hộ gia đình (kê khai BHXH)</td></tr>
<tr><td>Họ tên, mã nhân viên, phòng ban, chức vụ, quản lý trực tiếp, ngày vào làm…</td><td>Không tự đề nghị được — liên hệ phòng Nhân sự</td></tr>
</tbody>
</table>

<h2>Gửi đề nghị</h2>
<ol>
<li>Mở menu tài khoản ở góc phải ▸ <strong>Trang cá nhân</strong> ▸ mục <strong>Thông tin cá nhân</strong>, cuộn xuống thẻ <strong>Đề nghị sửa hồ sơ</strong> (ngay dưới phần Liên hệ và người báo tin).</li>
<li>Bấm <strong>Đề nghị sửa thông tin</strong>. Hộp <em>Đề nghị sửa thông tin hồ sơ</em> mở ra với bốn tab <strong>Cá nhân · Ngân hàng · Giấy tờ · Hộ gia đình</strong>, mọi ô đã điền sẵn giá trị hồ sơ hiện tại.</li>
<li>Chỉ sửa những ô cần đổi. Chuyển qua lại giữa các tab không làm mất chữ đã gõ. Ô <strong>Số con</strong> chỉ hiện khi tình trạng hôn nhân là <em>Có gia đình</em>.</li>
<li>Tab <strong>Hộ gia đình</strong>: bấm <strong>Thêm dòng</strong> để thêm người, biểu tượng thùng rác để xóa một dòng. Danh sách bạn gửi sẽ <strong>thay cho cả danh sách hiện tại</strong> khi được duyệt, nên giữ lại đủ những người vẫn còn. Dòng chưa có họ tên không được tính; tối đa 30 dòng.</li>
<li>Nếu cần giải thích, ghi vào ô <strong>Ghi chú cho phòng Nhân sự</strong> (tối đa 500 ký tự), ví dụ <em>đổi ngân hàng nhận lương từ tháng sau</em>.</li>
<li>Bấm <strong>Gửi đề nghị</strong>. Hệ chỉ gửi những ô bạn thật sự đổi; không đổi ô nào thì hộp báo <em>Không có thay đổi nào để gửi</em>.</li>
</ol>

<h2>Theo dõi và rút đề nghị</h2>
<ul>
<li>Thẻ <strong>Đề nghị sửa hồ sơ</strong> luôn hiện đề nghị gần nhất của bạn: trạng thái (<strong>Chờ duyệt</strong>, <strong>Đã duyệt</strong>, <strong>Từ chối</strong> hoặc <strong>Đã rút lại</strong>), giờ gửi, giờ xử lý và người xử lý, rồi từng ô <em>giá trị cũ → giá trị mới</em> và ghi chú của bạn.</li>
<li><strong>Mỗi lúc chỉ có một đề nghị đang chờ duyệt.</strong> Khi đang có một cái, nút <strong>Đề nghị sửa thông tin</strong> bị mờ. Muốn sửa thêm hay gửi lại, bấm <strong>Rút đề nghị</strong>, xác nhận <strong>Rút đề nghị</strong> trong hộp hỏi lại, rồi gửi đề nghị mới gồm đủ mọi ô cần đổi.</li>
<li>Phòng Nhân sự <strong>duyệt</strong>: hồ sơ của bạn được cập nhật ngay, chuông thông báo báo <em>Yêu cầu sửa hồ sơ đã được duyệt</em>.</li>
<li>Phòng Nhân sự <strong>từ chối</strong>: hồ sơ giữ nguyên, chuông báo <em>Yêu cầu sửa hồ sơ bị từ chối</em> và thẻ hiện dòng <strong>Lý do từ chối</strong>. Sửa theo lý do rồi gửi đề nghị mới.</li>
<li>Bấm vào thông báo là về Trang cá nhân để xem kết quả.</li>
</ul>

<h2>Gặp lỗi</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Không thấy thẻ "Đề nghị sửa hồ sơ"</td><td>Tài khoản chưa gắn với hồ sơ nhân sự</td><td>Liên hệ phòng Nhân sự để gắn tài khoản vào hồ sơ</td></tr>
<tr><td>Nút <strong>Đề nghị sửa thông tin</strong> bị mờ</td><td>Bạn đang có một đề nghị chờ duyệt</td><td>Đợi phòng Nhân sự xử lý, hoặc rút đề nghị đó rồi gửi lại</td></tr>
<tr><td>Báo <em>Không có thay đổi nào để gửi</em></td><td>Mọi ô vẫn giống hồ sơ hiện tại</td><td>Sửa ít nhất một ô rồi gửi lại</td></tr>
<tr><td>Bấm <strong>Rút đề nghị</strong> thì báo đề nghị đã được xử lý</td><td>Phòng Nhân sự vừa duyệt hoặc từ chối xong</td><td>Tải lại trang để xem kết quả</td></tr>
</tbody>
</table>
<p>Liên quan: {ref(PRINT_INFO, "In Phiếu thông tin nhân viên")} · {ref(REVIEW_CHANGE, "Duyệt đề nghị sửa hồ sơ của nhân viên")}.</p>""",
        },
        {
            "title": REVIEW_CHANGE,
            "icon": "shield-check",
            "summary": "Menu Nhân sự ▸ Danh mục ▸ 'Duyệt sửa hồ sơ': bảng so sánh Lúc gửi · Hiện tại · Đề nghị, Duyệt ghi vào hồ sơ, Từ chối kèm lý do; ai được duyệt",
            "content": f"""<h2>Duyệt đề nghị sửa hồ sơ của nhân viên</h2>
<p>Nhân viên tự gửi đề nghị sửa thông tin cá nhân, ngân hàng, giấy tờ và hộ gia đình từ Trang cá nhân (xem {ref(SELF_CHANGE, "Tự đề nghị sửa hồ sơ ở Trang cá nhân")}). Đề nghị <strong>chưa đụng vào hồ sơ</strong> cho tới khi phòng Nhân sự bấm <strong>Duyệt</strong>.</p>

<h2>Tìm đề nghị cần xử lý</h2>
<ul>
<li>Vào <strong>Nhân sự ▸ Danh mục ▸ Duyệt sửa hồ sơ</strong>. Con số cạnh tên menu là số đề nghị đang chờ duyệt trong phạm vi của bạn.</li>
<li>Danh sách mặc định lọc <strong>Chờ duyệt</strong>; đổi ô trạng thái sang <strong>Tất cả trạng thái</strong> để xem cả đề nghị đã xử lý. Ô tìm kiếm tìm theo mã hoặc tên nhân viên.</li>
<li>Các cột: <strong>Mã NV · Họ tên · Nhóm thay đổi · Số trường · Ngày gửi · Trạng thái</strong>. Bấm vào một dòng để mở chi tiết.</li>
<li>Mở hồ sơ một nhân viên đang có đề nghị chờ duyệt, đầu màn hiện dải <em>Nhân viên này đang có một đề nghị sửa hồ sơ chờ duyệt.</em> kèm liên kết <strong>Xem đề nghị</strong>.</li>
</ul>

<h2>Đọc bảng so sánh</h2>
<p>Màn chi tiết có tên nhân viên, mã, <em>Gửi bởi …</em>, trạng thái và nút <strong>Mở hồ sơ nhân sự</strong>; dưới đó là giờ gửi và <strong>Ghi chú của nhân viên</strong>. Mỗi nhóm đổi (Cá nhân, Ngân hàng, Giấy tờ) là một bảng bốn cột:</p>
<table>
<thead><tr><th>Cột</th><th>Nghĩa là</th></tr></thead>
<tbody>
<tr><td><strong>Trường</strong></td><td>Ô trên hồ sơ mà nhân viên muốn đổi</td></tr>
<tr><td><strong>Lúc gửi</strong></td><td>Giá trị hồ sơ đúng lúc nhân viên bấm gửi</td></tr>
<tr><td><strong>Hiện tại</strong></td><td>Giá trị hồ sơ ngay lúc bạn xem</td></tr>
<tr><td><strong>Đề nghị</strong></td><td>Giá trị sẽ được ghi vào hồ sơ nếu bạn duyệt</td></tr>
</tbody>
</table>
<p>⚠️ Dòng được tô màu và gắn nhãn <strong>Đã đổi sau khi gửi</strong> là ô hồ sơ đã bị sửa sau lúc nhân viên gửi (người khác trong phòng sửa tay, nhập tệp Excel…). Duyệt sẽ <strong>ghi đè</strong> giá trị hiện tại bằng giá trị đề nghị, nên hãy kiểm lại những dòng này trước khi bấm.</p>
<p>Nhóm <strong>Hộ gia đình</strong> hiện hai bảng cạnh nhau, <em>Lúc gửi (N người)</em> và <em>Đề nghị (N người)</em>: duyệt là thay cả danh sách cũ bằng danh sách đề nghị.</p>

<h2>Duyệt hoặc từ chối</h2>
<ol>
<li><strong>Duyệt</strong>: bấm <strong>Duyệt</strong> ở góc phải, xác nhận <strong>Duyệt</strong> trong hộp <em>Duyệt đề nghị?</em>. Các ô ở cột Đề nghị được ghi ngay vào hồ sơ, lần sửa được ghi vào lịch sử hồ sơ, và nhân viên nhận thông báo.</li>
<li><strong>Từ chối</strong>: bấm <strong>Từ chối</strong>, nhập <strong>Lý do từ chối</strong> (bắt buộc, tối đa 500 ký tự), rồi bấm <strong>Từ chối</strong> trong hộp. Hồ sơ giữ nguyên; nhân viên nhận thông báo và đọc được đúng lý do bạn viết, nên viết rõ cần sửa gì, ví dụ <em>số tài khoản không khớp tên chủ tài khoản</em>.</li>
</ol>
<p>Đề nghị đã xử lý xong (duyệt, từ chối hay nhân viên đã rút lại) thì hai nút không hiện nữa. Hai người cùng mở một đề nghị, người bấm sau sẽ nhận báo <em>Yêu cầu này đã được xử lý</em>.</p>

<h2>Ai được duyệt</h2>
<ul>
<li>Cần <strong>quyền sửa hồ sơ nhân sự</strong>, và chỉ thấy đề nghị của những nhân viên nằm trong phạm vi bạn được sửa. Không có quyền thì màn báo <em>Không có quyền duyệt sửa hồ sơ</em>.</li>
<li><strong>Không tự duyệt đề nghị của chính mình.</strong> Mở đề nghị của bạn, hai nút không hiện và màn ghi <em>Đây là đề nghị sửa hồ sơ của chính bạn — một người khác trong phòng Nhân sự phải duyệt.</em> Chỉ quản trị hệ thống được miễn luật này.</li>
<li>Đề nghị có đụng <strong>ngân hàng, giấy tờ, hộ gia đình hoặc ngày sinh</strong> thì người duyệt phải có thêm <strong>quyền xem thông tin nhạy cảm</strong>. Thiếu quyền đó, các giá trị nhạy cảm hiện <em>Đã ẩn (cần quyền xem thông tin nhạy cảm)</em>, hai nút không hiện, và màn nói rõ lý do. Hãy chuyển cho người có quyền này xử lý.</li>
</ul>
<p>Liên quan: {ref(PRINT_INFO, "In Phiếu thông tin nhân viên")}.</p>""",
        },
        {
            "title": SALARY,
            "icon": "wallet",
            "summary": "Nhập Lương và Phụ cấp ở hồ sơ nhân sự (tab Chung ▸ Công việc ▸ Lương): chỉ chính người đó xem được số ở Trang cá nhân ▸ thẻ 'Lương của tôi', người khác chỉ thấy 'Đã nhập (ẩn)'; ký HĐLĐ tự cập nhật",
            "content": f"""<h2>Lương ở hồ sơ dùng để làm gì</h2>
<p>Mỗi hồ sơ nhân sự có hai ô <strong>Lương (đ/tháng)</strong> và <strong>Phụ cấp (đ/tháng)</strong>. Đây là <strong>chỗ duy nhất</strong> giữ lương của một người trên ERP: báo cáo <strong>Quỹ lương theo pháp nhân</strong> cộng hai ô này lại (xem {ref(PAYROLL, "Đọc báo cáo Quỹ lương theo pháp nhân")}).</p>
<p>⚠️ <strong>Chỉ chính nhân sự đó xem được số lương của mình.</strong> Người khác, kể cả người vừa nhập, trưởng phòng Nhân sự hay quản trị hệ thống, chỉ biết được ô đã nhập hay chưa. Trợ lý AI cũng không đọc được lương, và nhật ký thay đổi của hồ sơ chỉ ghi là có cập nhật lương, không ghi số.</p>

<h2>Nhập lương cho nhân sự</h2>
<p>Người làm được việc này là người <strong>sửa được hồ sơ nhân sự</strong> của người đó (thường là phòng Nhân sự), trong phạm vi hồ sơ mình được sửa.</p>
<ol>
<li>Vào <strong>Nhân sự</strong> ▸ <strong>Nhân sự</strong>, bấm vào người cần nhập để mở hồ sơ.</li>
<li>Ở tab <strong>Chung</strong>, tìm khung <strong>Công việc</strong>, cuối khung có nhóm <strong>Lương</strong> với hai ô <strong>Lương (đ/tháng)</strong> và <strong>Phụ cấp (đ/tháng)</strong>.</li>
<li>Gõ số tiền một tháng, tính bằng đồng, vào từng ô. Người không có phụ cấp thì để trống ô Phụ cấp.</li>
<li>Bấm <strong>Lưu</strong> ở đầu trang.</li>
</ol>
<p>Lưu xong, mở lại hồ sơ bạn sẽ <strong>không thấy số vừa nhập</strong>: hai ô hiện chữ <em>Đã nhập (ẩn)</em>. Đó là đúng thiết kế, không phải mất dữ liệu. Ô hiện <em>Chưa nhập</em> nghĩa là người này chưa có lương trên hồ sơ.</p>

<h2>Đổi hoặc xóa lương đã nhập</h2>
<table>
<thead><tr><th>Bạn muốn</th><th>Làm thế nào</th></tr></thead>
<tbody>
<tr><td>Đổi sang mức lương mới</td><td>Gõ số mới vào ô cần đổi rồi bấm <strong>Lưu</strong>. Số mới thay số cũ; bạn không cần biết số cũ là bao nhiêu</td></tr>
<tr><td>Giữ nguyên số đã nhập</td><td>Để trống ô đó. Ô trống khi lưu nghĩa là <strong>không đụng</strong> vào số cũ, không phải xóa</td></tr>
<tr><td>Xóa hẳn lương đã nhập</td><td>Bấm liên kết <strong>Xóa số đã nhập</strong> dưới hai ô. Hai ô hiện <em>Sẽ xóa khi Lưu</em> và dòng nhắc <em>Lương và phụ cấp đã nhập sẽ bị xóa khi bấm Lưu.</em> Bấm <strong>Lưu</strong> để xóa thật, hoặc bấm <strong>Không xóa nữa</strong> để thôi</td></tr>
</tbody>
</table>

<h2>Ký hợp đồng lao động thì ô lương tự cập nhật</h2>
<p>Khi một hợp đồng lao động ở tab <strong>Hợp đồng</strong> của hồ sơ được bấm <strong>Đánh dấu đã ký</strong>, hệ thống tự chép lương và phụ cấp ghi trên hợp đồng đó sang hai ô lương của hồ sơ, nên không phải nhập hai lần. Việc chép này chỉ xảy ra khi hợp đồng vừa ký là hợp đồng <strong>đang có hiệu lực mới nhất</strong> của người đó (đã tới ngày bắt đầu, chưa hết hạn). Ký bổ sung một hợp đồng cũ, hay hợp đồng chưa tới ngày bắt đầu, thì lương trên hồ sơ giữ nguyên. Sau khi ký, bạn vẫn sửa được ô lương ở hồ sơ như bình thường.</p>

<h2>Không ai tự sửa được lương của mình</h2>
<ul>
<li>Bạn mở hồ sơ của chính mình trong phân hệ Nhân sự thì nhóm <strong>Lương</strong> chỉ để xem, kèm dòng <em>Chỉ bạn xem được số lương của mình. Cần điều chỉnh thì liên hệ phòng Nhân sự.</em> Điều này đúng cả với người có quyền sửa hồ sơ và quản trị.</li>
<li>Người chỉ có quyền xem hồ sơ (không sửa được) thấy hai ô <em>Đã nhập (ẩn)</em> hoặc <em>Chưa nhập</em>, kèm dòng <em>Chỉ chính nhân sự này xem được số lương.</em></li>
<li>Tệp Excel nhập hàng loạt hồ sơ nhân sự <strong>không nhận cột lương</strong>: cột có tiêu đề Lương hay Phụ cấp bị bỏ qua, kèm cảnh báo <em>Lương / phụ cấp không nhập được từ tệp Excel Nhân sự — bỏ qua các cột</em>. Lương chỉ nhập từng người ở hồ sơ.</li>
</ul>

<h2>Xem lương của tôi</h2>
<ol>
<li>Mở menu tài khoản ở góc phải ▸ <strong>Trang cá nhân</strong> ▸ mục <strong>Thông tin cá nhân</strong>.</li>
<li>Ở cột bên phải có thẻ <strong>Lương của tôi</strong> với ba dòng <strong>Lương</strong>, <strong>Phụ cấp</strong> và <strong>Tổng</strong>. Số mặc định bị che thành <em>••••</em>.</li>
<li>Bấm nút con mắt <strong>Xem số</strong> ở góc thẻ để hiện số. Bấm <strong>Ẩn số</strong> để che lại.</li>
</ol>
<p>Số bị che sẵn để bạn không lộ lương khi đang chia sẻ màn hình hay nhờ người khác xem giúp. Mở lại trang là số tự che lại. Thẻ ghi <em>Phòng Nhân sự chưa nhập lương cho bạn.</em> nghĩa là hồ sơ của bạn chưa có lương. Tài khoản chưa gắn với hồ sơ nhân sự thì không có thẻ này.</p>
<p>Thấy số lương sai, hãy báo phòng Nhân sự sửa giúp: bạn không tự sửa được, và lương không nằm trong {ref(SELF_CHANGE, "đề nghị sửa hồ sơ ở Trang cá nhân")}.</p>""",
        },
        {
            "title": PHONES,
            "icon": "phone",
            "summary": "Mỗi nhân sự có tối đa 5 số điện thoại kèm nhãn, dòng đầu là số chính; 'Đặt làm chính', 'Thêm số'; nút 'Giống địa chỉ thường trú'; tự sửa ở Trang cá nhân; tìm theo số khác; cột Excel 'Số điện thoại khác'",
            "content": f"""<h2>Danh sách "Số điện thoại" của một người</h2>
<p>Mỗi hồ sơ nhân sự giữ được <strong>tối đa 5 số điện thoại</strong>: một <strong>số chính</strong> và tối đa 4 số khác. Mỗi số có một <strong>nhãn</strong> để người đọc biết đó là số gì, ví dụ <em>Cá nhân</em>, <em>Công việc</em>, <em>Zalo</em>, <em>Nhà riêng</em>, <em>Khác</em>, hoặc bất kỳ chữ nào bạn tự gõ (tối đa 50 ký tự).</p>
<p><strong>Dòng đầu tiên luôn là số chính</strong>, cuối dòng có huy hiệu <strong>Số chính</strong>. Số chính là số mà mọi chỗ khác của ERP dùng: Phiếu thông tin nhân viên, phiếu đặt xe, trợ lý AI khi trả lời <em>số điện thoại của anh X</em>, và cột số điện thoại trong tệp Excel. Các số khác được lưu ở hồ sơ, hiện ở Trang cá nhân và tìm được bằng ô tìm nhanh, nhưng không thay số chính ở những chỗ đó.</p>

<h2>Thêm hoặc sửa số ở hồ sơ nhân sự</h2>
<p>Người làm được việc này là người <strong>sửa được hồ sơ nhân sự</strong> của người đó (thường là phòng Nhân sự).</p>
<ol>
<li>Vào <strong>Nhân sự</strong> ▸ <strong>Nhân sự</strong>, bấm vào người cần sửa để mở hồ sơ.</li>
<li>Chọn tab <strong>Liên hệ &amp; Ngân hàng</strong>. Khung <strong>Liên hệ</strong> có danh sách <strong>Số điện thoại</strong>; mỗi dòng gồm ô nhãn bên trái và ô số bên phải.</li>
<li>Gõ nhãn vào ô <em>Nhãn</em>: bấm vào ô để chọn một gợi ý có sẵn, hoặc gõ chữ của bạn.</li>
<li>Muốn thêm một số, bấm <strong>Thêm số</strong> (nút có dấu cộng dưới danh sách) rồi gõ nhãn và số vào dòng mới. Đủ 5 số thì nút này ẩn đi.</li>
<li>Muốn bỏ một số khác, bấm biểu tượng thùng rác ở cuối dòng đó.</li>
<li>Bấm <strong>Lưu</strong> ở đầu trang. Mọi thay đổi trong danh sách chỉ được ghi khi bạn bấm Lưu.</li>
</ol>
<p>Số điện thoại <strong>không thuộc</strong> nhóm thông tin nhạy cảm, nên người sửa được hồ sơ nhưng chưa có quyền xem thông tin nhạy cảm vẫn sửa được danh sách số. Hai ô địa chỉ thì khác: chúng thuộc nhóm nhạy cảm và bị khóa khi thiếu quyền đó.</p>

<h2>Đổi số chính</h2>
<ol>
<li>Ở dòng của số bạn muốn dùng làm số chính, bấm <strong>Đặt làm chính</strong>.</li>
<li>Số đó lên dòng đầu, còn số chính cũ xuống đúng chỗ của nó. <strong>Nhãn đi theo số</strong>: số Zalo lên làm số chính thì vẫn mang nhãn Zalo, không nhãn nào bị mất.</li>
<li>Bấm <strong>Lưu</strong> để ghi. Chưa bấm Lưu thì bạn vẫn đổi lại được, hồ sơ chưa bị đụng.</li>
</ol>
<p>Nút <strong>Đặt làm chính</strong> bị mờ khi dòng đó chưa có số. Muốn bỏ hẳn số chính cũ: đặt một số khác làm chính trước, rồi bấm thùng rác ở dòng của số cũ.</p>

<h2>Luật nhập số</h2>
<table>
<thead><tr><th>Luật</th><th>Ví dụ</th></tr></thead>
<tbody>
<tr><td>Mỗi số có từ <strong>8 đến 15 chữ số</strong></td><td><em>0901234567</em> được; <em>090123</em> không được</td></tr>
<tr><td>Chỉ gồm chữ số, khoảng trắng và các ký tự <strong>+ . - ( )</strong>; tối đa 20 ký tự cả dấu</td><td><em>0901 234 567</em>, <em>0901.234.567</em>, <em>+84 901 234 567</em>, <em>(028) 3822 1234</em> đều được</td></tr>
<tr><td><strong>Không trùng nhau</strong> và <strong>không trùng số chính</strong>. Hệ bỏ hết dấu cách và ký tự phân cách rồi mới so</td><td><em>0901 234 567</em> và <em>0901.234.567</em> bị coi là cùng một số</td></tr>
</tbody>
</table>
<p>Số sai luật được báo đỏ ngay dưới dòng đó, chưa cần bấm Lưu. Dòng còn trống số thì bị bỏ qua khi lưu, không tính là lỗi. Luật độ dài và ký tự áp cho các số khác; ô số chính vẫn nhận như trước (tối đa 25 ký tự), nhưng bạn nên ghi số chính đúng luật để sau này đổi chỗ với số khác không bị báo lỗi.</p>

<h2>Hai ô địa chỉ và nút <strong>Giống địa chỉ thường trú</strong></h2>
<p>Ngay dưới danh sách số là một hàng hai ô <strong>Địa chỉ thường trú</strong> và <strong>Địa chỉ hiện nay (tạm trú)</strong> (trên điện thoại hai ô xếp chồng lên nhau). Người đang ở đúng địa chỉ thường trú thì không phải gõ lại: bấm <strong>Giống địa chỉ thường trú</strong> dưới ô tạm trú để chép sang, rồi bấm <strong>Lưu</strong>. Nút này mờ khi ô thường trú còn trống.</p>

<h2>Nhân viên tự sửa số của mình ở Trang cá nhân</h2>
<ol>
<li>Mở menu tài khoản ở góc phải ▸ <strong>Trang cá nhân</strong> ▸ mục <strong>Thông tin cá nhân</strong>.</li>
<li>Ở thẻ <strong>Liên hệ</strong>, bấm nút <strong>Sửa</strong> ở góc thẻ. Hộp <strong>Sửa thông tin liên hệ</strong> mở ra với đúng danh sách số và hai ô địa chỉ như trên.</li>
<li>Thêm, sửa, xóa số hay bấm <strong>Đặt làm chính</strong> như ở hồ sơ, rồi bấm <strong>Lưu</strong>. Màn báo <em>Đã cập nhật thông tin liên hệ</em>.</li>
</ol>
<p>Thay đổi được áp dụng <strong>ngay</strong>, không phải chờ phòng Nhân sự duyệt, và được ghi vào lịch sử hồ sơ của bạn. Thẻ Liên hệ hiện số chính ở dòng <strong>Số điện thoại</strong>, mỗi số khác một dòng mang tên là nhãn của số đó (số chưa có nhãn hiện là <strong>Số điện thoại khác</strong>). Các thông tin khác như ngân hàng hay CCCD vẫn phải gửi đề nghị: xem {ref(SELF_CHANGE, "Tự đề nghị sửa hồ sơ ở Trang cá nhân")}.</p>

<h2>Tìm nhân sự theo số điện thoại</h2>
<p>Ô tìm nhanh <em>Tìm theo tên, mã NV, email, SĐT…</em> trên màn <strong>Nhân sự</strong> tìm được người theo <strong>cả số chính lẫn các số khác</strong>. Để tìm trong số khác, từ khóa phải chỉ gồm chữ số (có thể kèm dấu cách và + . - ( )) và có ít nhất 3 chữ số. Hệ tìm theo đúng cách số được lưu: số lưu là <em>0933 333 333</em> thì gõ <em>0933333333</em> sẽ không ra, hãy gõ một đoạn liền nhau như <em>0933</em> hoặc mấy chữ số cuối. Trợ lý AI tìm người theo số điện thoại cũng khớp cả các số khác.</p>

<h2>Nhập và xuất bằng tệp Excel</h2>
<p>Tệp Excel nhập hồ sơ nhân sự (nút <strong>Nhập Excel</strong> trên màn Nhân sự) và tệp xuất danh sách nhân sự có hai cột dành cho việc này:</p>
<table>
<thead><tr><th>Cột</th><th>Cách ghi</th></tr></thead>
<tbody>
<tr><td><strong>Nhãn số chính</strong></td><td>Nhãn của số chính, tức số ở cột <strong>Điện thoại</strong> của tệp nhập (trong tệp xuất cột này tên là <strong>Số điện thoại</strong>), ví dụ <em>Cá nhân</em>, tối đa 50 ký tự</td></tr>
<tr><td><strong>Số điện thoại khác</strong></td><td>Tối đa 4 số, ngăn cách bằng dấu chấm phẩy; nhãn đặt trong ngoặc ngay sau số, cách số một dấu cách. Số không có nhãn thì chỉ ghi số. Ví dụ: <em>0901234567 (Zalo); 0287654321 (Nhà riêng); 0912345678</em></td></tr>
</tbody>
</table>
<ul>
<li>Ô <strong>để trống</strong> thì danh sách số khác của người đó được <strong>giữ nguyên</strong>.</li>
<li>Ô <strong>có dữ liệu</strong> thì <strong>thay cả danh sách</strong> số khác cũ, nên phải ghi đủ mọi số muốn giữ, không chỉ số mới thêm.</li>
<li>Muốn <strong>xóa hết</strong> số khác, ghi đúng <em>__/empty_value/__</em> vào ô.</li>
<li>Các số trong tệp phải theo đúng luật ở trên (8–15 chữ số, không trùng nhau, không trùng số chính). Định dạng các cột số điện thoại là <strong>Văn bản</strong> để Excel không cắt mất số 0 ở đầu.</li>
<li>Trong tệp xuất, nhãn có dấu chấm phẩy được đổi thành dấu phẩy và ngoặc tròn được đổi thành ngoặc vuông, để tệp đó nhập lại được ngay.</li>
</ul>
<p>Như mọi lần nhập Excel, hệ mặc định <strong>Chạy thử</strong> trước để bạn xem dòng nào lỗi rồi mới ghi thật.</p>

<h2>Gặp lỗi</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Số điện thoại phải có từ 8 đến 15 chữ số</em></td><td>Số quá ngắn hoặc quá dài</td><td>Kiểm lại số, bỏ bớt hoặc thêm chữ số còn thiếu</td></tr>
<tr><td><em>Chỉ gồm chữ số, khoảng trắng và các ký tự + . - ( )</em></td><td>Ô số có chữ cái hay ký tự lạ, thường do dán kèm ghi chú</td><td>Xóa phần chữ, chuyển ghi chú sang ô nhãn</td></tr>
<tr><td><em>Số này đã nhập ở trên</em> hoặc <em>Có số điện thoại bị nhập trùng (kể cả trùng số chính)</em></td><td>Số đó đã có ở một dòng khác, kể cả khi chỉ khác cách đặt dấu cách</td><td>Xóa dòng trùng</td></tr>
<tr><td>Bấm <strong>Đặt làm chính</strong> xong thì dòng của số chính cũ báo đỏ</td><td>Số chính cũ được nhập từ trước khi có luật mới và chưa đúng luật</td><td>Sửa lại số đó cho đúng luật, hoặc xóa dòng đó nếu không còn dùng</td></tr>
<tr><td>Không thấy nút <strong>Thêm số</strong></td><td>Người này đã đủ 5 số</td><td>Xóa bớt một số khác rồi thêm</td></tr>
<tr><td>Không thấy nút <strong>Sửa</strong> ở thẻ Liên hệ trên Trang cá nhân</td><td>Tài khoản của bạn chưa gắn với hồ sơ nhân sự</td><td>Liên hệ phòng Nhân sự để gắn tài khoản vào hồ sơ</td></tr>
</tbody>
</table>""",
        },
        {
            "title": SO_DO,
            "icon": "building",
            "summary": "Menu Nhân sự > Danh mục > Sơ đồ tổ chức: cây pháp nhân, phòng ban, người; chỉ hiện người trong phạm vi bạn được xem",
            "content": f"""<h2>Sơ đồ tổ chức</h2>
<p>Vào <strong>Nhân sự ▸ Danh mục ▸ Sơ đồ tổ chức</strong>. Màn này <strong>không phải bản vẽ nhập tay</strong>: mỗi lần mở, hệ thống tự dựng từ dữ liệu phòng ban, trưởng phòng và ô <strong>Người quản lý trực tiếp</strong> trên hồ sơ. Đổi phòng cho một người hay đổi người quản lý xong, sơ đồ tự đúng ở lần mở sau — không có gì phải vẽ lại.</p>

<h2>Đọc sơ đồ</h2>
<ul>
<li>Cấp trên cùng là <strong>pháp nhân</strong> (tên công ty, kèm tổng số người). Người chưa gán pháp nhân nằm trong nhóm <em>Chưa gán pháp nhân</em>.</li>
<li>Dưới pháp nhân là các <strong>phòng ban</strong>, phòng con thụt vào dưới phòng cha. Mỗi phòng là một thẻ: tên phòng, <strong>Trưởng phòng: …</strong> và số người ở góc phải (đã gồm cả các phòng con).</li>
<li>Bấm vào thẻ phòng để <strong>mở hoặc thu gọn</strong>. Hai tầng đầu mở sẵn, các tầng sâu hơn thu lại cho gọn.</li>
<li>Bên trong phòng là <strong>cây quản lý trực tiếp</strong>: cấp dưới thụt vào dưới người quản lý của họ (cùng phòng). Mỗi người hiện tên, nhãn <strong>Trưởng phòng</strong> nếu là trưởng phòng, chức vụ và mã nhân sự.</li>
<li>Bấm vào <strong>tên một người</strong> để mở hồ sơ của họ.</li>
</ul>

<h2>Ai xem được, thấy những gì</h2>
<ul>
<li>Cần quyền <strong>xem hồ sơ nhân sự</strong>. Không có thì màn báo <em>Không có quyền xem sơ đồ tổ chức</em>; liên hệ quản trị để được cấp.</li>
<li>⚠️ Sơ đồ <strong>chỉ hiện những người trong phạm vi dữ liệu của bạn</strong> (xem cùng một sơ đồ, người thấy nhiều người thấy ít là bình thường). Một trưởng phòng hay quản lý <em>nằm ngoài phạm vi</em> của bạn thì tên họ <strong>không hiện</strong>, kể cả khi họ là cấp trên của người bạn xem được. Tên phòng ban thì vẫn hiện để cây liền mạch, nhưng không lộ người.</li>
<li>Người đã <strong>nghỉ việc</strong> hoặc đã ngưng hoạt động thì không có trên sơ đồ.</li>
<li>Con số <em>N người</em> cũng chỉ đếm người bạn được thấy, nên đừng dùng nó làm quân số chính thức của phòng.</li>
</ul>

<h2>Thấy sơ đồ sai thì sửa ở đâu</h2>
<table>
<thead><tr><th>Sơ đồ đang sai</th><th>Sửa ở</th></tr></thead>
<tbody>
<tr><td>Người nằm nhầm phòng</td><td>Hồ sơ nhân sự ▸ ô <strong>Phòng ban</strong></td></tr>
<tr><td>Người báo cáo nhầm sếp</td><td>Hồ sơ nhân sự ▸ ô <strong>Người quản lý trực tiếp</strong></td></tr>
<tr><td>Sai trưởng phòng</td><td>Nhân sự ▸ Danh mục ▸ <strong>Phòng ban</strong> ▸ chọn lại trưởng phòng</td></tr>
<tr><td>Phòng con nằm nhầm phòng cha</td><td>Nhân sự ▸ Danh mục ▸ <strong>Phòng ban</strong> ▸ ô phòng cha</td></tr>
<tr><td>Màn trống</td><td>Chưa có phòng ban hay nhân sự nào trong phạm vi của bạn — màn ghi đúng câu này</td></tr>
</tbody>
</table>
<p>Hệ chặn người dùng gán vòng lặp (A quản lý B, B quản lý A) ngay lúc lưu hồ sơ; nếu dữ liệu cũ vẫn còn vòng lặp thì sơ đồ vẫn hiển thị được, không bị treo.</p>
<p>Liên quan: {ref(KHOA, "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}.</p>""",
        },
        {
            "title": KHOA,
            "icon": "key-round",
            "summary": "Hộp 'việc đang giữ' hiện trước khi khóa tài khoản hoặc lưu hồ sơ nghỉ việc; chuyển từng việc hoặc chuyển hết; ai được chuyển",
            "content": f"""<h2>Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo</h2>
<p>Khóa tài khoản hay cho nghỉ việc mà người đó còn phiếu đang chờ họ duyệt thì <strong>phiếu sẽ kẹt</strong>: không ai khác thấy việc đó để làm. Từ ngày 22/10/2026, trước khi khóa hệ thống luôn mở hộp <strong>kiểm các việc người đó đang giữ</strong> để bạn chuyển đi trước.</p>

<h2>Hộp này hiện khi nào</h2>
<table>
<thead><tr><th>Bạn làm</th><th>Tên hộp</th></tr></thead>
<tbody>
<tr><td>Lưu hồ sơ nhân sự và đổi trạng thái sang <strong>nghỉ việc</strong> (hoặc bỏ tick đang hoạt động)</td><td><em>Lưu hồ sơ nghỉ việc?</em> — nút xác nhận <strong>Lưu và chuyển nghỉ việc</strong></td></tr>
<tr><td>Hồ sơ nhân sự ▸ tab <strong>Tài khoản</strong> ▸ bấm <strong>Khóa tài khoản + đăng xuất mọi thiết bị</strong></td><td><em>Khóa tài khoản</em></td></tr>
<tr><td>Quản trị ▸ Phân quyền tài khoản ▸ tab <strong>Người dùng</strong> ▸ biểu tượng ổ khóa <strong>Khóa tài khoản</strong> ở dòng người đó</td><td><em>Khóa tài khoản …?</em></td></tr>
<tr><td>Hồ sơ nhân sự ▸ tab <strong>Quá trình công tác</strong> ▸ thêm hoặc áp dòng <strong>Thôi việc</strong> vào hồ sơ</td><td><em>Chuyển hồ sơ sang nghỉ việc?</em></td></tr>
</tbody>
</table>
<p>Tài khoản chưa gắn với hồ sơ nhân sự nào thì không có việc duyệt để kiểm, nên bước này bị bỏ qua.</p>

<h2>Trong hộp có gì</h2>
<ul>
<li><strong>Việc duyệt đang chờ người này</strong>: mỗi dòng là một phiếu (loại phiếu, số phiếu, tiêu đề), bước đang chờ, người trình, <em>hạn</em> và nhãn <em>(quá hạn)</em> nếu đã quá. Bấm vào số phiếu để mở phiếu ở thẻ mới. Phiếu mà <em>bạn</em> không có quyền xem thì chỉ hiện <em>(bạn không có quyền xem phiếu này)</em>, không lộ số hay tên phiếu.</li>
<li><strong>Bước trong luồng duyệt chỉ đích danh người này</strong>: phiếu <em>mới</em> sau này sẽ lùi sang người dự phòng hoặc kẹt. Mỗi dòng dẫn tới luồng duyệt để bạn đổi người ở đó (hộp chỉ nêu, không sửa luồng tại chỗ).</li>
<li>Không còn việc nào thì hộp ghi <em>Người này không còn việc duyệt nào đang treo.</em></li>
</ul>

<h2>Chuyển việc cho người khác</h2>
<ol>
<li>Ở ô <strong>Chuyển cho…</strong>, tìm theo tên hoặc mã rồi chọn người nhận.</li>
<li>Bấm <strong>Chuyển</strong> ở từng dòng để chuyển <strong>riêng việc đó</strong>, hoặc <strong>Chuyển hết (N)</strong> để chuyển <strong>mọi việc</strong> đang chờ (kể cả những việc hộp chưa liệt kê hết vì quá dài).</li>
<li>Danh sách tự làm mới sau mỗi lần chuyển. Chuyển hết thì dòng cảnh báo biến mất.</li>
</ol>
<p>⚠️ <strong>Chỉ người có quyền ghi Luồng duyệt</strong> (thường là quản trị luồng duyệt) mới chuyển được. Nếu bạn không có quyền này, hộp vẫn liệt kê việc nhưng ghi <em>Bạn không có quyền chuyển việc duyệt … — nhờ quản trị luồng chuyển giúp trước khi khóa.</em> Hãy nhờ họ chuyển rồi quay lại khóa.</p>

<h2>Còn việc treo mà vẫn muốn khóa</h2>
<p>Hệ <strong>không chặn cứng</strong>, vì có người nghỉ đột xuất cần khóa ngay. Khi còn việc treo, nút xác nhận đổi chữ thành <strong>Vẫn khóa … (còn việc treo)</strong> để bạn biết mình đang để phiếu kẹt. Bấm xác nhận thì tài khoản vẫn bị khóa và người đó bị đăng xuất khỏi mọi thiết bị như thường; việc treo phải xử lý sau bằng cách nhờ quản trị luồng duyệt chuyển.</p>
<p>Nếu hộp ghi <em>Không xem được danh sách việc đang giữ (thiếu quyền hoặc lỗi)</em> thì bạn chưa đọc được danh sách; hãy tự kiểm ở màn Báo cáo duyệt trước khi khóa.</p>
<p>Xem thêm: {ref(SO_DO, "Xem Sơ đồ tổ chức")}.</p>""",
        },
    ],
}

if __name__ == "__main__":
    rebuild_tree(TREE)
