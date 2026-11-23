# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho cụm Giá nguyên vật liệu sản xuất của phân hệ Thu mua — duoc-CR-784 (21/11/2026).

Dựng 1 thẻ phân hệ *Hướng dẫn sử dụng Giá bao bì* + 8 bài theo TÁC VỤ: tổng quan (công thức, sổ giá, luật giá cũ / mới,
quyền), xem tác động khi NCC đổi giá, rà chi phí mọi sản phẩm, Bảng giá VTBB + nhập báo giá, giá các lần mua gần nhất,
lịch sử mua + biểu đồ, khai / nhập định mức bao bì, lỗi thường gặp + dành cho quản trị.

Cụm có ở CẢ HAI giao diện: ERP mới (menu Thu mua, nhóm Giá bao bì, `frontend-v2/src/modules/procurement/pages/packaging-*`)
và giao diện cũ Thu mua (menu Giá nguyên vật liệu sản xuất, `frontend/src/pages/packaging/*`, ngoại lệ D-026 người chủ duyệt
21/11/2026). Theo nếp các bài Thu mua có sẵn, mỗi bài ghi một đoạn ngắn *Trên giao diện cũ (Thu mua)* ở chỗ hai bản khác
nhau, không tách bài riêng.

Nhãn nút / tiêu đề cột chép từ mã màn (21/11/2026): `packaging-impact-page.tsx`, `packaging-code-picker.tsx`,
`packaging-impact-selected-table.tsx`, `packaging-product-columns.tsx`, `packaging-price-list-page.tsx`,
`packaging-quote-dialog.tsx`, `packaging-last-prices-toolbar.tsx`, `packaging-history-toolbar.tsx`,
`packaging-bom-crud.tsx`, `packaging-bom-import-button.tsx`, menu ở `procurement/routes.tsx`; bản cũ ở
`frontend/src/layouts/AppLayout.tsx`, `frontend/src/config/packaging-cruds.tsx`, `frontend/src/pages/ImportBatchDetail.tsx`.
Nhãn cảnh báo / xu hướng / vai trò lấy từ `backend/app/core/packaging_price_codes.py`.

CỐ Ý KHÔNG VIẾT: ngưỡng giá sàn / trần (công tắc `PACKAGING_LIMITS_ENABLED = false`, người chủ chốt 21/11/2026 "tạm thời
chưa xài") — nút Ngưỡng, cột Sàn – Trần, ô Chỉ mã ngoài ngưỡng, cảnh báo Dưới ngưỡng sàn / Vượt ngưỡng trần. Bật lại thì
thêm vào bài Bảng giá VTBB + tài liệu 21. Màn danh sách Báo giá VTBB ẩn khỏi menu: chỉ nhắc đường vào trong bài Bảng giá.

Chạy trong container api (KHÔNG chạy trên prod — prod đồng bộ Help Center theo đợt riêng):
    docker compose exec -T api python scripts/seed_help_gia_bao_bi_cr784.py --dry-run   # in cây + kiểm tiêu đề, không ghi
    docker compose exec -T api python scripts/seed_help_gia_bao_bi_cr784.py
    docker compose exec -T api python scripts/reindex_help_rag.py --purge-orphans

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (`help_seed_common.rebuild_tree`).

Phải KHỚP với `doc/erp/thu-mua/chuc-nang/21-tac-dong-gia-bao-bi.md` (mục 1–8) và cẩm nang trợ lý
`app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md` (mục Giá bao bì). Nội dung ở đây và ở tài liệu đó phải khớp nhau.
"""
import argparse

from help_seed_common import HelpArticle, SessionLocal, _delete_subtree, _descendants, rebuild_tree, ref, slugify

ROOT_TITLE = "Hướng dẫn sử dụng Giá nguyên vật liệu sản xuất"
#  Tên gốc cũ (trước 21/11/2026 chiều, khi menu còn tên "Giá bao bì"): `rebuild_tree` tìm cây theo TIÊU ĐỀ gốc nên phải
#  xóa riêng cây mang tên cũ, không thì dev / prod còn hai cây trùng nội dung.
LEGACY_ROOT_TITLES = ("Hướng dẫn sử dụng Giá bao bì",)
OVERVIEW_TITLE = "Giá NVL sản xuất — Các màn, ai được xem và giá cũ, giá mới lấy từ đâu"
IMPACT_TITLE = "Giá NVL sản xuất — Xem tác động khi nhà cung cấp đổi giá chai, nắp, nhãn, thùng"
PRODUCTS_TITLE = "Giá NVL sản xuất — Rà chi phí bao bì của mọi sản phẩm"
PRICES_TITLE = "Giá NVL sản xuất — Tra Bảng giá VTBB và nhập báo giá của nhà cung cấp"
LAST_PRICES_TITLE = "Giá NVL sản xuất — So đơn giá các lần mua gần nhất"
HISTORY_TITLE = "Giá NVL sản xuất — Xem lịch sử mua và biểu đồ giá của một mã"
BOM_TITLE = "Giá NVL sản xuất — Khai và nhập định mức bao bì từ Excel"
FAQ_TITLE = "Giá NVL sản xuất — Lỗi thường gặp, giới hạn và dành cho quản trị"

OLD_UI = "<p><strong>Trên giao diện cũ (Thu mua):</strong> "

TREE = {
    "title": ROOT_TITLE,
    "icon": "package",
    "summary": "Giá nguyên vật liệu sản xuất: xem NCC đổi giá chai, nắp, nhãn, thùng làm chi phí bao bì của sản phẩm nào tăng bao nhiêu, bảng giá VTBB, báo giá, lịch sử mua, định mức bao bì",
    "content": f"""<h2>Giá nguyên vật liệu sản xuất</h2>
<p>Cụm <strong>Giá nguyên vật liệu sản xuất</strong> giúp Thu mua trả lời một câu hỏi: <em>nhà cung cấp đổi giá một mã chai, nắp, nhãn, nhãn thùng hay thùng thì chi phí bao bì của những sản phẩm nào đổi theo, đổi bao nhiêu</em>. Có con số đó rồi mới quyết: nhận giá, thương lượng lại, đổi nhà cung cấp hay báo Kinh doanh xem lại giá bán.</p>
<p>Mở ở đâu:</p>
<ul>
<li><strong>Giao diện ERP mới:</strong> phân hệ <strong>Thu mua</strong>, nhóm menu <strong>Giá nguyên vật liệu sản xuất</strong> (Tác động giá bao bì, Tổng hợp theo sản phẩm, Bảng giá VTBB, Giá mua gần nhất, Lịch sử mua hàng, Định mức bao bì).</li>
<li><strong>Giao diện cũ (Thu mua):</strong> menu <strong>Giá nguyên vật liệu sản xuất</strong>, cùng các mục con và cùng tên như trên.</li>
</ul>
<p>Không thấy menu là tài khoản chưa được giao quyền <strong>Giá bao bì</strong>, nhờ quản trị (xem {ref(FAQ_TITLE, "Lỗi thường gặp và dành cho quản trị")}).</p>
<p>Đọc theo việc cần làm:</p>
<ul>
<li>Lần đầu dùng, muốn hiểu số trên màn từ đâu ra: {ref(OVERVIEW_TITLE, "Các màn, ai được xem và giá cũ, giá mới lấy từ đâu")}.</li>
<li>Nhà cung cấp vừa báo giá mới cho một mã, muốn biết sản phẩm nào bị ảnh hưởng: {ref(IMPACT_TITLE, "Xem tác động khi nhà cung cấp đổi giá")}.</li>
<li>Muốn nhìn một lượt sản phẩm nào đang tăng chi phí bao bì: {ref(PRODUCTS_TITLE, "Rà chi phí bao bì của mọi sản phẩm")}.</li>
<li>Muốn tra giá từng mã hoặc ghi lại báo giá nhà cung cấp gửi: {ref(PRICES_TITLE, "Tra Bảng giá VTBB và nhập báo giá")}.</li>
<li>Muốn so đơn giá 3, 5 hay 10 lần mua gần nhất: {ref(LAST_PRICES_TITLE, "So đơn giá các lần mua gần nhất")}.</li>
<li>Muốn xem từng lần mua và biểu đồ giá của một mã: {ref(HISTORY_TITLE, "Xem lịch sử mua và biểu đồ giá")}.</li>
<li>Sản phẩm mới chưa có định mức, hoặc định mức sai: {ref(BOM_TITLE, "Khai và nhập định mức bao bì từ Excel")}.</li>
</ul>""",
    "children": [
        {
            "title": OVERVIEW_TITLE,
            "icon": "book-open",
            "summary": "Công thức chi phí bao bì / chai, sổ giá (Sổ Misa tới 30/06/2026, sau đó đơn mua hàng ERP), luật giá cũ / giá mới, màu tăng giảm, In và Xuất Excel, quyền Giá bao bì và phạm vi pháp nhân",
            "content": f"""<h2>Cụm Giá nguyên vật liệu sản xuất gồm những màn nào</h2>
<table>
<thead><tr><th>Màn (menu)</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Tác động giá bao bì</strong></td><td>Chọn mã bao bì, nhập giá giả định, xem sản phẩm nào tăng chi phí bao nhiêu. Bài {ref(IMPACT_TITLE, "Xem tác động khi nhà cung cấp đổi giá")}.</td></tr>
<tr><td><strong>Tổng hợp theo sản phẩm</strong></td><td>Mọi sản phẩm có định mức, chi phí bao bì cũ so với mới, đang tăng hay giảm. Bài {ref(PRODUCTS_TITLE, "Rà chi phí bao bì của mọi sản phẩm")}.</td></tr>
<tr><td><strong>Bảng giá VTBB</strong></td><td>Mỗi mã vật tư bao bì một dòng: giá mua gần nhất, lần trước, báo giá, giá cũ / mới. Nhập báo giá ở đây. Bài {ref(PRICES_TITLE, "Tra Bảng giá VTBB và nhập báo giá")}.</td></tr>
<tr><td><strong>Giá mua gần nhất</strong></td><td>Đơn giá 3 / 5 / 10 lần mua gần nhất của từng mã, đặt cạnh nhau. Bài {ref(LAST_PRICES_TITLE, "So đơn giá các lần mua gần nhất")}.</td></tr>
<tr><td><strong>Lịch sử mua hàng</strong></td><td>Từng lần mua của một mã (hoặc của mọi thành phần trong định mức một sản phẩm), kèm biểu đồ. Bài {ref(HISTORY_TITLE, "Xem lịch sử mua và biểu đồ giá")}.</td></tr>
<tr><td><strong>Định mức bao bì</strong></td><td>Mỗi mã hàng hóa (mã HH) dùng chai, nắp, nhãn, nhãn thùng, thùng nào và bao nhiêu chai một thùng. Bài {ref(BOM_TITLE, "Khai và nhập định mức bao bì từ Excel")}.</td></tr>
</tbody>
</table>
<p>Ở mọi bảng của cụm, <strong>bấm vào một mã vật tư</strong> (chữ xanh) là mở ngay màn <strong>Lịch sử mua hàng</strong> lọc sẵn mã đó.</p>

<h2>Công thức chi phí bao bì</h2>
<ul>
<li><strong>CP bao bì / chai</strong> = Chai + Nắp + Nhãn + (Nhãn thùng + Thùng) / Quy cách thùng.</li>
<li><strong>CP bao bì / thùng</strong> = CP bao bì / chai x Quy cách thùng.</li>
</ul>
<p>Chai, nắp, nhãn tính theo từng chai; nhãn thùng và thùng là giá cho cả thùng nên chia cho số chai trong thùng. Ví dụ: chai 2.000 đ, nắp 300 đ, nhãn 150 đ, nhãn thùng 400 đ, thùng 8.000 đ, quy cách 40 chai / thùng thì CP / chai = 2.000 + 300 + 150 + (400 + 8.000) / 40 = <strong>2.660 đ</strong>, CP / thùng = 2.660 x 40 = <strong>106.400 đ</strong>.</p>
<p>Mọi giá là <strong>VNĐ, chưa VAT</strong>, theo đơn vị tính của danh mục sản phẩm. Đơn mua bằng ngoại tệ được quy ra VNĐ theo tỷ giá trên đơn.</p>

<h2>Giá lấy từ đâu</h2>
<p>Hệ thống tự gom giá vào một <strong>sổ giá</strong>, không ai phải nhập tay:</p>
<table>
<thead><tr><th>Nguồn</th><th>Vào sổ khi nào</th><th>Đổi thế nào</th></tr></thead>
<tbody>
<tr><td><strong>Lịch sử mua hàng</strong></td><td>Mỗi lần mua đã ghi vào lịch sử mua hàng (kể cả dữ liệu cũ đã nạp)</td><td>Ghi một lần, không sửa</td></tr>
<tr><td><strong>Dòng đơn mua hàng</strong> (hiện chữ <em>ĐMH đang mở</em>)</td><td>Đơn mua hàng đã duyệt, dòng chưa hủy, chưa sang lịch sử mua hàng</td><td>Sửa giá, số lượng, nhà cung cấp, ngày trên đơn thì sổ sửa theo. Dòng sang lịch sử mua hàng, bị hủy, hoặc đơn bị hủy duyệt thì dòng này tự rời sổ</td></tr>
<tr><td><strong>Sổ Misa</strong></td><td>Sổ chi tiết mua hàng Misa (đang có từ 2025 tới hết 30/06/2026, cùng số liệu với báo cáo giá NVL bản HTML)</td><td>Thu mua nạp tệp Excel xuất từ Misa bằng nút <strong>Nạp sổ Misa</strong> ở màn Lịch sử mua hàng ({ref(HISTORY_TITLE, "xem cách nạp")})</td></tr>
</tbody>
</table>
<p><strong>Mốc sổ Misa</strong> (hiện là 30/06/2026, tự dời tới ngày lớn nhất mỗi lần nạp sổ Misa mới): từ ngày này trở về trước hệ thống chỉ dùng giá trong <strong>Sổ Misa</strong>; sau mốc chỉ dùng lần mua của <strong>đơn mua hàng thật trên ERP</strong>. Lịch sử mua cũ nạp từ tệp khảo sát (có dòng sai ngày, sai giá) không còn được tính. Vì vậy số trên màn có thể khác bản HTML ở những mã đã có đơn mua hàng sau 30/06/2026: đó là giá mua mới hơn, đúng ý.</p>
<p>Lần mua có <strong>đơn giá 0</strong> vẫn được đếm vào số lần mua nhưng không bao giờ dùng làm giá.</p>

<h2>Giá cũ và giá mới</h2>
<table>
<thead><tr><th>Mã đang có</th><th>Giá mới</th><th>Giá cũ</th></tr></thead>
<tbody>
<tr><td>Có báo giá</td><td>Báo giá mới nhất (kể cả báo giá có ngày hiệu lực sau hôm nay, để xem trước tác động)</td><td>Lần mua có giá gần nhất (chưa từng mua thì bằng giá mới)</td></tr>
<tr><td>Không có báo giá, đã mua từ hai lần</td><td>Lần mua có giá gần nhất</td><td>Lần mua có giá ngay trước đó</td></tr>
<tr><td>Không có báo giá, mới mua một lần</td><td>Lần mua đó</td><td>Bằng giá mới (chênh 0)</td></tr>
<tr><td>Chưa mua lần nào, chưa có báo giá</td><td colspan="2">Chưa có giá (ô hiện gạch ngang)</td></tr>
</tbody>
</table>
<p><strong>Màu chênh lệch:</strong> số <strong>tăng hiện màu xanh</strong>, số <strong>giảm hiện màu đỏ</strong>, không đổi thì để màu thường. Màu này áp chung mọi màn, bản in và tệp Excel của cụm.</p>

<h2>In và Xuất Excel</h2>
<ul>
<li>Nút <strong>In</strong> (màn Tác động giá bao bì và Lịch sử mua hàng, cần quyền Xem) mở một thẻ mới đúng theo bộ lọc đang xem, nạp đủ mọi dòng rồi tự bật hộp in. Bản in khổ A4 ngang, trình bày như bản in của báo cáo HTML: tiêu đề báo cáo, ô lọc, thẻ số liệu và biểu đồ (Lịch sử mua hàng, khi xem một mã) và bảng.</li>
<li>Nút <strong>Xuất Excel</strong> (cần quyền Xuất) tải tệp theo đúng bộ lọc và thứ tự đang xem, tối đa 5.000 dòng. Tệp trình bày như tệp Excel của báo cáo HTML: dòng 1 tiêu đề <em>BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT — tên báo cáo</em>, dòng 2 ngày xuất và đơn vị (VNĐ, chưa VAT), đầu cột nền xanh đậm (cột chai, nắp, nhãn, nhãn thùng, thùng nền xanh lá), số có dấu nghìn, phần trăm dạng 12,4%, ô tăng xanh giảm đỏ, cố định hàng tiêu đề, có bộ lọc, in A4 ngang có số trang.</li>
</ul>

<h2>Ai được xem gì</h2>
<ul>
<li>Mọi màn cần quyền <strong>Giá bao bì</strong> (nhóm Thu mua ở màn phân quyền vai trò): <strong>Xem</strong> để mở màn, <strong>Xuất</strong> để có nút Xuất Excel, <strong>Tạo</strong> để nhập báo giá và định mức, <strong>Sửa</strong> / <strong>Xóa</strong> để sửa, xóa định mức hay báo giá.</li>
<li><strong>Giá tính theo pháp nhân bạn được xem:</strong> phạm vi của quyền Giá bao bì lọc sổ giá theo công ty mua. Hai người cùng mở một mã có thể thấy giá khác nhau nếu được xem các pháp nhân khác nhau.</li>
<li>Định mức bao bì và báo giá là danh mục dùng chung: ai có quyền Xem đều thấy đủ.</li>
</ul>
{OLD_UI}cùng dữ liệu, cùng công thức, cùng quyền. Đơn giá hiện tới 4 chữ số lẻ (giao diện mới làm tròn: dưới 100.000 đ giữ tối đa 2 chữ số lẻ, từ 100.000 đ làm tròn tới đồng).</p>""",
        },
        {
            "title": IMPACT_TITLE,
            "icon": "bar-chart",
            "summary": "Màn Tác động giá bao bì: chọn mã (hoặc cả nhóm), nhập giá giả định, đọc bảng mã đã chọn và sản phẩm bị ảnh hưởng, lọc nâng cao, xếp mọi cột kể cả Chai / Nắp / Nhãn, ghi chú cảnh báo, In, Xuất Excel",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Nhà cung cấp báo tăng (hoặc giảm) giá một hay nhiều mã bao bì, hoặc bạn muốn thử "nếu nắp lên 350 đ thì sao" trước khi chốt giá. Mở <strong>Thu mua › Giá nguyên vật liệu sản xuất › Tác động giá bao bì</strong> (màn có tiêu đề <strong>Tác động tăng giá bao bì</strong>).</p>

<h2>Các bước</h2>
<ol>
<li>Bấm vào ô <strong>Chọn mã chai / nắp / nhãn / nhãn thùng / thùng</strong>. Gõ mã, tên hoặc tên nhóm để lọc, bấm từng dòng để chọn. Muốn chọn cả nhóm: gõ tên nhóm (ví dụ <em>chai</em>, <em>nắp</em>, <em>nhãn</em>; nhiều nhóm thì cách nhau dấu phẩy, ví dụ <em>nhãn, thùng</em>) rồi bấm <strong>Chọn tất cả</strong>. Gõ không cần dấu, nhiều từ thì mã phải có đủ các từ (<em>nắp 0085</em> ra NAP0085). Mỗi lượt chọn tối đa 500 mã.</li>
<li>Mã đã chọn hiện thành nhãn nhỏ trong ô. Bấm dấu <strong>x</strong> trên một nhãn để bỏ mã đó; bấm dấu <strong>x</strong> ở cuối ô (<em>Bỏ hết mã đã chọn</em>) để bỏ tất cả.</li>
<li>Bảng <strong>mã đã chọn</strong> hiện ngay dưới ô: Mã, Tên vật tư, Nhóm, Giá cũ, Giá mới, <strong>Giá giả định</strong>, Chênh lệch, %, <strong>Số SP bị ảnh hưởng</strong> (số sản phẩm có dùng mã trong định mức), Min, Max, Ghi chú. Bấm dấu <strong>x</strong> cuối dòng cũng bỏ được mã.</li>
<li>Muốn thử giá chưa chốt: gõ vào ô <strong>Nhập giá</strong> (nền vàng) ở cột Giá giả định. Khoảng nửa giây sau khi ngừng gõ, mọi con số bên dưới tính lại theo giá đó. Xóa trắng ô là quay về giá mới.</li>
<li>Muốn biết sản phẩm nào tăng chi phí nhiều nhất: ở bảng sản phẩm bấm tiêu đề cột <strong>Tăng/giảm /thùng</strong> để xếp giảm dần. Số sản phẩm bị ảnh hưởng hiện ở chân bảng.</li>
<li>Đọc bảng sản phẩm bên dưới (xem mục tiếp). Cần gửi đi thì bấm <strong>Xuất Excel</strong> ở góc phải trên cùng: tệp có hai sheet <em>Sản phẩm bị ảnh hưởng</em> và <em>Mã đã chọn</em>, theo đúng giá giả định đang gõ, bộ lọc và thứ tự đang xếp. Cần bản giấy thì bấm <strong>In</strong> (phải chọn ít nhất một mã).</li>
</ol>
<p>Ô <strong>Khoảng ngày tính min – max</strong> ở góc phải chỉ đổi hai cột Min, Max (giá thấp nhất, cao nhất trong khoảng ngày đó). Giá cũ, giá mới không phụ thuộc ô này.</p>

<h2>Đọc bảng sản phẩm bị ảnh hưởng</h2>
<p>Mỗi dòng là một sản phẩm (mã HH) có dùng ít nhất một mã đã chọn trong định mức:</p>
<table>
<thead><tr><th>Cột</th><th>Nghĩa</th></tr></thead>
<tbody>
<tr><td>Mã HH, Tên hàng hóa, Quy cách thùng</td><td>Lấy từ định mức bao bì.</td></tr>
<tr><td>Chai, Nắp, Nhãn, Nhãn thùng (giá /thùng), Thùng (giá /thùng)</td><td>Mã thành phần và giá. Giá đổi thì hiện <em>giá cũ → giá đang dùng</em>; mã nằm trong danh sách đang chọn được tô nền vàng; chưa có giá thì ghi <em>chưa có giá</em>.</td></tr>
<tr><td>CP bao bì/chai cũ, CP bao bì/chai mới</td><td>Chi phí bao bì một chai theo giá cũ và theo giá đang dùng (giá giả định nếu có).</td></tr>
<tr><td>Tăng/giảm /chai, Tăng/giảm /thùng</td><td>Chênh lệch chi phí một chai và một thùng. Xanh là tăng, đỏ là giảm.</td></tr>
<tr><td>Ghi chú</td><td>Cảnh báo của dòng, ví dụ <em>Thiếu giá thành phần: Nhãn</em> (xem bảng dưới).</td></tr>
</tbody>
</table>
<h2>Lọc và xếp</h2>
<ul>
<li><strong>Bảng mã đã chọn</strong>: chọn mã của nhiều nhóm thì có hàng chip <strong>Tất cả</strong> · <strong>Chai</strong> · <strong>Nắp</strong> · <strong>Nhãn</strong>… kèm số mã; bấm một chip để chỉ xem mã của nhóm đó (chỉ lọc bảng này, không đổi các mã đang tính).</li>
<li><strong>Bảng sản phẩm</strong>: ô <strong>Tìm mã HH, tên, mã thành phần…</strong> và nút <strong>Lọc nâng cao</strong>. Trong hộp lọc nâng cao: <strong>Xu hướng chi phí</strong> (Tăng, Giảm, Không đổi, Chưa có giá), <strong>Có mã đã chọn ở vai trò</strong> (Chai, Nắp, Nhãn, Nhãn thùng, Thùng), các khoảng <strong>Từ – Đến</strong> cho Quy cách thùng, Tăng/giảm /chai, Tăng/giảm /thùng, CP bao bì/chai mới, và ô <strong>Chỉ sản phẩm có cảnh báo</strong>. Bấm <strong>Áp dụng</strong> để lọc, <strong>Xóa lọc</strong> để bỏ; nút hiện số điều kiện đang bật.</li>
<li>Bấm tiêu đề cột để xếp, kể cả các cột <strong>Chai</strong>, <strong>Nắp</strong>, <strong>Nhãn</strong>, <strong>Nhãn thùng</strong>, <strong>Thùng</strong> (xếp theo giá đang dùng của thành phần đó). Ví dụ xếp <strong>Tăng/giảm /thùng</strong> giảm dần để thấy sản phẩm bị ảnh hưởng nặng nhất.</li>
<li>Bảng chia trang; chọn cả nhóm chai có thể ra hàng nghìn sản phẩm, tổng số sản phẩm hiện ở chân bảng. Xuất Excel và In theo đúng bộ lọc, thứ tự đang xem.</li>
</ul>

<h2>Ghi chú cảnh báo nghĩa là gì</h2>
<table>
<thead><tr><th>Ghi chú</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Thiếu giá chai</td><td>Mã chai chưa có lần mua có giá, chưa có báo giá. Không tính được chi phí, hai ô CP để trống.</td><td>Nhập báo giá cho mã chai ở {ref(PRICES_TITLE, "Bảng giá VTBB")}.</td></tr>
<tr><td>Thiếu giá thành phần: Nắp / Nhãn / Nhãn thùng / Thùng</td><td>Thành phần đó có mã nhưng chưa có giá; hệ thống tính phần đó bằng 0 nên CP thấp hơn thật.</td><td>Nhập báo giá cho mã đó.</td></tr>
<tr><td>Chưa khai mã thành phần: Nắp / Nhãn</td><td>Định mức của sản phẩm bỏ trống ô nắp hoặc nhãn.</td><td>Sửa định mức ({ref(BOM_TITLE, "Định mức bao bì")}) nếu sản phẩm thật có dùng.</td></tr>
<tr><td>Thiếu quy cách thùng</td><td>Có nhãn thùng / thùng nhưng quy cách thùng bằng 0; phần thùng tính bằng 0.</td><td>Điền Quy cách thùng ở định mức.</td></tr>
<tr><td>ĐVT mua khác ĐVT danh mục</td><td>Lần mua gần nhất ghi đơn vị tính khác danh mục sản phẩm (ví dụ mua theo cuộn, danh mục theo cái), con số có thể lệch bậc.</td><td>Kiểm đơn mua hàng đó; báo người giữ danh mục sản phẩm nếu danh mục sai.</td></tr>
</tbody>
</table>
<p>Bảng mã đã chọn báo <em>Các mã đã chọn chưa có trong định mức nào.</em> nghĩa là chưa sản phẩm nào khai dùng các mã đó, nên không có tác động để tính.</p>
{OLD_UI}menu <strong>Giá nguyên vật liệu sản xuất › Tác động giá bao bì</strong>; các bước, nút và cột như trên. Đơn giá hiện tới 4 chữ số lẻ.</p>""",
        },
        {
            "title": PRODUCTS_TITLE,
            "icon": "pie-chart",
            "summary": "Màn Tổng hợp theo sản phẩm: mọi sản phẩm có định mức, CP cũ / mới một chai, chênh một chai và một thùng, % chênh, chip Tăng / Giảm / Không đổi / Chưa có giá kèm số đếm",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Đầu kỳ báo giá, hoặc khi Kinh doanh hỏi "sản phẩm nào đang tăng chi phí bao bì". Khác màn {ref(IMPACT_TITLE, "Tác động giá")} (bắt đầu từ mã bao bì), màn này bắt đầu từ <strong>sản phẩm</strong>: mọi mã HH có định mức, giá cũ so với giá mới hiện hành, không có giá giả định.</p>
<p>Mở <strong>Thu mua › Giá nguyên vật liệu sản xuất › Tổng hợp theo sản phẩm</strong>.</p>

<h2>Lọc nhanh bằng chip</h2>
<p>Hàng chip trên bảng kèm số sản phẩm của từng loại: <strong>Tất cả</strong>, <strong>Tăng</strong> (chi phí bao bì tăng, cần xem lại giá bán), <strong>Giảm</strong>, <strong>Không đổi</strong>, <strong>Chưa có giá</strong> (thiếu giá chai nên chưa tính được). Bấm một chip để chỉ xem loại đó; bấm <strong>Tất cả</strong> để bỏ lọc. Số trên chip đếm theo từ khóa đang tìm.</p>

<h2>Đọc bảng</h2>
<ul>
<li>Cột đầu: <strong>Mã HH</strong> (bấm để mở {ref(HISTORY_TITLE, "Lịch sử mua hàng")} ở chế độ theo mã sản phẩm, gồm mọi thành phần của định mức), <strong>Tên hàng hóa</strong>, <strong>Quy cách</strong>.</li>
<li>Con số cần đọc đứng trước: <strong>CP cũ /chai</strong>, <strong>CP mới /chai</strong>, <strong>Chênh /chai</strong>, <strong>Chênh /thùng</strong>, <strong>% chênh</strong>, <strong>Xu hướng</strong>.</li>
<li>Sau đó là năm ô thành phần (Chai, Nắp, Nhãn, Nhãn thùng, Thùng: mã và giá cũ → mới, mã bấm được) và <strong>Ghi chú</strong> (cùng bộ cảnh báo như màn Tác động giá).</li>
</ul>
<p>Ô <strong>Tìm mã HH, tên, mã thành phần…</strong> tìm không cần dấu. Bấm tiêu đề cột để xếp, ví dụ <strong>Chênh /thùng</strong> giảm dần. <strong>Xuất Excel</strong> ra đúng bộ lọc và thứ tự đang xem (tối đa 5.000 dòng).</p>
{OLD_UI}menu <strong>Giá nguyên vật liệu sản xuất › Tổng hợp theo sản phẩm</strong>, cùng chip, cột và nút.</p>""",
        },
        {
            "title": PRICES_TITLE,
            "icon": "coins",
            "summary": "Bảng giá VTBB: giá mua gần nhất, lần trước, báo giá mới, giá cũ / mới / chênh / %, Min, Max, số SP đang dùng; nút Báo giá mới và nút Báo giá từng dòng để ghi báo giá của NCC",
            "content": f"""<h2>Tra giá từng mã</h2>
<p>Mở <strong>Thu mua › Giá nguyên vật liệu sản xuất › Bảng giá VTBB</strong>. Mỗi mã vật tư bao bì một dòng:</p>
<table>
<thead><tr><th>Cột</th><th>Nghĩa</th></tr></thead>
<tbody>
<tr><td>Mã VTBB, Tên vật tư, Nhóm, ĐVT</td><td>Theo danh mục sản phẩm. Bấm mã để mở lịch sử mua của mã.</td></tr>
<tr><td>Số lần mua, Mua gần nhất</td><td>Số lần mua (kể cả lần đơn giá 0) và ngày mua cuối.</td></tr>
<tr><td>Giá mua gần nhất, Giá mua lần trước</td><td>Hai lần mua có giá gần nhất.</td></tr>
<tr><td>Báo giá mới</td><td>Báo giá mới nhất của mã, dòng dưới là ngày hiệu lực.</td></tr>
<tr><td>Giá cũ, Giá mới, Chênh lệch, %</td><td>Theo luật ở bài {ref(OVERVIEW_TITLE, "giá cũ, giá mới lấy từ đâu")}.</td></tr>
<tr><td>Min, Max</td><td>Giá thấp nhất, cao nhất trong sổ giá; chọn <strong>Khoảng ngày tính min – max</strong> ở góc phải để chỉ tính trong khoảng đó. Hai cột này ẩn sẵn, mở ở nút <strong>Cột</strong> của bảng.</td></tr>
<tr><td>Số SP đang dùng</td><td>Số sản phẩm có mã trong định mức.</td></tr>
<tr><td>Ghi chú</td><td>Cảnh báo của mã (ví dụ ĐVT mua khác ĐVT danh mục). Cột ẩn sẵn, mở ở nút <strong>Cột</strong>.</td></tr>
</tbody>
</table>
<p>Thanh lọc: ô <strong>Tìm mã, tên vật tư…</strong>, chip nhóm (<strong>Tất cả</strong>, Chai, Nắp, Nhãn…), và nút phạm vi <strong>Mã trong định mức</strong> (mặc định: mã đang dùng trong định mức và mã đã có báo giá) / <strong>Mọi mã có giá</strong> (thêm mọi mã có trong sổ giá). Bấm tiêu đề cột để xếp; <strong>Xuất Excel</strong> ra đúng bộ lọc và thứ tự đang xem.</p>

<h2>Nhập báo giá của nhà cung cấp</h2>
<p>Nhà cung cấp gửi giá mới (qua thư, Zalo, bảng báo giá) thì ghi vào hệ thống để màn Tác động giá dùng làm <strong>giá mới</strong>:</p>
<ol>
<li>Ở dòng của mã, bấm nút <strong>Báo giá</strong> cuối dòng (mã điền sẵn, con trỏ nằm ở ô đơn giá). Mã chưa có trong bảng thì bấm <strong>Báo giá mới</strong> ở góc phải trên cùng rồi gõ <strong>Mã VTBB</strong> (ví dụ NAP0085).</li>
<li>Điền <strong>Đơn giá (VNĐ, chưa VAT)</strong> theo đơn vị tính của danh mục, <strong>Ngày hiệu lực</strong>; tùy chọn <strong>Mã NCC</strong> (bỏ trống nếu chưa rõ), <strong>VAT (%)</strong>, <strong>Ghi chú</strong>.</li>
<li>Bấm <strong>Lưu báo giá</strong>. Bảng giá, màn Tác động giá và Tổng hợp theo sản phẩm tính lại ngay.</li>
</ol>
<ul>
<li>Báo giá có <strong>ngày hiệu lực ở tương lai vẫn tính ngay</strong> là giá mới, để xem trước tác động trước khi giá áp dụng.</li>
<li>Một mã có nhiều báo giá thì báo giá có ngày hiệu lực muộn nhất thắng. Báo giá không vào sổ giá: nó không thành "lần mua", không đổi số lần mua hay giá mua gần nhất.</li>
<li>Báo giá nhập nhầm: nhập lại báo giá đúng với <strong>cùng ngày hiệu lực</strong>, báo giá nhập sau thắng. Muốn sửa hay xóa hẳn báo giá nhầm thì dùng màn danh sách <strong>Báo giá VTBB</strong>: màn này không có trong menu, mở bằng đường <em>/procurement/packaging-cost/quotes</em>; bấm một dòng để mở hộp sửa (<strong>Lưu thay đổi</strong>), nút xóa trong hộp cần quyền Xóa.</li>
</ul>
<p>Hộp báo lỗi: <em>Nhập mã vật tư bao bì.</em>, <em>Nhập đơn giá báo giá (lớn hơn 0).</em>, <em>Chọn ngày hiệu lực.</em> là thiếu ô tương ứng.</p>

<h2>Nhập nhiều báo giá một lần từ Excel</h2>
<ol>
<li>Bấm <strong>Nhập báo giá</strong> ở góc phải trên cùng (cạnh Báo giá mới). Trong hộp, bấm <strong>Tải tệp mẫu</strong> để lấy tệp <em>mau-nhap-bao-gia-vtbb.xlsx</em>.</li>
<li>Điền mỗi báo giá một dòng: <strong>Mã VTBB</strong>, <strong>Đơn giá</strong> (VNĐ chưa VAT), <strong>Ngày hiệu lực</strong> (bắt buộc); <strong>Mã NCC</strong>, <strong>VAT (%)</strong> (ghi 8 là 8%), <strong>Ghi chú</strong> (tùy chọn). Sheet <em>Hướng dẫn</em> trong tệp có giải thích và ví dụ.</li>
<li>Chọn tệp, bấm <strong>Chạy thử</strong>: hệ thống chưa ghi gì, chuyển sang trang lô ở Quản lý Import với nhật ký từng dòng (thêm, sửa giá cũ → mới, dòng lỗi).</li>
<li>Đúng rồi thì bấm <strong>Ghi thật</strong>.</li>
</ol>
<ul>
<li>Trùng <strong>mã + mã NCC + ngày hiệu lực</strong> với báo giá đã có thì cập nhật đơn giá, VAT, ghi chú; chưa có thì thêm. Báo giá đang có mà không nằm trong tệp giữ nguyên.</li>
<li>Mã chưa có trong danh mục sản phẩm, đơn giá trống / bằng 0, ngày sai bị bỏ và ghi lỗi; các dòng khác vẫn nhập.</li>
<li>Cần quyền <strong>Tạo</strong> của Giá bao bì và quyền tạo, xem Quản lý Import. Lô nhập báo giá chưa hoàn tác được: sửa hay xóa báo giá nhầm ở màn Báo giá VTBB.</li>
</ul>
{OLD_UI}menu <strong>Giá nguyên vật liệu sản xuất › Bảng giá VTBB</strong>. Nút <strong>Báo giá mới</strong> và nút <strong>Báo giá</strong> từng dòng mở cùng hộp nhập như trên. Cột <strong>Min</strong>, <strong>Max</strong> hiện sẵn; đơn giá hiện tới 4 chữ số lẻ. Danh sách Báo giá VTBB (không có trong menu, đường <em>/product-price-quotes</em>) là màn danh sách chung: bấm một dòng mở <strong>trang chi tiết</strong> (không phải hộp thoại) để sửa rồi bấm <strong>Lưu</strong>, hoặc <strong>Xóa</strong>.</p>""",
        },
        {
            "title": LAST_PRICES_TITLE,
            "icon": "clipboard-list",
            "summary": "Màn Giá mua gần nhất: đơn giá 3 / 5 / 10 lần mua có giá gần nhất của từng mã VTBB, ngày, NCC, biến động lần 1 so lần 2 / lần n, giá TB, lọc NCC, ngày, xu hướng, ngưỡng %",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Muốn xem giá một mã đi lên hay đi xuống qua nhiều lần mua, mua của nhà cung cấp nào, để có lý lẽ khi thương lượng. Mở <strong>Thu mua › Giá nguyên vật liệu sản xuất › Giá mua gần nhất</strong>.</p>

<h2>Đọc bảng</h2>
<ul>
<li>Mỗi mã VTBB một dòng. Nhóm cột <strong>Thông tin VTBB</strong>: Mã VTBB, Tên vật tư, Nhóm, ĐVT, Số lần có giá.</li>
<li>Mỗi lần mua một nhóm cột có tiêu đề gộp: <strong>Lần 1 (gần nhất)</strong>, Lần 2, Lần 3… Trong mỗi nhóm: <strong>Ngày mua</strong>, <strong>Nhà cung cấp</strong>, <strong>Đơn giá</strong> (bật <strong>Hiện số lượng</strong> để thêm cột Số lượng). Đơn giá xanh là đắt hơn lần mua trước nó, đỏ là rẻ hơn.</li>
<li>Nhóm <strong>Biến động</strong>: <strong>Lần 1 so lần 2</strong> và <strong>Lần 1 so lần n</strong> (phần trăm). Nhóm <strong>Giá TB</strong>: giá trung bình của n lần.</li>
<li>Chỉ tính lần mua <strong>có giá</strong>; lần mua đơn giá 0 bị bỏ qua.</li>
</ul>

<h2>Lọc</h2>
<table>
<thead><tr><th>Ô lọc</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Tìm mã, tên, nhóm, nhà cung cấp…; chip nhóm</td><td>Lọc theo chữ và theo nhóm (chip kèm số mã).</td></tr>
<tr><td>Số lần hiển thị</td><td>3, 5 (mặc định) hoặc 10 lần mua.</td></tr>
<tr><td>Phạm vi mã</td><td><strong>Định mức + báo giá</strong> (mặc định) hoặc <strong>Mọi mã</strong> có trong sổ giá.</td></tr>
<tr><td>Nhà cung cấp</td><td>Giữ các mã có nhà cung cấp đó trong các lần mua đang hiện (không cắt bớt lần mua của nhà cung cấp khác).</td></tr>
<tr><td>Khoảng ngày mua</td><td>Chỉ xếp hạng các lần mua trong khoảng ngày.</td></tr>
<tr><td>Biến động lần 1 so lần 2; Biến động từ (%)</td><td>Chỉ mã <strong>Tăng</strong> / <strong>Giảm</strong> / <strong>Không đổi</strong>; chỉ mã biến động từ bao nhiêu phần trăm trở lên (0 là không lọc).</td></tr>
<tr><td>Chỉ mã đã có giá (bật sẵn); Chỉ mã đang dùng trong định mức; Hiện số lượng</td><td>Công tắc bật / tắt.</td></tr>
</tbody>
</table>
<p><strong>Xuất Excel</strong> ra đúng bộ lọc, số lần và thứ tự đang xem; bật Hiện số lượng thì tệp có thêm cột số lượng.</p>
{OLD_UI}menu <strong>Giá nguyên vật liệu sản xuất › Giá mua gần nhất</strong>, cùng bộ lọc và cột; đơn giá hiện tới 4 chữ số lẻ.</p>""",
        },
        {
            "title": HISTORY_TITLE,
            "icon": "calendar",
            "summary": "Màn Lịch sử mua hàng của cụm Giá NVL sản xuất: từng lần mua theo mã VTBB hoặc mã sản phẩm, thẻ số liệu, biểu đồ đơn giá khi chọn một mã, cột Kho, nguồn Sổ Misa / đơn mua hàng, In, Xuất Excel",
            "content": f"""<h2>Mở màn</h2>
<p>Mở <strong>Thu mua › Giá nguyên vật liệu sản xuất › Lịch sử mua hàng</strong>, hoặc bấm vào bất kỳ mã vật tư nào ở các bảng của cụm (màn mở sẵn đúng mã đó). Màn này khác tab Lịch sử mua hàng trên chi tiết sản phẩm: nó đọc sổ giá của cụm Giá nguyên vật liệu sản xuất nên có cả dòng đơn mua hàng đang mở.</p>

<h2>Chọn xem cái gì</h2>
<ol>
<li>Nút <strong>Theo mã VTBB</strong> (mặc định) hoặc <strong>Theo mã sản phẩm</strong>.</li>
<li>Theo mã VTBB: bấm ô chọn, gõ mã, tên hoặc tên nhóm để chọn một hay nhiều mã. Để trống là xem mọi mã VTBB.</li>
<li>Theo mã sản phẩm: chọn mã HH, màn hiện mọi lần mua của các thành phần trong định mức sản phẩm đó, kèm cột <strong>Vai trò</strong> (Chai, Nắp…).</li>
<li>Lọc thêm: <strong>Nhà cung cấp</strong>, <strong>Khoảng ngày mua</strong>, ô <strong>Tìm mã, tên, nhà cung cấp…</strong>.</li>
</ol>

<h2>Đọc kết quả</h2>
<ul>
<li><strong>Thẻ số liệu</strong> tính trên toàn bộ kết quả lọc. Chọn <strong>đúng một mã</strong>: Tổng số lần mua (kèm khoảng ngày), Tổng số lượng mua (kèm ĐVT), Tổng giá trị mua (kèm số lần có giá), Giá thấp nhất – cao nhất (kèm giá bình quân gia quyền), Gần nhất so với lần đầu (tăng xanh, giảm đỏ, kèm giá đầu → giá gần nhất), Số nhà cung cấp. Nhiều mã hoặc mọi mã: Số mã đã chọn, Tổng số lần mua, Tổng giá trị mua, Số nhà cung cấp. Chế độ theo mã sản phẩm: Số sản phẩm, Mã vật tư liên quan, Số dòng lịch sử, Số nhà cung cấp.</li>
<li><strong>Biểu đồ Diễn biến đơn giá</strong> hiện khi chọn đúng một mã: mỗi điểm là một lần mua có giá, rê chuột để xem ngày, đơn giá, nhà cung cấp, số lượng.</li>
<li>Bảng, mới nhất trước: Lần, Ngày mua, Mã VTBB, Tên vật tư, Nhà cung cấp, <strong>Kho</strong> (kho nhập hàng; lần mua trong Sổ Misa lấy kho của Misa, lần mua trên ERP lấy kho của dòng đơn mua hàng), Số lượng, Đơn giá, Thành tiền, <strong>So lần trước</strong> (chênh với lần mua có giá liền trước của cùng mã; xanh đắt hơn, đỏ rẻ hơn), <strong>Nguồn</strong> (mã đơn mua hàng bấm để mở đơn, hoặc chữ <em>Sổ Misa</em>). Ô tìm tìm được cả theo tên kho; bấm tiêu đề cột Kho để xếp.</li>
<li>Nhãn <strong>ĐMH đang mở</strong>: dòng của đơn mua hàng đã duyệt, chưa hoàn thành; giá còn có thể đổi nếu đơn được sửa.</li>
<li>Lần mua đơn giá 0 vẫn hiện để đối chiếu, nhưng không tính vào giá bình quân, thấp nhất, cao nhất và biểu đồ.</li>
</ul>
<p><strong>Xuất Excel</strong> ra đúng bộ lọc và thứ tự đang xem (tối đa 5.000 dòng). <strong>In</strong> mở bản in A4 ngang gồm ô lọc, thẻ số liệu, biểu đồ và mọi dòng.</p>

<h2>Nạp sổ Misa</h2>
<ol>
<li>Xuất <strong>Sổ chi tiết mua hàng</strong> từ Misa ra Excel, giữ nguyên tiêu đề cột của Misa (cần các cột Ngày, Mã hàng, Số lượng, Đơn giá; nên có Mã / Tên nhà cung cấp, Tên kho, ĐVT). Chưa có sẵn thì bấm <strong>Tải tệp mẫu</strong> trong hộp nạp.</li>
<li>Bấm <strong>Nạp sổ Misa</strong> ở góc phải trên cùng, chọn tệp, bấm <strong>Chạy thử</strong>.</li>
<li>Ở trang lô, đọc dòng tóm tắt đầu nhật ký: số lần mua trong tệp, khoảng ngày, số dòng <em>giữ / thêm / bỏ</em>, mốc sổ Misa cũ → mới, các dòng bị bỏ qua. Đúng thì bấm <strong>Ghi thật</strong>.</li>
</ol>
<ul>
<li>Chỉ dữ liệu Misa <strong>trong khoảng ngày của tệp</strong> bị thay: lần mua trùng giữ nguyên, lần mua mới thêm, lần mua không còn trong tệp bị bỏ. Ngoài khoảng ngày giữ nguyên, nên nạp từng tháng cũng được.</li>
<li>Mã đầu PPA, CKC, CPM, CPN và dòng số lượng 0 bị bỏ qua (giống báo cáo HTML). Đơn giá trống vẫn nhận nhưng không làm giá.</li>
<li>Mốc sổ Misa dời tới ngày lớn nhất đã nạp; giá các màn tính lại ngay.</li>
<li>Cần quyền <strong>Sửa</strong> của Giá bao bì (vì đổi giá cả cụm) và quyền tạo, xem Quản lý Import. Lô nạp sổ Misa chưa hoàn tác được: nạp lại tệp đúng để sửa.</li>
</ul>
{OLD_UI}menu <strong>Giá nguyên vật liệu sản xuất › Lịch sử mua hàng</strong>, cùng chế độ, bộ lọc, biểu đồ và cột; đơn giá hiện tới 4 chữ số lẻ.</p>""",
        },
        {
            "title": BOM_TITLE,
            "icon": "boxes",
            "summary": "Định mức bao bì theo mã HH: chai, nắp, nhãn, nhãn thùng, thùng, quy cách thùng; thêm, sửa từng dòng, Nhập từ Excel tệp DATA_CHAI.xlsx qua Quản lý Import (Chạy thử rồi Ghi thật)",
            "content": f"""<h2>Định mức bao bì là gì</h2>
<p>Mỗi mã hàng hóa (mã HH) một dòng: dùng mã <strong>chai</strong>, <strong>nắp</strong>, <strong>nhãn</strong> nào (tính theo chai), mã <strong>nhãn thùng</strong>, <strong>thùng</strong> nào (tính theo thùng) và <strong>quy cách thùng</strong> (bao nhiêu chai một thùng). Thu mua tự khai và giữ danh mục này; mọi con số chi phí của cụm Giá nguyên vật liệu sản xuất đều đọc từ đây. Mở <strong>Thu mua › Giá nguyên vật liệu sản xuất › Định mức bao bì</strong>.</p>
<p>Ở bảng, mã thành phần <strong>tô đỏ</strong> kèm chữ <em>chưa có trong danh mục</em> là mã chưa có trong danh mục sản phẩm (gõ sai, hoặc chưa tạo sản phẩm); quy cách thùng ghi <em>chưa có</em> là đang bằng 0.</p>

<h2>Thêm hoặc sửa một dòng</h2>
<ol>
<li>Bấm <strong>Thêm định mức</strong> để thêm; bấm vào một dòng để sửa.</li>
<li>Điền <strong>Mã HH</strong> (bắt buộc, không sửa được sau khi tạo), <strong>Quy cách thùng (chai / thùng)</strong> (0 = chưa có, phần nhãn thùng / thùng sẽ không tính được), <strong>Tên hàng hóa</strong>, <strong>Tên pháp lý</strong>.</li>
<li>Mục <strong>Thành phần bao bì</strong>: <strong>Mã chai</strong> (bắt buộc), Mã nắp, Mã nhãn, Mã nhãn thùng, Mã thùng.</li>
<li>Bấm <strong>Tạo mới</strong> (hoặc <strong>Lưu thay đổi</strong> khi sửa). Xóa một định mức: mở dòng, bấm nút xóa trong hộp (cần quyền Xóa).</li>
</ol>

<h2>Nhập hàng loạt từ Excel</h2>
<ol>
<li>Ở màn Định mức bao bì, bấm <strong>Nhập từ Excel</strong>. Hộp <strong>Nhập định mức bao bì</strong> mở ra. Chưa có tệp thì bấm <strong>Tải tệp mẫu</strong> (sheet MAP_SP đúng cột A–K, kèm sheet Hướng dẫn).</li>
<li>Chọn tệp <strong>DATA_CHAI.xlsx</strong> (chỉ nhận .xlsx). Tệp có sheet <strong>MAP_SP</strong>, hoặc hai sheet <strong>data</strong> + <strong>DATA CHUNG</strong>.</li>
<li>Bấm <strong>Chạy thử</strong>. Hệ thống chưa ghi gì, chỉ đọc tệp rồi chuyển sang trang lô ở <strong>Quản lý Import</strong>.</li>
<li>Ở trang lô, đọc nhật ký từng dòng: dòng nào thêm mới, dòng nào đổi ô nào (cũ → mới), dòng nào lỗi.</li>
<li>Đúng rồi thì bấm <strong>Ghi thật</strong>, xác nhận ở hộp hỏi lại. Hệ thống chạy lại đúng tệp đó và lưu.</li>
</ol>
<ul>
<li>Mã HH đã có thì cập nhật, chưa có thì tạo; dòng đang có mà không nằm trong tệp thì <strong>giữ nguyên</strong> (không bị xóa).</li>
<li>Mã HH so khớp không cần số 0 đầu: <em>HH0417.1</em> và <em>HH417.1</em> là một.</li>
<li>Tệp tối đa 20.000 dòng mỗi sheet. Lô nhập định mức <strong>chưa hoàn tác được</strong>: luôn đọc kỹ bản chạy thử trước khi Ghi thật.</li>
<li>Nút Nhập từ Excel chỉ hiện với người có quyền tạo Giá bao bì và quyền tạo, xem Quản lý Import.</li>
</ul>
{OLD_UI}menu <strong>Giá nguyên vật liệu sản xuất › Định mức bao bì</strong> là màn danh sách chung: bấm <strong>Thêm</strong> hoặc bấm một dòng là mở <strong>trang chi tiết</strong> (không phải hộp thoại), điền rồi bấm <strong>Tạo</strong> / <strong>Lưu</strong>, xóa bằng nút <strong>Xóa</strong> trên trang. Nhập từ Excel giống trên: bấm <strong>Chạy thử</strong>, sang trang lô import, bấm <strong>Ghi thật</strong> (nút này có ở trang lô của lô định mức bao bì đã chạy thử xong).</p>""",
        },
        {
            "title": FAQ_TITLE,
            "icon": "help",
            "summary": "Không thấy menu, số khác báo cáo HTML (mốc Sổ Misa 30/06/2026), thiếu giá, màn chưa đổi sau cập nhật, giới hạn hiện tại (một chai một bộ, một định mức một mã HH) và cách quản trị giao quyền Giá bao bì",
            "content": f"""<h2>Lỗi thường gặp</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Không thấy nhóm menu Giá bao bì</td><td>Tài khoản chưa có quyền Xem của Giá bao bì.</td><td>Nhờ quản trị giao quyền (mục dưới).</td></tr>
<tr><td>Thấy màn nhưng không có nút Xuất Excel / Báo giá mới / Nhập báo giá / Nạp sổ Misa / Nhập từ Excel</td><td>Thiếu quyền Xuất / Tạo của Giá bao bì; Nạp sổ Misa cần quyền Sửa; các nút nhập Excel cần thêm quyền tạo, xem Quản lý Import.</td><td>Nhờ quản trị bổ sung đúng quyền cần dùng.</td></tr>
<tr><td>Giá trên ERP khác báo cáo giá NVL bản HTML</td><td>Tới 30/06/2026 hai bên cùng số (Sổ Misa); sau mốc đó ERP lấy thêm đơn mua hàng thật trên ERP nên giá mới hơn. Báo giá chỉ có khi đã nhập ở Bảng giá VTBB. Pháp nhân bạn được xem cũng làm giá khác.</td><td>Bấm mã để mở Lịch sử mua hàng, cột Nguồn cho biết lần mua nào từ Sổ Misa, lần nào từ đơn mua hàng.</td></tr>
<tr><td>Vừa cập nhật mà màn vẫn như cũ (giao diện cũ)</td><td>Giao diện cũ là ứng dụng cài được, trình duyệt giữ bản cũ tới khi tải lại.</td><td>Bấm <strong>Tải lại</strong> ở hộp <em>Đã có phiên bản mới</em> góc phải dưới, hoặc đóng hết thẻ rồi mở lại.</td></tr>
<tr><td>Sản phẩm không hiện ở màn Tác động giá</td><td>Định mức của sản phẩm không chứa mã đang chọn, hoặc sản phẩm chưa có định mức.</td><td>Kiểm ở {ref(BOM_TITLE, "Định mức bao bì")}.</td></tr>
<tr><td>CP bao bì để trống, xu hướng <em>Chưa có giá</em></td><td>Thiếu giá chai.</td><td>Nhập báo giá cho mã chai ({ref(PRICES_TITLE, "Bảng giá VTBB")}).</td></tr>
<tr><td>Vừa sửa đơn mua hàng, giá trên màn chưa đổi</td><td>Chỉ đơn đã duyệt mới vào sổ giá; đơn nháp, chờ duyệt chưa tính.</td><td>Duyệt đơn rồi tải lại màn.</td></tr>
<tr><td>Hai người mở cùng mã thấy giá khác nhau</td><td>Giá tính theo pháp nhân mỗi người được xem.</td><td>Bình thường; cần thống nhất thì cùng xem bằng tài khoản có phạm vi rộng hơn.</td></tr>
</tbody>
</table>

<h2>Giới hạn hiện tại</h2>
<ul>
<li>Mỗi chai dùng đúng <strong>một</strong> chai, một nắp, một nhãn (chưa khai được hai nhãn trên một chai).</li>
<li>Mỗi mã HH <strong>một</strong> định mức, chưa có phiên bản định mức theo thời gian: đổi bao bì là sửa đè.</li>
<li>Đơn giá hiểu là giá <strong>một cái</strong> theo ĐVT danh mục; mua theo đơn vị khác thì xem cảnh báo <em>ĐVT mua khác ĐVT danh mục</em>.</li>
<li>Sổ Misa hiện có tới 30/06/2026; có số Misa mới hơn thì nạp bằng nút Nạp sổ Misa ở màn Lịch sử mua hàng.</li>
<li>Chọn một lần tối đa 500 mã ở màn Tác động giá; Lịch sử mua hàng chọn tối đa 200 mã.</li>
</ul>

<h2>Dành cho quản trị: giao quyền Giá bao bì</h2>
<ol>
<li>Vào <strong>Quản trị › Phân quyền tài khoản › Vai trò &amp; quyền</strong>, chọn vai trò của nhân sự thu mua cần dùng.</li>
<li>Ở nhóm <strong>Thu mua</strong>, dòng <strong>Giá bao bì</strong>, tick <strong>Xem</strong> (bắt buộc để thấy menu), thêm <strong>Xuất</strong>, <strong>Tạo</strong>, <strong>Sửa</strong>, <strong>Xóa</strong> tùy người.</li>
<li>Đặt <strong>phạm vi</strong> theo pháp nhân người đó được xem giá mua (phạm vi lọc sổ giá theo công ty mua).</li>
<li>Người cần Nhập từ Excel định mức: thêm quyền tạo và xem của <strong>Quản lý Import</strong>.</li>
<li>Người được giao đăng xuất rồi đăng nhập lại để menu hiện.</li>
</ol>
<p>Giá bao bì là <strong>giá vốn</strong>, thuộc nhóm dữ liệu nhạy cảm của Thu mua: tick Xem / Xuất cho vai trò mặc định của mọi tài khoản thì màn phân quyền hiện dòng nhắc màu vàng. Chỉ giao cho người thật sự cần.</p>""",
        },
    ],
}

EXPECTED_ARTICLES = 9
#  Chuỗi không được lọt vào bài: tên khóa ngưỡng (đang tắt) — bật lại thì bỏ khỏi đây và viết bài.
FORBIDDEN_SNIPPETS = ("Sàn – Trần", "ngưỡng sàn", "ngưỡng trần", "Ngưỡng giá", "Chỉ mã ngoài ngưỡng")


def iter_nodes():
    return [TREE, *TREE["children"]]


def check_unique_titles() -> None:
    """Slug trùng bài khác (ngoài cây này) là liên kết chéo nhảy nhầm trên portal — chặn trước khi ghi."""
    nodes = iter_nodes()
    titles = [n["title"] for n in nodes]
    assert len(titles) == EXPECTED_ARTICLES, titles
    #  Cột `summary` là String(255): dài hơn thì MySQL từ chối giữa chừng lúc chèn.
    too_long = [n["title"] for n in nodes if len(n.get("summary") or "") > 255]
    assert not too_long, f"Tóm tắt quá 255 ký tự: {too_long}"
    leaked = [(n["title"], s) for n in nodes for s in FORBIDDEN_SNIPPETS if s.lower() in n["content"].lower()]
    assert not leaked, f"Bài nhắc tới ngưỡng giá đang tắt: {leaked}"
    slugs = {slugify(t): t for t in titles}
    assert len(slugs) == len(titles), "Hai bài trong cây trùng slug"
    db = SessionLocal()
    try:
        own = (db.query(HelpArticle.id)
               .filter(HelpArticle.title == ROOT_TITLE, HelpArticle.parent_id.is_(None)).first())
        own_ids = {nid for nid, _ in _descendants(db, own[0])} if own else set()
        clash = [a.title for a in db.query(HelpArticle.id, HelpArticle.title).all()
                 if a.id not in own_ids and slugify(a.title) in slugs]
    finally:
        db.close()
    if clash:
        raise SystemExit(f"Tiêu đề đã có bài khác dùng, đổi tiêu đề trước: {clash}")


def drop_legacy_trees(dry_run: bool) -> None:
    """Xóa cây bài mang tiêu đề gốc CŨ (kèm thẻ trang chủ của nó) trước khi dựng cây tên mới."""
    db = SessionLocal()
    try:
        for title in LEGACY_ROOT_TITLES:
            old = db.query(HelpArticle).filter(HelpArticle.title == title, HelpArticle.parent_id.is_(None)).first()
            if old is None:
                continue
            if dry_run:
                print(f"  (sẽ xóa cây tên cũ '{title}', gốc id={old.id})")
                continue
            print(f"Đã xóa cây tên cũ '{title}': {_delete_subtree(db, old.id)} bài (gốc id={old.id}).")
        if not dry_run:
            db.commit()
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Bài HDSD duoc-CR-784: cụm Giá nguyên vật liệu sản xuất")
    parser.add_argument("--dry-run", action="store_true", help="chỉ kiểm tiêu đề và in cây, không ghi")
    args = parser.parse_args()
    check_unique_titles()
    if args.dry_run:
        for node in iter_nodes():
            print(f"  {'(gốc) ' if node is TREE else '  '}{node['title']} — /{slugify(node['title'])} "
                  f"({len(node['content'])} ký tự)")
        drop_legacy_trees(dry_run=True)
        print(f"Thử xong: {EXPECTED_ARTICLES} bài, tiêu đề không trùng, chưa ghi gì.")
        return
    drop_legacy_trees(dry_run=False)
    rebuild_tree(TREE)


if __name__ == "__main__":
    main()
