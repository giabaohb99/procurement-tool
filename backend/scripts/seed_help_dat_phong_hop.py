# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ ĐẶT PHÒNG HỌP.

Dựng cây bài viết: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ") -> 5 bài
chia theo TÁC VỤ (xem lịch & đặt nhanh / lập phiếu & mời / kéo thả đổi lịch /
duyệt phiếu / danh mục phòng cho quản trị).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_dat_phong_hop.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/18-dat-phong-hop.md` và
gói tri thức trợ lý `app/modules/assistant/packs/50-dat-phong-hop.md`. Ba nơi
lệch nhau thì người dùng đọc một đằng, trợ lý trả lời một nẻo.
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
DUYET = "Duyệt phiếu đặt phòng"
DANH_MUC = "Dành cho quản trị — Danh mục phòng"


TREE = {
    "title": ROOT_TITLE,
    "icon": "building",
    "summary": "Xem phòng nào trống, đặt phòng, kéo thả đổi lịch, duyệt phiếu",
    "content": f"""<h2>Đặt phòng họp là gì?</h2>
<p>Phân hệ để <strong>giữ chỗ phòng họp</strong>: xem phòng nào đang trống, lập phiếu đặt, gửi duyệt và mời người tham dự. Vào bằng menu <strong>Nhân sự ▸ Đặt phòng họp</strong>.</p>
<h3>Ba khu vực, chuyển bằng thanh tab</h3>
<table>
<thead><tr><th>Tab</th><th>Dùng để</th></tr></thead>
<tbody>
<tr><td><strong>Lịch đặt phòng</strong></td><td>Xem cả ngày một lượt, bấm ô trống để đặt, kéo thả đổi lịch.</td></tr>
<tr><td><strong>Phiếu đặt phòng</strong></td><td>Danh sách phiếu: phiếu của bạn, phiếu chờ bạn duyệt, phiếu bạn đã duyệt.</td></tr>
<tr><td><strong>Danh mục phòng</strong></td><td>Khai phòng, sức chứa, thiết bị — dành cho quản trị.</td></tr>
</tbody>
</table>
<h3>Điều quan trọng nhất phải nhớ</h3>
<p>⚠️ <strong>Phòng bị giữ ngay khi bạn bấm «Gửi duyệt», không đợi ai duyệt xong.</strong> Nghĩa là nộp phiếu là yên tâm — không ai chen ngang được. Ngược lại, <strong>phiếu để ở «Nháp» thì KHÔNG giữ chỗ gì cả</strong>, người khác vẫn đặt mất phòng như thường.</p>
<h3>Đọc theo việc bạn cần làm</h3>
<p>{ref(XEM_LICH, "Xem lịch & đặt nhanh")} · {ref(LAP_PHIEU, "lập phiếu & mời người dự")} · {ref(KEO_THA, "kéo thả đổi lịch")} · {ref(DUYET, "duyệt phiếu")} · {ref(DANH_MUC, "danh mục phòng")}.</p>""",
    "children": [
        {
            "title": XEM_LICH,
            "icon": "calendar",
            "summary": "Đọc lưới lịch, lọc phòng, bấm ô trống để đặt ngay",
            "content": f"""<h2>Xem lịch phòng và đặt nhanh</h2>
<p>Tab <strong>Lịch đặt phòng</strong> trả lời đúng một câu: <em>«bây giờ phòng nào còn trống»</em>.</p>
<h3>Đọc lưới</h3>
<ul>
<li><strong>Mỗi phòng một hàng</strong>, giờ chạy ngang từ <strong>7:00 đến 20:00</strong>. Tên phòng dính bên trái khi bạn cuộn ngang.</li>
<li>Mỗi khối màu là một lượt giữ phòng: <strong>xanh lá = đã duyệt</strong>, <strong>vàng cam = chờ duyệt</strong>. Chú giải màu nằm ngay góc trên bên trái.</li>
<li>Phần <strong>tô xám mờ</strong> là ngoài giờ hành chính và giờ nghỉ trưa.</li>
<li><strong>Vạch đỏ dọc</strong> là mốc «bây giờ», chỉ hiện khi bạn đang xem hôm nay.</li>
<li>Rê chuột lên một khối để xem đầy đủ mã phiếu, nội dung, giờ và người đặt. Bấm vào khối để mở phiếu.</li>
</ul>
<h3>Đổi ngày, lọc phòng</h3>
<ul>
<li>Bấm <strong>tên ngày</strong> ở thanh trên để mở lịch chọn ngày; hai nút mũi tên và nút <strong>Hôm nay</strong> nằm cạnh đó.</li>
<li>Công ty nhiều phòng thì có ô <strong>lọc theo phòng, tầng, thiết bị</strong>. Gõ <strong>không dấu vẫn tìm ra</strong> — «tang 3» ra «Tầng 3».</li>
<li>Đường dẫn có mang theo ngày, nên <strong>copy link gửi cho người khác</strong> là họ mở đúng ngày bạn đang xem.</li>
</ul>
<h3>Đặt nhanh từ ô trống</h3>
<p>Rê chuột vào một ô trống, nhãn <strong>«+ giờ»</strong> hiện lên — bấm là mở form đặt phòng <strong>đã điền sẵn đúng phòng và đúng giờ</strong> đó. Ô chia <strong>nửa tiếng</strong> một, vì họp 30 phút là chuyện thường.</p>
<h3>Lịch chỉ xem MỘT ngày</h3>
<p>Không có chế độ tuần: một ngày làm việc đã chiếm gần trọn bề ngang màn hình, nhân bảy lần thì mỗi cuộc họp còn vài pixel, không đọc nổi. Nhìn xa hơn một ngày thì sang tab <strong>Phiếu đặt phòng</strong> rồi lọc theo phòng và khoảng thời gian.</p>
<p>⚠️ <strong>Đừng tin lưới đã cũ.</strong> Phòng có thể vừa bị người khác giữ mất trong lúc bạn đang nhìn — chốt chặn thật nằm ở bước gửi duyệt. Xem tiếp {ref(LAP_PHIEU, "bài Lập phiếu đặt phòng")}.</p>""",
        },
        {
            "title": LAP_PHIEU,
            "icon": "file-text",
            "summary": "Điền phiếu, chọn phòng còn trống, mời người dự, gửi duyệt",
            "content": f"""<h2>Lập phiếu đặt phòng và mời người dự</h2>
<h3>Mở phiếu mới</h3>
<p>Bấm <strong>Đặt phòng</strong> ở góc trên bên phải — nút này có ở cả tab Lịch lẫn tab Phiếu. Hoặc {ref(XEM_LICH, "bấm thẳng vào ô trống trên lịch")} để form tự điền sẵn phòng và giờ.</p>
<h3>Điền phiếu</h3>
<ul>
<li><strong>Nội dung cuộc họp</strong> — bắt buộc khi gửi duyệt. Người duyệt mở phiếu ra mà không có dòng này thì họ duyệt cái gì.</li>
<li><strong>Từ lúc / Đến lúc</strong>. Tối đa <strong>24 giờ một lượt</strong> — vượt trần gần như luôn là chọn nhầm ngày.</li>
<li><strong>Phòng</strong> — bấm nút chọn phòng, hộp thoại <strong>chỉ bày phòng ĐANG TRỐNG</strong> trong khung giờ bạn vừa chọn. Muốn xem cả phòng đang bận (để đi xin lại) thì bật công tắc trong hộp thoại. Ô tìm ở đây cũng <strong>bỏ dấu vẫn khớp</strong>.</li>
<li><strong>Số người dự</strong> — hệ so với sức chứa của phòng. Nhét 30 người vào phòng 8 chỗ là bị chặn. Phòng chưa khai sức chứa thì không chặn.</li>
<li><strong>Mục đích</strong> — mô tả thêm, không bắt buộc.</li>
</ul>
<h3>Mời người tham dự</h3>
<ul>
<li>Thêm từng người vào danh sách người dự. <strong>Mời trùng một người hai lần chỉ ghi một dòng</strong>, và bạn không tự mời chính mình.</li>
<li>⚠️ <strong>Người được mời chỉ nhận thông báo SAU khi phiếu được duyệt.</strong> Phiếu còn chờ duyệt thì chưa ai được báo — cuộc họp chưa chắc diễn ra, mà thư đã gửi thì không rút lại được. Cần báo gấp thì tự nhắn cho họ.</li>
</ul>
<h3>Đặt hộ người khác</h3>
<p>Thư ký đặt hộ sếp thì điền người đặt vào ô riêng. <strong>Phòng ban và pháp nhân của phiếu lấy theo người được đặt hộ</strong>, không lấy theo người ngồi gõ.</p>
<h3>Lưu nháp hay gửi duyệt?</h3>
<table>
<thead><tr><th></th><th>Lưu nháp</th><th>Gửi duyệt</th></tr></thead>
<tbody>
<tr><td>Giữ phòng?</td><td><strong>KHÔNG</strong> — người khác vẫn đặt mất</td><td><strong>CÓ</strong>, ngay lập tức</td></tr>
<tr><td>Kiểm trùng?</td><td>Không kiểm</td><td>Kiểm, chặn nếu trùng</td></tr>
<tr><td>Sửa được?</td><td>Sửa thoải mái</td><td>Khóa (trừ giờ và phòng, xem {ref(KEO_THA, "kéo thả")})</td></tr>
</tbody>
</table>
<h3>Bị chặn vì trùng giờ thì làm gì</h3>
<p>Câu báo lỗi <strong>nói rõ phiếu nào đang giữ, giữ từ mấy giờ tới mấy giờ, đã duyệt hay đang chờ duyệt</strong>. Đọc câu đó rồi đi xin lại phòng của người kia, hoặc dời giờ, hoặc chọn phòng khác — <strong>bấm lại lần nữa không giúp được gì</strong>.</p>
<p>Lưu ý: <strong>hai ca liền nhau KHÔNG tính là trùng</strong>. Họp 9–10h và họp 10–11h đặt được cả hai.</p>""",
        },
        {
            "title": KEO_THA,
            "icon": "lightbulb",
            "summary": "Kéo khối trên lịch để dời giờ, đổi phòng, đổi độ dài",
            "content": f"""<h2>Đổi giờ và đổi phòng bằng kéo thả</h2>
<p>Ngay trên {ref(XEM_LICH, "lưới Lịch đặt phòng")}, bạn <strong>kéo khối phiếu</strong> để dời lịch mà không cần mở phiếu ra sửa.</p>
<table>
<thead><tr><th>Thao tác</th><th>Đổi gì</th></tr></thead>
<tbody>
<tr><td>Kéo ngang khối</td><td>Giờ bắt đầu và kết thúc, giữ nguyên độ dài</td></tr>
<tr><td>Kéo dọc sang hàng khác</td><td><strong>Đổi phòng</strong></td></tr>
<tr><td>Kéo mép trái / mép phải</td><td>Độ dài cuộc họp (ngắn nhất 15 phút)</td></tr>
<tr><td>Bấm (không kéo)</td><td>Mở trang chi tiết phiếu</td></tr>
</tbody>
</table>
<h3>Trong lúc kéo</h3>
<ul>
<li>Một <strong>khung nét đứt</strong> hiện ở chỗ sắp thả, kèm <strong>giờ mới</strong>. Khung đó nằm ở <strong>đúng hàng phòng</strong> bạn đang trỏ tới, nên kéo dọc là thấy ngay nó sẽ rơi vào phòng nào.</li>
<li>Giờ <strong>hút về mốc 15 phút</strong> — không thả được vào 9:03. Chuột không đủ chính xác, mà lịch đầy con số lẻ thì rất khó đọc.</li>
<li>Muốn bỏ giữa chừng thì kéo trả về chỗ cũ, hoặc nhả chuột ra ngoài cửa sổ.</li>
</ul>
<h3>Bốn điều đáng biết</h3>
<ul>
<li><strong>Kéo được cả phiếu «Chờ duyệt» lẫn «Đã duyệt», và trạng thái giữ nguyên</strong> — dời một phiếu đã duyệt <strong>không</strong> bắt đi duyệt lại.</li>
<li><strong>Vẫn chặn trùng y hệt.</strong> Kéo vào khung đã có người là bị chặn, khối bật về chỗ cũ và hiện câu báo nói rõ ai đang giữ.</li>
<li><strong>Phiếu đã duyệt bị dời thì người dự nhận thông báo «Đổi giờ họp».</strong> Cuộc họp bị dời mà không báo thì họ tới đúng phòng cũ vào đúng giờ cũ.</li>
<li><strong>Không kéo sang ngày khác được.</strong> Lưới vẽ một ngày, nên kéo ngang bị kẹp trong 7:00–20:00 của chính ngày đang xem. Dời sang ngày khác thì mở phiếu ra sửa.</li>
</ul>
<h3>Kéo không được?</h3>
<p>Nếu con trỏ không đổi thành hình bàn tay và khối không nhúc nhích, gần như chắc là <strong>bạn không có quyền sửa phiếu</strong> (khóa <code>room_booking</code> quyền ghi) — lúc đó kéo thả tắt hẳn, khối chỉ bấm mở phiếu. Hỏi quản trị, đừng báo lỗi hệ thống.</p>
<p>Phiếu <strong>đã hủy</strong> hoặc <strong>bị từ chối</strong> thì không dời được — chúng đã nhả phòng rồi, dời chỉ đẻ ra một cuộc họp không ai giữ chỗ cho.</p>""",
        },
        {
            "title": DUYET,
            "icon": "workflow",
            "summary": "Ba tab của màn Phiếu, ba nút, và điều gì xảy ra sau khi ký",
            "content": f"""<h2>Duyệt phiếu đặt phòng</h2>
<p>Tab <strong>Phiếu đặt phòng</strong> chia làm ba: <strong>Cần tôi duyệt</strong> (đứng đầu, tự chọn khi có việc, kèm số việc đang chờ) · <strong>Phiếu của tôi</strong> · <strong>Tôi đã duyệt</strong>.</p>
<h3>Ba nút</h3>
<table>
<thead><tr><th>Nút</th><th>Dùng khi</th><th>Hậu quả</th></tr></thead>
<tbody>
<tr><td><strong>Duyệt</strong></td><td>Đồng ý</td><td>Sang chặng sau, hoặc xong hẳn nếu là chặng cuối. Xong thì <strong>người được mời nhận thư mời họp</strong>.</td></tr>
<tr><td><strong>Trả về</strong></td><td>Thiếu thông tin, sửa là được</td><td>Người đặt <strong>sửa rồi gửi lại</strong> chính tờ phiếu đó. <strong>Phòng được nhả ra ngay</strong>.</td></tr>
<tr><td><strong>Từ chối</strong></td><td>Không cho đặt</td><td><strong>Khóa hẳn</strong>, muốn họp thì lập <strong>phiếu khác</strong>. <strong>Phòng được nhả ra ngay</strong>.</td></tr>
</tbody>
</table>
<p>⚠️ <strong>Ba kết cục không-duyệt đều NHẢ phòng</strong>: Trả về · Từ chối · Đã hủy. Nhả rồi thì ai đặt cũng được, kể cả người khác — nên nếu người đặt còn muốn phòng đó, họ phải nộp lại sớm.</p>
<h3>Vài điều đáng biết</h3>
<ul>
<li><strong>Đang có việc trên tờ phiếu thì bạn đọc được nó</strong>, kể cả khi phạm vi dữ liệu của bạn không với tới. <strong>Ký xong quyền đó đóng lại</strong> — xem lại thì vào tab <strong>Tôi đã duyệt</strong>.</li>
<li>Có việc mới, bạn nhận <strong>thông báo chuông</strong> kèm liên kết mở thẳng tờ phiếu.</li>
<li>Chỗ nào <strong>chưa khai luồng duyệt</strong> thì người có quyền duyệt bấm <strong>Duyệt</strong> thẳng trên phiếu. Phiếu đang chạy trong luồng thì đường đó bị chặn.</li>
</ul>
<h3>Hủy phiếu</h3>
<p>Người đặt bấm <strong>Hủy phiếu</strong> ở màn chi tiết. <strong>Hủy được cả phiếu đã duyệt</strong> — họp hoãn là chuyện thường, và không nhả thì phòng bị khóa suốt khung giờ đó dù chẳng ai dùng.</p>
<h3>Không thấy phiếu mình đang tìm?</h3>
<p>Bạn chỉ đọc được phiếu <strong>trong phạm vi dữ liệu</strong> của mình. Phiếu ngoài phạm vi thì hệ báo «Không tìm thấy» — không có nghĩa là phiếu đó không tồn tại, chỉ là bạn không được xem. Nội dung cuộc họp hay chứa chuyện nhân sự nên hệ cố ý chặt tay.</p>""",
        },
        {
            "title": DANH_MUC,
            "icon": "settings",
            "summary": "Khai phòng, sức chứa, thiết bị, phòng dùng chung, phân quyền",
            "content": f"""<h2>Dành cho quản trị — Danh mục phòng</h2>
<p>Tab <strong>Danh mục phòng</strong>. Mỗi dòng là một phòng họp có thật trong toà nhà.</p>
<h3>Các ô cần khai</h3>
<ul>
<li><strong>Mã phòng</strong> — ⚠️ <strong>đặt xong thì không đổi được.</strong> Mã đi vào mọi phiếu đã đặt và vào cách người ta gọi nhau («họp ở P301»).</li>
<li><strong>Tên phòng</strong> và <strong>vị trí</strong> (vd «Tầng 3») — vị trí hiện ngay dưới tên trên lưới lịch, và người dùng lọc bằng nó.</li>
<li><strong>Sức chứa</strong> — hệ dùng để chặn khi số người dự vượt quá. Để <strong>0</strong> nghĩa là <strong>chưa khai</strong>, không phải «không chứa được ai», nên sẽ không chặn ai cả.</li>
<li><strong>Thiết bị</strong> — chữ mô tả tự do (máy chiếu, TV 55 inch, bảng trắng). Người đặt tìm phòng bằng ô này.</li>
<li><strong>Pháp nhân</strong> — ⚠️ <strong>để trống nghĩa là phòng DÙNG CHUNG cho mọi pháp nhân</strong>. Khai một pháp nhân cụ thể thì chỉ pháp nhân đó thấy.</li>
<li><strong>Thứ tự</strong> — quyết định thứ tự hàng trên lưới lịch. Phòng hay dùng nên để lên đầu.</li>
</ul>
<h3>Dẹp một phòng: bỏ tick, đừng xóa</h3>
<p><strong>Bỏ tick «Đang dùng»</strong> thì phòng biến khỏi ô chọn và không ai đặt được nữa, nhưng <strong>phiếu cũ vẫn đọc được</strong>. Còn <strong>xóa</strong> thì hệ chặn nếu phòng đang có phiếu — xóa được là để lại những cuộc họp không biết ở đâu.</p>
<h3>Xem lịch riêng của một phòng</h3>
<p>Mở một phòng trong danh mục, tab <strong>Lịch đặt của phòng</strong> liệt kê các lượt đặt sắp tới và đã qua của riêng phòng đó.</p>
<h3>Hai khóa quyền — đừng gộp</h3>
<table>
<thead><tr><th>Khóa</th><th>Mở gì</th></tr></thead>
<tbody>
<tr><td><code>room_booking</code></td><td>Lịch đặt phòng · Phiếu đặt phòng (đặt, sửa, kéo thả, duyệt, hủy)</td></tr>
<tr><td><code>meeting_room</code></td><td>Danh mục phòng (khai phòng, sức chứa, thiết bị)</td></tr>
</tbody>
</table>
<p>⚠️ <strong>Người dùng báo «không thấy menu Đặt phòng họp» thì gần như chắc là do phân quyền.</strong> Hai khóa này mới thêm nên các vai trò cũ <strong>không tự có</strong> — vào <strong>Nhân sự ▸ Phân quyền tài khoản</strong> tick thêm.</p>
<p>Người chỉ có quyền <strong>đọc</strong> vẫn xem được lịch nhưng <strong>không kéo thả được</strong> — xem {ref(KEO_THA, "bài Kéo thả")}.</p>
<h3>Luồng duyệt</h3>
<p>Khai ở phân hệ <strong>Phê duyệt</strong> cho loại chứng từ «Phiếu đặt phòng họp». <strong>Chưa khai luồng nào thì phiếu vẫn gửi duyệt được</strong> và người có quyền duyệt bấm <strong>Duyệt</strong> thẳng — không có đường lùi này thì cài mới xong là không ai đặt nổi phòng.</p>""",
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
