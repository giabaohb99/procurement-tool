# -*- coding: utf-8 -*-
"""Bài HDSD Thu mua cho duoc-CR-777 (17/11/2026): Mẫu thu mua ở màn In phiếu đề xuất mua hàng từ Đơn mua hàng.

Cây trợ giúp Thu mua được dựng TAY trên giao diện (không có script sở hữu), nên script này KHÔNG xóa / dựng lại cây.
Nó chỉ thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Dành cho Nhân viên Mua hàng*, rồi nạp lại kho
vector cho đúng bài đó (`help_seed_common.run_article_upsert`). Bài người dùng tự viết không bao giờ bị đụng.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_mau_in_cr777.py --dry-run
    docker compose exec -T api python scripts/seed_help_thu_mua_mau_in_cr777.py

Nội dung khớp cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
from help_seed_common import run_article_upsert

STAFF_ROOT = "Dành cho Nhân viên Mua hàng"

ARTICLES = [
    (STAFF_ROOT, "Mẫu thu mua khi in phiếu đề xuất mua hàng từ Đơn mua hàng",
     "In phiếu đề xuất từ Đơn mua hàng bằng Mẫu thu mua: người đề xuất là bạn, trưởng phòng là quản lý trực tiếp, NCC và hàng theo đơn.",
     """<h2>Mẫu thu mua khi in phiếu đề xuất mua hàng từ Đơn mua hàng</h2>
<p>Từ ngày 17/11/2026, khi in <strong>phiếu đề xuất mua hàng từ Đơn mua hàng</strong> (nút in phiếu yêu cầu ở trang chi tiết Đơn mua hàng), ô <strong>Mẫu in</strong> có thêm hai mẫu: <strong>Mẫu thu mua – có chữ ký</strong> và <strong>Mẫu thu mua – không chữ ký</strong>. Áp dụng cho cả giao diện Thu mua cũ lẫn giao diện ERP mới. Hai mẫu này đứng <strong>đầu</strong> danh sách, nhưng khi mở màn hệ thống vẫn chọn sẵn <strong>Mẫu thường – có chữ ký</strong>; muốn in mẫu thu mua thì chọn ở ô Mẫu in.</p>
<h3>1. Khác mẫu thường ở đâu</h3>
<table>
<thead><tr><th>Mục trên phiếu</th><th>Mẫu thường</th><th>Mẫu thu mua</th></tr></thead>
<tbody>
<tr><td><strong>Người đề xuất</strong> (kèm chức vụ, bộ phận)</td><td>Người lập phiếu yêu cầu</td><td><strong>Bạn</strong> — người đang đăng nhập bấm in</td></tr>
<tr><td><strong>Trưởng phòng ban/bộ phận</strong></td><td>Trưởng phòng ghi trên phiếu yêu cầu</td><td><strong>Quản lý trực tiếp</strong> của bạn theo hồ sơ nhân sự</td></tr>
<tr><td><strong>Nhà cung cấp do bộ phận đề xuất</strong></td><td>Theo phiếu yêu cầu</td><td>NCC của <strong>Đơn mua hàng</strong></td></tr>
<tr><td><strong>Bảng hàng</strong></td><td>Dòng phiếu yêu cầu, giá đề xuất</td><td>Dòng của <strong>Đơn mua hàng</strong>: số lượng đặt, đơn giá; tổng cộng, tiền VAT và tổng thanh toán theo đơn</td></tr>
<tr><td><strong>Ô ký</strong></td><td>Theo phiếu yêu cầu</td><td>Ô <em>Người lập</em> là chữ ký của bạn, ô <em>TP/BP đề xuất</em> là chữ ký quản lý trực tiếp; ô Giám đốc và TP/BP mua hàng như mẫu thường</td></tr>
</tbody>
</table>
<p>Các phần còn lại (số phiếu, ngày, mục đích, nơi giao, ghi chú dòng) vẫn lấy từ phiếu yêu cầu mua hàng. Cột <em>Thành tiền</em> từng dòng là số lượng × đơn giá chưa VAT; tiền VAT và tổng thanh toán nằm ở hai dòng riêng bên dưới.</p>
<h3>2. Ai thấy hai mẫu này</h3>
<ul>
<li>Chỉ người có quyền <strong>đọc Đơn mua hàng</strong> và đơn đó nằm trong phạm vi được xem của mình. Không đủ quyền thì ô Mẫu in chỉ có các mẫu cũ.</li>
<li>Màn in phiếu yêu cầu mua hàng thường (không đi từ Đơn mua hàng) không có hai mẫu này.</li>
<li>Không được xem nhà cung cấp thì phần nhà cung cấp in chữ <em>Nhà cung cấp tối ưu nhất</em> như mẫu thường.</li>
</ul>
<h3>3. Khi phiếu thiếu thông tin</h3>
<ul>
<li>Hồ sơ của bạn <strong>chưa gán quản lý trực tiếp</strong> thì dòng Trưởng phòng ban/bộ phận và ô ký TP/BP đề xuất để trống — nhờ phòng Nhân sự gán quản lý trực tiếp trên hồ sơ.</li>
<li>Chưa thấy chữ ký: tải chữ ký ở <strong>Trang cá nhân</strong> (thẻ Chữ ký cá nhân); quản lý trực tiếp cũng phải tự tải chữ ký của họ.</li>
<li>Cần ký tay thì chọn <strong>Mẫu thu mua – không chữ ký</strong>: bốn ô ký để trống.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD Thu mua duoc-CR-777: Mẫu thu mua khi in phiếu đề xuất từ ĐMH")
