# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho phân hệ NHÂN SỰ — các tính năng hồ sơ ra từ 22/10/2026.

CHỈ viết bài cho tính năng MỚI, KHÔNG viết lại toàn bộ phân hệ hồ sơ nhân sự. Dựng 1 thẻ phân hệ + 7 bài:
  * duoc-CR-670 (22/10): Sơ đồ tổ chức (CR-669) và hộp "kiểm việc đang giữ" trước khi khóa tài khoản /
    cho nghỉ việc (CR-665);
  * duoc-CR-676 (23/10, HR2-2): in Phiếu thông tin nhân viên BM00../QT01/NS, nhân viên tự đề nghị sửa hồ sơ ở
    Trang cá nhân, phòng Nhân sự duyệt ở menu "Duyệt sửa hồ sơ";
  * duoc-CR-693 (29/10): nhập Lương / Phụ cấp ở hồ sơ (tab Chung ▸ nhóm Lương), chỉ chính chủ xem số ở
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
  * duoc-CR-708 (02/11): màn chi tiết nhân sự đổi khung theo ERPNext — tab Chung không còn thẻ, các nhóm Thông tin cá
    nhân · Công việc · Vào làm & nghỉ việc ngăn bằng đường kẻ, Lương và Kiêm nhiệm gập / mở được; nút In / Lưu / Xóa vẫn ở góc phải hàng tiêu đề.
  * duoc-CR-713 (02/11): Cài đặt nhân sự (Master ▸ Cài đặt nhân sự) — 3 tab: Nhân viên (tiền tố mã, sơ đồ tổ chức cho
    mọi nhân viên, mốc kỷ niệm), Nghỉ phép (chặn đơn lùi ngày + vai trò miễn, chặn tự duyệt, lối tắt danh mục), Hợp đồng
    lao động (ngày báo hết hạn, mức gấp). Nhãn đối chiếu bằng đọc `hr/components/hr-settings-form.tsx` và `FIELDS` nhóm `hr` ở
    `setting/service.py` (lời giải thích trên màn lấy nguyên từ đó).
  * 03/11 (đối chiếu duoc-CR-713/714/715): đường menu bỏ chữ "Danh mục" cho khớp thanh đường dẫn (Nhân sự › Master ›
    Cài đặt nhân sự, trang không lặp tiêu đề — CR-714); nhãn ô viết đúng chữ của `FIELDS`; nút duyệt thẳng tên thật
    là "Duyệt đơn"; thêm ý phiếu nghỉ bù luôn chặn tự duyệt; bài Sơ đồ tổ chức thêm công tắc "Sơ đồ tổ chức cho mọi
    nhân viên".
  * duoc-CR-711 (02/11): Sơ đồ tổ chức làm lại theo ERPNext — khung vẽ kéo thả, thẻ người nối theo quản lý trực tiếp,
    nút mở nhóm, khung thông tin, tìm người, Tìm tôi, Mở hết, hai kiểu vẽ, lọc pháp nhân / phòng ban. Nhãn đối chiếu
    bằng đọc `hr/pages/org-chart-page.tsx`, `hr/components/org-chart-{board,canvas,person-popover}.tsx`.
  * duoc-CR-752 (12/11/2026) thêm bốn bài cho các đợt đã lên mà chưa có HDSD, để Trợ lý AI trích được qua RAG:
    Sửa hồ sơ ở màn chi tiết (ô chọn có ô tìm của duoc-CR-747 đặt đúng chỗ: trước đó câu này nằm nhầm ở bài Tự đề
    nghị sửa hồ sơ, nơi hộp đề nghị KHÔNG có ô Công ty / Phòng ban / Chức vụ / Quản lý), Nhập Excel nhân sự
    (duoc-CR-628), Quyền mặc định theo chức vụ (duoc-CR-653), Quyền Xuất / Nhập và che cột nhạy cảm khi xuất
    (duoc-CR-660 — thuộc Nền tảng, gác ở Quản trị ▸ Phân quyền tài khoản và Quản trị ▸ Xuất dữ liệu, đặt ở đây vì
    câu hỏi hay gặp là xuất danh sách nhân sự); thẻ gốc thêm đoạn cụm menu Master (duoc-CR-712) và nối sang bộ
    Hợp đồng lao động (`seed_help_hop_dong_lao_dong.py`). Bài Lương sửa bước mở nhóm Lương: duoc-CR-708 (khung
    ERPNext, nhóm gập / mở) và khối Hoạt động của duoc-CR-710 đã bị bao-CR-724 (04/11) trả về giao diện cũ — nhóm
    Lương nay nằm cuối thẻ Công việc, không gập; cuối trang là khối Lịch sử thao tác.
  * duoc-CR-754 (12/11/2026): đổi đường menu theo menu mới (một danh sách không tiêu đề nhóm; cụm Master đổi tên
    Danh mục; Cài đặt nhân sự cùng các màn cấu hình của Nghỉ phép, Lịch làm việc, Đặt phòng họp gom vào mục Thiết lập —
    một dòng menu, vào trong là MỘT dải tab phẳng chín tab, không có tab con lồng bên trong).
(Nghỉ phép đã có bộ riêng: `seed_help_nghi_phep.py`; Hợp đồng lao động: `seed_help_hop_dong_lao_dong.py`.)

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
from seed_help_hop_dong_lao_dong import check_unique_titles

EDIT_PROFILE = "Nhân sự — Sửa hồ sơ nhân sự ở màn chi tiết"
IMPORT_EXCEL = "Nhân sự — Nhập hồ sơ hàng loạt bằng tệp Excel"
POSITION_ROLES = "Nhân sự — Quyền mặc định theo chức vụ cho tài khoản mới"
EXPORT_PERM = "Nhân sự — Quyền Xuất, Nhập và che cột nhạy cảm khi xuất tệp"
#  Thẻ gốc của bộ Hợp đồng lao động (`seed_help_hop_dong_lao_dong.py`) — chỉ để nối liên kết.
HDLD_ROOT = "Hướng dẫn sử dụng Hợp đồng lao động"
SO_DO = "Nhân sự — Xem Sơ đồ tổ chức"
KHOA = "Nhân sự — Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo"
PRINT_INFO = "Nhân sự — In Phiếu thông tin nhân viên"
SELF_CHANGE = "Nhân sự — Tự đề nghị sửa hồ sơ ở Trang cá nhân"
REVIEW_CHANGE = "Nhân sự — Duyệt đề nghị sửa hồ sơ của nhân viên"
SALARY = "Nhân sự — Nhập lương ở hồ sơ và xem lương của mình"
PHONES = "Nhân sự — Khai nhiều số điện thoại và địa chỉ liên hệ"
HR_SETTINGS = "Nhân sự — Cài đặt nhân sự: mã nhân sự, sơ đồ tổ chức, nghỉ phép, hợp đồng"
#  Bài thuộc cây Báo cáo Nhân sự (`seed_help_bao_cao_nhan_su.py`) — chỉ để nối liên kết.
PAYROLL = "Báo cáo Nhân sự — Đọc báo cáo Quỹ lương theo pháp nhân"

TREE = {
    "title": "Hướng dẫn sử dụng Nhân sự — Hồ sơ và tổ chức",
    "icon": "users",
    "summary": "Sửa hồ sơ, nhập Excel hàng loạt; in phiếu thông tin; tự đề nghị sửa hồ sơ, phòng Nhân sự duyệt; lương ở hồ sơ; nhiều số điện thoại; sơ đồ tổ chức; chuyển việc duyệt treo khi khóa tài khoản; cài đặt nhân sự; quyền mặc định theo chức vụ; quyền xuất / nhập",
    "content": f"""<h2>Nhân sự — Hồ sơ và tổ chức</h2>
<p>Phân hệ <strong>Nhân sự</strong> giữ hồ sơ nhân viên, phòng ban, chức vụ và (ở bộ hướng dẫn riêng) nghỉ phép, hợp đồng lao động. Bộ hướng dẫn này gom các tính năng về hồ sơ và tổ chức:</p>
<ul>
<li>Cần sửa thông tin trong hồ sơ một người (phòng ban, chức vụ, quản lý trực tiếp…): {ref(EDIT_PROFILE, "Sửa hồ sơ nhân sự ở màn chi tiết")}.</li>
<li>Cần tạo hoặc cập nhật nhiều hồ sơ một lượt: {ref(IMPORT_EXCEL, "Nhập hồ sơ hàng loạt bằng tệp Excel")}.</li>
<li>Cần in tờ khai thông tin của một người (hay của chính mình) để ký nộp: {ref(PRINT_INFO, "In Phiếu thông tin nhân viên")}.</li>
<li>Bạn thấy hồ sơ của mình sai ngày sinh, đổi tài khoản ngân hàng, làm lại CCCD hay có thêm người trong hộ gia đình: {ref(SELF_CHANGE, "Tự đề nghị sửa hồ sơ ở Trang cá nhân")}.</li>
<li>Bạn ở phòng Nhân sự và cần xem, duyệt hay từ chối các đề nghị đó: {ref(REVIEW_CHANGE, "Duyệt đề nghị sửa hồ sơ của nhân viên")}.</li>
<li>Bạn ở phòng Nhân sự cần nhập lương cho một người, hoặc muốn xem lương của chính mình: {ref(SALARY, "Nhập lương ở hồ sơ và xem lương của mình")}.</li>
<li>Một người dùng nhiều số điện thoại (số cá nhân, số công việc, Zalo…) hay cần sửa địa chỉ liên hệ: {ref(PHONES, "Khai nhiều số điện thoại và địa chỉ liên hệ")}.</li>
<li>Muốn xem ai thuộc phòng nào, ai quản lý ai: {ref(SO_DO, "Xem Sơ đồ tổ chức")}.</li>
<li>Sắp khóa tài khoản hay cho một người nghỉ việc mà người đó còn phiếu cần duyệt: {ref(KHOA, "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}.</li>
<li>Muốn đổi tiền tố mã nhân sự, giới hạn ai xem sơ đồ tổ chức, chặn đơn nghỉ lùi ngày / tự duyệt, hay đổi số ngày báo HĐLĐ hết hạn: {ref(HR_SETTINGS, "Cài đặt nhân sự")}.</li>
<li>Bạn là quản trị, muốn người mới có tài khoản là có đủ quyền theo chức vụ: {ref(POSITION_ROLES, "Quyền mặc định theo chức vụ cho tài khoản mới")}.</li>
<li>Bạn là quản trị, cần biết ai được xuất danh sách nhân sự ra tệp, ai được nhập tệp, và vì sao có cột bị để trống: {ref(EXPORT_PERM, "Quyền Xuất, Nhập và che cột nhạy cảm khi xuất tệp")}.</li>
</ul>

<h2>Các màn trong menu Nhân sự</h2>
<p>Menu trái của phân hệ Nhân sự là một danh sách xếp từ trên xuống, không chia tiêu đề nhóm: <strong>Tổng quan</strong> · <strong>Nhân sự</strong> (danh sách hồ sơ) · <strong>Duyệt sửa hồ sơ</strong> · <strong>Sơ đồ tổ chức</strong> · <strong>Nghỉ phép</strong> (Đơn nghỉ phép, Nghỉ bù, Thanh toán nghỉ phép, Lịch nghỉ, Quỹ phép năm) · <strong>Lịch làm việc</strong> (một mục bấm vào là xem lịch, không sổ xuống) · <strong>Đặt phòng họp</strong> (Lịch phòng họp, Phiếu đặt phòng) · <strong>Danh mục</strong> · <strong>Thiết lập</strong>. Mục có mục con (Nghỉ phép, Đặt phòng họp, Danh mục) thì bấm vào để sổ xuống; <strong>Thiết lập</strong> là một dòng, không sổ xuống.</p>
<p>Cụm <strong>Danh mục</strong> gom các danh mục nền:</p>
<table>
<thead><tr><th>Mục con của Danh mục</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Phòng ban</strong></td><td>Danh mục phòng ban, phòng ban cấp trên, trưởng bộ phận</td></tr>
<tr><td><strong>Công ty</strong></td><td>Danh mục pháp nhân</td></tr>
<tr><td><strong>Chức vụ</strong></td><td>Danh sách chức danh dùng ở ô Vị trí / Chức vụ, kèm {ref(POSITION_ROLES, "quyền mặc định theo chức vụ")}</td></tr>
<tr><td><strong>Mẫu hợp đồng</strong></td><td>Mẫu Word hợp đồng lao động của từng pháp nhân, xem bộ {ref(HDLD_ROOT, "Hướng dẫn sử dụng Hợp đồng lao động")}</td></tr>
</tbody>
</table>
<p>Mục <strong>Thiết lập</strong> gom mọi màn cấu hình nền của phân hệ, trước đây nằm rải ở Nghỉ phép, Lịch làm việc và Đặt phòng họp. Bấm <strong>Thiết lập</strong> là mở màn đầu tiên bạn có quyền; ở đầu mỗi màn có <strong>một dải tab</strong> nằm ngang để chuyển sang màn khác, không có tab con lồng bên trong. Bạn chỉ thấy tab của màn mình được vào; được vào đúng một màn thì không hiện dải tab.</p>
<table>
<thead><tr><th>Tab của Thiết lập</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Cài đặt nhân sự</strong></td><td>Tiền tố mã nhân sự, ai xem sơ đồ tổ chức, luật chặn đơn nghỉ, ngày báo hợp đồng hết hạn; xem {ref(HR_SETTINGS, "Cài đặt nhân sự")}</td></tr>
<tr><td><strong>Phân bổ chính sách</strong></td><td>Gán gói chính sách nghỉ phép cho từng người hoặc cả nhóm người trong một khoảng ngày</td></tr>
<tr><td><strong>Gói chính sách</strong></td><td>Khai gói số ngày nghỉ mỗi năm cho một nhóm người (cấp quản lý, thử việc…)</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Luật của từng loại nghỉ, bậc thâm niên, hạn mức theo nhóm</td></tr>
<tr><td><strong>Lịch ngày lễ</strong></td><td>Ngày lễ không trừ vào phép</td></tr>
<tr><td><strong>Ngày cấm nghỉ</strong></td><td>Khoảng ngày công ty không muốn ai nghỉ</td></tr>
<tr><td><strong>Mẫu lịch tuần</strong></td><td>Khai giờ làm từng ngày trong tuần của một mẫu lịch</td></tr>
<tr><td><strong>Gán lịch</strong></td><td>Gán mẫu lịch tuần cho người, phòng ban hay pháp nhân</td></tr>
<tr><td><strong>Danh mục phòng họp</strong></td><td>Khai phòng họp, sức chứa, thiết bị (chỉ quản trị phòng họp)</td></tr>
</tbody>
</table>
<p>Thanh đường dẫn ở đầu trang ghi theo cụm, ví dụ <em>Nhân sự › Danh mục › Chức vụ</em> hay <em>Nhân sự › Thiết lập › Cài đặt nhân sự</em>. Dời menu không đổi quyền của màn nào và không đổi địa chỉ trang: mỗi màn vẫn theo quyền của riêng nó, bạn chỉ thấy mục hay tab mình được vào, và <strong>Danh mục</strong> hay <strong>Thiết lập</strong> chỉ hiện khi bạn được vào ít nhất một màn bên trong.</p>
<p>Nghỉ phép có bộ hướng dẫn riêng ở thẻ <strong>Hướng dẫn sử dụng Nghỉ phép</strong>; hợp đồng lao động ở thẻ {ref(HDLD_ROOT, "Hướng dẫn sử dụng Hợp đồng lao động")}.</p>""",
    "children": [
        {
            "title": EDIT_PROFILE,
            "icon": "users",
            "summary": "Nhân sự ▸ Nhân sự ▸ mở hồ sơ: các tab, thẻ Thông tin cá nhân và Công việc, ô chọn Công ty / Phòng ban / Vị trí / Chức vụ / Người quản lý trực tiếp có ô gõ để tìm, nút Lưu, khối Lịch sử thao tác",
            "content": f"""<h2>Mở hồ sơ một người</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Nhân sự</strong>. Gõ vào ô tìm nhanh (tên, mã NV, email, số điện thoại) hoặc lọc theo phòng ban, tình trạng.</li>
<li>Bấm vào dòng của người cần sửa. Màn chi tiết mở ra; đầu trang có nút <strong>Danh sách nhân sự</strong> để quay về (mở từ chỗ khác thì nút ghi <strong>Quay lại</strong>), và bên phải là <strong>In phiếu thông tin</strong>, <strong>Lưu</strong>, <strong>Xóa</strong> (hai nút sau chỉ hiện khi bạn có quyền).</li>
</ol>
<p>Người mới thì bấm <strong>Thêm mới</strong> ở góc phải màn danh sách, điền hộp <strong>Thêm nhân sự</strong>. Nhiều người một lượt thì dùng tệp Excel: {ref(IMPORT_EXCEL, "Nhập hồ sơ hàng loạt bằng tệp Excel")}.</p>

<h2>Các tab của hồ sơ</h2>
<table>
<thead><tr><th>Tab</th><th>Có gì</th></tr></thead>
<tbody>
<tr><td><strong>Chung</strong></td><td>Thẻ <strong>Thông tin cá nhân</strong> và thẻ <strong>Công việc</strong> (Công ty, Phòng ban, Vị trí / Chức vụ, Người quản lý trực tiếp, Tình trạng làm việc, Trạng thái hồ sơ, nhóm Lương)</td></tr>
<tr><td><strong>Quá trình công tác</strong></td><td>Lịch sử bổ nhiệm, điều chuyển, kiêm nhiệm, thôi việc</td></tr>
<tr><td><strong>Quyết định bổ nhiệm</strong></td><td>Các quyết định liên quan người này</td></tr>
<tr><td><strong>Liên hệ &amp; Ngân hàng</strong></td><td>Số điện thoại, địa chỉ, tài khoản ngân hàng, người báo tin (xem {ref(PHONES, "Khai nhiều số điện thoại và địa chỉ liên hệ")})</td></tr>
<tr><td><strong>Giấy tờ &amp; BHXH</strong></td><td>CCCD, mã số thuế, BHXH, BHYT, hộ gia đình</td></tr>
<tr><td><strong>Hợp đồng</strong></td><td>Hợp đồng lao động; chỉ hiện với người có quyền xem hợp đồng, xem bộ {ref(HDLD_ROOT, "Hướng dẫn sử dụng Hợp đồng lao động")}</td></tr>
<tr><td><strong>Quỹ phép</strong></td><td>Quỹ phép năm của người này</td></tr>
<tr><td><strong>Tài khoản</strong></td><td>Tài khoản đăng nhập gắn với hồ sơ</td></tr>
</tbody>
</table>
<p>Một nút <strong>Lưu</strong> ở đầu trang lưu mọi ô của các tab hồ sơ một lần, sửa ở tab này rồi sang tab kia bấm Lưu vẫn đủ. Các bảng riêng (người báo tin, hộ gia đình, quá trình công tác, hợp đồng…) có nút lưu của riêng chúng.</p>

<h2>Ô chọn gõ được để tìm</h2>
<p>Các ô chọn có danh sách dài trong phân hệ Nhân sự đều có ô tìm: bấm vào ô, gõ vài chữ vào dòng <em>Gõ để tìm…</em> (không dấu cũng được), rồi chọn. Không khớp mục nào thì ô báo <em>Không tìm thấy mục nào.</em></p>
<ul>
<li>Ở hồ sơ và hộp <strong>Thêm nhân sự</strong>: <strong>Công ty</strong> (hộp thêm ghi là <strong>Pháp nhân</strong>), <strong>Phòng ban</strong>, <strong>Vị trí / Chức vụ</strong>, <strong>Người quản lý trực tiếp</strong>.</li>
<li>Ở hộp thêm dòng quá trình công tác: pháp nhân, phòng ban, chức vụ.</li>
<li>Ở màn <strong>Phòng ban</strong> và <strong>Công ty</strong> (cụm Danh mục): các ô chọn pháp nhân, phòng ban, nhân sự, ví dụ <strong>Phòng ban cấp trên</strong>, <strong>Trưởng bộ phận</strong>, <strong>Người đại diện pháp lý</strong>.</li>
<li>Ô <strong>Quan hệ</strong> ở bảng người thân, hộ gia đình.</li>
</ul>
<p>Các ô ngắn vài lựa chọn (Giới tính, Tình trạng hôn nhân, Trình độ học vấn, Hình thức nhân viên, Cấp bậc) vẫn là ô chọn thường.</p>

<h2>Những ô cần đọc kỹ trước khi đổi</h2>
<table>
<thead><tr><th>Ô</th><th>Đổi xong thì sao</th></tr></thead>
<tbody>
<tr><td><strong>Công ty</strong></td><td>Pháp nhân quyết định phạm vi dữ liệu người này đọc được. Đổi pháp nhân sẽ <strong>gỡ họ khỏi mọi phòng ban của pháp nhân cũ</strong>, kể cả phòng kiêm nhiệm. Họ phải đăng xuất rồi đăng nhập lại mới thấy hiệu lực</td></tr>
<tr><td><strong>Người quản lý trực tiếp</strong></td><td>Người ký duyệt đơn từ của nhân viên này ở những luồng duyệt có bước <em>Quản lý trực tiếp người nộp</em>; bỏ trống thì bước đó chuyển cho trưởng bộ phận. Sơ đồ tổ chức cũng vẽ theo ô này</td></tr>
<tr><td><strong>Vị trí / Chức vụ</strong></td><td>Chức danh in trên phiếu. Nếu chức vụ đó đã khai gói quyền, tài khoản của người này được cấp lại vai trò theo chức vụ mới: xem {ref(POSITION_ROLES, "Quyền mặc định theo chức vụ cho tài khoản mới")}</td></tr>
<tr><td><strong>Tình trạng làm việc</strong> sang nghỉ việc</td><td>Hệ thống hỏi trước và khóa tài khoản đăng nhập: xem {ref(KHOA, "Khóa tài khoản hoặc cho nghỉ việc khi còn việc duyệt treo")}</td></tr>
</tbody>
</table>
<p>Thiếu quyền xem thông tin nhạy cảm thì hồ sơ có dòng <em>Một số ô đang ẩn với bạn: CCCD, tài khoản ngân hàng, địa chỉ nhà, ngày sinh, mã số thuế và số BHXH.</em> Các ô đó hiện trống dù hồ sơ có thể đã có dữ liệu, và bấm Lưu <strong>không làm mất</strong> phần đó.</p>

<h2>Xem ai đã sửa gì</h2>
<p>Cuối trang, dưới mọi tab, là khối <strong>Lịch sử thao tác</strong>: mỗi lần lưu là một dòng, ghi người sửa, lúc nào và sửa gì. Quản trị bấm vào liên kết ở từng dòng để mở lượt ghi tương ứng ở Nhật ký hệ thống. Riêng lương không bao giờ hiện số trong lịch sử.</p>""",
        },
        {
            "title": IMPORT_EXCEL,
            "icon": "database",
            "summary": "Màn Nhân sự ▸ nút Nhập Excel: Tải file mẫu, Chạy thử xem lỗi từng dòng, Ghi thật, Hoàn tác cả lô; ô trống là giữ nguyên, __/empty_value/__ là xóa; cột nhạy cảm cần quyền ghi thông tin nhạy cảm; tối đa 2000 dòng, không xóa nhân sự qua tệp",
            "content": f"""<h2>Dùng khi nào</h2>
<p>Phòng Nhân sự tạo mới hoặc cập nhật <strong>nhiều hồ sơ một lượt</strong> bằng tệp Excel: nhập hồ sơ ban đầu, bổ sung ngày vào làm, đổi phòng ban cho cả một nhóm… Hệ thống cho <strong>chạy thử</strong> để xem trước từng dòng sẽ thành gì, rồi mới ghi thật, và <strong>hoàn tác</strong> được cả lô nếu nhập sai.</p>

<h2>Các bước</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Nhân sự</strong>, bấm <strong>Nhập Excel</strong> ở góc phải (cạnh <strong>Thêm mới</strong>). Hộp <strong>Nhập dữ liệu</strong> mở ra, bảng dữ liệu đã khóa sẵn là Nhân sự.</li>
<li>Bấm <strong>Tải file mẫu</strong> để lấy tệp mẫu. Tệp có sheet hướng dẫn giải thích từng cột; điền dữ liệu vào sheet chính, mỗi người một dòng.</li>
<li>Ở ô <strong>Chế độ</strong>, giữ <strong>Chạy thử</strong> (mặc định): hệ thống kiểm toàn bộ tệp nhưng <strong>chưa ghi</strong> gì.</li>
<li>Kéo thả tệp .xlsx (hoặc .csv) vào ô <strong>File nhập dữ liệu</strong>, bấm <strong>Bắt đầu import</strong>.</li>
<li>Màn chuyển sang trang chi tiết lần nhập: số <strong>Tổng dòng · Tạo · Cập nhật · Bỏ qua · Cảnh báo · Rà soát · Lỗi</strong>, và bảng nhật ký từng dòng (lọc <strong>Lỗi</strong>, <strong>Cần rà soát</strong>, <strong>Cảnh báo</strong>). Sửa tệp theo các dòng lỗi rồi chạy thử lại cho tới khi sạch.</li>
<li>Bấm <strong>Ghi thật</strong> ở góc phải trang chi tiết, xác nhận <strong>Ghi thật</strong> trong hộp <em>Ghi thật dữ liệu từ bản chạy thử?</em>. Hệ thống chạy lại đúng tệp đó và lưu vào hồ sơ. Mỗi bản chạy thử chỉ ghi thật được <strong>một lần</strong>.</li>
</ol>
<p>Chọn chế độ <strong>Ghi</strong> ngay từ đầu cũng được, nhưng nên chạy thử trước: nhập nhầm 500 dòng rồi mới thấy thì phải hoàn tác cả lô.</p>

<h2>Luật của tệp</h2>
<ul>
<li><strong>Mã NV</strong>: mã đã có thì <strong>cập nhật</strong> hồ sơ đó, mã chưa có thì <strong>tạo mới</strong>, để trống thì tạo mới và hệ thống tự sinh mã (ghi trong nhật ký lô). Một mã NV chỉ được xuất hiện <strong>một lần</strong> trong tệp.</li>
<li><strong>Ô trống hoặc thiếu cột là giữ nguyên</strong> giá trị cũ, không xóa. Muốn xóa một ô thì ghi đúng <em>__/empty_value/__</em>. Không xóa được Họ tên, Trạng thái, Đang dùng.</li>
<li>Cột tham chiếu ghi theo mã: <strong>Công ty (mã)</strong> (mã, tên, mã số thuế hoặc tên viết tắt của pháp nhân), <strong>Phòng ban (mã)</strong> (mã, hoặc tên chính xác trong đúng công ty), <strong>Chức vụ (mã/tên)</strong>, <strong>Quản lý trực tiếp (mã NV)</strong> (người đã có, hoặc ở dòng phía trên trong cùng tệp).</li>
<li>Các ô mã số (Giới tính, Tình trạng hôn nhân, Trình độ học vấn, Hình thức nhân viên, Cấp bậc, Trạng thái) ghi số hoặc chữ như sheet hướng dẫn. Giá trị lạ là <strong>lỗi dòng</strong>, hệ thống không đoán.</li>
<li>Ngày ghi <em>dd/mm/yyyy</em> hoặc <em>yyyy-mm-dd</em>, hoặc ô kiểu ngày của Excel. Định dạng các cột Số CCCD, Số tài khoản, Điện thoại là <strong>Văn bản</strong> để Excel không cắt số 0 ở đầu.</li>
<li>Cột <strong>Ngày vào làm</strong> có trong tệp: đây là cách nhanh nhất để nhập bù ngày vào làm cho hồ sơ cũ (thiếu ngày này thì thâm niên phép tính bằng 0).</li>
<li>Tối đa <strong>2000 dòng</strong> một tệp.</li>
<li><strong>Không xóa nhân sự qua tệp.</strong> Muốn ngưng một người thì đặt Trạng thái là nghỉ việc (khóa luôn tài khoản đăng nhập) hoặc Đang dùng = 0.</li>
<li>Không nhập qua tệp: ảnh CCCD, người thân / người báo tin, kiêm nhiệm phòng ban, tài khoản đăng nhập, <strong>lương</strong> (cột Lương / Phụ cấp bị bỏ qua kèm cảnh báo). Những thứ đó làm ở màn hồ sơ.</li>
<li>Cột số điện thoại khác và nhãn số chính: xem {ref(PHONES, "Khai nhiều số điện thoại và địa chỉ liên hệ")}.</li>
</ul>

<h2>Cột nhạy cảm</h2>
<p>Ngày sinh, mã số thuế, địa chỉ, ngân hàng, CCCD, BHXH là cột nhạy cảm. Bạn cần <strong>quyền ghi thông tin nhạy cảm</strong> của nhân sự mới nhập được các cột này; thiếu quyền thì <strong>cả cột bị bỏ qua</strong> kèm một cảnh báo, các cột khác vẫn ghi. Tệp gốc của lô có thể chứa CCCD, số tài khoản nên nút <strong>Tải file</strong> ở trang chi tiết lô cần quyền xem thông tin nhạy cảm. Nhật ký và câu báo lỗi không bao giờ chứa giá trị của các cột này.</p>

<h2>Hoàn tác một lô</h2>
<ol>
<li>Mở lại lô ở <strong>Quản trị ▸ Nhập dữ liệu</strong> (hoặc đường dẫn trang chi tiết vừa ghi).</li>
<li>Bấm <strong>Hoàn tác</strong>, xác nhận <strong>Hoàn tác</strong> trong hộp <em>Hoàn tác lần import này?</em>.</li>
</ol>
<ul>
<li>Hồ sơ bị <strong>sửa</strong> trở về giá trị trước khi nhập. Nếu một ô đã bị ai sửa tiếp sau lô thì hệ thống <strong>từ chối cả lượt hoàn tác</strong> và nêu mã NV cùng tên cột, để không đè mất lần sửa sau.</li>
<li>Hồ sơ <strong>tạo mới</strong> bởi lô bị xóa, trừ khi đã có dữ liệu con (người báo tin, người thân, quá trình công tác, hợp đồng, kiêm nhiệm) hoặc đã bị sửa sau lô.</li>
<li>Ai đủ quyền trong phạm vi đều hoàn tác được, không riêng người tạo lô. Hoàn tác về trạng thái nghỉ việc thì tài khoản bị khóa lại; hoàn tác không mở lại tài khoản đã khóa vì nghỉ việc.</li>
</ul>

<h2>Ai dùng được</h2>
<p>Nút <strong>Nhập Excel</strong> chỉ hiện khi bạn có đủ: quyền <strong>Xem</strong> và <strong>Tạo</strong> ở dòng <strong>Nhập dữ liệu (Import)</strong>, cộng quyền <strong>Tạo</strong> hoặc <strong>Sửa</strong> hồ sơ nhân viên. Hoàn tác lô có tạo hồ sơ mới cần thêm quyền <strong>Xóa</strong> hồ sơ. Mỗi dòng chỉ ghi được cho người trong phạm vi của bạn; bạn không chuyển được ai ra khỏi phạm vi của mình và không tự đổi phòng của chính mình. Vai trò cũ không tự có các quyền này; quản trị tick ở <strong>Quản trị ▸ Phân quyền tài khoản</strong>. Lưu ý quyền xem Nhập dữ liệu là quyền chung: người có nó thấy cả danh sách lô nhập của các phân hệ khác.</p>

<h2>Gặp lỗi</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Không thấy nút <strong>Nhập Excel</strong></td><td>Thiếu một trong các quyền ở mục trên</td><td>Nhờ quản trị cấp</td></tr>
<tr><td>Cảnh báo cột nhạy cảm bị bỏ qua</td><td>Thiếu quyền ghi thông tin nhạy cảm</td><td>Nhờ người có quyền nhập, hoặc xin quyền</td></tr>
<tr><td>Dòng lỗi vì mã NV trùng</td><td>Một mã NV xuất hiện hai lần trong tệp</td><td>Gộp hai dòng thành một</td></tr>
<tr><td>Dòng cảnh báo Rà soát ở cột chức vụ</td><td>Chữ ở cột chức vụ không khớp danh mục Chức vụ, hệ thống giữ nguyên chữ làm chức danh</td><td>Sửa cho khớp tên / mã trong <strong>Danh mục ▸ Chức vụ</strong>, hoặc thêm chức vụ mới</td></tr>
<tr><td>Bấm <strong>Ghi thật</strong> lần hai trên cùng bản chạy thử bị từ chối</td><td>Bản chạy thử đó đã được ghi thật một lần</td><td>Mở lô ghi thật đã có để xem kết quả; cần nhập thêm thì chạy thử một tệp mới</td></tr>
<tr><td>Lúc lô đang ghi, người khác thêm nhân sự bằng tay phải chờ</td><td>Lô đang giữ bộ sinh mã NV tới khi ghi xong</td><td>Điền sẵn Mã NV trong tệp để lô chạy nhẹ hơn</td></tr>
</tbody>
</table>""",
        },
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
<li>Ô <strong>Quan hệ</strong> ở bảng người thân có ô tìm: bấm vào ô rồi gõ vài chữ (không dấu cũng được) để lọc, khỏi phải cuộn danh sách dài.</li>
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
            "summary": "Menu Nhân sự ▸ 'Duyệt sửa hồ sơ': bảng so sánh Lúc gửi · Hiện tại · Đề nghị, Duyệt ghi vào hồ sơ, Từ chối kèm lý do; ai được duyệt",
            "content": f"""<h2>Duyệt đề nghị sửa hồ sơ của nhân viên</h2>
<p>Nhân viên tự gửi đề nghị sửa thông tin cá nhân, ngân hàng, giấy tờ và hộ gia đình từ Trang cá nhân (xem {ref(SELF_CHANGE, "Tự đề nghị sửa hồ sơ ở Trang cá nhân")}). Đề nghị <strong>chưa đụng vào hồ sơ</strong> cho tới khi phòng Nhân sự bấm <strong>Duyệt</strong>.</p>

<h2>Tìm đề nghị cần xử lý</h2>
<ul>
<li>Vào <strong>Nhân sự ▸ Duyệt sửa hồ sơ</strong>. Con số cạnh tên menu là số đề nghị đang chờ duyệt trong phạm vi của bạn.</li>
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
            "summary": "Nhập Lương và Phụ cấp ở hồ sơ nhân sự (tab Chung ▸ thẻ Công việc ▸ nhóm Lương): chỉ chính người đó xem được số ở Trang cá nhân ▸ thẻ 'Lương của tôi', người khác chỉ thấy 'Đã nhập (ẩn)'; ký HĐLĐ tự cập nhật",
            "content": f"""<h2>Lương ở hồ sơ dùng để làm gì</h2>
<p>Mỗi hồ sơ nhân sự có hai ô <strong>Lương (đ/tháng)</strong> và <strong>Phụ cấp (đ/tháng)</strong>. Đây là <strong>chỗ duy nhất</strong> giữ lương của một người trên ERP: báo cáo <strong>Quỹ lương theo pháp nhân</strong> cộng hai ô này lại (xem {ref(PAYROLL, "Đọc báo cáo Quỹ lương theo pháp nhân")}).</p>
<p>⚠️ <strong>Chỉ chính nhân sự đó xem được số lương của mình.</strong> Người khác, kể cả người vừa nhập, trưởng phòng Nhân sự hay quản trị hệ thống, chỉ biết được ô đã nhập hay chưa. Trợ lý AI cũng không đọc được lương, và nhật ký thay đổi của hồ sơ chỉ ghi là có cập nhật lương, không ghi số.</p>

<h2>Nhập lương cho nhân sự</h2>
<p>Người làm được việc này là người <strong>sửa được hồ sơ nhân sự</strong> của người đó (thường là phòng Nhân sự), trong phạm vi hồ sơ mình được sửa.</p>
<ol>
<li>Vào <strong>Nhân sự</strong> ▸ <strong>Nhân sự</strong>, bấm vào người cần nhập để mở hồ sơ.</li>
<li>Ở tab <strong>Chung</strong>, kéo xuống cuối thẻ <strong>Công việc</strong> tới nhóm <strong>Lương</strong>, có hai ô <strong>Lương (đ/tháng)</strong> và <strong>Phụ cấp (đ/tháng)</strong>.</li>
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
            "summary": "Menu Nhân sự > Sơ đồ tổ chức: khung vẽ kéo thả, thẻ người nối theo quản lý trực tiếp, tìm người, lọc pháp nhân / phòng ban; chỉ hiện người trong phạm vi bạn được xem",
            "content": f"""<h2>Sơ đồ tổ chức</h2>
<p>Vào <strong>Nhân sự ▸ Sơ đồ tổ chức</strong>. Màn này <strong>không phải bản vẽ nhập tay</strong>: mỗi lần mở, hệ thống tự dựng từ ô <strong>Người quản lý trực tiếp</strong> trên hồ sơ. Đổi người quản lý hay đổi phòng cho một người xong, sơ đồ tự đúng ở lần mở sau — không có gì phải vẽ lại.</p>

<h2>Đọc sơ đồ</h2>
<ul>
<li>Mỗi người là một <strong>thẻ</strong>: vòng chữ viết tắt, họ tên và chức vụ. Thẻ của chính bạn có chữ <strong>Bạn</strong>.</li>
<li>Cây đi theo <strong>quản lý trực tiếp</strong>: cấp dưới treo dưới người quản lý của họ, nối bằng đường kẻ. Người không có quản lý (hoặc quản lý nằm ngoài phần đang xem) đứng ở hàng trên cùng; người có nhiều cấp dưới nhất đứng trước.</li>
<li>Dưới thẻ người có cấp dưới là nút nhỏ có <strong>ba vòng chữ viết tắt và con số</strong> (số cấp dưới trực tiếp). Bấm nút để <strong>mở / thu nhóm</strong>; sơ đồ tự dời và thu nhỏ cho cả nhóm vừa khung.</li>
<li>Bấm vào <strong>thẻ</strong> để mở khung thông tin: mã nhân sự, phòng ban, số cấp dưới, người quản lý (bấm tên để nhảy tới thẻ của họ) và nút <strong>Mở hồ sơ</strong>. Bấm ra nền hoặc nhấn Esc để đóng.</li>
</ul>

<h2>Di chuyển và phóng to</h2>
<ul>
<li><strong>Kéo chuột</strong> trên nền để dời sơ đồ; cuộn chuột / bàn di cũng dời được.</li>
<li><strong>Ctrl (hoặc ⌘) + cuộn</strong>, chụm hai ngón trên bàn di hay màn cảm ứng để phóng to / thu nhỏ; hoặc dùng nút <strong>−</strong> / <strong>+</strong> ở thanh dưới góc trái. Bấm con số phần trăm để về 100%, nút <strong>Vừa khung</strong> (hoặc phím 0) để thấy cả sơ đồ.</li>
<li>Nút <strong>Tìm tôi</strong> (hình tâm ngắm) mở đường tới thẻ của bạn. Nút <strong>Mở hết</strong> mở mọi nhóm cùng lúc, bấm lại (<strong>Thu gọn</strong>) để về như lúc đầu.</li>
<li>Hai nút cuối chọn kiểu vẽ: <strong>Trên xuống dưới</strong> hoặc <strong>Trái sang phải</strong> — hệ thống nhớ lựa chọn cho lần sau. Trên điện thoại sơ đồ luôn xếp dọc.</li>
</ul>

<h2>Tìm người, lọc theo pháp nhân và phòng ban</h2>
<ul>
<li>Ô <strong>Tìm một người</strong> ở góc trên trái: gõ tên, mã hoặc chức vụ (không dấu cũng được), chọn người là sơ đồ mở đường và đưa thẻ đó ra giữa.</li>
<li>Ô <strong>pháp nhân</strong> (chỉ hiện khi bạn xem được từ hai pháp nhân trở lên) mặc định là pháp nhân của bạn; chọn <em>Tất cả pháp nhân</em> để xem hết.</li>
<li>Ô <strong>phòng ban</strong> chỉ vẽ người của phòng đó và các phòng con. Quản lý ở phòng khác thì người đó lên hàng trên cùng. <em>Chưa gắn phòng ban</em> lọc ra những người chưa có phòng.</li>
</ul>

<h2>Ai xem được, thấy những gì</h2>
<ul>
<li>Cần quyền <strong>xem hồ sơ nhân sự</strong>. Không có thì màn báo <em>Không có quyền xem sơ đồ tổ chức</em>; liên hệ quản trị để được cấp.</li>
<li>Công ty có thể tắt <strong>Sơ đồ tổ chức cho mọi nhân viên</strong> ở {ref(HR_SETTINGS, "Cài đặt nhân sự")}. Khi đó chỉ người xem được toàn bộ hồ sơ nhân sự mới mở được sơ đồ; người khác thấy câu <em>Sơ đồ tổ chức chưa mở cho bạn</em> — liên hệ phòng Nhân sự nếu cần xem.</li>
<li>⚠️ Sơ đồ <strong>chỉ hiện những người trong phạm vi dữ liệu của bạn</strong> (xem cùng một sơ đồ, người thấy nhiều người thấy ít là bình thường). Một trưởng phòng hay quản lý <em>nằm ngoài phạm vi</em> của bạn thì tên họ <strong>không hiện</strong>, kể cả khi họ là cấp trên của người bạn xem được. Khi đó người đó đứng ở hàng trên cùng như không có quản lý.</li>
<li>Người đã <strong>nghỉ việc</strong> hoặc đã ngưng hoạt động thì không có trên sơ đồ.</li>
<li>Con số trên nút mở nhóm cũng chỉ đếm cấp dưới bạn được thấy, nên đừng dùng nó làm quân số chính thức.</li>
</ul>

<h2>Thấy sơ đồ sai thì sửa ở đâu</h2>
<table>
<thead><tr><th>Sơ đồ đang sai</th><th>Sửa ở</th></tr></thead>
<tbody>
<tr><td>Người nằm nhầm phòng</td><td>Hồ sơ nhân sự ▸ ô <strong>Phòng ban</strong></td></tr>
<tr><td>Người báo cáo nhầm sếp</td><td>Hồ sơ nhân sự ▸ ô <strong>Người quản lý trực tiếp</strong></td></tr>
<tr><td>Lọc một phòng mà thiếu (hoặc thừa) người của phòng con</td><td>Nhân sự ▸ Danh mục ▸ <strong>Phòng ban</strong> ▸ ô phòng cha</td></tr>
<tr><td>Màn trống</td><td>Chưa có nhân sự nào trong phạm vi của bạn — màn ghi đúng câu này. Trống sau khi chọn phòng ban thì phòng đó chưa có ai: bỏ bớt bộ lọc</td></tr>
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
        {
            "title": HR_SETTINGS,
            "icon": "settings",
            "summary": "Menu Nhân sự > Thiết lập, tab Cài đặt nhân sự: tiền tố mã, sơ đồ tổ chức, mốc kỷ niệm; chặn đơn nghỉ lùi ngày, vai trò duyệt qua ngày cấm nghỉ, chặn tự duyệt; ngày báo HĐLĐ hết hạn",
            "content": f"""<h2>Cài đặt nhân sự</h2>
<p>Vào <strong>Nhân sự ▸ Thiết lập</strong> (mục cuối của menu trái), chọn tab <strong>Cài đặt nhân sự</strong> ở dải tab đầu trang. Tên trang hiện trên thanh đường dẫn ở đầu màn (<em>Nhân sự › Thiết lập › Cài đặt nhân sự</em>) nên trang không lặp lại tiêu đề lần nữa. Trang có ba tab <strong>Nhân viên</strong> · <strong>Nghỉ phép</strong> · <strong>Hợp đồng lao động</strong>; mọi ô mặc định đúng như hệ vẫn chạy trước nay, và mỗi ô có sẵn lời giải thích ngay dưới nhãn.</p>
<p>Sửa ở tab nào cũng được, rồi bấm <strong>Lưu</strong> ở đầu phải dải tab (lưu cả ba tab một lần; nút chỉ sáng khi có thay đổi). Lưu xong màn báo <em>Đã lưu cài đặt nhân sự</em>; thay đổi có hiệu lực sau tối đa khoảng nửa phút (máy chủ giữ bộ nhớ đệm cấu hình 30 giây), không cần khởi động lại gì.</p>
<p>Ai mở được trang: người có quyền <strong>Cấu hình hệ thống</strong> (xem). Ai sửa được: người có quyền Cấu hình hệ thống (sửa) — thường chỉ quản trị. Người chỉ có quyền xem thì không thấy nút Lưu, các ô bị khóa và đầu mỗi tab có câu <em>Bạn chỉ xem được — sửa cần quyền Cấu hình hệ thống.</em> Mỗi lần lưu đều ghi vào tab <strong>Lịch sử thay đổi</strong> của màn <strong>Quản trị ▸ Cấu hình hệ thống</strong>.</p>

<h2>Tab Nhân viên</h2>
<ul>
<li><strong>Tiền tố mã nhân sự</strong> (mặc định NSU): hồ sơ tạo mới — tạo tay hoặc nhập Excel mà để trống Mã NV — được đánh mã tiền tố này + số tăng dần, ví dụ NSU245. 2–10 chữ cái in hoa không dấu, không có số. Mã đã cấp không đổi theo. Để trống là dùng NSU.</li>
<li><strong>Sơ đồ tổ chức cho mọi nhân viên</strong> (mặc định BẬT): bật thì ai có quyền xem hồ sơ nhân sự đều mở được Sơ đồ tổ chức (chỉ thấy người trong phạm vi của mình). Tắt thì chỉ người xem được <em>toàn bộ</em> hồ sơ nhân sự (thường là phòng Nhân sự, quản trị) mới mở được; người khác mở ra sẽ thấy câu <em>Sơ đồ tổ chức chưa mở cho bạn</em>.</li>
<li><strong>Mốc kỷ niệm vào làm (năm)</strong> (mặc định 1, 3, 5, 10): ô <em>Lịch nhắc trong tháng</em> ở Tổng quan Nhân sự liệt kê người tròn đúng các mốc này. Nhập các số cách nhau bằng dấu phẩy, mỗi số 1–60, tối đa 10 mốc.</li>
</ul>

<h2>Tab Nghỉ phép — chặn đơn nghỉ lùi ngày</h2>
<ul>
<li>Công tắc <strong>Chặn đơn nghỉ lùi ngày</strong> (mặc định TẮT). Bật thì <strong>không lập, sửa hay gửi duyệt</strong> được đơn nghỉ có ngày nghỉ <strong>trước hôm nay</strong> (tính theo giờ Việt Nam). Ngày hôm nay vẫn lập được.</li>
<li>Nháp lập khi còn hợp lệ mà để qua ngày mới bấm gửi thì lúc gửi cũng bị chặn — đổi ngày hoặc nhờ người được miễn.</li>
<li>Ô <strong>Vai trò được lập đơn nghỉ lùi ngày</strong> (bấm <em>Chọn vai trò được miễn</em>): các vai trò chọn ở đây (ví dụ Hành chính, Nhân sự — người hay lập hộ đơn quên nộp) vẫn lập được. Quản trị hệ thống luôn được miễn. Để trống là chỉ quản trị. Ô này mờ đi khi công tắc ở trên đang tắt, vì lúc đó nó không có tác dụng.</li>
<li>Đơn đã gửi duyệt hay đã duyệt trước khi bật <strong>không bị ảnh hưởng</strong>. Đơn bị <strong>trả về</strong> vẫn sửa lý do, bổ sung giấy tờ và gửi lại được; chỉ khi đổi sang ngày đã qua mới bị chặn. Đơn do người được miễn lập hộ thì người nghỉ vẫn gửi duyệt được.</li>
<li>Bị chặn thì màn báo <em>Không lập được đơn nghỉ cho ngày đã qua (ngày …). Cài đặt nhân sự đang chặn đơn lùi ngày — nhờ phòng Nhân sự lập hộ nếu cần.</em></li>
</ul>

<h2>Tab Nghỉ phép — vai trò duyệt qua ngày cấm nghỉ</h2>
<ul>
<li>Ô <strong>Vai trò được duyệt đơn nghỉ rơi vào ngày cấm nghỉ</strong> đi cặp với tab <strong>Ngày cấm nghỉ</strong> của Thiết lập. Đơn nghỉ đụng một khoảng cấm vẫn lập và gửi duyệt được, nhưng lượt duyệt cuối bị chặn — trừ người có vai trò chọn ở ô này.</li>
<li>Quản trị hệ thống luôn được duyệt qua. Để trống là chỉ quản trị.</li>
<li>Ô này không có công tắc riêng: danh mục Ngày cấm nghỉ trống thì không có gì để chặn.</li>
</ul>

<h2>Tab Nghỉ phép — chặn tự duyệt đơn nghỉ</h2>
<ul>
<li>Bình thường, người duyệt được <strong>suy ra</strong> (trưởng phòng, quản lý trực tiếp, theo vai trò…) đã tự né người nộp đơn. Riêng bước luồng duyệt <strong>khai đích danh</strong> một người, hay <strong>người dự phòng</strong>, thì hệ giữ đúng người đã khai — kể cả khi đó chính là người nghỉ.</li>
<li>Bật công tắc <strong>Chặn tự duyệt đơn nghỉ</strong> (mặc định TẮT) thì với đơn nghỉ, <strong>người nghỉ không bao giờ là người duyệt</strong> đơn của chính mình ở mọi kiểu bước, và nút <strong>Duyệt đơn</strong> trên trang chi tiết (duyệt thẳng khi chưa khai luồng) cũng không cho họ tự bấm.</li>
<li>Bước chỉ có mỗi người nghỉ thì đơn chuyển cho <strong>người dự phòng</strong> của bước. Không có người dự phòng (hoặc người dự phòng cũng là người nghỉ) thì đơn <strong>dừng lại</strong> ở trạng thái kẹt, chờ quản trị sửa luồng — hệ <strong>không tự duyệt qua</strong>.</li>
<li>Việc duyệt đã giao cho người nghỉ từ trước khi bật: họ bấm duyệt sẽ bị báo <em>Cài đặt nhân sự đang chặn tự duyệt: bạn không duyệt được đơn nghỉ của chính mình.</em> Quản trị chuyển việc đó cho người khác ở màn quản lý luồng duyệt.</li>
<li><strong>Phiếu nghỉ bù luôn chặn tự duyệt</strong>, dù công tắc này bật hay tắt, vì duyệt phiếu là tạo thêm ngày phép.</li>
</ul>
<p>Cuối tab Nghỉ phép có khối <strong>Danh mục nghỉ phép</strong> với ba lối tắt <strong>Loại nghỉ &amp; bậc thâm niên</strong>, <strong>Lịch ngày lễ</strong> và <strong>Ngày cấm nghỉ</strong> (mỗi lối tắt chỉ hiện với người được sửa danh mục đó).</p>

<h2>Tab Hợp đồng lao động</h2>
<ul>
<li><strong>Báo HĐLĐ sắp hết hạn trước (ngày)</strong> (mặc định 30, được đặt 15–180): HĐLĐ đã ký còn từng này ngày (hoặc đã quá hạn) mà chưa có hợp đồng nối tiếp thì hiện ở chuông thông báo, ô Tổng quan Nhân sự và màn HĐLĐ sắp hết hạn.</li>
<li><strong>Mức gấp — tô đỏ khi còn (ngày)</strong> (mặc định 15): còn từng này ngày trở xuống thì cảnh báo chuyển đỏ. Không được dưới 15 (Điều 45 Bộ luật Lao động 2019 buộc báo người lao động trước ít nhất 15 ngày) và không lớn hơn số ngày báo ở trên — đặt sai thì bấm Lưu sẽ bị báo lỗi.</li>
<li>Các chỉ số cố định <em>Hết hạn trong 30 / 60 / 90 ngày</em> của báo cáo Hợp đồng lao động ở phân hệ Báo cáo không đổi theo ô này.</li>
</ul>
<p>Liên quan: {ref("Nộp đơn nghỉ phép", "Nộp đơn nghỉ phép")} · {ref("Nhân sự — Phân quyền và luồng duyệt", "Phân quyền và luồng duyệt nghỉ phép")} · {ref("Nhân sự — Loại nghỉ, bậc thâm niên và Lịch ngày lễ", "Loại nghỉ và Ngày cấm nghỉ")} · {ref(SO_DO, "Xem Sơ đồ tổ chức")}.</p>""",
        },
        {
            "title": POSITION_ROLES,
            "icon": "key-round",
            "summary": "Danh mục ▸ Chức vụ ▸ tab Quyền mặc định: khai gói vai trò cho một chức vụ, tài khoản của người giữ chức vụ được tự cấp khi cấp tài khoản và khi đổi chức vụ; nút Áp lại cho người đang giữ chức vụ; nhãn Theo chức vụ ở Phân quyền tài khoản",
            "content": f"""<h2>Dùng để làm gì</h2>
<p>Người mới vào công ty có tài khoản là <strong>làm việc được ngay</strong>, không phải chờ quản trị gán từng vai trò. Mỗi chức vụ khai sẵn một <strong>gói vai trò</strong>; tài khoản của người giữ chức vụ đó được hệ thống tự cấp gói, và đổi chức vụ thì gói tự đổi theo.</p>

<h2>Khai gói vai trò cho một chức vụ</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Danh mục ▸ Chức vụ</strong>, bấm vào chức vụ cần khai.</li>
<li>Chọn tab <strong>Quyền mặc định</strong>. Khung <strong>Quyền mặc định của chức vụ</strong> liệt kê các vai trò đang có trong gói (cột <strong>Vai trò</strong> và <strong>Mã</strong>).</li>
<li>Ở ô <em>Chọn vai trò để thêm…</em>, gõ để tìm rồi chọn một vai trò, bấm <strong>Thêm</strong>. Lặp lại cho đủ. Bỏ một vai trò bằng biểu tượng thùng rác ở dòng đó.</li>
<li>Bấm <strong>Lưu</strong>.</li>
</ol>
<p><strong>Lưu gói chưa đổi quyền của ai.</strong> Từ lúc này, người <em>mới</em> được cấp tài khoản hay <em>mới</em> đổi sang chức vụ này sẽ nhận gói. Muốn áp cho những người <strong>đang</strong> giữ chức vụ, xem mục dưới.</p>

<h2>Áp lại cho người đang giữ chức vụ</h2>
<ol>
<li>Lưu gói xong, bấm <strong>Áp lại cho người đang giữ chức vụ (N người)</strong>. Nút mờ khi gói còn thay đổi chưa lưu (rê chuột thấy <em>Lưu gói trước khi áp lại</em>) hoặc khi chưa ai giữ chức vụ.</li>
<li>Hộp <strong>Áp lại quyền mặc định</strong> nói rõ sẽ làm gì với N người: thêm vai trò còn thiếu trong gói, gỡ vai trò hệ thống đã tự cấp trước đây mà nay không còn trong gói; vai trò quản trị gán tay không bị đụng tới. Bấm <strong>Áp lại</strong>.</li>
</ol>

<h2>Hệ thống tự cấp khi nào</h2>
<ul>
<li>Cấp tài khoản cho một nhân sự.</li>
<li>Đổi chức vụ: lưu hồ sơ, nhập Excel, hoàn tác lô nhập, áp một dòng quá trình công tác.</li>
<li>Mở khóa lại tài khoản.</li>
</ul>
<p>Tài khoản đang khóa hoặc hồ sơ đã nghỉ việc thì bỏ qua. Đổi chức vụ từ X sang Y thì hệ thống <strong>chỉ gỡ những vai trò đã tự cấp theo X</strong>; vai trò quản trị gán tay giữ nguyên. Ở <strong>Quản trị ▸ Phân quyền tài khoản</strong>, vai trò được cấp theo gói có nhãn <strong>Theo chức vụ: …</strong> để phân biệt với vai trò gán tay.</p>

<h2>Luật đã chốt</h2>
<ul>
<li><strong>Gói chỉ là danh sách vai trò, không có mức phạm vi.</strong> Mức xem của mình / cả phòng / cả công ty nằm ở cấu hình của từng vai trò. Muốn trưởng phòng xem cả phòng thì chọn vai trò đã cấu hình phạm vi đó.</li>
<li>Không đưa vào gói được: vai trò quản trị, và vai trò có quyền tạo / sửa / xóa ở <strong>Vai trò &amp; phân quyền</strong> hoặc <strong>Tài khoản</strong>.</li>
<li><strong>Không ai tự cấp cho chính mình.</strong> Người không phải quản trị đổi chức vụ của chính mình thì không nhận gói (thu hồi vẫn chạy). Người đang giữ một chức vụ không thêm được vai trò vào gói của chính chức vụ đó.</li>
<li><strong>Không vượt quyền người thao tác.</strong> Người không phải quản trị chỉ cấp được vai trò mà mình có đủ quyền; vai trò còn lại bị bỏ qua và ghi nhật ký.</li>
<li>Sửa gói cần quyền <strong>Sửa</strong> ở dòng <strong>Vai trò &amp; phân quyền</strong> (không phải quyền sửa danh mục chức vụ). Thiếu quyền xem vai trò thì tab ghi <em>Bạn cần quyền xem Vai trò để xem quyền mặc định của chức vụ.</em></li>
<li>Một vai trò đang nằm trong gói của chức vụ nào đó thì không xóa được vai trò đó.</li>
</ul>

<h2>Hạn chế cần biết</h2>
<ul>
<li><strong>Bỏ một vai trò của gói cho riêng một người</strong>: phải sửa gói hoặc đổi chức vụ của họ. Bỏ tick ở Phân quyền tài khoản sẽ bị cấp lại ở lần <strong>Áp lại</strong> hay lần đổi chức vụ sau.</li>
<li>Vai trò vừa gỡ có thể còn tác dụng tối đa khoảng một phút; người đang đăng nhập nên đăng xuất rồi đăng nhập lại để thấy đúng quyền mới.</li>
</ul>
<p>Liên quan: {ref(EDIT_PROFILE, "Sửa hồ sơ nhân sự ở màn chi tiết")} · {ref(IMPORT_EXCEL, "Nhập hồ sơ hàng loạt bằng tệp Excel")}.</p>""",
        },
        {
            "title": EXPORT_PERM,
            "icon": "shield-check",
            "summary": "Cột Xuất và cột Nhập trong ma trận quyền là quyền riêng, không còn đi theo Xem / Sửa; xuất danh sách nhân sự lọc theo phạm vi của quyền Xuất; cột nhạy cảm để trống khi thiếu quyền xem thông tin nhạy cảm; ai tải lại được tệp đã xuất",
            "content": f"""<h2>Xuất và Nhập là quyền riêng</h2>
<p>Trong ma trận quyền của vai trò (<strong>Quản trị ▸ Phân quyền tài khoản</strong> ▸ tab <strong>Vai trò &amp; quyền</strong>), mỗi dòng chức năng có hai cột riêng:</p>
<table>
<thead><tr><th>Cột</th><th>Cho làm gì</th><th>Trước đây</th></tr></thead>
<tbody>
<tr><td><strong>Xuất</strong></td><td>Tải danh sách ra tệp CSV / Excel: hồ sơ nhân sự, phòng ban, sản phẩm, nhà cung cấp và các danh mục khác có nút xuất tệp</td><td>Ai có <strong>Xem</strong> là xuất được</td></tr>
<tr><td><strong>Nhập</strong></td><td>Nhập tệp CSV hàng loạt vào các danh mục có nút nhập tệp (ví dụ sản phẩm, nhà cung cấp)</td><td>Ai có <strong>Sửa</strong> là nhập được</td></tr>
</tbody>
</table>
<p>Lý do tách: một tệp xuất là cả danh sách mang ra ngoài hệ thống, và một tệp nhập có thể tạo / sửa hàng trăm dòng một lúc; hai việc này không nên tự đi kèm quyền xem hay quyền sửa từng dòng. <strong>Vai trò cũ không tự có hai cột này</strong>: sau khi lên bản mới, quản trị tick lại <strong>Xuất</strong> / <strong>Nhập</strong> cho những vai trò trước đây vẫn xuất / nhập được.</p>
<p>Nhập hồ sơ nhân sự bằng tệp Excel ở màn Nhân sự đi đường khác, cần quyền ở dòng <strong>Nhập dữ liệu (Import)</strong>: xem {ref(IMPORT_EXCEL, "Nhập hồ sơ hàng loạt bằng tệp Excel")}.</p>

<h2>Xuất danh sách nhân sự</h2>
<ul>
<li>Cần quyền <strong>Xuất</strong> ở dòng <strong>Nhân viên</strong>. Ở bản mới, cách làm là <strong>Quản trị ▸ Xuất dữ liệu</strong> ▸ nút <strong>Xuất dữ liệu</strong> ▸ chọn phân hệ Nhân sự, bảng Nhân sự, định dạng <strong>Excel (XLSX)</strong> hoặc <strong>CSV</strong> ▸ bấm <strong>Xuất dữ liệu</strong>. Chưa được cấp quyền xuất bảng nào thì hộp báo <em>Bạn chưa được cấp quyền xuất bảng nào.</em></li>
<li>Tệp chỉ gồm những hồ sơ nằm trong <strong>phạm vi của quyền Xuất</strong> (không phải phạm vi của quyền Xem). Ví dụ vai trò xem được cả công ty nhưng chỉ được xuất phòng mình thì tệp chỉ có phòng mình.</li>
<li><strong>Cột nhạy cảm</strong> (ngày sinh, mã số thuế, địa chỉ, ngân hàng, CCCD, BHXH) để <strong>trống</strong> nếu người xuất không có quyền xem thông tin nhạy cảm của nhân sự; dòng hồ sơ của chính người xuất thì vẫn đủ. Ô trống trong tệp vì thế không có nghĩa là hồ sơ chưa nhập.</li>
<li>Lương không bao giờ có trong tệp xuất.</li>
</ul>

<h2>Ai tải lại được tệp đã xuất</h2>
<p>Mỗi lần xuất được ghi vào bảng ở <strong>Quản trị ▸ Xuất dữ liệu</strong>, kèm nút tải lại tệp. Tệp là ảnh chụp theo quyền của <strong>người đã xuất</strong>, nên chỉ những người sau tải lại được:</p>
<ul>
<li>Chính người đã xuất.</li>
<li>Người có quyền <strong>Xuất</strong> phạm vi <strong>tất cả</strong> trên đúng bảng đó. Với bảng Nhân sự còn cần thêm quyền xem thông tin nhạy cảm phạm vi tất cả, vì tệp do người có quyền đó xuất ra chứa đủ CCCD, tài khoản ngân hàng.</li>
</ul>
<p>Người khác bấm tải sẽ bị báo <em>Chỉ người đã xuất, hoặc người có quyền xuất toàn hệ trên bảng này, được tải lại tệp</em>.</p>

<h2>Cấp quyền gợi ý</h2>
<table>
<thead><tr><th>Ai</th><th>Nên có</th></tr></thead>
<tbody>
<tr><td>Nhân viên phòng Nhân sự làm hồ sơ</td><td>Nhân viên: Xem, Tạo, Sửa; Xuất trong phạm vi pháp nhân mình. Thông tin nhạy cảm: Xem, Sửa nếu được giao nhập CCCD, ngân hàng</td></tr>
<tr><td>Trưởng phòng ban khác</td><td>Nhân viên: Xem phạm vi phòng mình. Thường <strong>không</strong> cần Xuất</td></tr>
</tbody>
</table>
<p>Người đang đăng nhập giữ quyền cũ tới khi đăng xuất rồi đăng nhập lại.</p>""",
        },
    ],
}

if __name__ == "__main__":
    check_unique_titles(TREE)
    rebuild_tree(TREE)
