# -*- coding: utf-8 -*-
"""Bài HDSD Thu mua cho duoc-CR-775 (17/11/2026): cột NSPT của màn Tiến độ mua hàng hiện MÃ kèm TÊN nhân sự.

Cây trợ giúp Thu mua được dựng TAY trên giao diện (không có script sở hữu), nên script này KHÔNG xóa / dựng lại cây.
Nó chỉ thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Dành cho Nhân viên Mua hàng*, rồi nạp lại kho
vector cho đúng bài đó (`help_seed_common.run_article_upsert`). Bài người dùng tự viết không bao giờ bị đụng.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_nspt_cr775.py --dry-run
    docker compose exec -T api python scripts/seed_help_thu_mua_nspt_cr775.py

Nội dung khớp cẩm nang trợ lý `app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
from help_seed_common import run_article_upsert

STAFF_ROOT = "Dành cho Nhân viên Mua hàng"

ARTICLES = [
    (STAFF_ROOT, "Cột NSPT ở màn Tiến độ mua hàng: mã kèm tên nhân sự",
     "Từ 17/11/2026 cột NSPT ở Tiến độ mua hàng hiện mã nhân sự kèm tên theo hồ sơ; đơn cũ chưa gắn hồ sơ giữ chữ đã lưu.",
     """<h2>Cột NSPT ở màn Tiến độ mua hàng: mã kèm tên nhân sự</h2>
<p>Từ ngày 17/11/2026, cột <strong>NSPT</strong> (nhân sự phụ trách mua) ở màn <strong>Tiến độ mua hàng</strong> hiện <strong>mã nhân sự trước, tên sau</strong>, ví dụ <em>NSU209 · Nguyễn Văn A</em>. Áp dụng cho cả giao diện Thu mua cũ lẫn giao diện ERP mới.</p>
<h3>1. Tên lấy từ đâu</h3>
<ul>
<li>Mã và tên được tra từ <strong>hồ sơ nhân sự</strong> mà đơn mua hàng đang gắn, nên luôn là tên <strong>hiện hành</strong>: phòng Nhân sự sửa họ tên trên hồ sơ thì màn Tiến độ đổi theo ngay, không phải mở từng đơn lưu lại.</li>
<li>Trước đây cột này in đúng chữ đã lưu trên đơn, nên có đơn hiện <strong>mã trần</strong> (ví dụ <em>NM_NV</em>) thay cho tên, vì lúc tạo đơn từ yêu cầu mua hàng hệ thống lưu nhầm mã vào ô tên.</li>
</ul>
<h3>2. Đơn cũ hiện chữ khác thường</h3>
<p>Đơn chưa gắn với hồ sơ nhân sự nào (thường là dữ liệu nhập từ hệ cũ, ví dụ <em>Mr Tiên</em>) thì cột chỉ hiện <strong>đúng chữ đã lưu</strong>, không có mã đi kèm — hệ thống không tự đoán đó là ai. Muốn đơn đó hiện mã kèm tên, mở đơn, chọn lại <strong>NSPT</strong> trong danh sách nhân sự rồi lưu.</p>
<h3>3. Sắp xếp và xuất Excel</h3>
<ul>
<li>Bấm tiêu đề cột <strong>NSPT</strong> để xếp: thứ tự đi theo <strong>mã nhân sự</strong> (chữ đứng đầu ô); đơn để trống NSPT luôn nằm cuối dù xếp xuôi hay ngược.</li>
<li>Nút <strong>Xuất Excel</strong> ghi cột NSPT cùng dạng <em>Mã · Tên</em>.</li>
</ul>
<h3>4. Lưu đơn bằng mã cũng được</h3>
<p>Ô NSPT trên đơn mua hàng (kể cả khi nhập từ tệp Excel) mà nhận được <strong>mã nhân sự</strong> thay cho tên thì hệ thống tự tra đúng người theo mã và lưu họ tên đầy đủ. Đơn mới vì vậy không còn hiện mã trần.</p>
<h3>5. Hỏi Trợ lý AI</h3>
<p>Hỏi Trợ lý về một đơn mua hàng (ví dụ <em>đơn PO02344 ai phụ trách</em>), câu trả lời nêu người phụ trách cùng dạng <em>Mã · Tên</em> như trên màn hình.</p>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD Thu mua duoc-CR-775: NSPT mã kèm tên ở Tiến độ mua hàng")
