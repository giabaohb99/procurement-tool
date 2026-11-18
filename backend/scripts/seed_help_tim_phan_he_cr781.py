# -*- coding: utf-8 -*-
"""Bài HDSD cho duoc-CR-781 (18/11/2026): ô tìm phân hệ và chức năng ở màn chọn phân hệ (giao diện ERP mới).

Thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Bắt đầu*, rồi nạp lại kho vector cho đúng bài đó
(`help_seed_common.run_article_upsert`). Không xóa / dựng lại cây trợ giúp.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_tim_phan_he_cr781.py --dry-run
    docker compose exec -T api python scripts/seed_help_tim_phan_he_cr781.py
"""
from help_seed_common import run_article_upsert

START_ROOT = "Bắt đầu"

ARTICLES = [
    (START_ROOT, "Tìm nhanh phân hệ và chức năng ở màn chọn phân hệ",
     "Ô tìm ở đầu màn chọn phân hệ (hoặc phím Ctrl K / ⌘ K) ra cả phân hệ lẫn từng màn bên trong, gõ không dấu được.",
     """<h2>Tìm nhanh phân hệ và chức năng ở màn chọn phân hệ</h2>
<p>Từ ngày 18/11/2026, trên giao diện ERP mới, màn chọn phân hệ (trang đầu tiên sau khi đăng nhập) có ô <strong>Tìm phân hệ,
chức năng…</strong> ở bên phải lời chào. Không cần nhớ màn nằm trong phân hệ nào: gõ tên việc cần làm là ra đường vào.</p>
<h3>1. Mở hộp tìm</h3>
<ul>
<li>Bấm vào ô <strong>Tìm phân hệ, chức năng…</strong>, hoặc</li>
<li>nhấn <strong>Ctrl K</strong> (máy Mac: <strong>⌘ K</strong>).</li>
</ul>
<p>Chưa gõ gì thì hộp liệt kê các phân hệ bạn đang được dùng, mỗi dòng kèm mô tả ngắn.</p>
<h3>2. Gõ để tìm</h3>
<ul>
<li>Kết quả gồm cả <strong>phân hệ</strong> lẫn <strong>từng màn bên trong</strong> (ví dụ Đơn mua hàng, Nghỉ phép, Công nợ),
gom theo phân hệ; dòng chữ nhỏ cho biết màn nằm ở đâu, ví dụ <em>Thu mua › Mua hàng</em>.</li>
<li>Gõ <strong>không dấu cũng được</strong>: gõ <em>don mua</em> vẫn ra <em>Đơn mua hàng</em>. Gõ nhiều chữ thì mỗi chữ chỉ cần
có mặt ở tên màn hoặc tên phân hệ, ví dụ <em>thu mua don</em>.</li>
<li>Phần chữ khớp được tô màu để dễ nhận ra.</li>
</ul>
<h3>3. Mở màn</h3>
<ul>
<li>Dùng phím <strong>mũi tên lên / xuống</strong> để chọn, <strong>Enter</strong> để mở; hoặc bấm thẳng vào dòng.</li>
<li><strong>Esc</strong> hoặc bấm ra ngoài để đóng.</li>
</ul>
<p><strong>Lưu ý:</strong> hộp tìm chỉ hiện những phân hệ và màn bạn có quyền vào, đúng như menu bên trái của từng phân hệ.
Không thấy màn cần tìm thì có thể tài khoản chưa được phân quyền — liên hệ quản trị hệ thống.</p>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD duoc-CR-781: tìm nhanh phân hệ và chức năng ở màn chọn phân hệ")
