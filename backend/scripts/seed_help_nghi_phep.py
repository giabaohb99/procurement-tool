# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ NGHỈ PHÉP.

Dựng cây bài viết: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ") -> 10 bài
chia theo VAI TRÒ + TÁC VỤ. Nghỉ phép khác Diễn đàn ở chỗ ba nhóm người dùng
làm ba việc hoàn toàn khác nhau — người nộp đơn, người duyệt, và phòng Nhân sự
cấp quỹ — nên chia theo vai trước rồi mới tới tác vụ.

Bản 2 (04/09/2026) viết dày hơn hẳn bản đầu: mỗi bài đi theo TỪNG BƯỚC với đúng
nhãn nút và nhãn ô trên màn hình, thêm ba bài mới — *tình huống thường gặp*,
*câu báo lỗi*, và tách phần Nhân sự làm ba bài (quỹ · danh mục · phân quyền).
Lý do tách: bài gộp cũ dài mà vẫn hụt, người đọc phải tự suy phần còn thiếu.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_nghi_phep.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/17-nghi-phep.md` và gói
tri thức trợ lý `app/modules/assistant/packs/40-nghi-phep.md`. Ba nơi lệch nhau
thì người dùng đọc một đằng, trợ lý trả lời một nẻo.

⚠️ Câu báo lỗi trích trong bài *Gặp câu báo lỗi* lấy nguyên văn từ
`app/modules/leave/request_service.py`. Sửa câu bên đó thì sửa cả ở đây, nếu
không người dùng tra theo câu mình nhìn thấy sẽ không ra bài nào.
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

ROOT_TITLE = "Hướng dẫn sử dụng Nghỉ phép"


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


NOP_DON = "Nộp đơn nghỉ phép"
QUY_PHEP = "Hiểu số ngày phép còn lại"
THEO_DOI = "Theo dõi, sửa và hủy đơn nghỉ"
DUYET = "Duyệt đơn nghỉ phép"
LICH_NGHI = "Xem Lịch nghỉ của phòng ban"
TINH_HUONG = "Mười tình huống nghỉ thường gặp"
BAO_LOI = "Gặp câu báo lỗi thì làm gì"
NS_QUY = "Nhân sự — Cấp và điều chỉnh quỹ phép"
NS_DANH_MUC = "Nhân sự — Loại nghỉ, bậc thâm niên và Lịch ngày lễ"
NS_QUYEN = "Nhân sự — Phân quyền và luồng duyệt"


TREE = {
    "title": ROOT_TITLE,
    "icon": "calendar",
    "summary": "Nộp đơn nghỉ phép, xem quỹ phép còn lại, duyệt đơn và cấp quỹ",
    "content": f"""<h2>Nghỉ phép là gì?</h2>
<p>Phân hệ để nhân viên <strong>nộp đơn nghỉ phép</strong>, người quản lý duyệt, và phòng Nhân sự cấp <strong>quỹ phép năm</strong>. Vào bằng menu <strong>Nhân sự ▸ Nghỉ phép</strong>.</p>
<p>Thứ đáng giá nhất ở đây không phải tờ đơn — mà là <strong>số ngày phép còn lại hiện ngay lúc bạn đang nhập</strong>. Toàn bộ phần quỹ phép, bậc thâm niên và lịch ngày lễ tồn tại để con số đó đúng.</p>

<h2>Bốn khu vực, chuyển bằng thanh tab</h2>
<table>
<thead><tr><th>Tab</th><th>Dùng để</th><th>Ai thấy</th></tr></thead>
<tbody>
<tr><td><strong>Đơn nghỉ phép</strong></td><td>Nộp đơn, theo dõi đơn của mình, duyệt đơn của người khác</td><td>Mọi người</td></tr>
<tr><td><strong>Lịch nghỉ</strong></td><td>Ai nghỉ ngày nào — xem theo ngày / tuần / tháng</td><td>Mọi người</td></tr>
<tr><td><strong>Quỹ phép năm</strong></td><td>Số ngày phép của từng người từng năm, cấp phát và điều chỉnh</td><td>Phòng Nhân sự</td></tr>
<tr><td><strong>Thiết lập</strong></td><td>Loại nghỉ (kèm bậc thâm niên) và Lịch ngày lễ</td><td>Phòng Nhân sự</td></tr>
</tbody>
</table>
<p>Không thấy đủ bốn tab <strong>không phải lỗi</strong> — đó là phân quyền. Xem {ref(NS_QUYEN, "bài Phân quyền và luồng duyệt")}.</p>

<h2>Bốn khái niệm đừng lẫn</h2>
<table>
<thead><tr><th>Thứ</th><th>Là gì</th></tr></thead>
<tbody>
<tr><td><strong>Đơn nghỉ phép</strong></td><td>Chứng từ bạn nộp, có số dạng <code>NP001</code>. Đây là thứ để xin nghỉ.</td></tr>
<tr><td><strong>Giấy nghỉ phép (GNP)</strong></td><td><strong>Văn bản</strong> bên phân hệ Văn thư, hệ <strong>tự sinh sau khi đơn đã duyệt</strong>. Là hồ sơ lưu sổ, không phải thứ để nộp.</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Danh mục: Phép năm, Nghỉ ốm, Thai sản, Nghỉ không lương… Mỗi loại một bộ luật riêng.</td></tr>
<tr><td><strong>Quỹ phép</strong></td><td>Số ngày của <strong>một người × một năm × một loại nghỉ</strong>.</td></tr>
</tbody>
</table>
<p>⚠️ Muốn xin nghỉ thì <strong>nộp đơn</strong> ở đây, <strong>đừng</strong> vào Văn thư tạo «Giấy nghỉ phép» — làm tay ra một tờ giấy không gắn với quỹ phép nào, và không ai được báo để duyệt.</p>

<h2>Vòng đời một tờ đơn</h2>
<pre>                gửi duyệt              ký chặng cuối
Nháp  ─────────────────────►  Chờ duyệt  ─────────────────►  Đã duyệt
  ▲                             │  │  │                        │
  │  (sửa rồi gửi lại)          │  │  │                        └─ trừ quỹ thật
  └──── Trả về chỉnh sửa  ◄─────┘  │  │                           + sinh giấy GNP
                                   │  └──►  Từ chối   (khóa hẳn)
        Đã hủy  ◄── người nộp tự rút, kể cả sau khi đã duyệt</pre>
<p>Ba kết cục không-duyệt (<strong>Từ chối · Trả về · Hủy</strong>) đều <strong>trả lại</strong> số ngày phép đang bị giữ chỗ.</p>

<h2>Ba câu hay hỏi nhất</h2>
<ul>
<li><strong>«Vừa nộp đơn xong sao phép còn lại hụt luôn?»</strong> — đúng như vậy, và là cố ý. Xem {ref(QUY_PHEP, "Hiểu số ngày phép còn lại")}.</li>
<li><strong>«Nộp rồi sửa được không?»</strong> — không. Chỉ sửa được lúc <em>Nháp</em> và <em>Trả về chỉnh sửa</em>. Xem {ref(THEO_DOI, "Theo dõi, sửa và hủy đơn")}.</li>
<li><strong>«Không thấy menu Nghỉ phép»</strong> — gần như luôn là phân quyền, xem {ref(NS_QUYEN, "bài Phân quyền")}.</li>
</ul>

<h2>Đọc theo việc bạn cần làm</h2>
<p><strong>Người đi nghỉ:</strong> {ref(NOP_DON, "Nộp đơn")} · {ref(QUY_PHEP, "hiểu quỹ phép")} · {ref(THEO_DOI, "theo dõi, sửa, hủy")} · {ref(TINH_HUONG, "tình huống thường gặp")} · {ref(BAO_LOI, "câu báo lỗi")}.</p>
<p><strong>Người duyệt:</strong> {ref(DUYET, "Duyệt đơn nghỉ phép")} · {ref(LICH_NGHI, "xem Lịch nghỉ")}.</p>
<p><strong>Phòng Nhân sự:</strong> {ref(NS_QUY, "cấp và điều chỉnh quỹ")} · {ref(NS_DANH_MUC, "loại nghỉ và ngày lễ")} · {ref(NS_QUYEN, "phân quyền và luồng duyệt")}.</p>""",
    "children": [
        {
            "title": NOP_DON,
            "icon": "file-text",
            "summary": "Sáu bước từ mở đơn tới gửi duyệt, giải thích từng ô trên form",
            "content": f"""<h2>Nộp đơn nghỉ phép</h2>
<p>Toàn bộ việc gói trong sáu bước dưới đây. Đơn <strong>luôn</strong> sinh ra ở trạng thái <em>Nháp</em> — gửi duyệt là một bước riêng, bấm sau.</p>

<h2>Sáu bước</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Nghỉ phép</strong>, đứng ở tab <strong>Đơn nghỉ phép</strong>.</li>
<li>Bấm nút <strong>«Nộp đơn nghỉ phép»</strong> ở góc trên bên phải.</li>
<li>Chọn <strong>Loại nghỉ</strong> <em>trước tiên</em> — mỗi loại một luật riêng, và chọn xong thì số ngày còn lại của loại đó hiện ra ngay dưới.</li>
<li>Chọn <strong>Từ ngày / Đến ngày</strong> (kèm <strong>buổi</strong> nếu nghỉ nửa ngày). Ô <strong>Tổng số ngày</strong> tự điền.</li>
<li>Viết <strong>Lý do nghỉ</strong>, khai <strong>Bàn giao công việc</strong>, điền số điện thoại liên hệ nếu công ty yêu cầu.</li>
<li>Bấm <strong>«Lưu nháp»</strong>. Kiểm lại một lượt rồi bấm <strong>«Gửi duyệt»</strong>.</li>
</ol>
<p>⚠️ Nút <strong>«Gửi duyệt»</strong> chỉ hiện <strong>sau khi đơn đã được lưu ít nhất một lần</strong>. Chưa lưu mà không thấy nút thì không phải hỏng — bấm «Lưu nháp» trước.</p>

<h2>Từng ô trên đơn</h2>
<table>
<thead><tr><th>Ô</th><th>Bắt buộc</th><th>Ghi gì / cần biết</th></tr></thead>
<tbody>
<tr><td><strong>Loại nghỉ</strong></td><td>Có</td><td>Quyết định mọi luật còn lại: có trừ quỹ không, phải báo trước mấy ngày, tối đa mấy ngày một lần, có trừ cuối tuần và ngày lễ không.</td></tr>
<tr><td><strong>Tổng số ngày</strong></td><td>Có (tự điền)</td><td>Hệ tính sẵn và <strong>đã trừ thứ Bảy, Chủ nhật, ngày lễ</strong>. Gõ đè được — lúc đó dòng chú thích đổi thành <em>«Bạn đang nhập tay. Hệ thống gợi ý N ngày.»</em> để bạn biết mình đang lệch với máy.</td></tr>
<tr><td><strong>Từ ngày</strong> + <strong>Buổi bắt đầu</strong></td><td>Có</td><td>Buổi: <em>Cả ngày · Buổi sáng · Buổi chiều</em>.</td></tr>
<tr><td><strong>Đến ngày</strong> + <strong>Buổi kết thúc</strong></td><td>Có</td><td>Nghỉ một ngày thì để hai ô ngày bằng nhau.</td></tr>
<tr><td><strong>Lý do nghỉ</strong></td><td>Có, khi gửi duyệt</td><td>Người duyệt đọc đúng dòng này để quyết. Viết cụ thể, đừng viết «việc riêng».</td></tr>
<tr><td><strong>Bàn giao công việc</strong></td><td>Không, nhưng nên</td><td>Ai gánh việc gì thay bạn. <strong>Thiếu người bàn giao là lý do bị trả đơn phổ biến nhất.</strong></td></tr>
<tr><td><strong>Điện thoại liên hệ khi nghỉ</strong></td><td>Không</td><td>Số gọi được trong thời gian nghỉ.</td></tr>
<tr><td><strong>Địa chỉ khi nghỉ</strong></td><td>Không</td><td>Nơi ở trong thời gian nghỉ (đi tỉnh, về quê…).</td></tr>
</tbody>
</table>

<h2>Số ngày phép còn lại — ô quan trọng nhất</h2>
<p>Ngay dưới «Loại nghỉ» và «Tổng số ngày» có một dải chạy hết bề ngang, nói bạn còn bao nhiêu ngày của <em>chính loại nghỉ vừa chọn</em>. Ba trạng thái của dải này:</p>
<ul>
<li><strong>Còn đủ</strong> — hiện số còn lại trên tổng quỹ, cứ thế gửi duyệt.</li>
<li><strong>Xin vượt quỹ</strong> — cảnh báo ngay tại chỗ, kèm gợi ý chuyển sang <strong>«Nghỉ không lương»</strong>. Đừng bấm gửi duyệt, backend cũng chặn.</li>
<li><strong>Loại nghỉ không trừ quỹ</strong> — nói thẳng là không giới hạn, chứ không hiện số <code>0</code> gây hiểu nhầm là hết phép.</li>
</ul>
<p>Xin <strong>đúng bằng</strong> số còn lại thì <strong>không</strong> bị cảnh báo — đó là hợp lệ. Chi tiết cách con số này được tính: {ref(QUY_PHEP, "Hiểu số ngày phép còn lại")}.</p>

<h2>Lưu nháp hay Gửi duyệt?</h2>
<table>
<thead><tr><th></th><th>Lưu nháp</th><th>Gửi duyệt</th></tr></thead>
<tbody>
<tr><td>Ai thấy đơn</td><td>Chỉ bạn</td><td>Người duyệt nhận việc + thông báo chuông</td></tr>
<tr><td>Trừ phép chưa</td><td><strong>Chưa</strong></td><td><strong>Trừ ngay</strong> (giữ chỗ)</td></tr>
<tr><td>Kiểm nhập đủ</td><td>Không kiểm</td><td>Kiểm — thiếu ô nào là chặn</td></tr>
<tr><td>Sửa lại được</td><td>Thoải mái</td><td><strong>Khóa</strong></td></tr>
<tr><td>Xóa được</td><td>Được (nút <strong>«Xóa đơn»</strong>)</td><td>Không — chỉ <strong>hủy</strong></td></tr>
</tbody>
</table>
<p>Cứ lưu nháp thoải mái rồi hoàn thiện sau: hệ chỉ kiểm "nhập đủ" ở bước gửi duyệt.</p>

<h2>Nghỉ nửa ngày</h2>
<p>Đặt <strong>Từ ngày = Đến ngày</strong>, rồi chọn <strong>Buổi bắt đầu</strong> và <strong>Buổi kết thúc</strong> là <em>Buổi sáng</em> (hoặc cả hai là <em>Buổi chiều</em>). Tổng số ngày ra <strong>0,5</strong> và quỹ trừ đúng nửa ngày.</p>
<p>⚠️ Nghỉ <strong>từ buổi chiều đến buổi sáng cùng ngày</strong> là một khoảng trống — hệ chặn.</p>

<h2>Nộp hộ người khác</h2>
<p>Hành chính hoặc trợ lý nộp hộ được: điền <strong>người nghỉ</strong> vào ô riêng trên đơn. Bỏ trống ô đó thì người nghỉ chính là người đang gõ.</p>
<p>Cả <strong>người lập</strong> lẫn <strong>người nghỉ</strong> đều thấy tờ đơn đó trong tab <em>Đơn của tôi</em> — cố ý, vì hai người đều có việc với nó.</p>

<h2>Gửi duyệt xong thì gì xảy ra</h2>
<ol>
<li>Số ngày bị <strong>giữ chỗ</strong> ngay, trừ khỏi «còn lại».</li>
<li>Đơn khóa, không sửa được nữa.</li>
<li>Việc rơi vào hộp <em>Cần tôi duyệt</em> của người ký chặng 1, kèm thông báo chuông.</li>
<li>Ký hết các chặng thì đơn thành <strong>Đã duyệt</strong>: quỹ trừ thật, và hệ <strong>tự sinh Giấy nghỉ phép</strong> bên Văn thư.</li>
</ol>
<p>Theo dõi tiếp ở {ref(THEO_DOI, "Theo dõi, sửa và hủy đơn nghỉ")}. Bị chặn không gửi được thì tra câu báo lỗi ở {ref(BAO_LOI, "bài Gặp câu báo lỗi")}.</p>""",
        },
        {
            "title": QUY_PHEP,
            "icon": "wallet",
            "summary": "Công thức, ví dụ bằng số, vì sao vừa nộp đơn đã thấy hụt ngày, thâm niên",
            "content": f"""<h2>Hiểu số ngày phép còn lại</h2>
<p>Con số này xuất hiện ở <strong>ba chỗ</strong>: dải ngay dưới ô «Loại nghỉ» khi đang điền đơn · cột <strong>Còn lại</strong> ở bảng <em>Quỹ phép năm</em> · và thẻ chi tiết của một dòng quỹ. Ba chỗ cùng một công thức, không có chỗ nào tính riêng.</p>

<h2>Công thức</h2>
<pre>còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay)
          − đã nghỉ − đang chờ duyệt</pre>
<p><strong>Số còn lại không được lưu thành cột nào cả</strong> — nó luôn được tính lại. Lưu thêm thì có hai nguồn sự thật, và cái thứ hai chắc chắn sẽ lệch.</p>

<h2>Sáu con số cấu thành</h2>
<table>
<thead><tr><th>Cột trên bảng</th><th>Ở đâu ra</th></tr></thead>
<tbody>
<tr><td><strong>Hạn mức</strong></td><td>Khai trên <em>Loại nghỉ</em> (ví dụ Phép năm 12 ngày).</td></tr>
<tr><td><strong>Thâm niên</strong></td><td>Cộng thêm theo bảng bậc, tính tại 01/01 của năm đó.</td></tr>
<tr><td><strong>Chuyển năm trước</strong></td><td>Phép tồn năm ngoái chuyển sang, nếu loại nghỉ đó bật cờ cho chuyển.</td></tr>
<tr><td><strong>Điều chỉnh tay</strong></td><td>Phòng Nhân sự sửa, cột duy nhất nhận <strong>số âm</strong>. Luôn kèm lý do.</td></tr>
<tr><td><strong>Đã nghỉ</strong></td><td>Cộng dồn các đơn <strong>đã duyệt</strong>.</td></tr>
<tr><td><strong>Chờ duyệt (đang giữ chỗ)</strong></td><td>Cộng dồn các đơn <strong>đang trong luồng duyệt</strong>.</td></tr>
</tbody>
</table>

<h2>Ví dụ bằng số</h2>
<p>Chị A vào làm được 11 năm, Phép năm hạn mức 12, năm ngoái không chuyển ngày nào, chưa từng bị điều chỉnh tay. Trong năm đã nghỉ 4 ngày, và đang có một đơn 3 ngày chờ sếp ký:</p>
<pre>(12 hạn mức + 2 thâm niên + 0 chuyển + 0 điều chỉnh) − 4 đã nghỉ − 3 chờ duyệt = 7 ngày</pre>
<p>Chị A mở form nộp đơn ra sẽ thấy <strong>7</strong>, không phải 10. Ba ngày kia <em>chưa</em> nghỉ nhưng <em>đã</em> bị giữ chỗ.</p>

<h2>Vì sao vừa nộp đơn đã thấy hụt ngày?</h2>
<p><strong>Vì «đang chờ duyệt» ĐÃ bị trừ khỏi «còn lại».</strong> Nộp đơn 3 ngày là số còn lại tụt ngay 3 ngày, chưa cần ai duyệt.</p>
<p>Đây là <strong>cố ý</strong>: không giữ chỗ như vậy thì nộp mười đơn liền tay đều lọt qua chốt kiểm, vì đơn nào cũng thấy quỹ còn nguyên. Lỗi đó chỉ lộ ra khi đã có người nghỉ thừa hai tuần.</p>
<p>Ngày bị giữ chỗ được <strong>trả lại ngay</strong> trong cả ba trường hợp: đơn bị <strong>từ chối</strong> · bị <strong>trả về chỉnh sửa</strong> · bạn <strong>tự hủy</strong>. Hủy một đơn <strong>đã duyệt</strong> thì hoàn lại phần «đã nghỉ».</p>

<h2>Thâm niên</h2>
<p>Bảng bậc mặc định:</p>
<table>
<thead><tr><th>Làm đủ</th><th>Cộng thêm</th></tr></thead>
<tbody>
<tr><td>5 năm</td><td>+1 ngày</td></tr>
<tr><td>10 năm</td><td>+2 ngày</td></tr>
<tr><td>15 năm</td><td>+3 ngày</td></tr>
<tr><td>20 năm trở lên</td><td>+4 ngày</td></tr>
</tbody>
</table>
<p>⚠️ <strong>Lấy bậc CAO NHẤT khớp được, KHÔNG cộng dồn</strong>: người làm 10 năm được <strong>+2</strong>, không phải +1+2 = 3.</p>
<p>Thâm niên tính <strong>tại ngày 01/01</strong> của năm cấp quỹ, không cộng dần theo tháng. Sang bậc mới giữa năm thì bậc đó áp cho quỹ năm sau.</p>
<p>⚠️ Hồ sơ <strong>chưa có ngày vào làm</strong> thì thâm niên tính bằng <strong>0</strong> và quỹ thiếu ngày. Màn hình có cảnh báo riêng cho ca này — thấy nó thì báo phòng Nhân sự nhập bổ sung, đừng bỏ qua.</p>

<h2>Không có ứng phép</h2>
<p>Xin vượt quỹ bị <strong>chặn ngay lúc gửi duyệt</strong>, không phải chờ ai đó phát hiện. Hệ <strong>không ghi nợ phép</strong>. Muốn nghỉ thêm thì chọn loại <strong>«Nghỉ không lương»</strong> — câu chặn của hệ nói thẳng đường đó.</p>
<p>Ghi nợ nghe thì tiện nhưng kéo theo cả một sổ công nợ phép và luật trừ lương khi nghỉ việc, nên bản này cố ý không làm.</p>

<h2>Thấy số sai thì hỏi ai</h2>
<p>Số không khớp thực tế (thiếu ngày thâm niên, quên chuyển phép tồn, cấp nhầm) là việc của {ref(NS_QUY, "phòng Nhân sự")} — họ điều chỉnh tay được và mọi lần điều chỉnh đều lưu vết kèm lý do.</p>""",
        },
        {
            "title": THEO_DOI,
            "icon": "clipboard-list",
            "summary": "Ba tab, sáu trạng thái, bảng làm-được-gì, khác nhau giữa xóa và hủy",
            "content": f"""<h2>Theo dõi, sửa và hủy đơn nghỉ</h2>

<h2>Ba tab trong màn Đơn nghỉ phép</h2>
<table>
<thead><tr><th>Tab</th><th>Chứa gì</th></tr></thead>
<tbody>
<tr><td><strong>Cần tôi duyệt</strong></td><td>Đơn đang chờ chữ ký của bạn. Đứng <strong>đầu</strong> và <strong>tự được chọn khi có việc</strong>, kèm con số việc đang chờ. Không có quyền duyệt thì tab này rỗng.</td></tr>
<tr><td><strong>Đơn của tôi</strong></td><td>Đơn bạn nộp, <em>hoặc</em> đơn người khác nộp hộ bạn.</td></tr>
<tr><td><strong>Tôi đã duyệt</strong></td><td>Đơn bạn từng ký — <strong>chỉ 30 ngày gần đây</strong>. Mỗi đơn một dòng, kể cả khi bạn ký hai chặng của cùng tờ đơn.</td></tr>
</tbody>
</table>
<p>Con số trên tab <em>Cần tôi duyệt</em> chỉ hiện khi khác 0. Tab đang chọn nằm trên đường dẫn, nên <strong>copy link gửi cho người khác</strong> là họ mở đúng tab bạn đang xem, và nút Back của trình duyệt chạy đúng.</p>
<p>Màn tự nhảy sang <em>Cần tôi duyệt</em> <strong>một lần duy nhất lúc mới mở</strong>. Sau đó bạn đang xem tab nào thì ở yên tab đó, dù có việc mới về.</p>

<h2>Tìm một tờ đơn</h2>
<ul>
<li>Ô tìm khớp <strong>tên người nghỉ · số đơn · lý do</strong> — ba thứ người ta thường nhớ về một tờ đơn.</li>
<li>Hai ô lọc: <strong>Lọc theo loại nghỉ</strong> và <strong>Lọc theo trạng thái</strong>.</li>
<li>Cột bảng: <em>Số đơn · Trạng thái · Người nghỉ · Loại nghỉ · Từ ngày · Đến ngày · Số ngày</em>. Tab <em>Cần tôi duyệt</em> có thêm <em>Việc của tôi</em> và <strong>Hạn xử lý</strong>.</li>
</ul>

<h2>Sáu trạng thái</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Nghĩa là</th><th>Quỹ phép</th></tr></thead>
<tbody>
<tr><td><strong>Nháp</strong></td><td>Chưa ai thấy. Sửa thoải mái.</td><td>Chưa trừ</td></tr>
<tr><td><strong>Chờ duyệt</strong></td><td>Đang trong luồng, đã khóa sửa.</td><td><strong>Đang giữ chỗ</strong></td></tr>
<tr><td><strong>Đã duyệt</strong></td><td>Xong. Hệ tự sinh Giấy nghỉ phép bên Văn thư.</td><td>Trừ thật</td></tr>
<tr><td><strong>Trả về chỉnh sửa</strong></td><td>Người duyệt <strong>mời bạn sửa rồi gửi lại chính tờ đơn đó</strong>.</td><td>Trả lại</td></tr>
<tr><td><strong>Từ chối</strong></td><td><strong>Khóa hẳn.</strong> Muốn nghỉ nữa thì lập <strong>đơn khác</strong>.</td><td>Trả lại</td></tr>
<tr><td><strong>Đã hủy</strong></td><td>Bạn tự rút.</td><td>Trả lại</td></tr>
</tbody>
</table>
<p>⚠️ <strong>«Từ chối» khác «Trả về chỉnh sửa»</strong> — một cái là dẹp, một cái là mời sửa. Hai chữ giống nhau về cảm giác nhưng khác hẳn về việc bạn phải làm tiếp. Đọc kỹ ô lý do người duyệt ghi; lý do luôn hiện trên dòng thời gian của đơn.</p>

<h2>Ở trạng thái nào thì làm được gì</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Sửa</th><th>Xóa đơn</th><th>Gửi duyệt</th><th>Hủy đơn</th></tr></thead>
<tbody>
<tr><td>Nháp</td><td>Được</td><td>Được</td><td>Được</td><td>—</td></tr>
<tr><td>Trả về chỉnh sửa</td><td>Được</td><td>—</td><td>Được</td><td>Được</td></tr>
<tr><td>Chờ duyệt</td><td>Không</td><td>Không</td><td>Đã gửi rồi</td><td>Được</td></tr>
<tr><td>Đã duyệt</td><td>Không</td><td>Không</td><td>—</td><td><strong>Vẫn được</strong></td></tr>
<tr><td>Từ chối / Đã hủy</td><td>Không</td><td>Không</td><td>Không</td><td>—</td></tr>
</tbody>
</table>

<h2>Xóa đơn khác Hủy đơn</h2>
<ul>
<li><strong>Xóa đơn</strong> — chỉ với đơn <em>chưa vào luồng</em>. Tờ đơn biến khỏi danh sách như chưa từng có.</li>
<li><strong>Hủy đơn</strong> — tờ đơn <strong>ở lại</strong> với trạng thái <em>Đã hủy</em> kèm lý do. Đơn đã duyệt là hồ sơ, phải hủy chứ không xóa được.</li>
</ul>

<h2>Hủy đơn</h2>
<p>Bấm <strong>«Hủy đơn»</strong> ở màn chi tiết, hộp thoại <em>Hủy đơn nghỉ phép</em> hiện ra và <strong>bắt ghi lý do</strong> (gõ toàn dấu cách không tính là lý do). <strong>Hủy được cả khi đơn đã duyệt</strong> — đổi kế hoạch là chuyện thường, và ngày phép được hoàn lại.</p>
<p>Đơn đang chạy trong luồng thì hệ <strong>rút phiên duyệt trước rồi mới hủy</strong>, nên người duyệt không còn thấy việc đó nữa.</p>
<p>⚠️ <strong>Chỉ chính người nộp</strong> mới hủy được đơn đang nằm trong luồng. Người khác muốn chặn thì dùng <strong>Trả về</strong> hoặc <strong>Từ chối</strong> — hai nút đó có ô ghi lý do gửi về cho người nộp.</p>

<h2>Sửa rồi gửi lại</h2>
<p>Đơn bị <em>Trả về chỉnh sửa</em> thì mở ra, sửa đúng chỗ người duyệt nêu, bấm <strong>«Lưu nháp»</strong> rồi <strong>«Gửi duyệt»</strong> lần nữa. Đơn <strong>không</strong> bị đóng và <strong>giữ nguyên số đơn</strong> — người duyệt nhìn thấy đúng tờ họ đã trả về.</p>

<h2>Không thấy đơn mình đang tìm?</h2>
<p>Bạn chỉ đọc được đơn <strong>trong phạm vi dữ liệu</strong> của mình. Đơn ngoài phạm vi thì hệ báo «Không tìm thấy» — không có nghĩa là đơn đó không tồn tại, chỉ là bạn không được xem. Lý do nghỉ là chuyện riêng tư nên hệ cố ý chặt tay ở chỗ này.</p>
<p>Cần xem rộng hơn thì xin thêm phạm vi ở {ref(NS_QUYEN, "màn Phân quyền")}, đừng nhờ người khác chụp màn hình gửi qua.</p>""",
        },
        {
            "title": DUYET,
            "icon": "workflow",
            "summary": "Duyệt ngay trong màn Nghỉ phép, đọc gì trước khi ký, ba nút và hậu quả",
            "content": f"""<h2>Duyệt đơn nghỉ phép</h2>
<p>Dành cho người được giao ký. Bạn <strong>không phải sang màn Phê duyệt</strong> — duyệt ngay trong <strong>Nhân sự ▸ Nghỉ phép ▸ tab «Cần tôi duyệt»</strong>.</p>

<h2>Nhận việc</h2>
<ul>
<li>Có việc mới, bạn nhận <strong>thông báo chuông</strong> kèm liên kết mở thẳng tờ đơn.</li>
<li>Mở màn Nghỉ phép ra là tab <em>Cần tôi duyệt</em> <strong>tự được chọn</strong>, kèm con số việc đang chờ.</li>
<li>Cột <strong>Hạn xử lý</strong> cho biết việc này đến hạn khi nào; cột <strong>Việc của tôi</strong> nói bạn đang ở chặng nào.</li>
</ul>

<h2>Đọc gì trước khi ký</h2>
<p>Thẻ tóm tắt trên đầu trang chi tiết gom đủ bốn thứ để quyết mà không phải đi lục:</p>
<ol>
<li><strong>Loại nghỉ và số ngày</strong> — kèm số ngày còn lại của người xin.</li>
<li><strong>Khoảng ngày</strong> — kèm buổi, nếu khác «cả ngày».</li>
<li><strong>Lý do nghỉ</strong>.</li>
<li><strong>Bàn giao công việc</strong> — mục này <strong>luôn hiện, kể cả khi trống</strong>, và khi trống thì nói thẳng <em>«Người nộp chưa khai ai nhận bàn giao trong thời gian nghỉ.»</em></li>
</ol>
<p>⚠️ Mục bàn giao luôn hiện là <strong>cố ý</strong>: người duyệt phải phân biệt được <em>"người nộp chưa khai ai"</em> với <em>"màn hình thiếu mục đó"</em>. Mà thiếu người bàn giao chính là <strong>lý do trả đơn phổ biến nhất</strong> — nó phải nói thành lời, không để suy ra từ một khoảng trống.</p>
<p>Bên dưới là <strong>dòng thời gian duyệt</strong>: ai đã ký chặng nào, lúc mấy giờ, ghi ý kiến gì.</p>

<h2>Ba nút</h2>
<table>
<thead><tr><th>Nút</th><th>Dùng khi</th><th>Hậu quả</th></tr></thead>
<tbody>
<tr><td><strong>Duyệt</strong></td><td>Đồng ý</td><td>Sang chặng sau, hoặc xong hẳn nếu là chặng cuối. Xong thì <strong>trừ quỹ thật</strong> và <strong>sinh Giấy nghỉ phép</strong>.</td></tr>
<tr><td><strong>Trả về</strong></td><td>Đơn thiếu thông tin, sửa là được</td><td>Người nộp <strong>sửa rồi gửi lại chính tờ đó</strong>. Phép được trả lại. Đơn <strong>không</strong> đóng.</td></tr>
<tr><td><strong>Từ chối</strong></td><td>Không cho nghỉ</td><td><strong>Đóng hẳn</strong> — người nộp phải lập đơn khác. Phép được trả lại.</td></tr>
</tbody>
</table>
<p><strong>Duyệt</strong> không bắt ghi lý do, ô ý kiến để trống cũng bấm được. <strong>Trả về</strong> và <strong>Từ chối</strong> thì <strong>bắt buộc</strong> — nút không bấm được cho tới khi có chữ, và gõ toàn dấu cách không tính. Người nhận chỉ đọc được đúng dòng bạn ghi, nên viết cho rõ phải sửa gì:</p>
<ul>
<li><em>«Thiếu người bàn giao, bổ sung rồi gửi lại.»</em> — trả về</li>
<li><em>«Trùng lịch nghỉ của cả phòng, dời sang tuần sau.»</em> — từ chối</li>
</ul>

<h2>Bốn điều đáng biết</h2>
<ul>
<li><strong>Đang có việc trên tờ đơn thì bạn đọc được nó</strong>, kể cả khi phạm vi dữ liệu của bạn không với tới — thường gặp với trưởng phòng Nhân sự ký chặng 2 cho nhân viên phòng khác. <strong>Ký xong quyền đó đóng lại</strong>; muốn xem lại thì vào tab <strong>Tôi đã duyệt</strong> (30 ngày gần đây).</li>
<li><strong>Người nộp không tự duyệt đơn của mình</strong> — hệ loại họ khỏi danh sách người ký. Vì vậy mỗi chặng đều phải khai <strong>người dự phòng</strong>, nếu không thì trưởng phòng tự xin nghỉ sẽ không có ai ký và đơn kẹt.</li>
<li>Chỗ nào <strong>chưa khai luồng duyệt</strong> thì người có quyền duyệt bấm <strong>«Duyệt đơn»</strong> thẳng trên đơn. Đơn <em>đang</em> chạy trong luồng thì đường tắt đó bị chặn — không chặn là mở một lối đi vòng qua cả luồng.</li>
<li>Duyệt xong <strong>không rút lại được</strong>. Cần chặn một đơn đã duyệt thì bảo người nộp <strong>hủy đơn</strong>, phép sẽ được hoàn.</li>
</ul>
<p>Cách khai luồng: {ref(NS_QUYEN, "bài Phân quyền và luồng duyệt")}.</p>""",
        },
        {
            "title": LICH_NGHI,
            "icon": "users",
            "summary": "Ba chế độ ngày / tuần / tháng, cách lọc, và lịch KHÔNG hiện đơn nào",
            "content": f"""<h2>Xem Lịch nghỉ</h2>
<p>Tab <strong>Lịch nghỉ</strong> trong <strong>Nhân sự ▸ Nghỉ phép</strong> — trả lời câu <em>«tuần sau ai nghỉ»</em> mà không phải mở từng tờ đơn.</p>

<h2>Thanh điều khiển</h2>
<ul>
<li>Cụm ba nút liền nhau: <strong>lùi</strong> · <strong>Hôm nay</strong> · <strong>tiến</strong>.</li>
<li>Ô chọn <strong>Tháng</strong> và <strong>Năm</strong> để nhảy xa.</li>
<li>Bộ chọn chế độ ở bên phải: <strong>Ngày · Tuần · Tháng</strong>.</li>
</ul>

<h2>Ba chế độ</h2>
<table>
<thead><tr><th>Chế độ</th><th>Thấy gì</th><th>Dùng khi</th></tr></thead>
<tbody>
<tr><td><strong>Ngày</strong></td><td>Danh sách người nghỉ hôm đó, kèm loại nghỉ và vị trí trong đợt (<em>ngày đầu · đang giữa đợt · ngày cuối</em>). Có ô tìm tên và ô lọc loại nghỉ.</td><td>Sáng ra muốn biết hôm nay vắng ai</td></tr>
<tr><td><strong>Tuần</strong></td><td>Bảy ngày từ thứ Hai, mỗi ngày một cột người nghỉ.</td><td>Xếp lịch họp, phân ca</td></tr>
<tr><td><strong>Tháng</strong></td><td>Lưới 42 ô. Mỗi ô liệt kê vài người, quá thì gộp thành nút <strong>«+N người nữa»</strong> — bấm vào là mở <strong>đúng ngày đó</strong> ở chế độ Ngày.</td><td>Nhìn toàn cảnh, tránh dồn nghỉ</td></tr>
</tbody>
</table>
<p>Ô lọc loại nghỉ ở chế độ Ngày <strong>chỉ bày loại có mặt trong ngày đó</strong>, và <strong>tự ẩn khi cả ngày chỉ có một loại</strong> — một lựa chọn thì lọc được gì.</p>

<h2>Đọc lịch</h2>
<ul>
<li>Bấm vào một dòng để <strong>mở thẳng tờ đơn</strong>.</li>
<li><strong>Ngày lễ</strong> hiện tên lễ ngay trên ô của nó, kèm ghi chú là ngày đó không tính vào phép.</li>
<li>Không ai nghỉ thì lịch <strong>nói rõ</strong> («Không ai nghỉ ngày này.» / «Cả tuần này không ai nghỉ.») chứ không để bảng trống trơn — trống trơn thì không biết là không ai nghỉ hay là màn hình lỗi.</li>
<li>Tìm không ra ai khớp bộ lọc thì câu báo <strong>khác hẳn</strong> câu «không ai nghỉ», để bạn biết là do bộ lọc.</li>
</ul>

<h2>Lịch KHÔNG hiện những đơn nào</h2>
<p><strong>Nháp · Từ chối · Đã hủy</strong> — ba loại này không dẫn tới ai nghỉ cả, vẽ lên lịch chỉ làm người xem tưởng phòng vắng người.</p>

<h2>Phạm vi dữ liệu</h2>
<p>Lịch chỉ hiện đơn <strong>trong phạm vi dữ liệu của bạn</strong>: trưởng bộ phận thấy người trong bộ phận mình, nhân viên thường chỉ thấy đơn của chính mình. Thấy lịch trống trơn trong khi biết chắc có người nghỉ thì đó là phạm vi, không phải lỗi — xem {ref(NS_QUYEN, "bài Phân quyền")}.</p>""",
        },
        {
            "title": TINH_HUONG,
            "icon": "lightbulb",
            "summary": "Nghỉ ốm đột xuất, nửa buổi, cưới hỏi, thai sản, nghỉ quá quỹ, đổi ngày sau khi duyệt",
            "content": f"""<h2>Mười tình huống nghỉ thường gặp</h2>
<p>Mỗi ô dưới đây là một tình huống có thật, kèm cách làm đúng ngay lần đầu.</p>

<h3>1. Sáng ngủ dậy thấy ốm, chưa kịp xin phép</h3>
<p>Chọn loại <strong>Nghỉ ốm</strong> — loại này <strong>báo trước 0 ngày</strong>, nộp trong ngày vẫn được (không ai biết trước mai mình ốm). Nếu công ty bật yêu cầu giấy khám thì nộp bổ sung sau cho phòng Nhân sự.</p>

<h3>2. Chỉ nghỉ buổi chiều</h3>
<p><strong>Từ ngày = Đến ngày</strong>, <strong>Buổi bắt đầu = Buổi kết thúc = Buổi chiều</strong>. Tổng số ngày ra <strong>0,5</strong>.</p>
<p>Ngược lại, <em>chiều hôm nay đến sáng hôm nay</em> là khoảng trống — hệ chặn.</p>

<h3>3. Nghỉ dài hơn số phép còn lại</h3>
<p>Không có ứng phép. Tách làm <strong>hai đơn</strong>: một đơn <em>Phép năm</em> đúng bằng số còn lại, một đơn <strong>Nghỉ không lương</strong> cho phần dôi ra.</p>
<p>⚠️ Hai đơn <strong>không được chồng ngày</strong> — cùng một ngày nằm trên hai đơn là bị chặn. Chia theo ngày liền mạch: ví dụ 05–09/10 phép năm, 12–16/10 không lương.</p>

<h3>4. Nghỉ vắt qua cuối tuần hoặc ngày lễ</h3>
<p>Cứ chọn khoảng ngày thật (ví dụ thứ Sáu đến thứ Ba). Hệ <strong>tự trừ</strong> thứ Bảy, Chủ nhật và ngày lễ ra khỏi «Tổng số ngày» — bạn không phải cắt đơn làm đôi.</p>

<h3>5. Bộ phận làm cả thứ Bảy, hoặc chạy ca</h3>
<p>Máy trừ cuối tuần theo lịch hành chính, mà lịch thật của bạn khác. <strong>Gõ đè «Tổng số ngày»</strong> cho đúng số ngày công thực tế. Chú thích dưới ô sẽ đổi thành <em>«Bạn đang nhập tay…»</em> — người duyệt nhìn vào biết con số là do bạn khai.</p>

<h3>6. Cưới hỏi, tang chế</h3>
<p>Chọn đúng loại nghỉ tương ứng. Hai loại này thường có <strong>trần 3 ngày mỗi lần</strong> — xin 5 ngày là bị chặn ngay lúc gửi duyệt.</p>

<h3>7. Nghỉ thai sản</h3>
<ul>
<li>Phải <strong>báo trước 15 ngày</strong>.</li>
<li>Loại này <strong>không trừ</strong> cuối tuần và ngày lễ — nghỉ sáu tháng thì không ai bù cuối tuần, nên số ngày đếm tuốt.</li>
<li>Chỉ áp cho hồ sơ <strong>nữ</strong>. Hồ sơ <em>chưa khai giới tính</em> thì vẫn nộp được (chặn là khóa cả công ty tới khi nhập bù), nhưng hồ sơ khai là nam thì bị chặn.</li>
</ul>

<h3>8. Đã duyệt rồi nhưng phải đổi ngày</h3>
<p>Không sửa được tờ đơn cũ. Làm hai bước: <strong>Hủy đơn</strong> cũ (phép hoàn lại ngay) rồi <strong>nộp đơn mới</strong> với ngày đúng. Đừng nhờ người duyệt "sửa hộ" — họ cũng không sửa được.</p>

<h3>9. Sếp trả đơn về</h3>
<p>Mở đơn ra, đọc lý do trên dòng thời gian, sửa đúng chỗ đó, bấm <strong>Lưu nháp</strong> rồi <strong>Gửi duyệt</strong> lần nữa. Vẫn là tờ đơn cũ, vẫn số đơn cũ — <strong>đừng lập đơn mới</strong>, lập mới là người duyệt phải đọc lại từ đầu.</p>
<p>Bị <strong>Từ chối</strong> thì ngược lại: tờ đó đóng hẳn, muốn nghỉ thì <strong>phải</strong> lập đơn khác.</p>

<h3>10. Nghỉ đột xuất, người khác nộp hộ</h3>
<p>Hành chính mở form, điền <strong>người nghỉ</strong> vào ô riêng. Cả người lập lẫn người nghỉ đều thấy tờ đơn trong <em>Đơn của tôi</em>. Quỹ phép trừ vào <strong>người nghỉ</strong>, không phải người gõ.</p>

<p>Gặp câu chặn không hiểu thì tra ở {ref(BAO_LOI, "bài Gặp câu báo lỗi thì làm gì")}.</p>""",
        },
        {
            "title": BAO_LOI,
            "icon": "help",
            "summary": "Tra nguyên văn câu chặn của hệ thống, hiểu nó nói gì và làm gì tiếp",
            "content": f"""<h2>Gặp câu báo lỗi thì làm gì</h2>
<p>Hệ chặn là để bạn khỏi nghỉ sai rồi phải gỡ sau. Mỗi câu dưới đây nói đúng một việc — đọc rồi sửa, <strong>bấm lại lần nữa không giúp được gì</strong>.</p>

<h2>Lúc gửi duyệt</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Không đủ phép: «Phép năm» còn 3 ngày, đơn này xin 5 ngày. Muốn nghỉ tiếp thì chọn loại «Nghỉ không lương».»</em></td><td>Xin vượt quỹ. Hệ không ghi nợ phép.</td><td>Giảm số ngày, hoặc tách phần dôi ra thành đơn <strong>Nghỉ không lương</strong>.</td></tr>
<tr><td><em>«Đã có đơn «NP012» nghỉ từ … đến … trùng khoảng ngày này.»</em></td><td>Bạn đã có một đơn còn hiệu lực chồng lên khoảng ngày này.</td><td>Mở đơn NP012 ra xem. Muốn gộp thì hủy nó rồi nộp một đơn dài; muốn tách thì dời ngày cho khỏi chồng.</td></tr>
<tr><td><em>«Thiếu «Lý do nghỉ» — nhập đủ trước khi gửi duyệt.»</em></td><td>Ô bắt buộc còn trống.</td><td>Điền rồi <strong>Lưu nháp</strong>, sau đó gửi duyệt lại.</td></tr>
<tr><td><em>«Phép năm» phải nộp trước ít nhất 3 ngày.»</em></td><td>Không đủ số ngày báo trước. Đếm từ <strong>hôm nay</strong>, không phải từ ngày bạn lập đơn.</td><td>Dời ngày nghỉ ra xa hơn, hoặc chọn loại nghỉ không đòi báo trước (Nghỉ ốm).</td></tr>
<tr><td><em>«Nghỉ cưới hỏi» chỉ cho nghỉ tối đa 3 ngày mỗi lần, đơn này xin 5.»</em></td><td>Vượt trần của loại nghỉ.</td><td>Cắt bớt, hoặc xin phần dôi bằng loại nghỉ khác.</td></tr>
<tr><td><em>«Loại nghỉ «Thai sản» không áp dụng cho hồ sơ này»</em></td><td>Loại nghỉ giới hạn theo giới tính, mà hồ sơ khai không khớp.</td><td>Hồ sơ khai sai thì báo phòng Nhân sự sửa; đúng thì chọn loại khác.</td></tr>
</tbody>
</table>

<h2>Lúc chọn ngày</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Đến ngày» phải bằng hoặc sau «Từ ngày»</em></td><td>Chọn ngược ngày.</td><td>Đổi lại hai ô.</td></tr>
<tr><td><em>«Nghỉ từ buổi chiều đến buổi sáng cùng ngày là khoảng trống»</em></td><td>Buổi bắt đầu là chiều, buổi kết thúc là sáng, cùng một ngày — không có khoảng nào.</td><td>Chọn cùng một buổi cho cả hai ô.</td></tr>
<tr><td><em>«Khoảng ngày này không có ngày làm việc nào (rơi trọn vào cuối tuần hoặc ngày lễ). Sửa lại ngày, hoặc nhập tay «Tổng số ngày».»</em></td><td>Cả khoảng bạn chọn đều là ngày nghỉ sẵn.</td><td>Không cần xin phép thì thôi. Bộ phận có làm ngày đó thì <strong>gõ đè Tổng số ngày</strong>.</td></tr>
<tr><td><em>«Tổng số ngày» phải lớn hơn 0</em></td><td>Bạn xóa trắng hoặc gõ 0 vào ô số ngày.</td><td>Nhập số đúng, hoặc xóa ô để hệ tính lại.</td></tr>
</tbody>
</table>

<h2>Lúc sửa hoặc gửi lại</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Đơn đã gửi duyệt nên không sửa được. Rút phiếu duyệt hoặc hủy đơn…»</em></td><td>Đơn đang trong luồng, đã khóa.</td><td><strong>Hủy đơn</strong> rồi nộp lại, hoặc nhờ người duyệt <strong>Trả về</strong> để sửa mà giữ nguyên số đơn.</td></tr>
<tr><td><em>«Đơn này đã gửi duyệt rồi»</em></td><td>Bấm «Gửi duyệt» hai lần.</td><td>Không phải lỗi. Tải lại trang là thấy trạng thái <em>Chờ duyệt</em>.</td></tr>
</tbody>
</table>

<h2>Lỗi về tài khoản</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>«Chưa xác định được người nghỉ — tài khoản này chưa gắn hồ sơ nhân sự.»</em></td><td>Tài khoản đăng nhập chưa nối với một hồ sơ nhân sự nào, nên hệ không biết trừ phép của ai.</td><td>Báo phòng Nhân sự gắn hồ sơ. Không tự sửa được.</td></tr>
<tr><td>Không thấy menu <strong>Nghỉ phép</strong>, hoặc thiếu tab</td><td>Phân quyền — bốn khóa quyền của Nghỉ phép là khóa mới, vai trò cũ không tự có.</td><td>Xin quản trị tick thêm, xem {ref(NS_QUYEN, "bài Phân quyền")}.</td></tr>
<tr><td>Hệ báo <em>«Không tìm thấy»</em> khi mở một tờ đơn</td><td>Đơn nằm ngoài <strong>phạm vi dữ liệu</strong> của bạn.</td><td>Xin mở rộng phạm vi, hoặc nhờ người trong phạm vi xử lý.</td></tr>
<tr><td>Cảnh báo <em>hồ sơ thiếu ngày vào làm</em></td><td>Không có ngày vào làm thì thâm niên tính bằng 0, quỹ <strong>thiếu ngày</strong>.</td><td>Báo phòng Nhân sự nhập bổ sung rồi cấp lại quỹ.</td></tr>
</tbody>
</table>

<p>Câu chặn không nằm trong bảng nào ở trên thì chụp màn hình gửi phòng Nhân sự — kèm <strong>số đơn</strong> và <strong>giờ bấm</strong>, hai thứ đó đủ để tra lại.</p>""",
        },
        {
            "title": NS_QUY,
            "icon": "coins",
            "summary": "Đọc bảng Quỹ phép năm, cấp quỹ đầu năm, điều chỉnh tay và dấu vết",
            "content": f"""<h2>Nhân sự — Cấp và điều chỉnh quỹ phép</h2>
<p>Tab <strong>Quỹ phép năm</strong> (khóa quyền <code>leave_balance</code>). Mỗi dòng là <strong>một người × một năm × một loại nghỉ</strong>.</p>

<h2>Đọc bảng</h2>
<table>
<thead><tr><th>Cột</th><th>Nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Nhân sự</strong></td><td>Người sở hữu dòng quỹ.</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Mỗi loại nghỉ có trừ quỹ là một dòng riêng.</td></tr>
<tr><td><strong>Hạn mức</strong></td><td>Chép từ danh mục Loại nghỉ tại lúc cấp phát.</td></tr>
<tr><td><strong>Thâm niên</strong></td><td>Cộng thêm theo bậc, tính tại 01/01.</td></tr>
<tr><td><strong>Chuyển năm trước</strong></td><td>Phép tồn mang sang.</td></tr>
<tr><td><strong>Điều chỉnh tay</strong></td><td>Cột duy nhất nhận <strong>số âm</strong>; số dương hiện kèm dấu <code>+</code>.</td></tr>
<tr><td><strong>Đã nghỉ</strong></td><td>Cộng dồn đơn đã duyệt.</td></tr>
<tr><td><strong>Còn lại</strong></td><td>Kết quả cuối. <strong>Hết phép thì tô đỏ</strong> — đó là thứ cần thấy ngay.</td></tr>
</tbody>
</table>
<p>Bộ lọc: ô tìm theo <strong>tên hoặc mã nhân sự</strong>, ô chọn <strong>loại nghỉ</strong>, ô chọn <strong>năm</strong>.</p>

<h2>Cấp quỹ đầu năm</h2>
<p>Nút <strong>«Cấp quỹ năm 2026»</strong> ở góc trên bên phải (con số đổi theo năm đang chọn). Bảng rỗng thì chính câu trạng thái rỗng đã chỉ đường: <em>«Chưa cấp quỹ phép năm 2026. Bấm «Cấp quỹ năm 2026» để tạo.»</em></p>
<ul>
<li><strong>Chạy lại được</strong>: chỉ tạo dòng còn thiếu. Bấm hai lần không nhân đôi.</li>
<li>Thêm người giữa năm thì <strong>bấm lại</strong> là họ có quỹ, không phải tạo tay.</li>
<li>Cấp <strong>một lần đầu năm</strong>; thâm niên tính tại 01/01, không cộng dần theo tháng.</li>
</ul>
<p>⚠️ Cố ý <strong>không cập nhật dòng đã có</strong> theo hạn mức mới: đổi hạn mức giữa năm thì quỹ đã cấp giữ nguyên, luật mới áp cho lần cấp sau. Muốn áp ngay cho vài người thì dùng <strong>điều chỉnh tay</strong>.</p>
<p>⚠️ Cấp quỹ <strong>trước khi</strong> hồ sơ có <strong>ngày vào làm</strong> thì thâm niên ra 0. Nhập bù ngày vào làm rồi phải sửa lại bằng điều chỉnh tay — cấp lại không sửa dòng cũ.</p>

<h2>Điều chỉnh tay</h2>
<p>Mở một dòng quỹ ra, dùng thẻ <strong>Điều chỉnh tay</strong>: nhập số và <strong>lý do</strong>, bấm <strong>«Lưu điều chỉnh»</strong>.</p>
<ul>
<li>⚠️ <strong>GHI ĐÈ, không cộng dồn.</strong> Ô nạp sẵn số của lần chỉnh trước; bạn gõ con số bạn muốn nó <em>thành</em>. Cộng dồn thì bấm Lưu hai lần là gấp đôi.</li>
<li>Thẻ nói trước <strong>«còn lại» sẽ thành bao nhiêu</strong> sau khi lưu — đọc dòng đó rồi hãy bấm.</li>
<li><strong>Bắt buộc có lý do</strong>, khoảng trắng không tính. Đây là thao tác <em>tặng ngày phép cho người khác</em> nên phải để lại dấu vết đọc được: <em>«Bù phép tồn 2025»</em>, <em>«Cấp nhầm, trừ lại»</em>.</li>
<li>Nhận <strong>số âm</strong> để trừ bớt.</li>
</ul>
<p>Trang chi tiết có khối <strong>Lịch sử thao tác</strong> — nhìn con số hiện tại không biết ai đưa nó tới đó, nên <strong>đọc lịch sử trước khi sửa tiếp</strong>. Chưa từng chỉnh tay thì khối đó không hiện dòng rỗng nào.</p>
<p>Trang chi tiết cũng liệt kê <strong>các đơn nghỉ</strong> đã ăn vào dòng quỹ này, để đối chiếu khi người dùng kêu sai số.</p>

<h2>Người dùng kêu «số phép của tôi sai»</h2>
<ol>
<li>Mở dòng quỹ của họ, đọc <strong>đủ sáu số cấu thành</strong> — thường lệch ở <em>thâm niên</em> (thiếu ngày vào làm) hoặc <em>chuyển năm trước</em>.</li>
<li>Xem khối <strong>các đơn nghỉ</strong>: phần <em>đang chờ duyệt</em> cũng đã bị trừ, và người dùng hay quên điều này — xem {ref(QUY_PHEP, "bài Hiểu số ngày phép còn lại")}.</li>
<li>Vẫn sai thì <strong>điều chỉnh tay</strong> kèm lý do nói rõ vì sao.</li>
</ol>""",
        },
        {
            "title": NS_DANH_MUC,
            "icon": "settings",
            "summary": "Khai luật cho từng loại nghỉ, bảng bậc thâm niên, và cái bẫy Tết Âm lịch",
            "content": f"""<h2>Nhân sự — Loại nghỉ, bậc thâm niên và Lịch ngày lễ</h2>
<p>Hai màn nằm trong tab <strong>Thiết lập</strong>. Đây là nơi <strong>đổi luật bằng dữ liệu</strong> — không phải sửa mã, không phải chờ bản cập nhật.</p>

<h2>Thiết lập ▸ Loại nghỉ</h2>
<p>Nút <strong>Thêm</strong> mở <strong>một trang riêng</strong> chứ không mở hộp thoại, vì form dài và còn kèm bảng bậc thâm niên.</p>
<table>
<thead><tr><th>Ô</th><th>Quyết định điều gì</th></tr></thead>
<tbody>
<tr><td><strong>Có trừ quỹ</strong></td><td>Tắt thì loại nghỉ đó không giới hạn số ngày, và màn nộp đơn nói thẳng «không giới hạn» thay vì hiện số 0.</td></tr>
<tr><td><strong>Hạn mức</strong></td><td>Số ngày cấp cho một năm (Phép năm 12…).</td></tr>
<tr><td><strong>Số ngày báo trước</strong></td><td>So với <strong>hôm nay</strong>, không phải ngày lập đơn. Nghỉ ốm phải để <strong>0</strong>.</td></tr>
<tr><td><strong>Trần mỗi lần</strong></td><td>Cưới hỏi, tang chế thường 3. Đặt <strong>0</strong> = không giới hạn.</td></tr>
<tr><td><strong>Trừ cuối tuần / ngày lễ</strong></td><td>Bật thì T7·CN·lễ không tính vào số ngày. ⚠️ <strong>Thai sản phải TẮT</strong> — nghỉ sáu tháng thì không ai bù cuối tuần.</td></tr>
<tr><td><strong>Chỉ áp cho giới tính</strong></td><td>Thai sản → nữ. Hồ sơ <strong>chưa khai giới tính vẫn nộp được</strong> — chặn là khóa cả công ty tới khi nhập bù.</td></tr>
<tr><td><strong>Bắt đính kèm</strong></td><td>Cờ đã có sẵn cho Nghỉ ốm; phần đính kèm trên đơn còn đang làm.</td></tr>
<tr><td><strong>Cho chuyển sang năm sau</strong></td><td>Mặc định <strong>tắt</strong>. Bật thì cột <em>Chuyển năm trước</em> mới có số.</td></tr>
</tbody>
</table>
<p>⚠️ <strong>Đừng xóa một loại nghỉ đang có đơn.</strong> Ngừng dùng nó thì bỏ tick <em>đang dùng</em> — đơn cũ vẫn đọc được, còn người mới thì không chọn được nữa.</p>

<h2>Tab Bậc thâm niên</h2>
<p>Nằm ngay trong màn Loại nghỉ. Mỗi dòng là <em>làm đủ N năm thì cộng thêm M ngày</em>. Bộ mặc định: <strong>5→+1 · 10→+2 · 15→+3 · 20→+4</strong>.</p>
<p>⚠️ Hệ lấy <strong>bậc cao nhất khớp được, KHÔNG cộng dồn</strong>. Khai bậc theo lối cộng dồn (5→+1, 10→+1, 15→+1) thì người 15 năm chỉ được +1, không phải +3.</p>
<p>Công ty đổi sang bậc không đều thì <strong>sửa bảng này</strong> — luật nằm ở dữ liệu chứ không nằm trong mã.</p>

<h2>Thiết lập ▸ Lịch ngày lễ</h2>
<p>Quyết định ngày nào <strong>không</strong> bị trừ vào phép của toàn công ty. Sai ở đây thì cả công ty bị trừ oan, mà không ai phát hiện ngay.</p>
<ul>
<li><strong>Không khai pháp nhân</strong> = áp cho <strong>mọi pháp nhân</strong>. Pháp nhân có lịch riêng thì thêm dòng của nó — hai nguồn được <strong>gộp</strong>, không loại trừ nhau.</li>
<li>Cờ <strong>lặp hằng năm</strong> chỉ dùng cho ngày <strong>cố định theo dương lịch</strong>: 01/01 · 30/4 · 01/5 · 02/9.</li>
</ul>
<p>⚠️ <strong>Cái bẫy lớn nhất của cả phân hệ:</strong> <strong>Tết Âm lịch và Giỗ Tổ trôi theo lịch âm</strong>, dương lịch mỗi năm một khác — <strong>không</strong> đánh dấu lặp hằng năm được, <strong>mỗi năm phải nhập lại bằng tay</strong>. Quên là cả công ty bị trừ phép vào những ngày nghỉ Tết. Đặt việc này vào lịch tháng 12 hằng năm.</p>
<p>Sửa lịch lễ <strong>không</strong> tính lại các đơn đã nộp — số ngày đã chốt trên tờ đơn. Sửa lễ sau khi người ta đã nộp thì phải rà lại đơn trong khoảng đó bằng tay.</p>""",
        },
        {
            "title": NS_QUYEN,
            "icon": "key-round",
            "summary": "Bốn khóa quyền, phạm vi dữ liệu, và cách khai luồng duyệt cho khỏi kẹt",
            "content": f"""<h2>Nhân sự — Phân quyền và luồng duyệt</h2>

<h2>Bốn khóa quyền — đừng gộp</h2>
<table>
<thead><tr><th>Khóa</th><th>Mở màn nào</th></tr></thead>
<tbody>
<tr><td><code>leave_request</code></td><td>Đơn nghỉ phép · Lịch nghỉ</td></tr>
<tr><td><code>leave_balance</code></td><td>Quỹ phép năm (cấp phát, <strong>điều chỉnh tay</strong>)</td></tr>
<tr><td><code>leave_type</code></td><td>Thiết lập ▸ Loại nghỉ (kèm bậc thâm niên)</td></tr>
<tr><td><code>holiday</code></td><td>Thiết lập ▸ Lịch ngày lễ</td></tr>
</tbody>
</table>
<p>Tách bốn vì <strong><code>leave_balance</code> ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai</strong>. Gộp nó với <code>leave_request</code> thì cho ai xem đơn của mình là cho họ tự cộng phép.</p>
<p>Có quyền <strong>một trong hai</strong> danh mục thì vẫn vào được tab <em>Thiết lập</em>; chỉ sửa được một danh mục thì hệ không dựng hàng tab con một mục.</p>

<h2>«Không thấy menu Nghỉ phép»</h2>
<p>⚠️ Gần như <strong>luôn</strong> là phân quyền. Bốn khóa trên là khóa <strong>mới</strong>, mà seed cố ý <strong>không ghi đè</strong> phân quyền đã chỉnh tay trên hệ đang chạy — nên vai trò cũ <strong>không tự có</strong> chúng.</p>
<p>Cách xử lý: vào <strong>Nhân sự ▸ Phân quyền tài khoản</strong>, tick bốn khóa cho đúng vai trò. (Quản trị hệ thống có thể chạy một lần với cờ đồng bộ cưỡng bức, nhưng cách đó ghi đè cả những chỉnh tay khác — cân nhắc.)</p>

<h2>Ai nên có gì</h2>
<table>
<thead><tr><th>Vai</th><th>Khóa</th><th>Hành động</th></tr></thead>
<tbody>
<tr><td>Nhân viên</td><td><code>leave_request</code></td><td>đọc · tạo · sửa · hủy</td></tr>
<tr><td>Trưởng bộ phận</td><td><code>leave_request</code></td><td>thêm <strong>duyệt</strong>, phạm vi tới bộ phận mình</td></tr>
<tr><td>Nhân sự phụ trách phép</td><td>đủ bốn khóa</td><td>vai trò mẫu <code>hr_leave</code>, không gán tự động cho ai</td></tr>
</tbody>
</table>

<h2>Phạm vi dữ liệu</h2>
<p>Quyền mở màn, <strong>phạm vi</strong> quyết định thấy được dòng nào.</p>
<ul>
<li><code>leave_request</code> là entity <strong>duy nhất</strong> khai cả <em>người lập</em> lẫn <em>người nghỉ</em> vào phạm vi «của mình» — vì hành chính lập hộ là việc có thật, và cả hai người đều phải thấy tờ đơn.</li>
<li><code>leave_balance</code> chỉ khai theo <em>người sở hữu dòng quỹ</em>. Nhân viên thường <strong>không</strong> vào tab Quỹ phép năm; họ xem số của mình ngay trên form nộp đơn.</li>
<li>Hai danh mục (<em>Loại nghỉ</em>, <em>Lịch ngày lễ</em>) là dữ liệu chung, không lọc theo phạm vi.</li>
</ul>
<p>Người duyệt <strong>không cần</strong> phạm vi rộng: đang có việc trên tờ đơn thì đọc được nó, ký xong quyền đó đóng lại. Nhờ vậy trưởng phòng Nhân sự ký chặng 2 cho nhân viên phòng khác mà không phải mở phạm vi toàn công ty.</p>

<h2>Luồng duyệt</h2>
<p>Khai ở phân hệ <strong>Phê duyệt</strong> cho loại chứng từ <em>Đơn nghỉ phép</em>. Luồng mẫu: <strong>trưởng bộ phận của người xin nghỉ → trưởng phòng Nhân sự</strong>.</p>
<ul>
<li>⚠️ <strong>Mỗi chặng PHẢI khai người dự phòng.</strong> Hệ loại người nộp khỏi danh sách người ký, nên trưởng phòng tự xin nghỉ thì chặng đó rỗng và <strong>đơn kẹt vĩnh viễn</strong> — mà quản lý thì cũng phải nghỉ phép.</li>
<li><strong>Chưa khai luồng nào thì vẫn nộp được</strong>: lúc đó người có quyền duyệt bấm <strong>«Duyệt đơn»</strong> thẳng ở màn chi tiết. Không có đường lùi này thì cài mới xong là không ai nghỉ nổi.</li>
<li>Đơn <em>đang</em> chạy trong luồng thì đường duyệt thẳng <strong>bị chặn</strong> — nếu không thì đó là lối đi vòng qua cả luồng.</li>
</ul>
<p>Cách ký và ý nghĩa ba nút: {ref(DUYET, "bài Duyệt đơn nghỉ phép")}.</p>

<h2>Dọn dữ liệu trước khi chạy thật</h2>
<ol>
<li><strong>Nhập ngày vào làm</strong> cho toàn bộ hồ sơ — thiếu là thâm niên bằng 0 và quỹ thiếu ngày.</li>
<li>Khai <strong>giới tính</strong> cho hồ sơ nữ nếu dùng loại nghỉ Thai sản.</li>
<li>Nhập <strong>Lịch ngày lễ</strong> của năm hiện tại, <strong>kể cả Tết Âm</strong> — xem {ref(NS_DANH_MUC, "bài Loại nghỉ và Lịch ngày lễ")}.</li>
<li>Rà lại <strong>hạn mức</strong> từng loại nghỉ, rồi mới bấm <strong>Cấp quỹ năm</strong> — xem {ref(NS_QUY, "bài Cấp và điều chỉnh quỹ phép")}.</li>
<li>Khai <strong>luồng duyệt</strong> kèm người dự phòng.</li>
<li>Tick <strong>bốn khóa quyền</strong> cho các vai trò.</li>
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
        print(f"Đã dựng cây Nghỉ phép: {total} bài (gốc id={root_id}, sort_order={next_order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
