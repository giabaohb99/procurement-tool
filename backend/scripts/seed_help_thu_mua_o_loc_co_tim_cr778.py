# -*- coding: utf-8 -*-
"""Bài HDSD Thu mua cho duoc-CR-778 (17/11/2026): ô lọc gõ tìm được ở các màn danh sách cụm Mua hàng (giao diện ERP mới).

Cây trợ giúp Thu mua được dựng TAY trên giao diện (không có script sở hữu), nên script này KHÔNG xóa / dựng lại cây.
Nó chỉ thêm (hoặc ghi đè nếu đã có cùng tiêu đề) MỘT bài dưới thẻ *Dành cho Nhân viên Mua hàng*, rồi nạp lại kho
vector cho đúng bài đó (`help_seed_common.run_article_upsert`).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_o_loc_co_tim_cr778.py --dry-run
    docker compose exec -T api python scripts/seed_help_thu_mua_o_loc_co_tim_cr778.py
"""
from help_seed_common import run_article_upsert

STAFF_ROOT = "Dành cho Nhân viên Mua hàng"

ARTICLES = [
    (STAFF_ROOT, "Gõ tìm trong ô lọc ở các màn danh sách Mua hàng",
     "Ô lọc nhà cung cấp, nhân sự, phân loại, bộ phận, công ty ở danh sách Mua hàng (giao diện ERP mới) gõ tìm được, không cần dấu.",
     """<h2>Gõ tìm trong ô lọc ở các màn danh sách Mua hàng</h2>
<p>Từ ngày 17/11/2026, trên giao diện ERP mới, các ô lọc chọn từ danh sách dài ở thanh lọc của các màn danh sách Mua hàng có ô <strong>gõ để tìm</strong> ngay khi mở ra, thay vì phải cuộn tìm từng dòng.</p>
<table>
<thead><tr><th>Màn danh sách</th><th>Ô lọc gõ tìm được</th></tr></thead>
<tbody>
<tr><td><strong>Đơn mua hàng</strong></td><td>Công ty, Nhà cung cấp, NSPT, Phân loại</td></tr>
<tr><td><strong>Yêu cầu mua hàng</strong></td><td>Công ty, Bộ phận, Phân loại, NSTM</td></tr>
<tr><td><strong>Yêu cầu báo giá</strong></td><td>Công ty, Bộ phận, Phân loại, NSTM</td></tr>
<tr><td><strong>Phân công phụ trách</strong></td><td>Phân loại, Phòng</td></tr>
<tr><td><strong>Tiến độ đơn mua hàng</strong></td><td>Bộ phận</td></tr>
</tbody>
</table>
<ul>
<li>Gõ <strong>không dấu cũng được</strong>: gõ <em>le nguyen</em> vẫn ra <em>Lê Nguyên</em>. Tìm theo cả tên lẫn mã (ví dụ mã nhà cung cấp, mã nhân sự).</li>
<li>Muốn bỏ lọc thì chọn lại mục <strong>Tất cả …</strong> ở đầu danh sách.</li>
<li>Kết quả lọc không đổi so với trước, chỉ cách chọn nhanh hơn. Các ô danh sách ngắn (trạng thái, hồ sơ, loại đơn, đơn gấp) giữ nguyên.</li>
</ul>
<p>Cùng đợt, ở <strong>Bộ lọc</strong> nâng cao của các màn có trường chọn theo danh mục (ví dụ Văn bản: Loại văn bản, Pháp nhân ban hành, Phòng chủ trì, Người chịu trách nhiệm, Sổ văn bản; Nhân sự: Vị trí / Chức vụ), ô giá trị nay là ô chọn có tìm kiếm thay vì ô gõ chữ — trước đây gõ tên vào ô chữ thì bộ lọc không có tác dụng.</p>"""),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Bài HDSD Thu mua duoc-CR-778: gõ tìm trong ô lọc danh sách Mua hàng")
