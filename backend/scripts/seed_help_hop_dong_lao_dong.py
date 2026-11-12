# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho cụm HỢP ĐỒNG LAO ĐỘNG của phân hệ Nhân sự (duoc-CR-752, 12/11/2026).

Dựng 1 thẻ phân hệ + 7 bài theo TÁC VỤ, gom các đợt đã lên mà chưa có bài HDSD:
  * duoc-CR-606: lập HĐLĐ trong hồ sơ nhân sự, sinh tệp Word từ mẫu của ĐÚNG pháp nhân + loại hợp đồng;
  * duoc-CR-632: chọn tệp bản ký / scan ngay trong hộp Lập / Sửa hợp đồng;
  * duoc-CR-633: cột Thao tác là một nút "..." mở menu icon + chữ (nhóm Xem · Soạn · Trạng thái · Xóa);
  * duoc-CR-630: danh sách biến của mẫu (biến hệ thống + biến tùy chỉnh nhập tay theo từng hợp đồng);
  * duoc-CR-642 / 643: màn Mẫu hợp đồng mở ngay trong Nhân sự (Master ▸ Mẫu hợp đồng), menu "..." của bảng mẫu;
  * duoc-CR-652: Hợp đồng của tôi ở Trang cá nhân (bản mềm + bản đã ký);
  * duoc-CR-620: cảnh báo HĐLĐ sắp hết / đã hết hạn (chuông, Việc cần làm, thẻ Tổng quan Nhân sự).
Bản lưu trữ ở Văn bản + nút Ban hành (bài của `seed_help_van_ban.py`) và báo cáo HĐ sắp hết hạn (bài của
`seed_help_bao_cao_nhan_su.py`) CHỈ được nối sang bằng `ref`, không viết lại.

Nhãn đối chiếu bằng đọc mã ngày 12/11/2026: `hr/components/employee-tab-labor-contracts.tsx`,
`labor-contract-form-dialog*.tsx`, `labor-contract-signed-file-field.tsx`, `labor-contract-term-presets.tsx`,
`labor-contract-row-actions.tsx`, `labor-contract-generate-dialog.tsx`, `labor-contract-transition-dialog.tsx`,
`hr/utils/labor-contract-rules.ts`, `labor-contract-template-*.tsx`, `hr/pages/labor-contract-template-*.tsx`,
`hr/pages/labor-contract-variables-page.tsx`, `labor-contract-variable-*.tsx`, `expiring-labor-contracts-card.tsx`,
`app/components/profile/profile-labor-contracts-tab.tsx`, `hr/routes.tsx` (cụm Master); câu lỗi lấy từ
`backend/app/modules/labor_contract/` (`service.py`, `rules.py`, `contract_custom_values.py`, `expiry_service.py`).
duoc-CR-753: đổi đường menu theo menu mới (cụm Master đổi tên Danh mục; Cài đặt nhân sự là một tab của mục Thiết lập).

Chạy trong container api (KHÔNG chạy lên prod; prod đồng bộ Help Center theo đợt riêng):
    docker compose exec -T api python scripts/seed_help_hop_dong_lao_dong.py
    docker compose exec -T api python scripts/reindex_help_rag.py     # nạp vào kho tìm kiếm của trợ lý

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (`help_seed_common.rebuild_tree`).
Trước khi ghi, `check_unique_titles` chặn nếu một tiêu đề bài đã có ở cây KHÁC (trùng tiêu đề = trùng slug,
liên kết chéo nhảy nhầm bài).

Phải KHỚP với `doc/erp/hrm/04-hop-dong-lao-dong.md` (phần A).
"""
import sys

from help_seed_common import HelpArticle, SessionLocal, rebuild_tree, ref

ROOT_TITLE = "Hướng dẫn sử dụng Hợp đồng lao động"
LAP = "Hợp đồng lao động — Lập hợp đồng cho một nhân sự"
THAO_TAC = "Hợp đồng lao động — Sinh tệp, ký, hủy và chấm dứt bằng menu Thao tác"
MAU = "Hợp đồng lao động — Tải lên và soạn mẫu Word theo pháp nhân"
BIEN = "Hợp đồng lao động — Danh sách biến và biến tùy chỉnh của mẫu"
CANH_BAO = "Hợp đồng lao động — Nhận cảnh báo hợp đồng sắp hết hạn"
CUA_TOI = "Hợp đồng lao động — Xem lại hợp đồng của tôi ở Trang cá nhân"
QUYEN = "Hợp đồng lao động — Quyền xem, lập hợp đồng và quản lý mẫu"
#  Bài của cây khác — chỉ để nối liên kết.
VB_LUU_TRU = "Văn bản — Bản lưu trữ hợp đồng lao động và nút Ban hành"
BC_HET_HAN = "Báo cáo Nhân sự — Theo dõi hợp đồng lao động sắp hết hạn"
SALARY = "Nhân sự — Nhập lương ở hồ sơ và xem lương của mình"
HR_SETTINGS = "Nhân sự — Cài đặt nhân sự: mã nhân sự, sơ đồ tổ chức, nghỉ phép, hợp đồng"

#  Chuỗi có ngoặc nhọn để riêng, tránh phải nhân đôi ngoặc trong f-string.
VAR_SAMPLE = "{{ ten_bien }}"
VAR_MONEY = "{{ phu_cap_xang_xe }}"
VAR_MONEY_WORDS = "{{ phu_cap_xang_xe_bang_chu }}"

TREE = {
    "title": ROOT_TITLE,
    "icon": "file-text",
    "summary": "Lập hợp đồng lao động trong hồ sơ nhân sự, sinh tệp Word từ mẫu của từng pháp nhân, tải bản đã ký, ký, chấm dứt; quản lý mẫu và biến; cảnh báo sắp hết hạn; người lao động xem lại hợp đồng của mình",
    "content": f"""<h2>Hợp đồng lao động trên ERP</h2>
<p>Phòng Nhân sự lập hợp đồng lao động <strong>ngay trong hồ sơ của từng người</strong> (tab <strong>Hợp đồng</strong> ở màn chi tiết nhân sự), sinh tệp Word từ <strong>mẫu riêng của pháp nhân</strong> người đó đang làm, lưu bản đã ký, đánh dấu đã ký, chấm dứt khi thanh lý. Hệ thống tự nhắc khi hợp đồng sắp hết hạn, và người lao động tự xem lại hợp đồng của mình ở Trang cá nhân.</p>

<h2>Đọc theo việc bạn cần làm</h2>
<ul>
<li>Lập hợp đồng mới cho một nhân sự, kèm luôn bản scan nếu đã có: {ref(LAP, "Lập hợp đồng cho một nhân sự")}.</li>
<li>Sinh tệp Word từ mẫu, tải bản đã ký lên, đánh dấu đã ký, hủy hay chấm dứt: {ref(THAO_TAC, "Sinh tệp, ký, hủy và chấm dứt bằng menu Thao tác")}.</li>
<li>Đưa mẫu hợp đồng Word của một pháp nhân lên hệ thống, hoặc sửa nội dung mẫu ngay trên web: {ref(MAU, "Tải lên và soạn mẫu Word theo pháp nhân")}.</li>
<li>Cần một ô mới trong mẫu mà hồ sơ không có (số ngày phép, phụ cấp riêng…): {ref(BIEN, "Danh sách biến và biến tùy chỉnh của mẫu")}.</li>
<li>Muốn biết hợp đồng nào sắp hết hạn để gia hạn kịp: {ref(CANH_BAO, "Nhận cảnh báo hợp đồng sắp hết hạn")}.</li>
<li>Bạn là người lao động và muốn xem hay tải lại hợp đồng của mình: {ref(CUA_TOI, "Xem lại hợp đồng của tôi ở Trang cá nhân")}.</li>
<li>Bạn là quản trị, cần cấp quyền cho phòng Nhân sự: {ref(QUYEN, "Quyền xem, lập hợp đồng và quản lý mẫu")}.</li>
</ul>

<h2>Năm trạng thái của một hợp đồng</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Nghĩa là</th><th>Làm được gì</th></tr></thead>
<tbody>
<tr><td><strong>Nháp</strong></td><td>Vừa lập, chưa ký</td><td>Sửa, sinh tệp, tải bản ký, đánh dấu đã ký, hủy, xóa</td></tr>
<tr><td><strong>Đã ký – hiệu lực</strong></td><td>Đã ký, đang chạy</td><td>Tải / thay bản ký, chấm dứt. Không sửa nội dung được nữa</td></tr>
<tr><td><strong>Hết hạn</strong></td><td>Đã ký nhưng đã qua ngày kết thúc. Trạng thái này hệ thống tự suy ra theo ngày, không ai bấm</td><td>Như Đã ký; hệ thống nhắc cho tới khi có hợp đồng nối tiếp</td></tr>
<tr><td><strong>Đã chấm dứt / thanh lý</strong></td><td>Chấm dứt trước hạn hoặc thanh lý, có ngày và lý do</td><td>Chỉ xem</td></tr>
<tr><td><strong>Đã hủy</strong></td><td>Bản nháp bị bỏ, có lý do</td><td>Chỉ xem hoặc xóa</td></tr>
</tbody>
</table>
<p>Mỗi hợp đồng còn có một <strong>bản lưu trữ</strong> ở phân hệ Văn bản, tự đổi trạng thái theo hợp đồng: xem {ref(VB_LUU_TRU, "Bản lưu trữ hợp đồng lao động và nút Ban hành")}. Danh sách tổng hợp toàn công ty nằm ở báo cáo: {ref(BC_HET_HAN, "Theo dõi hợp đồng lao động sắp hết hạn")}.</p>""",
    "children": [
        {
            "title": LAP,
            "icon": "clipboard-list",
            "summary": "Hồ sơ nhân sự ▸ tab Hợp đồng ▸ nút Lập hợp đồng: loại, ngày, nút Chọn nhanh thời hạn, lương, Thông tin bổ sung cho mẫu, ô Tệp hợp đồng (bản ký / scan) ngay trong hộp, Lưu",
            "content": f"""<h2>Lập hợp đồng cho một nhân sự</h2>
<p>Hợp đồng lao động nằm trong hồ sơ của từng người, không có màn danh sách riêng. Mỗi người có thể có nhiều hợp đồng nối tiếp nhau (thử việc, rồi xác định thời hạn, rồi không xác định thời hạn).</p>

<h2>Các bước</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Nhân sự</strong>, bấm vào người cần lập để mở hồ sơ.</li>
<li>Chọn tab <strong>Hợp đồng</strong>. Bảng <strong>Hợp đồng lao động</strong> liệt kê mọi hợp đồng của người này (Số HĐ · Trạng thái · Loại · Hiệu lực · Chức danh · Lương cơ bản · Thao tác).</li>
<li>Bấm <strong>Lập hợp đồng</strong> ở góc phải bảng. Hộp <strong>Lập hợp đồng lao động</strong> mở ra.</li>
<li>Chọn <strong>Loại hợp đồng</strong>. Ô <strong>Pháp nhân</strong> bên cạnh chỉ để xem: hệ thống lấy pháp nhân hiện tại của người này.</li>
<li>Điền <strong>Số hợp đồng</strong> (để trống thì hệ thống lấy mã tự sinh), <strong>Ngày bắt đầu</strong> và <strong>Ngày kết thúc</strong>. Dưới ô ngày kết thúc có hàng nút <strong>Chọn nhanh</strong>: bấm là điền ngày kết thúc tính từ ngày bắt đầu (phải chọn ngày bắt đầu trước).</li>
<li>Điền <strong>Chức danh</strong>, <strong>Địa điểm làm việc</strong>, <strong>Lương cơ bản (đ)</strong>, <strong>Lương đóng BH (đ)</strong>, <strong>Phụ cấp (đ)</strong>, <strong>Ghi chú phụ cấp</strong> (ví dụ <em>ăn trưa, xăng xe, điện thoại</em>) và <strong>Ghi chú</strong>.</li>
<li>Nếu công ty đã khai biến tùy chỉnh, hộp có thêm khối <strong>Thông tin bổ sung cho mẫu</strong>: điền các ô ở đó (xem {ref(BIEN, "Danh sách biến và biến tùy chỉnh của mẫu")}).</li>
<li>Đã có bản hợp đồng ký tay hay bản scan thì kéo thả vào ô <strong>Tệp hợp đồng (bản ký / scan)</strong>, hoặc bấm vào ô để chọn tệp. Ô này <strong>không bắt buộc</strong>; nhận PDF, JPG, PNG, tối đa 50 MB.</li>
<li>Bấm <strong>Lưu</strong>. Hợp đồng mới ở trạng thái <strong>Nháp</strong>. Nếu bạn đã chọn tệp, tệp được tải lên ngay sau khi lưu xong.</li>
</ol>

<h2>Loại hợp đồng và ngày kết thúc</h2>
<table>
<thead><tr><th>Loại hợp đồng</th><th>Ngày kết thúc</th><th>Nút Chọn nhanh</th></tr></thead>
<tbody>
<tr><td><strong>Thử việc</strong></td><td>Bắt buộc</td><td>30 ngày · 60 ngày</td></tr>
<tr><td><strong>Xác định thời hạn</strong></td><td>Bắt buộc. Quá 36 tháng thì hệ thống chỉ <strong>nhắc</strong>, không chặn</td><td>12 tháng · 24 tháng · 36 tháng</td></tr>
<tr><td><strong>Không xác định thời hạn</strong></td><td>Không có ô ngày kết thúc</td><td>Không có</td></tr>
<tr><td><strong>Khoán việc / dịch vụ</strong>, <strong>Cộng tác viên</strong></td><td>Bắt buộc</td><td>3 tháng · 6 tháng · 12 tháng</td></tr>
<tr><td><strong>Khác</strong></td><td>Không bắt buộc</td><td>3 tháng · 6 tháng · 12 tháng</td></tr>
</tbody>
</table>
<p>Nút thử việc tính theo ngày chứ không theo tháng, vì luật giới hạn thời gian thử việc theo ngày (tối đa 60 ngày với việc cần trình độ cao đẳng trở lên). Nút đang khớp với ngày kết thúc đã chọn được tô đậm.</p>

<h2>Cần biết trước khi lưu</h2>
<ul>
<li><strong>Pháp nhân và phòng ban được chụp lại lúc lập.</strong> Người này chuyển công ty hay đổi phòng sau đó thì hợp đồng cũ vẫn giữ pháp nhân cũ, và lúc sinh tệp vẫn dùng mẫu của pháp nhân cũ.</li>
<li>Pháp nhân chưa có mẫu cho loại hợp đồng vừa chọn thì hộp báo <em>Pháp nhân … chưa có mẫu cho loại này</em>, kèm liên kết <strong>Mở màn Mẫu hợp đồng</strong> (nếu bạn có quyền xem mẫu). Bạn vẫn lưu được hợp đồng; chỉ chưa sinh được tệp Word.</li>
<li>Hợp đồng xác định thời hạn dài hơn 36 tháng: lưu xong màn hiện câu nhắc <em>Hợp đồng xác định thời hạn nên không quá 36 tháng (đang là khoảng … tháng).</em> Đây là nhắc, hợp đồng vẫn được lưu.</li>
<li>Không ai tự lập hợp đồng cho chính mình; hồ sơ của bạn cần một người khác trong phòng Nhân sự lập.</li>
<li>Tệp đã chọn mà tải lên bị lỗi thì <strong>hợp đồng vẫn được lưu</strong>. Tải lại bằng mục <strong>Tải lên bản đã ký</strong> trong menu Thao tác của dòng đó, đừng lập lại hợp đồng.</li>
</ul>

<h2>Sửa hợp đồng nháp</h2>
<p>Bấm nút <strong>…</strong> (Thao tác) ở cuối dòng ▸ <strong>Sửa hợp đồng</strong>. Hộp <strong>Sửa hợp đồng</strong> giống hộp lập. Chỉ sửa được khi hợp đồng còn <strong>Nháp</strong>. Hợp đồng đã có bản ký thì dưới ô tệp có dòng <em>Hợp đồng đã có bản ký — chọn tệp mới sẽ thay bản cũ.</em></p>
<p>Sửa nội dung (lương, ngày, giá trị biến…) sau khi đã sinh tệp Word thì <strong>tệp đã sinh bị gỡ</strong>, vì nó không còn khớp nội dung. Sinh lại tệp theo {ref(THAO_TAC, "bài Sinh tệp, ký, hủy và chấm dứt")}.</p>

<h2>Gặp lỗi</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Không thấy tab <strong>Hợp đồng</strong> trong hồ sơ</td><td>Bạn chưa có quyền xem hợp đồng lao động (hợp đồng có lương nên quyền này tách riêng)</td><td>Nhờ quản trị cấp, xem {ref(QUYEN, "bài Quyền")}</td></tr>
<tr><td>Có tab nhưng không thấy nút <strong>Lập hợp đồng</strong></td><td>Thiếu quyền lập hợp đồng, hoặc hồ sơ chưa gắn công ty</td><td>Gắn ô <strong>Công ty</strong> ở tab Chung của hồ sơ rồi lưu; hoặc xin quyền</td></tr>
<tr><td><em>Nhân sự chưa gắn pháp nhân — cập nhật hồ sơ trước khi lập hợp đồng</em></td><td>Hồ sơ chưa có công ty</td><td>Như trên</td></tr>
<tr><td><em>Số hợp đồng "…" đã tồn tại trong pháp nhân này</em></td><td>Số hợp đồng trùng một hợp đồng khác cùng pháp nhân</td><td>Đổi số, hoặc để trống cho hệ thống tự sinh</td></tr>
<tr><td><em>Loại hợp đồng này bắt buộc có ngày kết thúc</em></td><td>Thiếu ngày kết thúc</td><td>Chọn ngày, hoặc bấm một nút Chọn nhanh</td></tr>
<tr><td><em>Ngày kết thúc phải sau hoặc bằng ngày bắt đầu</em></td><td>Nhập ngược hai ngày</td><td>Sửa lại</td></tr>
<tr><td><em>Không được tự lập hợp đồng lao động cho chính mình</em></td><td>Bạn đang lập hợp đồng ở hồ sơ của chính bạn</td><td>Nhờ người khác trong phòng Nhân sự lập</td></tr>
<tr><td><em>Chỉ sửa được hợp đồng ở trạng thái Nháp</em></td><td>Hợp đồng đã ký, đã hủy hoặc đã chấm dứt</td><td>Hợp đồng đã ký không sửa được nữa; cần đổi nội dung thì chấm dứt hợp đồng đó rồi lập hợp đồng mới</td></tr>
</tbody>
</table>""",
        },
        {
            "title": THAO_TAC,
            "icon": "workflow",
            "summary": "Nút ... ở cột Thao tác mở menu nhóm Xem (bản lưu trữ, bản đã ký, tải .docx) · Soạn (Sửa, Sinh tệp, Tải lên bản đã ký) · Trạng thái (Đánh dấu đã ký, Hủy, Chấm dứt / thanh lý) · Xóa hợp đồng",
            "content": f"""<h2>Menu Thao tác của một hợp đồng</h2>
<p>Ở tab <strong>Hợp đồng</strong> của hồ sơ nhân sự, cuối mỗi dòng có một nút nhỏ <strong>…</strong> (rê chuột hiện chữ <em>Thao tác</em>). Bấm vào là mở menu, mỗi mục có biểu tượng và chữ, chia bốn nhóm. Mục nào hiện là do hệ thống quyết định theo trạng thái hợp đồng và quyền của bạn; không có mục nào thì không có nút.</p>
<table>
<thead><tr><th>Nhóm</th><th>Mục</th><th>Hiện khi</th></tr></thead>
<tbody>
<tr><td rowspan="3"><strong>Xem</strong></td><td><strong>Mở bản lưu trữ ở Văn bản</strong></td><td>Hợp đồng đã có bản lưu trữ và bạn mở được nó. Mở ở thẻ trình duyệt mới để không mất phần hồ sơ đang sửa</td></tr>
<tr><td><strong>Xem bản đã ký</strong></td><td>Đã có bản ký / scan</td></tr>
<tr><td><strong>Tải hợp đồng (.docx)</strong></td><td>Đã sinh tệp Word và bạn có quyền in hợp đồng</td></tr>
<tr><td rowspan="3"><strong>Soạn</strong></td><td><strong>Sửa hợp đồng</strong></td><td>Hợp đồng còn Nháp</td></tr>
<tr><td><strong>Sinh tệp hợp đồng</strong> / <strong>Sinh lại tệp</strong></td><td>Hợp đồng còn Nháp</td></tr>
<tr><td><strong>Tải lên bản đã ký</strong> / <strong>Thay bản đã ký</strong></td><td>Hợp đồng Nháp hoặc Đã ký</td></tr>
<tr><td rowspan="3"><strong>Trạng thái</strong></td><td><strong>Đánh dấu đã ký</strong></td><td>Hợp đồng Nháp</td></tr>
<tr><td><strong>Hủy hợp đồng</strong> (chữ đỏ)</td><td>Hợp đồng Nháp</td></tr>
<tr><td><strong>Chấm dứt / thanh lý</strong> (chữ đỏ)</td><td>Hợp đồng Đã ký</td></tr>
<tr><td>(cuối menu)</td><td><strong>Xóa hợp đồng</strong> (chữ đỏ)</td><td>Hợp đồng Nháp hoặc Đã hủy</td></tr>
</tbody>
</table>
<p>Trên điện thoại, mỗi hợp đồng là một thẻ, nút <strong>…</strong> ở góc thẻ mở đúng menu này.</p>

<h2>Sinh tệp Word từ mẫu</h2>
<ol>
<li>Mở menu ▸ <strong>Sinh tệp hợp đồng</strong>. Hộp <strong>Sinh tệp hợp đồng</strong> mở ra.</li>
<li>Ô <strong>Mẫu hợp đồng</strong> chỉ liệt kê mẫu <strong>đang dùng</strong> của <strong>đúng pháp nhân và đúng loại</strong> của hợp đồng này. Chỉ có một mẫu thì hệ thống chọn sẵn; sinh lại thì chọn sẵn mẫu đã dùng lần trước.</li>
<li>Bấm <strong>Sinh tệp</strong>. Hệ thống điền thông tin từ hồ sơ và hợp đồng vào mẫu, ra một tệp .docx.</li>
<li>Tải tệp về bằng menu ▸ <strong>Tải hợp đồng (.docx)</strong>, in ra cho hai bên ký.</li>
</ol>
<p>Sinh lại thì hộp ghi <em>Tệp đã sinh trước đó sẽ được thay bằng tệp mới.</em> Không có mẫu nào thì hộp báo <em>Pháp nhân … chưa có mẫu cho loại hợp đồng này.</em> kèm liên kết <strong>Mở màn Mẫu hợp đồng</strong>: xem {ref(MAU, "Tải lên và soạn mẫu Word theo pháp nhân")}.</p>

<h2>Tải lên bản đã ký</h2>
<p>Mở menu ▸ <strong>Tải lên bản đã ký</strong> (đã có bản ký thì là <strong>Thay bản đã ký</strong>), chọn tệp PDF, JPG hoặc PNG, tối đa 50 MB. Có thể làm cả trước lẫn sau khi đánh dấu đã ký. Lúc lập hợp đồng bạn cũng chọn được tệp ngay trong hộp lập (xem {ref(LAP, "bài Lập hợp đồng")}). Bản ký được chép sang bản lưu trữ ở Văn bản.</p>

<h2>Đánh dấu đã ký</h2>
<ol>
<li>Mở menu ▸ <strong>Đánh dấu đã ký</strong>. Hộp hỏi <strong>Ngày ký</strong> (điền sẵn hôm nay).</li>
<li>Bấm <strong>Xác nhận</strong>. Hợp đồng chuyển sang <strong>Đã ký – hiệu lực</strong>.</li>
</ol>
<ul>
<li>Ký <strong>không bắt buộc</strong> phải có tệp bản ký; tải lên sau cũng được.</li>
<li>Mẫu có biến tùy chỉnh <strong>bắt buộc</strong> mà hợp đồng còn để trống thì bị chặn, câu báo nêu tên ô còn thiếu (xem bảng lỗi dưới).</li>
<li>Nếu đây là hợp đồng đang có hiệu lực mới nhất của người đó, lương và phụ cấp trên hợp đồng được tự chép sang hồ sơ: xem {ref(SALARY, "Nhập lương ở hồ sơ và xem lương của mình")}.</li>
<li>Đã ký thì <strong>không sửa nội dung được nữa</strong>. Bản lưu trữ ở Văn bản tự chuyển sang Có hiệu lực.</li>
</ul>

<h2>Hủy hoặc chấm dứt</h2>
<table>
<thead><tr><th>Mục</th><th>Dùng khi</th><th>Hộp hỏi gì</th></tr></thead>
<tbody>
<tr><td><strong>Hủy hợp đồng</strong></td><td>Bản nháp lập nhầm hay không ký nữa</td><td><strong>Lý do hủy</strong> (bắt buộc, tối đa 500 ký tự)</td></tr>
<tr><td><strong>Chấm dứt / thanh lý</strong></td><td>Hợp đồng đã ký nhưng kết thúc trước hạn, hoặc thanh lý</td><td><strong>Ngày chấm dứt</strong> (không trước ngày bắt đầu) và <strong>Lý do chấm dứt</strong> (bắt buộc)</td></tr>
</tbody>
</table>
<p>Hai thao tác này <strong>không hoàn tác được</strong> (hộp ghi rõ). Hợp đồng chỉ hết hạn tự nhiên thì <strong>không cần</strong> bấm gì: trạng thái tự đổi sang <strong>Hết hạn</strong> khi qua ngày kết thúc.</p>

<h2>Xóa hợp đồng</h2>
<p>Mở menu ▸ <strong>Xóa hợp đồng</strong>, xác nhận <strong>Xóa</strong> trong hộp <em>Xóa hợp đồng</em>. Chỉ xóa được hợp đồng <strong>Nháp</strong> hoặc <strong>Đã hủy</strong>; tệp đã sinh và bản ký cũng bị xóa theo. Hợp đồng đã ký không xóa được, chỉ chấm dứt.</p>

<h2>Gặp lỗi</h2>
<table>
<thead><tr><th>Câu bạn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Hợp đồng còn thiếu: … — mở "Sửa hợp đồng" để nhập trước khi …</em></td><td>Mẫu dùng một biến tùy chỉnh bắt buộc mà hợp đồng chưa điền</td><td>Menu ▸ <strong>Sửa hợp đồng</strong>, điền ô đó ở khối <strong>Thông tin bổ sung cho mẫu</strong>, lưu rồi làm lại</td></tr>
<tr><td><em>Chỉ sinh được tệp khi hợp đồng ở trạng thái Nháp</em></td><td>Hợp đồng đã ký hoặc đã đóng</td><td>Hợp đồng đã ký thì dùng bản đã sinh trước đó hoặc bản ký đã tải lên</td></tr>
<tr><td><em>Mẫu hợp đồng đã ngừng dùng</em></td><td>Mẫu vừa bị tắt</td><td>Chọn mẫu khác, hoặc nhờ người quản lý mẫu bật lại</td></tr>
<tr><td><em>Hợp đồng chưa có tệp — hãy sinh tệp từ mẫu trước</em></td><td>Chưa sinh tệp Word, hoặc tệp đã bị gỡ vì bạn sửa nội dung sau khi sinh</td><td>Menu ▸ <strong>Sinh tệp hợp đồng</strong></td></tr>
<tr><td><em>Bản ký chỉ nhận PDF, JPG hoặc PNG</em> / <em>Bản ký lớn hơn 50 MB</em></td><td>Tệp sai loại hoặc quá lớn</td><td>Xuất lại bản scan thành PDF, hoặc giảm độ phân giải</td></tr>
<tr><td><em>Chỉ xóa được hợp đồng Nháp hoặc Đã hủy</em></td><td>Hợp đồng đã ký hoặc đã chấm dứt</td><td>Dùng <strong>Chấm dứt / thanh lý</strong> nếu cần đóng</td></tr>
<tr><td>Không thấy mục <strong>Tải hợp đồng (.docx)</strong> dù đã sinh tệp</td><td>Tải bản Word cần thêm quyền <strong>In</strong> hợp đồng lao động</td><td>Xin quản trị cấp, xem {ref(QUYEN, "bài Quyền")}</td></tr>
</tbody>
</table>""",
        },
        {
            "title": MAU,
            "icon": "book-open",
            "summary": "Nhân sự ▸ Danh mục ▸ Mẫu hợp đồng: Tải lên mẫu .docx gắn một pháp nhân + một loại hợp đồng, menu ... (Soạn nội dung, Tải tệp mẫu, Sửa thông tin, Thay tệp mẫu, Ngừng dùng, Xóa mẫu), soạn trên web với khung Chèn biến, sửa lỗi biến lạ",
            "content": f"""<h2>Mẫu hợp đồng là gì</h2>
<p>Mỗi mẫu là một tệp Word (.docx) trong đó những chỗ cần điền được gõ thành <strong>biến</strong> dạng <code>{VAR_SAMPLE}</code>. Lúc sinh tệp, hệ thống thay từng biến bằng thông tin của người lao động và của hợp đồng. Mỗi mẫu gắn với <strong>một pháp nhân</strong> và <strong>một loại hợp đồng</strong>, nên mỗi công ty dùng đúng mẫu của mình.</p>

<h2>Mở màn Mẫu hợp đồng</h2>
<ul>
<li>Vào <strong>Nhân sự ▸ Danh mục ▸ Mẫu hợp đồng</strong>. Trang mở ngay trong phân hệ Nhân sự (thanh đường dẫn <em>Nhân sự › Danh mục › Mẫu hợp đồng</em>), không nhảy sang phân hệ khác.</li>
<li>Văn thư cũng mở được cùng bảng này ở <strong>Văn bản ▸ Thiết lập văn bản</strong> ▸ tab <strong>Thư viện văn bản mẫu</strong> ▸ mục <strong>Mẫu hợp đồng lao động</strong>. Hai chỗ là một dữ liệu.</li>
<li>Bảng có ô <em>Tìm theo tên mẫu…</em> và ba ô lọc: pháp nhân (<em>Tất cả pháp nhân</em>), loại (<em>Tất cả loại HĐ</em>), trạng thái (<em>Đang dùng</em> / <em>Ngừng</em>). Các cột: <strong>ID · Tên mẫu · Pháp nhân · Loại HĐ · Tệp gốc · Số HĐ đã dùng · Trạng thái · Ngày tạo · Thao tác</strong>.</li>
</ul>

<h2>Tải lên một mẫu mới</h2>
<ol>
<li>Soạn tệp Word như hợp đồng thật, chỗ nào cần điền thì gõ biến, ví dụ <code>{{{{ ho_ten }}}}</code>. Danh sách mã biến xem bằng nút <strong>Danh sách biến</strong> ở góc phải trang (xem {ref(BIEN, "Danh sách biến và biến tùy chỉnh của mẫu")}).</li>
<li>Bấm <strong>Tải lên mẫu</strong> ở góc phải trang. Hộp <strong>Tải lên mẫu hợp đồng</strong> mở ra.</li>
<li>Điền <strong>Tên mẫu</strong>, chọn <strong>Pháp nhân</strong> (ô chọn hiện kèm mã pháp nhân vì có công ty trùng tên), chọn <strong>Loại hợp đồng</strong>, ghi <strong>Ghi chú</strong> nếu cần.</li>
<li>Kéo thả tệp vào ô, hoặc bấm vào ô để chọn. Chỉ nhận .docx, tối đa 10 MB.</li>
<li>Bấm <strong>Tải lên</strong>. Hệ thống kiểm tệp trước khi nhận.</li>
</ol>
<p>Tên mẫu không được trùng một mẫu khác trong cùng pháp nhân.</p>

<h2>Mẫu bị từ chối vì biến lạ</h2>
<p>Tệp có biến không nằm trong danh sách thì hộp báo đỏ và liệt kê từng biến lạ. Có hai nguyên nhân thường gặp:</p>
<ul>
<li><strong>Gõ sai mã biến</strong>: so lại với <strong>Danh sách biến</strong>; biến chưa có thì quản trị thêm biến tùy chỉnh trước.</li>
<li><strong>Word tách biến thành nhiều đoạn</strong> khi bạn đổi định dạng giữa chừng (in đậm nửa biến, đổi màu…). Hộp có dòng mẹo: xóa rồi gõ lại biến liền một lần, không đổi chữ đậm / nghiêng / màu ở giữa, rồi tải lại.</li>
</ul>
<p>Mẫu chỉ được chứa <strong>biến đơn</strong> dạng <code>{VAR_SAMPLE}</code>. Câu lệnh, vòng lặp, macro, liên kết ngoài và đối tượng nhúng đều bị chặn để tệp mẫu không làm treo máy chủ.</p>

<h2>Menu Thao tác của một mẫu</h2>
<p>Cuối mỗi dòng có nút <strong>…</strong>. Mục nào hiện tùy quyền của bạn:</p>
<table>
<thead><tr><th>Nhóm</th><th>Mục</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td rowspan="2"><strong>Nội dung</strong></td><td><strong>Soạn nội dung</strong> (người chỉ xem thì là <strong>Xem nội dung</strong>)</td><td>Mở trình soạn trên web (mục dưới)</td></tr>
<tr><td><strong>Tải tệp mẫu</strong></td><td>Tải tệp .docx hiện tại về máy</td></tr>
<tr><td rowspan="3"><strong>Quản lý</strong></td><td><strong>Sửa thông tin</strong></td><td>Đổi tên mẫu, loại hợp đồng, ghi chú. <strong>Pháp nhân không đổi được</strong>; cần mẫu cho pháp nhân khác thì tải lên mẫu mới</td></tr>
<tr><td><strong>Thay tệp mẫu</strong></td><td>Chọn tệp .docx mới thay tệp cũ, bấm <strong>Thay tệp</strong>. Tệp mới cũng bị kiểm biến như lúc tải lên</td></tr>
<tr><td><strong>Ngừng dùng</strong> / <strong>Bật dùng</strong></td><td>Mẫu ngừng dùng không còn hiện trong hộp Sinh tệp; hợp đồng đã sinh từ nó giữ nguyên</td></tr>
<tr><td>(cuối menu)</td><td><strong>Xóa mẫu</strong></td><td>Chỉ xóa được mẫu chưa có hợp đồng nào dùng. Đã có thì hộp nhắc chọn <strong>Ngừng dùng</strong></td></tr>
</tbody>
</table>

<h2>Soạn nội dung mẫu ngay trên web</h2>
<ol>
<li>Menu ▸ <strong>Soạn nội dung</strong>. Trang <em>Soạn mẫu "…"</em> mở ra, dòng dưới tiêu đề ghi pháp nhân và loại hợp đồng.</li>
<li>Sửa chữ, bảng, ảnh như soạn văn bản thường. Muốn chèn một biến, đặt con trỏ ở chỗ cần điền, tìm biến ở khung <strong>Chèn biến</strong> bên phải (ô <em>Tìm biến…</em>) rồi bấm vào biến đó.</li>
<li>Bấm <strong>Lưu</strong>. Lần lưu đầu, hệ thống hỏi lại vì lưu trên web sẽ dựng lại tệp Word: chữ, bảng, ảnh, căn lề và lề trái / phải được giữ, nhưng <strong>đầu trang / chân trang và một số định dạng riêng của Word có thể mất</strong>. Nên bấm <strong>Tải bản Word</strong> để giữ bản gốc trước khi lưu lần đầu.</li>
<li>Bấm <strong>Quay lại</strong> để về danh sách mẫu. Còn chữ chưa lưu thì hệ thống hỏi <em>Bỏ thay đổi?</em> trước khi rời trang.</li>
</ol>
<p>Lưu mà nội dung có biến không nằm trong danh sách thì đầu trang báo <em>Biến không có trong danh sách: …</em>; xóa hoặc thay bằng biến ở khung <strong>Chèn biến</strong> rồi lưu lại. Mẫu cần đầu trang / chân trang phức tạp thì nên sửa bằng Word rồi dùng <strong>Thay tệp mẫu</strong>.</p>

<p>Quyền cần có để xem, tải lên, sửa, xóa mẫu: {ref(QUYEN, "Quyền xem, lập hợp đồng và quản lý mẫu")}.</p>""",
        },
        {
            "title": BIEN,
            "icon": "tags",
            "summary": "Mẫu hợp đồng ▸ nút Danh sách biến: biến hệ thống lấy từ hồ sơ, biến tùy chỉnh (Chữ, Chữ nhiều dòng, Số, Ngày, Tiền) nhập tay ở khối Thông tin bổ sung cho mẫu; Bắt buộc, Giá trị mặc định, Ngừng dùng khác Xóa",
            "content": f"""<h2>Hai loại biến</h2>
<p>Mở <strong>Nhân sự ▸ Danh mục ▸ Mẫu hợp đồng</strong> ▸ nút <strong>Danh sách biến</strong> ở góc phải. Trang <strong>Danh sách biến mẫu hợp đồng</strong> liệt kê mọi biến gõ được vào tệp Word, dùng chung cho mọi pháp nhân.</p>
<table>
<thead><tr><th></th><th>Biến hệ thống</th><th>Biến tùy chỉnh</th></tr></thead>
<tbody>
<tr><td>Ai tạo</td><td>Có sẵn (họ tên, ngày sinh, CCCD, lương trên hợp đồng, ngày bắt đầu…)</td><td>Phòng Nhân sự tự thêm</td></tr>
<tr><td>Giá trị lấy từ đâu</td><td>Tự lấy từ hồ sơ nhân sự và từ hợp đồng</td><td><strong>Nhập tay theo từng hợp đồng</strong>, ở khối <strong>Thông tin bổ sung cho mẫu</strong> trong hộp Lập / Sửa hợp đồng</td></tr>
<tr><td>Sửa được gì</td><td>Chỉ tên hiển thị, mô tả và công tắc <strong>Ẩn khỏi danh sách hướng dẫn</strong>. Không đổi mã, không xóa</td><td>Mọi thứ; mã và kiểu bị khóa khi đã có mẫu hoặc hợp đồng dùng</td></tr>
</tbody>
</table>
<p>Bảng có ô <em>Tìm theo mã hoặc tên biến…</em>, lọc theo nguồn, kiểu và trạng thái. Các cột: <strong>Biến · Tên hiển thị · Nhóm · Kiểu · Ví dụ · Bắt buộc · Số mẫu dùng · Trạng thái · Thao tác</strong>. Cột <strong>Biến</strong> là đúng chữ cần gõ vào tệp Word.</p>

<h2>Thêm một biến tùy chỉnh</h2>
<p>Ví dụ: mẫu của một công ty có dòng phụ cấp xăng xe riêng mà hồ sơ không có ô nào giữ.</p>
<ol>
<li>Bấm <strong>Thêm biến</strong>. Hộp <strong>Thêm biến tùy chỉnh</strong> mở ra.</li>
<li><strong>Mã biến</strong>: chữ thường không dấu, số và dấu gạch dưới, bắt đầu bằng chữ, 2–40 ký tự, ví dụ <em>phu_cap_xang_xe</em>. Không trùng mã biến hệ thống, không có hai dấu gạch dưới liền nhau, không kết thúc bằng dấu gạch dưới.</li>
<li><strong>Tên hiển thị</strong> (bắt buộc) là nhãn ô nhập trong hộp hợp đồng, ví dụ <em>Phụ cấp xăng xe</em>. <strong>Mô tả</strong> hiện dưới ô nhập để người lập biết ghi gì.</li>
<li>Chọn <strong>Kiểu giá trị</strong> (bảng dưới), ghi <strong>Ví dụ</strong>, <strong>Giá trị mặc định</strong> nếu có, <strong>Thứ tự</strong> hiện trong hộp.</li>
<li>Bật <strong>Bắt buộc</strong> nếu hợp đồng nào dùng mẫu chứa biến này cũng phải điền. Giữ <strong>Đang dùng</strong> bật.</li>
<li>Bấm <strong>Lưu</strong>, rồi gõ biến vào tệp Word (ví dụ <code>{VAR_MONEY}</code>) và tải mẫu lên hoặc thay tệp mẫu.</li>
</ol>

<h2>Năm kiểu giá trị</h2>
<table>
<thead><tr><th>Kiểu</th><th>Nhập thế nào</th><th>In ra mẫu thế nào</th></tr></thead>
<tbody>
<tr><td><strong>Chữ</strong></td><td>Một dòng chữ</td><td>Đúng như gõ</td></tr>
<tr><td><strong>Chữ nhiều dòng</strong></td><td>Ô nhiều dòng</td><td>Mỗi lần xuống dòng thành một ngắt dòng trong Word</td></tr>
<tr><td><strong>Số</strong></td><td>Số không âm, tối đa 2 chữ số lẻ</td><td>Kiểu Việt Nam, ví dụ <em>1.234,5</em></td></tr>
<tr><td><strong>Ngày</strong></td><td>Chọn ngày</td><td><em>dd/mm/yyyy</em></td></tr>
<tr><td><strong>Tiền</strong></td><td>Số đồng nguyên, từ 0 đến 1.000 tỷ</td><td>Ví dụ <em>15.000.000</em>. Hệ thống <strong>tự có thêm biến đọc bằng chữ</strong>: thêm đuôi <em>_bang_chu</em> vào mã, ví dụ <code>{VAR_MONEY_WORDS}</code></td></tr>
</tbody>
</table>

<h2>Bắt buộc và giá trị mặc định</h2>
<ul>
<li><strong>Giá trị mặc định được chép vào hợp đồng lúc lập</strong> (hộp Lập điền sẵn). Đổi giá trị mặc định về sau <strong>không đổi</strong> các hợp đồng đã lập.</li>
<li><strong>Bắt buộc</strong> không chặn lưu nháp. Nó chặn hai bước: <strong>Sinh tệp</strong> (chỉ khi mẫu được chọn thật sự có biến đó) và <strong>Đánh dấu đã ký</strong>. Câu báo nêu tên ô còn thiếu. Với kiểu Số và Tiền, số 0 là giá trị thật; chỉ ô để trống mới là chưa nhập.</li>
<li>Trong hộp hợp đồng, ô bắt buộc có dấu sao và dòng <em>Bắt buộc khi sinh tệp (lưu nháp vẫn để trống được).</em></li>
</ul>

<h2>Ngừng dùng khác Xóa</h2>
<table>
<thead><tr><th></th><th>Ngừng dùng</th><th>Xóa</th></tr></thead>
<tbody>
<tr><td>Cách làm</td><td>Nút <strong>Ngừng dùng</strong> ở cột Thao tác (bấm lại là <strong>Bật lại</strong>), hoặc tắt <strong>Đang dùng</strong> trong hộp Sửa biến</td><td>Nút <strong>Xóa</strong> ở cột Thao tác</td></tr>
<tr><td>Sau đó</td><td>Biến không còn ở ô nhập và ở khung <strong>Chèn biến</strong>; mẫu mới không nhận nó. Mẫu cũ đã chứa nó vẫn sinh tệp được, giá trị đã lưu vẫn in ra và hiện chỉ đọc trong hộp Sửa hợp đồng, kèm dòng <em>Biến đã ngừng dùng — vẫn được in vào mẫu cũ, không sửa được.</em></td><td>Biến biến mất hẳn</td></tr>
<tr><td>Khi nào được</td><td>Luôn được</td><td>Chỉ khi chưa mẫu nào chứa và chưa hợp đồng nào (kể cả đã xóa) giữ giá trị. Đang dùng thì bị chặn, câu báo nêu số mẫu / số hợp đồng; hãy chọn <strong>Ngừng dùng</strong></td></tr>
</tbody>
</table>
<p>Biến hệ thống không ngừng dùng hay xóa được; muốn nó khỏi hiện ở khung <strong>Chèn biến</strong> thì dùng nút <strong>Ẩn khỏi danh sách hướng dẫn</strong> (biến ẩn vẫn dùng được trong mẫu).</p>

<h2>Ai thêm, sửa được biến</h2>
<p>Danh sách biến dùng chung cho mọi công ty, nên chỉ người có quyền sửa mẫu hợp đồng với phạm vi <strong>tất cả pháp nhân</strong> mới thêm, sửa, xóa được biến. Người Nhân sự của riêng một pháp nhân chỉ xem và dùng; đầu trang ghi <em>Chỉ người có phạm vi "tất cả pháp nhân" mới thêm, sửa, xóa được biến.</em> Xem {ref(QUYEN, "bài Quyền")}.</p>""",
        },
        {
            "title": CANH_BAO,
            "icon": "bell",
            "summary": "Hợp đồng đã ký sắp hết hạn trong 30 ngày (hoặc đã quá hạn) hiện ở chuông, Trang cá nhân ▸ Việc cần làm và thẻ Hợp đồng lao động sắp hết hạn ở Tổng quan Nhân sự; đỏ khi còn 15 ngày; không báo khi đã có hợp đồng nối tiếp hoặc đã nghỉ việc",
            "content": f"""<h2>Hệ thống báo ở đâu</h2>
<p>Hợp đồng lao động sắp hết hạn được báo ở <strong>ba chỗ</strong>, cùng một danh sách:</p>
<table>
<thead><tr><th>Chỗ</th><th>Thấy gì</th></tr></thead>
<tbody>
<tr><td><strong>Chuông thông báo</strong></td><td>Mỗi hợp đồng một dòng, ví dụ <em>HĐLĐ còn 12 ngày: Nguyễn Văn A (NSU101) · HD0007 (hết 24/11/2026)</em>, <em>HĐLĐ hết hạn HÔM NAY: …</em> hoặc <em>HĐLĐ ĐÃ HẾT HẠN 5 ngày: …</em>. Bấm vào là mở thẳng tab <strong>Hợp đồng</strong> của hồ sơ người đó</td></tr>
<tr><td><strong>Trang cá nhân ▸ Việc cần làm</strong></td><td>Cùng các dòng đó, loại <strong>HĐ lao động hết hạn</strong> (lọc được bằng ô loại việc). Đây là chỗ <strong>tắt được</strong> một dòng: bấm đánh dấu đã hoàn thành ở dòng đó</td></tr>
<tr><td><strong>Nhân sự ▸ Tổng quan</strong>, thẻ <strong>Hợp đồng lao động sắp hết hạn</strong></td><td>Danh sách người, mã hợp đồng, loại, ngày hết, kèm nhãn số ngày còn lại; dòng mô tả đếm tổng và số đã quá hạn. Bấm một dòng để mở tab Hợp đồng của người đó. Không có gì thì thẻ ghi <em>Chưa có hợp đồng nào cần gia hạn.</em></td></tr>
</tbody>
</table>

<h2>Hợp đồng nào bị báo</h2>
<ul>
<li>Hợp đồng <strong>Đã ký</strong>, có ngày kết thúc, nằm trong phạm vi hồ sơ bạn được xem, và hết hạn trong <strong>30 ngày tới</strong> hoặc <strong>đã quá hạn</strong>. Người vẫn đi làm mà hợp đồng đã hết là đang không có hợp đồng, nên hệ thống báo tới khi xử lý xong.</li>
<li><strong>Đỏ</strong> khi còn từ <strong>15 ngày</strong> trở xuống hoặc đã quá hạn (luật buộc báo trước cho người lao động ít nhất 15 ngày); còn lại là vàng. Một dòng vàng bạn đã tắt ở Việc cần làm sẽ hiện lại khi chuyển sang đỏ.</li>
<li>Hai con số 30 và 15 đổi được ở <strong>Nhân sự ▸ Thiết lập</strong>, tab <strong>Cài đặt nhân sự</strong>, rồi tab <strong>Hợp đồng lao động</strong> trong màn: xem {ref(HR_SETTINGS, "Cài đặt nhân sự")}.</li>
</ul>

<h2>Khi nào hết bị báo</h2>
<ul>
<li>Người đó đã có <strong>hợp đồng nối tiếp</strong> bắt đầu sau hợp đồng cũ: hợp đồng mới đã ký thì luôn thôi báo; hợp đồng mới còn nháp thì chỉ thôi báo khi hợp đồng cũ <strong>chưa</strong> hết hạn (nháp bị quên không che được hợp đồng đã quá hạn).</li>
<li>Người đó đã <strong>nghỉ việc</strong>.</li>
<li>Hợp đồng được <strong>chấm dứt / thanh lý</strong> (xem {ref(THAO_TAC, "bài menu Thao tác")}).</li>
</ul>
<p>Cách gia hạn thông thường: lập hợp đồng mới nối tiếp theo {ref(LAP, "bài Lập hợp đồng")}, sinh tệp, ký rồi bấm <strong>Đánh dấu đã ký</strong>.</p>

<h2>Cần lưu ý</h2>
<ul>
<li>Hệ thống tính lúc bạn mở trang, theo ngày giờ Việt Nam; không gửi email.</li>
<li>Không có quyền xem hợp đồng lao động thì không thấy thẻ ở Tổng quan và không nhận dòng chuông nào.</li>
<li>Cần danh sách toàn công ty để rà theo tháng, theo phòng ban, xuất Excel: dùng báo cáo, xem {ref(BC_HET_HAN, "Theo dõi hợp đồng lao động sắp hết hạn")}.</li>
</ul>""",
        },
        {
            "title": CUA_TOI,
            "icon": "users",
            "summary": "Trang cá nhân ▸ nhóm Hồ sơ ▸ Hợp đồng của tôi: bảng chỉ xem các hợp đồng đã ký / đã chấm dứt của chính mình, nút Tải bản mềm (.docx) và Xem / tải bản đã ký",
            "content": f"""<h2>Xem lại hợp đồng của tôi</h2>
<p>Người lao động tự xem lại các hợp đồng lao động của <strong>chính mình</strong>, không cần nhờ phòng Nhân sự gửi lại.</p>
<ol>
<li>Mở menu tài khoản ở góc phải ▸ <strong>Trang cá nhân</strong>.</li>
<li>Ở nhóm <strong>Hồ sơ</strong>, chọn <strong>Hợp đồng của tôi</strong>.</li>
<li>Bảng hiện các cột <strong>Số HĐ · Trạng thái · Loại · Hiệu lực · Chức danh · Lương cơ bản · Tệp</strong>.</li>
<li>Ở cột <strong>Tệp</strong>: bấm <strong>Tải bản mềm (.docx)</strong> để tải tệp Word phòng Nhân sự đã sinh, hoặc <strong>Xem / tải bản đã ký</strong> để tải bản ký / scan. Hợp đồng chưa có tệp nào thì ghi <em>Chưa có tệp</em>.</li>
</ol>

<h2>Thấy những hợp đồng nào</h2>
<ul>
<li>Chỉ hợp đồng <strong>đã ký</strong> (kể cả đã hết hạn) và <strong>đã chấm dứt / thanh lý</strong>. Hợp đồng còn nháp, đã hủy hay đã xóa không hiện.</li>
<li>Chưa có hợp đồng đã ký nào thì bảng ghi <em>Bạn chưa có hợp đồng lao động nào đã ký.</em></li>
<li>Bảng <strong>chỉ để xem</strong>: không sửa, không tải tệp lên, không đổi trạng thái. Thấy sai thì báo phòng Nhân sự.</li>
<li>Mục này chỉ có khi tài khoản đã gắn với hồ sơ nhân sự. Không thấy mục <strong>Hợp đồng của tôi</strong> thì liên hệ phòng Nhân sự để gắn tài khoản.</li>
<li>Không cần quyền gì thêm: ai cũng xem được hợp đồng của chính mình, và không xem được của người khác.</li>
</ul>
<p>Bản lưu trữ của hợp đồng ở phân hệ Văn bản: người lao động cũng đọc được bản lưu trữ của chính mình khi hợp đồng đã ký hoặc đã chấm dứt, nhưng mở màn Văn bản còn cần quyền xem văn bản của vai trò. Tải tệp ngay ở Trang cá nhân thì không cần quyền đó. Xem {ref(VB_LUU_TRU, "Bản lưu trữ hợp đồng lao động và nút Ban hành")}.</p>""",
        },
        {
            "title": QUYEN,
            "icon": "key-round",
            "summary": "Hai khóa quyền Hợp đồng lao động (có lương) và Mẫu hợp đồng lao động: Xem, Tạo, Sửa, Xóa, In; phạm vi theo pháp nhân / phòng ban; sửa danh sách biến cần phạm vi tất cả pháp nhân",
            "content": f"""<h2>Hai khóa quyền</h2>
<p>Quản trị cấp ở <strong>Quản trị ▸ Phân quyền tài khoản</strong> ▸ tab <strong>Vai trò &amp; quyền</strong>, trong ma trận của vai trò:</p>
<table>
<thead><tr><th>Dòng trong ma trận</th><th>Cột</th><th>Cho làm gì</th></tr></thead>
<tbody>
<tr><td rowspan="5"><strong>Hợp đồng lao động (có lương)</strong></td><td>Xem</td><td>Thấy tab <strong>Hợp đồng</strong> trong hồ sơ, xem và tải bản đã ký, nhận cảnh báo sắp hết hạn</td></tr>
<tr><td>Tạo</td><td>Nút <strong>Lập hợp đồng</strong></td></tr>
<tr><td>Sửa</td><td>Sửa hợp đồng nháp, sinh tệp, tải bản ký, đánh dấu đã ký, hủy, chấm dứt</td></tr>
<tr><td>Xóa</td><td>Xóa hợp đồng nháp hoặc đã hủy</td></tr>
<tr><td>In</td><td>Tải tệp Word đã sinh (<strong>Tải hợp đồng (.docx)</strong>)</td></tr>
<tr><td rowspan="3"><strong>Mẫu hợp đồng lao động</strong></td><td>Xem</td><td>Mở <strong>Danh mục ▸ Mẫu hợp đồng</strong> và <strong>Danh sách biến</strong>, tải tệp mẫu</td></tr>
<tr><td>Tạo / Sửa</td><td>Tải lên mẫu, soạn nội dung, sửa thông tin, thay tệp, ngừng dùng</td></tr>
<tr><td>Xóa</td><td>Xóa mẫu chưa dùng</td></tr>
</tbody>
</table>
<p><strong>Hợp đồng có lương</strong>, nên khóa này tách riêng khỏi quyền xem hồ sơ nhân sự. Người chỉ xem được hồ sơ thì không thấy tab Hợp đồng. Vai trò mẫu <strong>Nhân sự — Hồ sơ nhân viên</strong> có sẵn cả hai khóa.</p>

<h2>Phạm vi dữ liệu</h2>
<ul>
<li>Hợp đồng lọc theo <strong>pháp nhân</strong> và <strong>phòng ban</strong> của hợp đồng (chụp lúc lập), và theo chính người lao động. Ví dụ Nhân sự của công ty A chỉ thấy và lập hợp đồng cho người của công ty A.</li>
<li>Mẫu hợp đồng lọc theo <strong>pháp nhân</strong> của mẫu.</li>
<li><strong>Danh sách biến</strong> dùng chung mọi công ty: thêm, sửa, xóa biến cần quyền <strong>Sửa</strong> / <strong>Xóa</strong> Mẫu hợp đồng lao động <strong>với phạm vi tất cả pháp nhân</strong>. Người có phạm vi một pháp nhân chỉ xem và dùng biến.</li>
<li>Người lao động xem hợp đồng của chính mình ở Trang cá nhân không cần khóa nào (xem {ref(CUA_TOI, "Hợp đồng của tôi")}).</li>
</ul>

<h2>Lưu ý khi đưa vào dùng</h2>
<ul>
<li>Vai trò cũ trên hệ đang chạy <strong>không tự có</strong> hai khóa này; quản trị phải tick tay cho đúng vai trò.</li>
<li>Người đang đăng nhập giữ quyền cũ tới khi đăng xuất rồi đăng nhập lại; vừa được cấp mà vẫn không thấy tab thì đăng nhập lại.</li>
<li>Thứ tự dựng: khai pháp nhân và loại hợp đồng cần dùng ▸ {ref(MAU, "tải lên mẫu cho từng pháp nhân")} ▸ thêm {ref(BIEN, "biến tùy chỉnh")} nếu mẫu cần ▸ cấp quyền ▸ phòng Nhân sự {ref(LAP, "lập hợp đồng")}.</li>
</ul>""",
        },
    ],
}


def _tree_titles(node: dict) -> list[str]:
    """Mọi tiêu đề trong cây (gồm gốc), theo thứ tự duyệt."""
    titles = [node["title"]]
    for child in node.get("children", []):
        titles.extend(_tree_titles(child))
    return titles


def check_unique_titles(tree: dict) -> None:
    """Chặn trước khi ghi nếu một tiêu đề của cây này đã có ở cây KHÁC (trùng tiêu đề = trùng slug trên portal)."""
    titles = _tree_titles(tree)
    dup_inside = {t for t in titles if titles.count(t) > 1}
    if dup_inside:
        sys.exit(f"Tiêu đề lặp ngay trong cây: {sorted(dup_inside)}")
    db = SessionLocal()
    try:
        rows = db.query(HelpArticle.id, HelpArticle.parent_id, HelpArticle.title).all()
        root = next((r for r in rows if r.parent_id is None and r.title == tree["title"]), None)
        own: set[int] = set()
        if root is not None:
            own, frontier = {root.id}, [root.id]
            while frontier:
                pid = frontier.pop()
                for r in rows:
                    if r.parent_id == pid and r.id not in own:
                        own.add(r.id)
                        frontier.append(r.id)
        clash = sorted({r.title for r in rows if r.title in titles and r.id not in own})
        if clash:
            sys.exit(f"Tiêu đề đã có ở cây khác, đổi tiêu đề trước khi seed: {clash}")
    finally:
        db.close()


if __name__ == "__main__":
    check_unique_titles(TREE)
    rebuild_tree(TREE)
