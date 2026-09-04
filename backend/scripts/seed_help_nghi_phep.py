# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ NGHỈ PHÉP.

Dựng cây bài viết: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ") -> 6 bài
chia theo VAI TRÒ + TÁC VỤ. Nghỉ phép khác Diễn đàn ở chỗ ba nhóm người dùng
làm ba việc hoàn toàn khác nhau — người nộp đơn, người duyệt, và phòng Nhân sự
cấp quỹ — nên chia theo vai trước rồi mới tới tác vụ.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_nghi_phep.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/17-nghi-phep.md` và gói
tri thức trợ lý `app/modules/assistant/packs/40-nghi-phep.md`. Ba nơi lệch nhau
thì người dùng đọc một đằng, trợ lý trả lời một nẻo.
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
NHAN_SU = "Dành cho phòng Nhân sự"


TREE = {
    "title": ROOT_TITLE,
    "icon": "calendar",
    "summary": "Nộp đơn nghỉ phép, xem quỹ phép còn lại, duyệt đơn và cấp quỹ",
    "content": f"""<h2>Nghỉ phép là gì?</h2>
<p>Phân hệ để nhân viên <strong>nộp đơn nghỉ phép</strong>, người quản lý duyệt, và phòng Nhân sự cấp <strong>quỹ phép năm</strong>. Vào bằng menu <strong>Nhân sự ▸ Nghỉ phép</strong>.</p>
<h3>Bốn khu vực, chuyển bằng thanh tab</h3>
<ul>
<li><strong>Đơn nghỉ phép</strong> — nơi bạn nộp đơn, theo dõi đơn của mình và duyệt đơn của người khác.</li>
<li><strong>Lịch nghỉ</strong> — ai nghỉ ngày nào, xem theo ngày / tuần / tháng.</li>
<li><strong>Quỹ phép năm</strong> — số ngày phép của từng người từng năm.</li>
<li><strong>Thiết lập</strong> — Loại nghỉ và Lịch ngày lễ (dành cho phòng Nhân sự).</li>
</ul>
<p>Không thấy đủ bốn tab là do <strong>phân quyền</strong>, không phải lỗi — xem {ref(NHAN_SU, "bài dành cho phòng Nhân sự")}.</p>
<h3>Bốn khái niệm đừng lẫn</h3>
<table>
<thead><tr><th>Thứ</th><th>Là gì</th></tr></thead>
<tbody>
<tr><td><strong>Đơn nghỉ phép</strong></td><td>Chứng từ bạn nộp. Đây là thứ để xin nghỉ.</td></tr>
<tr><td><strong>Giấy nghỉ phép (GNP)</strong></td><td><strong>Văn bản</strong> bên phân hệ Văn thư, hệ <strong>tự sinh sau khi đơn đã duyệt</strong>. Là hồ sơ lưu sổ, không phải thứ để nộp.</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Danh mục: Phép năm, Nghỉ ốm, Thai sản, Nghỉ không lương…</td></tr>
<tr><td><strong>Quỹ phép</strong></td><td>Số ngày của <strong>một người × một năm × một loại nghỉ</strong>.</td></tr>
</tbody>
</table>
<p>⚠️ Muốn xin nghỉ thì <strong>nộp đơn</strong> ở đây, <strong>đừng</strong> vào Văn thư tạo «Giấy nghỉ phép» — làm tay ra một tờ giấy không gắn với quỹ phép nào.</p>
<h3>Đọc theo việc bạn cần làm</h3>
<p>{ref(NOP_DON, "Nộp đơn")} · {ref(QUY_PHEP, "hiểu quỹ phép")} · {ref(THEO_DOI, "sửa/hủy đơn")} · {ref(DUYET, "duyệt đơn")} · {ref(LICH_NGHI, "xem lịch nghỉ")} · {ref(NHAN_SU, "phòng Nhân sự")}.</p>""",
    "children": [
        {
            "title": NOP_DON,
            "icon": "file-text",
            "summary": "Điền đơn, khai bàn giao công việc, gửi duyệt",
            "content": f"""<h2>Nộp đơn nghỉ phép</h2>
<h3>Mở đơn mới</h3>
<p>Vào <strong>Nhân sự ▸ Nghỉ phép</strong>, tab <strong>Đơn nghỉ phép</strong>, bấm nút <strong>Nộp đơn</strong> ở góc trên bên phải.</p>
<h3>Điền đơn</h3>
<ul>
<li><strong>Loại nghỉ</strong> — chọn trước, vì mỗi loại có luật riêng (số ngày báo trước, trần mỗi lần, có trừ quỹ hay không). Chọn xong, ô bên cạnh hiện luôn <strong>số ngày còn lại</strong> của loại đó.</li>
<li><strong>Từ ngày / Đến ngày</strong> và <strong>buổi</strong> (cả ngày, sáng, chiều). Nghỉ nửa ngày thì chọn buổi.</li>
<li><strong>Số ngày nghỉ</strong> — hệ tự tính và <strong>đã trừ thứ Bảy, Chủ nhật và ngày lễ</strong>. Bạn <strong>sửa đè được</strong> con số này khi lịch làm việc thật có ngoại lệ (ca kíp, nghỉ bù, công trường chạy Chủ nhật).</li>
<li><strong>Lý do</strong> — người duyệt đọc dòng này để quyết định, viết cho rõ.</li>
<li><strong>Bàn giao công việc</strong> — khai ai gánh việc thay bạn, việc gì. <strong>Thiếu người bàn giao là lý do bị trả đơn phổ biến nhất</strong>, nên khai luôn cho đỡ mất một vòng.</li>
</ul>
<h3>Lưu nháp hay gửi duyệt?</h3>
<ul>
<li><strong>Lưu nháp</strong> — cất tạm, chưa ai thấy, chưa trừ phép. Sửa lại lúc nào cũng được.</li>
<li><strong>Gửi duyệt</strong> — đẩy đơn vào luồng duyệt. <strong>Từ lúc này số ngày phép còn lại đã bị trừ</strong> (xem {ref(QUY_PHEP, "bài về quỹ phép")}) và <strong>đơn khóa, không sửa được nữa</strong>.</li>
</ul>
<p>Hệ chỉ kiểm "nhập đủ" ở bước <strong>gửi duyệt</strong>, không kiểm lúc lưu nháp — cứ lưu nháp thoải mái rồi hoàn thiện sau.</p>
<h3>Những chỗ hay bị chặn</h3>
<ul>
<li><strong>Xin quá số ngày còn lại</strong> — bị chặn. Không có ứng phép, không ghi nợ. Muốn nghỉ tiếp thì chọn loại <strong>«Nghỉ không lương»</strong>.</li>
<li><strong>Hai đơn chồng ngày</strong> của cùng một người — bị chặn, vì cùng một ngày sẽ bị trừ phép hai lần.</li>
<li><strong>Nghỉ từ buổi chiều đến buổi sáng cùng ngày</strong> — đó là khoảng trống, hệ chặn.</li>
<li><strong>Báo trước không đủ</strong> — phép năm thường phải báo trước 3 ngày, thai sản 15 ngày. Nghỉ ốm <strong>không</strong> phải báo trước (không ai biết trước mai mình ốm) nhưng có thể phải đính kèm giấy khám bệnh.</li>
<li><strong>Cưới hỏi và tang chế</strong> tối đa 3 ngày mỗi lần.</li>
</ul>
<h3>Nộp hộ người khác</h3>
<p>Hành chính hoặc trợ lý <strong>nộp hộ được</strong>: điền người nghỉ vào ô riêng trên đơn. Cả người lập lẫn người nghỉ đều thấy tờ đơn đó trong danh sách của mình.</p>
<p>Nộp xong thì theo dõi ở {ref(THEO_DOI, "bài Theo dõi, sửa và hủy đơn")}.</p>""",
        },
        {
            "title": QUY_PHEP,
            "icon": "wallet",
            "summary": "Công thức, vì sao vừa nộp đơn đã thấy hụt ngày, thâm niên",
            "content": f"""<h2>Hiểu số ngày phép còn lại</h2>
<p>Số ngày còn lại hiện ở <strong>hai chỗ</strong>: ô ngay cạnh «Loại nghỉ» khi bạn đang điền đơn, và thẻ <strong>Quỹ phép của tôi</strong>. Đừng tự cộng trừ ở nhà — hệ tính theo công thức dưới đây.</p>
<h3>Công thức</h3>
<pre>còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay)
          − đã nghỉ − đang chờ duyệt</pre>
<h3>Vì sao vừa nộp đơn đã thấy hụt ngày?</h3>
<p><strong>«Đang chờ duyệt» ĐÃ bị trừ khỏi «còn lại».</strong> Nộp đơn 3 ngày là số còn lại tụt ngay 3 ngày, chưa cần ai duyệt. Đây là <strong>cố ý</strong>: không giữ chỗ như vậy thì nộp mười đơn liền tay đều lọt qua chốt kiểm.</p>
<p>Đơn bị <strong>từ chối</strong>, bị <strong>trả về chỉnh sửa</strong> hay bạn <strong>tự hủy</strong> thì số ngày được <strong>trả lại ngay</strong>.</p>
<h3>Thâm niên</h3>
<p>Cộng thêm theo bảng bậc, mặc định: <strong>5 năm +1 · 10 năm +2 · 15 năm +3 · 20 năm trở lên +4</strong>. Lấy <strong>bậc cao nhất khớp được</strong>, <strong>không cộng dồn</strong> — làm 10 năm được +2 ngày, không phải +3.</p>
<p>⚠️ Hồ sơ <strong>chưa có ngày vào làm</strong> thì thâm niên tính bằng <strong>0</strong> và quỹ có thể thiếu ngày. Màn hình có cảnh báo — báo phòng Nhân sự nhập bổ sung.</p>
<h3>Không có ứng phép</h3>
<p>Xin vượt quỹ là <strong>bị chặn ngay lúc gửi duyệt</strong>, không phải chờ ai đó phát hiện. Hệ không ghi nợ phép. Nghỉ thêm thì chọn loại <strong>«Nghỉ không lương»</strong>.</p>
<p>Số ngày sai so với thực tế thì đó là việc của {ref(NHAN_SU, "phòng Nhân sự")} — họ điều chỉnh tay được.</p>""",
        },
        {
            "title": THEO_DOI,
            "icon": "clipboard-list",
            "summary": "Ba tab của màn Đơn, sáu trạng thái, khi nào sửa được, cách hủy",
            "content": f"""<h2>Theo dõi, sửa và hủy đơn nghỉ</h2>
<h3>Ba tab trong màn Đơn nghỉ phép</h3>
<ul>
<li><strong>Cần tôi duyệt</strong> — đơn đang chờ chữ ký của bạn. Tab này <strong>đứng đầu và tự được chọn</strong> khi có việc, kèm con số việc đang chờ. Không có quyền duyệt thì tab này rỗng.</li>
<li><strong>Đơn của tôi</strong> — đơn bạn nộp, hoặc đơn người khác nộp hộ bạn.</li>
<li><strong>Tôi đã duyệt</strong> — đơn bạn từng ký, để xem lại. Mỗi đơn một dòng, kể cả khi bạn ký hai chặng.</li>
</ul>
<h3>Sáu trạng thái</h3>
<table>
<thead><tr><th>Trạng thái</th><th>Nghĩa là</th></tr></thead>
<tbody>
<tr><td><strong>Nháp</strong></td><td>Chưa ai thấy, chưa trừ phép. Sửa thoải mái.</td></tr>
<tr><td><strong>Chờ duyệt</strong></td><td>Đang trong luồng. <strong>Đã trừ phép</strong>, đã khóa sửa.</td></tr>
<tr><td><strong>Đã duyệt</strong></td><td>Xong. Hệ tự sinh Giấy nghỉ phép bên Văn thư.</td></tr>
<tr><td><strong>Trả về chỉnh sửa</strong></td><td>Người duyệt <strong>mời bạn sửa rồi gửi lại</strong> chính tờ đơn đó. Phép được trả lại.</td></tr>
<tr><td><strong>Từ chối</strong></td><td><strong>Khóa hẳn.</strong> Muốn nghỉ nữa thì lập <strong>đơn khác</strong>. Phép được trả lại.</td></tr>
<tr><td><strong>Đã hủy</strong></td><td>Bạn tự rút. Phép được trả lại.</td></tr>
</tbody>
</table>
<p>⚠️ <strong>«Từ chối» khác «Trả về chỉnh sửa»</strong> — một cái là dẹp, một cái là mời sửa. Đọc kỹ ô lý do người duyệt ghi.</p>
<h3>Sửa đơn</h3>
<p><strong>Chỉ sửa được ở «Nháp» và «Trả về chỉnh sửa».</strong> Đã gửi duyệt là khóa. Muốn đổi thì hủy đơn rồi lập lại, hoặc nhờ người duyệt trả về.</p>
<h3>Hủy đơn</h3>
<p>Bấm <strong>Hủy đơn</strong> ở màn chi tiết. <strong>Hủy được cả khi đơn đã duyệt</strong> — đổi kế hoạch là chuyện thường, và ngày phép được hoàn lại.</p>
<p>⚠️ <strong>Chỉ chính người nộp</strong> mới hủy được đơn đang nằm trong luồng duyệt. Người khác muốn chặn thì dùng <strong>Trả về</strong> hoặc <strong>Từ chối</strong> — hai nút đó có ô ghi lý do, còn hủy thì không.</p>
<h3>Không thấy đơn mình đang tìm?</h3>
<p>Bạn chỉ đọc được đơn <strong>trong phạm vi dữ liệu</strong> của mình. Đơn ngoài phạm vi thì hệ báo «Không tìm thấy» — không có nghĩa là đơn đó không tồn tại, chỉ là bạn không được xem. Lý do nghỉ là chuyện riêng tư, hệ cố ý chặt tay ở chỗ này.</p>""",
        },
        {
            "title": DUYET,
            "icon": "workflow",
            "summary": "Duyệt ngay trong màn Nghỉ phép, ba nút và khi nào dùng nút nào",
            "content": f"""<h2>Duyệt đơn nghỉ phép</h2>
<p>Dành cho người được giao ký. Bạn <strong>không phải sang màn Phê duyệt</strong> — duyệt ngay trong <strong>Nhân sự ▸ Nghỉ phép ▸ tab «Cần tôi duyệt»</strong>.</p>
<h3>Đọc gì trước khi ký</h3>
<ul>
<li><strong>Loại nghỉ và số ngày</strong> — cùng với số ngày còn lại của người xin.</li>
<li><strong>Lý do</strong>.</li>
<li><strong>Bàn giao công việc</strong> — mục này <strong>luôn hiện, kể cả khi trống</strong>. Trống nghĩa là người nộp <strong>chưa khai ai</strong>, không phải màn hình thiếu mục. Đây là lý do trả đơn phổ biến nhất nên nó phải nói thành lời.</li>
<li><strong>Luồng duyệt</strong> — cột chữ cho biết đơn đang ở chặng mấy trên mấy.</li>
</ul>
<h3>Ba nút</h3>
<table>
<thead><tr><th>Nút</th><th>Dùng khi</th><th>Hậu quả</th></tr></thead>
<tbody>
<tr><td><strong>Duyệt</strong></td><td>Đồng ý</td><td>Sang chặng sau, hoặc xong hẳn nếu là chặng cuối. Xong thì trừ quỹ thật và sinh Giấy nghỉ phép.</td></tr>
<tr><td><strong>Trả về</strong></td><td>Đơn thiếu thông tin, sửa là được</td><td>Người nộp <strong>sửa rồi gửi lại chính tờ đó</strong>. Phép được trả lại.</td></tr>
<tr><td><strong>Từ chối</strong></td><td>Không cho nghỉ</td><td><strong>Khóa hẳn</strong>, người nộp phải lập đơn khác. Phép được trả lại.</td></tr>
</tbody>
</table>
<p>Cả <strong>Trả về</strong> và <strong>Từ chối</strong> đều có ô ghi lý do — người nhận chỉ đọc được dòng đó, viết cho rõ.</p>
<h3>Vài điều đáng biết</h3>
<ul>
<li><strong>Đang có việc trên tờ đơn thì bạn đọc được nó</strong>, kể cả khi phạm vi dữ liệu của bạn không với tới (thường gặp với trưởng phòng Nhân sự ký chặng 2 cho nhân viên phòng khác). <strong>Ký xong quyền đó đóng lại</strong> — muốn xem lại thì vào tab <strong>Tôi đã duyệt</strong>.</li>
<li><strong>Người nộp không tự duyệt đơn của mình</strong> — hệ loại họ khỏi danh sách người ký. Vì vậy mỗi chặng đều phải khai <strong>người dự phòng</strong>, nếu không thì trưởng phòng tự xin nghỉ sẽ không có ai ký.</li>
<li>Chỗ nào <strong>chưa khai luồng duyệt</strong> thì người có quyền duyệt bấm <strong>Duyệt</strong> thẳng trên đơn. Đơn đang chạy trong luồng thì đường đó bị chặn.</li>
<li>Có việc mới, bạn nhận <strong>thông báo chuông</strong> kèm liên kết mở thẳng tờ đơn.</li>
</ul>""",
        },
        {
            "title": LICH_NGHI,
            "icon": "users",
            "summary": "Xem ai nghỉ ngày nào theo ngày / tuần / tháng",
            "content": """<h2>Xem Lịch nghỉ</h2>
<p>Tab <strong>Lịch nghỉ</strong> trong <strong>Nhân sự ▸ Nghỉ phép</strong> — trả lời câu «tuần sau ai nghỉ» mà không phải mở từng tờ đơn.</p>
<ul>
<li>Ba chế độ: <strong>ngày · tuần · tháng</strong>, chọn năm ở đầu trang.</li>
<li>Chế độ <strong>ngày</strong> có ô tìm tên và bộ lọc theo loại nghỉ.</li>
<li>Lịch chỉ hiện đơn <strong>trong phạm vi dữ liệu của bạn</strong> — trưởng bộ phận thấy người trong bộ phận mình, nhân viên thường chỉ thấy đơn của chính mình.</li>
<li>Bấm vào một dòng để mở tờ đơn.</li>
</ul>
<p>Lịch <strong>không</strong> hiện đơn nháp, đơn bị từ chối và đơn đã hủy — những đơn đó không dẫn tới ai nghỉ cả.</p>""",
        },
        {
            "title": NHAN_SU,
            "icon": "settings",
            "summary": "Cấp quỹ phép, điều chỉnh tay, Loại nghỉ, Lịch ngày lễ, phân quyền",
            "content": f"""<h2>Dành cho phòng Nhân sự</h2>
<h3>Quỹ phép năm</h3>
<p>Tab <strong>Quỹ phép năm</strong>: mỗi dòng là <strong>một người × một năm × một loại nghỉ</strong>.</p>
<ul>
<li><strong>Cấp phát</strong> đầu năm cho cả danh sách.</li>
<li><strong>Điều chỉnh tay</strong> khi số thực tế khác công thức (thưởng thêm ngày, cấn trừ…). ⚠️ Điều chỉnh tay <strong>GHI ĐÈ</strong>, nên nhìn con số hiện tại không biết ai đưa nó tới đó — vì vậy trang chi tiết có khối <strong>Lịch sử thao tác</strong>, đọc nó trước khi sửa tiếp.</li>
</ul>
<h3>Thiết lập ▸ Loại nghỉ</h3>
<p>Khai từng loại nghỉ và luật của nó: có trừ quỹ không, hạn mức, số ngày báo trước, trần mỗi lần, có trừ cuối tuần và ngày lễ không, chỉ áp cho giới tính nào, có bắt đính kèm không. Tab <strong>Bậc thâm niên</strong> nằm trong chính màn này.</p>
<ul>
<li><strong>Thai sản</strong> cố ý <strong>không</strong> trừ cuối tuần và lễ — nghỉ sáu tháng thì không ai bù cuối tuần.</li>
<li>Loại chỉ áp cho <strong>nữ</strong> thì hồ sơ <strong>chưa khai giới tính vẫn nộp được</strong> — chặn là khóa cả công ty tới khi nhập bù giới tính.</li>
<li>Nút <strong>Thêm</strong> mở <strong>trang riêng</strong> chứ không mở hộp thoại, vì form dài và có bảng bậc thâm niên.</li>
</ul>
<h3>Thiết lập ▸ Lịch ngày lễ</h3>
<ul>
<li>Ngày lễ <strong>không khai pháp nhân</strong> thì áp cho <strong>mọi pháp nhân</strong>. Pháp nhân có lịch riêng thì thêm dòng của nó — hai nguồn được gộp.</li>
<li>Cờ <strong>lặp hằng năm</strong> chỉ dùng cho ngày <strong>cố định theo dương lịch</strong> (01/01, 30/4, 02/9). <strong>Tết Âm và Giỗ Tổ trôi theo lịch âm nên mỗi năm phải nhập lại</strong> — đây là chỗ hay quên nhất, quên là cả công ty bị trừ phép vào ngày lễ.</li>
</ul>
<h3>Bốn khóa quyền — đừng gộp</h3>
<table>
<thead><tr><th>Khóa</th><th>Mở màn nào</th></tr></thead>
<tbody>
<tr><td><code>leave_request</code></td><td>Đơn nghỉ phép · Lịch nghỉ</td></tr>
<tr><td><code>leave_balance</code></td><td>Quỹ phép năm (cấp phát, <strong>điều chỉnh tay</strong>)</td></tr>
<tr><td><code>leave_type</code></td><td>Thiết lập ▸ Loại nghỉ</td></tr>
<tr><td><code>holiday</code></td><td>Thiết lập ▸ Lịch ngày lễ</td></tr>
</tbody>
</table>
<p>Tách bốn vì <strong><code>leave_balance</code> ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai</strong> — đó là việc của phòng Nhân sự, không phải của người nộp đơn.</p>
<p>⚠️ <strong>Người dùng báo «không thấy menu Nghỉ phép» thì gần như chắc là do phân quyền.</strong> Bốn khóa này mới thêm nên các vai trò cũ <strong>không tự có</strong> — vào <strong>Nhân sự ▸ Phân quyền tài khoản</strong> tick thêm.</p>
<h3>Luồng duyệt</h3>
<p>Khai ở phân hệ <strong>Phê duyệt</strong>. Luồng mẫu: <strong>trưởng bộ phận của người xin nghỉ → trưởng phòng Nhân sự</strong>. ⚠️ <strong>Mỗi chặng phải khai người dự phòng</strong> — hệ loại người nộp khỏi danh sách người ký, nên trưởng phòng tự xin nghỉ thì chặng đó rỗng và đơn kẹt.</p>
<p>Chi tiết cách ký xem {ref(DUYET, "bài Duyệt đơn nghỉ phép")}.</p>""",
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
