# -*- coding: utf-8 -*-
"""Bài HDSD cho duoc-CR-783 (18/11/2026): tạo dự án trong nhóm thì gán sẵn thành viên của nhóm vào dự án.

Thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Hướng dẫn sử dụng Dự án và Công việc* (thẻ do
`seed_help_cong_viec.py` dựng), rồi nạp lại kho vector cho đúng bài đó (`help_seed_common.run_article_upsert`). Không xóa
/ dựng lại cây.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_du_an_gan_thanh_vien_nhom_cr783.py --dry-run
    docker compose exec -T api python scripts/seed_help_du_an_gan_thanh_vien_nhom_cr783.py
"""
from help_seed_common import run_article_upsert

PROJECT_ROOT = "Hướng dẫn sử dụng Dự án và Công việc"

ARTICLES = [
    (PROJECT_ROOT, "Dự án — Tạo dự án trong nhóm và gán thành viên của nhóm",
     "Tạo dự án trong một nhóm dự án: tick sẵn gán thành viên của nhóm vào dự án, bỏ chọn được từng người.",
     """<h2>Tạo dự án trong nhóm và gán thành viên của nhóm</h2>
<p>Người trong một <strong>nhóm dự án</strong> (ví dụ nhóm DX) tự có quyền trên mọi dự án bên trong nhóm. Từ ngày
18/11/2026, khi tạo dự án mới trong nhóm, bạn gán luôn được họ thành <strong>thành viên của dự án</strong>, để họ hiện trong
danh sách thành viên và trong ô chọn người phụ trách của dự án.</p>
<h3>Cách làm</h3>
<ol>
<li>Ở cây <strong>Danh sách dự án</strong> bên trái, rê chuột vào tên nhóm rồi bấm nút <strong>Tạo dự án trong nhóm</strong>
(hoặc mở menu ba chấm của nhóm, chọn <em>Tạo dự án trong nhóm</em>).</li>
<li>Gõ tên dự án.</li>
<li>Ô <strong>Gán thành viên của nhóm vào dự án</strong> đã được tick sẵn và mọi thành viên của nhóm đã được chọn sẵn. Bỏ tick
ở người nào không cần vào dự án; bấm <em>Chọn tất cả</em> để chọn lại cả nhóm. Không muốn gán ai thì bỏ tick ô trên cùng.</li>
<li>Bấm <strong>Tạo</strong>.</li>
</ol>
<h3>Vai trò của người được gán</h3>
<ul>
<li>Mỗi người giữ đúng vai trò của họ ở nhóm (Quản trị, Thành viên, Khách xem) — vai trò hiện ở cột bên phải của danh sách.</li>
<li><strong>Chủ sở hữu</strong> của nhóm vào dự án với vai trò <strong>Quản trị</strong>, vì mỗi dự án chỉ có một chủ là người tạo.</li>
<li>Bạn (người tạo) luôn là chủ dự án nên không có tên trong danh sách chọn.</li>
</ul>
<h3>Lưu ý</h3>
<ul>
<li>Danh sách chỉ gồm người được mời <strong>thẳng vào nhóm</strong> này.</li>
<li>Chỉ áp lúc <strong>tạo</strong> dự án. Dự án tạo ở ngoài rồi mới chuyển vào nhóm thì mời thêm người ở hộp
<strong>Quản lý dự án</strong>.</li>
<li>Người không được chọn vẫn thấy dự án nhờ là thành viên nhóm, chỉ là không hiện trong danh sách thành viên của dự án.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD duoc-CR-783: gán thành viên nhóm khi tạo dự án")
