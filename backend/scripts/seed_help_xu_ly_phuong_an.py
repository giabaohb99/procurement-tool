# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp: LUỒNG PHƯƠNG ÁN trên yêu cầu mua hàng (bao-CR-449).

Đóng nợ N-20 của bao-CR-310: kho hướng dẫn đang chạy có 12 bài về mua hàng, không bài nào
nhắc tới phương án. Người dùng mới vì thế không biết nút *Chốt hoàn thành xử lý* của thu mua
khác nút chọn phương án của người yêu cầu chỗ nào.

Script dựng HAI bài, mỗi bài một nhóm có sẵn (không đẻ nhóm mới):

1. «Xử lý phương án trên yêu cầu mua hàng» — nhóm «Dành cho Nhân viên Mua hàng».
   Bài chính, kể đủ đường đi: gắn phương án, phương án 0, chốt hoàn thành xử lý, chốt rỗng,
   sửa giá / NCC sau chốt, áp 1 NCC cho nhiều dòng, tạo đơn, in phiếu.
2. «Chọn phương án trên yêu cầu mua hàng» — nhóm «Dành cho Người yêu cầu».
   Bài ngắn, chỉ nói phần người yêu cầu bấm, và cố ý KHÔNG nhắc tên nhà cung cấp vì màn chọn
   của họ che cụm NCC (H.3.8).

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_xu_ly_phuong_an.py

Idempotent: đã có bài cùng tiêu đề dưới đúng nhóm thì xóa bài đó (kèm bài con, nếu có) rồi
chèn lại ở nguyên chỗ cũ. Thiếu nhóm cha thì DỪNG, không tự tạo bài gốc.

Nội dung phải KHỚP với `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md` mục H (H.1 → H.12) và
mục I, cùng hành vi thật của `purchase-request-process-card.tsx` +
`purchase-request-choose-card.tsx`. Không nêu mã phiếu mẫu của môi trường thử.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

STAFF_PARENT_TITLE = "Dành cho Nhân viên Mua hàng"
REQUESTER_PARENT_TITLE = "Dành cho Người yêu cầu"

STAFF_ARTICLE_TITLE = "Xử lý phương án trên yêu cầu mua hàng"
REQUESTER_ARTICLE_TITLE = "Chọn phương án trên yêu cầu mua hàng"


# --------------------------------------------------------------------------- #
#  LIÊN KẾT NỘI BỘ — slug sinh y hệt slugify() của help-center (help-slug.tsx).
#  Tiêu đề đích phải DUY NHẤT trong tab_help_article, không thì portal gắn hậu tố "-{id}".
# --------------------------------------------------------------------------- #
def slugify(value: str) -> str:
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


# --------------------------------------------------------------------------- #
#  BÀI 1 — cho thu mua
# --------------------------------------------------------------------------- #
STAFF_SUMMARY = (
    "Gắn phương án (nhà cung cấp + giá) lên từng dòng của yêu cầu mua hàng, chốt hoàn thành "
    "xử lý, rồi từ phương án người yêu cầu chọn sinh thẳng đơn mua hàng"
)

STAFF_CONTENT = f"""<h2>I. Luồng phương án là gì</h2>
<p>Người yêu cầu lập phiếu mua một món đã có mã hàng, đã có giá. Thu mua tiếp nhận thì phát hiện <strong>giá vừa biến động</strong>, có khi phải đổi sang nhà cung cấp khác. Trước đây phải trả phiếu về hoặc mở một {ref("Yêu cầu báo giá", "Yêu cầu báo giá")} mới. Nay thu mua gắn thêm vài <strong>phương án</strong> ngay trên dòng hàng đó để người yêu cầu chọn lại.</p>
<p>Đây là <strong>đường thứ hai</strong>, dùng khi phiếu đã đủ mã hàng và thông tin mà chỉ vướng giá. Luồng Yêu cầu báo giá <strong>giữ nguyên</strong>, không bị thay thế. Một phiếu đi đường nào là do thu mua quyết khi tiếp nhận.</p>
<p>Một phương án = <strong>một cách mua một dòng hàng</strong>: nhà cung cấp nào, đơn giá bao nhiêu, giao khi nào, ở đâu. Dòng hàng vẫn là <strong>"tôi cần gì"</strong>; phương án là <strong>"mua ở đâu, giá nào"</strong>.</p>

<h2>II. Ai làm gì</h2>
<table><thead><tr><th>Vai</th><th>Làm gì</th><th>Ở màn nào</th></tr></thead><tbody>
<tr><td><strong>Nhân viên thu mua</strong></td><td><strong>Gắn</strong> phương án lên dòng mình được giao, rồi <strong>Chốt hoàn thành xử lý</strong>. Không chọn thay.</td><td><em>Xử lý phương án</em> (màn riêng)</td></tr>
<tr><td><strong>Người yêu cầu</strong></td><td><strong>Chọn</strong> một phương án cho mỗi dòng — chỉ họ biết mức giá đó còn đáng mua không.</td><td>thẻ <em>Phương án</em> trên màn chi tiết phiếu</td></tr>
<tr><td><strong>Quản lý / Admin thu mua</strong></td><td>Chọn <strong>thay</strong> người yêu cầu (đường tắt cho hàng gấp) và <strong>Tạo đơn</strong>.</td><td>thẻ <em>Phương án</em> trên màn chi tiết phiếu</td></tr>
</tbody></table>
<p><strong>Hàng rào dòng.</strong> Nhân viên thu mua chỉ gắn được phương án vào dòng có mình là người phụ trách. Bấm vào dòng của người khác thì máy chủ từ chối. Muốn đổi người phụ trách thì dùng nút <em>Phân bổ</em> như thường lệ.</p>
<p><strong>Cổng thời điểm.</strong> Gắn / sửa / chọn phương án chỉ làm được khi phiếu đang ở <strong>Đã điều phối · Đang xử lý · Đang mua · Đã mua</strong> — tức sau khi thu mua tiếp nhận phiếu và trước khi phiếu đóng. <strong>Xem</strong> thì lúc nào cũng xem được, kể cả phiếu đã hoàn thành hay đã hủy.</p>

<h2>III. Mở màn Xử lý phương án</h2>
<ul>
<li>Mở chi tiết một Yêu cầu mua hàng đã được điều phối, bấm nút <strong>Xử lý phương án</strong> ở đầu trang.</li>
<li>Màn chia theo <strong>dòng hàng</strong>: mỗi dòng một khối, đầu khối ghi mã hàng, phân loại, số lượng, giá đề xuất và người phụ trách.</li>
<li>Phiếu <strong>chưa điều phối</strong> thì màn báo "chỉ gắn phương án được sau khi thu mua đã tiếp nhận phiếu". Phiếu <strong>đã đóng</strong> thì mở được nhưng chỉ để xem lại.</li>
</ul>

<h2>IV. Gắn phương án — hai đường</h2>
<p>Mỗi dòng gắn được <strong>tối đa 5 phương án</strong>.</p>

<h3>Đường 1 — lấy từ kho khảo sát</h3>
<ul>
<li>Trong khối của dòng, phần dưới là <strong>kho báo giá đã duyệt</strong> — lọc được theo nhà cung cấp, theo phân loại, hoặc gõ tìm theo tên sản phẩm / mã / NCC.</li>
<li>Thấy dòng báo giá phù hợp thì bấm <strong>dấu cộng</strong> ở cuối dòng để gắn làm phương án.</li>
<li>Chỉ báo giá đã duyệt mới hiện ra. Báo giá khác phân loại với dòng yêu cầu vẫn gắn được nhưng có chú <em>Khác phân loại của dòng</em> — đọc kỹ trước khi gắn.</li>
</ul>

<h3>Đường 2 — nhập tay</h3>
<ul>
<li>Bấm <strong>Nhập tay</strong>, hộp <em>Nhập tay phương án</em> mở ra.</li>
<li><strong>Nhà cung cấp</strong>: chọn trong danh mục, hoặc gõ tên NCC ngoài danh mục vào ô bên dưới.</li>
<li>Điền <strong>Đơn giá</strong>, và điền thêm được <em>Tên SP theo NCC · Quy cách · ĐVT báo giá · Giá theo số lượng · Thời gian giao · Nơi giao · Phí vận chuyển · Ghi chú NSTM</em>.</li>
<li>Bấm <strong>Thêm phương án</strong>.</li>
</ul>
<p>Nhập tay dành cho trường hợp giá biến động liên tục, cần đưa ra một mức hợp lý cho người yêu cầu chốt — <strong>không phải để lách kho khảo sát</strong>.</p>

<h3>Phương án là bản chụp</h3>
<p>Gắn xong, phương án <strong>chụp lại</strong> giá và thông số tại thời điểm gắn. Phiếu khảo sát gốc sửa giá về sau thì phương án đã gắn <strong>không đổi theo</strong> — dấu vết thương lượng giữ nguyên.</p>

<h2>V. Phương án 0 — "Yêu cầu gốc"</h2>
<p>Ngay khi phiếu được điều phối, hệ thống <strong>tự sinh cho mọi dòng</strong> một phương án đặc biệt, nguồn ghi là <em>Yêu cầu gốc</em>: nó chụp đúng chính dòng yêu cầu — tên hàng, quy cách, ĐVT, giá người yêu cầu đề xuất — và <strong>chưa có nhà cung cấp</strong>.</p>
<table><thead><tr><th>Đặc điểm</th><th>Nghĩa là</th></tr></thead><tbody>
<tr><td><strong>Được tick sẵn</strong></td><td>Chỉ khi dòng chưa chọn gì khác. Người yêu cầu im lặng = đồng ý mua đúng theo yêu cầu gốc. Chọn một phương án khác thì phương án 0 tự bỏ chọn.</td></tr>
<tr><td><strong>Không xóa được</strong></td><td>Nó là đường lui của dòng — mọi dòng luôn có ít nhất một phương án để mua được.</td></tr>
<tr><td><strong>Không chiếm chỗ trong trần 5</strong></td><td>Mỗi dòng vẫn gắn đủ 5 phương án, phương án 0 đứng ngoài.</td></tr>
<tr><td><strong>Sửa được</strong></td><td>Như phương án nhập tay: sửa giá, và điền được nhà cung cấp.</td></tr>
</tbody></table>
<p><strong>Lưu ý.</strong> Phiếu đang chạy dở từ trước khi có tính năng này thì hệ thống sinh bù phương án 0 khi mở ra, không cần làm gì.</p>

<h2>VI. Chốt hoàn thành xử lý</h2>
<p>Gắn xong hết các dòng của mình thì bấm <strong>Chốt hoàn thành xử lý</strong> ở đầu màn. Chốt là lời khai "phần của tôi xong rồi" — dòng đã chốt mới hiện ra ở thẻ <em>Phương án</em> cho người yêu cầu chọn.</p>
<p>Còn dòng chưa gắn phương án nào thì hộp <strong>Dòng chưa có phương án</strong> mở ra, liệt kê đúng các dòng đó và bắt đánh dấu <strong>chốt rỗng</strong> trước khi chốt.</p>
<h3>Chốt rỗng nghĩa là gì</h3>
<p><strong>Chốt rỗng = "khảo sát không ra nhà cung cấp phù hợp cho dòng này"</strong>, không phải "không mua dòng này". Dòng chốt rỗng <strong>vẫn có phương án 0</strong> và người yêu cầu vẫn chọn được, nên vẫn mua được — thu mua tự tìm nhà cung cấp ở nhịp sau, hoặc điền nhà cung cấp thẳng vào phương án 0.</p>

<h2>VII. Sau khi người yêu cầu đã chọn</h2>
<p>Dòng đã chốt hoàn thành xử lý thì <strong>khóa</strong> phần gắn thêm / gỡ phương án. Nhưng thu mua vẫn chỉnh được ngay trên thẻ <em>Phương án</em> của màn chi tiết, đúng một khe:</p>
<table><thead><tr><th>Việc</th><th>Sau khi chốt</th></tr></thead><tbody>
<tr><td>Sửa <strong>giá</strong> của bất kỳ phương án nào</td><td>Được</td></tr>
<tr><td>Điền / sửa <strong>nhà cung cấp</strong> trên phương án 0 và phương án nhập tay</td><td>Được</td></tr>
<tr><td>Đổi nhà cung cấp của phương án <strong>lấy từ khảo sát</strong></td><td>Không — đổi NCC nghĩa là một phương án khác, hãy gắn phương án mới</td></tr>
<tr><td>Gắn thêm / gỡ phương án</td><td>Không — bấm <strong>Mở lại cho NSTM xử lý</strong> trên dòng đó</td></tr>
</tbody></table>
<p>Nút sửa là hình cây bút ở góc phải mỗi thẻ phương án, chỉ hiện cho người có quyền ghi Yêu cầu mua hàng và quyền xem nhà cung cấp.</p>

<h3>Áp 1 NCC cho nhiều dòng</h3>
<p>Cuối thẻ <em>Phương án</em> có khu <strong>Áp 1 NCC cho nhiều dòng</strong>, gom sẵn các dòng đang chọn một phương án <strong>chưa có nhà cung cấp</strong> (thường là phương án 0). Tick các dòng cần áp, chọn một nhà cung cấp, sửa đơn giá theo dòng nếu cần, rồi bấm <strong>Áp NCC</strong> — một lượt xong cả nhóm.</p>
<p>Khu này chỉ nhận dòng <strong>mình phụ trách</strong> và chỉ nhận phương án nhập tay / phương án 0, không đụng phương án lấy từ khảo sát.</p>

<h3>Mở lại một dòng</h3>
<p>Chọn nhầm, hoặc cần gắn thêm phương án, thì bấm <strong>Mở lại cho NSTM xử lý</strong> trên dòng đó. Dòng quay về màn <em>Xử lý phương án</em> và biến mất khỏi thẻ chọn cho tới khi chốt lại.</p>

<h2>VIII. Tạo đơn mua hàng</h2>
<p>Trên màn chi tiết phiếu chỉ có <strong>một nút Tạo đơn</strong>. Hệ thống tự chọn đường, người bấm không phải chọn:</p>
<ol>
<li>Còn dòng gom được theo phương án (đã chốt hoàn thành xử lý, chưa hủy, chưa nằm trên đơn nào, còn một phương án đang chọn) thì chạy <strong>đường gom theo nhà cung cấp</strong>.</li>
<li>Không có dòng nào như vậy nhưng còn dòng chưa đặt đủ thì chạy <strong>đường lập đơn tay</strong> như trước nay.</li>
<li>Không có cả hai thì nút ẩn đi.</li>
</ol>
<p>Nút đòi quyền <strong>tạo Đơn mua hàng</strong>, nên người yêu cầu không thấy nút này.</p>

<h3>Đường gom theo nhà cung cấp</h3>
<p>Một Đơn mua hàng chỉ mang <strong>một</strong> nhà cung cấp, nên <strong>N nhà cung cấp = N đơn</strong>. Bấm <em>Tạo đơn</em> thì hệ thống gom các dòng đã chọn phương án theo nhà cung cấp và sinh N <strong>đơn nháp</strong> một lượt:</p>
<ul>
<li>Đơn giá lấy theo giá của phương án đã chọn; VAT lấy của phương án, trống thì rơi về VAT của dòng.</li>
<li>ĐVT lấy theo ĐVT báo giá nếu phương án có ghi; cam kết giao và nơi giao chép vào ghi chú dòng.</li>
<li>Các dòng mà phương án đang chọn <strong>chưa có nhà cung cấp</strong> gom thành <strong>một đơn nháp riêng không NCC</strong>, đứng cuối, ghi chú nhắc bổ sung NCC trước khi gửi duyệt.</li>
<li>Dòng <strong>đã nằm trên một đơn</strong> (kể cả đơn nháp) bị bỏ qua — bấm lại không sinh đơn trùng.</li>
<li>Dòng bị người yêu cầu <strong>bỏ chọn hết</strong> (kể cả phương án 0) nghĩa là "khoan mua dòng này" — cũng bỏ qua.</li>
</ul>
<p>Hộp xác nhận luôn mở trước khi gom. Phiếu <strong>chưa có đơn nào</strong> thì hộp tả việc sắp làm, nút đồng ý ghi <em>Tạo đơn nháp</em>. Phiếu <strong>đã có đơn</strong> thì hộp đổi lời thành <em>Phiếu này đã có đơn mua hàng</em>, nêu số đơn đang có và vài mã đầu, nói rõ chỉ gom thêm dòng chưa nằm trên đơn nào; nút đồng ý ghi <em>Tạo thêm đơn nháp</em>.</p>
<p>Gom xong, hệ thống chuyển sang danh sách {ref("Đơn mua hàng (PO)", "Đơn mua hàng")} đã lọc theo phiếu. Đơn sinh ra là <strong>nháp</strong> — vào từng đơn kiểm lại rồi gửi duyệt như thường.</p>

<h3>Đường lập đơn tay vẫn còn</h3>
<p>Phiếu chưa ai chốt phương án (phiếu cũ, hoặc đang giữa chừng) vẫn lập đơn tay được từ nút đó. Đường tay nay còn <strong>điền sẵn</strong> giá / VAT / ĐVT / cam kết giao theo phương án đã chọn của từng dòng, và điền sẵn nhà cung cấp lên đầu đơn khi <strong>mọi dòng còn mua đều chọn cùng một nhà cung cấp</strong>.</p>

<h3>Một mẹo nhỏ: mã hàng tự điền</h3>
<p>Dòng <strong>chưa có mã hàng</strong> mà phương án được chọn có mã VTBB thì lúc chọn, hệ thống <strong>chép mã đó lên dòng</strong>. Nhờ vậy dòng bắt đầu được tính tiến độ đặt hàng / nhận hàng. Bỏ chọn thì <strong>không xóa mã</strong> đã chép — mã đã thành dữ liệu của dòng. Mã trùng với một dòng khác trên cùng phiếu thì không chép.</p>

<h2>IX. In phiếu</h2>
<p>Nút <strong>In phiếu</strong> ở đầu trang cũng chỉ một nút, hệ thống chọn bản in theo vai và theo tình trạng phiếu:</p>
<ul>
<li><strong>Bản thường</strong> — tờ phiếu đề xuất quen thuộc, nay có thêm cặp cột <em>Giá đề xuất · Giá chốt · Chênh lệch</em> để thấy ngay giá đã đổi bao nhiêu.</li>
<li><strong>Bản tách theo nhà cung cấp</strong> — vẫn là tờ phiếu đề xuất đó, nhưng <strong>mỗi nhà cung cấp một trang</strong>, chỉ in các dòng đã chọn phương án của nhà cung cấp đó và điền sẵn tên NCC vào ô nhà cung cấp. Chỉ người có quyền xem nhà cung cấp mới ra bản này.</li>
</ul>

<h2>X. Chứng từ liên quan</h2>
<p>Dưới thẻ <em>Phương án</em> có thẻ <strong>Chứng từ liên quan</strong>, luôn hiện dù rỗng, gồm hai khu:</p>
<ul>
<li><strong>Yêu cầu báo giá nguồn</strong> — mọi phiếu báo giá đã sinh ra phiếu này (một yêu cầu mua hàng gom được dòng từ nhiều phiếu báo giá). Phiếu lập tay thì nói rõ là lập tay.</li>
<li><strong>Đơn mua hàng đã lập</strong> — mã, ngày đặt, nhà cung cấp, tổng tiền, trạng thái; bấm mã là sang thẳng đơn.</li>
</ul>

<h2>XI. Bẫy hay gặp</h2>
<ul>
<li><strong>Chốt hoàn thành xử lý không phải là chọn phương án.</strong> Thu mua chốt = "tôi gắn xong"; người yêu cầu chọn = "tôi mua theo phương án này". Hai việc, hai người, hai nút.</li>
<li><strong>Dòng chưa chốt thì người yêu cầu không thấy.</strong> Người yêu cầu báo "không thấy phương án nào" thì kiểm lại đã bấm <em>Chốt hoàn thành xử lý</em> chưa.</li>
<li><strong>ĐVT lệch nhau.</strong> Dòng ghi "cái" mà nhà cung cấp báo giá theo "thùng 100 cái" thì hệ thống <strong>không tự quy đổi</strong> — sai hệ số một lần là sai tiền cả đơn. Màn hình cảnh báo, bản in ghi cả hai đơn vị; khi nhập tay hãy <strong>tự quy giá về đúng ĐVT của dòng</strong>.</li>
<li><strong>Số lượng tối thiểu lớn hơn số cần.</strong> Thẻ phương án cảnh báo để người yêu cầu thấy trước khi chọn. Đơn sinh ra vẫn lấy số lượng của dòng, không tự nâng lên.</li>
<li><strong>Chọn phương án không ghi đè giá của dòng.</strong> Cố ý — để giữ dấu vết giá đề xuất so với giá chốt, và để bỏ chọn không phải khôi phục gì. Bản in có đủ hai cột.</li>
<li><strong>Danh sách phiếu không cho biết phiếu đang ở chặng nào của phương án.</strong> Trạng thái phiếu vẫn là năm bậc cũ; cả chặng phương án diễn ra bên trong <em>Đã điều phối</em>. Đây là cố ý, không phải thiếu sót — muốn biết thì mở phiếu ra.</li>
<li><strong>Không có chuông nào cho chặng phương án.</strong> Gắn xong thì tự nhắn cho người yêu cầu, chọn xong thì tự nhắn cho thu mua. Chuông đã viết nhưng đang tắt vì phần lớn người yêu cầu còn dùng giao diện cũ, nơi không có khu phương án.</li>
<li><strong>Bấm Tạo đơn hai lần không sinh đơn trùng</strong>, nhưng hộp xác nhận sẽ nói rõ phiếu đã có đơn — đọc rồi hãy bấm.</li>
</ul>

<h2>XII. Điều hướng</h2>
<ul>
<li><strong>Thuộc thư mục:</strong> {ref(STAFF_PARENT_TITLE, STAFF_PARENT_TITLE)}</li>
<li><strong>Bài liên quan:</strong> {ref(REQUESTER_ARTICLE_TITLE, "Chọn phương án (cho người yêu cầu)")} · {ref("Yêu cầu mua hàng", "Yêu cầu mua hàng")} · {ref("Xử lý yêu cầu mua hàng", "Xử lý yêu cầu mua hàng")} · {ref("Đơn mua hàng (PO)", "Đơn mua hàng (PO)")} · {ref("Khảo sát & Phiếu khảo sát", "Khảo sát &amp; Phiếu khảo sát")}</li>
</ul>
"""


# --------------------------------------------------------------------------- #
#  BÀI 2 — cho người yêu cầu
# --------------------------------------------------------------------------- #
REQUESTER_SUMMARY = (
    "Thu mua đã tìm được vài mức giá cho phiếu của bạn: cách đọc các phương án, chọn một "
    "phương án cho mỗi dòng, đổi ý, và điều gì xảy ra nếu bạn không chọn gì"
)

REQUESTER_CONTENT = f"""<h2>I. Chuyện gì đang xảy ra</h2>
<p>Bạn lập một {ref("Yêu cầu mua hàng", "Yêu cầu mua hàng")} với giá bạn biết. Thu mua tiếp nhận và phát hiện giá đã đổi, hoặc tìm được nơi bán tốt hơn. Thay vì trả phiếu về cho bạn làm lại, họ gắn lên từng dòng hàng vài <strong>phương án</strong> — mỗi phương án là một mức giá kèm thông số và thời gian giao.</p>
<p>Việc của bạn: <strong>mỗi dòng chọn đúng một phương án</strong>. Chỉ bạn mới biết mức giá đó còn đáng mua không.</p>
<p><strong>Bạn không thấy tên nhà cung cấp</strong> — đó là cố ý. Các phương án hiện dưới tên <em>Phương án 1 · Phương án 2 · …</em>, bạn chọn theo <strong>giá và thông số</strong>.</p>

<h2>II. Mở chỗ chọn</h2>
<ul>
<li>Mở chi tiết phiếu của bạn, kéo xuống thẻ <strong>Phương án</strong>.</li>
<li>Thẻ chỉ hiện những dòng mà thu mua đã <strong>xử lý xong</strong>. Dòng nào chưa thấy là thu mua còn đang tìm giá.</li>
<li>Mỗi dòng một khối; trong khối, mỗi phương án là một thẻ bấm được.</li>
</ul>
<p><strong>Lưu ý.</strong> Không có thông báo nào báo cho bạn biết đã tới lượt chọn. Phiếu đang chạy thì thỉnh thoảng mở ra xem, hoặc nhờ thu mua nhắn.</p>

<h2>III. Chọn một phương án</h2>
<ul>
<li>Bấm vào <strong>bất kỳ chỗ nào trên thẻ</strong> là chọn — không cần nhắm đúng ô tròn nhỏ.</li>
<li>Thẻ đang chọn viền đậm lên và có phù hiệu <strong>Đã chọn</strong>.</li>
<li>Mỗi dòng <strong>đúng một</strong> phương án. Bấm sang thẻ khác là đổi; bấm lại chính thẻ đang chọn là <strong>bỏ chọn</strong>.</li>
<li>Không có nút Lưu — bấm là ghi ngay.</li>
</ul>
<p>Trên thẻ có <em>Đơn giá · ĐVT báo giá · Khoảng SL áp giá · Xuất xứ · Thời gian giao · Địa điểm giao · Phí vận chuyển · Có mẫu · Kết quả lab</em> và ghi chú của thu mua. Đọc kỹ hai chỗ hay làm lệch tiền:</p>
<ul>
<li><strong>ĐVT báo giá khác đơn vị bạn ghi</strong> (bạn ghi "cái", báo giá theo "thùng"). Thấy chú cảnh báo thì hỏi lại thu mua trước khi chọn.</li>
<li><strong>Số lượng tối thiểu lớn hơn số bạn cần.</strong> Thẻ cảnh báo trước. Chọn thì vẫn chỉ mua đúng số bạn cần, nhưng nhà cung cấp có thể không bán.</li>
</ul>

<h2>IV. Nếu bạn không chọn gì</h2>
<p>Mỗi dòng luôn có sẵn một thẻ <strong>Phương án 0</strong>, nguồn ghi <em>Yêu cầu gốc</em> — chính là mua đúng theo dòng bạn đã ghi trong phiếu, với giá bạn đề xuất. Thẻ này <strong>được tick sẵn</strong>.</p>
<p>Nghĩa là <strong>không làm gì = đồng ý mua theo yêu cầu gốc</strong>. Chọn một phương án khác thì Phương án 0 tự bỏ tick.</p>
<p>Muốn <strong>khoan mua</strong> một dòng thì bỏ chọn <strong>hết</strong>, kể cả Phương án 0 — dòng không chọn gì sẽ bị bỏ qua khi thu mua lập đơn.</p>

<h2>V. Dòng ghi "chốt rỗng" là sao</h2>
<p>Có dòng thu mua đánh dấu <strong>chốt rỗng</strong>, kèm câu "không có NCC phù hợp cho dòng hàng này". Đó <strong>không phải</strong> là từ chối mua — chỉ là khảo sát chưa ra nơi bán phù hợp. Dòng đó <strong>vẫn chọn được Phương án 0</strong> và vẫn mua được; thu mua sẽ tìm nơi bán ở nhịp sau.</p>

<h2>VI. Chọn nhầm thì sao</h2>
<ul>
<li><strong>Đổi sang phương án khác</strong>: bấm thẻ khác, xong.</li>
<li><strong>Muốn thu mua tìm thêm giá</strong>: bấm <strong>Mở lại cho NSTM xử lý</strong> ở đầu khối dòng đó. Dòng quay về cho thu mua, tạm biến mất khỏi thẻ của bạn cho tới khi họ xử lý xong.</li>
<li><strong>Dòng đã lên đơn mua hàng rồi</strong> thì đổi chọn không kéo đơn về được nữa — báo thu mua.</li>
</ul>

<h2>VII. Chọn xong rồi thì sao</h2>
<p>Không có nút "chốt xong" nào phải bấm nữa. Thu mua nhìn thấy lựa chọn của bạn và bấm <strong>Tạo đơn</strong> — hệ thống gom các dòng bạn đã chọn theo từng nhà cung cấp thành các đơn mua hàng nháp.</p>
<p>Theo dõi tiếp ở thẻ <strong>Chứng từ liên quan</strong> ngay bên dưới: khu <em>Đơn mua hàng đã lập</em> liệt kê mọi đơn sinh ra từ phiếu này. Chưa có đơn nào thì thẻ nói rõ là chưa có.</p>
<p><strong>Lưu ý.</strong> Giá bạn ghi ban đầu <strong>không bị ghi đè</strong> khi bạn chọn một phương án khác. Bản in giữ cả hai cột <em>Giá đề xuất</em> và <em>Giá chốt</em> để thấy chênh lệch.</p>

<h2>VIII. Bẫy hay gặp</h2>
<ul>
<li><strong>Không thấy thẻ Phương án.</strong> Phiếu chưa được thu mua tiếp nhận (điều phối), hoặc chưa dòng nào được xử lý xong.</li>
<li><strong>Thấy dòng này mà không thấy dòng kia.</strong> Bình thường — thu mua xử lý xong dòng nào thì dòng đó hiện ra, không phải chờ đủ cả phiếu.</li>
<li><strong>Bấm mãi không chọn được.</strong> Phiếu đã đóng hoặc đã hủy thì chỉ xem lại được, không chọn thêm.</li>
<li><strong>Quản lý thu mua chọn thay bạn.</strong> Với hàng gấp thì được phép, để khỏi phải chờ. Mở phiếu ra là thấy lựa chọn hiện tại.</li>
</ul>

<h2>IX. Điều hướng</h2>
<ul>
<li><strong>Thuộc thư mục:</strong> {ref(REQUESTER_PARENT_TITLE, REQUESTER_PARENT_TITLE)}</li>
<li><strong>Bài liên quan:</strong> {ref("Yêu cầu mua hàng", "Yêu cầu mua hàng")} · {ref("Trạng thái yêu cầu mua hàng", "Trạng thái yêu cầu mua hàng")} · {ref("Trạng thái dòng hàng", "Trạng thái dòng hàng")} · {ref(STAFF_ARTICLE_TITLE, "Xử lý phương án (cho thu mua)")}</li>
</ul>
"""


#  Chỗ đứng mong muốn khi bài CHƯA tồn tại. Bài thu mua xếp ngay sau «Tiến độ mua hàng» (4)
#  chứ không rơi xuống cuối nhóm — nhóm này có một bài cố ý để sort_order 50.
#  Bài đã tồn tại thì giữ nguyên chỗ cũ, không kéo về đây.
ARTICLES = [
    (STAFF_PARENT_TITLE, STAFF_ARTICLE_TITLE, STAFF_SUMMARY, STAFF_CONTENT, 5),
    (REQUESTER_PARENT_TITLE, REQUESTER_ARTICLE_TITLE, REQUESTER_SUMMARY, REQUESTER_CONTENT, 8),
]


def find_group(db, title: str):
    """Nhóm cha là bài GỐC (parent_id rỗng); trùng tiêu đề thì ưu tiên bài gốc."""
    candidates = db.query(HelpArticle).filter(HelpArticle.title == title).all()
    if not candidates:
        return None
    for art in candidates:
        if art.parent_id is None:
            return art
    return candidates[0]


def collect_descendants(db, root_id):
    nodes = []
    stack = [root_id]
    while stack:
        nid = stack.pop()
        nodes.append(nid)
        for (cid,) in db.query(HelpArticle.id).filter(HelpArticle.parent_id == nid).all():
            stack.append(cid)
    return nodes


def delete_subtree(db, root_id):
    #  Xóa RAW theo thứ tự sâu-trước: FK tự tham chiếu parent_id KHÔNG cascade.
    nodes = collect_descendants(db, root_id)
    for nid in reversed(nodes):
        db.execute(text("DELETE FROM tab_help_home_item WHERE article_id = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article_slide WHERE article_id = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article WHERE id = :id"), {"id": nid})
    db.flush()
    return len(nodes)


def seed_one(db, parent, title: str, summary: str, content: str, default_order: int):
    old = (
        db.query(HelpArticle)
        .filter(HelpArticle.title == title, HelpArticle.parent_id == parent.id)
        .first()
    )
    order = None
    if old is not None:
        order = old.sort_order
        removed = delete_subtree(db, old.id)
        print(f"  Đã xóa bài cũ «{title}»: {removed} bài (id={old.id}).")
    if order is None:
        order = default_order

    art = HelpArticle(
        parent_id=parent.id,
        title=title,
        summary=summary,
        content=content,
        sort_order=order,
    )
    db.add(art)
    db.flush()
    print(f"  Đã dựng «{title}» (id={art.id}) dưới «{parent.title}» "
          f"(id={parent.id}, sort_order={order}).")


def main():
    db = SessionLocal()
    try:
        #  Kiểm ĐỦ hai nhóm TRƯỚC khi ghi: thiếu một nhóm mà đã chèn bài kia thì lần chạy
        #  sau vẫn idempotent, nhưng người chạy dễ tưởng script đã xong.
        groups = {}
        for parent_title, *_ in ARTICLES:
            group = find_group(db, parent_title)
            if group is None:
                print(f"Không thấy nhóm «{parent_title}» — dừng, không tạo bài gốc mới.")
                sys.exit(1)
            groups[parent_title] = group

        for parent_title, title, summary, content, default_order in ARTICLES:
            seed_one(db, groups[parent_title], title, summary, content, default_order)

        db.commit()
        print("Xong.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
