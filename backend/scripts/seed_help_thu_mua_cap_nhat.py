# -*- coding: utf-8 -*-
"""Nạp bài HDSD Thu mua cho đợt duoc-CR-662/663 — MỘT LỆNH: thêm/cập nhật bài rồi nạp luôn kho vector.

Cây trợ giúp Thu mua được dựng TAY trên giao diện (không có script seed sở hữu), nên script này
KHÔNG xóa / dựng lại cây như các `seed_help_*` khác. Nó chỉ:
  1. tìm thẻ cha theo TIÊU ĐỀ (id ở local, dev, prod khác nhau);
  2. có bài cùng tiêu đề dưới thẻ đó thì ghi đè nội dung, chưa có thì thêm vào cuối;
  3. nạp lại đúng các bài vừa ghi vào kho vector của trợ lý AI (seed ghi thẳng ORM nên hook nạp
     chỉ mục không chạy — xem `reindex_help_rag.py`). RAG tắt (`AI_RAG_ENABLED=false`) thì bỏ qua.
Bài người dùng tự viết trong cây không bao giờ bị đụng. Chạy lại vô hại.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_cap_nhat.py
    docker compose exec -T api python scripts/seed_help_thu_mua_cap_nhat.py --dry-run

⚠️ Nội dung phải khớp cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
from help_seed_common import run_article_upsert

STAFF_ROOT = "Dành cho Nhân viên Mua hàng"
GENERAL_ROOT = "Hướng dẫn sử dụng công cụ thu mua"

ARTICLES = [
    (STAFF_ROOT, "Chuông báo khi gửi duyệt Đơn mua hàng và Yêu cầu thanh toán",
     "Ai nhận chuông khi Đơn mua hàng hoặc Yêu cầu thanh toán được gửi duyệt, và cần kiểm gì khi không thấy chuông.",
     """<h2>Chuông báo khi gửi duyệt Đơn mua hàng và Yêu cầu thanh toán</h2>
<p>Từ ngày 22/10/2026, mỗi khi một <strong>Đơn mua hàng</strong> hoặc <strong>Yêu cầu thanh toán</strong> được gửi duyệt, hệ thống gửi chuông báo tới người duyệt để họ không phải tự mở danh sách đi tìm.</p>
<h3>1. Ai nhận chuông</h3>
<ul>
<li>Người vừa có quyền <strong>Duyệt</strong> với loại phiếu đó, <strong>vừa xem được chính phiếu đó</strong> trong phạm vi dữ liệu của mình. Người không mở được phiếu sẽ không bị báo nhầm.</li>
<li>Phiếu của <strong>phòng tự mua</strong> chỉ báo cho quản lý của phòng ấy, không báo cho cả phòng Thu mua chung.</li>
<li>Người được chọn ở ô <strong>Trưởng phòng phê duyệt</strong> trên Đơn mua hàng vẫn nhận chuông như trước.</li>
<li>Nếu không có ai phù hợp, chuông chuyển cho tài khoản quản trị có quyền duyệt, để phiếu không bị bỏ quên.</li>
</ul>
<p>Cách duyệt phiếu không thay đổi, chỉ thêm phần báo.</p>
<h3>2. Không thấy chuông thì kiểm gì</h3>
<ol>
<li>Tài khoản của người duyệt có quyền <strong>Duyệt</strong> với loại phiếu này không (màn <strong>Phân quyền</strong>).</li>
<li>Phiếu có nằm trong phạm vi dữ liệu của người duyệt không: thử mở phiếu bằng tài khoản đó, mở được thì mới nhận được chuông.</li>
<li>Phiếu đã thật sự ở trạng thái chờ duyệt chưa (lưu nháp thì chưa báo).</li>
</ol>"""),
    (STAFF_ROOT, 'Ô "Tên trên hóa đơn" tự điền từ danh mục Sản phẩm',
     "Khi nào ô Tên trên hóa đơn của dòng Đơn mua hàng tự điền, và muốn có tên sẵn thì khai ở đâu.",
     """<h2>Ô <strong>Tên trên hóa đơn</strong> tự điền từ danh mục Sản phẩm</h2>
<p>Trên dòng hàng của <strong>Đơn mua hàng</strong>, ô <strong>Tên trên hóa đơn</strong> để trống sẽ được hệ thống tự điền theo tên trên hóa đơn đã khai ở danh mục <strong>Sản phẩm</strong> của đúng mã hàng đó.</p>
<h3>1. Khi nào tự điền</h3>
<ul>
<li>Khi bấm <strong>Lưu</strong> đơn mua hàng.</li>
<li>Khi <strong>sao chép</strong> một đơn mua hàng có dòng còn trống tên.</li>
<li>Khi <strong>nhập Excel</strong> đơn mua hàng.</li>
</ul>
<h3>2. Những điều cần biết</h3>
<ul>
<li>Bạn đã gõ tên thì hệ thống <strong>giữ nguyên</strong>, không thay bằng tên trong danh mục.</li>
<li>Sản phẩm chưa khai tên trên hóa đơn thì ô vẫn trống. Muốn có tên sẵn cho mọi đơn sau, hãy khai ở danh mục <strong>Sản phẩm</strong> trước.</li>
<li>Các đơn cũ còn trống tên đã được hệ thống điền bù một lần khi cập nhật phiên bản.</li>
</ul>""",
     ["Ô «Tên trên hóa đơn» tự điền từ danh mục Sản phẩm", "Ô 'Tên trên hóa đơn' tự điền từ danh mục Sản phẩm"]),
    (GENERAL_ROOT, "Báo cáo mua hàng gom theo phòng hiện hành",
     "Vì sao báo cáo mua hàng hiện tên phòng mới sau khi đổi tên phòng, và trường hợp hai phòng trùng tên.",
     """<h2>Báo cáo mua hàng gom theo phòng hiện hành</h2>
<p>Các báo cáo mua hàng chia theo phòng ban giờ lấy <strong>tên phòng hiện hành</strong> trong danh mục Phòng ban, không còn lấy tên đã ghi trên từng phiếu.</p>
<ul>
<li>Phòng <strong>đổi tên</strong> thì báo cáo hiện tên mới, và số liệu của phòng đó dồn về <strong>một dòng</strong>, không còn tách thành hai dòng tên cũ và tên mới.</li>
<li>Phiếu cũ chưa gắn phòng ban vẫn hiện theo tên đã ghi trên phiếu.</li>
<li>Hai phòng đặt <strong>trùng tên</strong> sẽ gộp thành một dòng. Nên đặt tên phòng khác nhau để báo cáo tách đúng.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD Thu mua đợt duoc-CR-662/663 + kho vector")
