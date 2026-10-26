# -*- coding: utf-8 -*-
"""Viết lại bài HDSD «AI riêng của bạn làm được gì trong ERP: công cụ và skill» cho khớp prod 26/10/2026 (main 51c9a2b6).
MỘT LỆNH: ghi đè đúng bài cùng tiêu đề dưới thẻ «Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI» rồi nạp kho vector
cho bài đó (khuôn `help_seed_common.upsert_articles`) — không dựng lại cả cây.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_ai_rieng_lam_duoc_gi.py --dry-run
    docker compose exec -T api python scripts/seed_help_ai_rieng_lam_duoc_gi.py

⚠️ Bảng nhóm phải khớp `app/modules/agent_hub/mcp_settings.py` (GROUPS) và cột *Trên ERP hiện nay* khớp cấu hình G7 đang
bật trên prod. `seed_help_ket_noi_ai_mcp.py` (dựng cả cây) lấy SUMMARY / CONTENT từ tệp này — sửa một chỗ.
"""
from help_seed_common import ref, run_article_upsert

ROOT = "Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI"
TITLE = "AI riêng của bạn làm được gì trong ERP: công cụ và skill"
NHAT_KY = "Nhật ký lượt gọi của AI riêng và lỗi thường gặp khi nối"
from seed_help_ket_noi_ai_cach_1 import OAUTH, TAO_KHOA  # noqa: E402 — tiêu đề Cách 1 / Cách 2 (26/10)

SUMMARY = ("Công cụ theo nhóm (nhóm nào đang bật, nhóm nào nhờ quản trị bật), việc có xác nhận hai bước, câu hỏi mẫu theo "
           "phòng và những việc AI chưa làm được")

CONTENT = f"""<h2>AI riêng của bạn làm được gì trong ERP: công cụ và skill</h2>
<p>Nối xong ({ref(OAUTH, "Cách 1: đăng nhập ERP")}, hoặc {ref(TAO_KHOA, "Cách 2: khóa riêng")}), ứng dụng AI của bạn (Claude, ChatGPT, Cursor…) thấy hai loại thứ từ ERP:</p>
<ul>
<li><strong>Công cụ</strong>: hàm AI gọi vào ERP để lấy dữ liệu hoặc soạn phiếu. Có sẵn trong hệ thống, quản trị bật / tắt theo nhóm.</li>
<li><strong>Skill</strong>: cẩm nang công ty viết cho AI (quy trình, mẫu báo cáo, nguyên tắc so giá). Quản trị và trưởng phòng soạn
trong phân hệ Kho skill AI, gán ai được đọc.</li>
</ul>
<p><strong>Mọi công cụ chạy dưới quyền của chính bạn.</strong> AI chỉ thấy phiếu bạn được xem trên web, báo cáo bạn được giao;
thiếu quyền thì AI báo bị từ chối và nói thiếu quyền gì. Nhóm đang bật không có nghĩa bạn thấy tất cả.</p>

<h2>Công cụ theo nhóm</h2>
<p>Quản trị bật / tắt từng nhóm ở <strong>Kho skill AI ▸ Cấu hình</strong>. Nhóm tắt thì công cụ không hiện trong ứng dụng; AI cố
gọi thì bị từ chối kèm tên nhóm. Nhóm cần dùng mà đang tắt: nhờ quản trị bật.</p>
<table>
<thead><tr><th>Nhóm</th><th>AI làm được</th><th>Trên ERP hiện nay</th></tr></thead>
<tbody>
<tr><td><strong>Tra cứu phiếu và việc của chính mình</strong></td><td>Phiếu tôi lập đang ở bước nào, việc chờ tôi duyệt, YCMH chờ duyệt, văn bản, phiếu hỗ trợ, việc dự án của tôi, tìm lại hội thoại cũ.</td><td>Bật</td></tr>
<tr><td><strong>Nghỉ phép</strong></td><td>Quỹ phép còn bao nhiêu, đơn nghỉ của tôi; soạn đơn nghỉ (khóa được ghi).</td><td>Bật</td></tr>
<tr><td><strong>Danh bạ, thuật ngữ, hướng dẫn sử dụng</strong></td><td>Tra nhân sự, nghĩa từ nội bộ, tìm bài hướng dẫn.</td><td>Bật</td></tr>
<tr><td><strong>Báo cáo gom sẵn và bảng số tổng hợp</strong></td><td>13 báo cáo của phân hệ Báo cáo và bảng số tự ghép (mua hàng, công nợ, đề nghị thanh toán) — chỉ báo cáo bạn được giao.</td><td>Bật</td></tr>
<tr><td><strong>Kho skill AI</strong></td><td>Liệt kê, đọc skill và tệp đi kèm.</td><td>Bật</td></tr>
<tr><td><strong>Thu mua</strong></td><td>Đọc danh sách / chi tiết YCMH, YCBG, ĐMH, nhận hàng; sản phẩm, nhà cung cấp, hợp đồng; giá tốt nhất và lịch sử mua; chấm điểm NCC; <strong>so giá trên web</strong> với giá mua gần nhất; soạn YCMH, YCBG.</td><td>Bật</td></tr>
<tr><td><strong>Công nợ và thanh toán</strong></td><td>Tra công nợ, đọc đề nghị thanh toán; soạn đề nghị thanh toán thì AI trả link mở form điền sẵn trên web.</td><td>Bật</td></tr>
<tr><td><strong>Tra cứu thị trường (tờ khai hải quan)</strong></td><td>Giá nhập khẩu theo kỳ, thời điểm nên mua, nhà nhập khẩu / xuất xứ, kiểm pháp lý hóa chất và biểu thuế.</td><td>Bật</td></tr>
<tr><td><strong>Đặt xe, duyệt dấu, tồn kho, diễn đàn</strong></td><td>Đọc phiếu đặt xe, phiếu duyệt dấu, tồn kho theo kho / mã hàng, tìm và đọc bài diễn đàn (chỉ đọc).</td><td>Bật</td></tr>
<tr><td><strong>Xuất tệp Excel / Word mẫu công ty</strong></td><td>Xuất bảng số ra Excel, báo cáo trình bày ra Word mẫu DEGO; đường tải dùng một lần, hết hạn sau 15 phút.</td><td>Bật</td></tr>
<tr><td><strong>Quản trị Kho skill và khóa AI bằng lời</strong></td><td>Soạn / xuất bản skill, gán quyền đọc, cấp / thu hồi khóa — chỉ người có quyền quản trị tương ứng, khóa được ghi.</td><td>Bật</td></tr>
<tr><td>Lập phiếu đặt xe, duyệt dấu</td><td>Soạn phiếu đặt xe (chọn người phê duyệt và công ty, gửi duyệt luôn được) và phiếu duyệt dấu (chỉ lưu Nháp — tải chứng từ và gửi duyệt trên web).</td><td>Tắt — nhờ quản trị bật</td></tr>
<tr><td>Duyệt phiếu qua AI (đợt 1)</td><td>Duyệt / từ chối phiếu đặt xe, đặt phòng họp, đơn nghỉ phép đang chờ CHÍNH bạn duyệt — mỗi phiếu một lần xác nhận, từ chối phải có lý do.</td><td>Tắt — nhờ quản trị bật</td></tr>
<tr><td>Văn thư</td><td>Tìm và đọc văn bản, xem cấu hình luồng duyệt.</td><td>Tắt — nhờ quản trị bật</td></tr>
<tr><td><strong>Công việc và dự án</strong></td><td>Soạn việc, soạn cả kế hoạch nhiều giai đoạn, gợi ý ai nên giao, thống kê tốc độ theo loại việc.</td><td>Bật</td></tr>
<tr><td>Sửa và xóa phiếu của chính mình</td><td>Đề xuất sửa / xóa phiếu mình lập (có xác nhận, xem dưới).</td><td>Tắt — nhờ quản trị bật</td></tr>
<tr><td><strong>Tạo phiếu hỗ trợ</strong></td><td>Lập phiếu hỗ trợ cho bộ phận nhận phiếu. (Báo lỗi phần mềm qua công cụ <em>báo lỗi</em> thì luôn có.)</td><td>Bật</td></tr>
<tr><td>Lịch và Drive Google · Sổ nhớ, ghi chú, nhóm chat, biên bản họp · Nghiên cứu sâu nhiều nguồn</td><td>Các việc cá nhân dùng chủ yếu qua bot Telegram; nghiên cứu sâu tốn phí công ty.</td><td>Tắt — nhờ quản trị bật</td></tr>
</tbody>
</table>

<h2>Khóa chỉ đọc và khóa được ghi</h2>
<ul>
<li><strong>Chỉ đọc</strong>: chỉ thấy công cụ tra cứu, đọc skill và báo lỗi. Nhờ tạo phiếu bằng khóa này, AI sẽ nói không có công cụ tạo.</li>
<li><strong>Được ghi</strong>: thêm công cụ soạn nháp, đề xuất sửa / xóa và xác nhận. Phiếu tạo ra ghi tên bạn, đi đúng luồng duyệt như lập trên web.</li>
</ul>

<h2>Việc có xác nhận hai bước</h2>
<p>AI <strong>không bao giờ ghi thẳng</strong>. Mọi việc ghi đi qua hai bước, bước hai chỉ chạy khi bạn đồng ý rõ:</p>
<table>
<thead><tr><th>Việc</th><th>Bước 1 (chưa ghi gì)</th><th>Bước 2 (ghi thật)</th></tr></thead>
<tbody>
<tr><td>Lập đơn nghỉ, YCMH, YCBG, phiếu hỗ trợ, phiếu đặt xe, phiếu duyệt dấu</td><td>AI soạn <strong>bản nháp</strong> và đưa bạn xem.</td><td>Bạn gật ▸ AI xác nhận nháp; nói <em>tạo và gửi duyệt</em> thì gửi duyệt luôn.</td></tr>
<tr><td>Sửa phiếu của mình</td><td>AI đưa bảng <strong>cũ → mới</strong>.</td><td>Bạn gật ▸ AI xác nhận. ERP kiểm lại quyền, phạm vi, trạng thái, trường được sửa; đề xuất hết hạn sau 15 phút.</td></tr>
<tr><td>Xóa phiếu của mình</td><td>AI nêu phiếu sẽ xóa.</td><td>Bạn gật ▸ AI xác nhận. Chỉ xóa phiếu chính bạn lập, còn Nháp hoặc Bị trả lại.</td></tr>
<tr><td>Duyệt / từ chối phiếu (đặt xe, phòng họp, nghỉ phép)</td><td>AI tóm tắt phiếu đang chờ bạn và nêu sẽ duyệt hay từ chối (kèm lý do).</td><td>Bạn đồng ý rõ ▸ AI xác nhận. ERP kiểm lại bạn còn đúng là người được giao duyệt chặng đó và phiếu chưa đổi; lịch sử duyệt ghi <em>qua AI</em>. Mỗi phiếu một lần, không duyệt hàng loạt.</td></tr>
<tr><td>Quản trị skill / khóa AI</td><td>AI soạn bản nháp thao tác.</td><td>Bạn gật ▸ AI xác nhận; ERP kiểm lại quyền quản trị.</td></tr>
</tbody>
</table>
<p>Mọi việc AI làm hộ được ghi sổ thay đổi, xem ở <strong>Trang cá nhân ▸ Bot vừa làm gì</strong>; việc tạo / sửa / xóa phiếu hoàn tác được trong 24 giờ ở đó.</p>

<h2>Skill và lời nhắc sẵn</h2>
<ul>
<li>Cổng dặn AI xem cẩm nang công ty liên quan trước khi làm việc nghiệp vụ. AI không tự mở thì nhắc: <em>Hãy xem cẩm nang công ty trước khi trả lời</em>.</li>
<li>Ứng dụng nào hỗ trợ <strong>lời nhắc sẵn</strong> (prompts, ví dụ Claude Desktop) sẽ thấy danh sách từ ERP: <em>bắt đầu việc theo cẩm nang</em> và mỗi skill bạn được đọc một lời nhắc — chọn là AI đọc đúng cẩm nang đó rồi làm.</li>
<li>AI chỉ đọc skill <strong>đã xuất bản</strong> và <strong>được gán cho bạn</strong>; skill không được gán trả về cùng câu với skill không tồn tại.</li>
</ul>

<h2>Câu hỏi mẫu theo phòng</h2>
<p>Dán nguyên câu vào Claude / ChatGPT. Câu có chữ <em>xuất Excel</em> cần nhóm Xuất tệp đang bật.</p>
<h3>Thu mua</h3>
<ul>
<li><em>Tra giá nhập khẩu giấy in A4 trên tờ khai hải quan 6 tháng gần đây, theo nước xuất xứ, và cho biết tháng nào giá thấp nhất.</em></li>
<li><em>So giá trên web của mực in HP 85A với giá công ty mua gần nhất, kèm link mua.</em></li>
<li><em>Nhà cung cấp nào bán giấy A4 cho công ty với giá tốt nhất 6 tháng qua? Chấm điểm 3 nhà cung cấp đứng đầu.</em></li>
<li><em>Liệt kê đơn mua hàng tháng này chưa nhận đủ hàng, xuất Excel.</em></li>
</ul>
<h3>Kế toán</h3>
<ul>
<li><em>Công nợ phải trả quá hạn theo nhà cung cấp, sắp theo số tiền, xuất Excel.</em></li>
<li><em>Tổng tiền mua hàng tháng 9 theo pháp nhân, trước và sau VAT.</em></li>
<li><em>Đề nghị thanh toán tôi lập tuần này đang ở bước nào, chờ ai duyệt?</em></li>
<li><em>Tra giá nhập khẩu hải quan của bột ngọt quý 3 để đối chiếu đơn giá trên hóa đơn nhập khẩu.</em></li>
</ul>
<h3>Nhân sự</h3>
<ul>
<li><em>Tôi còn bao nhiêu ngày phép? Đơn nghỉ gần nhất của tôi được duyệt chưa?</em></li>
<li><em>Đơn nghỉ nào đang chờ tôi duyệt?</em></li>
<li><em>Số điện thoại và chức vụ của các trưởng phòng ở công ty AGC.</em></li>
<li><em>Báo cáo nghỉ phép tháng này theo phòng, xuất Excel.</em></li>
</ul>
<h3>Văn thư</h3>
<ul>
<li><em>Phiếu duyệt dấu nào đã duyệt mà chưa đóng dấu?</em></li>
<li><em>Lịch đặt xe tuần này: chuyến nào chưa phân xe?</em></li>
<li><em>Tìm bài diễn đàn có chữ «lịch nghỉ lễ» mới nhất.</em></li>
<li><em>Văn bản số 08/2026/TB-NS nói gì?</em> — cần nhóm Văn thư đang bật.</li>
</ul>
<h3>Quản lý</h3>
<ul>
<li><em>Việc nào đang chờ tôi duyệt, sắp theo hạn?</em></li>
<li><em>Báo cáo mua hàng quý 3 theo phòng ban, so với quý 2, xuất Excel.</em></li>
<li><em>Giá trị tồn kho theo từng kho, mã hàng nào đã hết.</em></li>
<li><em>So giá web của máy in Canon LBP2900 với giá mua gần nhất, và giá nhập khẩu trên tờ khai hải quan.</em></li>
</ul>

<h2>Chưa làm được</h2>
<ul>
<li><strong>Gửi duyệt phiếu duyệt dấu</strong> qua AI: AI chỉ lưu Nháp, vì gửi duyệt cần tệp chứng từ tải lên trên web.</li>
<li><strong>Duyệt phiếu khác ba loại trên</strong> (YCTT, ĐMH, YCMH, YCBG, duyệt dấu, văn bản) và <strong>trả lại để chỉnh sửa</strong>: làm trên web.</li>
<li><strong>Tạo đề nghị thanh toán</strong>: AI chỉ trả link mở form điền sẵn trên web.</li>
<li><strong>Xóa đề nghị thanh toán, phiếu hỗ trợ</strong>, xóa phiếu của người khác hoặc phiếu đã gửi duyệt.</li>
<li><strong>Sửa / xóa phiếu, văn thư</strong> khi nhóm tương ứng đang tắt — nhờ quản trị bật.</li>
<li><strong>Đọc tệp đính kèm của phiếu</strong> (hóa đơn, ảnh, PDF) và <strong>xem màn hình</strong> của bạn.</li>
</ul>
<p>Số AI trả về là số ERP tính, cùng phạm vi với màn web; <strong>câu chữ là của AI</strong> — đối chiếu lại màn web trước khi gửi
báo cáo. Lỗi khi nối: {ref(NHAT_KY, "bài Nhật ký và lỗi thường gặp")}.</p>"""

ARTICLES = [(ROOT, TITLE, SUMMARY, CONTENT)]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Viết lại bài HDSD AI riêng làm được gì (khớp prod 26/10) + kho vector")
