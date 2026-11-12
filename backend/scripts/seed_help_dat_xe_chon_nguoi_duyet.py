# -*- coding: utf-8 -*-
"""Nạp bài HDSD duoc-CR-681 (sửa ở duoc-CR-706, duoc-CR-752) — phiếu đặt xe chọn Công ty và Người duyệt. MỘT LỆNH: thêm/cập nhật bài rồi
nạp luôn kho vector (khuôn `help_seed_common.upsert_articles`, chỉ ghi đè đúng bài cùng tiêu đề).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_dat_xe_chon_nguoi_duyet.py
    docker compose exec -T api python scripts/seed_help_dat_xe_chon_nguoi_duyet.py --dry-run

⚠️ Nội dung phải khớp `app/modules/vehicle_booking/approver_picker.py` (danh sách người duyệt, hai chốt)
và `notify._approvers` / `approval_bridge._mail_new_task` (thư tới ai). Từ duoc-CR-706: người CÙNG quyền duyệt
đặt xe mà phạm vi phủ phiếu cũng duyệt được (`approval/permission_approvers.resolve`), nhưng chuông + thư chỉ tới
người được chọn (`approval_bridge._should_notify_task`).
"""
from help_seed_common import run_article_upsert

ROOT = "Các chức năng khác"
TITLE = "Đặt xe: chọn Công ty và Người duyệt trên phiếu"

ARTICLES = [
    (ROOT, TITLE,
     #  Cột summary là String(255): giữ dưới 255 ký tự, dài hơn là MySQL báo "Data too long".
     "Phiếu đặt xe có hai ô Người phê duyệt và Công ty. Gửi duyệt xong, chuông và thư chỉ tới người được chọn; "
     "người khác cùng quyền duyệt đặt xe mà phạm vi phủ phiếu cũng duyệt được.",
     """<h2>Chọn Người phê duyệt và Công ty trên phiếu đặt xe</h2>
<p>Khi tạo hoặc sửa phiếu ở <strong>Đặt xe ▸ Yêu cầu đặt xe ▸ Tạo yêu cầu</strong>, ngay dưới phần <em>Thông tin người tạo</em>
có khối <strong>Người phê duyệt và công ty</strong> gồm hai ô, cả hai bắt buộc khi bấm <strong>Gửi duyệt</strong> (lưu nháp thì chưa bắt).</p>

<h3>1. Người phê duyệt</h3>
<ul>
<li>Bấm vào ô để mở danh sách, gõ <strong>tên hoặc mã nhân viên</strong> để lọc nhanh.</li>
<li>Mỗi dòng có <strong>ảnh đại diện</strong> (chưa có ảnh thì hiện chữ cái đầu), tên dạng <strong>Mã - Họ tên</strong>
(ví dụ <em>NSU209 - Huỳnh Gia Bảo</em>) và dòng nhỏ bên dưới ghi <strong>vai trò cấp quyền duyệt kèm phạm vi</strong>
(ví dụ <em>Điều phối viên (Đặt xe) (Tất cả)</em>).</li>
<li>Danh sách <strong>trùng đúng</strong> danh sách <strong>Người có quyền duyệt</strong> ở màn Phê duyệt ▸ Luồng duyệt: người có vai trò được tick
<strong>Duyệt</strong> ở dòng <em>Đặt xe</em> (Nhân sự ▸ Phân quyền tài khoản) với phạm vi Phòng ban, Công ty hoặc Tất cả — không gồm tài khoản
Quản trị hệ thống. Chính bạn không có trong danh sách — không tự duyệt phiếu của mình.</li>
<li>Người được chọn <strong>xem và duyệt được phiếu</strong> dù phiếu thuộc công ty khác công ty của họ.</li>
</ul>

<h3>2. Công ty</h3>
<ul>
<li>Mỗi dòng có <strong>logo</strong>, tên công ty và dòng nhỏ ghi <strong>MST</strong>; gõ tên hoặc MST để lọc.</li>
<li>Mặc định là công ty trên hồ sơ của bạn; đổi được sang bất kỳ công ty nào đang hoạt động.</li>
<li>Công ty quyết định phiếu đi theo <strong>luồng duyệt</strong> của công ty nào.</li>
<li>Chọn công ty <strong>khác</strong> công ty mình thì người có phạm vi <strong>Công ty</strong> ở <strong>cả hai bên</strong> (công ty của bạn và công ty
đã chọn) đều thấy phiếu; người cùng phòng với bạn cũng vẫn thấy.</li>
<li>Hai ô <strong>độc lập</strong>: đổi công ty không làm đổi danh sách người phê duyệt.</li>
</ul>

<h3>3. Gửi duyệt xong thì sao</h3>
<table>
<thead><tr><th>Trường hợp</th><th>Ai duyệt được</th><th>Ai nhận chuông và thư</th></tr></thead>
<tbody>
<tr><td>Chưa bật luồng duyệt cho Đặt xe</td><td>Người bạn đã chọn, và mọi người có quyền <strong>Duyệt</strong> đặt xe mà phạm vi phủ phiếu (xem mục 4)</td><td>Chỉ người bạn đã chọn nhận chuông và thư <em>YCĐX … chờ bạn duyệt</em>; họ bấm vào là mở được phiếu để Duyệt / Yêu cầu chỉnh sửa / Từ chối.</td></tr>
<tr><td>Đã bật luồng, bước duyệt khai <em>Người có quyền duyệt (theo phân quyền)</em></td><td>Bước đó giao cho <strong>người bạn đã chọn</strong> (đứng đầu) <strong>cùng mọi người cùng quyền</strong> mà phạm vi phủ phiếu</td><td>Chỉ người bạn đã chọn.</td></tr>
<tr><td>Đã bật luồng, bước duyệt khai cách khác (trưởng bộ phận, theo vai trò…)</td><td>Theo cấu hình luồng</td><td>Người luồng giao việc.</td></tr>
</tbody>
</table>
<p>Luồng nhiều chặng: <strong>mỗi chặng</strong> mở ra đều có chuông và thư cho người nhận việc ở chặng đó (chặng <em>Người có quyền duyệt</em>
thì chỉ báo người bạn đã chọn, nếu người đó có việc ở chặng này). Người duyệt đang <strong>ủy quyền</strong> cho người khác thì người nhận
ủy quyền cũng nhận thư. Thư đi ngay sau khi phiếu được lưu, không làm chậm nút bấm.</p>

<h3>4. Người khác cùng quyền duyệt cũng duyệt được</h3>
<p>Chọn <strong>Người phê duyệt</strong> là chọn người được <strong>báo</strong> trước, không khóa phiếu vào riêng một người. Khi người đó vắng,
người khác giữ quyền <strong>Duyệt</strong> đặt xe vẫn xử lý được phiếu, miễn là phạm vi của họ phủ phiếu:</p>
<ul>
<li>Phạm vi <strong>Phòng ban</strong>: phiếu thuộc phòng ban của họ.</li>
<li>Phạm vi <strong>Công ty</strong>: phiếu của công ty họ, tính cả công ty người tạo lẫn công ty đã chọn trên phiếu.</li>
<li>Phạm vi <strong>Tất cả</strong>: mọi phiếu.</li>
</ul>
<p>Người cùng quyền <strong>không nhận chuông hay thư</strong>. Họ thấy phiếu ở <strong>Đặt xe ▸ Yêu cầu đặt xe</strong> (lọc trạng thái <em>Chờ duyệt</em>)
hoặc ở khối <strong>Chờ tôi duyệt</strong> trên <strong>Đặt xe ▸ Tổng quan</strong> (khối này ẩn sẵn, bật lại ở nút <strong>Hiển thị</strong>). Mở phiếu là có
nút <strong>Duyệt</strong> cùng các lựa chọn <strong>Yêu cầu chỉnh sửa</strong> / <strong>Từ chối</strong>.</p>
<p>Ai bấm trước thì phiếu đi tiếp theo người đó. Với bước khai <em>Một người duyệt là đủ</em>, một người duyệt xong là việc của những người còn
lại tự đóng. <strong>Lưu ý cho quản trị:</strong> nếu bước <em>Người có quyền duyệt</em> khai <em>Tất cả phải duyệt</em> thì mọi người cùng quyền đều phải
duyệt mới qua bước, nên bước này thường để <em>Một người duyệt là đủ</em>.</p>
<p>Người bạn chọn vẫn duyệt được dù phạm vi của họ không phủ phiếu (ví dụ phiếu thuộc công ty khác). Tài khoản Quản trị hệ thống không được luồng
duyệt giao việc.</p>

<h3>5. Hay gặp</h3>
<ul>
<li><strong>Tôi có quyền duyệt đặt xe nhưng phiếu không có nút Duyệt</strong>: phạm vi của bạn không phủ phiếu (phiếu của phòng ban hoặc công ty khác),
hoặc luồng nhiều chặng chưa tới chặng của bạn. Phiếu gửi duyệt trước đợt cập nhật đầu tháng 11/2026 mà vẫn đang chờ thì nhờ quản trị bổ sung người duyệt.</li>
<li><strong>Người được chọn chưa duyệt mà phiếu đã qua bước</strong>: một người cùng quyền đã duyệt trước. Xem ai duyệt ở khối <em>Tiến trình xử lý</em> trên trang chi tiết phiếu.</li>
<li><strong>Người duyệt đã chọn không có quyền duyệt phiếu đặt xe — chọn lại</strong>: người đó vừa bị gỡ quyền, tài khoản bị khóa
hoặc đã nghỉ việc. Phiếu nháp cũ hiện người đó kèm chữ <em>(không còn quyền duyệt — chọn lại)</em>; chọn người khác rồi gửi.</li>
<li><strong>Danh sách người phê duyệt trống</strong> (khung vàng): chưa ai được tick quyền Duyệt đặt xe — nhờ quản trị cấp ở Nhân sự ▸ Phân quyền tài khoản,
thường là vai trò <em>Điều phối viên (Đặt xe)</em> hoặc <em>Quản lý điều phối (Đặt xe)</em>.</li>
<li><strong>Thấy người không liên quan trong danh sách</strong>: vai trò của họ đang được tick Duyệt đặt xe. Quản trị bỏ tick ở màn Phân quyền là danh sách tự bớt.</li>
<li>Trang chi tiết phiếu hiện <strong>Người phê duyệt</strong> (kèm ảnh đại diện) và <strong>Công ty</strong> (kèm logo) ngay trong thẻ người yêu cầu; tiến độ từng chặng xem ở khối <em>Tiến trình xử lý</em>.</li>
<li><strong>Phiếu chuyển từ app đặt xe cũ</strong>: khi phiếu đã được thao tác trên ERP (duyệt, điều phối, sửa nội dung…), thay đổi sau đó bên app cũ <strong>không chép đè</strong> về ERP nữa — ERP giữ đúng những gì đã làm. Ngoại lệ: app cũ <strong>hủy</strong> hoặc <strong>từ chối</strong> phiếu chưa hoàn tất thì ERP vẫn nhận trạng thái đó. Phiếu chưa ai đụng trên ERP vẫn cập nhật theo app cũ như trước.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD đặt xe chọn người duyệt duoc-CR-681 + kho vector")
