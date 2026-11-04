# -*- coding: utf-8 -*-
"""Nạp bài HDSD trang Có gì mới và phiên bản (bao-CR-722) dưới thẻ "Bắt đầu" — MỘT LỆNH, chạy lại vô hại.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_co_gi_moi.py
    docker compose exec -T api python scripts/seed_help_co_gi_moi.py --dry-run
Sau đó: python scripts/reindex_help_rag.py --purge-orphans

Nội dung phải khớp trang `/whats-new` (frontend-v2/src/app/pages/whats-new-page.tsx) và tệp
backend/app/data/release_notes.json.
"""
from help_seed_common import run_article_upsert

START_ROOT = "Bắt đầu"
TITLE = "Có gì mới: xem hệ đang chạy bản nào và mỗi đợt cập nhật đổi gì"

ARTICLES = [
    (START_ROOT, TITLE,
     "Trang Có gì mới liệt kê từng đợt cập nhật của hệ (thêm, sửa, bỏ theo phân hệ) và dòng phiên bản đang chạy ở chân menu "
     "trái; chấm đỏ báo có đợt mới chưa xem.",
     """<h2>Có gì mới: xem hệ đang chạy bản nào và mỗi đợt cập nhật đổi gì</h2>
<p>Mỗi lần hệ được cập nhật, bộ phận kỹ thuật ghi một mục <strong>ghi chú phát hành</strong> bằng lời người dùng: thêm gì, sửa gì,
bỏ gì, ở phân hệ nào. Trang <strong>Có gì mới</strong> cho mọi người đọc các mục đó mà không cần hỏi.</p>
<h3>1. Mở trang</h3>
<ul>
<li>Bấm vào dòng <strong>Phiên bản 2.12.0</strong> ở chân menu trái (rê chuột lên dòng này thấy mã bản dựng và giờ dựng) của bất kỳ phân hệ nào, hoặc mở menu tài khoản
(ảnh đại diện góc phải) rồi chọn <strong>Có gì mới</strong>. Đường dẫn: <code>/whats-new</code>.</li>
<li>Ai đăng nhập cũng xem được, không cần quyền riêng.</li>
</ul>
<h3>2. Đọc trang</h3>
<ul>
<li>Dòng đầu ghi <strong>phiên bản đang chạy</strong> dạng 2.X.Y (2 là ERP thế hệ hai, X tăng mỗi đợt có tính năng mới, Y tăng khi
đợt chỉ sửa lỗi, ví dụ 2.12.0), ngày phát hành, mã bản dựng của máy chủ, giờ dựng và môi trường. Chỗ nào ghi <em>không rõ</em> là bản dựng không kèm thông tin đó, không phải lỗi.</li>
<li>Các đợt xếp <strong>mới nhất trước</strong>, đợt đầu có nhãn <strong>Mới nhất</strong>. Trong mỗi đợt, từng dòng có nhãn
<strong>Thêm</strong> (xanh lá), <strong>Sửa</strong> (xanh dương) hay <strong>Bỏ</strong> (đỏ), tên phân hệ, câu mô tả và mã thay đổi để
tra khi cần.</li>
<li>Khung <strong>Lưu ý</strong> ở cuối đợt ghi điều cần biết thêm, ví dụ có thay đổi dữ liệu hay bài hướng dẫn mới.</li>
<li>Ô chọn <strong>Phân hệ</strong> ở góc phải lọc đúng phân hệ mình dùng; đợt không có thay đổi của phân hệ đó thì ẩn.</li>
</ul>
<h3>3. Chấm đỏ</h3>
<p>Khi hệ vừa lên bản mới mà bạn chưa mở trang, một <strong>chấm đỏ nhỏ</strong> hiện trước dòng phiên bản ở chân menu trái và cạnh
mục Có gì mới trong menu tài khoản. Mở trang một lần là chấm tắt, hệ nhớ theo tài khoản nên đổi máy vẫn đúng.</p>
<h3>4. Hay gặp</h3>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Chân menu không có dòng phiên bản</td><td>Menu đang thu gọn, hoặc máy chủ chưa trả được phiên bản</td><td>Mở rộng menu; vẫn không có thì tải lại trang.</td></tr>
<tr><td>Phiên bản ghi <em>không rõ</em> ở mã bản dựng</td><td>Bản dựng không kèm mã</td><td>Không ảnh hưởng gì; số phiên bản vẫn đúng.</td></tr>
<tr><td>Thấy chức năng mới trên màn nhưng trang chưa ghi</td><td>Ghi chú đợt đó chưa cập nhật</td><td>Báo bộ phận kỹ thuật bổ sung mục.</td></tr>
</tbody>
</table>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD trang Có gì mới (bao-CR-722) + kho vector")
