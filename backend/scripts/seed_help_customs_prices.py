# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp: TRA CỨU THỊ TRƯỜNG (bao-CR-470, A-04 của doc/erp/hai-quan/01; sửa ở duoc-CR-752).

Hai bài dưới nhóm DỰNG TAY "Dành cho Nhân viên Mua hàng" (cây Thu mua, không có script sở hữu):
- "Tra cứu thị trường": dữ liệu là gì (dòng hàng, không phải tờ khai), năm thẻ của Giá thị trường, Tra cứu
  hóa chất (nút Cột ẩn / hiện mọi cột, duoc-CR-609/610), bốn luật đọc biểu đồ, cảnh báo pháp lý, nạp dữ liệu và
  hoàn tác, hỏi trợ lý AI.
- "Tra cứu thị trường: cấu hình ...": bốn khối của mục Cấu hình (bao-CR-501, mã dạng chế phẩm duoc-CR-684).

Chạy trong container api (LOCAL / dev — KHÔNG chạy ở prod khi đại ca chưa bảo):
    docker compose exec -T api python scripts/seed_help_customs_prices.py
    docker compose exec -T api python scripts/seed_help_customs_prices.py --dry-run

duoc-CR-752: bỏ kiểu xóa bài rồi chèn lại (đổi id mỗi lần chạy, để lại mảnh RAG mồ côi) — nay dùng
`help_seed_common.run_article_upsert`: chỉ thêm hoặc ghi đè đúng bài cùng tiêu đề dưới thẻ cha, giữ id, không
đụng bài khác của cây Thu mua; thiếu thẻ cha thì bỏ qua bài đó. Chạy lại vô hại.

Nội dung phải KHỚP với doc/erp/hai-quan/chuc-nang/11-giao-dien.md, màn /procurement/customs-prices và
`frontend-v2/src/modules/procurement/config/customs-*-crud.tsx`. Không nêu tên doanh nghiệp có trong dữ liệu.
"""
from help_seed_common import ref, run_article_upsert

STAFF_PARENT_TITLE = "Dành cho Nhân viên Mua hàng"
ARTICLE_TITLE = "Tra cứu thị trường"  # bao-CR-500: đổi từ "Tra cứu giá hải quan"

SUMMARY = (
    "Xem giá và lượng của thị trường theo tờ khai hải quan: lọc theo tên hàng, hoạt "
    "chất, mã HS; biểu đồ giá theo tháng, quý, năm; ai đang nhập; cảnh báo pháp lý và biểu thuế"
)

CONTENT = """<h2>I. Màn này dùng để làm gì</h2>
<p>Trước khi mua một mặt hàng, người thu mua cần biết <strong>thị trường đang nhập mặt hàng đó về Việt Nam với giá bao nhiêu, lượng bao nhiêu, và tháng nào giá tốt</strong>. Màn <strong>Tra cứu thị trường</strong> (menu <em>Mua hàng</em>) trả lời câu đó bằng dữ liệu tờ khai hải quan do người được giao nạp vào từ tệp Excel.</p>
<p>Màn này <strong>độc lập</strong>: không nối với danh mục vật tư, tồn kho hay lịch sử mua hàng của công ty. Tìm theo chữ, không theo mã sản phẩm nội bộ.</p>
<p>Cần quyền <strong>Tra cứu thị trường</strong> (xem). Nạp dữ liệu, hoàn tác, xuất Excel là các quyền riêng — không có quyền thì không thấy nút.</p>

<h2>II. Một dòng là gì</h2>
<p>Mỗi dòng trên màn là <strong>một dòng hàng</strong> trên tờ khai, không phải một tờ khai. Một tờ khai có thể gồm nhiều dòng hàng, và tệp dữ liệu không có số tờ khai, nên mọi con số trên màn đều đếm theo <strong>dòng hàng</strong>.</p>
<p>Bảng hiện <strong>đủ 32 cột đúng thứ tự và tiêu đề như tệp Excel</strong> hải quan, cả <em>Đơn giá khai báo</em> lẫn <em>Đơn giá điều chỉnh</em>. Biểu đồ và các con số thống kê dùng giá điều chỉnh nếu có, không thì giá khai báo (đổi được ở nút <em>Giá</em> trên thẻ Biểu đồ). Cột nào không cần thì ẩn ở nút <strong>Cột</strong>.</p>
<p>Hai cột cuối <strong>Hoạt chất (suy ra)</strong> và <strong>Hàm lượng / dạng (suy ra)</strong> do hệ thống <strong>suy ra</strong> từ tên hàng (tên hàng là chữ tự do). Khoảng một nửa số dòng nhận ra được hoạt chất; phần còn lại phần lớn là hóa chất khử trùng, tẩy rửa. Dòng không nhận ra vẫn tìm được bằng tên hàng.</p>

<h2>III. Đầu trang: dữ liệu đang phủ tới đâu</h2>
<p>Dải ô tháng ngay dưới tiêu đề cho biết tháng nào đã có dữ liệu (xanh), tháng nào <strong>trống</strong> (đỏ) và tháng nào chưa tới (mờ). Một tháng đã qua mà trống gần như luôn là do <strong>quên nạp một tệp</strong> — báo cho người phụ trách nạp dữ liệu.</p>

<h2>IV. Tìm và lọc</h2>
<ul>
<li><strong>Tên hàng / hoạt chất</strong>: gõ, ví dụ <em>ATRAZINE</em>, <em>mancozeb</em>; ngưng gõ một chút là bảng tự lọc (Enter để lọc ngay). Khớp cả tên hàng lẫn hoạt chất đã suy ra.</li>
<li><strong>Mã HS · Xuất xứ · Đơn vị tính · Phân loại · Hàm lượng / dạng · Ngày đăng ký</strong>: chọn xong là bảng lọc ngay, không cần bấm nút.</li>
<li><strong>Lọc thêm</strong> mở sáu ô phụ (nguyên tệ, giao hàng, tệp nguồn, ba khoảng số); thu gọn lại được cả khi đang có giá trị, số ô đang áp hiện cạnh nút.</li>
<li>Bộ lọc nằm trên <strong>địa chỉ trang</strong>: gửi đường dẫn cho người khác là họ thấy đúng kết quả; tải lại trang hay bấm Quay lại vẫn giữ bộ lọc.</li>
<li>Muốn xem riêng một doanh nghiệp: sang thẻ <em>Doanh nghiệp</em>, bấm vào dòng của doanh nghiệp đó. Thẻ nhỏ <em>Doanh nghiệp: ...</em> hiện dưới thanh lọc, bấm dấu x để bỏ.</li>
</ul>
<p>Bảng trống có hai câu khác nhau: <em>Chưa có dữ liệu hải quan</em> nghĩa là chưa ai nạp gì; <em>Không có dòng hàng nào khớp bộ lọc</em> nghĩa là bộ lọc quá hẹp hoặc gõ sai chữ.</p>

<h2>V. Năm thẻ của Giá thị trường và các mục khác</h2>
<p>Menu <strong>Tra cứu thị trường</strong> có các mục con: <strong>Giá thị trường</strong> (năm thẻ chuyển qua lại trên đầu trang, bảng dưới),
<strong>Tra cứu hóa chất</strong>, <strong>Tra cứu Thuốc BVTV</strong>, <strong>Lịch sử nạp</strong> và <strong>Cấu hình</strong> (chỉ người được giao mới thấy, xem bài
{config_ref}).</p>
<table>
<thead><tr><th>Thẻ</th><th>Cho biết gì</th></tr></thead>
<tbody>
<tr><td><strong>Danh sách</strong></td><td>Các dòng hàng khớp bộ lọc, mới nhất lên đầu. Bấm một dòng để xem đủ 32 trường. Nút <em>Xuất dữ liệu</em> có ba mục: <em>Xuất ngay</em> tải về một tệp đúng các dòng đang lọc (tối đa 50.000 dòng); <em>Xuất toàn bộ theo bộ lọc (chạy nền)</em> xuất hết các dòng khớp bộ lọc, chia mỗi tệp 50.000 dòng, xong thì chuông báo; <em>Lô xuất của tôi</em> liệt kê các lần xuất đó, xem tiến độ và tải từng tệp (tệp giữ 7 ngày rồi tự xóa). Mỗi người chỉ chạy một lô xuất một lúc.</td></tr>
<tr><td><strong>Biểu đồ</strong></td><td>Giá thấp nhất, bình quân, cao nhất và lượng nhập theo <strong>tháng / quý / năm</strong>. Chỉ hiện khi đã nhập từ khóa hoặc chọn mã HS.</td></tr>
<tr><td><strong>Doanh nghiệp</strong></td><td>20 doanh nghiệp nhập nhiều nhất mặt hàng đang lọc: số dòng, tổng lượng, thị phần, giá bình quân, lần nhập gần nhất. Gộp theo mã số thuế.</td></tr>
<tr><td><strong>So sánh</strong></td><td>Đặt 2–5 mặt hàng hoặc hoạt chất cạnh nhau trên cùng một biểu đồ, cùng một đơn vị tính.</td></tr>
<tr><td><strong>Thuế</strong></td><td>Gõ mã HS (ít nhất 4 chữ số, ví dụ 38089199) để xem thuế suất XNK, VAT và thuế theo hiệp định thương mại tự do.</td></tr>
</tbody>
</table>
<p><strong>Tra cứu hóa chất</strong> (mục riêng trên menu): tìm hóa chất trong các danh mục pháp lý theo tên, số CAS hoặc công thức (ví dụ H2SO4), lọc
theo văn bản. Bảng có nút <strong>Cột</strong> ở góc phải hàng lọc: bỏ tick để ẩn cột không cần, tick lại để hiện, kéo để đổi thứ tự. Cột nào cũng
ẩn được, kể cả <em>Phụ lục / Văn bản</em>, <em>Mã số CAS</em>, <em>Ngưỡng / Mức cấm</em> và <em>Lưu ý</em>; lựa chọn được nhớ trên máy cho lần mở sau. Trên điện
thoại bảng hiện thành thẻ nên không có nút này. Bản Thu mua cũ cũng có nút <strong>Cột</strong> trên bảng này, báo <em>Cột (ẩn n)</em> khi đang ẩn, kèm
<strong>Chọn tất cả</strong> và <strong>Mặc định</strong> để hiện lại.</p>

<h2>VI. Đọc biểu đồ cho đúng — bốn điều</h2>
<ol>
<li><strong>Mỗi lần chỉ vẽ một đơn vị tính.</strong> Cùng một hoạt chất có dòng tính bằng kg, có dòng tính bằng lít — cộng chung là ra con số vô nghĩa. Hàng nút đơn vị phía trên biểu đồ cho chọn đơn vị, mặc định là đơn vị nhiều dòng nhất.</li>
<li><strong>Kỳ không có dòng nào thì để trống</strong>, đường giá đứt ở đó. Trống không có nghĩa là giá bằng 0.</li>
<li><strong>Kỳ có dưới 5 dòng vẽ điểm rỗng</strong> và không bao giờ được chọn làm <em>kỳ giá tốt nhất</em> (điểm xanh lá). Một tháng trông rẻ nhất mà chỉ dựa trên 3 dòng thì chưa đủ để tin.</li>
<li><strong>Dải tô nhạt là khoảng thấp – cao.</strong> Dải rộng thường do cùng một từ khóa đang trộn thuốc kỹ thuật với thành phẩm. Lọc thêm <em>Hàm lượng / dạng</em> (ví dụ 97%) để tách ra.</li>
</ol>
<p>Dòng chữ vàng trên biểu đồ nói biểu đồ đang dựa trên bao nhiêu dòng, bao nhiêu tháng, bao nhiêu năm. Khi mới có <strong>một năm</strong> dữ liệu, biểu đồ chỉ cho thấy xu hướng trong năm đó, <strong>chưa đủ để kết luận theo mùa vụ</strong>.</p>

<h2>VII. Cảnh báo pháp lý</h2>
<p>Gõ từ khóa trùng một hóa chất trong danh sách <strong>hoạt chất cấm</strong>, danh sách <strong>có ngưỡng khối lượng</strong> hoặc danh sách <strong>phải công bố theo lô</strong> thì một dải cảnh báo đỏ hiện ngay dưới thanh lọc, nói rõ văn bản và việc cần lưu ý. Đây là tra cứu tham khảo; trước khi quyết định vẫn phải đối chiếu văn bản gốc.</p>
<p>Các danh sách đó nằm ở khối <em>Danh mục hóa chất theo văn bản</em> trong mục <strong>Cấu hình</strong> (quyền riêng). Khi văn bản thay đổi, người có quyền sửa trực tiếp ở đó.</p>

<h2>VIII. Nạp dữ liệu (người có quyền nạp)</h2>
<ol>
<li>Bấm <strong>Nạp dữ liệu</strong>, chọn một hoặc nhiều tệp <em>.xls / .xlsx</em> kết xuất từ hệ thống hải quan (mẫu GTT02, đủ 32 cột), bấm <strong>Chạy thử</strong>.</li>
<li>Xem bảng chạy thử: số dòng mới, số dòng <strong>đã có</strong> và số dòng <strong>trùng trong tệp</strong> (hai loại này sẽ được bỏ qua), khoảng ngày, số ngày đã tự sửa. Lúc này chưa có gì được ghi.</li>
<li>Bấm <strong>Áp dụng</strong>. Hệ thống báo khi ghi xong.</li>
</ol>
<ul>
<li>Hệ thống tự so trùng: dòng giống hệt một dòng đã có trong bảng giá, hoặc lặp lại một dòng phía trên trong cùng tệp, sẽ <strong>được bỏ qua</strong> — nạp lại một tệp hay nạp các tệp chồng ngày nhau không làm nhân đôi dữ liệu. Tệp GTT02 không có cột <em>ID</em> thì không dòng cũ nào bị xóa hay ghi đè.</li>
<li>Dòng mới trùng ngày, doanh nghiệp, đối tác, mã HS, số thứ tự và tên hàng với một dòng đã có nhưng <strong>khác giá hoặc số lượng</strong> vẫn được thêm (thường là một lô hàng khác), kèm ghi chú <em>nghi sửa giá</em> trong nhật ký lô để người nạp rà. Nếu đúng là nguồn sửa số liệu thì hoàn tác lần nạp cũ rồi nạp lại tệp đúng.</li>
<li><strong>Sửa hàng loạt bằng tệp xuất:</strong> tệp xuất từ màn này có cột <em>ID</em> và <em>Thao tác</em>. Sửa ô của dòng nào rồi nạp lại cả tệp thì chỉ dòng đã sửa được <strong>ghi đè</strong> (dòng không đổi được bỏ qua); gõ <em>xóa</em> ở cột <em>Thao tác</em> thì dòng có ID đó bị xóa. Hoàn tác lần nạp trả các dòng đó về như trước.</li>
<li>Mỗi tệp nạp tối đa <strong>30 MB</strong> (một tệp xuất 50.000 dòng khoảng 13 MB); tệp lớn hơn bị từ chối, chia nhỏ rồi nạp lại.</li>
<li>Cột ngày đăng ký trong tệp xuất đôi khi bị Excel đảo ngày và tháng; hệ thống tự nhận ra và đọc lại. Ô ngày có dấu lịch màu cam là dòng đã được sửa.</li>
<li><strong>Lịch sử nạp</strong> liệt kê mọi lần nạp, ai nạp, lúc nào, số dòng bỏ qua vì trùng, kèm nhật ký từng dòng. Hoàn tác một lần nạp chỉ xóa đúng các dòng lần đó đã thêm. Riêng các lần nạp cũ (trước khi có so trùng) đã thay dòng cũ thì không hoàn tác được.</li>
</ul>

<h2>IX. Hỏi trợ lý AI</h2>
<p>Trợ lý AI (cả trên web lẫn bot Telegram) đọc được cùng dữ liệu này nếu người hỏi có quyền xem. Các kiểu câu hỏi:</p>
<ul>
<li><strong>Giá theo kỳ, so sánh:</strong> <em>Giá atrazine nhập về theo tháng bao nhiêu?</em>, <em>So giá atrazine với mesotrione</em> — so tối đa 5 mặt hàng, cùng một đơn vị tính.</li>
<li><strong>Thời điểm mua:</strong> <em>Nên mua mancozeb vào tháng nào?</em>, <em>Có nên mua atrazine lúc này không?</em> — trợ lý nói giá tháng gần nhất đang thấp, trung bình hay cao so với các tháng khác, xu hướng mấy tháng gần đây, và dữ liệu mới tới ngày nào. Tháng gần nhất quá ít lô thì trợ lý nói rõ và lấy tháng đủ dữ liệu gần nhất làm mốc.</li>
<li><strong>Thị trường:</strong> <em>Ai đang nhập atrazine nhiều nhất?</em>, <em>Mua atrazine của ai, từ nước nào?</em>, <em>Lô atrazine gần nhất giá bao nhiêu?</em></li>
<li><strong>Pháp lý và thuế:</strong> <em>H2SO4 có phải khai báo không?</em>, <em>Carbosulfan có bị cấm không?</em>, <em>Thuế nhập mã 38089199 bao nhiêu?</em> — trợ lý chỉ nói đúng danh mục đã nạp, không nêu mức phạt (dữ liệu không có), và không có trong danh mục thì KHÔNG có nghĩa là được phép.</li>
</ul>
<p>Trợ lý luôn nói kèm <strong>độ tin cậy</strong> và số dòng dữ liệu, chỉ gợi ý tháng có đủ dữ liệu, và nhắc cảnh báo pháp lý nếu có. Trợ lý chỉ biết <strong>giá thị trường</strong> — không biết tồn kho, nhu cầu sản xuất, hạn dùng hay dòng tiền của công ty — nên câu trả lời để tham khảo, không thay cho quyết định mua.</p>

<h2>X. Câu hỏi thường gặp</h2>
<p><strong>Thẻ Biểu đồ chỉ hiện một câu nhắc, không có hình?</strong> Chưa nhập từ khóa hoặc mã HS. Biểu đồ của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng nên không vẽ.</p>
<p><strong>Tổng lượng trên biểu đồ ít hơn ở Danh sách?</strong> Biểu đồ chỉ tính đơn vị đang chọn; bấm sang đơn vị khác để xem phần còn lại.</p>
<p><strong>Doanh nghiệp tôi tìm có hai cách viết tên?</strong> Hệ thống gộp doanh nghiệp theo mã số thuế, nên hai cách viết vẫn là một doanh nghiệp ở thẻ Doanh nghiệp.</p>
"""

CONFIG_TITLE = "Tra cứu thị trường: cấu hình từ khóa, từ đồng nghĩa và mã dạng chế phẩm"  # duoc-CR-752

CONFIG_SUMMARY = (
    "Dành cho người được giao cấu hình Tra cứu thị trường: bốn khối ở mục Cấu hình (từ khóa Thành phẩm / Nguyên liệu, "
    "từ đồng nghĩa tìm kiếm, mã dạng chế phẩm thuốc BVTV, danh mục hóa chất theo văn bản), khi nào bấm Gắn lại nhãn"
)

CONFIG_CONTENT = """<h2>I. Mở ở đâu, ai thấy</h2>
<p>Vào <strong>Mua hàng ▸ Tra cứu thị trường ▸ Cấu hình</strong>. Mục này gom các danh mục điều khiển cách màn tra cứu gắn nhãn và tìm kiếm, nên không có màn riêng ở chỗ khác.</p>
<ul>
<li>Ba khối đầu (từ khóa, từ đồng nghĩa, mã dạng chế phẩm) hiện với người có quyền <strong>thêm, sửa hoặc xóa</strong> ở Tra cứu thị trường.</li>
<li>Khối <strong>Danh mục hóa chất theo văn bản</strong> hiện với người có quyền <strong>xem</strong> danh mục hóa chất (quyền riêng).</li>
<li>Không có quyền nào ở trên thì menu không có mục <strong>Cấu hình</strong>.</li>
<li>Bản Thu mua cũ cũng có thẻ <strong>Cấu hình</strong> với cùng các khối từ khóa, từ đồng nghĩa và mã dạng chế phẩm; dữ liệu là một.</li>
</ul>

<h2>II. Bốn khối</h2>
<table>
<thead><tr><th>Khối</th><th>Dùng để</th><th>Lưu ý</th></tr></thead>
<tbody>
<tr><td><strong>Từ khóa Thành phẩm / Nguyên liệu</strong></td><td>Hệ thống tự gắn nhãn từng dòng hàng: tên hàng chứa từ khóa loại <em>Nguyên liệu</em> thì là nguyên liệu kỹ thuật, còn lại là thành phẩm. Nhãn này là bộ lọc <em>Phân loại</em> trên màn tra cứu.</td><td>Thêm, sửa hay xóa từ khóa xong phải bấm <strong>Gắn lại nhãn</strong> thì các dòng đã nạp mới đổi theo. Từ ngắn (TC, TG…) chỉ khớp khi đứng thành một từ; từ dài khớp cả khi nằm trong chuỗi. Chọn <em>Thành phẩm</em> cho từ khóa ngoại lệ muốn thắng ngược.</td></tr>
<tr><td><strong>Từ đồng nghĩa tìm kiếm</strong></td><td>Khai một nhóm gồm <strong>Từ gốc</strong> và các <strong>Từ đồng nghĩa</strong>. Gõ từ nào trong nhóm vào ô tìm của màn tra cứu cũng ra kết quả của cả nhóm, ví dụ nhóm WG gồm WDG, cốm phân tán.</td><td>Mỗi cách viết một dòng hoặc ngăn bằng dấu chấm phẩy; không phân biệt hoa thường. Nồng độ (3,6% · 3.6EC · 36 G/L) hệ thống tự quy đổi, không cần khai.</td></tr>
<tr><td><strong>Mã dạng chế phẩm</strong></td><td>Tra ý nghĩa mã dạng chế phẩm thuốc BVTV trên tên hàng (EC, SC, WG…): tên tiếng Anh, tên tiếng Việt, đặc điểm.</td><td>Số đứng trước mã: dạng rắn (WP, WG, SG, SP, GR) là % khối lượng, dạng lỏng (EC, SC, SL, EW…) thường là g/L. Khối này chỉ để tra cứu, không ảnh hưởng gắn nhãn hay tìm kiếm.</td></tr>
<tr><td><strong>Danh mục hóa chất theo văn bản</strong></td><td>Nguồn của dải cảnh báo pháp lý trên màn tra cứu và của mục <strong>Tra cứu hóa chất</strong>.</td><td>Cảnh báo chỉ lấy từ ba danh sách: hoạt chất cấm, NĐ 24 Phụ lục IV (có ngưỡng) và danh sách phải công bố. Chuyển sang ngừng dùng thì hóa chất không còn hiện trong tra cứu và cảnh báo.</td></tr>
</tbody>
</table>

<h2>III. Thêm, sửa, tạm tắt</h2>
<ol>
<li>Tìm nhanh bằng ô tìm của từng khối, lọc <strong>Trạng thái</strong> (<em>Đang dùng</em> / <em>Ngừng dùng</em>); khối từ khóa lọc thêm theo <strong>Loại</strong>.</li>
<li>Bấm nút <strong>Thêm từ khóa</strong>, <strong>Thêm nhóm từ</strong>, <strong>Thêm mã dạng</strong> hoặc <strong>Thêm hóa chất</strong> ở góc phải khối để thêm mới; bấm vào một dòng để mở hộp sửa.</li>
<li>Muốn tạm tắt mà không mất dữ liệu: mở dòng, tắt công tắc <strong>Đang sử dụng</strong> rồi lưu. Xóa hẳn chỉ khi chắc không dùng lại.</li>
<li>Sửa ở khối từ khóa xong: bấm <strong>Gắn lại nhãn</strong>. Hệ thống báo đã gắn lại bao nhiêu dòng, bao nhiêu nguyên liệu, bao nhiêu thành phẩm.</li>
</ol>
<p>Người chỉ có quyền xem vẫn mở được hộp để đọc, nhưng không có nút lưu hay xóa.</p>

<h2>IV. Dữ liệu có sẵn</h2>
<p>Ngày 26/10/2026 bộ cấu hình ban đầu đã được nạp sẵn: thêm 4 từ khóa nguyên liệu, 10 nhóm từ đồng nghĩa (phần lớn là cách viết khác nhau của mã dạng chế phẩm, như WG và WDG) và 18 mã dạng chế phẩm, rồi gắn lại nhãn cho toàn bộ dòng hàng. Người được giao chỉ cần bổ sung khi gặp cách viết mới.</p>
<p>Cách tìm và đọc số liệu xem ở bài {main_ref}.</p>
"""

ARTICLES = [
    (STAFF_PARENT_TITLE, ARTICLE_TITLE, SUMMARY,
     CONTENT.replace("{config_ref}", ref(CONFIG_TITLE, CONFIG_TITLE))),
    (STAFF_PARENT_TITLE, CONFIG_TITLE, CONFIG_SUMMARY,
     CONFIG_CONTENT.replace("{main_ref}", ref(ARTICLE_TITLE, ARTICLE_TITLE))),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD Tra cứu thị trường (bao-CR-470, duoc-CR-752) + kho vector")
