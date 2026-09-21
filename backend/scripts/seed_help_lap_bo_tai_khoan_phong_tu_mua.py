# -*- coding: utf-8 -*-
"""Seed bài Trung tâm trợ giúp: LẬP BỘ TÀI KHOẢN PHÒNG TỰ MUA HÀNG (bao-CR-444).

Bài này là BÀI CON của bài «Trợ lý AI» (nằm trong nhóm «Các chức năng khác»), đứng cạnh bài
«Lập bộ tài khoản thu mua bằng Trợ lý AI» (bao-CR-441). Bài kia nói cách nhờ trợ lý làm hai
bước cuối; bài này nói đủ BỐN BƯỚC LÀM TAY cho hai bộ tài khoản (phòng tự mua + Thu mua chung
trừ phòng đó) và cách kiểm tra sau khi làm. Không dựng thẻ phân hệ mới ngoài trang chủ,
không đụng nội dung bài cha.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_lap_bo_tai_khoan_phong_tu_mua.py

Idempotent: đã có bài cùng tiêu đề dưới cùng bài cha thì xóa bài đó (kèm con, nếu có)
rồi chèn lại. Không thấy bài cha «Trợ lý AI» thì DỪNG, không tự tạo bài gốc.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md`
(mục 1 → 8) và với hành vi thật của màn Nhân sự / Phân quyền tài khoản / hộp Phạm vi.
Bài cố ý nói bằng TÊN VAI TRÒ, không nêu mã tài khoản mẫu của môi trường thử.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

PARENT_TITLE = "Trợ lý AI"
GRANDPARENT_TITLE = "Các chức năng khác"
ARTICLE_TITLE = "Lập bộ tài khoản phòng tự mua hàng"
AI_ARTICLE_TITLE = "Lập bộ tài khoản thu mua bằng Trợ lý AI"


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


SUMMARY = (
    "HD bốn bước lập tay bộ tài khoản cho phòng tự mua hàng và bộ Thu mua chung trừ phòng đó: "
    "hồ sơ nhân sự, tài khoản đăng nhập, vai trò, phạm vi, rồi kiểm tra"
)

CONTENT = f"""<h2>I. Giới thiệu</h2>
<p>Một phòng ban <strong>tự mua hàng</strong> (ví dụ nhà máy Dego Organic) nghĩa là phiếu của phòng đó do người thu mua <em>của chính phòng</em> xử lý, còn phòng Thu mua chung <strong>không thấy</strong> phiếu đó. Hệ thống <strong>không có ô cấu hình</strong> nào tên là "phòng tự mua hàng": công tắc nằm hoàn toàn ở <strong>vai trò + phạm vi của từng tài khoản</strong>. Bài này hướng dẫn lập tay đủ hai bộ tài khoản và kiểm tra lại. Cách làm dùng cho <strong>mọi phòng tự mua</strong>, không riêng nhà máy.</p>
<p>Đã tạo xong hồ sơ và tài khoản đăng nhập rồi thì hai bước gán vai trò + khai phạm vi có thể nhờ trợ lý làm thay: xem bài {ref(AI_ARTICLE_TITLE, "Lập bộ tài khoản thu mua bằng Trợ lý AI")}.</p>

<h2>II. Hiểu trước khi bấm</h2>
<table><thead><tr><th>Bộ</th><th>Ai giữ</th><th>Vai trò</th><th>Phạm vi</th><th>Thấy gì</th></tr></thead><tbody>
<tr><td><strong>A. Phòng tự mua</strong></td><td>người đang thuộc phòng đó</td><td><em>Quản lý thu mua phòng</em> + <em>Nhân viên thu mua</em></td><td>bậc <strong>Được giao + đã duyệt trong phòng</strong>, gắn sẵn trong vai trò</td><td>phiếu đã duyệt <strong>của phòng mình</strong> và phiếu phòng khác <strong>nhờ</strong> phòng mình xử lý</td></tr>
<tr><td><strong>B. Thu mua chung trừ phòng đó</strong></td><td>người phòng Thu mua chung</td><td><em>Quản lý thu mua</em>, <em>Admin thu mua</em>, <em>Nhân viên thu mua</em></td><td>như hiện tại + ô <strong>Loại trừ phòng ban</strong> = phòng tự mua</td><td>mọi phiếu <strong>trừ</strong> phiếu của phòng tự mua; phiếu phòng tự mua <strong>nhờ</strong> Thu mua chung thì vẫn thấy</td></tr>
</tbody></table>
<p>Bốn điều quyết định kết quả:</p>
<ul>
<li><strong>Phòng ban trong hồ sơ nhân sự</strong> là thứ máy dùng để tính "phòng mình". Người của bộ A phải có phòng ban chính (hoặc phòng kiêm nhiệm) đúng là phòng tự mua.</li>
<li><strong>Pháp nhân trong hồ sơ nhân sự không thu hẹp gì.</strong> Đó chỉ là công ty ký hợp đồng lao động. Người của nhà máy ký với công ty mẹ vẫn thấy và xử lý phiếu của phòng mình <strong>đứng tên bất kỳ pháp nhân nào</strong>, vì nhà máy mua cho nhiều công ty. Muốn nhốt một tài khoản vào đúng một pháp nhân thì mới khai ô <em>Chỉ trong công ty</em>; <strong>hai bộ trong bài này không khai ô đó</strong>.</li>
<li><strong>Loại trừ thắng mọi bậc.</strong> Ô <em>Loại trừ phòng ban</em> trừ ra khỏi cả bậc <em>Tất cả</em>, nên bộ B giữ nguyên bậc đang có, chỉ khai thêm ô loại trừ.</li>
<li><strong>Ô "Xem thêm phòng ban" là cộng thêm, không thu hẹp.</strong> Đừng dùng nó để giới hạn bộ A; giới hạn đã nằm sẵn trong vai trò <em>Quản lý thu mua phòng</em>.</li>
</ul>
<p>💡 Với người thật đang làm việc, <strong>không tạo hồ sơ mới</strong>: bỏ qua Bước 1 và 2, đi thẳng từ Bước 3 trên hồ sơ có sẵn của họ.</p>

<h2>III. Chuẩn bị</h2>
<table><thead><tr><th>Cần</th><th>Kiểm ở đâu</th></tr></thead><tbody>
<tr><td>Tài khoản quản trị (vai trò <em>Quản trị hệ thống</em>, hoặc vai trò có quyền quản lý Vai trò, sửa Người dùng và tạo Nhân sự)</td><td>Menu <strong>Quản trị › Phân quyền tài khoản</strong> mở được là đủ</td></tr>
<tr><td>Phòng tự mua và phòng Thu mua chung đã có trong danh mục</td><td><strong>Nhân sự › Phòng ban</strong> — xem bài {ref("Phòng ban", "Phòng ban")}</td></tr>
<tr><td>Vai trò <em>Quản lý thu mua phòng</em> có trong danh sách vai trò</td><td><strong>Quản trị › Phân quyền tài khoản › Vai trò &amp; quyền</strong> — xem bài {ref("Vai trò", "Vai trò")}. Thiếu thì báo kỹ thuật</td></tr>
<tr><td>Không tự sửa quyền của chính mình</td><td>Màn hồ sơ và màn phân quyền <strong>khóa</strong> khi mở đúng tài khoản đang đăng nhập; nhờ một quản trị khác</td></tr>
</tbody></table>

<h2>IV. Bốn bước chung cho MỖI tài khoản</h2>
<p>Mọi tài khoản của cả hai bộ đều đi qua đúng bốn bước này; mục V và VI chỉ nói phần khác nhau.</p>

<h3>Bước 1 — Tạo hồ sơ nhân sự</h3>
<ul>
<li>Menu trái <strong>Nhân sự › Nhân sự</strong>, bấm <strong>Thêm mới</strong> (chi tiết từng ô xem bài {ref("Nhân sự", "Nhân sự")}).</li>
<li><strong>Mã NV</strong>: gõ mã theo quy ước công ty (để trống thì hệ tự sinh).</li>
<li><strong>Email</strong>: bắt buộc điền ngay. Email này là <strong>tên đăng nhập</strong> của tài khoản sẽ tạo ở Bước 2.</li>
<li><strong>Pháp nhân</strong>: chọn công ty ký hợp đồng lao động. Ô này <strong>không</strong> giới hạn phiếu người đó thấy (mục II).</li>
<li><strong>Phòng ban</strong>: chọn đúng phòng của bộ (phòng tự mua cho bộ A, phòng Thu mua chung cho bộ B). Ô này chỉ hiện phòng của pháp nhân vừa chọn.</li>
<li><strong>Vị trí / Chức vụ</strong>: chọn chức danh in trên phiếu. Chức vụ <strong>chỉ là nhãn</strong>, không cấp quyền gì.</li>
<li><strong>Tình trạng làm việc</strong>: Chính thức. <strong>Trạng thái hồ sơ</strong>: Đang hoạt động. Bấm <strong>Lưu</strong>.</li>
</ul>
<p>Người phụ trách thu mua cho <strong>nhiều phòng tự mua</strong> thì mở hồ sơ vừa tạo, tab <strong>Chung</strong>, kéo xuống thẻ <strong>Kiêm nhiệm</strong>, chọn thêm phòng rồi bấm <strong>Lưu kiêm nhiệm</strong> (nút riêng, không phải nút Lưu ở đầu trang). Bậc trong phòng tính cả phòng kiêm nhiệm.</p>

<h3>Bước 2 — Tạo tài khoản đăng nhập</h3>
<ul>
<li>Mở hồ sơ vừa tạo (<strong>Nhân sự › Nhân sự</strong>, bấm vào dòng), sang tab <strong>Tài khoản</strong>.</li>
<li>Thẻ <em>Tài khoản đăng nhập</em> báo "Nhân sự này chưa có tài khoản đăng nhập". Bấm <strong>Tạo tài khoản đăng nhập</strong>.</li>
<li>Hộp <em>Tạo tài khoản &amp; đặt mật khẩu</em>: nhập <strong>Mật khẩu mới</strong> và <strong>Nhập lại mật khẩu</strong>, bấm <strong>Xác nhận</strong>. Luật mật khẩu: tối thiểu 8 ký tự, có cả chữ và số, không trùng mã nhân viên hay email.</li>
<li>Tài khoản mới <strong>tự nhận vai trò Nhân sự</strong>. Người chỉ lập phiếu thế là xong; các tài khoản khác đi tiếp Bước 3.</li>
</ul>
<p>⚠️ Nút không hiện mà thẻ báo "Hãy nhập Email ở hồ sơ và lưu trước" thì quay lại Bước 1 điền email.</p>

<h3>Bước 3 — Gán vai trò</h3>
<ul>
<li>Trên cùng thẻ <em>Tài khoản đăng nhập</em>, bấm nút <strong>Phân quyền tài khoản</strong> (hoặc menu <strong>Quản trị › Phân quyền tài khoản › tab Người dùng</strong>, tìm theo mã NV, bấm vào dòng).</li>
<li>Thẻ <em>Vai trò &amp; phạm vi</em>: <strong>tick</strong> vai trò theo bảng ở mục V hoặc VI, <strong>bỏ tick</strong> <em>Nhân sự</em> nếu người đó không lập phiếu. Người thu mua giữ đúng <strong>một</strong> vai trò thu mua là đủ; trưởng phòng giữ <em>Trưởng phòng (duyệt PYC)</em>.</li>
<li>Bấm <strong>Lưu vai trò</strong> ở góc trên phải. Chưa lưu thì cạnh vai trò chỉ có chữ "Lưu vai trò trước để đặt phạm vi".</li>
</ul>

<h3>Bước 4 — Phạm vi (chỉ khi bảng ghi "loại trừ")</h3>
<ul>
<li>Sau khi lưu, cạnh vai trò đã lưu hiện nút <strong>Phạm vi</strong>. Bấm vào.</li>
<li>Hộp <em>Phạm vi — {{tên vai trò}}</em>. Phần trên tóm tắt tài khoản này đang thấy gì với vai trò đó; <strong>bộ A không cần khai gì thêm</strong>.</li>
<li>Bộ B: mở mục gập <strong>Ngoại lệ</strong>, xuống ô <strong>Loại trừ phòng ban</strong> (khung đỏ), chọn phòng tự mua. Các ô còn lại <strong>để trống</strong>, nhất là <em>Chỉ trong công ty</em>: khai vào là bộ B mất phiếu đứng tên các pháp nhân khác.</li>
<li>Bấm <strong>Lưu phạm vi</strong>.</li>
</ul>
<p>💡 Bước 3 và 4 làm cho nhiều người thì nhờ trợ lý cho nhanh: gõ một câu như <em>"lập bộ tài khoản nhân viên thu mua cho Nguyễn Văn A, loại trừ phòng Dego Organic"</em>, đọc thẻ đề xuất rồi bấm Xác nhận. Cách hỏi và các giới hạn ở bài {ref(AI_ARTICLE_TITLE, "Lập bộ tài khoản thu mua bằng Trợ lý AI")}.</p>

<h2>V. Bộ A — Phòng tự mua hàng</h2>
<table><thead><tr><th>Tài khoản</th><th>Bước 1 — Phòng ban</th><th>Bước 3 — Vai trò</th><th>Bước 4 — Phạm vi</th></tr></thead><tbody>
<tr><td>Người lập phiếu của phòng</td><td>phòng tự mua</td><td>giữ <em>Nhân sự</em> (mặc định)</td><td>không</td></tr>
<tr><td>Trưởng phòng</td><td>phòng tự mua, chức vụ Trưởng phòng</td><td><em>Trưởng phòng (duyệt PYC)</em></td><td>không</td></tr>
<tr><td>Quản lý thu mua của phòng</td><td>phòng tự mua, chức vụ Quản lý thu mua phòng</td><td><em>Quản lý thu mua phòng</em></td><td>không</td></tr>
<tr><td>Nhân viên thu mua của phòng</td><td>phòng tự mua, chức vụ Nhân viên thu mua</td><td><em>Nhân viên thu mua</em></td><td>không</td></tr>
</tbody></table>
<p>Quản lý thu mua của phòng <strong>không cần Ngoại lệ nào</strong>: bậc gắn sẵn trong vai trò đã giới hạn đúng phòng trong hồ sơ. Mở hộp <em>Phạm vi</em> chỉ để đọc phần tóm tắt cho chắc: câu tóm tắt phải nêu tên phòng tự mua.</p>

<h3>Phân công phụ trách riêng cho phòng</h3>
<p>Khi quản lý thu mua của phòng bấm <strong>Điều phối</strong> một phiếu, máy tra bảng phân công <strong>theo phòng đang xử lý phiếu</strong>. Người của phòng tự mua <strong>không được rơi về bộ "Thu mua chung"</strong> (nếu không là tự gán người ngoài vào phiếu của phòng), nên phải khai bộ riêng:</p>
<ul>
<li>Menu <strong>Thu mua › Cấu hình › Phân công phụ trách</strong>, bấm <strong>Gán phân công mới</strong>.</li>
<li><strong>Phòng áp dụng</strong>: chọn phòng tự mua (không để <em>Thu mua chung</em>).</li>
<li><strong>Phân loại VTBB</strong>: tick các phân loại phòng hay mua.</li>
<li><strong>NSTM chính</strong>: chọn nhân viên thu mua của phòng. <strong>NSTM dự phòng</strong>: tùy chọn.</li>
<li><strong>Lưu phân công</strong>. Lặp lại cho từng nhóm phân loại.</li>
</ul>
<p>⚠️ Không khai bảng này thì điều phối vẫn chạy nhưng <strong>mọi dòng đều trống người</strong>, quản lý phòng phải gán tay từng dòng bằng nút <em>Phân bổ</em>.</p>

<h2>VI. Bộ B — Thu mua chung trừ phòng tự mua</h2>
<table><thead><tr><th>Tài khoản</th><th>Bước 1 — Phòng ban</th><th>Bước 3 — Vai trò</th><th>Bước 4 — Phạm vi</th></tr></thead><tbody>
<tr><td>Quản lý thu mua</td><td>phòng Thu mua chung</td><td><em>Quản lý thu mua</em></td><td><strong>Loại trừ phòng ban = phòng tự mua</strong></td></tr>
<tr><td>Admin thu mua</td><td>phòng Thu mua chung</td><td><em>Admin thu mua</em></td><td><strong>Loại trừ phòng ban = phòng tự mua</strong></td></tr>
<tr><td>Nhân viên thu mua chung</td><td>phòng Thu mua chung</td><td><em>Nhân viên thu mua</em></td><td>không (bậc <em>Được giao</em> chỉ thấy dòng được gán, không rò gì thêm)</td></tr>
</tbody></table>
<p>Ghi chú khi khai ô loại trừ:</p>
<ul>
<li>Hộp thoại <strong>không hiện cảnh báo vàng</strong> ở ca này: cảnh báo "phòng của chính người này" chỉ bật khi phòng bị trừ trùng phòng trong hồ sơ. Nếu thấy vàng, nghĩa là đang mở nhầm hồ sơ của một người thuộc phòng tự mua.</li>
<li>Hộp thoại <strong>báo mâu thuẫn</strong> nếu cùng một phòng nằm ở cả ô <em>Xem thêm</em> lẫn ô <em>Loại trừ</em>. Bỏ bên <em>Xem thêm</em>.</li>
<li>Với người Thu mua chung <strong>đã có tài khoản thật</strong>, chỉ làm Bước 4 cho <strong>từng vai trò thu mua</strong> họ đang giữ (mỗi vai trò một hộp Phạm vi riêng). Bỏ sót một vai trò là vai trò đó vẫn thấy phiếu của phòng tự mua.</li>
</ul>

<h2>VII. Kiểm tra sau khi làm</h2>
<p>Đăng xuất tài khoản quản trị. Người đang đăng nhập <strong>giữ bản quyền cũ</strong> tới khi đăng nhập lại, và máy chủ còn nhớ bản cũ tối đa một phút, nên kiểm bằng cửa sổ ẩn danh, đăng nhập bằng email (hoặc mã NV) của từng tài khoản.</p>
<table><thead><tr><th>Tài khoản</th><th>Phải thấy</th><th>Không được thấy</th></tr></thead><tbody>
<tr><td>Người lập phiếu của phòng</td><td>lập được Yêu cầu mua hàng; danh sách chỉ có phiếu mình lập</td><td>nhà cung cấp, đơn mua hàng</td></tr>
<tr><td>Trưởng phòng</td><td>phiếu <strong>Đã gửi duyệt</strong> của phòng mình, nút <em>Duyệt</em></td><td>phiếu phòng khác</td></tr>
<tr><td>Quản lý thu mua của phòng</td><td>phiếu <strong>Đã duyệt</strong> trở đi của phòng mình <strong>đứng tên bất kỳ pháp nhân nào</strong>; nút <em>Điều phối</em>; phiếu phòng khác có ô <em>Nhờ phòng xử lý</em> = phòng mình</td><td>phiếu đã duyệt của phòng khác; danh sách trống khi chưa có phiếu nào của phòng được duyệt</td></tr>
<tr><td>Nhân viên thu mua của phòng</td><td>dòng đã được gán cho mình</td><td>dòng gán người khác</td></tr>
<tr><td>Quản lý thu mua (chung)</td><td>mọi phiếu đã duyệt của mọi phòng, <strong>mọi pháp nhân</strong>, <strong>trừ</strong> phòng tự mua; phiếu phòng tự mua <strong>nhờ</strong> Thu mua chung</td><td>phiếu thường của phòng tự mua (kể cả gõ thẳng id lên đường dẫn: phải ra <em>Không tìm thấy</em>)</td></tr>
<tr><td>Admin thu mua</td><td>như Quản lý thu mua, không có nút duyệt</td><td>như Quản lý thu mua</td></tr>
<tr><td>Nhân viên thu mua chung</td><td>dòng được gán</td><td>phiếu chưa gán</td></tr>
</tbody></table>
<p>💡 <strong>Đường chạy thử ngắn nhất:</strong> người lập phiếu của phòng lập một phiếu, trưởng phòng duyệt, quản lý thu mua của phòng thấy và điều phối, quản lý thu mua chung <strong>không</strong> thấy phiếu đó. Rồi lập phiếu thứ hai chọn <em>Nhờ phòng xử lý</em> = phòng Thu mua chung, trưởng phòng duyệt: lúc này quản lý thu mua chung thấy, quản lý thu mua của phòng vẫn thấy.</p>

<h2>VIII. Bẫy hay gặp</h2>
<ul>
<li><strong>Đổi email trên hồ sơ không đổi tên đăng nhập</strong> của tài khoản đã cấp. Điền đúng email trước khi bấm <em>Tạo tài khoản đăng nhập</em>.</li>
<li><strong>Không thấy nút Phạm vi</strong>: chưa bấm <em>Lưu vai trò</em>.</li>
<li><strong>Đổi quyền xong vẫn thấy như cũ</strong>: người đó chưa đăng xuất, hoặc chưa qua một phút.</li>
<li><strong>Sửa hồ sơ hoặc quyền của chính mình bị khóa</strong>: cố ý, nhờ quản trị khác.</li>
<li><strong>Hai phòng trùng tên ở hai công ty</strong>: ô loại trừ khớp theo <strong>tên</strong>, sẽ trừ cả hai. Đặt tên phòng khác nhau trước.</li>
<li><strong>Không thấy phiếu đứng tên pháp nhân khác</strong>: có người đã khai <em>Chỉ trong công ty</em> trong hộp Phạm vi của vai trò đó. Xóa ô đó. Pháp nhân trong hồ sơ nhân sự <strong>không</strong> phải nguyên nhân.</li>
<li><strong>Nhờ nhầm sang phòng không có ai giữ vai trò thu mua</strong>: phiếu chỉ còn phòng lập thấy. Sửa lại ô <em>Nhờ phòng xử lý</em> khi phiếu còn Nháp / Bị trả lại, hoặc dùng nút <em>Trả về phòng lập</em> trên phiếu đã duyệt.</li>
<li><strong>Chuyển đi giữa chừng</strong>: nút <em>Chuyển phòng xử lý</em> / <em>Trả về phòng lập</em> trên chi tiết Yêu cầu mua hàng và Yêu cầu báo giá chỉ hiện cho quản lý thu mua của phòng đang giữ phiếu (hoặc quản lý thu mua toàn hệ), và chỉ khi <strong>chưa dòng nào lên đơn mua hàng</strong>. Chuyển là chuyển <strong>cả phiếu</strong>, người phụ trách ở mọi dòng bị gỡ để phòng nhận phân công lại; <strong>không chuyển một phần dòng</strong>. Mua được nửa phiếu rồi mới muốn nhờ thì tách các dòng chưa mua sang một phiếu mới.</li>
</ul>

<h2>IX. Mở thêm một phòng tự mua khác</h2>
<p>Không sửa mã, không sửa cấu hình. Lặp lại:</p>
<ul>
<li>Mục V cho phòng mới: hồ sơ ở phòng đó, cấp <em>Quản lý thu mua phòng</em> + <em>Nhân viên thu mua</em>, khai <em>Phân công phụ trách</em> với <em>Phòng áp dụng</em> = phòng đó.</li>
<li>Mục VI Bước 4: mở <strong>từng</strong> tài khoản Thu mua chung, thêm phòng mới vào ô <em>Loại trừ phòng ban</em> của <strong>từng</strong> vai trò thu mua họ giữ.</li>
</ul>
<p>⚠️ Việc thứ hai là chỗ dễ quên nhất và quên thì <strong>lủng im lặng</strong>: Thu mua chung vẫn thấy phiếu phòng mới mà không ai báo lỗi. Ghi phòng mới vào danh sách kiểm định kỳ của quản trị.</p>

<h2>X. Điều hướng</h2>
<ul>
<li><strong>Thuộc thư mục:</strong> Các chức năng khác › {ref(PARENT_TITLE, "Trợ lý AI")}</li>
<li><strong>Bài liên quan:</strong> {ref(AI_ARTICLE_TITLE, "Lập bộ tài khoản thu mua bằng Trợ lý AI")} · {ref("Vai trò", "Vai trò")} · {ref("Nhân sự", "Nhân sự")} · {ref("Phòng ban", "Phòng ban")}</li>
</ul>
"""


def find_parent(db):
    """Bài «Trợ lý AI»; nếu trùng tiêu đề thì ưu tiên bài nằm dưới «Các chức năng khác»."""
    candidates = db.query(HelpArticle).filter(HelpArticle.title == PARENT_TITLE).all()
    if not candidates:
        return None
    for art in candidates:
        if art.parent_id:
            parent = db.get(HelpArticle, art.parent_id)
            if parent is not None and parent.title == GRANDPARENT_TITLE:
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


def main():
    db = SessionLocal()
    try:
        parent = find_parent(db)
        if parent is None:
            print(f"Không thấy bài cha «{PARENT_TITLE}» — dừng, không tạo bài gốc mới.")
            sys.exit(1)

        old = (
            db.query(HelpArticle)
            .filter(HelpArticle.title == ARTICLE_TITLE, HelpArticle.parent_id == parent.id)
            .first()
        )
        order = None
        if old is not None:
            order = old.sort_order
            removed = delete_subtree(db, old.id)
            print(f"Đã xóa bài cũ: {removed} bài (id={old.id}).")
        if order is None:
            max_order = (
                db.query(HelpArticle.sort_order)
                .filter(HelpArticle.parent_id == parent.id)
                .order_by(HelpArticle.sort_order.desc())
                .first()
            )
            order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

        art = HelpArticle(
            parent_id=parent.id,
            title=ARTICLE_TITLE,
            summary=SUMMARY,
            content=CONTENT,
            sort_order=order,
        )
        db.add(art)
        db.commit()
        print(f"Đã dựng bài «{ARTICLE_TITLE}» (id={art.id}) dưới «{parent.title}» "
              f"(id={parent.id}, sort_order={order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
