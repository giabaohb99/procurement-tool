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
     "Tạo dự án trong nhóm, gán sẵn thành viên của nhóm; chuông khi được mời, nút Mời lại; chuyển nhóm, lưu trữ và xóa vĩnh viễn dự án.",
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
</ul>
<h3>Chuông báo khi được mời</h3>
<ul>
<li>Người <strong>mới</strong> được mời vào dự án hoặc nhóm dự án (kể cả được gán sẵn lúc tạo dự án như trên) nhận chuông
<em>Bạn được mời vào dự án</em> / <em>Bạn được mời vào nhóm dự án</em>. Bấm vào chuông là mở thẳng dự án.</li>
<li>Đổi vai trò của người đã có trong dự án thì không có chuông.</li>
<li>Trong hộp <strong>Quản lý dự án</strong> (hoặc <strong>Quản lý nhóm dự án</strong>), mỗi người hiện dòng nhỏ
<em>Đã mời ngày …</em>. Người có quyền Quản trị trở lên thấy nút <strong>Mời lại</strong> (hình máy bay giấy) để gửi lại chuông
nhắc cho người đó; bấm xong nút tạm khóa 30 giây.</li>
</ul>
<h3>Đưa dự án vào lưu trữ, xóa vĩnh viễn, chuyển nhóm</h3>
<p>Chỉ <strong>chủ dự án</strong> làm được. Ở cây <strong>Danh sách dự án</strong> bên trái, rê chuột vào dòng dự án rồi bấm nút
<strong>…</strong> (hoặc mở dự án, bấm <strong>Quản lý dự án</strong> ở góc phải trên cùng):</p>
<ul>
<li><strong>Chuyển sang nhóm</strong>: chọn nhóm muốn đưa dự án vào (chỉ hiện nhóm bạn quản trị), hoặc <strong>Bỏ khỏi nhóm</strong>
để dự án đứng riêng. Chỉ có ở menu <strong>…</strong> của cây. Trên máy tính có thể <strong>kéo</strong> dòng dự án thả lên
tên nhóm, hoặc thả vào khu <em>Chưa thuộc nhóm</em> để đưa ra khỏi nhóm.</li>
<li><strong>Đưa vào lưu trữ</strong>: dự án ẩn khỏi danh sách, việc bên trong giữ nguyên. Muốn lấy lại: ở màn
<strong>Dự án</strong> bật nút <strong>Lưu trữ</strong>, mở dự án đó, vào <strong>Quản lý dự án › Thành viên &amp; thông tin</strong>
và bấm <strong>Khôi phục dự án</strong>.</li>
<li><strong>Xóa vĩnh viễn</strong> (chữ đỏ): xóa hẳn dự án cùng mọi việc, bình luận và tệp đính kèm bên trong.
<strong>Không lấy lại được</strong> — hệ thống hỏi lại một lần trước khi xóa.</li>
</ul>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD duoc-CR-783: gán thành viên nhóm khi tạo dự án")
