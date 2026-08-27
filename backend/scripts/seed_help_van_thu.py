# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ VĂN THƯ.

Dựng cây bài viết hướng dẫn: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ")
-> nhóm theo VAI TRÒ -> bài hướng dẫn theo từng TAB trong menu Văn bản, viết
riêng cho từng vai trò, kèm HAI VÍ DỤ chạy xuyên vai trò và LIÊN KẾT các bài
theo từng bước.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_van_thu.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

ROOT_TITLE = "Hướng dẫn sử dụng công cụ văn thư"


# --------------------------------------------------------------------------- #
#  LIÊN KẾT NỘI BỘ
#  Slug sinh y hệt hàm slugify() của help-center (help-slug.tsx) — vì portal tra
#  ngược slug -> id ngay trên client. Tiêu đề các bài đều DUY NHẤT nên không dính
#  hậu tố "-{id}". Nút/link nhúng thẳng style để đi kèm nội dung (không phụ thuộc
#  CSS help-center khi port sang dev/prod).
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


def step_btn(target_title: str, label: str) -> str:
    return (
        f'<p><a href="/{slugify(target_title)}" '
        'style="display:inline-block;margin-top:.4rem;padding:.55rem 1rem;'
        "background:var(--primary,#2563eb);color:#fff;border-radius:.5rem;"
        'text-decoration:none;font-weight:600">'
        f"{label} →</a></p>"
    )


def ref(target_title: str, text: str) -> str:
    return (
        f'<a href="/{slugify(target_title)}" '
        'style="color:var(--primary,#2563eb);font-weight:600;text-decoration:underline">'
        f"{text}</a>"
    )


# --------------------------------------------------------------------------- #
#  TIÊU ĐỀ (hằng, để tham chiếu chéo khỏi gõ nhầm)
# --------------------------------------------------------------------------- #
# Nhân viên
NV = "Dành cho Nhân viên"
NV_TQ = "Tổng quan — dành cho nhân viên"
NV_VB = "Văn bản — dành cho nhân viên"
NV_SO = "Sổ văn bản — tra cứu (nhân viên)"
NV_VD = "Ví dụ: Nhân viên tạo giấy xin nghỉ phép"
# Trưởng bộ phận
TBP = "Dành cho Trưởng bộ phận"
TBP_TQ = "Tổng quan — dành cho trưởng bộ phận"
TBP_VB = "Văn bản — dành cho trưởng bộ phận"
TBP_CD = "Chờ tôi duyệt — dành cho trưởng bộ phận"
TBP_SO = "Sổ văn bản — dành cho trưởng bộ phận"
TBP_VD = "Ví dụ: Trưởng bộ phận duyệt giấy nghỉ phép"
# Nhân viên văn thư
VT = "Dành cho Nhân viên văn thư"
VT_TQ = "Tổng quan — dành cho văn thư"
VT_NV = "Nghiệp vụ — tổng quan nhóm (văn thư)"
VT_VB = "Văn bản — soạn và ban hành (văn thư)"
VT_CD = "Chờ tôi duyệt — dành cho văn thư"
VT_SO = "Sổ văn bản — khai và quản lý (văn thư)"
VT_DM = "Danh mục — tổng quan nhóm (văn thư)"
VT_TL = "Thiết lập văn bản (văn thư)"
VT_VD = "Ví dụ: Văn thư tạo thông báo nghỉ lễ"
# Trưởng bộ phận văn thư
TVT = "Dành cho Trưởng bộ phận văn thư"
TVT_TQ = "Tổng quan — dành cho trưởng bộ phận văn thư"
TVT_VB = "Văn bản — dành cho trưởng bộ phận văn thư"
TVT_CD = "Chờ tôi duyệt — dành cho trưởng bộ phận văn thư"
TVT_SO = "Sổ văn bản — dành cho trưởng bộ phận văn thư"
TVT_TL = "Thiết lập văn bản (trưởng bộ phận văn thư)"
TVT_DS = "Quy tắc đánh số"
TVT_QH = "Quy tắc quan hệ"
TVT_VD = "Ví dụ: Duyệt và ban hành thông báo nghỉ lễ"
# Giám đốc
GD = "Dành cho Giám đốc công ty"
GD_TQ = "Tổng quan — dành cho giám đốc"
GD_CD = "Chờ tôi duyệt — dành cho giám đốc"
GD_VB = "Văn bản — dành cho giám đốc"
GD_SO = "Sổ văn bản — dành cho giám đốc"


# --------------------------------------------------------------------------- #
#  CÂY NỘI DUNG
# --------------------------------------------------------------------------- #
TREE = {
    "title": ROOT_TITLE,
    "icon": "file-text",
    "summary": "Tổng quan quy trình văn thư, các vai trò và cách thao tác trên từng trang",
    "content": f"""<h2>Hướng dẫn sử dụng công cụ văn thư</h2>
<p>Công cụ Văn thư số hóa toàn bộ vòng đời văn bản của DEGO Holding: <strong>soạn thảo → gửi duyệt → ký/duyệt → ban hành → vào sổ và lưu trữ</strong>. Mỗi văn bản đi qua các trạng thái rõ ràng, số hiệu do hệ thống tự cấp theo quy tắc, và quyền xem được kiểm soát theo vai trò và theo từng quyển sổ.</p>
<h3>Hai ví dụ xuyên suốt</h3>
<p>Bộ tài liệu này bám theo hai tình huống thật, mỗi tình huống nối nhiều bài theo từng bước:</p>
<ul>
<li><strong>Xin nghỉ phép</strong> — nhân viên tạo đơn, trưởng bộ phận duyệt. Bắt đầu ở {ref(NV_VD, "Ví dụ: Nhân viên tạo giấy xin nghỉ phép")}.</li>
<li><strong>Thông báo nghỉ lễ</strong> — văn thư soạn, trưởng bộ phận văn thư duyệt và ban hành tới từng công ty. Bắt đầu ở {ref(VT_VD, "Ví dụ: Văn thư tạo thông báo nghỉ lễ")}.</li>
</ul>
<h3>Các vai trò</h3>
<ul>
<li><strong>Nhân viên</strong> — đọc văn bản áp dụng cho mình, tạo đơn cá nhân (vd nghỉ phép), tra cứu, theo dõi.</li>
<li><strong>Trưởng bộ phận</strong> — duyệt/trả lại văn bản trong phạm vi bộ phận.</li>
<li><strong>Nhân viên văn thư</strong> — soạn, gửi duyệt, ban hành, cấp số, quản lý sổ và danh mục nền.</li>
<li><strong>Trưởng bộ phận văn thư</strong> — như nhân viên văn thư, thêm cấu hình quy tắc đánh số/quan hệ và duyệt/ký.</li>
<li><strong>Giám đốc công ty</strong> — ký/ban hành cuối, theo dõi toàn công ty.</li>
</ul>
<h3>Các trang trong menu Văn bản</h3>
<p>Tổng quan · Văn bản · Chờ tôi duyệt · Sổ văn bản · Thiết lập văn bản · Quy tắc đánh số · Quy tắc quan hệ. Bạn <strong>chỉ thấy trang mà quản trị đã cấp quyền</strong>; ngoài ra "Sổ văn bản", "Chờ tôi duyệt" và "Văn bản đến" còn mở theo việc bạn được thêm vào <strong>người xem sổ</strong> hoặc được phân vào <strong>luồng duyệt</strong>, không chỉ theo vai trò.</p>
<h3>Đọc hướng dẫn theo vai trò</h3>
<p>Chọn nhóm ứng với vai trò của bạn ở bên dưới để xem hướng dẫn thao tác trên từng trang.</p>""",
    "children": [
        # ============================ NHÂN VIÊN ============================ #
        {
            "title": NV,
            "icon": "users",
            "summary": "Đọc văn bản áp dụng cho mình, tạo đơn cá nhân, tra cứu",
            "content": f"""<h2>Dành cho Nhân viên</h2>
<p>Là nhân viên, bạn <strong>đọc và làm theo</strong> các văn bản đã ban hành áp dụng cho mình, <strong>tự tạo đơn cá nhân</strong> (ví dụ Giấy xin nghỉ phép) khi được cấp quyền, tra cứu văn bản trong các sổ được chia và theo dõi nhanh trên Tổng quan.</p>
<p>Các trang liên quan: <strong>Tổng quan</strong>, <strong>Văn bản</strong> (thẻ Văn bản đến), <strong>Sổ văn bản</strong>.</p>
<h3>Bắt đầu bằng ví dụ</h3>
<p>Xem trọn một lượt từ tạo đơn tới khi được duyệt: {ref(NV_VD, "Ví dụ: Nhân viên tạo giấy xin nghỉ phép")}.</p>""",
            "children": [
                {
                    "title": NV_TQ,
                    "icon": "bar-chart",
                    "content": """<h2>Tổng quan — dành cho nhân viên</h2>
<p>Trang Tổng quan cho bạn thấy nhanh tình hình văn bản trong phạm vi bạn được xem, không phải mở từng phiếu.</p>
<h3>Các bước</h3>
<ol>
<li>Vào <strong>Văn bản → Tổng quan</strong>.</li>
<li>Lọc theo <strong>pháp nhân</strong>, <strong>phòng ban</strong> hoặc <strong>khoảng thời gian</strong> (mặc định "Tất cả").</li>
<li>Bấm một dòng trong <strong>Văn bản gần đây</strong> để mở chi tiết.</li>
</ol>
<h3>Bạn thấy gì</h3>
<ul>
<li>5 thẻ số liệu: <strong>Đang có hiệu lực</strong>, <strong>Đang chờ duyệt</strong>, <strong>Cần rà lại</strong>, <strong>Sắp hết hiệu lực</strong> (30 ngày), <strong>Bản nháp</strong>.</li>
<li>Biểu đồ ban hành theo tháng, cơ cấu theo loại, danh sách văn bản gần đây.</li>
</ul>
<p>Số liệu luôn <strong>giới hạn trong phạm vi dữ liệu của bạn</strong>; người khác mở cùng bộ lọc mà ra số khác là do phạm vi khác nhau.</p>""",
                },
                {
                    "title": NV_VB,
                    "icon": "file-text",
                    "content": f"""<h2>Văn bản — dành cho nhân viên</h2>
<p>Trang Văn bản có hai thẻ. Là nhân viên, bạn luôn thấy thẻ <strong>Văn bản đến</strong> — những văn bản mà bạn nằm trong <strong>phạm vi áp dụng</strong> (phải làm theo). Thẻ <strong>Văn bản đi</strong> chỉ hiện khi bạn được cấp quyền xem.</p>
<h3>Xem văn bản áp dụng cho mình</h3>
<ol>
<li>Mở thẻ <strong>Văn bản đến</strong>.</li>
<li>Tìm theo số hiệu, tên hoặc loại văn bản.</li>
<li>Bấm một dòng để mở chi tiết: nội dung, tệp đính kèm, ngày hiệu lực, các văn bản liên quan.</li>
</ol>
<h3>Tự tạo đơn cá nhân</h3>
<p>Nếu được cấp quyền soạn, bạn thấy nút <strong>Tạo văn bản</strong> để tự lập đơn (vd nghỉ phép). Làm theo hướng dẫn từng bước ở {ref(NV_VD, "Ví dụ: Nhân viên tạo giấy xin nghỉ phép")}.</p>
<h3>Lưu ý</h3>
<ul>
<li>Không thấy nút <strong>Tạo văn bản</strong> nghĩa là bạn chưa được cấp quyền soạn.</li>
<li>Đọc kỹ <strong>ngày hiệu lực</strong> và <strong>độ khẩn</strong> của văn bản đến.</li>
</ul>""",
                },
                {
                    "title": NV_SO,
                    "icon": "book-open",
                    "content": """<h2>Sổ văn bản — tra cứu</h2>
<p>Sổ văn bản là nơi văn thư gom và đánh số các văn bản theo từng quyển (Đến / Đi / Nội bộ). Là nhân viên, bạn chỉ thấy những <strong>sổ mà bạn được thêm vào danh sách người xem</strong>.</p>
<h3>Các bước tra cứu</h3>
<ol>
<li>Vào <strong>Văn bản → Sổ văn bản</strong>.</li>
<li>Lọc theo <strong>pháp nhân</strong> và <strong>năm</strong>, chọn thẻ loại sổ (Đến/Đi/Nội bộ).</li>
<li>Mở một sổ để xem danh sách văn bản bên trong cùng số thứ tự trong sổ.</li>
</ol>
<p>Bạn không có nút <strong>Thêm mới</strong> (chỉ văn thư mới khai sổ). Cần xem một sổ chưa thấy, đề nghị người quản lý sổ thêm bạn vào ô <strong>Người xem sổ</strong>.</p>""",
                },
                {
                    "title": NV_VD,
                    "icon": "clipboard-list",
                    "summary": "Từng bước tạo đơn nghỉ phép và gửi trưởng bộ phận duyệt",
                    "content": f"""<h2>Ví dụ: Nhân viên tạo giấy xin nghỉ phép</h2>
<p>Bài này hướng dẫn bạn — nhân viên — tự tạo một <strong>Giấy xin nghỉ phép</strong> và gửi trưởng bộ phận duyệt, đi qua đúng các màn hình thật.</p>

<h3>Bước 1. Đăng nhập &amp; mở trang Văn bản</h3>
<ol>
<li>Mở ứng dụng ở <strong>http://localhost:8083</strong>, đăng nhập bằng tài khoản của bạn.</li>
<li>Ở menu trái chọn phân hệ <strong>Văn bản</strong>, rồi vào mục <strong>Văn bản</strong>.</li>
<li>Bấm nút <strong>Tạo văn bản</strong> (góc trên bên phải). Không thấy nút này nghĩa là bạn chưa được cấp quyền soạn — báo văn thư/quản trị.</li>
</ol>

<h3>Bước 2. Điền "Thông tin chính"</h3>
<p>Form tạo có 3 bước. Ở bước <strong>Thông tin chính</strong>, các ô có dấu <strong>*</strong> là bắt buộc:</p>
<ul>
<li><strong>Tên văn bản</strong> * — vd: "Đơn xin nghỉ phép — Nguyễn Văn A (12–13/09/2026)".</li>
<li><strong>Loại văn bản</strong> * — chọn <strong>Giấy nghỉ phép</strong>. Vừa chọn xong, form sẽ bổ sung khối <strong>Thông tin nghỉ phép</strong> ở bước sau.</li>
<li><strong>Pháp nhân ban hành</strong> * — công ty bạn thuộc về.</li>
<li><strong>Phòng chủ trì</strong> * — phòng của bạn. <em>Hệ thống dựa vào phòng này để tìm đúng trưởng bộ phận duyệt.</em></li>
<li><strong>Người chịu trách nhiệm nội dung</strong> * — thường là chính bạn.</li>
<li><strong>Văn bản mẫu</strong>, <strong>Vào sổ</strong>, <strong>Người soạn</strong> — để trống cũng được.</li>
</ul>
<p>Bấm <strong>Tiếp tục</strong>. Lúc này hệ thống đã lưu một <strong>bản nháp</strong> (bấm <strong>Hủy</strong> sẽ xóa bản nháp vừa sinh).</p>

<h3>Bước 3. Khai "Thông tin nghỉ phép"</h3>
<p>Sang bước <strong>Phạm vi &amp; quyền</strong> sẽ hiện khối <strong>Thông tin nghỉ phép</strong>. Kiểm tra và điền đủ:</p>
<ul>
<li><strong>Người nghỉ</strong> — để mặc định là bạn, hoặc chọn người khác nếu khai hộ.</li>
<li><strong>Loại nghỉ</strong> — Phép năm / Không lương / Ốm đau / Thai sản / Cưới hỏi / Tang chế / Nghỉ bù.</li>
<li><strong>Từ ngày</strong> * và <strong>Buổi</strong> (Cả ngày / Sáng / Chiều).</li>
<li><strong>Đến ngày</strong> * và <strong>Buổi</strong>.</li>
<li><strong>Tổng số ngày</strong> — tự tính, sửa được (đếm cả cuối tuần).</li>
<li><strong>Người bàn giao công việc</strong>, <strong>Số liên lạc khi nghỉ</strong> — nên điền.</li>
<li><strong>Lý do nghỉ</strong> *.</li>
</ul>
<p>Đơn nghỉ phép áp cho riêng bạn nên phần <strong>Phạm vi áp dụng</strong> để trống là được. Bấm <strong>Tiếp tục</strong>.</p>

<h3>Bước 4. "Thông tin bổ sung" rồi tạo</h3>
<p>Bước cuối có thể bỏ qua phần lớn: <strong>Mức mật</strong>/<strong>Độ khẩn</strong> đã có mặc định. Cần nộp kèm giấy tờ (vd giấy khám bệnh) thì kéo thả vào khối <strong>Tệp đính kèm</strong>. Bấm <strong>Tạo và soạn thảo</strong>.</p>

<h3>Bước 5. Kiểm tra rồi Gửi duyệt</h3>
<ol>
<li>Bạn được đưa vào tab <strong>Soạn thảo</strong>. Đơn nghỉ phép thường không cần gõ thêm — thông tin đã nằm ở khối nghỉ phép. Trang <strong>tự động lưu</strong>.</li>
<li>Bấm <strong>Gửi duyệt</strong>. Nếu còn thiếu <strong>Từ ngày / Đến ngày / Lý do</strong>, hệ thống chặn và nhắc — quay lại điền đủ.</li>
<li>Gửi xong, đơn chuyển sang <strong>Đang duyệt</strong> và tự đi tới <strong>trưởng bộ phận của phòng bạn</strong>.</li>
</ol>

<h3>Bước 6. Theo dõi kết quả</h3>
<p>Mở lại đơn ở <strong>Văn bản → Văn bản đi</strong>, xem tab <strong>Phê duyệt</strong> để biết đang ở bước nào. Được duyệt và ban hành thì bạn nhận thông báo ở chuông; bị <strong>Trả lại</strong> thì mở đơn, sửa theo lý do rồi <strong>Gửi duyệt</strong> lại.</p>

{step_btn(TBP_VD, "Bước tiếp theo — Trưởng bộ phận nhận thông báo &amp; duyệt")}""",
                },
            ],
        },
        # ========================= TRƯỞNG BỘ PHẬN ========================= #
        {
            "title": TBP,
            "icon": "shield-check",
            "summary": "Duyệt/trả lại văn bản của bộ phận, theo dõi và tra cứu",
            "content": f"""<h2>Dành cho Trưởng bộ phận</h2>
<p>Là trưởng bộ phận, ngoài đọc và tra cứu như nhân viên, bạn còn là <strong>người duyệt</strong>: văn bản do bộ phận trình sẽ vào hộp <strong>Chờ tôi duyệt</strong> để bạn duyệt hoặc trả lại.</p>
<p>Các trang liên quan: <strong>Tổng quan</strong>, <strong>Văn bản</strong>, <strong>Chờ tôi duyệt</strong>, <strong>Sổ văn bản</strong>. Việc bạn xuất hiện trong luồng duyệt do quản trị/luồng cấu hình, không tự động theo chức danh.</p>
<h3>Bắt đầu bằng ví dụ</h3>
<p>Xem cách nhận thông báo và duyệt một đơn nghỉ phép: {ref(TBP_VD, "Ví dụ: Trưởng bộ phận duyệt giấy nghỉ phép")}.</p>""",
            "children": [
                {
                    "title": TBP_TQ,
                    "icon": "bar-chart",
                    "content": """<h2>Tổng quan — dành cho trưởng bộ phận</h2>
<p>Dùng Tổng quan để nắm nhanh khối lượng văn bản của bộ phận và những việc đang chờ.</p>
<h3>Các bước</h3>
<ol>
<li>Vào <strong>Văn bản → Tổng quan</strong>, lọc theo <strong>phòng ban</strong> của bạn và khoảng thời gian.</li>
<li>Bấm biểu đồ <strong>Việc cần xử lý</strong> hoặc dòng văn bản để đi thẳng tới chi tiết.</li>
</ol>
<h3>Chú ý các thẻ</h3>
<ul>
<li><strong>Đang chờ duyệt</strong> — bao nhiêu văn bản đang ở bước duyệt (một phần là việc của bạn).</li>
<li><strong>Cần rà lại</strong> — văn bản con cần soát vì văn bản cha đã đổi.</li>
<li><strong>Sắp hết hiệu lực</strong> — để nhắc gia hạn/thay thế kịp thời.</li>
</ul>""",
                },
                {
                    "title": TBP_VB,
                    "icon": "file-text",
                    "content": """<h2>Văn bản — dành cho trưởng bộ phận</h2>
<p>Bạn xem được cả <strong>Văn bản đến</strong> (áp cho bạn) và, nếu được cấp quyền đọc, thẻ <strong>Văn bản đi</strong> của bộ phận.</p>
<h3>Theo dõi văn bản bộ phận</h3>
<ol>
<li>Mở thẻ <strong>Văn bản đi</strong>, lọc theo loại/trạng thái/thời gian.</li>
<li>Tìm bản treo lâu ở <strong>Nháp</strong> hoặc <strong>Trả về</strong> để nhắc người soạn.</li>
<li>Cần gửi ra ngoài hoặc lưu, dùng <strong>Xuất Excel</strong>.</li>
</ol>
<p>Việc duyệt không làm ở đây mà ở trang <strong>Chờ tôi duyệt</strong> / trang chi tiết văn bản.</p>""",
                },
                {
                    "title": TBP_CD,
                    "icon": "workflow",
                    "content": f"""<h2>Chờ tôi duyệt — dành cho trưởng bộ phận</h2>
<p>Đây là hộp việc cá nhân: gộp <strong>văn bản đang chờ bạn bấm</strong> (nằm trên) và <strong>văn bản bạn vừa xử lý gần đây</strong> (nằm dưới) trong cùng một bảng.</p>
<h3>Nhận biết có việc</h3>
<ul>
<li>Menu <strong>Chờ tôi duyệt</strong> hiện <strong>huy hiệu số</strong> (đỏ nếu có việc quá hạn).</li>
<li>Bạn còn nhận <strong>thông báo ở chuông</strong>: "<em>Chờ bạn duyệt: {{tên văn bản}}</em>" — bấm là mở thẳng.</li>
</ul>
<h3>Duyệt một văn bản</h3>
<ol>
<li>Bấm dòng để <strong>mở ra đọc</strong> — bảng cố ý không có nút duyệt trên dòng, để bạn đọc kỹ trước.</li>
<li>Tại chi tiết, bấm <strong>Duyệt và ban hành</strong> nếu đồng ý, hoặc <strong>Trả lại</strong> kèm lý do để người soạn sửa.</li>
</ol>
<p>Lọc nhanh theo <strong>chờ / quá hạn / đã duyệt</strong>; phần đã duyệt chọn được mốc 7/30/90 ngày. Xem một ca cụ thể: {ref(TBP_VD, "Ví dụ: Trưởng bộ phận duyệt giấy nghỉ phép")}.</p>""",
                },
                {
                    "title": TBP_SO,
                    "icon": "book-open",
                    "content": """<h2>Sổ văn bản — dành cho trưởng bộ phận</h2>
<p>Bạn tra cứu văn bản của bộ phận trong các sổ được chia. Nếu được giao làm <strong>người quản lý sổ</strong>, bạn còn sửa được thông tin sổ và danh sách người xem.</p>
<h3>Các bước</h3>
<ol>
<li>Vào <strong>Văn bản → Sổ văn bản</strong>, chọn pháp nhân + năm, mở thẻ Đến/Đi/Nội bộ.</li>
<li>Mở một sổ để xem văn bản và số thứ tự trong sổ.</li>
</ol>
<p>Nút <strong>Thêm mới</strong> chỉ hiện khi bạn có quyền tạo sổ — thường là văn thư.</p>""",
                },
                {
                    "title": TBP_VD,
                    "icon": "shield-check",
                    "summary": "Từng bước nhận thông báo và duyệt đơn nghỉ phép",
                    "content": f"""<h2>Ví dụ: Trưởng bộ phận duyệt giấy nghỉ phép</h2>
<p>Tiếp nối ví dụ nhân viên vừa gửi đơn nghỉ phép. Bài này hướng dẫn bạn — trưởng bộ phận — nhận thông báo và duyệt.</p>

<h3>Bước 1. Nhận biết có đơn cần duyệt</h3>
<ul>
<li>Trên menu <strong>Chờ tôi duyệt</strong> xuất hiện <strong>huy hiệu số</strong> (đỏ nếu có việc quá hạn) — đếm số văn bản đang chờ chính bạn.</li>
<li>Bạn cũng nhận <strong>thông báo ở chuông</strong> (góc trên phải): "<em>Chờ bạn duyệt: {{tên đơn}}</em>" — bấm là mở thẳng đơn.</li>
</ul>

<h3>Bước 2. Mở đơn và đọc</h3>
<ol>
<li>Vào <strong>Văn bản → Chờ tôi duyệt</strong> (hoặc bấm thông báo). Đơn chờ nằm ở phần trên bảng.</li>
<li>Bấm dòng để <strong>mở đơn</strong>.</li>
<li>Xem khối <strong>Thông tin nghỉ phép</strong>: loại nghỉ, từ/đến ngày, tổng số ngày, người bàn giao, lý do.</li>
</ol>

<h3>Bước 3. Duyệt hoặc trả lại</h3>
<ul>
<li>Đồng ý: bấm <strong>Duyệt và ban hành</strong> — đơn được duyệt và cấp số.</li>
<li>Chưa hợp lý: bấm <strong>Trả lại</strong>, nhập <strong>lý do</strong> — đơn quay về cho nhân viên sửa.</li>
</ul>

<h3>Bước 4. Sau khi duyệt</h3>
<p>Nhân viên theo dõi kết quả ở tab <strong>Phê duyệt</strong> của đơn; khi ban hành xong hệ thống gửi thông báo. Nếu bạn trả lại, nhân viên nhận lại đơn để chỉnh và gửi tiếp.</p>

{step_btn(NV_VD, "Xem lại — Nhân viên tạo &amp; theo dõi đơn")}""",
                },
            ],
        },
        # ======================= NHÂN VIÊN VĂN THƯ ======================== #
        {
            "title": VT,
            "icon": "clipboard-list",
            "summary": "Soạn, gửi duyệt, ban hành, cấp số, quản lý sổ và danh mục nền",
            "content": f"""<h2>Dành cho Nhân viên văn thư</h2>
<p>Nhân viên văn thư là người <strong>vận hành chính</strong>: soạn văn bản, gửi duyệt, ban hành, cấp số, quản lý các sổ. Bạn cũng khai báo <strong>danh mục nền</strong> (loại văn bản, mẫu, mức mật, đơn vị gửi nhận).</p>
<p>Các trang liên quan: Tổng quan · Nghiệp vụ (Văn bản, Chờ tôi duyệt, Sổ văn bản) · Danh mục (Thiết lập văn bản). Quy tắc đánh số/quan hệ thường thuộc trưởng bộ phận văn thư.</p>
<h3>Bắt đầu bằng ví dụ</h3>
<p>Soạn một thông báo nghỉ lễ gửi nhiều công ty: {ref(VT_VD, "Ví dụ: Văn thư tạo thông báo nghỉ lễ")}.</p>""",
            "children": [
                {
                    "title": VT_TQ,
                    "icon": "bar-chart",
                    "content": """<h2>Tổng quan — dành cho văn thư</h2>
<p>Tổng quan giúp bạn kiểm soát dòng chảy văn bản: bao nhiêu bản nháp đang treo, đang chờ duyệt, sắp hết hiệu lực hay cần rà lại.</p>
<h3>Việc thường làm</h3>
<ol>
<li>Xem thẻ <strong>Bản nháp</strong> và <strong>Đang chờ duyệt</strong> để đốc thúc hoàn tất.</li>
<li>Xem <strong>Sắp hết hiệu lực (30 ngày)</strong> để chuẩn bị gia hạn/thay thế.</li>
<li>Lọc theo pháp nhân/phòng ban/thời gian; bấm biểu đồ hoặc dòng để mở chi tiết.</li>
</ol>""",
                },
                {
                    "title": VT_NV,
                    "icon": "workflow",
                    "content": f"""<h2>Nghiệp vụ — tổng quan nhóm</h2>
<p>"Nghiệp vụ" là nhóm menu gồm ba trang bạn làm việc hằng ngày:</p>
<ul>
<li><strong>Văn bản</strong> — soạn, gửi duyệt, ban hành, cấp số.</li>
<li><strong>Chờ tôi duyệt</strong> — nếu bạn nằm trong luồng, xử lý các bước được giao.</li>
<li><strong>Sổ văn bản</strong> — khai sổ, vào sổ, cấp quyền xem theo quyển.</li>
</ul>
<p>Luồng chuẩn: <strong>Soạn (Nháp) → Gửi duyệt → Duyệt/Ký → Ban hành (cấp số) → Vào sổ</strong>. Xem trọn một ca thật: {ref(VT_VD, "Ví dụ: Văn thư tạo thông báo nghỉ lễ")}.</p>""",
                },
                {
                    "title": VT_VB,
                    "icon": "file-text",
                    "content": f"""<h2>Văn bản — soạn và ban hành</h2>
<p>Đây là nơi bạn tạo và đưa văn bản ra đời. Nút <strong>Tạo văn bản</strong> yêu cầu quyền soạn.</p>
<h3>1. Tạo bản nháp (3 bước)</h3>
<ol>
<li><strong>Thông tin chính</strong>: điền <strong>Tên văn bản</strong>, <strong>Loại văn bản</strong>, <strong>Pháp nhân ban hành</strong>, <strong>Phòng chủ trì</strong>, <strong>Người chịu trách nhiệm nội dung</strong> (đều bắt buộc); chọn <strong>Vào sổ</strong> nếu cần cấp số thứ tự trong sổ. Bấm <strong>Tiếp tục</strong> là đã có bản nháp.</li>
<li><strong>Phạm vi &amp; quyền</strong>: khai <strong>Phạm vi áp dụng</strong> (ai phải làm theo) và <strong>Quyền truy cập</strong> (ai được đọc) — hai khối tách riêng.</li>
<li><strong>Thông tin bổ sung</strong>: mức mật/độ khẩn, ngày hiệu lực, từ khóa, trích yếu, tệp đính kèm. Bấm <strong>Tạo và soạn thảo</strong>.</li>
</ol>
<h3>2. Soạn thảo &amp; gửi duyệt</h3>
<ol>
<li>Ở tab <strong>Soạn thảo</strong>, gõ nội dung (tự động lưu); có thể dùng <strong>Văn bản mẫu</strong> hoặc nhập từ Word.</li>
<li>Kiểm tra <strong>quan hệ bắt buộc</strong> (theo Quy tắc quan hệ) đã đủ, nếu thiếu sẽ bị chặn.</li>
<li>Bấm <strong>Gửi duyệt</strong> — nội dung đóng băng, văn bản chuyển sang <strong>Đang duyệt</strong>.</li>
</ol>
<h3>3. Ban hành &amp; cấp số</h3>
<ul>
<li>Loại <strong>tự ban hành sau duyệt</strong>: duyệt xong là ban hành và cấp số ngay.</li>
<li>Loại <strong>không tự ban hành</strong>: ký đủ → <strong>Chờ ban hành</strong>; <strong>chính người soạn</strong> bấm <strong>Ban hành</strong>, chọn hộp thư gửi thông báo → phát hành và cấp số.</li>
</ul>
<p><strong>Xóa</strong> chỉ được khi văn bản còn nháp/bị trả về và <strong>chưa cấp số</strong>. Làm theo ví dụ đầy đủ: {ref(VT_VD, "Ví dụ: Văn thư tạo thông báo nghỉ lễ")}.</p>""",
                },
                {
                    "title": VT_CD,
                    "icon": "workflow",
                    "content": """<h2>Chờ tôi duyệt — dành cho văn thư</h2>
<p>Nếu bạn được phân vào một bước trong luồng phê duyệt, các văn bản chờ bạn xử lý sẽ nằm ở đây (kèm huy hiệu số trên menu và thông báo ở chuông).</p>
<h3>Cách xử lý</h3>
<ol>
<li>Bấm dòng để mở văn bản, kiểm tra nội dung, số hiệu dự kiến và các quan hệ.</li>
<li>Tại chi tiết, thực hiện bước được giao: duyệt/chuyển tiếp hoặc trả lại kèm lý do.</li>
</ol>
<p>Phần dưới bảng là các văn bản bạn <strong>vừa xử lý gần đây</strong> để tra lại. Chú ý cảnh báo quá hạn.</p>""",
                },
                {
                    "title": VT_SO,
                    "icon": "book-open",
                    "content": """<h2>Sổ văn bản — khai và quản lý</h2>
<p>Sổ là nơi vào số và cấp quyền xem theo quyển. Bạn quản lý ba loại: <strong>Đến · Đi · Nội bộ</strong>, mỗi sổ có <strong>bộ đếm số riêng</strong> (đếm lại từ 1 mỗi năm).</p>
<h3>Tạo và cấu hình sổ</h3>
<ol>
<li>Vào <strong>Văn bản → Sổ văn bản</strong>, chọn thẻ loại sổ, bấm <strong>Thêm mới</strong>.</li>
<li>Khai <strong>Mã sổ, Tên sổ, Pháp nhân, Người quản lý</strong> và <strong>Người xem sổ</strong>.</li>
<li>Người trong "Người xem sổ" tra cứu được văn bản trong quyển; người quản lý sửa được sổ.</li>
</ol>
<h3>Vào sổ</h3>
<p>Khi văn bản gắn vào một sổ, hệ thống cấp <strong>số thứ tự trong sổ</strong> (vd <em>CVĐ 08/2026</em>) và trao quyền theo quyển. Theo dõi <strong>Số kế tiếp</strong> và <strong>Đã cấp trong năm</strong> trên danh sách.</p>""",
                },
                {
                    "title": VT_DM,
                    "icon": "tags",
                    "content": f"""<h2>Danh mục — tổng quan nhóm</h2>
<p>"Danh mục" là nhóm menu chứa các phần khai báo nền: <strong>Thiết lập văn bản</strong> (loại, mẫu, mức mật, đơn vị gửi nhận), <strong>Quy tắc đánh số</strong> và <strong>Quy tắc quan hệ</strong>.</p>
<p>Là nhân viên văn thư, bạn thường phụ trách {ref(VT_TL, "Thiết lập văn bản")}. Hai quy tắc {ref(TVT_DS, "đánh số")} và {ref(TVT_QH, "quan hệ")} thường do trưởng bộ phận văn thư cấu hình.</p>""",
                },
                {
                    "title": VT_TL,
                    "icon": "settings",
                    "content": """<h2>Thiết lập văn bản</h2>
<p>Trang này gom bốn danh mục nền, mỗi thẻ tự ẩn/hiện theo quyền của bạn.</p>
<h3>Bốn thẻ</h3>
<ul>
<li><strong>Loại văn bản</strong> — quyết định lược đồ số hiệu, mức mật mặc định, các bước bắt buộc và bộ trường riêng (vd Giấy nghỉ phép mã GNP).</li>
<li><strong>Thư viện văn bản mẫu</strong> — nội dung mẫu theo loại, người soạn dùng làm điểm bắt đầu.</li>
<li><strong>Mức mật / Độ khẩn</strong> — thêm bậc mới được; bậc đã tạo chỉ sửa tên/mô tả/trạng thái.</li>
<li><strong>Đơn vị gửi nhận</strong> — cơ quan/doanh nghiệp/cá nhân/đơn vị nội bộ trao đổi văn bản.</li>
</ul>
<h3>Thao tác</h3>
<ol>
<li>Chọn thẻ cần khai (thẻ đang xem ghi lên URL <em>?tab=</em>).</li>
<li>Bấm <strong>Thêm mới</strong>, hoặc mở một dòng để vào trang chi tiết chỉnh sửa.</li>
</ol>
<p>Thẻ bị ẩn nghĩa là bạn chưa có quyền đọc danh mục đó — đề nghị quản trị cấp.</p>""",
                },
                {
                    "title": VT_VD,
                    "icon": "clipboard-list",
                    "summary": "Từng bước soạn thông báo nghỉ lễ, chọn phạm vi nhiều công ty và gửi duyệt",
                    "content": f"""<h2>Ví dụ: Văn thư tạo thông báo nghỉ lễ</h2>
<p>Bài này hướng dẫn bạn — nhân viên văn thư — soạn một <strong>Thông báo nghỉ lễ</strong> áp cho nhiều công ty và gửi trưởng bộ phận văn thư duyệt.</p>

<h3>Bước 1. Đăng nhập &amp; mở Tạo văn bản</h3>
<ol>
<li>Đăng nhập <strong>http://localhost:8083</strong>, vào phân hệ <strong>Văn bản → Văn bản</strong>.</li>
<li>Bấm <strong>Tạo văn bản</strong>.</li>
</ol>

<h3>Bước 2. Thông tin chính</h3>
<ul>
<li><strong>Tên văn bản</strong> * — vd: "Thông báo lịch nghỉ lễ Quốc khánh 02/09/2026".</li>
<li><strong>Loại văn bản</strong> * — chọn <strong>Thông báo</strong>. (Loại này dùng bộ trường chung, không có khối riêng như nghỉ phép.)</li>
<li><strong>Pháp nhân ban hành</strong> * — công ty đứng tên ban hành (vd công ty mẹ/Holding).</li>
<li><strong>Phòng chủ trì</strong> * — phòng Hành chính–Văn thư.</li>
<li><strong>Người chịu trách nhiệm nội dung</strong> * — người phụ trách.</li>
<li><strong>Vào sổ</strong> — nên chọn sổ "Văn bản đi" để cấp số thứ tự trong sổ.</li>
</ul>
<p>Bấm <strong>Tiếp tục</strong>.</p>

<h3>Bước 3. Phạm vi áp dụng — chọn từng công ty</h3>
<p>Đây là bước quyết định thông báo tới đúng các công ty. Ở khối <strong>Phạm vi áp dụng</strong>, bấm <strong>Thêm dòng phạm vi</strong>:</p>
<ol>
<li><strong>Cách áp</strong> = <strong>Bao gồm</strong>.</li>
<li><strong>Áp theo</strong> = <strong>Pháp nhân</strong>.</li>
<li>Chọn <strong>các pháp nhân (công ty)</strong> cần nhận; bật <strong>Gồm cả đơn vị con</strong> nếu muốn phủ luôn công ty con.</li>
</ol>
<p>Vì có pháp nhân ngoài nơi ban hành, form hiện thêm khối <strong>Bản clone ở pháp nhân con</strong> — có thể đặt <strong>Hạn xử lý</strong> và <strong>Ghi chú cho pháp nhân nhận</strong>. Bấm <strong>Tiếp tục</strong>.</p>

<h3>Bước 4. Thông tin bổ sung rồi tạo</h3>
<p>Đặt <strong>Ngày hiệu lực</strong> (vd ngày công bố), <strong>Độ khẩn</strong> phù hợp; đính kèm file nếu có. Bấm <strong>Tạo và soạn thảo</strong>.</p>

<h3>Bước 5. Soạn nội dung rồi Gửi duyệt</h3>
<ol>
<li>Ở tab <strong>Soạn thảo</strong>, gõ nội dung thông báo (lịch nghỉ, số ngày, lịch trực…). Có thể dùng <strong>Văn bản mẫu</strong> hoặc nút nhập từ Word. Trang tự động lưu.</li>
<li>Bấm <strong>Gửi duyệt</strong> — thông báo chuyển sang <strong>Đang duyệt</strong> và tới <strong>trưởng bộ phận văn thư</strong>.</li>
</ol>

{step_btn(TVT_VD, "Bước tiếp theo — Trưởng bộ phận văn thư duyệt &amp; ban hành")}""",
                },
            ],
        },
        # ==================== TRƯỞNG BỘ PHẬN VĂN THƯ ===================== #
        {
            "title": TVT,
            "icon": "shield-check",
            "summary": "Vận hành như văn thư, cấu hình quy tắc đánh số/quan hệ và duyệt/ký",
            "content": f"""<h2>Dành cho Trưởng bộ phận văn thư</h2>
<p>Trưởng bộ phận văn thư làm mọi việc của nhân viên văn thư, cộng thêm <strong>cấu hình luật của cả hệ</strong>: quy tắc đánh số, quy tắc quan hệ cha–con, và thường là <strong>người duyệt/ký</strong> ở một chặng trong luồng.</p>
<p>Các trang liên quan: Tổng quan · Văn bản · Chờ tôi duyệt · Sổ văn bản · Thiết lập văn bản (đủ 4 thẻ) · Quy tắc đánh số · Quy tắc quan hệ.</p>
<h3>Bắt đầu bằng ví dụ</h3>
<p>Duyệt và ban hành thông báo nghỉ lễ tới từng công ty: {ref(TVT_VD, "Ví dụ: Duyệt và ban hành thông báo nghỉ lễ")}.</p>""",
            "children": [
                {
                    "title": TVT_TQ,
                    "icon": "bar-chart",
                    "content": """<h2>Tổng quan — dành cho trưởng bộ phận văn thư</h2>
<p>Bạn dùng Tổng quan để giám sát toàn bộ dòng văn bản và phát hiện điểm nghẽn.</p>
<h3>Nhìn vào đâu</h3>
<ul>
<li><strong>Đang chờ duyệt</strong> và biểu đồ <strong>Việc cần xử lý</strong> — phát hiện văn bản kẹt ở một chặng.</li>
<li><strong>Cần rà lại</strong> — văn bản con cần soát vì văn bản cha đã đổi.</li>
<li><strong>Ma trận mức độ quan trọng × khẩn cấp</strong> — ưu tiên xử lý.</li>
</ul>
<p>Lọc theo pháp nhân/phòng ban để soi từng đơn vị.</p>""",
                },
                {
                    "title": TVT_VB,
                    "icon": "file-text",
                    "content": """<h2>Văn bản — dành cho trưởng bộ phận văn thư</h2>
<p>Bạn xem và soạn như văn thư, nhưng ở vai trò giám sát, hãy tập trung vào <strong>chất lượng và tính hợp lệ</strong> trước khi văn bản ra ngoài.</p>
<h3>Việc nên làm</h3>
<ol>
<li>Rà thẻ <strong>Văn bản đi</strong>: lọc theo trạng thái để tìm bản treo lâu ở <strong>Nháp</strong> hay <strong>Trả về</strong>.</li>
<li>Kiểm tra số hiệu, loại và quan hệ đã khai đúng quy tắc.</li>
<li>Với văn bản cần bạn ký, xử lý ở <strong>Chờ tôi duyệt</strong>.</li>
</ol>""",
                },
                {
                    "title": TVT_CD,
                    "icon": "workflow",
                    "content": f"""<h2>Chờ tôi duyệt — dành cho trưởng bộ phận văn thư</h2>
<p>Là một chặng trong luồng (thường sau trưởng bộ phận, trước giám đốc), bạn duyệt và có thể là người <strong>ban hành</strong>.</p>
<h3>Nhận biết &amp; xử lý</h3>
<ol>
<li>Menu <strong>Chờ tôi duyệt</strong> hiện huy hiệu số; chuông báo "<em>Chờ bạn duyệt: …</em>".</li>
<li>Bấm dòng để mở văn bản; đọc kỹ nội dung, mức mật, quan hệ bắt buộc.</li>
<li>Bấm <strong>Duyệt</strong> để chuyển tiếp, <strong>Duyệt và ban hành</strong> nếu bạn là bước cuối, hoặc <strong>Trả lại</strong> kèm lý do.</li>
<li>Nếu có quyền hủy, bạn còn <strong>Bãi bỏ</strong> được văn bản đã ban hành (giữ số hiệu, thu hồi quyền xem).</li>
</ol>
<p>Xem một ca có ban hành gửi nhiều công ty: {ref(TVT_VD, "Ví dụ: Duyệt và ban hành thông báo nghỉ lễ")}.</p>""",
                },
                {
                    "title": TVT_SO,
                    "icon": "book-open",
                    "content": """<h2>Sổ văn bản — dành cho trưởng bộ phận văn thư</h2>
<p>Bạn quản lý toàn bộ hệ thống sổ: mở sổ mới theo năm, phân người quản lý và người xem, đảm bảo mỗi chiều (Đến/Đi/Nội bộ) có sổ phù hợp.</p>
<h3>Quản trị sổ</h3>
<ol>
<li>Đầu năm, mở sổ mới cho từng pháp nhân/loại; bộ đếm số tự đếm lại từ 1.</li>
<li>Giao <strong>người quản lý sổ</strong> cho từng văn thư phụ trách.</li>
<li>Kiểm soát <strong>người xem sổ</strong> để cấp quyền tra cứu đúng người.</li>
</ol>""",
                },
                {
                    "title": TVT_TL,
                    "icon": "settings",
                    "content": f"""<h2>Thiết lập văn bản — đầy đủ bốn thẻ</h2>
<p>Với đủ quyền, bạn thấy và khai được cả bốn thẻ: <strong>Loại văn bản</strong>, <strong>Thư viện văn bản mẫu</strong>, <strong>Mức mật / Độ khẩn</strong>, <strong>Đơn vị gửi nhận</strong>.</p>
<h3>Ưu tiên khai đúng "Loại văn bản"</h3>
<ul>
<li>Loại văn bản là gốc: gắn <strong>lược đồ số hiệu</strong>, <strong>mức mật mặc định</strong>, các <strong>bước bắt buộc</strong> và bộ trường (metadata) riêng.</li>
<li>Khai loại trước rồi mới gắn {ref(TVT_DS, "Quy tắc đánh số")} và {ref(TVT_QH, "Quy tắc quan hệ")} cho loại đó.</li>
</ul>
<h3>Thao tác</h3>
<ol>
<li>Chọn thẻ, bấm <strong>Thêm mới</strong>, hoặc mở một dòng để vào trang chi tiết.</li>
<li>Với "Đơn vị gửi nhận", khai đủ cơ quan/doanh nghiệp/cá nhân để form soạn thảo chọn nhanh.</li>
</ol>""",
                },
                {
                    "title": TVT_DS,
                    "icon": "tags",
                    "content": """<h2>Quy tắc đánh số</h2>
<p>Nơi định <strong>mẫu số hiệu và bộ đếm tự động</strong> cho từng chiều văn bản — ba thẻ <strong>Đến · Đi · Nội bộ</strong>. Máy chủ cấp số theo các quy tắc này, nên client không tự đánh số.</p>
<h3>Tạo một quy tắc</h3>
<ol>
<li>Vào <strong>Văn bản → Quy tắc đánh số</strong>, chọn thẻ chiều văn bản, bấm <strong>Thêm mới</strong> (mở trang riêng vì form dài).</li>
<li>Khai <strong>mẫu số</strong> (pattern) + <strong>độ ưu tiên</strong>, và <strong>phạm vi áp dụng</strong> theo loại văn bản / sổ.</li>
<li>Chọn <strong>số bắt đầu</strong>, cách đếm (<strong>theo năm</strong> hay <strong>liên tục</strong>), và có cho <strong>sửa số tay</strong> hay không.</li>
</ol>
<h3>Lưu ý</h3>
<ul>
<li>Nhiều quy tắc có thể cùng áp — <strong>độ ưu tiên</strong> quyết định cái nào thắng.</li>
<li>Đổi quy tắc chỉ ảnh hưởng văn bản cấp số <strong>từ đây về sau</strong>, không đánh lại số cũ.</li>
</ul>""",
                },
                {
                    "title": TVT_QH,
                    "icon": "workflow",
                    "content": """<h2>Quy tắc quan hệ</h2>
<p>Quy tắc quan hệ định các <strong>quan hệ cha–con</strong> giữa các loại văn bản. Nó điều khiển hai thứ người soạn gặp hằng ngày: form hiện <strong>ô quan hệ nào</strong>, và văn bản có <strong>bị chặn gửi duyệt</strong> khi thiếu quan hệ bắt buộc hay không.</p>
<h3>Tạo một quy tắc</h3>
<ol>
<li>Vào <strong>Văn bản → Quy tắc quan hệ</strong>, bấm <strong>Thêm mới</strong>; chọn <strong>loại văn bản áp dụng</strong> và <strong>loại quan hệ</strong> (có thể đặt "Khóa").</li>
<li>Chọn <strong>loại văn bản đích</strong> mà quan hệ trỏ tới.</li>
<li>Đặt ràng buộc <strong>Bắt buộc</strong> hay <strong>Tùy chọn</strong>, số văn bản cho phép, có <strong>kế thừa đánh số</strong> và <strong>không hạ mức mật</strong> hay không.</li>
</ol>
<p>Có thể khai quan hệ ngay trong trang <strong>Loại văn bản</strong>. Đặt "Bắt buộc" cho quan hệ nào thì người soạn buộc phải khai trước khi gửi duyệt.</p>""",
                },
                {
                    "title": TVT_VD,
                    "icon": "shield-check",
                    "summary": "Từng bước duyệt và ban hành thông báo, gửi tới từng công ty",
                    "content": f"""<h2>Ví dụ: Duyệt và ban hành thông báo nghỉ lễ</h2>
<p>Tiếp nối ví dụ văn thư vừa gửi thông báo nghỉ lễ. Bài này hướng dẫn bạn — trưởng bộ phận văn thư — duyệt và ban hành để gửi tới từng công ty.</p>

<h3>Bước 1. Nhận biết &amp; mở</h3>
<ul>
<li>Menu <strong>Chờ tôi duyệt</strong> hiện huy hiệu số; chuông báo "<em>Chờ bạn duyệt: …</em>".</li>
<li>Vào <strong>Văn bản → Chờ tôi duyệt</strong>, bấm dòng để mở thông báo; đọc nội dung và phạm vi các công ty nhận.</li>
</ul>

<h3>Bước 2. Duyệt và ban hành</h3>
<ol>
<li>Bấm <strong>Duyệt và ban hành</strong> — mở hộp <strong>Ban hành văn bản</strong>.</li>
<li>Hệ thống cho biết: vì phạm vi gồm nhiều pháp nhân con, bấm Ban hành sẽ <strong>sinh bản riêng cho từng công ty</strong> (mỗi nơi một số hiệu).</li>
<li>Ở ô <strong>Gửi thông báo danh nghĩa</strong>, chọn <strong>hộp thư</strong> phù hợp (vd hộp thư Văn thư/Hành chính) để thư mang địa chỉ phòng ban thay vì cá nhân; để mặc định cũng được.</li>
<li>Bấm <strong>Ban hành</strong>.</li>
</ol>

<h3>Bước 3. Các công ty nhận thông báo</h3>
<p>Sau ban hành, hệ thống gửi <strong>thông báo ở chuông và email</strong> "[Văn bản mới] {{số hiệu}} — {{tên}}" tới mọi người trong phạm vi mỗi công ty. Người nhận thấy nó ở <strong>Văn bản → Văn bản đến</strong>.</p>
<p>Nếu chưa hợp lý, thay vì ban hành bạn có thể <strong>Trả lại</strong> kèm lý do để văn thư sửa.</p>

{step_btn(VT_VD, "Xem lại — Văn thư soạn thông báo")}""",
                },
            ],
        },
        # ======================= GIÁM ĐỐC CÔNG TY ======================== #
        {
            "title": GD,
            "icon": "building",
            "summary": "Ký/ban hành cuối và theo dõi toàn cảnh văn bản của công ty",
            "content": """<h2>Dành cho Giám đốc công ty</h2>
<p>Giám đốc thường là <strong>bước ký/ban hành cuối</strong> trong luồng và là người theo dõi toàn cảnh văn bản của công ty. Bạn ít khi soạn thảo; việc chính là <strong>duyệt/ký</strong> và <strong>giám sát</strong>.</p>
<p>Các trang liên quan: Tổng quan · Chờ tôi duyệt · Văn bản · Sổ văn bản.</p>""",
            "children": [
                {
                    "title": GD_TQ,
                    "icon": "bar-chart",
                    "content": """<h2>Tổng quan — dành cho giám đốc</h2>
<p>Dùng Tổng quan như bảng điều khiển cấp công ty: khối lượng ban hành, việc đang chờ, rủi ro hết hiệu lực.</p>
<h3>Theo dõi</h3>
<ul>
<li>Lọc theo <strong>pháp nhân</strong> công ty bạn phụ trách.</li>
<li><strong>Văn bản ban hành theo tháng</strong> — nhịp độ ban hành.</li>
<li><strong>Đang chờ duyệt</strong> — trong đó có việc chờ chính bạn ký.</li>
<li><strong>Sắp hết hiệu lực</strong> — để chỉ đạo gia hạn/thay thế.</li>
</ul>""",
                },
                {
                    "title": GD_CD,
                    "icon": "workflow",
                    "content": """<h2>Chờ tôi duyệt — dành cho giám đốc</h2>
<p>Đây là hộp việc ký của bạn. Văn bản đã qua các chặng trước và đang chờ bạn quyết sẽ nằm ở đầu bảng (kèm huy hiệu số trên menu và thông báo ở chuông).</p>
<h3>Ký/ban hành</h3>
<ol>
<li>Bấm dòng để mở văn bản, đọc bản trình và các văn bản liên quan.</li>
<li>Bấm <strong>Duyệt và ban hành</strong> để phát hành (hệ thống cấp số trong cùng giao dịch), hoặc <strong>Trả lại</strong> kèm lý do.</li>
<li>Chữ ký gắn với đúng <strong>phiên bản</strong> văn bản bạn duyệt.</li>
</ol>
<p>Chú ý băng <strong>quá hạn duyệt</strong> để không giữ văn bản quá lâu.</p>""",
                },
                {
                    "title": GD_VB,
                    "icon": "file-text",
                    "content": """<h2>Văn bản — dành cho giám đốc</h2>
<p>Bạn tra cứu văn bản đã và đang ban hành của công ty ở thẻ <strong>Văn bản đi</strong>, và các văn bản áp cho bạn ở <strong>Văn bản đến</strong>.</p>
<h3>Tra cứu nhanh</h3>
<ol>
<li>Mở <strong>Văn bản đi</strong>, lọc theo loại/trạng thái/thời gian.</li>
<li>Bấm một dòng để xem toàn văn, người ký, ngày hiệu lực và lịch sử phiên bản.</li>
</ol>""",
                },
                {
                    "title": GD_SO,
                    "icon": "book-open",
                    "content": """<h2>Sổ văn bản — dành cho giám đốc</h2>
<p>Bạn tra cứu văn bản theo sổ của công ty (Đến/Đi/Nội bộ). Việc khai và quản lý sổ do văn thư đảm nhiệm.</p>
<h3>Tra cứu</h3>
<ol>
<li>Vào <strong>Văn bản → Sổ văn bản</strong>, chọn pháp nhân công ty + năm, mở thẻ loại sổ.</li>
<li>Mở một sổ để xem toàn bộ văn bản và số thứ tự trong sổ.</li>
</ol>
<p>Cần xem sổ chưa thấy, đề nghị văn thư thêm bạn vào <strong>Người xem sổ</strong>.</p>""",
                },
            ],
        },
    ],
}


# --------------------------------------------------------------------------- #
#  DỰNG CÂY
# --------------------------------------------------------------------------- #
def collect_descendants(db, root_id):
    result = []
    frontier = [(root_id, 0)]
    while frontier:
        nid, depth = frontier.pop()
        result.append((nid, depth))
        for (cid,) in db.query(HelpArticle.id).filter(HelpArticle.parent_id == nid).all():
            frontier.append((cid, depth + 1))
    return result


def delete_subtree(db, root_id):
    #  Xóa RAW theo thứ tự sâu-trước: FK tự tham chiếu parent_id KHÔNG cascade và
    #  không khai relationship nên unit-of-work của ORM tự sắp xếp sai (xóa cha
    #  trước con -> 1451). Cascade của slides/home_item là ở tầng DB, tự lo.
    nodes = collect_descendants(db, root_id)
    for nid, _ in sorted(nodes, key=lambda x: x[1], reverse=True):
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
        count += insert_node(db, child, art.id, i)
    return count


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

        total = insert_node(db, TREE, None, next_order)
        db.commit()
        print(f"Đã dựng cây Văn thư: {total} bài (sort_order gốc = {next_order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
