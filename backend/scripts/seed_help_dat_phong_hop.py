# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ ĐẶT PHÒNG HỌP.

Dựng cây bài viết: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ") -> 8 bài
chia theo TÁC VỤ (xem lịch & đặt nhanh / lập phiếu & mời / kéo thả đổi lịch /
theo dõi & hủy / duyệt phiếu / câu báo lỗi / danh mục phòng / phân quyền).

Bản 2 (04/09/2026) viết dày hơn hẳn bản đầu: đi theo TỪNG BƯỚC với đúng nhãn nút
và nhãn ô trên màn hình, thêm ba bài mới — *theo dõi/sửa/hủy phiếu*, *xử lý câu
báo lỗi*, và tách phần quản trị thành *danh mục phòng* + *phân quyền & luồng*.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_dat_phong_hop.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/18-dat-phong-hop.md` và
gói tri thức trợ lý `app/modules/assistant/packs/50-dat-phong-hop.md`. Ba nơi
lệch nhau thì người dùng đọc một đằng, trợ lý trả lời một nẻo.

⚠️ Tiêu đề bài phải KHÁC mọi bài đang có trong Trung tâm trợ giúp: portal tra
ngược slug -> id ngay trên client, hai bài trùng tiêu đề là trùng slug và liên
kết chéo sẽ nhảy nhầm bài (vì vậy bài lỗi ở đây tên «… khi đặt phòng», không
trùng bài cùng loại bên Nghỉ phép).
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: F401,E402 — nạp đủ mapper trước khi query
from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import (  # noqa: E402
    HelpArticle,
    HelpHomeItem,
    HelpHomeSection,
)

ROOT_TITLE = "Hướng dẫn sử dụng Đặt phòng họp"


def slugify(value: str) -> str:
    """Sinh slug y hệt `slugify()` của help-center (help-slug.tsx).

    Portal tra ngược slug -> id ngay trên client, lệch một ký tự là liên kết chết.
    """
    value = value.replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFD", value)
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"^-+|-+$", "", value)


def ref(target_title: str, label: str) -> str:
    return (
        f'<a href="/{slugify(target_title)}" '
        'style="color:var(--primary,#2563eb);font-weight:600;text-decoration:underline">'
        f"{label}</a>"
    )


XEM_LICH = "Xem lịch phòng và đặt nhanh"
LAP_PHIEU = "Lập phiếu đặt phòng và mời người dự"
KEO_THA = "Đổi giờ và đổi phòng bằng kéo thả"
THEO_DOI = "Theo dõi, sửa và hủy phiếu đặt phòng"
DUYET = "Duyệt phiếu đặt phòng"
BAO_LOI = "Xử lý câu báo lỗi khi đặt phòng"
DANH_MUC = "Dành cho quản trị — Danh mục phòng"
QUYEN = "Quản trị — Phân quyền và luồng duyệt đặt phòng"


TREE = {
    "title": ROOT_TITLE,
    "icon": "building",
    "summary": "Xem phòng nào trống, đặt phòng, kéo thả đổi lịch, duyệt phiếu",
    "content": f"""<h2>Đặt phòng họp là gì?</h2>
<p>Phân hệ để <strong>giữ chỗ phòng họp</strong>: xem phòng nào đang trống, lập phiếu đặt, gửi duyệt và mời người tham dự. Vào bằng menu <strong>Nhân sự ▸ Đặt phòng họp</strong>.</p>

<h2>Ba khu vực, chuyển bằng thanh tab</h2>
<table>
<thead><tr><th>Tab</th><th>Dùng để</th><th>Ai dùng</th></tr></thead>
<tbody>
<tr><td><strong>Lịch đặt phòng</strong></td><td>Xem cả ngày một lượt, bấm ô trống để đặt, kéo thả đổi lịch.</td><td>Mọi người</td></tr>
<tr><td><strong>Phiếu đặt phòng</strong></td><td>Danh sách phiếu: phiếu của bạn, phiếu chờ bạn duyệt, phiếu bạn đã duyệt.</td><td>Mọi người</td></tr>
<tr><td><strong>Danh mục phòng</strong></td><td>Khai phòng, sức chứa, thiết bị.</td><td>Quản trị / hành chính</td></tr>
</tbody>
</table>

<h2>Điều quan trọng nhất phải nhớ</h2>
<p>⚠️ <strong>Phòng bị giữ ngay khi bạn bấm «Gửi duyệt», không đợi ai duyệt xong.</strong> Nghĩa là nộp phiếu xong là yên tâm — không ai chen ngang được.</p>
<p>Ngược lại, <strong>phiếu để ở «Nháp» thì KHÔNG giữ chỗ gì cả</strong>: người khác vẫn đặt mất phòng như thường. Chọn xong phòng và giờ thì gửi duyệt luôn, đừng để nháp qua đêm.</p>

<h2>Vòng đời một tờ phiếu</h2>
<pre>              gửi duyệt              ký chặng cuối
Nháp  ───────────────────►  Chờ duyệt  ────────────────►  Đã duyệt
  ▲    (chưa giữ phòng)      (ĐÃ giữ phòng)   │            (giữ phòng
  │                            │  │           │             + gửi thư mời)
  └──── Trả về chỉnh sửa  ◄────┘  └──► Từ chối (khóa hẳn)
        Đã hủy  ◄── người đặt tự rút, kể cả sau khi đã duyệt</pre>
<p><strong>Ba kết cục không-duyệt đều NHẢ phòng</strong>: Trả về · Từ chối · Đã hủy. Nhả rồi thì ai đặt cũng được.</p>

<h2>Ba câu hay hỏi nhất</h2>
<ul>
<li><strong>«Đặt xong có phải chờ duyệt mới giữ được phòng không?»</strong> — không, giữ ngay lúc gửi duyệt.</li>
<li><strong>«Người tôi mời sao chưa thấy thông báo?»</strong> — thư mời chỉ gửi <strong>sau khi phiếu được duyệt</strong>. Xem {ref(LAP_PHIEU, "bài Lập phiếu")}.</li>
<li><strong>«Dời giờ họp có phải duyệt lại không?»</strong> — không. Kéo thả trên lịch, trạng thái giữ nguyên. Xem {ref(KEO_THA, "bài Kéo thả")}.</li>
</ul>

<h2>Đọc theo việc bạn cần làm</h2>
<p><strong>Người đặt phòng:</strong> {ref(XEM_LICH, "Xem lịch & đặt nhanh")} · {ref(LAP_PHIEU, "lập phiếu & mời người dự")} · {ref(KEO_THA, "kéo thả đổi lịch")} · {ref(THEO_DOI, "theo dõi, sửa, hủy")} · {ref(BAO_LOI, "câu báo lỗi")}.</p>
<p><strong>Người duyệt:</strong> {ref(DUYET, "Duyệt phiếu đặt phòng")}.</p>
<p><strong>Quản trị:</strong> {ref(DANH_MUC, "danh mục phòng")} · {ref(QUYEN, "phân quyền và luồng duyệt")}.</p>""",
    "children": [
        {
            "title": XEM_LICH,
            "icon": "calendar",
            "summary": "Đọc lưới lịch, đổi ngày, lọc phòng, bấm ô trống để đặt ngay",
            "content": f"""<h2>Xem lịch phòng và đặt nhanh</h2>
<p>Tab <strong>Lịch đặt phòng</strong> trả lời đúng một câu: <em>«bây giờ phòng nào còn trống»</em>.</p>

<h2>Đọc lưới</h2>
<ul>
<li><strong>Mỗi phòng một HÀNG</strong>, giờ chạy ngang từ <strong>7:00 đến 20:00</strong>. Tên phòng dính bên trái khi bạn cuộn ngang, kèm vị trí (vd «Tầng 3») ngay dưới.</li>
<li>Mỗi khối màu là một lượt giữ phòng: <strong>xanh lá = đã duyệt</strong>, <strong>vàng cam = chờ duyệt</strong>. Chú giải màu nằm ngay góc trên bên trái.</li>
<li>Phần <strong>tô xám mờ</strong> là ngoài giờ hành chính và giờ nghỉ trưa — vẫn đặt được, chỉ là nhắc bạn nhìn kỹ.</li>
<li><strong>Vạch đỏ dọc</strong> là mốc «bây giờ», chỉ hiện khi bạn đang xem hôm nay.</li>
<li>Rê chuột lên một khối để xem đầy đủ <strong>mã phiếu, nội dung, giờ và người đặt</strong>. Bấm vào khối để mở phiếu.</li>
</ul>
<p>Lưới xếp phòng theo hàng chứ không theo cột là <strong>cố ý</strong>: lấy cột làm phòng thì 20 phòng rộng 4.500px, cuộn bốn màn hình mới xem hết; đảo lại thì số phòng chỉ làm lưới <em>dài xuống</em>, còn cả ngày làm việc nằm trọn một màn.</p>

<h2>Đổi ngày, lọc phòng</h2>
<ul>
<li>Bấm <strong>tên ngày</strong> ở thanh trên để mở lịch chọn ngày; hai nút <strong>mũi tên</strong> (ngày trước / ngày sau) và nút <strong>Hôm nay</strong> nằm cạnh đó.</li>
<li>Ô <strong>«Lọc phòng, tầng, thiết bị…»</strong> lọc ngay trên lưới. Gõ <strong>không dấu vẫn tìm ra</strong> — «tang 3» ra «Tầng 3», «may chieu» ra phòng có máy chiếu.</li>
<li>Đường dẫn <strong>có mang theo ngày</strong>, nên copy link gửi cho người khác là họ mở đúng ngày bạn đang xem.</li>
</ul>

<h2>Đặt nhanh từ ô trống</h2>
<ol>
<li>Rê chuột vào một ô trống trên hàng phòng bạn muốn.</li>
<li>Nhãn <strong>«+ giờ»</strong> hiện lên (ví dụ «+ 14:30»).</li>
<li>Bấm — form đặt phòng mở ra <strong>đã điền sẵn đúng phòng và đúng giờ</strong> đó.</li>
</ol>
<p>Ô chia <strong>nửa tiếng</strong> một, vì họp 30 phút là chuyện thường. Điền nốt nội dung rồi gửi duyệt: {ref(LAP_PHIEU, "xem bài Lập phiếu đặt phòng")}.</p>

<h2>Lịch chỉ xem MỘT ngày</h2>
<p>Không có chế độ tuần. Một ngày làm việc đã chiếm gần trọn bề ngang màn hình; nhân bảy lần thì mỗi cuộc họp còn vài pixel, không đọc nổi.</p>
<p>Muốn nhìn xa hơn một ngày thì sang tab <strong>Phiếu đặt phòng</strong> rồi lọc theo phòng và trạng thái — {ref(THEO_DOI, "xem bài Theo dõi phiếu")}.</p>

<h2>Đừng tin lưới đã cũ</h2>
<p>⚠️ Phòng có thể vừa bị người khác giữ mất <strong>trong lúc bạn đang nhìn</strong>. Lưới không tự làm mới liên tục, và chốt chặn thật nằm ở bước <strong>gửi duyệt</strong>. Thấy trống mà gửi lên bị chặn thì không phải hệ thống sai — là ai đó nhanh tay hơn. Tải lại trang rồi chọn lại.</p>""",
        },
        {
            "title": LAP_PHIEU,
            "icon": "file-text",
            "summary": "Năm bước, giải thích từng ô, chọn phòng còn trống, mời người dự",
            "content": f"""<h2>Lập phiếu đặt phòng và mời người dự</h2>

<h2>Năm bước</h2>
<ol>
<li>Bấm <strong>«Đặt phòng»</strong> ở góc trên bên phải — nút này có ở cả tab <em>Lịch</em> lẫn tab <em>Phiếu</em>. Hoặc {ref(XEM_LICH, "bấm thẳng vào ô trống trên lịch")} để form tự điền sẵn phòng và giờ.</li>
<li>Điền <strong>Nội dung cuộc họp</strong>, <strong>Bắt đầu</strong>, <strong>Kết thúc</strong>.</li>
<li>Bấm nút chọn <strong>Phòng họp</strong> — hộp thoại chỉ bày phòng đang trống trong khung giờ đó.</li>
<li>Ghi <strong>Số người dự</strong> và chọn <strong>Người được mời</strong>.</li>
<li><strong>«Lưu nháp»</strong> để kiểm lại, rồi <strong>«Gửi duyệt»</strong> để giữ phòng.</li>
</ol>
<p>⚠️ Nút <strong>«Gửi duyệt»</strong> chỉ hiện <strong>sau khi phiếu đã được lưu ít nhất một lần</strong>.</p>

<h2>Từng ô trên phiếu</h2>
<table>
<thead><tr><th>Ô</th><th>Bắt buộc</th><th>Ghi gì / cần biết</th></tr></thead>
<tbody>
<tr><td><strong>Nội dung cuộc họp</strong></td><td>Có, khi gửi duyệt</td><td>Người duyệt đọc đúng dòng này để quyết. Ví dụ: <em>«Họp giao ban tuần 37»</em>.</td></tr>
<tr><td><strong>Bắt đầu / Kết thúc</strong></td><td>Có</td><td>Ngày + giờ. Tối đa <strong>24 giờ một lượt</strong> — vượt trần gần như luôn là chọn nhầm sang ngày hôm sau.</td></tr>
<tr><td><strong>Phòng họp</strong></td><td>Có</td><td>Hộp thoại <strong>chỉ bày phòng ĐANG TRỐNG</strong> trong khung giờ vừa chọn. Ô tìm ở đây cũng <strong>bỏ dấu vẫn khớp</strong>.</td></tr>
<tr><td><strong>Số người dự (dự kiến)</strong></td><td>Không</td><td>Hệ so với <strong>sức chứa</strong> của phòng và <strong>chặn lúc lưu</strong> nếu vượt. Phòng chưa khai sức chứa thì không chặn.</td></tr>
<tr><td><strong>Người được mời</strong></td><td>Không</td><td>Họ nhận thông báo <strong>sau khi phiếu được duyệt</strong>.</td></tr>
<tr><td><strong>Ghi chú / chuẩn bị</strong></td><td>Không</td><td>Thứ cần chuẩn bị trước. Ví dụ: <em>«cần máy chiếu, in sẵn 10 bộ tài liệu»</em>.</td></tr>
</tbody>
</table>

<h2>Chọn phòng</h2>
<p>Hộp thoại chọn phòng mặc định <strong>chỉ bày phòng còn trống</strong> trong khung giờ bạn vừa nhập — đó là câu trả lời bạn cần trong 9/10 lần.</p>
<ul>
<li>Muốn xem <strong>cả phòng đang bận</strong> (để đi xin lại người đang giữ) thì bật công tắc trong hộp thoại.</li>
<li>Ô tìm khớp <strong>tên phòng · tầng · thiết bị</strong>, gõ không dấu vẫn ra.</li>
<li>Đổi giờ sau khi đã chọn phòng thì <strong>kiểm lại phòng</strong> — khung giờ mới có thể đã có người.</li>
</ul>

<h2>Mời người tham dự</h2>
<ul>
<li>Thêm từng người vào danh sách. <strong>Mời trùng một người hai lần chỉ ghi một dòng</strong>, và bạn <strong>không tự mời chính mình</strong>.</li>
<li>⚠️ <strong>Người được mời chỉ nhận thông báo SAU khi phiếu được duyệt.</strong> Phiếu còn chờ duyệt thì chưa ai được báo — cuộc họp chưa chắc diễn ra, mà thư đã gửi thì không rút lại được. Cần báo gấp thì tự nhắn cho họ.</li>
<li>Không có quyền xem danh bạ nhân sự thì ô này khóa lại và nói rõ lý do — vẫn đặt phòng được, chỉ là không mời qua hệ thống.</li>
</ul>

<h2>Đặt hộ người khác</h2>
<p>Thư ký đặt hộ sếp thì điền <strong>người đặt</strong> vào ô riêng. <strong>Phòng ban và pháp nhân của phiếu lấy theo người được đặt hộ</strong>, không lấy theo người ngồi gõ. Cả hai đều thấy phiếu trong tab <em>Phiếu của tôi</em>.</p>

<h2>Lưu nháp hay Gửi duyệt?</h2>
<table>
<thead><tr><th></th><th>Lưu nháp</th><th>Gửi duyệt</th></tr></thead>
<tbody>
<tr><td>Giữ phòng?</td><td><strong>KHÔNG</strong> — người khác vẫn đặt mất</td><td><strong>CÓ</strong>, ngay lập tức</td></tr>
<tr><td>Kiểm trùng?</td><td>Không kiểm</td><td>Kiểm, chặn nếu trùng</td></tr>
<tr><td>Hiện trên lịch?</td><td>Không</td><td>Có</td></tr>
<tr><td>Sửa được?</td><td>Sửa thoải mái</td><td>Khóa (trừ giờ và phòng, xem {ref(KEO_THA, "kéo thả")})</td></tr>
<tr><td>Xóa được?</td><td>Được (nút <strong>«Xóa phiếu»</strong>)</td><td>Không — chỉ <strong>hủy</strong></td></tr>
</tbody>
</table>
<p>Sức chứa được kiểm ngay <strong>lúc lưu</strong>, còn trùng giờ thì kiểm <strong>lúc gửi duyệt</strong>.</p>

<h2>Bị chặn vì trùng giờ thì làm gì</h2>
<p>Câu báo lỗi <strong>nói rõ phiếu nào đang giữ, giữ từ mấy giờ tới mấy giờ, đã duyệt hay đang chờ duyệt</strong>. Đọc câu đó rồi chọn một trong ba đường: đi xin lại phòng của người kia · dời giờ · chọn phòng khác. <strong>Bấm lại lần nữa không giúp được gì.</strong></p>
<p>Lưu ý: <strong>hai ca liền nhau KHÔNG tính là trùng</strong>. Họp 9–10h và họp 10–11h đặt được cả hai, đúng cách người ta xếp lịch thật.</p>
<p>Các câu chặn khác: {ref(BAO_LOI, "bài Xử lý câu báo lỗi khi đặt phòng")}.</p>""",
        },
        {
            "title": KEO_THA,
            "icon": "lightbulb",
            "summary": "Kéo khối trên lịch để dời giờ, đổi phòng, đổi độ dài — không phải duyệt lại",
            "content": f"""<h2>Đổi giờ và đổi phòng bằng kéo thả</h2>
<p>Ngay trên {ref(XEM_LICH, "lưới Lịch đặt phòng")}, bạn <strong>kéo khối phiếu</strong> để dời lịch mà không cần mở phiếu ra sửa.</p>

<h2>Bốn thao tác</h2>
<table>
<thead><tr><th>Thao tác</th><th>Đổi gì</th></tr></thead>
<tbody>
<tr><td>Kéo ngang khối</td><td>Giờ bắt đầu và kết thúc, <strong>giữ nguyên độ dài</strong></td></tr>
<tr><td>Kéo dọc sang hàng khác</td><td><strong>Đổi phòng</strong></td></tr>
<tr><td>Kéo mép trái / mép phải</td><td>Độ dài cuộc họp (ngắn nhất <strong>15 phút</strong>)</td></tr>
<tr><td>Bấm (không kéo)</td><td>Mở trang chi tiết phiếu</td></tr>
</tbody>
</table>

<h2>Trong lúc kéo</h2>
<ul>
<li>Một <strong>khung nét đứt</strong> hiện ở chỗ sắp thả, kèm <strong>giờ mới</strong>. Khung đó nằm ở <strong>đúng hàng phòng</strong> bạn đang trỏ tới, nên kéo dọc là thấy ngay nó sẽ rơi vào phòng nào.</li>
<li>Giờ <strong>hút về mốc 15 phút</strong> — không thả được vào 9:03. Chuột không đủ chính xác, mà lịch đầy con số lẻ thì rất khó đọc.</li>
<li>Muốn bỏ giữa chừng thì kéo trả về chỗ cũ, hoặc nhả chuột ra ngoài cửa sổ.</li>
</ul>

<h2>Bốn điều đáng biết</h2>
<ul>
<li><strong>Kéo được cả phiếu «Chờ duyệt» lẫn «Đã duyệt», và trạng thái giữ nguyên</strong> — dời một phiếu đã duyệt <strong>không</strong> bắt đi duyệt lại. Nếu chặn theo luật sửa thông thường (chỉ <em>Nháp</em> mới sửa được) thì tính năng này không dùng được lấy một lần, vì lịch cố ý chỉ vẽ phiếu đang giữ phòng.</li>
<li><strong>Vẫn chặn trùng y hệt.</strong> Kéo vào khung đã có người là bị chặn, khối bật về chỗ cũ và hiện câu báo nói rõ ai đang giữ. Bỏ chốt đó thì ai muốn đặt đôi chỉ cần đặt lệch giờ rồi kéo về.</li>
<li><strong>Phiếu đã duyệt bị dời thì người dự nhận thông báo «Đổi giờ họp».</strong> Cuộc họp bị dời mà không báo thì họ tới đúng phòng cũ vào đúng giờ cũ — tệ hơn cả không mời.</li>
<li><strong>Không kéo sang ngày khác được.</strong> Lưới vẽ một ngày, nên kéo ngang bị kẹp trong 7:00–20:00 của chính ngày đang xem. Dời sang ngày khác thì mở phiếu ra sửa — mà phiếu đã gửi duyệt thì phải <strong>hủy rồi đặt lại</strong>.</li>
</ul>

<h2>Kéo không được?</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nguyên nhân</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Con trỏ không đổi thành hình bàn tay, khối không nhúc nhích</td><td>Bạn <strong>không có quyền sửa phiếu</strong> — thiếu quyền ghi trên khóa <code>room_booking</code>. Lúc đó kéo thả tắt hẳn, khối chỉ bấm mở phiếu.</td><td>Hỏi quản trị, đừng báo lỗi hệ thống. Xem {ref(QUYEN, "bài Phân quyền")}.</td></tr>
<tr><td>Khối kéo được nhưng bật về chỗ cũ, kèm câu báo</td><td>Khung giờ mới đã có người giữ.</td><td>Đọc câu báo xem ai giữ, rồi chọn chỗ khác.</td></tr>
<tr><td>Hệ báo <em>«Phiếu đã hủy hoặc bị từ chối thì không dời được»</em></td><td>Phiếu đó <strong>đã nhả phòng</strong> rồi.</td><td>Lập phiếu mới. Dời một phiếu đã chết chỉ đẻ ra cuộc họp không ai giữ chỗ cho.</td></tr>
</tbody>
</table>""",
        },
        {
            "title": THEO_DOI,
            "icon": "clipboard-list",
            "summary": "Ba tab, sáu trạng thái, bảng làm-được-gì, và khác nhau giữa xóa và hủy",
            "content": f"""<h2>Theo dõi, sửa và hủy phiếu đặt phòng</h2>

<h2>Ba tab trong màn Phiếu đặt phòng</h2>
<table>
<thead><tr><th>Tab</th><th>Chứa gì</th></tr></thead>
<tbody>
<tr><td><strong>Cần tôi duyệt</strong></td><td>Phiếu đang chờ chữ ký của bạn. Đứng <strong>đầu</strong> và <strong>tự được chọn khi có việc</strong>, kèm con số việc đang chờ.</td></tr>
<tr><td><strong>Phiếu của tôi</strong></td><td>Phiếu bạn đặt, hoặc phiếu người khác đặt hộ bạn.</td></tr>
<tr><td><strong>Tôi đã duyệt</strong></td><td>Phiếu bạn từng ký — <strong>chỉ 30 ngày gần đây</strong>.</td></tr>
</tbody>
</table>

<h2>Tìm một tờ phiếu</h2>
<ul>
<li>Ô tìm khớp <strong>số phiếu</strong> hoặc <strong>nội dung cuộc họp</strong>.</li>
<li>Hai ô lọc: <strong>Phòng</strong> và <strong>Trạng thái</strong>.</li>
<li>Cột bảng: <em>Trạng thái · Nội dung cuộc họp · Phòng · Ngày họp · Người đặt</em>. Tab <em>Cần tôi duyệt</em> có thêm <em>Việc của tôi</em> và <strong>Hạn xử lý</strong>.</li>
</ul>
<p>Đây cũng là chỗ <strong>nhìn xa hơn một ngày</strong> — lịch chỉ vẽ được một ngày, còn danh sách thì lọc theo phòng bao nhiêu ngày cũng được.</p>

<h2>Sáu trạng thái</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Nghĩa là</th><th>Phòng</th></tr></thead>
<tbody>
<tr><td><strong>Nháp</strong></td><td>Chưa ai thấy, chưa lên lịch.</td><td><strong>KHÔNG giữ</strong></td></tr>
<tr><td><strong>Chờ duyệt</strong></td><td>Đang trong luồng, hiện màu vàng cam trên lịch.</td><td><strong>ĐANG giữ</strong></td></tr>
<tr><td><strong>Đã duyệt</strong></td><td>Xong, màu xanh lá trên lịch. Người được mời đã nhận thư.</td><td><strong>ĐANG giữ</strong></td></tr>
<tr><td><strong>Trả về chỉnh sửa</strong></td><td>Người duyệt mời bạn sửa rồi gửi lại chính tờ phiếu đó.</td><td>Nhả ra ngay</td></tr>
<tr><td><strong>Từ chối</strong></td><td><strong>Khóa hẳn.</strong> Muốn họp thì lập <strong>phiếu khác</strong>.</td><td>Nhả ra ngay</td></tr>
<tr><td><strong>Đã hủy</strong></td><td>Bạn tự rút.</td><td>Nhả ra ngay</td></tr>
</tbody>
</table>
<p>⚠️ <strong>Nhả phòng nghĩa là ai đặt cũng được</strong>, kể cả người khác. Phiếu bị trả về mà bạn còn muốn phòng đó thì <strong>sửa và gửi lại sớm</strong> — mỗi phút chờ là một phút phòng đang mở cho cả công ty.</p>

<h2>Ở trạng thái nào thì làm được gì</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Sửa nội dung</th><th>Kéo thả đổi giờ</th><th>Xóa phiếu</th><th>Hủy phiếu</th></tr></thead>
<tbody>
<tr><td>Nháp</td><td>Được</td><td>Không hiện trên lịch</td><td>Được</td><td>—</td></tr>
<tr><td>Trả về chỉnh sửa</td><td>Được</td><td>Không hiện trên lịch</td><td>—</td><td>Được</td></tr>
<tr><td>Chờ duyệt</td><td>Không</td><td><strong>Được</strong></td><td>Không</td><td>Được</td></tr>
<tr><td>Đã duyệt</td><td>Không</td><td><strong>Được</strong></td><td>Không</td><td><strong>Vẫn được</strong></td></tr>
<tr><td>Từ chối / Đã hủy</td><td>Không</td><td>Không</td><td>Không</td><td>—</td></tr>
</tbody>
</table>
<p>Nghĩa là sau khi gửi duyệt, <strong>giờ và phòng vẫn đổi được</strong> (bằng kéo thả), còn <strong>nội dung, người mời, số người dự thì khóa</strong>. Cần sửa mấy thứ đó thì hủy phiếu rồi đặt lại, hoặc nhờ người duyệt trả về.</p>

<h2>Xóa phiếu khác Hủy phiếu</h2>
<ul>
<li><strong>Xóa phiếu</strong> — chỉ với phiếu <em>chưa vào luồng</em>. Tờ phiếu biến mất hẳn.</li>
<li><strong>Hủy phiếu</strong> — tờ phiếu <strong>ở lại</strong> với trạng thái <em>Đã hủy</em> kèm lý do, và phòng được nhả.</li>
</ul>

<h2>Hủy phiếu</h2>
<p>Bấm <strong>«Hủy phiếu»</strong> ở màn chi tiết, hộp thoại <em>Hủy phiếu đặt phòng</em> hiện ra và <strong>bắt ghi lý do</strong>. <strong>Hủy được cả phiếu đã duyệt</strong> — họp hoãn là chuyện thường, và không nhả thì phòng bị khóa suốt khung giờ đó dù chẳng ai dùng.</p>
<p>⚠️ <strong>Hoãn họp thì phải vào hủy phiếu.</strong> Không hủy là chiếm chỗ của người khác mà chính bạn cũng không dùng — đây là lỗi tốn kém nhất của cả phân hệ, và nó <strong>không có triệu chứng</strong> nào cho tới khi có người đứng ngoài cửa một phòng trống.</p>

<h2>Không thấy phiếu mình đang tìm?</h2>
<p>Bạn chỉ đọc được phiếu <strong>trong phạm vi dữ liệu</strong> của mình. Phiếu ngoài phạm vi thì hệ báo «Không tìm thấy» — không có nghĩa là phiếu đó không tồn tại, chỉ là bạn không được xem. Nội dung cuộc họp hay chứa chuyện nhân sự nên hệ cố ý chặt tay ở chỗ này.</p>""",
        },
        {
            "title": DUYET,
            "icon": "workflow",
            "summary": "Nhận việc, ba nút và hậu quả, điều gì xảy ra với phòng sau khi ký",
            "content": f"""<h2>Duyệt phiếu đặt phòng</h2>
<p>Dành cho người được giao ký. Duyệt ngay trong <strong>Nhân sự ▸ Đặt phòng họp ▸ tab «Phiếu đặt phòng» ▸ «Cần tôi duyệt»</strong>, không phải sang màn Phê duyệt.</p>

<h2>Nhận việc</h2>
<ul>
<li>Có việc mới, bạn nhận <strong>thông báo chuông</strong> kèm liên kết mở thẳng tờ phiếu.</li>
<li>Tab <em>Cần tôi duyệt</em> đứng đầu, <strong>tự được chọn khi có việc</strong>, kèm con số việc đang chờ.</li>
<li>Cột <strong>Hạn xử lý</strong> cho biết việc đến hạn khi nào.</li>
</ul>

<h2>Đọc gì trước khi ký</h2>
<ol>
<li><strong>Nội dung cuộc họp</strong> — không có dòng này thì bạn duyệt cái gì. Trống là lý do trả về chính đáng.</li>
<li><strong>Phòng · ngày · khung giờ</strong>.</li>
<li><strong>Số người dự</strong> so với sức chứa — hệ đã chặn khi vượt, nhưng phòng chưa khai sức chứa thì không ai chặn cả.</li>
<li><strong>Mục «Mời tham dự»</strong> — <strong>luôn hiện kể cả khi rỗng</strong>, để bạn phân biệt được <em>"chưa mời ai"</em> với <em>"màn hình thiếu mục đó"</em>.</li>
</ol>

<h2>Ba nút</h2>
<table>
<thead><tr><th>Nút</th><th>Dùng khi</th><th>Hậu quả</th></tr></thead>
<tbody>
<tr><td><strong>Duyệt</strong></td><td>Đồng ý</td><td>Sang chặng sau, hoặc xong hẳn nếu là chặng cuối. Xong thì phòng thuộc về phiếu này trong khung giờ đã đặt, và <strong>người được mời nhận thông báo</strong>.</td></tr>
<tr><td><strong>Trả về</strong></td><td>Thiếu thông tin, sửa là được</td><td>Người đặt <strong>sửa rồi gửi lại</strong> chính tờ phiếu đó. <strong>Phòng được nhả trong lúc chờ họ sửa.</strong></td></tr>
<tr><td><strong>Từ chối</strong></td><td>Không cho đặt</td><td><strong>Khóa hẳn</strong> — người đặt phải lập phiếu khác nếu vẫn cần họp. <strong>Phòng được nhả ra ngay.</strong></td></tr>
</tbody>
</table>
<p><strong>Duyệt</strong> không bắt ghi lý do (ô ý kiến không bắt buộc). <strong>Trả về</strong> và <strong>Từ chối</strong> thì <strong>bắt buộc</strong> ghi lý do — người nhận chỉ đọc được đúng dòng đó.</p>
<p>⚠️ <strong>Trả về cũng nhả phòng.</strong> Nghĩa là trả về một phiếu vào giờ cao điểm là mở phòng đó cho cả công ty trong lúc người kia đang sửa. Sửa được ngay bằng một câu nhắn thì nhắn, đừng trả về.</p>

<h2>Vài điều đáng biết</h2>
<ul>
<li><strong>Đang có việc trên tờ phiếu thì bạn đọc được nó</strong>, kể cả khi phạm vi dữ liệu của bạn không với tới. <strong>Ký xong quyền đó đóng lại</strong> — xem lại thì vào tab <strong>Tôi đã duyệt</strong> (30 ngày gần đây).</li>
<li>Chỗ nào <strong>chưa khai luồng duyệt</strong> thì người có quyền duyệt bấm <strong>«Duyệt phiếu»</strong> thẳng trên phiếu. Phiếu <em>đang</em> chạy trong luồng thì đường đó bị chặn.</li>
<li>Duyệt xong <strong>không rút lại được</strong>. Cần chặn một phiếu đã duyệt thì bảo người đặt <strong>hủy phiếu</strong>.</li>
<li>Người đặt <strong>vẫn kéo thả đổi giờ được</strong> sau khi bạn đã duyệt, và <strong>không phải duyệt lại</strong> — {ref(KEO_THA, "xem bài Kéo thả")}. Người dự sẽ nhận thông báo đổi giờ.</li>
</ul>

<h2>Hủy phiếu</h2>
<p>Người đặt bấm <strong>«Hủy phiếu»</strong> ở màn chi tiết, kể cả với phiếu đã duyệt. Chi tiết ở {ref(THEO_DOI, "bài Theo dõi, sửa và hủy phiếu")}.</p>

<h2>Không thấy phiếu mình đang tìm?</h2>
<p>Phạm vi dữ liệu — hệ báo «Không tìm thấy» chứ không nói «bạn không có quyền», và điều đó là cố ý. Xem {ref(QUYEN, "bài Phân quyền và luồng duyệt")}.</p>""",
        },
        {
            "title": BAO_LOI,
            "icon": "help",
            "summary": "Tra nguyên văn câu chặn khi đặt phòng, hiểu nó nói gì và làm gì tiếp",
            "content": f"""<h2>Xử lý câu báo lỗi khi đặt phòng</h2>
<p>Mỗi câu dưới đây nói đúng một việc — đọc rồi sửa, <strong>bấm lại lần nữa không giúp được gì</strong>.</p>

<h2>Lúc gửi duyệt hoặc kéo thả</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Phòng họp 301» đã có phiếu PH012 giữ từ 09:00 20/09 đến 10:30 20/09 (đã duyệt). Chọn phòng khác hoặc dời giờ.»</em></td><td>Trùng giờ. Câu báo nói rõ <strong>ai giữ, tới mấy giờ, đã duyệt hay đang chờ</strong>.</td><td>Ba đường: xin lại phòng của người kia · dời giờ · chọn phòng khác. Nhớ là <strong>hai ca liền nhau không tính là trùng</strong>.</td></tr>
<tr><td><em>«Phòng họp 301» chứa được 8 người, phiếu này ghi 30 người. Chọn phòng lớn hơn hoặc sửa lại số người.»</em></td><td>Vượt sức chứa. Kiểm ngay lúc lưu.</td><td>Chọn phòng lớn hơn, hoặc sửa lại con số nếu bạn gõ nhầm.</td></tr>
<tr><td><em>«Một lượt đặt tối đa 24 giờ. Kiểm tra lại ngày — thường là chọn nhầm sang ngày hôm sau.»</em></td><td>Khoảng giờ dài bất thường.</td><td>Xem lại <strong>ngày</strong> ở ô Kết thúc. Cần giữ phòng nhiều ngày thì đặt mỗi ngày một phiếu.</td></tr>
<tr><td><em>«Giờ kết thúc» phải sau «Giờ bắt đầu»</em></td><td>Nhập ngược.</td><td>Đổi lại hai ô.</td></tr>
<tr><td><em>«Thiếu «Nội dung cuộc họp» — nhập đủ trước khi gửi duyệt.»</em></td><td>Ô bắt buộc còn trống.</td><td>Điền rồi <strong>Lưu nháp</strong>, sau đó gửi duyệt lại.</td></tr>
<tr><td><em>«Phòng họp không tồn tại hoặc đã ngừng dùng»</em></td><td>Phòng vừa bị quản trị bỏ tick «Đang dùng».</td><td>Chọn phòng khác. Phiếu cũ của phòng đó vẫn đọc được bình thường.</td></tr>
</tbody>
</table>

<h2>Lúc sửa hoặc dời phiếu</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Phiếu đã gửi duyệt nên không sửa được. Hủy phiếu rồi đặt lại nếu cần đổi.»</em></td><td>Nội dung, người mời, số người dự đã khóa.</td><td>Chỉ đổi <strong>giờ hoặc phòng</strong> thì dùng {ref(KEO_THA, "kéo thả trên lịch")} — không bị chặn. Đổi thứ khác thì hủy rồi đặt lại.</td></tr>
<tr><td><em>«Phiếu đã hủy hoặc bị từ chối thì không dời được. Muốn họp lại thì lập phiếu mới.»</em></td><td>Phiếu đã nhả phòng, không còn giữ chỗ nào.</td><td>Lập phiếu mới.</td></tr>
<tr><td><em>«Phiếu này đã gửi duyệt rồi»</em></td><td>Bấm «Gửi duyệt» hai lần.</td><td>Không phải lỗi. Tải lại trang là thấy trạng thái <em>Chờ duyệt</em>.</td></tr>
<tr><td>Hệ trả lỗi khi dời giờ, kèm chữ về <strong>múi giờ</strong></td><td>Giờ gửi lên phải là <strong>giờ địa phương, không kèm múi giờ</strong>. Cả hệ lưu giờ trần theo giờ Việt Nam.</td><td>Người dùng thường không gặp — gặp thì báo quản trị, đừng đoán giờ rồi nhập lại.</td></tr>
</tbody>
</table>

<h2>Lỗi về quyền và tài khoản</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Chưa xác định được người đặt — tài khoản này chưa gắn hồ sơ nhân sự.»</em></td><td>Tài khoản chưa nối với hồ sơ nhân sự nào.</td><td>Báo phòng Nhân sự gắn hồ sơ. Không tự sửa được.</td></tr>
<tr><td>Không thấy menu <strong>Đặt phòng họp</strong></td><td>Phân quyền — hai khóa của phân hệ này là khóa mới, vai trò cũ không tự có.</td><td>Xin quản trị tick thêm, xem {ref(QUYEN, "bài Phân quyền")}.</td></tr>
<tr><td>Thấy lịch nhưng <strong>không kéo thả được</strong></td><td>Chỉ có quyền đọc.</td><td>Xin thêm quyền ghi trên khóa <code>room_booking</code>.</td></tr>
<tr><td>Vào được lịch nhưng <strong>không thấy tab Danh mục phòng</strong></td><td>Thiếu khóa <code>meeting_room</code> — đó là khóa riêng.</td><td>Bình thường: khai phòng là việc của quản trị, không phải của người đặt.</td></tr>
<tr><td>Hệ báo <em>«Không tìm thấy»</em> khi mở một phiếu</td><td><strong>Phạm vi dữ liệu</strong>, không phải phiếu bị xóa.</td><td>Xin mở rộng phạm vi, hoặc nhờ người trong phạm vi xử lý.</td></tr>
</tbody>
</table>

<h2>Không phải lỗi, nhưng hay bị tưởng là lỗi</h2>
<ul>
<li><strong>Người được mời chưa nhận thông báo</strong> — thư chỉ gửi <strong>sau khi phiếu được duyệt</strong>.</li>
<li><strong>Phiếu nháp không hiện trên lịch</strong> — đúng như vậy, nháp không giữ phòng.</li>
<li><strong>Lịch không có chế độ tuần</strong> — cố ý; nhìn xa hơn một ngày thì dùng tab <em>Phiếu đặt phòng</em>.</li>
<li><strong>Kéo khối sang ngày khác không được</strong> — lưới chỉ vẽ một ngày.</li>
</ul>""",
        },
        {
            "title": DANH_MUC,
            "icon": "settings",
            "summary": "Khai phòng, sức chứa, thiết bị, phòng dùng chung, và cách dẹp một phòng",
            "content": f"""<h2>Dành cho quản trị — Danh mục phòng</h2>
<p>Tab <strong>Danh mục phòng</strong> (khóa quyền <code>meeting_room</code>). Mỗi dòng là một phòng họp có thật trong toà nhà.</p>

<h2>Các ô cần khai</h2>
<table>
<thead><tr><th>Ô</th><th>Cần biết</th></tr></thead>
<tbody>
<tr><td><strong>Mã phòng</strong></td><td>⚠️ <strong>Đặt xong thì KHÔNG đổi được.</strong> Mã đi vào mọi phiếu đã đặt và vào cách người ta gọi nhau («họp ở P301»). Nghĩ kỹ trước khi lưu.</td></tr>
<tr><td><strong>Tên phòng</strong></td><td>Tên người dùng đọc. Ví dụ «Phòng họp 301».</td></tr>
<tr><td><strong>Vị trí</strong></td><td>Ví dụ «Tầng 3, toà A». Hiện ngay dưới tên trên lưới lịch, và người dùng <strong>lọc bằng nó</strong>.</td></tr>
<tr><td><strong>Sức chứa (người)</strong></td><td>Hệ dùng để chặn khi số người dự vượt quá. ⚠️ Để <strong>0</strong> nghĩa là <strong>CHƯA KHAI</strong>, không phải «không chứa được ai» — nên sẽ không chặn ai cả.</td></tr>
<tr><td><strong>Thiết bị sẵn có</strong></td><td>Chữ mô tả tự do: máy chiếu, TV 55 inch, bảng trắng, thiết bị họp trực tuyến. Người đặt <strong>tìm phòng bằng ô này</strong>, nên viết đủ từ khóa họ hay gõ.</td></tr>
<tr><td><strong>Pháp nhân riêng</strong></td><td>⚠️ <strong>Để trống = phòng DÙNG CHUNG cho mọi pháp nhân</strong> (toà nhà chung) — đây là mặc định và là ca phổ biến nhất. Khai một pháp nhân cụ thể thì chỉ pháp nhân đó thấy.</td></tr>
<tr><td><strong>Thứ tự hiển thị</strong></td><td>Quyết định thứ tự hàng trên lưới lịch. Phòng hay dùng để lên đầu, người ta đỡ phải cuộn.</td></tr>
<tr><td><strong>Đang dùng</strong></td><td>Tắt là phòng biến khỏi ô chọn. Xem mục dưới.</td></tr>
<tr><td><strong>Ghi chú</strong></td><td>Nội bộ, không hiện cho người đặt.</td></tr>
</tbody>
</table>

<h2>Dẹp một phòng: bỏ tick, đừng xóa</h2>
<ul>
<li><strong>Bỏ tick «Đang dùng»</strong> — phòng biến khỏi ô chọn, không ai đặt được nữa, nhưng <strong>phiếu cũ vẫn đọc được</strong>. Dùng cách này khi phòng sửa chữa, đổi công năng, hoặc trả mặt bằng.</li>
<li><strong>Xóa</strong> — hệ chặn nếu phòng đang có phiếu. Xóa được là để lại những cuộc họp không biết ở đâu.</li>
</ul>
<p>Bộ lọc trạng thái ở đầu bảng có sẵn hai lựa chọn <em>Đang dùng</em> và <em>Ngừng / Ẩn</em> để rà lại.</p>

<h2>Xem lịch riêng của một phòng</h2>
<p>Mở một phòng trong danh mục, tab <strong>«Lịch đặt của phòng»</strong> liệt kê các lượt đặt sắp tới và đã qua của riêng phòng đó. Dùng khi cần trả lời <em>«phòng 301 tuần này ai dùng»</em> hoặc trước khi tắt một phòng.</p>

<h2>Ba lỗi khai phòng hay gặp</h2>
<ol>
<li><strong>Quên khai sức chứa</strong> — để 0 thì chốt chặn theo sức chứa <em>không chạy</em>, và người ta nhét 30 người vào phòng 8 chỗ mà hệ không nói gì.</li>
<li><strong>Khai pháp nhân cho phòng dùng chung</strong> — làm phòng biến mất khỏi danh sách của các pháp nhân khác, mà không có câu báo nào. Toà nhà chung thì <strong>để trống</strong>.</li>
<li><strong>Thiết bị ghi quá sơ sài</strong> — người đặt tìm «may chieu» không ra phòng nào rồi đi hỏi hành chính.</li>
</ol>

<h2>Nạp phòng mẫu (chỉ môi trường thử)</h2>
<p>Quản trị hệ thống có sẵn một bộ 4 phòng mẫu để thử nghiệm, chạy lại được. Bộ này <strong>cố ý không</strong> tự nạp khi khởi động — danh mục phòng là thứ mỗi công ty tự khai theo toà nhà của mình, nạp tự động là áp phòng tưởng tượng lên dữ liệu thật.</p>

<p>Phân quyền và luồng duyệt: {ref(QUYEN, "xem bài riêng")}.</p>""",
        },
        {
            "title": QUYEN,
            "icon": "key-round",
            "summary": "Hai khóa quyền, phạm vi dữ liệu, khai luồng duyệt và thứ tự dựng phân hệ",
            "content": f"""<h2>Quản trị — Phân quyền và luồng duyệt đặt phòng</h2>

<h2>Hai khóa quyền — đừng gộp</h2>
<table>
<thead><tr><th>Khóa</th><th>Mở gì</th><th>Cho ai</th></tr></thead>
<tbody>
<tr><td><code>room_booking</code></td><td>Lịch đặt phòng · Phiếu đặt phòng (đặt, sửa, kéo thả, duyệt, hủy)</td><td>Mọi nhân sự</td></tr>
<tr><td><code>meeting_room</code></td><td>Danh mục phòng (khai phòng, sức chứa, thiết bị)</td><td>Quản trị / hành chính</td></tr>
</tbody>
</table>
<p><strong>Cho quyền khai danh mục KHÁC cho quyền đặt phòng.</strong> Người đặt phòng không cần và không nên sửa được danh mục — đổi sức chứa một phòng là gỡ chốt chặn của mọi phiếu sau đó.</p>

<h2>Hành động trong <code>room_booking</code></h2>
<table>
<thead><tr><th>Hành động</th><th>Cho phép</th></tr></thead>
<tbody>
<tr><td><strong>đọc</strong></td><td>Xem lịch và phiếu trong phạm vi. <strong>Không kéo thả được.</strong></td></tr>
<tr><td><strong>tạo</strong></td><td>Lập phiếu mới.</td></tr>
<tr><td><strong>ghi</strong></td><td>Sửa phiếu nháp và <strong>kéo thả đổi giờ / đổi phòng</strong>.</td></tr>
<tr><td><strong>duyệt</strong></td><td>Ký phiếu; nơi chưa khai luồng thì duyệt thẳng.</td></tr>
<tr><td><strong>hủy</strong></td><td>Hủy phiếu.</td></tr>
</tbody>
</table>
<p>⚠️ Thiếu quyền <strong>ghi</strong> thì kéo thả <strong>tắt hẳn</strong>, khối vẫn bấm mở phiếu như cũ. Cố ý làm vậy: không gác thì người chỉ được xem vẫn kéo được, thấy khối nhảy sang chỗ mới rồi bật về — họ sẽ tưởng hệ thống lỗi chứ không nghĩ là mình không có quyền.</p>

<h2>«Không thấy menu Đặt phòng họp»</h2>
<p>⚠️ Gần như <strong>luôn</strong> là phân quyền. Hai khóa trên là khóa <strong>mới</strong>, mà seed cố ý <strong>không ghi đè</strong> phân quyền đã chỉnh tay trên hệ đang chạy — nên vai trò cũ <strong>không tự có</strong> chúng.</p>
<p>Cách xử lý: vào <strong>Nhân sự ▸ Phân quyền tài khoản</strong>, tick khóa cho đúng vai trò.</p>

<h2>Phạm vi dữ liệu</h2>
<p>Quyền mở màn, <strong>phạm vi</strong> quyết định thấy được phiếu nào.</p>
<ul>
<li><code>room_booking</code> khai cả <em>người lập</em> phiếu lẫn <em>người đặt</em> vào phạm vi «của mình» — thư ký đặt hộ sếp là việc có thật, và cả hai đều phải thấy phiếu.</li>
<li>Người duyệt <strong>không cần</strong> phạm vi rộng: đang có việc trên tờ phiếu thì đọc được nó, ký xong quyền đó đóng lại.</li>
<li>Phạm vi hẹp quá thì <strong>lưới lịch cũng thưa theo</strong> — người dùng nhìn thấy phòng «trống» trong khi thật ra đã có người giữ, rồi gửi duyệt lên bị chặn mà không hiểu vì sao. Với phân hệ này nên để phạm vi <strong>rộng ở mức đọc</strong>: lịch phòng họp không phải bí mật, còn nội dung cuộc họp thì vẫn nằm trong phiếu.</li>
</ul>

<h2>Luồng duyệt</h2>
<p>Khai ở phân hệ <strong>Phê duyệt</strong> cho loại chứng từ <em>Phiếu đặt phòng họp</em>. Chạy trên cùng bộ máy duyệt với Nghỉ phép và Văn thư.</p>
<ul>
<li><strong>Chưa khai luồng nào thì phiếu vẫn gửi duyệt được</strong>, và người có quyền duyệt bấm <strong>«Duyệt phiếu»</strong> thẳng. Không có đường lùi này thì cài mới xong là không ai đặt nổi phòng.</li>
<li>Phiếu <em>đang</em> chạy trong luồng thì đường duyệt thẳng <strong>bị chặn</strong>.</li>
<li>Cân nhắc kỹ trước khi khai luồng nhiều chặng: <strong>phòng bị giữ suốt thời gian chờ ký</strong>, mà đặt phòng là việc gấp. Một chặng (hành chính) là đủ cho hầu hết công ty.</li>
</ul>
<p>Cách ký và ý nghĩa ba nút: {ref(DUYET, "bài Duyệt phiếu đặt phòng")}.</p>

<h2>Thứ tự dựng phân hệ</h2>
<ol>
<li>Khai <strong>Danh mục phòng</strong> — đủ mã, tên, vị trí, <strong>sức chứa</strong>, thiết bị. Xem {ref(DANH_MUC, "bài Danh mục phòng")}.</li>
<li>Để trống <strong>Pháp nhân riêng</strong> với phòng dùng chung.</li>
<li>Đặt <strong>Thứ tự hiển thị</strong> cho phòng hay dùng lên đầu lưới.</li>
<li>Tick <strong>hai khóa quyền</strong> cho các vai trò; nhớ quyền <strong>ghi</strong> nếu muốn người dùng kéo thả được.</li>
<li>Khai <strong>luồng duyệt</strong> (hoặc để trống và dùng duyệt thẳng).</li>
<li>Chỉ người dùng bài {ref(XEM_LICH, "Xem lịch phòng và đặt nhanh")} — đó là màn họ dùng hằng ngày.</li>
</ol>""",
        },
    ],
}


def collect_descendants(db, root_id):
    """Trả [(id, độ sâu)] của cả cây, gồm chính gốc."""
    found = [(root_id, 0)]
    frontier = [(root_id, 0)]
    while frontier:
        nid, depth = frontier.pop()
        for (cid,) in db.query(HelpArticle.id).filter(HelpArticle.parent_id == nid).all():
            found.append((cid, depth + 1))
            frontier.append((cid, depth + 1))
    return found


def delete_subtree(db, root_id):
    nodes = collect_descendants(db, root_id)
    #  Xóa RAW theo thứ tự sâu-trước: FK tự tham chiếu parent_id KHÔNG cascade.
    for nid, _ in sorted(nodes, key=lambda x: x[1], reverse=True):
        db.execute(text("DELETE FROM tab_help_home_item WHERE article_id = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article WHERE id = :id"), {"id": nid})
    db.flush()
    return len(nodes)


def insert_node(db, node, parent_id, order):
    art = HelpArticle(
        parent_id=parent_id,
        title=node["title"],
        content=node.get("content", ""),
        summary=node.get("summary"),
        icon=node.get("icon"),
        sort_order=order,
    )
    db.add(art)
    db.flush()
    count = 1
    for i, child in enumerate(node.get("children", [])):
        child_count, _ = insert_node(db, child, art.id, i)
        count += child_count
    return count, art.id


def attach_home_card(db, article_id):
    """Gắn thẻ phân hệ vào khung "Các Phân hệ" trang chủ nếu chưa có."""
    section = db.query(HelpHomeSection).filter(HelpHomeSection.key == "categories").first()
    if section is None:
        print("Không thấy khung categories — bỏ qua gắn thẻ trang chủ.")
        return
    existing = (
        db.query(HelpHomeItem)
        .filter(HelpHomeItem.section_id == section.id, HelpHomeItem.article_id == article_id)
        .first()
    )
    if existing is not None:
        return
    max_order = (
        db.query(HelpHomeItem.sort_order)
        .filter(HelpHomeItem.section_id == section.id)
        .order_by(HelpHomeItem.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0
    db.add(HelpHomeItem(section_id=section.id, article_id=article_id, sort_order=next_order))
    print(f"Đã gắn thẻ phân hệ vào trang chủ (sort_order={next_order}).")


def main():
    db = SessionLocal()
    try:
        old = (
            db.query(HelpArticle)
            .filter(HelpArticle.title == ROOT_TITLE, HelpArticle.parent_id.is_(None))
            .first()
        )
        if old is not None:
            removed = delete_subtree(db, old.id)
            print(f"Đã xóa cây cũ: {removed} bài (gốc id={old.id}).")

        max_order = (
            db.query(HelpArticle.sort_order)
            .filter(HelpArticle.parent_id.is_(None))
            .order_by(HelpArticle.sort_order.desc())
            .first()
        )
        next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

        total, root_id = insert_node(db, TREE, None, next_order)
        attach_home_card(db, root_id)
        db.commit()
        print(f"Đã dựng cây Đặt phòng họp: {total} bài (gốc id={root_id}, sort_order={next_order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
