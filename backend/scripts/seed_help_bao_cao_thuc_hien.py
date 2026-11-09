# -*- coding: utf-8 -*-
"""Nạp bài HDSD khối Báo cáo thực hiện trên YCBG và Đơn mua hàng (td-0311, cụm Thu mua) — MỘT LỆNH, chạy lại vô hại.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_bao_cao_thuc_hien.py
    docker compose exec -T api python scripts/seed_help_bao_cao_thuc_hien.py --dry-run

Nguồn sự thật: `frontend-v2/src/modules/procurement/components/survey-report/` (nhãn nút, hộp xác nhận),
`backend/app/modules/survey_request/report_controller.py` (ai được ghi), `report_constants.py` (hai mẫu, trần số).
Tài liệu chức năng: `doc/erp/thu-mua/chuc-nang/19-bao-cao-thuc-hien-ycbg.md`. Nội dung ở đây và ở tài liệu phải khớp nhau.
"""
from help_seed_common import run_article_upsert

PARENT = "Dành cho Nhân viên Mua hàng"
TITLE = "Báo cáo thực hiện trên YCBG và Đơn mua hàng: theo dõi hồ sơ sau khi duyệt"

ARTICLES = [
    (PARENT, TITLE,
     "Khối Báo cáo thực hiện ở trang chi tiết YCBG và Đơn mua hàng: dựng giai đoạn và hồ sơ theo mẫu, cập nhật trạng "
     "thái từng hồ sơ, người yêu cầu mở phiếu là thấy hàng của mình tới đâu.",
     """<p>Phiếu duyệt xong chưa phải là hàng đã về. Sau đó còn cả chuỗi việc: giấy phép, hợp đồng, sản xuất, vận chuyển, thông
quan, nhận hàng. Khối <strong>Báo cáo thực hiện</strong> ghi chuỗi việc đó ngay trên trang chi tiết phiếu, để người mua
cập nhật một chỗ và người yêu cầu mở phiếu là biết hàng của mình tới đâu, không phải đi hỏi.</p>

<h3>1. Khối nằm ở đâu, ai làm được gì</h3>
<table>
<thead><tr><th>Trang</th><th>Ai sửa được</th><th>Ai chỉ xem</th></tr></thead>
<tbody>
<tr><td>Chi tiết <strong>Yêu cầu báo giá (YCBG)</strong>, dưới bảng sản phẩm</td><td>Nhân sự thu mua xử lý phiếu, khi phiếu chưa khóa</td><td>Người lập phiếu, trưởng bộ phận và ai xem được phiếu. Phiếu chưa có báo cáo thì khối ẩn với họ</td></tr>
<tr><td>Chi tiết <strong>Đơn mua hàng (ĐMH)</strong>, cuối trang</td><td>Ai sửa được đơn. Đơn đã Hoàn thành hay Đã hủy thì chỉ xem</td><td>Ai xem được đơn</td></tr>
</tbody>
</table>
<p>Trên ĐMH, mỗi dòng của đơn tự thành một <strong>dòng hàng</strong> của báo cáo: thêm, bớt dòng trên đơn là khối tự theo,
không thêm hay đổi tên tay được. Trên YCBG thì dòng hàng đặt tay.</p>

<h3>2. Ba thứ cần phân biệt</h3>
<ul>
<li><strong>Giai đoạn</strong>: một chặng của tiến trình, ví dụ <em>Pháp lý &amp; Giấy phép</em>, kèm diễn giải hay nơi thực hiện.</li>
<li><strong>Hồ sơ</strong>: một đầu việc hay chứng từ cần làm xong, thuộc đúng một giai đoạn. Đây là thứ bạn cập nhật hằng ngày.</li>
<li><strong>Dòng hàng</strong>: nhãn để lọc hồ sơ theo mặt hàng. Hồ sơ không gắn dòng nào là hồ sơ <strong>Chung</strong>, hiện ở mọi dòng.</li>
</ul>

<h3>3. Khởi tạo báo cáo</h3>
<p>Phiếu chưa có báo cáo thì khối hiện ba nút:</p>
<ol>
<li><strong>Khởi tạo báo cáo mẫu</strong>: hộp chọn mẫu hiện ra, chọn một trong hai mẫu rồi xác nhận.
  <ul>
  <li><em>Mẫu chung hồ sơ nhập khẩu</em>: năm giai đoạn từ Pháp lý tới Nhận hàng &amp; về kho, kèm bộ hồ sơ chứng từ nhập khẩu đã nối sẵn hồ sơ tiên quyết.</li>
  <li><em>Tiến độ kế hoạch công việc nhập khẩu</em>: 21 việc từ Tìm NCC nước ngoài tới Theo dõi thanh toán công nợ, gom một giai đoạn; mô tả mỗi việc ghi số ngày xử lý.</li>
  </ul></li>
<li><strong>Thêm hồ sơ</strong>: ghi đúng một hồ sơ cho một dòng hàng mà không đổ cả mẫu.</li>
<li><strong>Thêm giai đoạn</strong>: dựng tay từ đầu.</li>
</ol>
<p>Sau khi đã có báo cáo, mỗi dòng hàng và mỗi giai đoạn có nút <strong>Tạo mẫu</strong> để đổ thêm phần mẫu vào đúng chỗ đó.
Hệ chỉ <strong>cộng thêm</strong> và bỏ qua hồ sơ trùng tiêu đề, nên bấm hai lần không nhân đôi: thông báo ghi
<em>Đã tạo n hồ sơ theo mẫu của báo cáo</em>, hoặc <em>Mẫu đã có đủ ở đây</em> nếu không thêm gì.</p>

<h3>4. Ba cách xem</h3>
<ul>
<li><strong>Xem tổng</strong>: hồ sơ xếp theo giai đoạn, từ trên xuống. Nút <strong>Mở tất cả / Thu gọn</strong> và mũi tên ở từng giai đoạn để gấp mở; trình duyệt nhớ giai đoạn nào bạn đã gấp và dạng xem bạn chọn.</li>
<li><strong>Theo dòng hàng</strong>: mỗi dòng hàng một dòng, bấm để sổ các hồ sơ của dòng đó.</li>
<li><strong>Bảng</strong>: mỗi hồ sơ một hàng, bấm vào ô để sửa ngay trên hàng.</li>
</ul>
<p>Trên đầu khối có ô tìm (khớp tiêu đề, mô tả, tệp; gõ không dấu vẫn ra) và ô lọc <strong>Mọi trạng thái</strong>.
Thanh tóm tắt cho biết tổng hồ sơ, số đã hoàn thành, hạn hết hiệu lực gần nhất và ngày dự định hoàn tất.</p>

<h3>5. Cập nhật hồ sơ hằng ngày</h3>
<ul>
<li><strong>Đổi trạng thái</strong>: bấm ô tick đầu dòng để gạt <em>Hoàn thành</em> ↔ <em>Đang làm</em>, hoặc chọn thẳng trạng thái ở ô nhỏ trên dòng. Bốn trạng thái: Chưa bắt đầu, Đang làm, Chờ duyệt, Hoàn thành.</li>
<li><strong>Sửa đầy đủ</strong>: bấm bút chì để mở hộp sửa: tiêu đề, mô tả, dòng hàng, giai đoạn, bắt buộc hay không, tệp đính kèm (tên tệp hoặc dán link Drive), hồ sơ tiên quyết, ngày bắt đầu, dự định hoàn tất, ngày hết hiệu lực, nhân sự thực hiện.</li>
<li><strong>Hồ sơ tiên quyết</strong>: hồ sơ còn tiên quyết chưa xong thì bị khóa, hiện mờ kèm biểu tượng ổ khóa, không tick xong được. Chọn tiên quyết vòng tròn (A chờ B, B chờ A) bị chặn ngay lúc lưu.</li>
<li><strong>Trễ hạn</strong>: hồ sơ chưa xong mà đã qua ngày dự định hoàn tất thì dòng ghi <em>Trễ n ngày</em> màu đỏ.</li>
</ul>

<h3>6. Xóa</h3>
<ul>
<li><strong>Một hồ sơ</strong>: biểu tượng thùng rác trên dòng, hỏi xác nhận một lần. Hồ sơ khác đang chờ nó sẽ được mở khóa.</li>
<li><strong>Nhiều hồ sơ</strong>: đánh dấu các hồ sơ cần xóa rồi bấm <strong>Xóa đã chọn</strong> trên thanh chọn (hộp xác nhận hỏi <em>Xóa n hồ sơ?</em>, bấm <strong>Xóa</strong>); hoặc xóa cả cụm hồ sơ của một dòng hàng.</li>
<li><strong>Cả báo cáo</strong>: nút thùng rác trên đầu khối (cạnh <strong>Thêm hồ sơ</strong>), hộp <em>Xóa báo cáo thực hiện</em> hỏi lại, bấm <strong>Xóa</strong>. Lấy lại được ngay: khối trống sau khi xóa có nút <strong>Hoàn tác xóa</strong>, hoặc hoàn tác ở khối <strong>Lịch sử thao tác</strong> của phiếu.</li>
<li>Giai đoạn còn hồ sơ thì không xóa được; chuyển hồ sơ sang giai đoạn khác trước. Xóa một dòng hàng trên YCBG thì hồ sơ của nó chuyển về <strong>Chung</strong>, không mất.</li>
</ul>

<h3>7. Báo cáo chặn việc đóng YCBG</h3>
<p>Trên YCBG, nút <strong>Chuyển Hoàn thành</strong> bị tắt khi còn hồ sơ <strong>bắt buộc</strong> chưa hoàn tất; rê chuột lên
nút để xem còn bao nhiêu hồ sơ. Làm xong (hoặc bỏ dấu bắt buộc) rồi mới đóng phiếu được.</p>

<h3>8. Hay gặp</h3>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Người yêu cầu nói không thấy khối</td><td>Phiếu chưa có báo cáo, khối ẩn với người chỉ xem</td><td>Người mua khởi tạo báo cáo là họ thấy.</td></tr>
<tr><td>Nút <strong>Thêm hồ sơ</strong> mờ, rê chuột ghi <em>Thêm giai đoạn trước</em></td><td>Báo cáo chưa có giai đoạn nào</td><td>Bấm <strong>Thêm giai đoạn</strong> hoặc <strong>Tạo mẫu</strong> trước.</td></tr>
<tr><td>Không tick xong được một hồ sơ</td><td>Hồ sơ còn tiên quyết chưa xong</td><td>Rê chuột lên ổ khóa xem đang chờ hồ sơ nào; làm xong hồ sơ đó, hoặc gỡ tiên quyết trong hộp sửa.</td></tr>
<tr><td>Trên ĐMH không đổi tên được dòng hàng</td><td>Dòng hàng của ĐMH bám theo dòng đơn</td><td>Sửa dòng trên đơn, khối tự theo.</td></tr>
<tr><td>ĐMH đã Hoàn thành, không sửa được báo cáo</td><td>Đơn đã khóa thì báo cáo chỉ xem</td><td>Mở lại đơn nếu thật sự cần sửa.</td></tr>
</tbody>
</table>
<p>Mọi thao tác trên khối đều ghi vào <strong>Lịch sử thao tác</strong> của phiếu với chữ <em>Báo cáo: …</em>, nên tra được ai làm gì lúc nào.</p>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD Báo cáo thực hiện trên YCBG và ĐMH (td-0311) + kho vector")
