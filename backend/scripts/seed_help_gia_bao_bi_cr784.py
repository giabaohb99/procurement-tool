# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp cho cụm Giá nguyên vật liệu sản xuất của phân hệ Thu mua — duoc-CR-784 (21/11/2026).

Dựng 1 thẻ phân hệ *Hướng dẫn sử dụng Giá nguyên vật liệu sản xuất* + 9 bài theo TÁC VỤ: tổng quan (công thức, sổ giá, luật
giá cũ / mới, quyền), xem tác động khi NCC đổi giá, rà chi phí mọi sản phẩm, Bảng giá VTBB + nhập báo giá, giá các lần mua gần
nhất, lịch sử mua + biểu đồ, khai / nhập định mức bao bì, xóa dữ liệu đã nhập theo lô, lỗi thường gặp + dành cho quản trị.

Cụm có ở CẢ HAI giao diện: ERP mới (phân hệ Thu mua, nhóm menu Mua hàng, mục cha đóng mở *Giá nguyên vật liệu sản xuất* ngay dưới
Tra cứu thị trường, `frontend-v2/src/modules/procurement/pages/packaging-*`) và giao diện cũ Thu mua (nhóm Mua hàng, cùng mục cha,
`frontend/src/pages/packaging/*`, ngoại lệ D-026 người chủ duyệt 21/11/2026). Theo nếp các bài Thu mua có sẵn, mỗi bài ghi một đoạn
ngắn *Trên giao diện cũ (Thu mua)* ở chỗ hai bản khác nhau, không tách bài riêng.

Nhãn nút / tiêu đề cột chép từ mã màn (soát lại 26/11/2026 trên `origin/erp-v2` @0039f8758): `packaging-impact-page.tsx`,
`packaging-code-picker.tsx`, `packaging-impact-selected-table.tsx`, `packaging-product-columns.tsx`,
`packaging-product-overview-toolbar.tsx`, `packaging-price-list-page.tsx`, `packaging-quote-dialog.tsx`, `packaging-quote-crud.tsx`
(cột Nguồn), `packaging-last-prices-toolbar.tsx`, `packaging-history-toolbar.tsx`, `use-packaging-history-columns.tsx`,
`packaging-history-cells.tsx` (ô Nguồn), `packaging-bom-crud.tsx`, `packaging-excel-imports.ts`, menu ở `procurement/routes.tsx`;
nút xóa theo lô ở `system/pages/import-detail-page.tsx` + `system/components/import-batch-purge-dialog.tsx`; bản cũ ở
`frontend/src/layouts/AppLayout.tsx`, `frontend/src/config/packaging-cruds.tsx`, `frontend/src/pages/ImportBatchDetail.tsx`,
`frontend/src/components/packaging/PackagingBatchPurgeModal.tsx`, `PackagingHistoryTable.tsx`. Câu lỗi báo giá trùng lấy từ
`product_price/quote_limit_controller.py`; luật xóa theo lô từ `packaging_cost/batch_purge_service.py`. Nhãn cảnh báo / xu hướng /
vai trò lấy từ `backend/app/core/packaging_price_codes.py`.

Cập nhật 26/11/2026 (phase 05 kế hoạch `doc/erp/thu-mua/plans/261125-toi-uu-bang-gia-nvl-duoc-cr-784/`): menu nằm trong nhóm Mua
hàng; sổ giá gộp nguồn (một lần mua trên ERP là một dòng, đang mở rồi chốt); cột Nguồn của Lịch sử mua hàng chỉ ghi số ĐMH (dòng
Sổ Misa / lịch sử cũ để trống, tệp Excel mới ghi chữ); báo giá có cột Nguồn và chặn trùng (mã, NCC, ngày hiệu lực); ghi chú đơn vị
VNĐ, chưa VAT trên màn; VAT dòng Misa để trống; bài mới Xóa dữ liệu theo lô nhập thay cho câu "chưa hoàn tác được".

KHÔNG CÓ trong bài: ngưỡng giá sàn / trần — người chủ chốt 21/11/2026 "tạm thời chưa xài", rồi 25/11/2026 chốt XÓA HẲN (phase 04,
migration `cleanup784`): nút Ngưỡng, cột Sàn – Trần, ô Chỉ mã ngoài ngưỡng, cảnh báo Dưới ngưỡng sàn / Vượt ngưỡng trần không còn
trên giao diện nên bài cũng không nhắc. Màn danh sách Báo giá VTBB ẩn khỏi menu: chỉ nhắc đường vào trong bài Bảng giá.

Chạy trong container api (KHÔNG chạy trên prod — prod đồng bộ Help Center theo đợt riêng):
    docker compose exec -T api python scripts/seed_help_gia_bao_bi_cr784.py --dry-run   # in cây + kiểm tiêu đề, không ghi
    docker compose exec -T api python scripts/seed_help_gia_bao_bi_cr784.py
    docker compose exec -T api python scripts/reindex_help_rag.py --purge-orphans

Idempotent: xóa nguyên cây cùng tiêu đề gốc rồi dựng lại ở đúng vị trí cũ (`help_seed_common.rebuild_tree`).

Phải KHỚP với `doc/erp/thu-mua/chuc-nang/21-tac-dong-gia-bao-bi.md` (mục 1–9) và cẩm nang trợ lý
`app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md` (mục Giá nguyên vật liệu sản xuất). Nội dung ở đây và ở tài liệu đó phải khớp nhau.
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
PURGE_TITLE = "Giá NVL sản xuất — Xóa dữ liệu đã nhập nhầm theo lô nhập Excel"
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
<li><strong>Giao diện ERP mới:</strong> phân hệ <strong>Thu mua</strong>, nhóm menu <strong>Mua hàng</strong>, mục <strong>Giá nguyên vật liệu sản xuất</strong> (ngay dưới Tra cứu thị trường). Bấm mục này để mở hoặc thu sáu mục con: Tác động giá bao bì, Tổng hợp theo sản phẩm, Bảng giá VTBB, Giá mua gần nhất, Lịch sử mua hàng, Định mức bao bì. Đang đứng ở một màn con vẫn bấm thu lại được.</li>
<li><strong>Giao diện cũ (Thu mua):</strong> cũng trong nhóm <strong>Mua hàng</strong>, mục <strong>Giá nguyên vật liệu sản xuất</strong> ngay dưới Tra cứu thị trường, cùng sáu mục con và cùng tên như trên.</li>
</ul>
<p>Không thấy mục này là tài khoản chưa được giao quyền <strong>Giá bao bì</strong>, nhờ quản trị (xem {ref(FAQ_TITLE, "Lỗi thường gặp và dành cho quản trị")}).</p>
<p>Đọc theo việc cần làm:</p>
<ul>
<li>Lần đầu dùng, muốn hiểu số trên màn từ đâu ra: {ref(OVERVIEW_TITLE, "Các màn, ai được xem và giá cũ, giá mới lấy từ đâu")}.</li>
<li>Nhà cung cấp vừa báo giá mới cho một mã, muốn biết sản phẩm nào bị ảnh hưởng: {ref(IMPACT_TITLE, "Xem tác động khi nhà cung cấp đổi giá")}.</li>
<li>Muốn nhìn một lượt sản phẩm nào đang tăng chi phí bao bì: {ref(PRODUCTS_TITLE, "Rà chi phí bao bì của mọi sản phẩm")}.</li>
<li>Muốn tra giá từng mã hoặc ghi lại báo giá nhà cung cấp gửi: {ref(PRICES_TITLE, "Tra Bảng giá VTBB và nhập báo giá")}.</li>
<li>Muốn so đơn giá 3, 5 hay 10 lần mua gần nhất: {ref(LAST_PRICES_TITLE, "So đơn giá các lần mua gần nhất")}.</li>
<li>Muốn xem từng lần mua và biểu đồ giá của một mã: {ref(HISTORY_TITLE, "Xem lịch sử mua và biểu đồ giá")}.</li>
<li>Sản phẩm mới chưa có định mức, hoặc định mức sai: {ref(BOM_TITLE, "Khai và nhập định mức bao bì từ Excel")}.</li>
<li>Lỡ nhập nhầm một tệp Excel định mức, báo giá hay sổ Misa, muốn gỡ đúng phần đã nhập: {ref(PURGE_TITLE, "Xóa dữ liệu đã nhập nhầm theo lô")}.</li>
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
<p>Mọi giá là <strong>VNĐ, chưa VAT</strong>, theo đơn vị tính của danh mục sản phẩm; dòng chú thích dưới tiêu đề mỗi màn (và bản in) cũng ghi <em>Đơn vị VNĐ, chưa VAT</em>. Đơn mua bằng ngoại tệ được quy ra VNĐ theo tỷ giá trên đơn.</p>

<h2>Giá lấy từ đâu</h2>
<p>Hệ thống tự gom giá vào một <strong>sổ giá</strong>, không ai phải nhập tay:</p>
<table>
<thead><tr><th>Nguồn</th><th>Vào sổ khi nào</th><th>Đổi thế nào</th></tr></thead>
<tbody>
<tr><td><strong>Đơn mua hàng trên ERP</strong></td><td>Dòng của đơn mua hàng đã duyệt, chưa hủy. Mỗi dòng đơn là <strong>một</strong> lần mua trong sổ, từ lúc duyệt tới lúc hoàn thành</td><td>Khi dòng còn đang mở (màn ghi nhãn <em>ĐMH đang mở</em>): sửa giá, số lượng, nhà cung cấp, ngày trên đơn thì sổ sửa theo; dòng bị hủy hoặc đơn bị hủy duyệt thì rời sổ. Khi dòng <strong>hoàn thành</strong>: giá được chốt theo số lúc hoàn thành và không đổi nữa, kể cả khi đơn bị hủy sau đó</td></tr>
<tr><td><strong>Lịch sử mua hàng cũ</strong></td><td>Dữ liệu mua hàng cũ đã nạp từ Excel trước khi có ERP</td><td>Ghi một lần, không sửa</td></tr>
<tr><td><strong>Sổ Misa</strong></td><td>Sổ chi tiết mua hàng Misa (đang có từ 2025 tới hết 30/06/2026, cùng số liệu với báo cáo giá NVL bản HTML)</td><td>Thu mua nạp tệp Excel xuất từ Misa bằng nút <strong>Nạp sổ Misa</strong> ở màn Lịch sử mua hàng ({ref(HISTORY_TITLE, "xem cách nạp")}). Sổ Misa không ghi VAT nên ô VAT của các lần mua này để trống</td></tr>
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
<p><strong>Màu chênh lệch:</strong> số <strong>tăng hiện màu đỏ</strong>, số <strong>giảm hiện màu xanh</strong>, không đổi thì để màu thường. Màu này áp chung mọi màn, bản in và tệp Excel của cụm.</p>

<h2>In và Xuất Excel</h2>
<ul>
<li>Nút <strong>In</strong> (màn Tác động giá bao bì và Lịch sử mua hàng, cần quyền Xem) mở một thẻ mới đúng theo bộ lọc đang xem, nạp đủ mọi dòng rồi tự bật hộp in. Bản in khổ A4 ngang, trình bày như bản in của báo cáo HTML: tiêu đề báo cáo, ô lọc, thẻ số liệu và biểu đồ (Lịch sử mua hàng, khi xem một mã hoặc một sản phẩm) và bảng.</li>
<li>Nút <strong>Xuất Excel</strong> (cần quyền Xuất) tải tệp theo đúng bộ lọc và thứ tự đang xem, tối đa 5.000 dòng. Tệp trình bày như tệp Excel của báo cáo HTML: dòng 1 tiêu đề <em>BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT — tên báo cáo</em>, dòng 2 ngày xuất và đơn vị (VNĐ, chưa VAT), đầu cột nền xanh đậm (cột chai, nắp, nhãn, nhãn thùng, thùng nền xanh lá), số có dấu nghìn, phần trăm dạng 12,4%, ô tăng đỏ giảm xanh, cố định hàng tiêu đề, có bộ lọc, in A4 ngang có số trang.</li>
</ul>

<h2>Ai được xem gì</h2>
<ul>
<li>Mọi màn cần quyền <strong>Giá bao bì</strong> (nhóm Thu mua ở màn phân quyền vai trò): <strong>Xem</strong> để mở màn, <strong>Xuất</strong> để có nút Xuất Excel, <strong>Tạo</strong> để nhập báo giá và định mức, <strong>Sửa</strong> / <strong>Xóa</strong> để sửa, xóa định mức hay báo giá. Nút <strong>Xóa dữ liệu của lô này</strong> ở trang lô nhập cần quyền <strong>Xóa</strong> của Giá bao bì cộng quyền xem Quản lý Import.</li>
<li><strong>Giá tính theo pháp nhân bạn được xem:</strong> phạm vi của quyền Giá bao bì lọc sổ giá theo công ty mua. Hai người cùng mở một mã có thể thấy giá khác nhau nếu được xem các pháp nhân khác nhau.</li>
<li>Định mức bao bì và báo giá là danh mục dùng chung: ai có quyền Xem đều thấy đủ.</li>
</ul>
{OLD_UI}cùng dữ liệu, cùng công thức, cùng quyền. Đơn giá hiện tới 4 chữ số lẻ (giao diện mới làm tròn: dưới 100.000 đ giữ tối đa 2 chữ số lẻ, từ 100.000 đ làm tròn tới đồng).</p>""",
        },
        {
            "title": IMPACT_TITLE,
            "icon": "bar-chart",
            "summary": "Màn Tác động giá bao bì: chọn mã (hoặc cả nhóm), nhập giá giả định, đọc bảng mã đã chọn và sản phẩm bị ảnh hưởng, lọc bằng chip điều kiện, xếp mọi cột kể cả Chai / Nắp / Nhãn, ghi chú cảnh báo, In, Xuất Excel",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Nhà cung cấp báo tăng (hoặc giảm) giá một hay nhiều mã bao bì, hoặc bạn muốn thử "nếu nắp lên 350 đ thì sao" trước khi chốt giá. Mở <strong>Thu mua › Mua hàng › Giá nguyên vật liệu sản xuất › Tác động giá bao bì</strong> (màn có tiêu đề <strong>Tác động tăng giá bao bì</strong>).</p>

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
<tr><td>Tăng/giảm /chai, Tăng/giảm /thùng</td><td>Chênh lệch chi phí một chai và một thùng. Đỏ là tăng, xanh là giảm.</td></tr>
<tr><td>Ghi chú</td><td>Cảnh báo của dòng, ví dụ <em>Thiếu giá thành phần: Nhãn</em> (xem bảng dưới).</td></tr>
</tbody>
</table>
<h2>Lọc và xếp</h2>
<ul>
<li><strong>Bảng mã đã chọn</strong>: chọn mã của nhiều nhóm thì có hàng chip <strong>Tất cả</strong> · <strong>Chai</strong> · <strong>Nắp</strong> · <strong>Nhãn</strong>… kèm số mã; bấm một chip để chỉ xem mã của nhóm đó (chỉ lọc bảng này, không đổi các mã đang tính).</li>
<li><strong>Bảng sản phẩm</strong>: ô <strong>Tìm mã HH, tên, mã thành phần…</strong> và nút <strong>Thêm điều kiện</strong>. Bấm nút để chọn một điều kiện: <strong>Xu hướng chi phí</strong> (Tăng, Giảm, Không đổi, Chưa có giá), <strong>Có mã đã chọn ở vai trò</strong> (Chai, Nắp, Nhãn, Nhãn thùng, Thùng), các khoảng <strong>từ … đến …</strong> cho Quy cách thùng, Tăng/giảm /chai, Tăng/giảm /thùng, CP bao bì/chai mới, hoặc <strong>Chỉ sản phẩm có cảnh báo</strong> (thiếu giá chai, thiếu mã / giá thành phần, thiếu quy cách thùng, lệch ĐVT). Mỗi điều kiện hiện thành một <strong>chip</strong> dưới ô tìm, ví dụ "Vai trò: Chai, Nắp" hay "Tăng/giảm /thùng ≥ 1.000 đ": bấm chip để sửa ngay tại chỗ, bấm dấu <strong>x</strong> trên chip để bỏ. Bảng lọc ngay, không cần bấm Áp dụng (ô số đợi chừng nửa giây sau khi bạn ngừng gõ). Nút <strong>Xóa lọc</strong> bỏ cả ô tìm lẫn mọi chip.</li>
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
{OLD_UI}menu <strong>Mua hàng › Giá nguyên vật liệu sản xuất › Tác động giá bao bì</strong>; các bước, nút và cột như trên. Đơn giá hiện tới 4 chữ số lẻ.</p>""",
        },
        {
            "title": PRODUCTS_TITLE,
            "icon": "pie-chart",
            "summary": "Màn Tổng hợp theo sản phẩm: mọi sản phẩm có định mức, CP cũ / mới một chai, chênh một chai và một thùng, % chênh, chip Tăng / Giảm / Không đổi / Chưa có giá kèm số đếm",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Đầu kỳ báo giá, hoặc khi Kinh doanh hỏi "sản phẩm nào đang tăng chi phí bao bì". Khác màn {ref(IMPACT_TITLE, "Tác động giá")} (bắt đầu từ mã bao bì), màn này bắt đầu từ <strong>sản phẩm</strong>: mọi mã HH có định mức, giá cũ so với giá mới hiện hành, không có giá giả định.</p>
<p>Mở <strong>Thu mua › Mua hàng › Giá nguyên vật liệu sản xuất › Tổng hợp theo sản phẩm</strong>.</p>

<h2>Lọc nhanh bằng chip</h2>
<p>Thanh lọc nằm trên <strong>một hàng</strong>: bên trái là ô tìm và hàng chip, bên phải là nút <strong>Xóa lọc</strong> (khi đang lọc), <strong>Tải lại</strong>, <strong>Cột</strong>. Sau ô tìm là nút <strong>Thêm điều kiện</strong>, rồi hàng chip kèm số sản phẩm của từng loại: <strong>Tất cả</strong>, <strong>Tăng</strong> (chi phí bao bì tăng, cần xem lại giá bán), <strong>Giảm</strong>, <strong>Không đổi</strong>, <strong>Chưa có giá</strong> (thiếu giá chai nên chưa tính được). Bấm một chip để chỉ xem loại đó; bấm <strong>Tất cả</strong> để bỏ lọc. Số trên chip đếm theo từ khóa và các chip điều kiện đang bật.</p>

<h2>Thêm điều kiện lọc</h2>
<p>Bấm <strong>Thêm điều kiện</strong> để lọc sâu hơn, ví dụ "sản phẩm có thùng mà chi phí tăng trên 5%". Menu liệt kê các điều kiện chưa bật; chọn một điều kiện thì hộp nhỏ hiện ngay dưới chip mới để bạn nhập:</p>
<ul>
<li><strong>Có mã ở vai trò</strong>: Chai, Nắp, Nhãn, Nhãn thùng, Thùng. Chọn nhiều vai trò thì sản phẩm chỉ cần có mã ở một trong các vai trò đó trong định mức.</li>
<li>Các khoảng <strong>từ … đến …</strong> (bỏ trống một ô nếu chỉ cần một phía, số âm được): <strong>Quy cách thùng</strong>, <strong>CP bao bì/chai cũ</strong>, <strong>CP bao bì/chai mới</strong>, <strong>Tăng/giảm /chai</strong>, <strong>Tăng/giảm /thùng</strong>, <strong>% chênh</strong> (gõ 5 là 5%, so với con số đang hiện trên bảng). Sản phẩm chưa có giá chai không có số để so nên bị loại khi bạn bật một khoảng. Nếu "từ" lớn hơn "đến" thì có dòng báo lỗi ngay dưới ô và điều kiện đó chưa được áp dụng.</li>
<li><strong>Chỉ sản phẩm có cảnh báo</strong>: thiếu giá chai, thiếu mã / giá thành phần, thiếu quy cách thùng, lệch ĐVT. Điều kiện này không có gì để nhập nên chọn là lọc luôn.</li>
</ul>
<p>Mỗi điều kiện là một chip: bấm chip để sửa, bấm <strong>x</strong> để bỏ. Bảng lọc ngay khi bạn chọn hoặc gõ xong, không có nút Áp dụng. Các điều kiện cùng lúc là "và" với nhau, và kết hợp được với ô tìm và chip xu hướng. <strong>Xóa lọc</strong> bỏ tất cả. <strong>Xuất Excel</strong> ra đúng bộ lọc đang xem.</p>

<h2>Đọc bảng</h2>
<ul>
<li>Cột đầu: <strong>Mã HH</strong> (bấm để mở {ref(HISTORY_TITLE, "Lịch sử mua hàng")} ở chế độ theo mã sản phẩm, gồm mọi thành phần của định mức), <strong>Tên hàng hóa</strong>, <strong>Quy cách</strong>.</li>
<li>Con số cần đọc đứng trước: <strong>CP cũ /chai</strong>, <strong>CP mới /chai</strong>, <strong>Tăng/giảm /chai</strong>, <strong>Tăng/giảm /thùng</strong>, <strong>% chênh</strong>, <strong>Xu hướng</strong>.</li>
<li>Sau đó là năm ô thành phần (Chai, Nắp, Nhãn, Nhãn thùng, Thùng: mã và giá cũ → mới, mã bấm được) và <strong>Ghi chú</strong> (cùng bộ cảnh báo như màn Tác động giá).</li>
</ul>
<p>Ô <strong>Tìm mã HH, tên, mã thành phần…</strong> tìm không cần dấu. Bấm tiêu đề cột để xếp, ví dụ <strong>Tăng/giảm /thùng</strong> giảm dần. <strong>Xuất Excel</strong> ra đúng bộ lọc và thứ tự đang xem (tối đa 5.000 dòng).</p>
{OLD_UI}menu <strong>Mua hàng › Giá nguyên vật liệu sản xuất › Tổng hợp theo sản phẩm</strong>, cùng chip, cột và nút.</p>""",
        },
        {
            "title": PRICES_TITLE,
            "icon": "coins",
            "summary": "Bảng giá VTBB: giá mua gần nhất, lần trước, báo giá mới, giá cũ / mới / chênh / %, Min, Max, số SP đang dùng; nút Báo giá mới và nút Báo giá từng dòng để ghi báo giá của NCC",
            "content": f"""<h2>Tra giá từng mã</h2>
<p>Mở <strong>Thu mua › Mua hàng › Giá nguyên vật liệu sản xuất › Bảng giá VTBB</strong>. Mỗi mã vật tư bao bì một dòng:</p>
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
<p>Thanh lọc: <strong>ô chọn mã</strong> (giống màn Tác động giá bao bì: gõ mã, tên, tên nhóm hoặc tên nhà cung cấp ngay trong ô, chọn được nhiều mã thành chip; danh sách gồm mọi mã có trong sổ giá, kể cả mã chưa nằm trong định mức), chip nhóm (<strong>Tất cả</strong>, Chai, Nắp, Nhãn…), và nút phạm vi <strong>Mã trong định mức</strong> (mặc định: mã đang dùng trong định mức và mã đã có báo giá) / <strong>Mọi mã có giá</strong> (thêm mọi mã có trong sổ giá). <strong>Đã chọn mã thì bảng chỉ còn đúng các mã đó</strong>, kể cả mã đã mua nhưng chưa nằm trong định mức nào (cột số sản phẩm dùng của mã đó bằng 0), không cần đổi nút phạm vi. Bấm tiêu đề cột để xếp; <strong>Xuất Excel</strong> ra đúng bộ lọc và thứ tự đang xem.</p>

<p><strong>Giữ nguyên bộ lọc khi tải lại:</strong> ô tìm, chip nhóm, phạm vi mã, khoảng ngày, cột đang xếp, trang và số dòng mỗi trang đều nằm trên địa chỉ của trang. Bấm F5 hoặc gửi địa chỉ cho đồng nghiệp là mở lại đúng bộ lọc đó; bấm <strong>Quay lại</strong> của trình duyệt không bị kẹt qua từng lần lọc.</p>

<h2>Nhập báo giá của nhà cung cấp</h2>
<p>Nhà cung cấp gửi giá mới (qua thư, Zalo, bảng báo giá) thì ghi vào hệ thống để màn Tác động giá dùng làm <strong>giá mới</strong>:</p>
<ol>
<li>Ở dòng của mã, bấm nút <strong>Báo giá</strong> cuối dòng (mã điền sẵn, con trỏ nằm ở ô đơn giá). Mã chưa có trong bảng thì bấm <strong>Báo giá mới</strong> ở góc phải trên cùng rồi gõ <strong>Mã VTBB</strong> (ví dụ NAP0085).</li>
<li>Điền <strong>Đơn giá (VNĐ, chưa VAT)</strong> theo đơn vị tính của danh mục, <strong>Ngày hiệu lực</strong>; tùy chọn <strong>Nhà cung cấp</strong> (chọn từ danh mục nhà cung cấp, gõ mã hoặc tên để tìm, bỏ trống nếu chưa rõ; người chưa có quyền xem danh mục nhà cung cấp thì gõ mã tay), <strong>VAT (%)</strong>, <strong>Ghi chú</strong>.</li>
<li>Bấm <strong>Lưu báo giá</strong>. Bảng giá, màn Tác động giá và Tổng hợp theo sản phẩm tính lại ngay.</li>
</ol>
<ul>
<li>Báo giá có <strong>ngày hiệu lực ở tương lai vẫn tính ngay</strong> là giá mới, để xem trước tác động trước khi giá áp dụng.</li>
<li>Một mã có nhiều báo giá thì báo giá có ngày hiệu lực muộn nhất thắng. Báo giá không vào sổ giá: nó không thành "lần mua", không đổi số lần mua hay giá mua gần nhất.</li>
<li><strong>Mỗi mã, mỗi nhà cung cấp, mỗi ngày hiệu lực chỉ có một báo giá</strong> (bỏ trống nhà cung cấp cũng tính là một nhà cung cấp). Lưu một báo giá trùng cả ba ô với báo giá đã có thì hệ thống báo <em>Đã có báo giá cùng mã, NCC và ngày hiệu lực</em> và không lưu: hãy sửa báo giá đang có, hoặc đổi ngày hiệu lực nếu đây là đợt giá mới.</li>
<li>Báo giá nhập nhầm: sửa hay xóa ở màn danh sách <strong>Báo giá VTBB</strong>. Màn này không có trong menu, mở bằng đường <em>/procurement/packaging-cost/quotes</em>; bấm một dòng để mở hộp sửa (<strong>Lưu thay đổi</strong>), nút xóa trong hộp cần quyền Xóa.</li>
<li>Màn Báo giá VTBB có cột <strong>Nguồn</strong> (chỉ xem): <em>Nhập tay</em> là báo giá gõ ở hộp <strong>Báo giá mới</strong> / <strong>Báo giá</strong> hoặc đã sửa tay đơn giá, VAT, mã, NCC hay ngày hiệu lực; <em>Nhập Excel (lô #N)</em> là báo giá do lô nhập Excel số N ghi giá lần cuối, bấm vào là mở trang lô đó ở Quản lý Import. Chỉ sửa ghi chú thì nguồn giữ nguyên.</li>
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
<li>Trùng <strong>mã + mã NCC + ngày hiệu lực</strong> với báo giá đã có thì cập nhật đơn giá, VAT, ghi chú; chưa có thì thêm. Báo giá đang có mà không nằm trong tệp giữ nguyên. Báo giá được thêm hoặc đổi đơn giá / VAT qua tệp sẽ mang nguồn <em>Nhập Excel (lô #N)</em> của lô này.</li>
<li>Mã chưa có trong danh mục sản phẩm, đơn giá trống / bằng 0, ngày sai bị bỏ và ghi lỗi; các dòng khác vẫn nhập.</li>
<li>Cần quyền <strong>Tạo</strong> của Giá bao bì và quyền tạo, xem Quản lý Import.</li>
<li>Ghi thật nhầm cả tệp: mở trang lô đó, bấm <strong>Xóa dữ liệu của lô này</strong> để gỡ đúng các báo giá lô đã ghi ({ref(PURGE_TITLE, "xem cách xóa theo lô")}). Sai vài dòng thì sửa hay xóa ở màn Báo giá VTBB.</li>
</ul>
{OLD_UI}menu <strong>Mua hàng › Giá nguyên vật liệu sản xuất › Bảng giá VTBB</strong>. Nút <strong>Báo giá mới</strong> và nút <strong>Báo giá</strong> từng dòng mở cùng hộp nhập như trên. Cột <strong>Min</strong>, <strong>Max</strong> hiện sẵn; đơn giá hiện tới 4 chữ số lẻ. Danh sách Báo giá VTBB (không có trong menu, đường <em>/product-price-quotes</em>) là màn danh sách chung, cũng có cột <strong>Nguồn</strong> (bấm lô để mở trang lô nhập): bấm một dòng mở <strong>trang chi tiết</strong> (không phải hộp thoại) để sửa rồi bấm <strong>Lưu</strong>, hoặc <strong>Xóa</strong>.</p>""",
        },
        {
            "title": LAST_PRICES_TITLE,
            "icon": "clipboard-list",
            "summary": "Màn Giá mua gần nhất: đơn giá 3 / 5 / 10 lần mua có giá gần nhất của từng mã VTBB, ngày, NCC, biến động lần 1 so lần 2 / lần n, giá TB, lọc NCC, ngày, xu hướng, mức biến động %",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Muốn xem giá một mã đi lên hay đi xuống qua nhiều lần mua, mua của nhà cung cấp nào, để có lý lẽ khi thương lượng. Mở <strong>Thu mua › Mua hàng › Giá nguyên vật liệu sản xuất › Giá mua gần nhất</strong>.</p>

<h2>Đọc bảng</h2>
<ul>
<li>Mỗi mã VTBB một dòng. Nhóm cột <strong>Thông tin VTBB</strong>: Mã VTBB, Tên vật tư, Nhóm, ĐVT, Số lần có giá.</li>
<li>Mỗi lần mua một nhóm cột có tiêu đề gộp: <strong>Lần 1 (gần nhất)</strong>, Lần 2, Lần 3… Trong mỗi nhóm: <strong>Ngày mua</strong>, <strong>Nhà cung cấp</strong>, <strong>Đơn giá</strong> (bật <strong>Hiện số lượng</strong> để thêm cột Số lượng). Đơn giá đỏ là đắt hơn lần mua trước nó, xanh là rẻ hơn.</li>
<li>Nhóm <strong>Biến động</strong>: <strong>Lần 1 so lần 2</strong> và <strong>Lần 1 so lần n</strong> (phần trăm). Nhóm <strong>Giá TB</strong>: giá trung bình của n lần.</li>
<li>Chỉ tính lần mua <strong>có giá</strong>; lần mua đơn giá 0 bị bỏ qua.</li>
</ul>

<h2>Mở màn lần đầu</h2>
<p>Lúc mới mở, <strong>mọi bộ lọc đều tắt</strong>: phạm vi <strong>Mọi mã</strong>, các công tắc tắt hết, ô <strong>Nhóm sản phẩm</strong> chưa chọn nhóm nào (tức xem mọi nhóm), không chọn nhà cung cấp, khoảng ngày hay chiều biến động. Màn chỉ hiện <strong>20 mã mua gần nhất</strong>, xếp theo <strong>Ngày mua của Lần 1, mới nhất trước</strong>, không có chân phân trang; cạnh ô Nhóm sản phẩm có dòng nhắc <em>20 mã mua gần nhất · chọn Tất cả ở ô Nhóm sản phẩm để xem hết</em>. Muốn xem mọi mã thì mở ô <strong>Nhóm sản phẩm</strong> và tick <strong>Tất cả</strong> (dòng đầu danh sách, ô ghi chữ Tất cả), bảng nạp hết và có phân trang (10, 20, 50, 100 dòng mỗi trang). Chọn mã, chọn nhóm, bật bất kỳ bộ lọc nào hoặc bấm xếp theo cột khác cũng chuyển sang xem hết mọi mã khớp, có phân trang.</p>

<h2>Lọc</h2>
<table>
<thead><tr><th>Ô lọc</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Ô chọn mã</td><td>Giống ô chọn mã của màn Tác động giá bao bì: gõ mã, tên, tên nhóm hoặc <strong>tên nhà cung cấp</strong> (ra các mã từng mua của nhà cung cấp đó) ngay trong ô, danh sách mã khớp hiện ra, bấm hoặc Enter để thêm; mã đã chọn thành chip trong ô (bấm x trên chip để bỏ, dấu x cuối ô để bỏ hết). Chọn được nhiều mã, bảng chỉ còn đúng các mã đó.</td></tr>
<tr><td>Nhóm sản phẩm</td><td>Lọc theo nhóm. Bấm ô <strong>Nhóm sản phẩm</strong> để mở danh sách nhóm: mỗi nhóm một dòng có ô tick, số mờ bên phải là số mã của nhóm; gõ vào ô để tìm nhóm cho nhanh. Tick nhiều nhóm thì hiện mã thuộc một trong các nhóm đó (ví dụ tick <strong>Chai</strong> và <strong>Nắp</strong> ra cả chai lẫn nắp), ô ghi tên nhóm đầu kèm <em>+n</em>; bấm dấu x trong ô để bỏ hết. Dòng <strong>Tất cả</strong> đứng đầu danh sách: tick thì bỏ mọi nhóm đang chọn và xem hết mọi mã; lúc mới mở màn dòng này chưa tick. Số mã của từng nhóm đếm theo các bộ lọc khác đang dùng, không co lại khi bạn chọn nhóm.</td></tr>
<tr><td>Số lần hiển thị</td><td>3, 5 (mặc định) hoặc 10 lần mua. Đây là số cột hiện, không phải bộ lọc.</td></tr>
<tr><td>Phạm vi mã</td><td><strong>Mọi mã</strong> (mặc định) hoặc <strong>Định mức + báo giá</strong> (chỉ mã thành phần của định mức và mã đã có báo giá).</td></tr>
<tr><td>Nhà cung cấp</td><td>Giữ các mã có nhà cung cấp đó trong các lần mua đang hiện (không cắt bớt lần mua của nhà cung cấp khác).</td></tr>
<tr><td>Khoảng ngày mua</td><td>Chỉ xếp hạng các lần mua trong khoảng ngày.</td></tr>
<tr><td>Biến động lần 1 so lần 2; Biến động từ (%)</td><td>Bấm <strong>Tăng</strong>, <strong>Giảm</strong> hoặc <strong>Không đổi</strong> để chỉ xem mã đổi giá theo chiều đó; bấm lại nút đang bật để tắt; bấm <strong>Tất cả</strong> để bỏ lọc biến động (nút sáng sau khi bấm, mới mở màn thì không nút nào sáng). Ô phần trăm: chỉ mã biến động từ bao nhiêu phần trăm trở lên (0 là không lọc).</td></tr>
<tr><td>Chỉ mã đã có giá; Chỉ mã đang dùng trong định mức; Hiện số lượng</td><td>Công tắc, mặc định tắt cả ba.</td></tr>
</tbody>
</table>
<p><strong>Xuất Excel</strong> ra đúng bộ lọc, số lần và thứ tự đang xem; bật Hiện số lượng thì tệp có thêm cột số lượng.</p>
<p><strong>Giữ nguyên bộ lọc khi tải lại:</strong> mọi bộ lọc ở trên khi khác mặc định, số lần hiển thị, công tắc, cột đang xếp, trang và số dòng mỗi trang đều nằm trên địa chỉ của trang (giá trị mặc định thì không ghi), nên F5 hoặc gửi địa chỉ cho đồng nghiệp là mở lại đúng màn đang xem.</p>
{OLD_UI}menu <strong>Mua hàng › Giá nguyên vật liệu sản xuất › Giá mua gần nhất</strong>, cùng bộ lọc và cột; đơn giá hiện tới 4 chữ số lẻ.</p>""",
        },
        {
            "title": HISTORY_TITLE,
            "icon": "calendar",
            "summary": "Màn Lịch sử mua hàng của cụm Giá NVL sản xuất: từng lần mua theo mã VTBB hoặc mã sản phẩm, thẻ số liệu, biểu đồ đơn giá khi chọn một mã, cột Lần, Giá trị mua, Kho, nhãn ĐMH đang mở, Nạp sổ Misa, In, Xuất Excel",
            "content": f"""<h2>Mở màn</h2>
<p>Mở <strong>Thu mua › Mua hàng › Giá nguyên vật liệu sản xuất › Lịch sử mua hàng</strong>, hoặc bấm vào bất kỳ mã vật tư nào ở các bảng của cụm (màn mở sẵn đúng mã đó). Màn này khác tab Lịch sử mua hàng trên chi tiết sản phẩm: nó đọc sổ giá của cụm Giá nguyên vật liệu sản xuất nên có cả dòng đơn mua hàng đang mở.</p>

<h2>Chọn xem cái gì</h2>
<ol>
<li>Nút <strong>Theo mã VTBB</strong> (mặc định) hoặc <strong>Theo mã sản phẩm</strong>.</li>
<li>Theo mã VTBB: bấm ô chọn, gõ mã, tên hoặc tên nhóm để chọn một hay nhiều mã. Để trống là xem mọi mã VTBB.</li>
<li>Theo mã sản phẩm: chọn mã HH (để trống là mọi sản phẩm có định mức). <strong>Mỗi dòng là một lần mua của một thành phần trong định mức của một sản phẩm</strong>: ví dụ mã chai dùng cho 275 sản phẩm thì một lần mua hiện thành 275 dòng, mỗi dòng ghi rõ <strong>Mã SP</strong>, <strong>Tên sản phẩm</strong> và <strong>Thành phần</strong> (Chai, Nắp, Nhãn, Nhãn thùng, Thùng). Sắp mặc định: ngày mới nhất trước, rồi mã sản phẩm, rồi thành phần; bấm tiêu đề cột để xếp lại. Ô tìm tìm được cả mã, tên sản phẩm và tên thành phần.</li>
<li>Lọc thêm: <strong>Nhà cung cấp</strong>, <strong>Khoảng ngày mua</strong>, ô <strong>Tìm mã, tên, nhà cung cấp…</strong>.</li>
</ol>

<h2>Đọc kết quả</h2>
<ul>
<li><strong>Thẻ số liệu</strong> tính trên toàn bộ kết quả lọc. Chọn <strong>đúng một mã</strong>: Tổng số lần mua (kèm khoảng ngày), Tổng số lượng mua (kèm ĐVT), Tổng giá trị mua (kèm số lần có giá), Giá thấp nhất – cao nhất (kèm giá bình quân gia quyền), Gần nhất so với lần đầu (tăng đỏ, giảm xanh, kèm giá đầu → giá gần nhất), Số nhà cung cấp. Nhiều mã: Số mã đã chọn, Tổng số lần mua, Tổng giá trị mua, Số nhà cung cấp; để trống ô mã (xem mọi mã) thì thẻ đầu là Số mã hàng, tức mọi mã có lịch sử mua. Chế độ theo mã sản phẩm: Số sản phẩm (đã chọn hoặc tất cả), Mã vật tư liên quan, Số dòng lịch sử, Số nhà cung cấp. Tổng giá trị mua và giá bình quân gia quyền cộng đúng cột <strong>Giá trị mua</strong> của từng lần.</li>
<li><strong>Biểu đồ Diễn biến đơn giá</strong> hiện khi chọn đúng một mã: mỗi điểm là một lần mua có giá, rê chuột để xem ngày, đơn giá, nhà cung cấp, số lượng.</li>
<li><strong>Biểu đồ Diễn biến đơn giá theo thành phần</strong> hiện khi ở chế độ theo mã sản phẩm và chọn <strong>đúng một sản phẩm</strong>: mỗi mã thành phần trong định mức có lần mua có giá (chai, nắp, nhãn, nhãn thùng, thùng) là một đường giá, chú giải ghi <strong>vai trò và mã</strong> (ví dụ Chai · CPT0105), thùng vẽ nét đứt. Rê chuột để xem giá của từng mã tại lần mua đó. Biểu đồ theo đúng bộ lọc đang chọn và có cả trong bản in. Chọn nhiều sản phẩm thì không có biểu đồ.</li>
<li>Bảng, mới nhất trước: <strong>Lần</strong> (<strong>Lần 1 là lần mua gần nhất của mã</strong>, số càng lớn càng cũ; tính trên toàn bộ lịch sử của mã, không đổi khi bạn lọc), Ngày mua, Mã VTBB, Tên vật tư (chế độ theo mã sản phẩm thêm ba cột Mã SP, Tên sản phẩm, Thành phần ở đầu bảng), Nhà cung cấp, <strong>Kho</strong> (kho nhập hàng; lần mua trong Sổ Misa lấy kho của Misa, lần mua trên ERP lấy kho của dòng đơn mua hàng), Số lượng, Đơn giá, <strong>Giá trị mua</strong> (thành tiền chưa VAT của lần mua: lần mua trong Sổ Misa là số <em>Giá trị</em> trên sổ Misa, có thể lệch vài chục đồng so với đơn giá nhân số lượng vì Misa làm tròn từng dòng; lần mua đã hoàn thành trên ERP hay lịch sử cũ lấy thành tiền đã chốt nếu có; còn lại lấy đơn giá nhân số lượng; lần đơn giá 0 để trống), <strong>So lần trước</strong> (chênh với lần mua có giá liền trước của cùng mã; đỏ đắt hơn, xanh rẻ hơn), <strong>Nguồn</strong> (lần mua trên ERP ghi mã đơn mua hàng, bấm để mở đơn; lần mua trong Sổ Misa hay lịch sử cũ để trống ô này; tệp Excel thì cột Nguồn ghi rõ chữ <em>Sổ Misa</em>, <em>Lịch sử mua hàng</em> hoặc <em>Dòng đơn mua hàng</em>). Ô tìm tìm được cả theo tên kho; bấm tiêu đề cột Kho để xếp.</li>
<li>Nhãn <strong>ĐMH đang mở</strong> (đứng trước mã đơn ở cột Nguồn): dòng của đơn mua hàng đã duyệt, chưa hoàn thành; giá còn có thể đổi nếu đơn được sửa. Khi dòng hoàn thành, nhãn mất, giá được chốt, dòng vẫn là chính dòng đó (không thêm dòng mới).</li>
<li>Lần mua đơn giá 0 vẫn hiện để đối chiếu, nhưng không tính vào giá bình quân, thấp nhất, cao nhất và biểu đồ.</li>
</ul>
<p><strong>Xuất Excel</strong> ra đúng bộ lọc và thứ tự đang xem (tối đa 5.000 dòng). <strong>In</strong> mở bản in A4 ngang gồm ô lọc, thẻ số liệu, biểu đồ và mọi dòng.</p>

<h2>Nạp sổ Misa</h2>
<ol>
<li>Xuất <strong>Sổ chi tiết mua hàng</strong> từ Misa ra Excel, giữ nguyên tiêu đề cột của Misa (cần các cột Ngày, Mã hàng, Số lượng, Đơn giá; nên có Mã / Tên nhà cung cấp, Tên kho, ĐVT và <strong>Giá trị</strong> là thành tiền để cột Giá trị mua khớp sổ Misa). Chưa có sẵn thì bấm <strong>Tải tệp mẫu</strong> trong hộp nạp.</li>
<li>Bấm <strong>Nạp sổ Misa</strong> ở góc phải trên cùng, chọn tệp, bấm <strong>Chạy thử</strong>.</li>
<li>Ở trang lô, đọc dòng tóm tắt đầu nhật ký: số lần mua trong tệp, khoảng ngày, số dòng <em>giữ / thêm / bỏ</em>, mốc sổ Misa cũ → mới, các dòng bị bỏ qua. Đúng thì bấm <strong>Ghi thật</strong>.</li>
</ol>
<ul>
<li>Chỉ dữ liệu Misa <strong>trong khoảng ngày của tệp</strong> bị thay: lần mua trùng giữ nguyên, lần mua mới thêm, lần mua không còn trong tệp bị bỏ. Ngoài khoảng ngày giữ nguyên, nên nạp từng tháng cũng được.</li>
<li>Cột <strong>Giá trị</strong> trong tệp được ghi làm Giá trị mua. Nạp lại <strong>cùng tệp</strong> thì các lần mua đã có được bổ sung hoặc sửa Giá trị mua theo tệp, không bị nhân đôi; nhật ký ghi dòng <em>cập nhật thành tiền</em>. Tệp không có cột Giá trị thì không đụng tới Giá trị mua đã có.</li>
<li>Mã đầu PPA, CKC, CPM, CPN và dòng số lượng 0 bị bỏ qua (giống báo cáo HTML). Đơn giá trống vẫn nhận nhưng không làm giá.</li>
<li>Mốc sổ Misa dời tới ngày lớn nhất đã nạp; giá các màn tính lại ngay.</li>
<li>Cần quyền <strong>Sửa</strong> của Giá bao bì (vì đổi giá cả cụm) và quyền tạo, xem Quản lý Import.</li>
<li>Nạp nhầm tệp: nạp lại tệp đúng của cùng khoảng ngày, hoặc mở trang lô rồi bấm <strong>Xóa dữ liệu của lô này</strong> để gỡ các lần mua lô đó đã THÊM; mốc sổ Misa tự tính lại ({ref(PURGE_TITLE, "xem cách xóa theo lô")}). Lần mua mà lô đó đã bỏ khỏi sổ thì xóa lô không trả lại, phải nạp lại tệp đúng.</li>
</ul>
{OLD_UI}menu <strong>Mua hàng › Giá nguyên vật liệu sản xuất › Lịch sử mua hàng</strong>, cùng chế độ, bộ lọc, biểu đồ và cột; đơn giá hiện tới 4 chữ số lẻ.</p>""",
        },
        {
            "title": BOM_TITLE,
            "icon": "boxes",
            "summary": "Định mức bao bì theo mã HH: chai, nắp, nhãn, nhãn thùng, thùng, quy cách thùng; thêm, sửa từng dòng, Nhập từ Excel tệp DATA_CHAI.xlsx qua Quản lý Import (Chạy thử rồi Ghi thật)",
            "content": f"""<h2>Định mức bao bì là gì</h2>
<p>Mỗi mã hàng hóa (mã HH) một dòng: dùng mã <strong>chai</strong>, <strong>nắp</strong>, <strong>nhãn</strong> nào (tính theo chai), mã <strong>nhãn thùng</strong>, <strong>thùng</strong> nào (tính theo thùng) và <strong>quy cách thùng</strong> (bao nhiêu chai một thùng). Thu mua tự khai và giữ danh mục này; mọi con số chi phí của cụm Giá nguyên vật liệu sản xuất đều đọc từ đây. Mở <strong>Thu mua › Mua hàng › Giá nguyên vật liệu sản xuất › Định mức bao bì</strong>.</p>
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
<li>Tệp tối đa 20.000 dòng mỗi sheet. Luôn đọc kỹ bản chạy thử trước khi Ghi thật.</li>
<li>Ghi thật nhầm tệp: mở trang lô đó, bấm <strong>Xóa dữ liệu của lô này</strong> ({ref(PURGE_TITLE, "xem cách xóa theo lô")}). Định mức mà lô đó tạo mới <strong>hoặc sửa lần cuối</strong> đều bị xóa hẳn (kèm thành phần), không quay về bản trước khi nhập; định mức đã được sửa tay sau khi nhập được giữ lại trừ khi bạn chọn xóa luôn.</li>
<li>Nút Nhập từ Excel chỉ hiện với người có quyền tạo Giá bao bì và quyền tạo, xem Quản lý Import. Màn Định mức bao bì không hiện số lô của từng dòng; muốn biết lô nào đã nhập thì xem danh sách lô ở Quản lý Import.</li>
</ul>
{OLD_UI}menu <strong>Mua hàng › Giá nguyên vật liệu sản xuất › Định mức bao bì</strong> là màn danh sách chung: bấm <strong>Thêm</strong> hoặc bấm một dòng là mở <strong>trang chi tiết</strong> (không phải hộp thoại), điền rồi bấm <strong>Tạo</strong> / <strong>Lưu</strong>, xóa bằng nút <strong>Xóa</strong> trên trang. Nhập từ Excel giống trên: bấm <strong>Chạy thử</strong>, sang trang lô import, bấm <strong>Ghi thật</strong> (nút này có ở trang lô của lô định mức bao bì đã chạy thử xong).</p>""",
        },
        {
            "title": PURGE_TITLE,
            "icon": "database",
            "summary": "Gỡ đúng phần dữ liệu một lô nhập Excel đã ghi (Định mức bao bì, Báo giá VTBB, Sổ Misa) bằng nút Xóa dữ liệu của lô này ở trang lô Quản lý Import: xem trước số dòng, giữ dòng đã sửa tay",
            "content": f"""<h2>Khi nào dùng</h2>
<p>Bạn đã bấm <strong>Ghi thật</strong> cho một tệp Excel rồi mới thấy nhầm (nhầm tệp, nhầm tháng, tệp thử): lô <strong>Nhập từ Excel</strong> ở {ref(BOM_TITLE, "Định mức bao bì")}, lô <strong>Nhập báo giá</strong> ở {ref(PRICES_TITLE, "Bảng giá VTBB")} hay lô <strong>Nạp sổ Misa</strong> ở {ref(HISTORY_TITLE, "Lịch sử mua hàng")}. Ba loại lô này không có nút Hoàn tác như các loại nhập khác; thay vào đó trang lô có nút <strong>Xóa dữ liệu của lô này</strong>, chỉ gỡ đúng các dòng lô đó đã ghi.</p>

<h2>Các bước</h2>
<ol>
<li>Mở trang lô cần gỡ. Ngay sau khi Ghi thật, hệ thống đã đưa bạn tới trang này. Mở lại sau: giao diện ERP mới vào <strong>Quản trị › Nhập dữ liệu</strong>, giao diện cũ vào <strong>Hệ thống › Quản lý Import</strong>, tìm lô có loại <em>Định mức bao bì</em>, <em>Báo giá VTBB</em> hoặc <em>Sổ Misa (giá NVL)</em>, chế độ ghi thật, rồi bấm vào lô. Với báo giá, bấm chữ <em>Nhập Excel (lô #N)</em> ở cột Nguồn của màn Báo giá VTBB cũng mở đúng lô.</li>
<li>Bấm <strong>Xóa dữ liệu của lô này</strong> (nút chữ đỏ ở góc phải trên cùng).</li>
<li>Hộp <strong>Xóa dữ liệu của lô này?</strong> tự đếm và báo <em>Sẽ xóa N … do lô này nhập.</em> Nếu có dòng đã được sửa tay sau khi nhập, hộp báo riêng số dòng đó và mặc định <strong>giữ lại</strong>; muốn xóa cả những dòng này thì tick <strong>Xóa luôn … dòng đã sửa tay</strong>. Lô Sổ Misa còn báo <em>Mốc sổ Misa sẽ được tính lại theo các dòng còn lại.</em></li>
<li>Đọc kỹ rồi bấm <strong>Xóa N dòng</strong> (hoặc <strong>Hủy</strong> để thôi). Xóa xong hệ thống báo <em>Đã xóa N dòng của lô nhập</em> và ghi nhật ký thao tác. <strong>Hành động này không thể đảo ngược</strong>: muốn có lại dữ liệu thì nhập lại tệp đúng.</li>
</ol>

<h2>Mỗi loại lô xóa những gì</h2>
<table>
<thead><tr><th>Loại lô</th><th>Bị xóa</th><th>Không bị xóa</th></tr></thead>
<tbody>
<tr><td><strong>Định mức bao bì</strong></td><td>Mọi định mức mà lô này <strong>tạo mới hoặc sửa lần cuối</strong>, kèm các thành phần (chai, nắp, nhãn…). Định mức lô này sửa đè thì bị xóa hẳn, <strong>không quay về bản trước</strong> khi nhập.</td><td>Định mức mà một lô nhập sau đã ghi đè; định mức khai tay; định mức đã sửa tay sau khi nhập (trừ khi tick xóa luôn).</td></tr>
<tr><td><strong>Báo giá VTBB</strong></td><td>Báo giá đang mang nguồn <em>Nhập Excel (lô #N)</em> của lô này, tức báo giá lô thêm mới hoặc đổi đơn giá / VAT lần cuối. Báo giá lô đổi giá thì bị xóa hẳn, không quay về giá cũ.</td><td>Báo giá đã sửa tay đơn giá, VAT, mã, NCC hay ngày hiệu lực (nguồn đã thành <em>Nhập tay</em>); báo giá của lô khác.</td></tr>
<tr><td><strong>Sổ Misa</strong></td><td>Các lần mua mà lô này <strong>thêm</strong> vào sổ. Xóa xong, mốc sổ Misa dời về ngày lớn nhất còn lại; hết dòng Misa thì bỏ mốc. Giá các màn tính lại ngay.</td><td>Lần mua đã có từ trước (lô chỉ giữ nguyên hay bổ sung Giá trị mua); lần mua mà lô đã bỏ khỏi sổ (xóa lô không trả lại, phải nạp lại tệp đúng); sổ Misa nạp bằng công cụ quản trị từ tệp HTML (không thuộc lô nào).</td></tr>
</tbody>
</table>
<p>Dòng <em>đã sửa tay sau khi nhập</em> là dòng có giờ cập nhật muộn hơn giờ lô chạy xong, ví dụ ai đó sửa quy cách thùng của một định mức hay sửa ghi chú của một báo giá.</p>

<h2>Không thấy nút hoặc hộp báo lạ</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Trang lô không có nút Xóa dữ liệu của lô này</td><td>Lô là bản <strong>chạy thử</strong> (chưa ghi gì), lô lỗi / chưa chạy xong, lô thuộc loại khác (loại khác dùng nút Hoàn tác), hoặc tài khoản thiếu quyền <strong>Xóa</strong> của Giá bao bì hay quyền xem Quản lý Import.</td><td>Chọn đúng lô ghi thật đã xong; thiếu quyền thì nhờ quản trị.</td></tr>
<tr><td><em>Lô này không còn dòng dữ liệu nào để xóa.</em></td><td>Dòng của lô đã bị xóa trước đó, hoặc đã bị lô sau ghi đè / sửa tay đổi nguồn.</td><td>Không cần làm gì.</td></tr>
<tr><td><em>Không xem trước được số dòng của lô.</em></td><td>Mất kết nối hoặc phiên đăng nhập hết hạn.</td><td>Đóng hộp, tải lại trang rồi thử lại.</td></tr>
</tbody>
</table>
{OLD_UI}trang lô ở <strong>Hệ thống › Quản lý Import</strong> có cùng nút <strong>Xóa dữ liệu của lô này</strong> và cùng hộp hỏi (nút xóa đổi thành <em>Đang xóa…</em> trong lúc chạy); xóa xong trang lô tự tải lại.</p>""",
        },
        {
            "title": FAQ_TITLE,
            "icon": "help",
            "summary": "Không thấy menu, số khác báo cáo HTML (mốc Sổ Misa 30/06/2026), báo giá bị báo trùng, thiếu giá, màn chưa đổi sau cập nhật, giới hạn hiện tại và cách quản trị giao quyền Giá bao bì, nạp Sổ Misa",
            "content": f"""<h2>Lỗi thường gặp</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Không thấy mục Giá nguyên vật liệu sản xuất trong nhóm Mua hàng</td><td>Tài khoản chưa có quyền Xem của Giá bao bì.</td><td>Nhờ quản trị giao quyền (mục dưới).</td></tr>
<tr><td>Thấy màn nhưng không có nút Xuất Excel / Báo giá mới / Nhập báo giá / Nạp sổ Misa / Nhập từ Excel</td><td>Thiếu quyền Xuất / Tạo của Giá bao bì; Nạp sổ Misa cần quyền Sửa; các nút nhập Excel cần thêm quyền tạo, xem Quản lý Import.</td><td>Nhờ quản trị bổ sung đúng quyền cần dùng.</td></tr>
<tr><td>Giá trên ERP khác báo cáo giá NVL bản HTML</td><td>Tới 30/06/2026 hai bên cùng số (Sổ Misa); sau mốc đó ERP lấy thêm đơn mua hàng thật trên ERP nên giá mới hơn. Báo giá chỉ có khi đã nhập ở Bảng giá VTBB. Pháp nhân bạn được xem cũng làm giá khác.</td><td>Bấm mã để mở Lịch sử mua hàng: dòng có mã đơn ở cột Nguồn là lần mua trên ERP, dòng để trống ô Nguồn là Sổ Misa (hoặc lịch sử cũ); tệp Xuất Excel ghi rõ chữ nguồn.</td></tr>
<tr><td>Vừa cập nhật mà màn vẫn như cũ (giao diện cũ)</td><td>Giao diện cũ là ứng dụng cài được, trình duyệt giữ bản cũ tới khi tải lại.</td><td>Bấm <strong>Tải lại</strong> ở hộp <em>Đã có phiên bản mới</em> góc phải dưới, hoặc đóng hết thẻ rồi mở lại.</td></tr>
<tr><td>Sản phẩm không hiện ở màn Tác động giá</td><td>Định mức của sản phẩm không chứa mã đang chọn, hoặc sản phẩm chưa có định mức.</td><td>Kiểm ở {ref(BOM_TITLE, "Định mức bao bì")}.</td></tr>
<tr><td>CP bao bì để trống, xu hướng <em>Chưa có giá</em></td><td>Thiếu giá chai.</td><td>Nhập báo giá cho mã chai ({ref(PRICES_TITLE, "Bảng giá VTBB")}).</td></tr>
<tr><td>Vừa sửa đơn mua hàng, giá trên màn chưa đổi</td><td>Chỉ đơn đã duyệt mới vào sổ giá; đơn nháp, chờ duyệt chưa tính.</td><td>Duyệt đơn rồi tải lại màn.</td></tr>
<tr><td>Lưu báo giá báo <em>Đã có báo giá cùng mã, NCC và ngày hiệu lực</em></td><td>Mã đó đã có báo giá của cùng nhà cung cấp (kể cả cùng bỏ trống nhà cung cấp) với cùng ngày hiệu lực.</td><td>Sửa báo giá đang có ở màn Báo giá VTBB, hoặc chọn ngày hiệu lực khác ({ref(PRICES_TITLE, "Bảng giá VTBB")}).</td></tr>
<tr><td>Ghi thật nhầm một tệp Excel của cụm</td><td>Lô định mức, báo giá, sổ Misa không có nút Hoàn tác.</td><td>Dùng nút <strong>Xóa dữ liệu của lô này</strong> ở trang lô ({ref(PURGE_TITLE, "Xóa dữ liệu theo lô")}).</td></tr>
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
<li>Người cần Nhập từ Excel định mức, Nhập báo giá, Nạp sổ Misa: thêm quyền tạo và xem của <strong>Quản lý Import</strong> (Nạp sổ Misa cần thêm quyền Sửa của Giá bao bì). Người được gỡ lô nhập nhầm bằng nút Xóa dữ liệu của lô này: quyền <strong>Xóa</strong> của Giá bao bì và quyền xem Quản lý Import.</li>
<li>Người được giao đăng xuất rồi đăng nhập lại để menu hiện.</li>
</ol>
<p>Giá bao bì là <strong>giá vốn</strong>, thuộc nhóm dữ liệu nhạy cảm của Thu mua: tick Xem / Xuất cho vai trò mặc định của mọi tài khoản thì màn phân quyền hiện dòng nhắc màu vàng. Chỉ giao cho người thật sự cần.</p>

<h2>Dành cho quản trị: hai đường nạp Sổ Misa</h2>
<p>Sổ Misa nạp được bằng hai đường: nút <strong>Nạp sổ Misa</strong> (tệp Excel, qua Quản lý Import, đường dùng hằng ngày) và công cụ quản trị nạp từ báo cáo HTML (bộ phận kỹ thuật chạy trên máy chủ). Hai đường đánh số dòng khác nhau nên <strong>không trộn được</strong>: khi đã có lô Nạp sổ Misa ghi thật mà sổ đang có dòng Misa, công cụ nạp từ HTML từ chối chạy. Muốn đổi sang nạp bằng HTML thì phải gỡ hết sổ Misa trước. Dòng Misa nạp bằng HTML không thuộc lô nào nên không gỡ được bằng nút Xóa dữ liệu của lô này.</p>""",
        },
    ],
}

EXPECTED_ARTICLES = 10
#  Chuỗi không được lọt vào bài: tên khóa ngưỡng (đã bỏ hẳn ở phase 04) — chặn lỡ tay chép lại câu cũ.
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
    assert not leaked, f"Bài nhắc tới ngưỡng giá đã bỏ: {leaked}"
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
