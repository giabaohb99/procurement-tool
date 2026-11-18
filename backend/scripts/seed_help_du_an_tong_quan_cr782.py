# -*- coding: utf-8 -*-
"""Bài HDSD cho duoc-CR-782 (18/11/2026): màn Tổng quan phân hệ Dự án theo góc nhìn người quản lý.

Thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Hướng dẫn sử dụng Dự án và Công việc* (thẻ do
`seed_help_cong_viec.py` dựng), rồi nạp lại kho vector cho đúng bài đó (`help_seed_common.run_article_upsert`). Không xóa
/ dựng lại cây.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_du_an_tong_quan_cr782.py --dry-run
    docker compose exec -T api python scripts/seed_help_du_an_tong_quan_cr782.py
"""
from help_seed_common import run_article_upsert

PROJECT_ROOT = "Hướng dẫn sử dụng Dự án và Công việc"

ARTICLES = [
    (PROJECT_ROOT, "Dự án — Màn Tổng quan: theo dõi đội, dự án và việc cần xử lý",
     "Tổng quan Dự án cho người quản lý: thẻ số theo kỳ, biểu đồ, việc cần xử lý ngay, bảng đối chiếu theo người, sức khỏe từng dự án.",
     """<h2>Màn Tổng quan của phân hệ Dự án</h2>
<p>Mở menu <strong>Dự án › Tổng quan</strong>. Từ ngày 18/11/2026 màn này trả lời bốn câu hỏi của người quản lý: đội đang có
bao nhiêu việc, việc nào phải ra tay ngay, từng người đang ra sao, từng dự án đang ra sao.</p>
<p>Màn chia ba tab: <strong>Tổng quan</strong> (mặc định — biểu đồ đứng đầu, ngay dưới là các việc cần xử lý, cơ cấu ưu tiên,
việc của tôi), <strong>Dự án</strong> (thẻ sức khỏe từng dự án + theo dõi một dự án) và <strong>Nhân sự</strong> (bảng đối chiếu + theo dõi
một người). Nút kỳ và sáu thẻ số nằm trên cùng, áp cho cả ba tab.</p>
<h3>1. Ai thấy số liệu của dự án nào</h3>
<ul>
<li>Người được giao xem báo cáo <strong>Công việc &amp; Dự án</strong> (tab <strong>Báo cáo</strong> ở Phân quyền tài khoản;
admin có sẵn) thấy số liệu của <strong>mọi dự án</strong> — dòng đầu màn ghi <em>Đang xem số liệu của mọi dự án</em>.</li>
<li>Người khác thấy số liệu của các dự án mình tham gia.</li>
<li>Dự án mình <strong>chưa là thành viên</strong> vẫn hiện số liệu nhưng ghi <em>chưa là thành viên</em> và không bấm vào
được — muốn mở bảng việc thì nhờ chủ dự án mời vào.</li>
</ul>
<h3>2. Thẻ số và kỳ thống kê</h3>
<p>Nút <strong>7 ngày / 30 ngày / 90 ngày</strong> ở góc phải chọn kỳ cho các chỉ số "trong kỳ".</p>
<table>
<thead><tr><th>Thẻ</th><th>Nghĩa</th></tr></thead>
<tbody>
<tr><td>Việc đang mở</td><td>Việc chưa xong, kèm số việc mới tạo trong kỳ.</td></tr>
<tr><td>Việc quá hạn</td><td>Việc chưa xong đã qua hạn, kèm tỉ lệ trên số việc đang mở.</td></tr>
<tr><td>Xong trong kỳ</td><td>Việc chuyển sang hoàn thành trong kỳ đang chọn.</td></tr>
<tr><td>Xong đúng hạn</td><td>Tỉ lệ việc xong trong kỳ <strong>có đặt hạn</strong> mà xong không sau hạn. Hiện "—" khi chưa có việc nào để đo.</td></tr>
<tr><td>Chưa ai nhận</td><td>Việc đang mở chưa có người phụ trách, kèm số việc chưa đặt hạn.</td></tr>
</tbody>
</table>
<h3>3. Biểu đồ</h3>
<ul>
<li><strong>Tình trạng việc đang mở</strong>: vòng chia việc chưa xong thành quá hạn (đỏ), đến hạn trong 7 ngày (cam), còn hạn
(xanh lá), chưa đặt hạn (xám), kèm số và tỉ lệ.</li>
<li><strong>Dự án: đang mở và làm ra</strong> và <strong>Theo người: đang giữ và làm ra</strong>: cột là việc đang mở (phần
đỏ là việc đã quá hạn), đường là việc xong trong kỳ đang chọn — cột cao mà đường thấp là chỗ đang dồn việc. Rê chuột lên
một cột để xem số từng phần.</li>
</ul>
<h3>4. Theo dõi từng dự án / từng người</h3>
<p>Bấm <strong>Dự án</strong> hoặc <strong>Người</strong> rồi chọn (gõ để tìm) một dự án / một người. Khối hiện dải số riêng của
đối tượng đó (đang mở, quá hạn, xong trong kỳ, % hoàn thành hoặc % xong đúng hạn, hạn chót hoặc trễ lâu nhất) và biểu đồ diễn
biến theo từng <strong>ngày</strong> (kỳ 7 và 30 ngày) hoặc từng <strong>tuần</strong> (kỳ 90 ngày): cột là việc xong — xanh
ngọc đúng hạn, đỏ trễ hạn, xám không đặt hạn — đường là việc mới giao. Đường nằm trên cột nhiều ngày liền nghĩa là việc đang
dồn lên; cột đỏ nhiều nghĩa là hay xong trễ. Theo người chỉ tính việc người đó <strong>phụ trách</strong>.</p>
<h3>5. Cần xử lý ngay</h3>
<ul>
<li><strong>Quá hạn lâu nhất</strong>: việc trễ lâu nhất lên đầu, kèm số ngày trễ và người đang giữ.</li>
<li><strong>Chưa ai nhận</strong>: việc không có người phụ trách — không ai làm, cũng không hiện ở bảng theo người.</li>
<li><strong>Chưa đặt hạn</strong>: việc không có hạn thì không bao giờ báo quá hạn; việc tạo lâu nhất lên đầu.</li>
</ul>
<h3>6. Đối chiếu theo người</h3>
<p>Mỗi người phụ trách một dòng, người nhiều việc quá hạn lên đầu: đang mở, quá hạn, trễ lâu nhất, hạn 7 ngày tới, xong trong
kỳ, % đúng hạn, cập nhật gần nhất (tô cam khi đã hơn 14 ngày không động tới việc nào). Hai cột giờ ước / giờ thực tế bật ở
nút <strong>Cột</strong>. Một việc có hai người phụ trách thì tính cho cả hai; người chỉ <em>theo dõi</em> không tính.
<strong>Bấm vào một người</strong> để xem danh sách việc đang mở của họ, quá hạn lên đầu.</p>
<h3>7. Sức khỏe từng dự án</h3>
<ul>
<li><strong>Trễ</strong>: từ 25% số việc đang mở đã quá hạn.</li>
<li><strong>Có rủi ro</strong>: có ít nhất một việc quá hạn.</li>
<li><strong>Đúng tiến độ</strong>: không việc nào quá hạn.</li>
<li><strong>Chưa có việc</strong>: bảng việc còn trống.</li>
</ul>
<p>Mỗi dự án một thẻ: nhãn sức khỏe, thanh hoàn thành (không tính việc đã hủy), số việc đang mở, quá hạn và hạn chót (hạn xa
nhất của việc còn mở). Dự án chưa có việc gom thành một dòng chữ cuối khối.
Nhiều dự án thì dùng ô <strong>Tìm dự án</strong> (gõ không dấu được) và nút lọc <strong>Trễ / Có rủi ro / Đúng tiến độ</strong> (kèm số
dự án); khối hiện 9 thẻ đáng lo nhất trước, bấm <strong>Xem thêm</strong> để mở tiếp. Bấm một thẻ để mở bảng việc; thẻ có biểu tượng ổ
khóa là dự án bạn chưa là thành viên.</p>
<h3>8. Báo cáo riêng của một dự án</h3>
<p>Mở một dự án, chọn tab <strong>Báo cáo</strong> (cạnh Bảng, Danh sách, Gantt, Hoạt động). Mọi số chỉ tính trong dự án
đó, theo kỳ chọn ở nút <strong>Kỳ thống kê</strong> trên cùng (7 / 30 / 90 ngày).</p>
<ul>
<li><strong>Cột phải</strong>: thẻ tóm tắt (% hoàn thành, nhãn sức khỏe, việc đang mở, quá hạn, xong trong kỳ, % xong đúng hạn,
chưa ai nhận, chưa đặt hạn, hạn chót dự án), vòng tình trạng việc mở, và thẻ <strong>Cần xử lý</strong>: bấm
<em>Quá hạn</em> / <em>Chưa nhận</em> / <em>Chưa hạn</em> để đổi danh sách, bấm một dòng để mở việc.</li>
<li><strong>Cột trái</strong>: biểu đồ diễn biến của dự án theo ngày / tuần, biểu đồ theo người trong dự án, bảng đối chiếu
theo người (bấm một người để xem việc đang mở của họ).</li>
</ul>
<p>Trên điện thoại hai cột xếp thành một, thẻ tóm tắt lên đầu. Nút mũi tên cạnh tên dự án đưa về danh sách dự án.</p>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD duoc-CR-782: màn Tổng quan phân hệ Dự án")
