# -*- coding: utf-8 -*-
"""Nạp bài HDSD duoc-CR-681 — phiếu đặt xe chọn Công ty và Người duyệt. MỘT LỆNH: thêm/cập nhật bài rồi
nạp luôn kho vector (khuôn `help_seed_common.upsert_articles`, chỉ ghi đè đúng bài cùng tiêu đề).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_dat_xe_chon_nguoi_duyet.py
    docker compose exec -T api python scripts/seed_help_dat_xe_chon_nguoi_duyet.py --dry-run

⚠️ Nội dung phải khớp `app/modules/vehicle_booking/approver_picker.py` (danh sách người duyệt, hai chốt)
và `notify._approvers` / `approval_bridge._mail_new_task` (thư tới ai).
"""
from help_seed_common import run_article_upsert

ROOT = "Các chức năng khác"
TITLE = "Đặt xe: chọn Công ty và Người duyệt trên phiếu"

ARTICLES = [
    (ROOT, TITLE,
     "Phiếu đặt xe có hai ô Người phê duyệt và Công ty. Người phê duyệt chọn từ đúng danh sách 'Người có quyền duyệt' "
     "của luồng duyệt Đặt xe; gửi duyệt xong, thư báo đi tới đúng người được chọn, ở mọi chặng của luồng duyệt.",
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
<thead><tr><th>Trường hợp</th><th>Ai nhận việc và thư báo</th></tr></thead>
<tbody>
<tr><td>Chưa bật luồng duyệt cho Đặt xe</td><td>Chỉ người phê duyệt bạn đã chọn nhận chuông và thư <em>YCĐX … chờ bạn duyệt</em>; họ bấm vào là mở được phiếu để Duyệt / Yêu cầu chỉnh sửa / Từ chối.</td></tr>
<tr><td>Đã bật luồng, bước duyệt khai <em>Người có quyền duyệt (theo phân quyền)</em></td><td>Bước đó giao <strong>đúng người bạn đã chọn</strong>, kèm chuông và thư.</td></tr>
<tr><td>Đã bật luồng, bước duyệt khai cách khác (trưởng bộ phận, theo vai trò…)</td><td>Bước đi theo cấu hình luồng; chuông và thư gửi tới người luồng giao việc.</td></tr>
</tbody>
</table>
<p>Luồng nhiều chặng: <strong>mỗi chặng</strong> mở ra đều có chuông và thư cho người nhận việc ở chặng đó. Người duyệt đang
<strong>ủy quyền</strong> cho người khác thì người nhận ủy quyền cũng nhận thư. Thư đi ngay sau khi phiếu được lưu, không làm chậm nút bấm.</p>

<h3>4. Hay gặp</h3>
<ul>
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
