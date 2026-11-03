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

Bản 3 (22/10/2026, duoc-CR-670): thêm "loại nghỉ bắt buộc đính kèm" (CR-661) vào bài Nộp đơn / Câu báo lỗi /
Loại nghỉ, và mục "Kết sổ cuối năm và bảng Đối chiếu" (CR-664) vào bài Quỹ phép của phòng Nhân sự.

Bản 4 (02/11/2026, bao-CR-708): bài Loại nghỉ thêm mục "Các loại nghỉ chế độ BHXH" — năm loại tách riêng
(khám thai, sảy thai, tránh thai, chăm con ốm, dưỡng sức) kèm mức luật và trần trên hệ.

Bản 5 (02/11/2026, duoc-CR-715): bài Loại nghỉ thêm ba ô luật cấp quỹ (cách cấp quỹ, dùng được sau N ngày,
cho ứng phép) và tab "Hạn mức theo nhóm"; bài Số phép còn lại nói thêm về loại cộng dần theo tháng.

Bản 6 (03/11/2026, đối chiếu duoc-CR-713/714/715/716 với màn thật): menu Nghỉ phép nay có năm mục (thêm Nghỉ bù),
Thiết lập có ba thẻ (thêm Ngày cấm nghỉ); trang Loại nghỉ bố cục phẳng với ba tab Thông tin / Bậc thâm niên / Hạn mức
theo nhóm và nhãn ô viết đúng chữ trên form; bỏ mọi câu về "số ngày báo trước" (luật đã bỏ từ 05/09/2026, cột
`min_notice_days` không ai đọc); "không có ứng phép" đổi thành "mặc định không cho ứng, Nhân sự bật được theo loại";
bài Xin nghỉ bù viết lại theo nhãn thật và luật sau lượt rà mã (luôn chặn tự duyệt, cộng vào năm nay khi ngày đi làm
thuộc năm cũ, chỉ nhận ngày từ 01/01 năm trước, câu 409 khi bấm đúp); phân quyền năm khóa (thêm `leave_comp_request`),
menu Phân quyền tài khoản ở phân hệ Quản trị. Nhãn đối chiếu bằng đọc `hr/config/leave-type-crud.tsx`,
`hr/config/leave-block-crud.tsx`, `hr/pages/leave-comp-request-*.tsx`, `hr/components/leave-comp-*.tsx`,
`hr/components/leave-type-quota-card.tsx`, câu báo lỗi ở `leave/comp_request_service.py`, `leave/accrual_service.py`,
`leave/block_period_service.py`, `leave/leave_policy.py`, `approval/self_approval_policy.py`.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_nghi_phep.py
    # rồi nạp bài mới vào kho tìm kiếm của trợ lý AI (seed ghi thẳng ORM nên hook không bắn):
    docker compose exec -T api python scripts/reindex_help_rag.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại.

⚠️ Nội dung ở đây phải KHỚP với `doc/erp/hrm/02-nghi-phep.md` và gói
cẩm nang trợ lý (Kho skill, hạt giống `app/modules/ai_skill/seed_handbook/40-nghi-phep.md`). Ba nơi lệch nhau
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
NGHI_BU = "Xin nghỉ bù"
NS_QUY = "Nhân sự — Cấp và điều chỉnh quỹ phép"
NS_DANH_MUC = "Nhân sự — Loại nghỉ, bậc thâm niên và Lịch ngày lễ"
NS_QUYEN = "Nhân sự — Phân quyền và luồng duyệt"


TREE = {
    "title": ROOT_TITLE,
    "icon": "calendar",
    "summary": "Nộp đơn nghỉ phép, xin nghỉ bù, xem quỹ phép còn lại, duyệt đơn, cấp quỹ và khai ngày cấm nghỉ",
    "content": f"""<h2>Nghỉ phép là gì?</h2>
<p>Phân hệ để nhân viên <strong>nộp đơn nghỉ phép</strong> và <strong>xin nghỉ bù</strong>, người quản lý duyệt, và phòng Nhân sự cấp <strong>quỹ phép năm</strong>. Vào bằng menu <strong>Nhân sự ▸ Nghỉ phép</strong>.</p>
<p>Thứ đáng giá nhất ở đây không phải tờ đơn — mà là <strong>số ngày phép còn lại hiện ngay lúc bạn đang nhập</strong>. Toàn bộ phần quỹ phép, bậc thâm niên và lịch ngày lễ tồn tại để con số đó đúng.</p>

<h2>Năm mục trong menu Nghỉ phép</h2>
<p>Bấm <strong>Nghỉ phép</strong> ở menu trái để mở năm mục con:</p>
<table>
<thead><tr><th>Mục</th><th>Dùng để</th><th>Ai thấy</th></tr></thead>
<tbody>
<tr><td><strong>Đơn nghỉ phép</strong></td><td>Nộp đơn, theo dõi đơn của mình, duyệt đơn của người khác</td><td>Mọi người</td></tr>
<tr><td><strong>Nghỉ bù</strong></td><td>Lập phiếu xin nghỉ bù khi đã đi làm vào ngày lễ hoặc ngày nghỉ, duyệt phiếu của người khác</td><td>Mọi người có quyền Phiếu nghỉ bù</td></tr>
<tr><td><strong>Lịch nghỉ</strong></td><td>Ai nghỉ ngày nào — xem theo ngày / tuần / tháng</td><td>Mọi người</td></tr>
<tr><td><strong>Quỹ phép năm</strong></td><td>Số ngày phép của từng người từng năm, cấp phát và điều chỉnh</td><td>Phòng Nhân sự</td></tr>
<tr><td><strong>Thiết lập</strong></td><td>Ba thẻ chuyển qua lại ở đầu trang: <strong>Loại nghỉ</strong> (kèm bậc thâm niên và hạn mức theo nhóm), <strong>Lịch ngày lễ</strong>, <strong>Ngày cấm nghỉ</strong></td><td>Phòng Nhân sự</td></tr>
</tbody>
</table>
<p>Không thấy đủ năm mục <strong>không phải lỗi</strong> — đó là phân quyền. Xem {ref(NS_QUYEN, "bài Phân quyền và luồng duyệt")}.</p>

<h2>Bốn khái niệm đừng lẫn</h2>
<table>
<thead><tr><th>Thứ</th><th>Là gì</th></tr></thead>
<tbody>
<tr><td><strong>Đơn nghỉ phép</strong></td><td>Chứng từ bạn nộp, có số dạng <code>NP001</code>. Đây là thứ để xin nghỉ.</td></tr>
<tr><td><strong>Giấy nghỉ phép (GNP)</strong></td><td><strong>Văn bản</strong> bên phân hệ Văn thư, hệ <strong>tự sinh sau khi đơn đã duyệt</strong>. Là hồ sơ lưu sổ, không phải thứ để nộp.</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Danh mục: Phép năm, Nghỉ ốm, Thai sản, Nghỉ không lương… Mỗi loại một bộ luật riêng.</td></tr>
<tr><td><strong>Quỹ phép</strong></td><td>Số ngày của <strong>một người × một năm × một loại nghỉ</strong>.</td></tr>
<tr><td><strong>Phiếu nghỉ bù</strong></td><td>Chứng từ có số dạng <code>NB001</code>, xin cộng thêm ngày vào quỹ vì đã đi làm ngày lễ hoặc ngày nghỉ. Phiếu không phải đơn nghỉ: duyệt xong bạn mới có thêm ngày để nộp đơn nghỉ.</td></tr>
</tbody>
</table>
<p>⚠️ Muốn xin nghỉ thì <strong>nộp đơn</strong> ở đây, <strong>đừng</strong> vào Văn thư tạo <strong>Giấy nghỉ phép</strong> — làm tay ra một tờ giấy không gắn với quỹ phép nào, và không ai được báo để duyệt.</p>

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
<li><strong>Vừa nộp đơn xong sao phép còn lại hụt luôn?</strong> — đúng như vậy, và là cố ý. Xem {ref(QUY_PHEP, "Hiểu số ngày phép còn lại")}.</li>
<li><strong>Nộp rồi sửa được không?</strong> — không. Chỉ sửa được lúc <em>Nháp</em> và <em>Trả về chỉnh sửa</em>. Xem {ref(THEO_DOI, "Theo dõi, sửa và hủy đơn")}.</li>
<li><strong>Không thấy menu Nghỉ phép</strong> — gần như luôn là phân quyền, xem {ref(NS_QUYEN, "bài Phân quyền")}.</li>
<li><strong>Nghỉ hai đợt không liền nhau trong một đơn được không?</strong> — được, bấm <strong>+ Thêm khoảng ngày</strong> ngay trên form. Xem {ref(NOP_DON, "Nộp đơn nghỉ phép")}.</li>
</ul>

<h2>Đọc theo việc bạn cần làm</h2>
<p><strong>Người đi nghỉ:</strong> {ref(NOP_DON, "Nộp đơn")} · {ref(QUY_PHEP, "hiểu quỹ phép")} · {ref(THEO_DOI, "theo dõi, sửa, hủy")} · {ref(NGHI_BU, "xin nghỉ bù")} · {ref(TINH_HUONG, "tình huống thường gặp")} · {ref(BAO_LOI, "câu báo lỗi")}.</p>
<p><strong>Người duyệt:</strong> {ref(DUYET, "Duyệt đơn nghỉ phép")} · {ref(NGHI_BU, "duyệt phiếu nghỉ bù")} · {ref(LICH_NGHI, "xem Lịch nghỉ")}.</p>
<p><strong>Phòng Nhân sự:</strong> {ref(NS_QUY, "cấp và điều chỉnh quỹ")} · {ref(NS_DANH_MUC, "loại nghỉ, ngày lễ và ngày cấm nghỉ")} · {ref(NS_QUYEN, "phân quyền và luồng duyệt")}. Các công tắc chặn đơn lùi ngày, chặn tự duyệt và vai trò được duyệt qua ngày cấm nghỉ nằm ở <strong>Nhân sự ▸ Master ▸ Cài đặt nhân sự</strong>, tab <strong>Nghỉ phép</strong>.</p>""",
    "children": [
        {
            "title": NOP_DON,
            "icon": "file-text",
            "summary": "Sáu bước từ mở đơn tới gửi duyệt, giải thích từng ô trên form",
            "content": f"""<h2>Nộp đơn nghỉ phép</h2>
<p>Toàn bộ việc gói trong sáu bước dưới đây. Đơn <strong>luôn</strong> sinh ra ở trạng thái <em>Nháp</em> — gửi duyệt là một bước riêng, bấm sau.</p>

<h2>Sáu bước</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Nghỉ phép ▸ Đơn nghỉ phép</strong>.</li>
<li>Bấm nút <strong>Nộp đơn nghỉ phép</strong> ở góc trên bên phải.</li>
<li>Chọn <strong>Loại nghỉ</strong> <em>trước tiên</em> — mỗi loại một luật riêng, và chọn xong thì số ngày còn lại của loại đó hiện ra ngay dưới.</li>
<li>Chọn <strong>Từ ngày / Đến ngày</strong> (kèm <strong>buổi</strong> nếu nghỉ nửa ngày). Ô <strong>Tổng số ngày</strong> tự điền.</li>
<li>Viết <strong>Lý do nghỉ</strong>, khai <strong>Bàn giao công việc</strong>, điền số điện thoại liên hệ nếu công ty yêu cầu.</li>
<li>Bấm <strong>Lưu nháp</strong>. Kiểm lại một lượt rồi bấm <strong>Gửi duyệt</strong>.</li>
</ol>
<p>⚠️ Nút <strong>Gửi duyệt</strong> chỉ hiện <strong>sau khi đơn đã được lưu ít nhất một lần</strong>. Chưa lưu mà không thấy nút thì không phải hỏng — bấm <strong>Lưu nháp</strong> trước.</p>

<h2>Từng ô trên đơn</h2>
<table>
<thead><tr><th>Ô</th><th>Bắt buộc</th><th>Ghi gì / cần biết</th></tr></thead>
<tbody>
<tr><td><strong>Loại nghỉ</strong></td><td>Có</td><td>Quyết định mọi luật còn lại: có trừ quỹ không, có cho ứng phép không, tối đa mấy ngày một lần, có trừ ngày nghỉ và ngày lễ không, có phải vào làm đủ một số ngày mới dùng được không, có bắt đính kèm giấy tờ không.</td></tr>
<tr><td><strong>Tổng số ngày</strong></td><td>Có (tự điền)</td><td>Hệ tính sẵn theo <strong>lịch làm việc của bạn</strong> và <strong>đã trừ ngày nghỉ trong tuần (thường là Chủ nhật) cùng ngày lễ</strong>. Gõ đè được — lúc đó dòng chú thích đổi thành <em>Bạn đang nhập tay. Hệ thống gợi ý N ngày.</em> để bạn biết mình đang lệch với máy.</td></tr>
<tr><td><strong>Từ ngày</strong> + <strong>Buổi bắt đầu</strong></td><td>Có</td><td>Buổi: <em>Cả ngày · Buổi sáng · Buổi chiều</em>.</td></tr>
<tr><td><strong>Đến ngày</strong> + <strong>Buổi kết thúc</strong></td><td>Có</td><td>Nghỉ một ngày thì để hai ô ngày bằng nhau.</td></tr>
<tr><td><strong>Lý do nghỉ</strong></td><td>Có, khi gửi duyệt</td><td>Người duyệt đọc đúng dòng này để quyết. Viết cụ thể, đừng viết <em>việc riêng</em>.</td></tr>
<tr><td><strong>Bàn giao công việc</strong></td><td>Không, nhưng nên</td><td>Ai gánh việc gì thay bạn. <strong>Thiếu người bàn giao là lý do bị trả đơn phổ biến nhất.</strong></td></tr>
<tr><td><strong>Điện thoại liên hệ khi nghỉ</strong></td><td>Không</td><td>Số gọi được trong thời gian nghỉ.</td></tr>
<tr><td><strong>Địa chỉ khi nghỉ</strong></td><td>Không</td><td>Nơi ở trong thời gian nghỉ (đi tỉnh, về quê…).</td></tr>
</tbody>
</table>

<h2>Số ngày phép còn lại — ô quan trọng nhất</h2>
<p>Ngay dưới <strong>Loại nghỉ</strong> và <strong>Tổng số ngày</strong> có một dải chạy hết bề ngang, nói bạn còn bao nhiêu ngày của <em>chính loại nghỉ vừa chọn</em>. Ba trạng thái của dải này:</p>
<ul>
<li><strong>Còn đủ</strong> — hiện số còn lại trên tổng quỹ, cứ thế gửi duyệt.</li>
<li><strong>Xin vượt quỹ</strong> — cảnh báo ngay tại chỗ, kèm gợi ý chuyển sang <strong>Nghỉ không lương</strong>. Đừng bấm gửi duyệt, hệ thống cũng chặn.</li>
<li><strong>Loại nghỉ không trừ quỹ</strong> — nói thẳng là không giới hạn, chứ không hiện số <code>0</code> gây hiểu nhầm là hết phép.</li>
</ul>
<p>Xin <strong>đúng bằng</strong> số còn lại thì <strong>không</strong> bị cảnh báo — đó là hợp lệ. Nếu phòng Nhân sự cho loại nghỉ đó <strong>ứng phép</strong> (ví dụ tối đa 3 ngày) thì dải chỉ cảnh báo khi bạn xin vượt quá cả phần được ứng. Chi tiết cách con số này được tính: {ref(QUY_PHEP, "Hiểu số ngày phép còn lại")}.</p>

<h2>Khung vàng «Đơn nghỉ này rơi vào ngày cấm nghỉ»</h2>
<p>Công ty có thể khai những khoảng ngày không muốn ai nghỉ (chốt sổ, kiểm kê, mùa cao điểm). Bạn chọn ngày đụng một khoảng như vậy thì form hiện <strong>khung vàng</strong> <em>Đơn nghỉ này rơi vào ngày cấm nghỉ.</em> kèm ngày và lý do. Bạn <strong>vẫn lưu và gửi duyệt được</strong>, nhưng lượt duyệt cuối sẽ bị chặn trừ khi người duyệt thuộc vai trò được miễn. Nên đổi ngày ngay từ đầu nếu được, hoặc ghi rõ lý do bắt buộc phải nghỉ để người duyệt cân nhắc.</p>

<h2>Loại nghỉ chỉ dùng được sau một số ngày vào làm</h2>
<p>Một số loại nghỉ (thường là Phép năm) có thể được phòng Nhân sự khai <em>dùng được sau N ngày kể từ ngày vào làm</em>. Nhân viên mới xin nghỉ loại đó trước mốc này thì hệ báo <em>Loại nghỉ "Phép năm" chỉ dùng được sau 60 ngày vào làm (từ dd/mm/yyyy).</em> Chọn ngày từ mốc đó trở đi, hoặc chọn loại khác như Nghỉ không lương.</p>

<h2>Lưu nháp hay Gửi duyệt?</h2>
<table>
<thead><tr><th></th><th>Lưu nháp</th><th>Gửi duyệt</th></tr></thead>
<tbody>
<tr><td>Ai thấy đơn</td><td>Chỉ bạn</td><td>Người duyệt nhận việc + thông báo chuông</td></tr>
<tr><td>Trừ phép chưa</td><td><strong>Chưa</strong></td><td><strong>Trừ ngay</strong> (giữ chỗ)</td></tr>
<tr><td>Kiểm nhập đủ</td><td>Không kiểm</td><td>Kiểm — thiếu ô nào là chặn</td></tr>
<tr><td>Sửa lại được</td><td>Thoải mái</td><td><strong>Khóa</strong></td></tr>
<tr><td>Xóa được</td><td>Được (nút <strong>Xóa đơn</strong>)</td><td>Không — chỉ <strong>hủy</strong></td></tr>
</tbody>
</table>
<p>Cứ lưu nháp thoải mái rồi hoàn thiện sau: hệ chỉ kiểm "nhập đủ" ở bước gửi duyệt.</p>

<h2>Loại nghỉ bắt buộc đính kèm giấy tờ</h2>
<p>Một số loại nghỉ (thường là <strong>Nghỉ ốm</strong>, <strong>Nghỉ vợ sinh con</strong>) được phòng Nhân sự bật cờ <strong>Bắt buộc đính kèm</strong>: đơn phải có <strong>ít nhất một tệp</strong> (giấy khám bệnh, giấy chứng sinh…) thì mới <strong>gửi duyệt</strong> được. <strong>Lưu nháp thì không bị chặn.</strong></p>
<ol>
<li>Điền đơn, bấm <strong>Lưu nháp</strong>. Mục <strong>Tệp đính kèm</strong> chỉ dùng được sau khi đơn đã được lưu, vì tệp phải gắn vào một tờ đơn đã có số.</li>
<li>Ở mục <strong>Tệp đính kèm</strong>, tải giấy tờ lên. Khi đã chọn loại nghỉ bắt buộc, mục này hiện <strong>dấu bắt buộc</strong> và dòng chữ đỏ <em>Loại nghỉ <strong>Nghỉ ốm</strong> bắt buộc đính kèm giấy tờ: cần có ít nhất một tệp trước khi gửi duyệt.</em></li>
<li>Bấm <strong>Gửi duyệt</strong>.</li>
</ol>
<p>Bấm <strong>Gửi duyệt</strong> khi chưa có tệp thì màn hình báo ngay <em>Loại nghỉ <strong>Nghỉ ốm</strong> bắt buộc đính kèm giấy tờ — tải tệp lên ở mục <strong>Tệp đính kèm</strong> rồi gửi duyệt.</em> và đơn vẫn nằm ở trạng thái Nháp, phép chưa bị giữ chỗ. Đơn khai nhiều loại nghỉ thì chỉ cần <strong>một</strong> loại bắt buộc là cả đơn phải có tệp.</p>

<h2>Nghỉ nửa ngày</h2>
<p>Đặt <strong>Từ ngày = Đến ngày</strong>, rồi chọn <strong>Buổi bắt đầu</strong> và <strong>Buổi kết thúc</strong> là <em>Buổi sáng</em> (hoặc cả hai là <em>Buổi chiều</em>). Tổng số ngày ra <strong>0,5</strong> và quỹ trừ đúng nửa ngày.</p>
<p>⚠️ Nghỉ <strong>từ buổi chiều đến buổi sáng cùng ngày</strong> là một khoảng trống — hệ chặn.</p>

<h2>Nghỉ nhiều đợt không liền nhau trong một đơn</h2>
<p>Ví dụ: nghỉ <strong>27/10</strong> cả ngày, rồi nghỉ tiếp từ <strong>chiều 03/11 đến hết 07/11</strong>. Không cần lập hai đơn — khai cả hai đợt trong <strong>một</strong> tờ đơn.</p>
<ol>
<li>Điền khoảng đầu như bình thường (Từ ngày / Đến ngày, kèm buổi).</li>
<li>Bấm nút <strong>+ Thêm khoảng ngày</strong> dưới ô ngày. Mỗi khoảng hiện trong một khung riêng, tiêu đề dạng <strong>Khoảng ngày 2 · 4,5 ngày</strong> (số ngày của khoảng do hệ tính sẵn). Nút <strong>X</strong> ở góc khung để bỏ khoảng đó.</li>
<li>Dòng cuối danh sách cộng giúp bạn: <strong>Cộng 2 khoảng: 5,5 ngày</strong>. Đây cũng là <strong>Tổng số ngày</strong> của đơn; gõ đè được ở ô Tổng số ngày như mọi đơn khác (không gõ đè riêng từng khoảng).</li>
<li>Lưu nháp rồi Gửi duyệt như bình thường.</li>
</ol>
<p>Những ngày <strong>nằm giữa hai khoảng</strong> (trong ví dụ là 28/10 – 02/11) là ngày đi làm: <strong>không bị trừ phép</strong>, và không hiện nghỉ ở Lịch nghỉ hay <strong>Ai làm / ai nghỉ</strong>.</p>
<table>
<thead><tr><th>Cần biết</th><th>Chi tiết</th></tr></thead>
<tbody>
<tr><td>Tối đa</td><td><strong>20 khoảng</strong> mỗi đơn. Đủ 20 thì nút <strong>+ Thêm khoảng ngày</strong> tắt, có dòng chú thích.</td></tr>
<tr><td>Không chồng ngày</td><td>Hai khoảng trong cùng một đơn không được trùng ngày. Trùng thì khung hiện chữ đỏ <em>Khoảng này chồng ngày với một khoảng khác — các khoảng không được trùng ngày.</em></td></tr>
<tr><td>Cùng một năm</td><td>Đơn có <strong>từ hai khoảng trở lên</strong> thì mọi khoảng phải cùng một năm (vì phép trừ theo năm). Ví dụ 29/12 và 05/01 sang năm: hệ báo <em>Đơn nhiều khoảng ngày phải nằm trong cùng một năm. Tách thành hai đơn…</em> — lập một đơn cho năm trước, một đơn cho năm sau. Đơn chỉ <strong>một</strong> khoảng vắt sang năm mới thì vẫn như trước.</td></tr>
<tr><td>Nghỉ theo giờ</td><td>Nghỉ <strong>theo giờ chỉ khai được một khoảng</strong>. Chọn <strong>Theo giờ</strong> thì nút <strong>+ Thêm khoảng ngày</strong> ẩn; đang có từ hai khoảng thì không chọn được <strong>Theo giờ</strong>.</td></tr>
<tr><td>Nhiều loại nghỉ</td><td>Vẫn dùng bảng loại nghỉ như cũ: các khoảng chỉ cho ra tổng số ngày, bạn chia tổng đó vào từng loại. Loại nghỉ <strong>không gắn</strong> với một khoảng cụ thể.</td></tr>
<tr><td>Trùng đơn khác</td><td>Hệ kiểm trùng ngày <strong>theo từng khoảng</strong>: một đơn khác nằm gọn trong khe giữa hai khoảng thì vẫn gửi được; chạm vào một khoảng thì bị chặn.</td></tr>
</tbody>
</table>
<p>Sau khi gửi, người duyệt thấy mục <strong>Thời gian nghỉ</strong> liệt kê từng khoảng (thay cho hai dòng Từ ngày / Đến ngày). Ở danh sách đơn, cột <em>Đến ngày</em> ghi thêm chữ mờ, ví dụ <strong>07/11/2026 · 2 khoảng</strong>. Bản in liệt kê đủ các khoảng.</p>
<p><strong>Nhờ Trợ lý AI soạn:</strong> bạn có thể nói <em>nghỉ 27/10 và chiều 3/11 tới 7/11</em> — Trợ lý soạn nháp có đủ hai khoảng, bạn kiểm lại rồi bấm tạo đơn.</p>

<h2>Nộp hộ người khác</h2>
<p>Hành chính hoặc trợ lý nộp hộ được: điền <strong>người nghỉ</strong> vào ô riêng trên đơn. Bỏ trống ô đó thì người nghỉ chính là người đang gõ.</p>
<p>Cả <strong>người lập</strong> lẫn <strong>người nghỉ</strong> đều thấy tờ đơn đó trong tab <em>Đơn của tôi</em> — cố ý, vì hai người đều có việc với nó.</p>

<h2>Đơn cho ngày đã qua</h2>
<p>Nếu công ty bật <strong>Chặn đơn nghỉ lùi ngày</strong> (ở Cài đặt nhân sự), bạn không lập, sửa hay gửi duyệt được đơn có ngày nghỉ <strong>trước hôm nay</strong>; hệ báo <em>Không lập được đơn nghỉ cho ngày đã qua (dd/mm/yyyy). Cài đặt nhân sự đang chặn đơn lùi ngày — nhờ phòng Nhân sự lập hộ nếu cần.</em> Ngày hôm nay vẫn lập được. Đơn quên nộp thì nhờ phòng Nhân sự hoặc người có vai trò được miễn lập hộ; đơn họ lập hộ thì bạn vẫn gửi duyệt được.</p>

<h2>Gửi duyệt xong thì gì xảy ra</h2>
<ol>
<li>Số ngày bị <strong>giữ chỗ</strong> ngay, trừ khỏi <strong>còn lại</strong>.</li>
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
<p>Con số này xuất hiện ở <strong>ba chỗ</strong>: dải ngay dưới ô <strong>Loại nghỉ</strong> khi đang điền đơn · cột <strong>Còn lại</strong> ở bảng <em>Quỹ phép năm</em> · và thẻ chi tiết của một dòng quỹ. Ba chỗ cùng một công thức, không có chỗ nào tính riêng.</p>

<h2>Công thức</h2>
<pre>còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay + nghỉ bù cộng thêm)
          − đã nghỉ − đang chờ duyệt</pre>
<p><strong>Số còn lại không được lưu thành cột nào cả</strong> — nó luôn được tính lại. Lưu thêm thì có hai nguồn sự thật, và cái thứ hai chắc chắn sẽ lệch.</p>
<p>Với loại nghỉ cấu hình <strong>Cộng dần theo tháng</strong>, phần hạn mức <em>chưa tới tháng</em> bị trừ khỏi số còn lại: hạn mức 12 ngày, đang tháng 5 thì mới dùng được 5 ngày (làm tròn xuống nửa ngày), sang tháng 6 là 6 ngày. Thâm niên, phép chuyển năm trước, điều chỉnh tay và ngày nghỉ bù không bị cộng dần. Số này giống nhau ở form nộp đơn, bảng Quỹ phép năm và báo cáo Quỹ phép năm.</p>
<p>Loại nghỉ được phòng Nhân sự bật <strong>Cho ứng phép tối đa</strong> thì số còn lại được xuống thấp hơn 0 tới mức đã khai (ví dụ tới âm 3 ngày). Khi đó cột <strong>Còn lại</strong> hiện số âm, nghĩa là bạn đã dùng trước bấy nhiêu ngày.</p>

<h2>Bảy con số cấu thành</h2>
<table>
<thead><tr><th>Cột trên bảng</th><th>Ở đâu ra</th></tr></thead>
<tbody>
<tr><td><strong>Hạn mức</strong></td><td>Khai trên <em>Loại nghỉ</em> (ví dụ Phép năm 12 ngày), hoặc mức riêng cho nhóm của bạn ở tab <em>Hạn mức theo nhóm</em>. Người vào làm giữa năm có thể chỉ nhận một phần nếu loại nghỉ cấp <em>theo tỷ lệ tháng làm việc</em>.</td></tr>
<tr><td><strong>Thâm niên</strong></td><td>Cộng thêm theo bảng bậc, tính tại 01/01 của năm đó.</td></tr>
<tr><td><strong>Chuyển năm trước</strong></td><td>Phép tồn năm ngoái chuyển sang, nếu loại nghỉ đó khai <em>Mang sang năm sau</em> hoặc nhận phần quy đổi.</td></tr>
<tr><td><strong>Điều chỉnh tay</strong></td><td>Phòng Nhân sự sửa, cột duy nhất nhận <strong>số âm</strong>. Luôn kèm lý do.</td></tr>
<tr><td><strong>Nghỉ bù cộng thêm</strong></td><td>Tổng ngày của các <strong>phiếu nghỉ bù đã duyệt</strong>, chỉ có ở loại nghỉ nhận ngày bù. Xem {ref(NGHI_BU, "bài Xin nghỉ bù")}.</td></tr>
<tr><td><strong>Đã nghỉ</strong></td><td>Cộng dồn các đơn <strong>đã duyệt</strong>.</td></tr>
<tr><td><strong>Chờ duyệt (đang giữ chỗ)</strong></td><td>Cộng dồn các đơn <strong>đang trong luồng duyệt</strong>.</td></tr>
</tbody>
</table>

<h2>Ví dụ bằng số</h2>
<p>Chị A vào làm được 11 năm, Phép năm hạn mức 12, năm ngoái không chuyển ngày nào, chưa từng bị điều chỉnh tay. Trong năm đã nghỉ 4 ngày, và đang có một đơn 3 ngày chờ sếp ký:</p>
<pre>(12 hạn mức + 2 thâm niên + 0 chuyển + 0 điều chỉnh + 0 nghỉ bù) − 4 đã nghỉ − 3 chờ duyệt = 7 ngày</pre>
<p>Chị A mở form nộp đơn ra sẽ thấy <strong>7</strong>, không phải 10. Ba ngày kia <em>chưa</em> nghỉ nhưng <em>đã</em> bị giữ chỗ.</p>

<h2>Vì sao vừa nộp đơn đã thấy hụt ngày?</h2>
<p><strong>Vì <em>đang chờ duyệt</em> ĐÃ bị trừ khỏi <strong>còn lại</strong>.</strong> Nộp đơn 3 ngày là số còn lại tụt ngay 3 ngày, chưa cần ai duyệt.</p>
<p>Đây là <strong>cố ý</strong>: không giữ chỗ như vậy thì nộp mười đơn liền tay đều lọt qua chốt kiểm, vì đơn nào cũng thấy quỹ còn nguyên. Lỗi đó chỉ lộ ra khi đã có người nghỉ thừa hai tuần.</p>
<p>Ngày bị giữ chỗ được <strong>trả lại ngay</strong> trong cả ba trường hợp: đơn bị <strong>từ chối</strong> · bị <strong>trả về chỉnh sửa</strong> · bạn <strong>tự hủy</strong>. Hủy một đơn <strong>đã duyệt</strong> thì hoàn lại phần <em>đã nghỉ</em>.</p>

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

<h2>Ứng phép: mặc định là không</h2>
<p>Mặc định mọi loại nghỉ <strong>không cho ứng phép</strong>: xin vượt quỹ bị <strong>chặn ngay lúc gửi duyệt</strong>, không phải chờ ai đó phát hiện. Muốn nghỉ thêm thì chọn loại <strong>Nghỉ không lương</strong> — câu chặn của hệ nói thẳng đường đó.</p>
<p>Phòng Nhân sự có thể bật ứng phép cho <strong>từng loại nghỉ</strong> bằng ô <strong>Cho ứng phép tối đa (ngày)</strong>, tối đa 30 ngày. Khi đó bạn được xin tới khi số còn lại xuống tới mức âm đã khai, quá mức đó thì vẫn bị chặn như trên. Hỏi phòng Nhân sự nếu không chắc loại nghỉ của mình có cho ứng hay không.</p>

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
<li>Cột bảng: <em>Số đơn · Trạng thái · Người nghỉ · Loại nghỉ · Từ ngày · Đến ngày · Số ngày</em>. Tab <em>Cần tôi duyệt</em> có thêm cột <strong>Hạn xử lý</strong> (và cột <em>Luồng duyệt</em> ẩn sẵn, bật ở menu <strong>Cột</strong>).</li>
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
<p>⚠️ <strong>Từ chối khác Trả về chỉnh sửa</strong> — một cái là dẹp, một cái là mời sửa. Hai chữ giống nhau về cảm giác nhưng khác hẳn về việc bạn phải làm tiếp. Đọc kỹ ô lý do người duyệt ghi; lý do luôn hiện trên dòng thời gian của đơn.</p>

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
<p>Bấm <strong>Hủy đơn</strong> ở màn chi tiết, hộp thoại <em>Hủy đơn nghỉ phép</em> hiện ra và <strong>bắt ghi lý do</strong> (gõ toàn dấu cách không tính là lý do). <strong>Hủy được cả khi đơn đã duyệt</strong> — đổi kế hoạch là chuyện thường, và ngày phép được hoàn lại.</p>
<p>Đơn đang chạy trong luồng thì hệ <strong>rút phiên duyệt trước rồi mới hủy</strong>, nên người duyệt không còn thấy việc đó nữa.</p>
<p>⚠️ <strong>Chỉ chính người nộp</strong> mới hủy được đơn đang nằm trong luồng. Người khác muốn chặn thì dùng <strong>Trả về</strong> hoặc <strong>Từ chối</strong> — hai nút đó có ô ghi lý do gửi về cho người nộp.</p>

<h2>Sửa rồi gửi lại</h2>
<p>Đơn bị <em>Trả về chỉnh sửa</em> thì mở ra, sửa đúng chỗ người duyệt nêu, bấm <strong>Lưu nháp</strong> rồi <strong>Gửi duyệt</strong> lần nữa. Đơn <strong>không</strong> bị đóng và <strong>giữ nguyên số đơn</strong> — người duyệt nhìn thấy đúng tờ họ đã trả về.</p>

<h2>Không thấy đơn mình đang tìm?</h2>
<p>Bạn chỉ đọc được đơn <strong>trong phạm vi dữ liệu</strong> của mình. Đơn ngoài phạm vi thì hệ báo <em>Không tìm thấy</em> — không có nghĩa là đơn đó không tồn tại, chỉ là bạn không được xem. Lý do nghỉ là chuyện riêng tư nên hệ cố ý chặt tay ở chỗ này.</p>
<p>Cần xem rộng hơn thì xin thêm phạm vi ở {ref(NS_QUYEN, "màn Phân quyền")}, đừng nhờ người khác chụp màn hình gửi qua.</p>""",
        },
        {
            "title": DUYET,
            "icon": "workflow",
            "summary": "Duyệt ngay trong màn Nghỉ phép, đọc gì trước khi ký, ba nút và hậu quả",
            "content": f"""<h2>Duyệt đơn nghỉ phép</h2>
<p>Dành cho người được giao ký. Bạn <strong>không phải sang màn Phê duyệt</strong> — duyệt ngay trong <strong>Nhân sự ▸ Nghỉ phép ▸ Đơn nghỉ phép</strong>, tab <strong>Cần tôi duyệt</strong>. Phiếu nghỉ bù duyệt ở mục <strong>Nghỉ bù</strong>, xem {ref(NGHI_BU, "bài Xin nghỉ bù")}.</p>

<h2>Nhận việc</h2>
<ul>
<li>Có việc mới, bạn nhận <strong>thông báo chuông</strong> kèm liên kết mở thẳng tờ đơn.</li>
<li>Mở màn Nghỉ phép ra là tab <em>Cần tôi duyệt</em> <strong>tự được chọn</strong>, kèm con số việc đang chờ.</li>
<li>Cột <strong>Hạn xử lý</strong> cho biết việc này đến hạn khi nào. Bạn đang ký chặng nào, hay đang ký thay ai, thì xem ở trang chi tiết đơn.</li>
</ul>

<h2>Đọc gì trước khi ký</h2>
<p>Thẻ tóm tắt trên đầu trang chi tiết gom đủ bốn thứ để quyết mà không phải đi lục:</p>
<ol>
<li><strong>Loại nghỉ và số ngày</strong> — kèm số ngày còn lại của người xin.</li>
<li><strong>Khoảng ngày</strong> — kèm buổi, nếu khác <em>cả ngày</em>.</li>
<li><strong>Lý do nghỉ</strong>.</li>
<li><strong>Bàn giao công việc</strong> — mục này <strong>luôn hiện, kể cả khi trống</strong>, và khi trống thì nói thẳng <em>Người nộp chưa khai ai nhận bàn giao trong thời gian nghỉ.</em></li>
</ol>
<p>⚠️ Mục bàn giao luôn hiện là <strong>cố ý</strong>: người duyệt phải phân biệt được <em>"người nộp chưa khai ai"</em> với <em>"màn hình thiếu mục đó"</em>. Mà thiếu người bàn giao chính là <strong>lý do trả đơn phổ biến nhất</strong> — nó phải nói thành lời, không để suy ra từ một khoảng trống.</p>
<p>Bên dưới là <strong>dòng thời gian duyệt</strong>: ai đã ký chặng nào, lúc mấy giờ, ghi ý kiến gì.</p>

<h2>Ba nút</h2>
<table>
<thead><tr><th>Nút</th><th>Dùng khi</th><th>Hậu quả</th></tr></thead>
<tbody>
<tr><td><strong>Duyệt đơn</strong></td><td>Đồng ý</td><td>Sang chặng sau, hoặc xong hẳn nếu là chặng cuối. Xong thì <strong>trừ quỹ thật</strong> và <strong>sinh Giấy nghỉ phép</strong>. Đơn rơi vào <strong>ngày cấm nghỉ</strong> thì lượt duyệt cuối bị chặn, trừ khi bạn thuộc vai trò được miễn — xem mục dưới.</td></tr>
<tr><td><strong>Trả về</strong></td><td>Đơn thiếu thông tin, sửa là được</td><td>Người nộp <strong>sửa rồi gửi lại chính tờ đó</strong>. Phép được trả lại. Đơn <strong>không</strong> đóng.</td></tr>
<tr><td><strong>Từ chối</strong></td><td>Không cho nghỉ</td><td><strong>Đóng hẳn</strong> — người nộp phải lập đơn khác. Phép được trả lại.</td></tr>
</tbody>
</table>
<p><strong>Duyệt đơn</strong> không bắt ghi lý do, ô ý kiến để trống cũng bấm được. <strong>Trả về</strong> và <strong>Từ chối</strong> thì <strong>bắt buộc</strong> — nút không bấm được cho tới khi có chữ, và gõ toàn dấu cách không tính. Người nhận chỉ đọc được đúng dòng bạn ghi, nên viết cho rõ phải sửa gì:</p>
<ul>
<li><em>Thiếu người bàn giao, bổ sung rồi gửi lại.</em> — trả về</li>
<li><em>Trùng lịch nghỉ của cả phòng, dời sang tuần sau.</em> — từ chối</li>
</ul>

<h2>Bốn điều đáng biết</h2>
<ul>
<li><strong>Đang có việc trên tờ đơn thì bạn đọc được nó</strong>, kể cả khi phạm vi dữ liệu của bạn không với tới — thường gặp với trưởng phòng Nhân sự ký chặng 2 cho nhân viên phòng khác. <strong>Ký xong quyền đó đóng lại</strong>; muốn xem lại thì vào tab <strong>Tôi đã duyệt</strong> (30 ngày gần đây).</li>
<li><strong>Người nộp không tự duyệt đơn của mình</strong> — hệ loại họ khỏi danh sách người ký được suy ra (trưởng phòng, quản lý trực tiếp, theo vai trò). Vì vậy mỗi chặng đều phải khai <strong>người dự phòng</strong>, nếu không thì trưởng phòng tự xin nghỉ sẽ không có ai ký và đơn kẹt. Riêng bước khai <strong>đích danh</strong> một người thì hệ giữ đúng người đã khai, trừ khi công ty bật <strong>Chặn tự duyệt đơn nghỉ</strong> ở Cài đặt nhân sự; khi đó người nghỉ bấm duyệt sẽ nhận câu <em>Cài đặt nhân sự đang chặn tự duyệt: bạn không duyệt được đơn nghỉ của chính mình.</em></li>
<li>Chỗ nào <strong>chưa khai luồng duyệt</strong> thì người có quyền duyệt bấm <strong>Duyệt đơn</strong> thẳng trên đơn. Đơn <em>đang</em> chạy trong luồng thì đường tắt đó bị chặn — không chặn là mở một lối đi vòng qua cả luồng.</li>
<li>Duyệt xong <strong>không rút lại được</strong>. Cần chặn một đơn đã duyệt thì bảo người nộp <strong>hủy đơn</strong>, phép sẽ được hoàn.</li>
</ul>

<h2>Đơn rơi vào ngày cấm nghỉ</h2>
<p>Trang chi tiết đơn hiện <strong>khung vàng</strong> <em>Đơn nghỉ này rơi vào ngày cấm nghỉ.</em> kèm ngày và lý do. Duyệt các chặng giữa vẫn được; ở <strong>chặng cuối</strong> (hoặc khi duyệt thẳng) hệ chặn với câu <em>Đơn nghỉ này rơi vào ngày cấm nghỉ: … Chưa duyệt được — nhờ người có vai trò được miễn (Cài đặt nhân sự › Nghỉ phép) duyệt, hoặc trả đơn về để người nghỉ đổi ngày.</em> Đơn vẫn ở <em>Chờ duyệt</em>, phép vẫn đang giữ chỗ, không có gì bị trừ. Bạn có hai đường: bấm <strong>Trả về</strong> để người nghỉ đổi ngày, hoặc chuyển cho quản trị hay người có vai trò được miễn duyệt.</p>
<p>Cách khai luồng: {ref(NS_QUYEN, "bài Phân quyền và luồng duyệt")}.</p>""",
        },
        {
            "title": LICH_NGHI,
            "icon": "users",
            "summary": "Ba chế độ ngày / tuần / tháng, cách lọc, và lịch KHÔNG hiện đơn nào",
            "content": f"""<h2>Xem Lịch nghỉ</h2>
<p>Mục <strong>Nhân sự ▸ Nghỉ phép ▸ Lịch nghỉ</strong> — trả lời câu <em>tuần sau ai nghỉ</em> mà không phải mở từng tờ đơn.</p>

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
<tr><td><strong>Tháng</strong></td><td>Lưới 42 ô. Mỗi ô liệt kê vài người, quá thì gộp thành nút <strong>+N người nữa</strong> — bấm vào là mở <strong>đúng ngày đó</strong> ở chế độ Ngày.</td><td>Nhìn toàn cảnh, tránh dồn nghỉ</td></tr>
</tbody>
</table>
<p>Ô lọc loại nghỉ ở chế độ Ngày <strong>chỉ bày loại có mặt trong ngày đó</strong>, và <strong>tự ẩn khi cả ngày chỉ có một loại</strong> — một lựa chọn thì lọc được gì.</p>

<h2>Đọc lịch</h2>
<ul>
<li>Bấm vào một dòng để <strong>mở thẳng tờ đơn</strong>.</li>
<li><strong>Ngày lễ</strong> hiện tên lễ ngay trên ô của nó, kèm ghi chú là ngày đó không tính vào phép.</li>
<li>Không ai nghỉ thì lịch <strong>nói rõ</strong> (<em>Không ai nghỉ ngày này.</em> / <em>Cả tuần này không ai nghỉ.</em>) chứ không để bảng trống trơn — trống trơn thì không biết là không ai nghỉ hay là màn hình lỗi.</li>
<li>Tìm không ra ai khớp bộ lọc thì câu báo <strong>khác hẳn</strong> câu <em>không ai nghỉ</em>, để bạn biết là do bộ lọc.</li>
</ul>

<p>Đơn nghỉ <strong>nhiều khoảng ngày</strong> chỉ tô đúng những ngày nằm trong từng khoảng; các ngày nằm giữa hai khoảng để trống (người đó đi làm).</p>

<h2>Lịch KHÔNG hiện những đơn nào</h2>
<p><strong>Nháp · Từ chối · Đã hủy</strong> — ba loại này không dẫn tới ai nghỉ cả, vẽ lên lịch chỉ làm người xem tưởng phòng vắng người.</p>

<h2>Phạm vi dữ liệu</h2>
<p>Lịch chỉ hiện đơn <strong>trong phạm vi dữ liệu của bạn</strong>: trưởng bộ phận thấy người trong bộ phận mình, nhân viên thường chỉ thấy đơn của chính mình. Thấy lịch trống trơn trong khi biết chắc có người nghỉ thì đó là phạm vi, không phải lỗi — xem {ref(NS_QUYEN, "bài Phân quyền")}.</p>""",
        },
        {
            "title": NGHI_BU,
            "icon": "calendar-plus",
            "summary": "Đi làm ngày lễ hoặc ngày nghỉ thì lập phiếu xin nghỉ bù ở Nghỉ phép ▸ Nghỉ bù; duyệt xong ngày bù cộng vào quỹ phép; hủy phiếu, câu báo lỗi, ai duyệt",
            "content": f"""<h2>Xin nghỉ bù</h2>
<p>Bạn đã đi làm vào <strong>ngày lễ</strong> hoặc vào <strong>ngày nghỉ theo lịch làm việc</strong> của mình (ví dụ Chủ nhật)? Lập một <strong>phiếu nghỉ bù</strong> để được cộng ngày nghỉ bù vào quỹ phép. Phiếu không phải đơn nghỉ: duyệt xong bạn mới có thêm ngày, rồi nộp đơn nghỉ như bình thường để dùng ngày đó.</p>

<h2>Lập phiếu</h2>
<ol>
<li>Vào <strong>Nhân sự ▸ Nghỉ phép ▸ Nghỉ bù</strong>. Màn <strong>Phiếu nghỉ bù</strong> mở ra; ô <strong>Phạm vi</strong> chọn <em>Của tôi</em>, <em>Cần tôi duyệt</em> (kèm số phiếu đang chờ bạn) hoặc <em>Tất cả trong phạm vi</em>.</li>
<li>Bấm <strong>Lập phiếu nghỉ bù</strong> ở góc trên bên phải.</li>
<li>Điền thẻ <strong>Phiếu xin nghỉ bù</strong>:
<ul>
<li><strong>Người nghỉ</strong>: mặc định là bạn. Ô này chỉ hiện với người xem được danh bạ nhân sự; lập hộ người khác cần quyền tạo phiếu trong phạm vi của người đó. Sau khi lưu thì không đổi được người nghỉ.</li>
<li><strong>Ngày đã đi làm</strong>: ngày lễ hoặc ngày nghỉ theo lịch làm việc mà bạn đã đi làm. Không chọn ngày tương lai, và chỉ nhận ngày từ <strong>01/01 của năm trước</strong> trở đi.</li>
<li><strong>Số ngày xin nghỉ bù</strong>: chọn <strong>Nửa ngày (0,5)</strong> hoặc <strong>Cả ngày (1)</strong>.</li>
<li><strong>Lý do đi làm</strong>: làm việc gì, theo yêu cầu của ai, để người duyệt không phải hỏi lại. Tối đa 1000 ký tự, bắt buộc khi gửi duyệt.</li>
</ul></li>
<li>Bấm <strong>Lưu nháp</strong> để để dành, hoặc <strong>Gửi duyệt</strong> (hệ lưu rồi gửi luôn).</li>
</ol>
<p>Mỗi ngày đi làm chỉ có <strong>một phiếu</strong> còn hiệu lực. Phiếu đã hủy hoặc bị từ chối thì không tính, nên bạn lập lại được cho đúng ngày đó.</p>

<h2>Ai duyệt và duyệt thế nào</h2>
<ul>
<li>Công ty đã khai <strong>luồng duyệt</strong> cho <em>Phiếu nghỉ bù</em> ở phân hệ Phê duyệt thì phiếu đi qua luồng đó; người được giao mở phiếu (từ thông báo chuông hoặc <em>Cần tôi duyệt</em>) và bấm <strong>Duyệt phiếu</strong>, <strong>Trả về</strong> hoặc <strong>Từ chối</strong>. Trả về và Từ chối bắt ghi lý do.</li>
<li>Chưa khai luồng thì người có quyền duyệt Phiếu nghỉ bù bấm thẳng <strong>Duyệt phiếu</strong> hoặc <strong>Từ chối</strong> trên trang chi tiết.</li>
<li>⚠️ <strong>Không ai tự duyệt được phiếu nghỉ bù của chính mình</strong>, bất kể công tắc ở Cài đặt nhân sự, vì phiếu này tạo ra ngày phép mới. Trong luồng, bước chỉ có chính người nghỉ sẽ chuyển cho người dự phòng của bước (không có người dự phòng thì phiếu dừng lại chờ quản trị sửa luồng); khi duyệt thẳng, người nghỉ bấm duyệt sẽ nhận câu <em>Bạn không được tự duyệt phiếu nghỉ bù của chính mình.</em></li>
</ul>

<h2>Kết quả lên quỹ phép</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Quỹ phép của bạn</th></tr></thead>
<tbody>
<tr><td><strong>Đã duyệt</strong></td><td>Số ngày trên phiếu được cộng vào quỹ của loại nghỉ nhận ngày bù (thường là Phép năm), hiện thành cột <strong>Nghỉ bù cộng thêm</strong> ở Quỹ phép năm. Ngày đi làm thuộc năm nay thì cộng vào quỹ năm nay. Ngày đi làm thuộc <strong>năm trước</strong> thì vẫn cộng vào quỹ <strong>năm nay</strong>, vì quỹ năm cũ đã kết sổ.</td></tr>
<tr><td><strong>Nháp · Chờ duyệt · Trả về chỉnh sửa · Từ chối</strong></td><td>Không đổi gì, vì phiếu chưa cộng ngày nào.</td></tr>
</tbody>
</table>
<p>Loại nghỉ nhận ngày bù được chốt <strong>lúc bạn gửi duyệt</strong>. Phòng Nhân sự đổi danh mục giữa chừng thì phiếu vẫn cộng đúng vào loại đã chốt.</p>

<h2>Sửa, xóa, hủy phiếu</h2>
<table>
<thead><tr><th>Trạng thái</th><th>Làm được gì</th></tr></thead>
<tbody>
<tr><td><strong>Nháp</strong></td><td>Sửa ngày, số ngày, lý do; bấm <strong>Xóa phiếu</strong> để bỏ hẳn.</td></tr>
<tr><td><strong>Trả về chỉnh sửa</strong></td><td>Sửa đúng chỗ người duyệt nêu rồi bấm <strong>Gửi duyệt</strong> lại; vẫn giữ số phiếu cũ.</td></tr>
<tr><td><strong>Chờ duyệt</strong></td><td>Không sửa được. Bấm <strong>Hủy phiếu</strong> (bắt ghi lý do) nếu không cần nữa; luồng duyệt đang chạy được rút trước.</td></tr>
<tr><td><strong>Đã duyệt</strong></td><td>Bấm <strong>Hủy phiếu</strong> thì hệ trừ lại đúng số ngày đã cộng. Chỉ hủy được khi số ngày còn dùng được của loại đó vẫn đủ; nếu bạn đã dùng ngày bù để nghỉ thì phải hủy đơn nghỉ đó trước.</td></tr>
</tbody>
</table>

<h2>Câu báo lỗi hay gặp</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Ngày này là ngày làm việc bình thường của bạn nên không có ngày nghỉ bù. Chỉ xin được cho ngày lễ hoặc ngày nghỉ theo lịch làm việc.</em></td><td>Theo lịch làm việc của bạn, hôm đó là ngày đi làm (kể cả nửa ngày, ví dụ sáng thứ Bảy).</td><td>Chọn đúng ngày nghỉ bạn đã đi làm. Lịch làm việc của bạn sai thì báo phòng Nhân sự.</td></tr>
<tr><td><em>Ngày đi làm không được ở tương lai — đi làm xong mới xin nghỉ bù</em></td><td>Bạn chọn ngày chưa tới.</td><td>Đợi đi làm xong mới lập phiếu.</td></tr>
<tr><td><em>Ngày đi làm quá cũ — chỉ xin nghỉ bù cho ngày từ 01/01/… trở đi</em></td><td>Ngày đi làm trước 01/01 của năm trước.</td><td>Không lập phiếu được nữa; cần thì nhờ phòng Nhân sự điều chỉnh tay quỹ phép kèm lý do.</td></tr>
<tr><td><em>Ngày … đã có phiếu nghỉ bù NB… — mỗi ngày một phiếu</em></td><td>Ngày này đã có một phiếu khác còn hiệu lực.</td><td>Mở phiếu đó ra xem. Muốn lập lại thì hủy phiếu cũ trước.</td></tr>
<tr><td><em>Phiếu vừa được xử lý bởi lượt khác — tải lại trang</em></td><td>Bạn bấm hai lần liền, hoặc người khác vừa duyệt / hủy phiếu này cùng lúc.</td><td>Tải lại trang để thấy trạng thái mới. Hệ chỉ ghi nhận một lượt, ngày bù không bị cộng hai lần.</td></tr>
<tr><td><em>Không hủy được: ngày nghỉ bù của phiếu này (… ngày) đã được dùng để nghỉ.</em></td><td>Số ngày còn dùng được của loại nhận ngày bù đã ít hơn số ngày trên phiếu.</td><td>Hủy hoặc sửa đơn nghỉ đã dùng quỹ này trước, rồi hủy phiếu.</td></tr>
<tr><td><em>Chưa có loại nghỉ nào bật «Loại nhận ngày nghỉ bù»…</em></td><td>Danh mục Loại nghỉ chưa có loại nào nhận ngày bù.</td><td>Phòng Nhân sự vào <strong>Nghỉ phép ▸ Thiết lập ▸ Loại nghỉ</strong>, mở một loại (thường là Phép năm), bật <strong>Loại nhận ngày nghỉ bù</strong> và <strong>Trừ vào quỹ phép năm</strong>, rồi lưu. Nhiều loại cùng bật thì hệ lấy loại xếp trước.</td></tr>
</tbody>
</table>

<h2>Ai thấy phiếu</h2>
<p>Nhân viên thấy phiếu mình lập hoặc phiếu người khác lập hộ mình; trưởng bộ phận thấy phiếu của bộ phận mình; người đang có việc duyệt trên phiếu thì mở được phiếu đó. Khóa quyền riêng là <strong>Nghỉ phép › Phiếu nghỉ bù</strong>; không thấy mục <strong>Nghỉ bù</strong> trong menu thì xem {ref(NS_QUYEN, "bài Phân quyền và luồng duyệt")}.</p>""",
        },
        {
            "title": TINH_HUONG,
            "icon": "lightbulb",
            "summary": "Nghỉ ốm đột xuất, nửa buổi, cưới hỏi, thai sản, nghỉ quá quỹ, đổi ngày sau khi duyệt",
            "content": f"""<h2>Mười tình huống nghỉ thường gặp</h2>
<p>Mỗi ô dưới đây là một tình huống có thật, kèm cách làm đúng ngay lần đầu.</p>

<h3>1. Sáng ngủ dậy thấy ốm, chưa kịp xin phép</h3>
<p>Chọn loại <strong>Nghỉ ốm đau</strong> và nộp ngay trong ngày — hệ không có luật "phải nộp trước N ngày", nên nộp sát ngày hay nộp trong ngày đều được. Loại này thường <strong>bắt buộc đính kèm</strong> giấy khám: lưu nháp trước, có giấy thì tải lên mục <strong>Tệp đính kèm</strong> rồi mới gửi duyệt. Nếu công ty bật <strong>Chặn đơn nghỉ lùi ngày</strong> thì để qua hôm sau mới nộp là bị chặn — khi đó nhờ phòng Nhân sự lập hộ.</p>

<h3>2. Chỉ nghỉ buổi chiều</h3>
<p><strong>Từ ngày = Đến ngày</strong>, <strong>Buổi bắt đầu = Buổi kết thúc = Buổi chiều</strong>. Tổng số ngày ra <strong>0,5</strong>.</p>
<p>Ngược lại, <em>chiều hôm nay đến sáng hôm nay</em> là khoảng trống — hệ chặn.</p>

<h3>3. Nghỉ dài hơn số phép còn lại</h3>
<p>Mặc định không có ứng phép (trừ khi phòng Nhân sự bật <strong>Cho ứng phép tối đa</strong> cho loại nghỉ đó, xem {ref(QUY_PHEP, "bài Hiểu số ngày phép còn lại")}). Một đơn khai được nhiều loại nghỉ, nên cách gọn nhất là chia tổng số ngày thành hai dòng: dòng <em>Phép năm</em> đúng bằng số còn lại, dòng <strong>Nghỉ không lương</strong> cho phần dôi ra. Muốn tách hẳn thì lập <strong>hai đơn</strong>.</p>
<p>⚠️ Nếu tách hai đơn thì hai đơn <strong>không được chồng ngày</strong> — cùng một ngày nằm trên hai đơn là bị chặn. Chia theo ngày liền mạch: ví dụ 05–09/10 phép năm, 12–16/10 không lương.</p>

<h3>4. Nghỉ vắt qua cuối tuần hoặc ngày lễ</h3>
<p>Cứ chọn khoảng ngày thật (ví dụ thứ Sáu đến thứ Ba). Hệ <strong>tự trừ</strong> ngày nghỉ theo lịch làm việc của bạn và ngày lễ ra khỏi <strong>Tổng số ngày</strong> — bạn không phải cắt đơn làm đôi.</p>

<h3>5. Bộ phận làm lịch khác, hoặc chạy ca</h3>
<p>Máy đếm theo lịch làm việc phòng Nhân sự gán cho bạn. Lịch đó chưa khớp lịch thật thì báo phòng Nhân sự sửa lịch; trong lúc chờ, <strong>gõ đè Tổng số ngày</strong> cho đúng số ngày công thực tế. Chú thích dưới ô sẽ đổi thành <em>Bạn đang nhập tay…</em> — người duyệt nhìn vào biết con số là do bạn khai.</p>

<h3>6. Cưới hỏi, tang chế</h3>
<p>Chọn đúng loại nghỉ tương ứng. Hai loại này thường có <strong>trần 3 ngày mỗi lần</strong> — xin 5 ngày là bị chặn ngay lúc gửi duyệt.</p>

<h3>7. Nghỉ thai sản</h3>
<ul>
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
<tr><td><em>Không đủ phép: <strong>Phép năm</strong> còn 3 ngày, đơn này xin 5 ngày. Muốn nghỉ tiếp thì chọn loại <strong>Nghỉ không lương</strong>.</em></td><td>Xin vượt quỹ, kể cả phần được ứng nếu loại nghỉ có cho ứng phép.</td><td>Giảm số ngày, hoặc tách phần dôi ra thành đơn <strong>Nghỉ không lương</strong>.</td></tr>
<tr><td><em>Đã có đơn <strong>NP012</strong> nghỉ từ … đến … trùng khoảng ngày này.</em></td><td>Bạn đã có một đơn còn hiệu lực chồng lên khoảng ngày này.</td><td>Mở đơn NP012 ra xem. Muốn gộp thì hủy nó rồi nộp một đơn dài; muốn tách thì dời ngày cho khỏi chồng.</td></tr>
<tr><td><em>Thiếu <strong>Lý do nghỉ</strong> — nhập đủ trước khi gửi duyệt.</em></td><td>Ô bắt buộc còn trống.</td><td>Điền rồi <strong>Lưu nháp</strong>, sau đó gửi duyệt lại.</td></tr>
<tr><td><em>Loại nghỉ "Phép năm" chỉ dùng được sau 60 ngày vào làm (từ dd/mm/yyyy).</em></td><td>Loại nghỉ này chỉ dùng được khi đã vào làm đủ số ngày phòng Nhân sự khai. Hệ kiểm cả lúc lập, lúc đổi ngày và lúc gửi duyệt.</td><td>Chọn ngày nghỉ từ mốc trong câu báo trở đi, hoặc chọn loại khác (Nghỉ không lương).</td></tr>
<tr><td><em>Không lập được đơn nghỉ cho ngày đã qua (dd/mm/yyyy). Cài đặt nhân sự đang chặn đơn lùi ngày — nhờ phòng Nhân sự lập hộ nếu cần.</em></td><td>Công ty bật <strong>Chặn đơn nghỉ lùi ngày</strong>, mà đơn có ngày nghỉ trước hôm nay. Nháp lập từ hôm trước mà để qua ngày mới gửi cũng bị chặn.</td><td>Đổi sang ngày từ hôm nay trở đi, hoặc nhờ phòng Nhân sự (vai trò được miễn) lập hộ đơn.</td></tr>
<tr><td><em>Nghỉ cưới hỏi chỉ cho nghỉ tối đa 3 ngày mỗi lần, đơn này xin 5.</em></td><td>Vượt trần của loại nghỉ.</td><td>Cắt bớt, hoặc xin phần dôi bằng loại nghỉ khác.</td></tr>
<tr><td><em>Loại nghỉ <strong>Nghỉ ốm</strong> bắt buộc đính kèm giấy tờ (giấy khám bệnh, giấy chứng nhận…) — tải tệp lên ở mục <strong>Tệp đính kèm</strong> rồi gửi duyệt lại.</em></td><td>Loại nghỉ này đòi giấy tờ mà đơn chưa có tệp nào.</td><td>Mở đơn (vẫn là Nháp), tải tệp ở mục <strong>Tệp đính kèm</strong>, rồi bấm <strong>Gửi duyệt</strong> lại. Chưa có giấy thì để Nháp, đừng lập đơn mới.</td></tr>
<tr><td><em>Loại nghỉ <strong>Thai sản</strong> không áp dụng cho hồ sơ này</em></td><td>Loại nghỉ giới hạn theo giới tính, mà hồ sơ khai không khớp.</td><td>Hồ sơ khai sai thì báo phòng Nhân sự sửa; đúng thì chọn loại khác.</td></tr>
</tbody>
</table>

<h2>Lúc chọn ngày</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Đến ngày phải bằng hoặc sau Từ ngày</em></td><td>Chọn ngược ngày.</td><td>Đổi lại hai ô.</td></tr>
<tr><td><em>Khoảng thứ 2 (01/11 → 01/11) không có ngày làm việc nào theo lịch làm việc … Bỏ khoảng này khỏi đơn.</em></td><td>Đơn nhiều khoảng có một khoảng rơi trọn vào ngày nghỉ (Chủ nhật, ngày lễ).</td><td>Bỏ khoảng đó khỏi đơn — ngày nghỉ sẵn thì không cần xin. Đơn nhiều khoảng không cho gõ đè tổng để vượt qua chốt này.</td></tr>
<tr><td><em>Khoảng thứ 1 (27/10 → 29/10) và Khoảng thứ 2 (29/10 → 30/10) chồng ngày nhau — các khoảng không được trùng ngày.</em></td><td>Hai khoảng trong cùng một đơn có ngày trùng nhau.</td><td>Dời ngày để các khoảng không trùng (sát nhau thì được), hoặc gộp thành một khoảng.</td></tr>
<tr><td><em>Đơn nhiều khoảng ngày phải nằm trong cùng một năm. Tách thành hai đơn…</em></td><td>Đơn có từ hai khoảng trở lên mà các khoảng rơi vào hai năm khác nhau.</td><td>Lập hai đơn: một đơn cho phần năm trước, một đơn cho phần năm sau.</td></tr>
<tr><td><em>Nghỉ theo giờ chỉ khai được một khoảng ngày…</em></td><td>Đơn có từ hai khoảng mà một khoảng chọn <strong>Theo giờ</strong>.</td><td>Bỏ bớt khoảng, hoặc chọn lại buổi nghỉ (Cả ngày / Sáng / Chiều).</td></tr>
<tr><td><em>Nghỉ từ buổi chiều đến buổi sáng cùng ngày là khoảng trống</em></td><td>Buổi bắt đầu là chiều, buổi kết thúc là sáng, cùng một ngày — không có khoảng nào.</td><td>Chọn cùng một buổi cho cả hai ô.</td></tr>
<tr><td><em>Khoảng ngày này không có ngày làm việc nào (rơi trọn vào cuối tuần hoặc ngày lễ). Sửa lại ngày, hoặc nhập tay <strong>Tổng số ngày</strong>.</em></td><td>Cả khoảng bạn chọn đều là ngày nghỉ sẵn.</td><td>Không cần xin phép thì thôi. Bộ phận có làm ngày đó thì <strong>gõ đè Tổng số ngày</strong>.</td></tr>
<tr><td><em>Tổng số ngày phải lớn hơn 0</em></td><td>Bạn xóa trắng hoặc gõ 0 vào ô số ngày.</td><td>Nhập số đúng, hoặc xóa ô để hệ tính lại.</td></tr>
</tbody>
</table>

<h2>Lúc duyệt</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Đơn nghỉ này rơi vào ngày cấm nghỉ: … Chưa duyệt được — nhờ người có vai trò được miễn (Cài đặt nhân sự › Nghỉ phép) duyệt, hoặc trả đơn về để người nghỉ đổi ngày.</em></td><td>Đơn đụng một khoảng ở <strong>Nghỉ phép ▸ Thiết lập ▸ Ngày cấm nghỉ</strong>, và người bấm duyệt chặng cuối (hoặc duyệt thẳng) không thuộc vai trò được miễn.</td><td>Bấm <strong>Trả về</strong> để người nghỉ đổi ngày, hoặc nhờ quản trị / người có vai trò được miễn duyệt. Đơn vẫn Chờ duyệt, quỹ phép không bị trừ.</td></tr>
<tr><td><em>Cài đặt nhân sự đang chặn tự duyệt: bạn không duyệt được đơn nghỉ của chính mình.</em></td><td>Công ty bật <strong>Chặn tự duyệt đơn nghỉ</strong>, mà bạn đang duyệt đơn của chính mình.</td><td>Nhờ quản trị chuyển việc duyệt đó cho người khác ở màn quản lý luồng duyệt.</td></tr>
<tr><td><em>Bạn không được tự duyệt phiếu nghỉ bù của chính mình.</em></td><td>Phiếu nghỉ bù luôn chặn tự duyệt, không phụ thuộc công tắc nào.</td><td>Để người khác có quyền duyệt xử lý. Xem {ref(NGHI_BU, "bài Xin nghỉ bù")}.</td></tr>
</tbody>
</table>

<h2>Lúc sửa hoặc gửi lại</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Đơn đã gửi duyệt nên không sửa được. Rút phiếu duyệt hoặc hủy đơn…</em></td><td>Đơn đang trong luồng, đã khóa.</td><td><strong>Hủy đơn</strong> rồi nộp lại, hoặc nhờ người duyệt <strong>Trả về</strong> để sửa mà giữ nguyên số đơn.</td></tr>
<tr><td><em>Đơn này đã gửi duyệt rồi</em></td><td>Bấm <strong>Gửi duyệt</strong> hai lần.</td><td>Không phải lỗi. Tải lại trang là thấy trạng thái <em>Chờ duyệt</em>.</td></tr>
</tbody>
</table>

<h2>Lỗi về tài khoản</h2>
<table>
<thead><tr><th>Câu bạn nhìn thấy</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Chưa xác định được người nghỉ — tài khoản này chưa gắn hồ sơ nhân sự.</em></td><td>Tài khoản đăng nhập chưa nối với một hồ sơ nhân sự nào, nên hệ không biết trừ phép của ai.</td><td>Báo phòng Nhân sự gắn hồ sơ. Không tự sửa được.</td></tr>
<tr><td>Không thấy menu <strong>Nghỉ phép</strong>, hoặc thiếu tab</td><td>Phân quyền — các khóa quyền của Nghỉ phép (kể cả <em>Phiếu nghỉ bù</em>) là khóa mới, vai trò cũ không tự có.</td><td>Xin quản trị tick thêm, xem {ref(NS_QUYEN, "bài Phân quyền")}.</td></tr>
<tr><td>Hệ báo <em>Không tìm thấy</em> khi mở một tờ đơn</td><td>Đơn nằm ngoài <strong>phạm vi dữ liệu</strong> của bạn.</td><td>Xin mở rộng phạm vi, hoặc nhờ người trong phạm vi xử lý.</td></tr>
<tr><td>Bấm <strong>In</strong> ra trang <em>Không có quyền mở bản in</em></td><td>Tài khoản chưa có quyền xem đơn nghỉ phép (trang in kiểm quyền trước khi mở, từ 22/10/2026).</td><td>Nhờ quản trị cấp quyền xem Đơn nghỉ phép, rồi đăng xuất đăng nhập lại.</td></tr>
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
<p>Mục <strong>Nhân sự ▸ Nghỉ phép ▸ Quỹ phép năm</strong> (khóa quyền <code>leave_balance</code>). Mỗi dòng là <strong>một người × một năm × một loại nghỉ</strong>.</p>

<h2>Đọc bảng</h2>
<table>
<thead><tr><th>Cột</th><th>Nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Nhân sự</strong></td><td>Người sở hữu dòng quỹ.</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Mỗi loại nghỉ có trừ quỹ là một dòng riêng.</td></tr>
<tr><td><strong>Hạn mức</strong></td><td>Chép tại lúc cấp phát: mức của nhóm khớp ở tab <em>Hạn mức theo nhóm</em> (hình thức nhân viên trước, cấp bậc sau), không có thì <em>Hạn mức mỗi năm</em> của loại nghỉ; đã nhân tỷ lệ nếu loại nghỉ cấp <em>theo tỷ lệ tháng làm việc</em> hoặc <em>cộng dần</em>.</td></tr>
<tr><td><strong>Thâm niên</strong></td><td>Cộng thêm theo bậc, tính tại 01/01.</td></tr>
<tr><td><strong>Chuyển năm trước</strong></td><td>Phép tồn mang sang.</td></tr>
<tr><td><strong>Điều chỉnh tay</strong></td><td>Cột duy nhất nhận <strong>số âm</strong>; số dương hiện kèm dấu <code>+</code>.</td></tr>
<tr><td><strong>Nghỉ bù cộng thêm</strong></td><td>Ngày của các phiếu nghỉ bù đã duyệt. Cột này <strong>ẩn sẵn</strong>; bật ở menu <strong>Cột</strong> của bảng. Trang chi tiết một dòng quỹ thì tự hiện ô này khi có số.</td></tr>
<tr><td><strong>Đã nghỉ</strong></td><td>Cộng dồn đơn đã duyệt.</td></tr>
<tr><td><strong>Còn lại</strong></td><td>Số còn <strong>dùng được hôm nay</strong>: với loại <em>Cộng dần theo tháng</em> đã trừ phần chưa tới tháng. <strong>Hết phép thì tô đỏ</strong> — đó là thứ cần thấy ngay. Báo cáo <em>Quỹ phép năm</em> ở phân hệ Báo cáo cho ra đúng số này.</td></tr>
</tbody>
</table>
<p>Bộ lọc: ô tìm theo <strong>tên hoặc mã nhân sự</strong>, ô chọn <strong>loại nghỉ</strong>, ô chọn <strong>năm</strong>.</p>

<h2>Cấp quỹ đầu năm</h2>
<p>Nút <strong>Cấp quỹ năm 2026</strong> ở góc trên bên phải (con số đổi theo năm đang chọn). Bảng rỗng thì chính câu trạng thái rỗng đã chỉ đường: <em>Chưa cấp quỹ phép năm 2026. Bấm <strong>Cấp quỹ năm 2026</strong> để tạo.</em></p>
<ul>
<li><strong>Chạy lại được</strong>: chỉ tạo dòng còn thiếu. Bấm hai lần không nhân đôi.</li>
<li>Thêm người giữa năm thì <strong>bấm lại</strong> là họ có quỹ, không phải tạo tay.</li>
<li>Cấp <strong>một lần đầu năm</strong>; thâm niên tính tại 01/01, không cộng dần theo tháng.</li>
<li>Số ngày mỗi người nhận theo <strong>Cách cấp quỹ</strong> của loại nghỉ: <em>Đủ hạn mức đầu năm</em> thì ai cũng đủ; <em>Theo tỷ lệ tháng làm việc</em> thì người vào làm trong năm nhận theo số tháng còn lại (vào làm ngày 1–15 tính cả tháng, từ ngày 16 tính từ tháng sau, làm tròn tới nửa ngày; ví dụ hạn mức 12, vào làm 10/03 được 10 ngày, vào làm 20/03 được 9 ngày); <em>Cộng dần theo tháng</em> thì dòng quỹ ghi đủ cả năm nhưng mỗi tháng mới mở thêm một phần mười hai. Xem {ref(NS_DANH_MUC, "bài Loại nghỉ")}.</li>
</ul>
<p>⚠️ Cố ý <strong>không cập nhật dòng đã có</strong> theo hạn mức mới: đổi hạn mức giữa năm thì quỹ đã cấp giữ nguyên, luật mới áp cho lần cấp sau. Muốn áp ngay cho vài người thì dùng <strong>điều chỉnh tay</strong>.</p>
<p>⚠️ Cấp quỹ <strong>trước khi</strong> hồ sơ có <strong>ngày vào làm</strong> thì thâm niên ra 0. Nhập bù ngày vào làm rồi phải sửa lại bằng điều chỉnh tay — cấp lại không sửa dòng cũ.</p>

<h2>Điều chỉnh tay</h2>
<p>Mở một dòng quỹ ra, dùng thẻ <strong>Điều chỉnh tay</strong>: nhập số và <strong>lý do</strong>, bấm <strong>Lưu điều chỉnh</strong>.</p>
<ul>
<li>⚠️ <strong>GHI ĐÈ, không cộng dồn.</strong> Ô nạp sẵn số của lần chỉnh trước; bạn gõ con số bạn muốn nó <em>thành</em>. Cộng dồn thì bấm Lưu hai lần là gấp đôi.</li>
<li>Thẻ nói trước <strong>còn lại sẽ thành bao nhiêu</strong> sau khi lưu — đọc dòng đó rồi hãy bấm.</li>
<li><strong>Bắt buộc có lý do</strong>, khoảng trắng không tính. Đây là thao tác <em>tặng ngày phép cho người khác</em> nên phải để lại dấu vết đọc được: <em>Bù phép tồn 2025</em>, <em>Cấp nhầm, trừ lại</em>.</li>
<li>Nhận <strong>số âm</strong> để trừ bớt.</li>
</ul>
<p>Trang chi tiết có khối <strong>Lịch sử thao tác</strong> — nhìn con số hiện tại không biết ai đưa nó tới đó, nên <strong>đọc lịch sử trước khi sửa tiếp</strong>. Chưa từng chỉnh tay thì khối đó không hiện dòng rỗng nào.</p>
<p>Trang chi tiết cũng liệt kê <strong>các đơn nghỉ</strong> đã ăn vào dòng quỹ này, để đối chiếu khi người dùng kêu sai số.</p>

<h2>Kết sổ cuối năm và bảng Đối chiếu</h2>
<p>Phép năm cũ còn dư đi đâu là do từng <em>Loại nghỉ</em> khai: <strong>Hết năm là mất</strong> (mặc định), <strong>Mang sang năm sau</strong> hoặc <strong>Quy đổi sang loại nghỉ khác</strong>. ⚠️ <strong>Không có gì tự chạy đêm 31/12</strong> — phải có người bấm nút <strong>Kết sổ năm …</strong> ở góc trên màn <em>Quỹ phép năm</em> (năm đang xem trừ một; cần quyền ghi Quỹ phép). Hộp xác nhận <em>Kết sổ quỹ phép năm …?</em> nhắc rằng loại để mặc định <strong>Hết năm là mất</strong> thì không đụng tới; bấm lại lần hai không nhân đôi số ngày.</p>
<p>Kết sổ xong, hộp <strong>Đối chiếu kết sổ phép năm …</strong> <strong>tự mở</strong> để bạn soát ngay kết quả. Mỗi dòng là một người × một loại nghỉ nguồn:</p>
<table>
<thead><tr><th>Cột</th><th>Nghĩa là</th></tr></thead>
<tbody>
<tr><td><strong>Nhân sự</strong></td><td>Tên và mã người có quỹ.</td></tr>
<tr><td><strong>Loại nghỉ</strong></td><td>Loại nghỉ có số dư năm cũ (ví dụ Phép năm).</td></tr>
<tr><td><strong>Số cũ (trước)</strong></td><td>Số ngày còn của năm cũ <strong>trước</strong> khi kết sổ.</td></tr>
<tr><td><strong>Số mới (sau)</strong></td><td>Số ngày còn của năm cũ <strong>sau</strong> khi kết sổ — phần đã chuyển đi không còn nằm ở đây.</td></tr>
<tr><td><strong>Chênh</strong></td><td><strong>Số mới trừ số cũ</strong>, nên thường là <strong>số âm</strong> — đúng bằng phần ngày đã chuyển đi khỏi năm cũ.</td></tr>
<tr><td><strong>Sang loại</strong></td><td>Loại nghỉ nhận phần chuyển ở năm sau (với <strong>Mang sang năm sau</strong> thì chính là loại đó). Ghi <em>Chưa khai</em> nghĩa là loại quy đổi này chưa khai loại nhận — nhờ phòng Nhân sự khai ở Thiết lập ▸ Loại nghỉ.</td></tr>
<tr><td><strong>Cộng vào năm sau</strong></td><td>Số ngày được cộng sang năm sau = phần đã chuyển đi × tỷ lệ quy đổi của loại nghỉ (mang sang nguyên loại thì tỷ lệ là 1; quy đổi 2 ngày lấy 1 ngày bù thì chỉ bằng một nửa).</td></tr>
</tbody>
</table>
<p>Cuối hộp có dòng tổng (<em>Tổng N dòng: số cũ … → số mới … (chênh …), cộng vào năm sau … ngày</em>). Muốn đối chiếu lại sau này hay gửi người khác soát: bấm nút <strong>Đối chiếu kết sổ …</strong> cạnh nút Kết sổ rồi bấm <strong>Xuất Excel</strong> trong hộp (nút này chỉ hiện với người có quyền xuất Quỹ phép năm).</p>
<p>⚠️ <strong>Hạn chế cần biết:</strong> hệ <strong>không chụp ảnh</strong> lúc bấm Kết sổ. <strong>Số cũ</strong> được <strong>tính lại mỗi lần mở bảng</strong> từ sổ quỹ hiện tại. Vì vậy nếu có đơn của năm cũ được duyệt hoặc bị hủy <em>sau</em> khi kết sổ thì các số trong bảng đổi theo; cột <strong>Sang loại</strong> và <strong>Cộng vào năm sau</strong> cũng tính theo cấu hình loại nghỉ <em>hiện hành</em> (sửa cấu hình sau khi kết sổ thì đó chỉ là số ước theo cấu hình mới). Bảng chỉ liệt kê loại nghỉ đang khai <strong>Mang sang</strong> hoặc <strong>Quy đổi</strong>. Cần lưu số đúng ngày kết sổ thì xuất Excel ngay lúc đó.</p>

<h2>Người dùng kêu <em>số phép của tôi sai</em></h2>
<ol>
<li>Mở dòng quỹ của họ, đọc <strong>đủ bảy số cấu thành</strong> — thường lệch ở <em>thâm niên</em> (thiếu ngày vào làm) hoặc <em>chuyển năm trước</em>.</li>
<li>Xem khối <strong>các đơn nghỉ</strong>: phần <em>đang chờ duyệt</em> cũng đã bị trừ, và người dùng hay quên điều này — xem {ref(QUY_PHEP, "bài Hiểu số ngày phép còn lại")}.</li>
<li>Vẫn sai thì <strong>điều chỉnh tay</strong> kèm lý do nói rõ vì sao.</li>
</ol>""",
        },
        {
            "title": NS_DANH_MUC,
            "icon": "settings",
            "summary": "Khai luật cho từng loại nghỉ, bảng bậc thâm niên, cái bẫy Tết Âm lịch, và khoảng Ngày cấm nghỉ",
            "content": f"""<h2>Nhân sự — Loại nghỉ, bậc thâm niên và Lịch ngày lễ</h2>
<p>Vào <strong>Nhân sự ▸ Nghỉ phép ▸ Thiết lập</strong>. Đầu trang có ba thẻ chuyển qua lại: <strong>Loại nghỉ</strong> · <strong>Lịch ngày lễ</strong> · <strong>Ngày cấm nghỉ</strong> (mỗi thẻ chỉ hiện với người được sửa danh mục đó). Đây là nơi <strong>đổi luật bằng dữ liệu</strong> — không phải sửa mã, không phải chờ bản cập nhật.</p>

<h2>Thiết lập ▸ Loại nghỉ</h2>
<p>Nút <strong>Thêm loại nghỉ</strong> mở <strong>một trang riêng</strong> chứ không mở hộp thoại, vì form dài. Trang làm theo kiểu ERPNext: một mặt phẳng trắng, hàng tiêu đề <strong>dính</strong> ở trên (mũi tên lùi về danh sách, tên loại nghỉ, nhãn trạng thái, nút <strong>Lưu</strong> — lúc thêm mới là <strong>Tạo loại nghỉ</strong>), ngay dưới là dải tab:</p>
<ul>
<li><strong>Thông tin</strong>: mã, tên và ba nhóm ô <strong>Quỹ phép và lương</strong> · <strong>Điều kiện áp dụng</strong> · <strong>Số dư cuối năm</strong>, mỗi nhóm bấm tiêu đề để gập / mở. Lời giải thích của từng ô nằm sau biểu tượng <strong>(i)</strong> cạnh nhãn (nút <em>Xem giải thích</em>) — bấm vào để đọc. Cuối tab có khối <strong>Hoạt động</strong> ghi ai đã sửa ô nào, lúc nào.</li>
<li><strong>Bậc thâm niên</strong> và <strong>Hạn mức theo nhóm</strong>: chỉ hiện <strong>sau khi đã tạo</strong> loại nghỉ (tạo xong mới có chỗ gắn bảng con).</li>
</ul>
<table>
<thead><tr><th>Ô</th><th>Quyết định điều gì</th></tr></thead>
<tbody>
<tr><td><strong>Mã loại nghỉ</strong></td><td>Chữ thường không dấu, <strong>không đổi được sau khi tạo</strong> vì mã đi vào mọi giấy nghỉ phép đã phát hành.</td></tr>
<tr><td><strong>Trừ vào quỹ phép năm</strong></td><td>Tắt thì loại nghỉ đó không giới hạn số ngày, và màn nộp đơn nói thẳng <em>không giới hạn</em> thay vì hiện số 0. Bật thì mở thêm các ô hạn mức, cách cấp quỹ, ứng phép và loại nhận ngày nghỉ bù.</td></tr>
<tr><td><strong>Có hưởng lương</strong></td><td>Tách khỏi ô trên: nghỉ cưới hỏi vẫn hưởng lương nhưng không ăn vào phép năm.</td></tr>
<tr><td><strong>Hạn mức mỗi năm (ngày)</strong></td><td>Số ngày cấp cho một năm (Phép năm 12…). Muốn mỗi nhóm nhân viên một mức thì khai thêm ở tab <strong>Hạn mức theo nhóm</strong>.</td></tr>
<tr><td><strong>Cách cấp quỹ</strong></td><td>Ba lựa chọn: <strong>Đủ hạn mức đầu năm</strong> (như trước đây, ai cũng nhận đủ); <strong>Theo tỷ lệ tháng làm việc (người vào làm trong năm)</strong> (người vào làm trong năm chỉ nhận hạn mức nhân với số tháng làm chia 12); <strong>Cộng dần theo tháng</strong> (mỗi tháng được dùng thêm một phần mười hai). Vào làm từ ngày 1 đến ngày 15 thì tính cả tháng đó, từ ngày 16 thì tính từ tháng sau; kết quả làm tròn tới nửa ngày. Ví dụ hạn mức 12 ngày, vào làm 10/03 được 10 ngày, vào làm 20/03 được 9 ngày.</td></tr>
<tr><td><strong>Cho ứng phép tối đa (ngày)</strong></td><td>Mặc định <strong>0</strong> là không cho nghỉ quá số còn lại. Điền 3 thì người dùng được xin nghỉ đến khi số còn lại xuống tới âm 3 ngày. Tối đa 30.</td></tr>
<tr><td><strong>Loại nhận ngày nghỉ bù</strong></td><td>Bật cho loại (thường là Phép năm) sẽ được cộng thêm ngày khi phiếu nghỉ bù được duyệt. Cần có đúng một loại bật; nhiều loại cùng bật thì hệ lấy loại xếp trước. Chưa loại nào bật thì không ai lập được phiếu nghỉ bù — xem {ref(NGHI_BU, "bài Xin nghỉ bù")}.</td></tr>
<tr><td><strong>Áp dụng cho giới tính</strong></td><td>Thai sản → nữ. Hồ sơ <strong>chưa khai giới tính vẫn nộp được</strong> — chặn là khóa cả công ty tới khi nhập bù.</td></tr>
<tr><td><strong>Tối đa mỗi lần nghỉ (ngày)</strong></td><td>Cưới hỏi, tang chế thường 3. Đặt <strong>0</strong> = không giới hạn.</td></tr>
<tr><td><strong>Dùng được sau (ngày kể từ ngày vào làm)</strong></td><td>Mặc định <strong>0</strong> là không chặn. Điền 60 thì ngày nghỉ sớm nhất của đơn phải từ ngày thứ 60 kể từ ngày vào làm; đơn sớm hơn bị chặn lúc lập, lúc đổi ngày và lúc gửi duyệt. Hồ sơ chưa có ngày vào làm thì không bị chặn.</td></tr>
<tr><td><strong>Trừ ngày nghỉ theo lịch làm việc và ngày lễ</strong></td><td>Bật thì ngày nghỉ trong tuần theo lịch làm việc của người nghỉ (thường là Chủ nhật) và ngày lễ không tính vào số ngày. ⚠️ <strong>Thai sản phải TẮT</strong> — nghỉ dài liên tục thì đếm cả ngày nghỉ tuần.</td></tr>
<tr><td><strong>Bắt buộc đính kèm</strong></td><td>Bật thì đơn thuộc loại này phải có ít nhất một tệp mới <strong>gửi duyệt</strong> được (lưu nháp thì không chặn). Mục <strong>Tệp đính kèm</strong> trên đơn hiện dấu bắt buộc và dòng nhắc đỏ. Nên bật cho Nghỉ ốm (giấy khám), Nghỉ vợ sinh con (giấy chứng sinh).</td></tr>
<tr><td><strong>Cách xử lý số dư</strong></td><td>Ba nước: <strong>Hết năm là mất</strong> (mặc định), <strong>Mang sang năm sau</strong> (kèm ô <em>Hạn dùng phép mang sang</em>), <strong>Quy đổi sang loại nghỉ khác</strong> (kèm ô <em>Loại nghỉ nhận số ngày</em> và <em>Tỷ lệ quy đổi</em>). Chỉ chạy khi có người bấm <em>Kết sổ</em> ở Quỹ phép năm.</td></tr>
<tr><td><strong>Đang dùng</strong></td><td>Tắt thì loại nghỉ ẩn khỏi ô chọn; đơn cũ giữ nguyên.</td></tr>
</tbody>
</table>
<p>Hệ <strong>không còn</strong> luật "phải nộp trước N ngày" (bỏ từ 05/09/2026), nên form không có ô số ngày báo trước.</p>
<p>⚠️ <strong>Đừng xóa một loại nghỉ đang có đơn.</strong> Ngừng dùng nó thì tắt công tắc <strong>Đang dùng</strong> — đơn cũ vẫn đọc được, còn người mới thì không chọn được nữa.</p>

<h2>Các loại nghỉ chế độ BHXH</h2>
<p>Ngoài các loại nghỉ công ty trả lương, hệ có sẵn <strong>năm loại nghỉ chế độ bảo hiểm xã hội</strong> tách riêng. Ở các loại này người lao động vẫn có tiền thay lương nhưng do <strong>BHXH chi trả, không phải công ty</strong>; chúng <strong>không trừ quỹ phép năm</strong> và bản in đơn đánh vào ô <em>Nghỉ chế độ bảo hiểm</em>.</p>
<table>
<thead><tr><th>Loại nghỉ</th><th>Mức theo Luật BHXH 2024</th><th>Trần trên hệ</th><th>Tính ngày lễ, cuối tuần?</th></tr></thead>
<tbody>
<tr><td><strong>Nghỉ khám thai</strong> (nữ)</td><td>Tối đa 5 lần trong thai kỳ, mỗi lần không quá 2 ngày (Điều 51)</td><td>2 ngày/lần</td><td>Không tính (trừ ra)</td></tr>
<tr><td><strong>Nghỉ sảy thai, phá thai</strong> (nữ)</td><td>10 ngày nếu thai dưới 5 tuần; 20 ngày nếu 5 đến dưới 13 tuần; 40 ngày nếu 13 đến dưới 22 tuần; 50 ngày nếu từ 22 tuần (Điều 52)</td><td>50 ngày/lần</td><td>Có tính</td></tr>
<tr><td><strong>Nghỉ thực hiện biện pháp tránh thai</strong></td><td>Đặt dụng cụ tử cung: không quá 7 ngày; triệt sản (nam hoặc nữ): không quá 15 ngày (Điều 57)</td><td>15 ngày/lần</td><td>Có tính</td></tr>
<tr><td><strong>Nghỉ chăm con ốm</strong></td><td>Con dưới 7 tuổi: 20 ngày làm việc/năm nếu con dưới 3 tuổi, 15 ngày nếu con từ 3 đến dưới 7 tuổi (chế độ ốm đau)</td><td>20 ngày/lần</td><td>Không tính (trừ ra)</td></tr>
<tr><td><strong>Nghỉ dưỡng sức phục hồi sức khỏe</strong></td><td>Sau ốm đau, thai sản, sảy thai: 5 đến 10 ngày; công ty cùng công đoàn quyết định số ngày</td><td>10 ngày/lần</td><td>Có tính</td></tr>
</tbody>
</table>
<p>⚠️ Hệ chỉ chặn <strong>trần mỗi lần</strong>: máy không biết tuổi thai, tuổi con hay ca phẫu thuật, nên người duyệt đối chiếu giấy tờ đính kèm với mức luật ở cột ghi chú của từng loại nghỉ. Bốn loại đầu <strong>bắt buộc đính kèm</strong> giấy của cơ sở y tế.</p>

<p>⚠️ <strong>Đổi cách cấp quỹ hay hạn mức không tính lại quỹ đã cấp.</strong> Chỉ người được cấp quỹ sau khi bạn lưu mới theo luật mới. Ngoại lệ là <strong>Cộng dần theo tháng</strong>: phần chưa tới tháng được trừ ngay khi xem số còn lại, nên đổi sang cách này là có hiệu lực luôn với quỹ năm nay. Số ngày thâm niên, phép mang sang và điều chỉnh tay không bao giờ bị tính theo tỷ lệ hay cộng dần.</p>

<h2>Tab Hạn mức theo nhóm</h2>
<p>Tab thứ ba của trang một loại nghỉ (cạnh tab Bậc thâm niên). Mỗi dòng là <em>nhóm nào được bao nhiêu ngày mỗi năm</em>. Cách thêm:</p>
<ol>
<li>Ô <strong>Theo</strong>: chọn <strong>Hình thức nhân viên</strong> (toàn thời gian, bán thời gian, thời vụ…) hoặc <strong>Cấp bậc</strong> (nhân viên, trưởng phòng…).</li>
<li>Ô <strong>Nhóm</strong>: chọn đúng nhóm; ô <strong>Số ngày mỗi năm</strong>: gõ số ngày (bước nửa ngày).</li>
<li>Bấm <strong>Thêm dòng</strong>. Thêm trùng nhóm thì dòng cũ bị ghi đè. Bỏ một dòng bằng nút thùng rác ở cuối dòng.</li>
<li>Bấm <strong>Lưu hạn mức</strong> — chưa bấm thì chưa có gì được lưu.</li>
</ol>
<p>Khi cấp quỹ, hệ thống tìm dòng khớp <strong>hình thức nhân viên</strong> trước, không có thì tìm theo <strong>cấp bậc</strong>, không có nữa thì dùng <strong>Hạn mức mỗi năm</strong> của loại nghỉ. Quỹ đã cấp cho người nào thì giữ nguyên, chỉ áp cho lần cấp sau. Mỗi loại nghỉ khai tối đa 50 dòng. Xóa loại nghỉ thì các dòng này mất theo.</p>

<h2>Tab Bậc thâm niên</h2>
<p>Tab thứ hai của trang một loại nghỉ. Mỗi dòng là <em>làm đủ N năm thì cộng thêm M ngày</em>. Bộ mặc định: <strong>5→+1 · 10→+2 · 15→+3 · 20→+4</strong>.</p>
<p>⚠️ Hệ lấy <strong>bậc cao nhất khớp được, KHÔNG cộng dồn</strong>. Khai bậc theo lối cộng dồn (5→+1, 10→+1, 15→+1) thì người 15 năm chỉ được +1, không phải +3.</p>
<p>Công ty đổi sang bậc không đều thì <strong>sửa bảng này</strong> — luật nằm ở dữ liệu chứ không nằm trong mã.</p>

<h2>Thiết lập ▸ Lịch ngày lễ</h2>
<p>Quyết định ngày nào <strong>không</strong> bị trừ vào phép của toàn công ty. Sai ở đây thì cả công ty bị trừ oan, mà không ai phát hiện ngay.</p>
<ul>
<li><strong>Không khai pháp nhân</strong> = áp cho <strong>mọi pháp nhân</strong>. Pháp nhân có lịch riêng thì thêm dòng của nó — hai nguồn được <strong>gộp</strong>, không loại trừ nhau.</li>
<li>Cờ <strong>lặp hằng năm</strong> chỉ dùng cho ngày <strong>cố định theo dương lịch</strong>: 01/01 · 30/4 · 01/5 · 02/9.</li>
</ul>
<p>⚠️ <strong>Cái bẫy lớn nhất của cả phân hệ:</strong> <strong>Tết Âm lịch và Giỗ Tổ trôi theo lịch âm</strong>, dương lịch mỗi năm một khác — <strong>không</strong> đánh dấu lặp hằng năm được, <strong>mỗi năm phải nhập lại bằng tay</strong>. Quên là cả công ty bị trừ phép vào những ngày nghỉ Tết. Đặt việc này vào lịch tháng 12 hằng năm.</p>
<p>Sửa lịch lễ <strong>không</strong> tính lại các đơn đã nộp — số ngày đã chốt trên tờ đơn. Sửa lễ sau khi người ta đã nộp thì phải rà lại đơn trong khoảng đó bằng tay.</p>

<h2>Thiết lập ▸ Ngày cấm nghỉ</h2>
<p>Nơi khai những khoảng ngày công ty <strong>không muốn ai nghỉ</strong> — chốt sổ cuối năm, kiểm kê kho, mùa cao điểm. Vào <strong>Nghỉ phép ▸ Thiết lập</strong>, bấm thẻ <strong>Ngày cấm nghỉ</strong> (cần quyền sửa danh mục Loại nghỉ), rồi bấm <strong>Thêm khoảng cấm nghỉ</strong>. Cũng vào được từ lối tắt <strong>Ngày cấm nghỉ</strong> ở cuối tab Nghỉ phép của Cài đặt nhân sự.</p>
<table>
<thead><tr><th>Ô</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Từ ngày · Đến ngày</strong></td><td>Hai đầu của khoảng cấm. Một khoảng dài tối đa 366 ngày; cấm đúng một ngày thì chọn hai ô cùng ngày.</td></tr>
<tr><td><strong>Lý do</strong></td><td>Tối đa 255 ký tự. Lý do hiện lại trong khung cảnh báo trên đơn nghỉ và trong câu báo chặn duyệt, nên viết ngắn gọn dễ hiểu.</td></tr>
<tr><td><strong>Pháp nhân · Phòng ban</strong></td><td>Để trống là áp cho <strong>mọi</strong> pháp nhân hoặc <strong>mọi</strong> phòng ban. Hệ so với pháp nhân và phòng ban của <strong>người nghỉ</strong>, không phải của người lập hộ.</td></tr>
<tr><td><strong>Đang áp dụng</strong></td><td>Tắt thì khoảng cấm hết hiệu lực ngay (không cảnh báo, không chặn) mà vẫn giữ lại để bật lại năm sau.</td></tr>
</tbody>
</table>
<p><strong>Hệ xử lý thế nào khi đơn đụng ngày cấm:</strong></p>
<ul>
<li><strong>Lập, sửa, gửi duyệt: không chặn.</strong> Ngay khi người nghỉ chọn ngày, form hiện <strong>khung vàng</strong> <em>Đơn nghỉ này rơi vào ngày cấm nghỉ</em> kèm ngày và lý do. Trang chi tiết đơn cũng hiện khung này để người duyệt biết.</li>
<li><strong>Duyệt ở chặng cuối (hoặc duyệt thẳng khi chưa khai luồng): bị chặn.</strong> Người duyệt cuối bấm duyệt sẽ nhận câu <em>Đơn nghỉ này rơi vào ngày cấm nghỉ: … Chưa duyệt được</em>; đơn vẫn ở trạng thái Chờ duyệt, quỹ phép vẫn đang giữ chỗ, không có gì bị trừ. Người duyệt có thể <strong>Trả về</strong> để người nghỉ đổi ngày.</li>
<li><strong>Ngoại lệ:</strong> quản trị hệ thống và các vai trò khai ở ô <strong>Vai trò được duyệt đơn nghỉ rơi vào ngày cấm nghỉ</strong> (<strong>Nhân sự ▸ Master ▸ Cài đặt nhân sự</strong>, tab Nghỉ phép) duyệt qua được. Để trống ô đó thì chỉ quản trị duyệt qua được.</li>
<li><strong>Đơn nhiều khoảng ngày:</strong> chỉ khoảng nào thật sự giao với ngày cấm mới tính. Ngày nằm ở <em>khe</em> giữa hai khoảng thì không bị coi là nghỉ.</li>
</ul>
<p>Thêm hay tắt một khoảng cấm <strong>không</strong> làm đổi đơn đã duyệt. Đơn đang chờ duyệt thì được kiểm lại ở lượt duyệt cuối theo đúng danh sách tại thời điểm bấm.</p>""",
        },
        {
            "title": NS_QUYEN,
            "icon": "key-round",
            "summary": "Năm khóa quyền (kể cả Phiếu nghỉ bù), phạm vi dữ liệu, và cách khai luồng duyệt cho khỏi kẹt",
            "content": f"""<h2>Nhân sự — Phân quyền và luồng duyệt</h2>

<h2>Năm khóa quyền — đừng gộp</h2>
<table>
<thead><tr><th>Khóa</th><th>Mở màn nào</th></tr></thead>
<tbody>
<tr><td><code>leave_request</code></td><td>Đơn nghỉ phép · Lịch nghỉ</td></tr>
<tr><td><code>leave_balance</code></td><td>Quỹ phép năm (cấp phát, <strong>điều chỉnh tay</strong>)</td></tr>
<tr><td><code>leave_comp_request</code> — nhãn <em>Nghỉ phép › Phiếu nghỉ bù</em></td><td>Nghỉ bù (lập, duyệt, hủy phiếu nghỉ bù)</td></tr>
<tr><td><code>leave_type</code></td><td>Thiết lập ▸ Loại nghỉ (kèm bậc thâm niên, hạn mức theo nhóm) và Thiết lập ▸ Ngày cấm nghỉ</td></tr>
<tr><td><code>holiday</code></td><td>Thiết lập ▸ Lịch ngày lễ</td></tr>
</tbody>
</table>
<p>Tách riêng vì <strong><code>leave_balance</code> ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai</strong>. Gộp nó với <code>leave_request</code> thì cho ai xem đơn của mình là cho họ tự cộng phép.</p>
<p><strong>Phiếu nghỉ bù có khóa riêng</strong> vì duyệt một phiếu là <em>tạo thêm ngày phép</em>. Vì cùng lý do đó, phiếu nghỉ bù <strong>luôn chặn tự duyệt</strong>, không phụ thuộc công tắc ở Cài đặt nhân sự.</p>
<p>Có quyền sửa <strong>một trong hai</strong> danh mục (<code>leave_type</code> hoặc <code>holiday</code>) thì vẫn vào được mục <em>Thiết lập</em>; chỉ sửa được một thẻ thì hệ không dựng hàng thẻ con.</p>

<h2><em>Không thấy menu Nghỉ phép</em></h2>
<p>⚠️ Gần như <strong>luôn</strong> là phân quyền. Năm khóa trên là khóa <strong>mới</strong> (khóa <code>leave_comp_request</code> có từ 02/11/2026), mà seed cố ý <strong>không ghi đè</strong> phân quyền đã chỉnh tay trên hệ đang chạy — nên vai trò cũ <strong>không tự có</strong> chúng.</p>
<p>Cách xử lý: vào <strong>Quản trị ▸ Phân quyền tài khoản</strong>, tick các khóa cho đúng vai trò, rồi nhờ người đó đăng xuất và đăng nhập lại. (Quản trị hệ thống có thể chạy một lần với cờ đồng bộ cưỡng bức, nhưng cách đó ghi đè cả những chỉnh tay khác — cân nhắc.)</p>

<h2>Ai nên có gì</h2>
<table>
<thead><tr><th>Vai</th><th>Khóa</th><th>Hành động</th></tr></thead>
<tbody>
<tr><td>Nhân viên</td><td><code>leave_request</code>, <code>leave_comp_request</code></td><td>đọc · tạo · sửa · hủy</td></tr>
<tr><td>Trưởng bộ phận</td><td><code>leave_request</code>, <code>leave_comp_request</code></td><td>thêm <strong>duyệt</strong>, phạm vi tới bộ phận mình</td></tr>
<tr><td>Nhân sự phụ trách phép</td><td>đủ năm khóa</td><td>vai trò mẫu <code>hr_leave</code>, không gán tự động cho ai</td></tr>
</tbody>
</table>

<h2>Phạm vi dữ liệu</h2>
<p>Quyền mở màn, <strong>phạm vi</strong> quyết định thấy được dòng nào.</p>
<ul>
<li><code>leave_request</code> và <code>leave_comp_request</code> khai cả <em>người lập</em> lẫn <em>người nghỉ</em> vào phạm vi <strong>của mình</strong> — vì hành chính lập hộ là việc có thật, và cả hai người đều phải thấy tờ đơn, tờ phiếu.</li>
<li><code>leave_balance</code> chỉ khai theo <em>người sở hữu dòng quỹ</em>. Nhân viên thường <strong>không</strong> vào mục Quỹ phép năm; họ xem số của mình ngay trên form nộp đơn.</li>
<li>Các danh mục (<em>Loại nghỉ</em>, <em>Lịch ngày lễ</em>, <em>Ngày cấm nghỉ</em>) là dữ liệu chung, không lọc theo phạm vi.</li>
</ul>
<p>Người duyệt <strong>không cần</strong> phạm vi rộng: đang có việc trên tờ đơn thì đọc được nó, ký xong quyền đó đóng lại. Nhờ vậy trưởng phòng Nhân sự ký chặng 2 cho nhân viên phòng khác mà không phải mở phạm vi toàn công ty.</p>

<h2>Luồng duyệt</h2>
<p>Khai ở phân hệ <strong>Phê duyệt</strong> cho loại chứng từ <em>Đơn nghỉ phép</em> (và riêng cho <em>Phiếu nghỉ bù</em> nếu muốn phiếu đi luồng). Luồng mẫu: <strong>trưởng bộ phận của người xin nghỉ → trưởng phòng Nhân sự</strong>.</p>
<ul>
<li>⚠️ <strong>Mỗi chặng PHẢI khai người dự phòng.</strong> Hệ loại người nộp khỏi danh sách người ký, nên trưởng phòng tự xin nghỉ thì chặng đó rỗng và <strong>đơn kẹt vĩnh viễn</strong> — mà quản lý thì cũng phải nghỉ phép. Bật <strong>Chặn tự duyệt đơn nghỉ</strong> ở Cài đặt nhân sự thì cả bước khai đích danh cũng né người nghỉ, nên người dự phòng càng cần.</li>
<li><strong>Chưa khai luồng nào thì vẫn nộp được</strong>: lúc đó người có quyền duyệt bấm <strong>Duyệt đơn</strong> thẳng ở màn chi tiết. Không có đường lùi này thì cài mới xong là không ai nghỉ nổi.</li>
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
<li>Tick <strong>năm khóa quyền</strong> cho các vai trò, và bật <strong>Loại nhận ngày nghỉ bù</strong> cho một loại nghỉ nếu dùng phiếu nghỉ bù.</li>
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
