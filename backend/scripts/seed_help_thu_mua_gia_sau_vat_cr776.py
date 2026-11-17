# -*- coding: utf-8 -*-
"""Bài HDSD Thu mua cho duoc-CR-776 (17/11/2026): nhập Đơn giá sau VAT ở dòng hàng YCMH và ĐMH, hệ thống tự tính giá
trước thuế.

Cây trợ giúp Thu mua được dựng TAY trên giao diện (không có script sở hữu), nên script này KHÔNG xóa / dựng lại cây.
Nó chỉ thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Dành cho Nhân viên Mua hàng*, rồi nạp lại kho
vector cho đúng bài đó (`help_seed_common.run_article_upsert`). Bài người dùng tự viết không bao giờ bị đụng.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_gia_sau_vat_cr776.py --dry-run
    docker compose exec -T api python scripts/seed_help_thu_mua_gia_sau_vat_cr776.py

Nội dung khớp cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
from help_seed_common import run_article_upsert

STAFF_ROOT = "Dành cho Nhân viên Mua hàng"

ARTICLES = [
    (STAFF_ROOT, "Nhập đơn giá sau VAT ở Yêu cầu mua hàng và Đơn mua hàng",
     "Gõ giá đã gồm VAT vào ô Đơn giá sau VAT, hệ thống tự tính đơn giá chưa VAT; đổi VAT thì giữ ô vừa gõ gần nhất.",
     """<h2>Nhập đơn giá sau VAT ở Yêu cầu mua hàng và Đơn mua hàng</h2>
<p>Từ ngày 17/11/2026, mỗi dòng hàng của <strong>Yêu cầu mua hàng</strong> và <strong>Đơn mua hàng</strong> có hai ô giá cùng sửa được: <strong>Đơn giá</strong> (chưa VAT) và <strong>Đơn giá sau VAT</strong> (ở Đơn mua hàng ghi là <strong>Đơn giá (Sau VAT)</strong>). Áp dụng cho cả giao diện Thu mua cũ lẫn giao diện ERP mới, ở bảng dòng hàng và trong hộp chi tiết dòng.</p>
<h3>1. Gõ ô nào thì ô kia tự tính</h3>
<ul>
<li>Nhà cung cấp báo giá <strong>đã gồm VAT</strong>: gõ thẳng vào ô <strong>Đơn giá sau VAT</strong>, ô <strong>Đơn giá</strong> tự ra giá chưa VAT. Ví dụ VAT 8%, gõ <em>108.000</em> thì đơn giá thành <em>100.000</em>.</li>
<li>Gõ ô <strong>Đơn giá</strong> như trước thì ô sau VAT tự tính, ví dụ <em>100.000</em> ở 8% thành <em>108.000</em>.</li>
<li>Giá chia ngược thường lẻ: đơn giá chưa VAT giữ <strong>4 số lẻ</strong> (ví dụ gõ sau VAT <em>100.000</em> ở 8% ra <em>92.592,5926</em>), nên nhân lại vẫn khớp đúng số đã gõ. Giá sau VAT làm tròn 2 số lẻ.</li>
</ul>
<h3>2. Đổi VAT % sau khi đã có giá</h3>
<ul>
<li>Bạn vừa gõ ô <strong>sau VAT</strong>: hệ thống <strong>giữ giá sau VAT</strong>, tính lại đơn giá chưa VAT theo VAT mới.</li>
<li>Bạn vừa gõ ô <strong>Đơn giá</strong>, hoặc mới mở phiếu chưa gõ gì: hệ thống <strong>giữ đơn giá chưa VAT</strong> như trước nay, giá sau VAT đổi theo.</li>
</ul>
<h3>3. Những điều không đổi</h3>
<ul>
<li>Hệ thống vẫn <strong>lưu đơn giá chưa VAT</strong>; thành tiền, công nợ, báo cáo và bản in tính như cũ. Ô sau VAT chỉ là cách nhập cho tiện.</li>
<li>Tải lại trang thì ô sau VAT tính lại từ đơn giá đã lưu.</li>
<li>Đơn mua hàng <strong>nhập khẩu</strong> không tính VAT ở dòng nên không có ô sau VAT; hai giá bằng nhau.</li>
<li>Yêu cầu báo giá, phiếu khảo sát chưa có ô này.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD Thu mua duoc-CR-776: nhập đơn giá sau VAT ở YCMH, ĐMH")
