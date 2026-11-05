# -*- coding: utf-8 -*-
"""Nạp bài HDSD màn Nhật ký email (bao-CR-721, nút Gửi lại bao-CR-727) dưới thẻ "Quản trị Hệ thống" — MỘT LỆNH, chạy lại vô hại.

Thẻ cha "Quản trị Hệ thống" dựng tay trên giao diện (không script nào sở hữu), nên script chỉ thêm / ghi đè đúng bài cùng
tiêu đề qua `help_seed_common.upsert_articles`.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_nhat_ky_email.py
    docker compose exec -T api python scripts/seed_help_nhat_ky_email.py --dry-run
Sau đó: python scripts/reindex_help_rag.py --purge-orphans

Nội dung phải khớp màn `/system/email-logs` (frontend-v2/src/modules/system/pages/email-log-list-page.tsx) và API
`/api/email-logs` (quyền audit.read; nút Gửi lại `POST /api/email-logs/{id}/resend` đòi audit.write, bao-CR-727).
"""
from help_seed_common import run_article_upsert

ADMIN_ROOT = "Quản trị Hệ thống"
TITLE = "Nhật ký email: tra thư hệ thống đã gửi cho ai, lỗi gì"

ARTICLES = [
    (ADMIN_ROOT, TITLE,
     "Màn Quản trị > Nhật ký email: xem từng thư hệ thống đã gửi hoặc gửi lỗi, lọc theo người nhận, loại thư, trạng thái, "
     "khoảng ngày; đọc nguyên văn câu lỗi của máy chủ thư; gửi lại y nguyên một thư đã gửi.",
     """<h2>Nhật ký email: tra thư hệ thống đã gửi cho ai, lỗi gì</h2>
<p>Mỗi khi hệ thống gửi thư (gửi duyệt, duyệt xong, trả về, điều phối xe, đóng dấu xong...), nó ghi một dòng vào nhật ký email:
gửi cho ai, tiêu đề gì, lúc nào, thành công hay lỗi, và nếu lỗi thì máy chủ thư trả lời gì. Màn này cho người quản trị đọc
nhật ký đó để trả lời câu hỏi thường gặp: <em>Người A nói không nhận được thư, hệ có gửi không?</em></p>
<h3>1. Mở màn và quyền</h3>
<ul>
<li>Vào <strong>Quản trị ▸ Nhật ký email</strong> (đường dẫn <code>/system/email-logs</code>).</li>
<li>Cần quyền <strong>Xem</strong> ở khóa <strong>Nhật ký hệ thống</strong> (<code>audit</code>), cùng khóa với màn Nhật ký hệ thống.
Không có quyền thì không thấy mục trong menu.</li>
<li>Nút <strong>Gửi lại</strong> (mục 5) cần thêm quyền <strong>Sửa</strong> ở cùng khóa <strong>Nhật ký hệ thống</strong>. Chỉ có quyền
Xem thì ngăn chi tiết không hiện nút.</li>
</ul>
<h3>2. Đọc màn</h3>
<ul>
<li>Ba thẻ đầu màn: <strong>Thư lỗi 7 ngày qua</strong>, <strong>Đã gửi 7 ngày qua</strong>, <strong>Đang chờ 7 ngày qua</strong>. Bấm
thẻ là lọc bảng theo trạng thái đó, bấm lại để bỏ lọc.</li>
<li>Bảng xếp <strong>mới nhất trước</strong>, các cột: Thời gian, Người nhận, Tiêu đề, Loại thư, Trạng thái, Lỗi (rút gọn một dòng),
Người gửi (hộp thư gửi danh nghĩa; trống nghĩa là dùng SMTP chung), Gửi xong lúc (ẩn sẵn, bật ở menu Cột).</li>
<li>Trạng thái: <strong>Đã gửi</strong> (xanh), <strong>Lỗi</strong> (đỏ), <strong>Đang chờ</strong> (vàng, thư còn trong hàng đợi),
<strong>Tắt gửi</strong> (xám, thư bị công tắc email chặn nên không gửi).</li>
<li><strong>Bấm một dòng</strong> mở ngăn chi tiết: đủ địa chỉ, loại thư kèm mã kỹ thuật, và <strong>nguyên văn câu lỗi</strong> của máy
chủ thư, có nút chép để dán vào phiếu hỗ trợ.</li>
<li>Dòng có nhãn <strong>Gửi lại từ #id</strong> là bản gửi lại của dòng mang số đó (xem mục 5).</li>
</ul>
<h3>3. Lọc</h3>
<table>
<thead><tr><th>Ô lọc</th><th>Cách dùng</th></tr></thead>
<tbody>
<tr><td><strong>Người nhận chứa</strong></td><td>Gõ một phần địa chỉ, không phân biệt hoa thường, ví dụ <em>an.nguyen</em>.</td></tr>
<tr><td><strong>Trạng thái</strong></td><td>Chọn một trạng thái; bỏ lọc bằng <em>Mọi trạng thái</em>.</td></tr>
<tr><td><strong>Thêm loại thư</strong></td><td>Chọn được <strong>nhiều</strong> loại, mỗi loại thành một nhãn bên cạnh, bấm dấu x trên nhãn để bỏ.
Tên loại thư lấy từ danh mục <em>Mẫu email thông báo</em>, ví dụ <em>Gửi duyệt → Người duyệt</em>.</td></tr>
<tr><td><strong>Từ ngày / Đến ngày</strong></td><td>Theo lúc ghi thư, lấy trọn ngày cuối.</td></tr>
</tbody>
</table>
<p>Bảng trống kèm câu <em>Không có thư nào khớp bộ lọc</em> nghĩa là đang có bộ lọc; bấm <strong>Xóa bộ lọc</strong> để xem lại tất cả.</p>
<h3>4. Hay gặp</h3>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Người dùng bảo không nhận được thư, nhật ký ghi <strong>Đã gửi</strong></td><td>Hệ đã giao thư cho máy chủ thư thành công</td><td>Nhờ người đó
xem thư rác, kiểm địa chỉ ở cột Người nhận có đúng không; sai thì sửa email trong hồ sơ nhân sự.</td></tr>
<tr><td>Không có dòng nào cho người đó</td><td>Hệ không gửi: người đó đã tắt nhận email ở Trang cá nhân, hoặc công tắc email toàn hệ tắt,
hoặc địa chỉ nằm trong danh sách loại trừ</td><td>Xem bài về công tắc email và màn <em>Cấu hình hệ thống</em>.</td></tr>
<tr><td>Nhiều dòng <strong>Lỗi</strong> cùng một câu như <em>authentication failed</em></td><td>Hộp thư gửi sai mật khẩu hoặc bị khóa</td><td>Vào
<strong>Quản trị ▸ Hộp thư gửi</strong> kiểm lại, hoặc bấm <em>Thử gửi thư</em> ở Cấu hình hệ thống.</td></tr>
<tr><td>Dòng <strong>Đang chờ</strong> lâu không đổi</td><td>Hàng đợi gửi thư nền không chạy</td><td>Báo kỹ thuật kiểm dịch vụ chạy ngầm (màn <em>Việc chạy ngầm</em>).</td></tr>
<tr><td>Thư <strong>Lỗi</strong> vì hộp thư gửi hỏng, nay đã sửa xong</td><td>Thư cũ không tự gửi lại</td><td>Mở dòng, bấm
<strong>Gửi lại</strong> (mục 5).</td></tr>
</tbody>
</table>
<h3>5. Gửi lại một thư</h3>
<ul>
<li>Bấm dòng để mở ngăn chi tiết, bấm <strong>Gửi lại</strong> ở chân ngăn. Hộp xác nhận ghi rõ <strong>người nhận</strong> và
<strong>tiêu đề</strong>; bấm <strong>Gửi lại</strong> để gửi, <strong>Hủy</strong> để thôi.</li>
<li>Hệ gửi lại <strong>y nguyên</strong> thư cũ: cùng người nhận, tiêu đề, nội dung, hộp thư gửi danh nghĩa. Thư hệ thống không có tệp đính
kèm, nên gửi lại là gửi trọn thư.</li>
<li>Gửi lại tạo <strong>một dòng mới</strong> ở trạng thái <strong>Đang chờ</strong>, mang nhãn <strong>Gửi lại từ #id</strong>; dòng cũ giữ
nguyên trạng thái (ví dụ vẫn là <strong>Lỗi</strong>). Xem dòng mới để biết lần này tới chưa.</li>
<li>Công tắc email toàn hệ vẫn áp: email đang tắt thì dòng mới chuyển <strong>Tắt gửi</strong>.</li>
<li>Cùng một thư vừa gửi lại thì phải đợi <strong>60 giây</strong> mới bấm lại được, tránh bấm liên tục làm người nhận nhận nhiều thư.</li>
<li>Nút bị <strong>tắt</strong> kèm lý do ở chân ngăn khi:
<ul>
<li>thư gửi trước đợt cập nhật lưu nội dung thư (ngày ghi trong câu báo): hệ không còn nội dung để gửi lại;</li>
<li>thư <strong>đặt lại mật khẩu</strong> hoặc <strong>cấp tài khoản</strong>: thư chứa liên kết đặt mật khẩu nên hệ không bao giờ lưu nội
dung. Người nhận tự bấm <em>Quên mật khẩu</em> ở màn đăng nhập để nhận liên kết mới.</li>
</ul></li>
<li>Mỗi lần gửi lại được ghi vào <strong>Nhật ký hệ thống</strong> (ai gửi lại thư nào, lúc nào).</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD màn Nhật ký email (bao-CR-721, bao-CR-727) + kho vector")
