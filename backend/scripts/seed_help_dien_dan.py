# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho phân hệ DIỄN ĐÀN NỘI BỘ.

Dựng cây bài viết hướng dẫn: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ")
-> 7 bài theo TÁC VỤ (làm quen / đăng bài / chuyên mục / tương tác / tìm kiếm /
trang của tôi / quản trị) — diễn đàn ai cũng dùng như nhau nên không chia theo
vai trò như bộ Văn thư; riêng bài Quản trị dành cho người được gán quyền.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_dien_dan.py

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự
tham chiếu không cascade) rồi dựng lại; thẻ ngoài trang chủ (HelpHomeItem khung
categories) tự gắn nếu chưa có.

CHỈ chạy ở môi trường ĐÃ có diễn đàn (local + dev). Prod chưa deploy diễn đàn —
đừng chạy ở prod cho tới khi phân hệ lên prod.
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

ROOT_TITLE = "Hướng dẫn sử dụng Diễn đàn nội bộ"


# --------------------------------------------------------------------------- #
#  LIÊN KẾT NỘI BỘ — slug sinh y hệt hàm slugify() của help-center
#  (help-slug.tsx) vì portal tra ngược slug -> id ngay trên client.
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
#  TIÊU ĐỀ (hằng, để tham chiếu chéo khỏi gõ nhầm)
# --------------------------------------------------------------------------- #
LAM_QUEN = "Làm quen với Diễn đàn nội bộ"
DANG_BAI = "Đăng bài viết mới trên diễn đàn"
CHUYEN_MUC = "Các chuyên mục trên diễn đàn"
TUONG_TAC = "Thả cảm xúc, bình luận và nhắc tên"
TIM_KIEM = "Tìm kiếm bài viết trên diễn đàn"
TRANG_TOI = "Trang của tôi và quản lý bài đã đăng"
QUAN_TRI = "Dành cho Quản trị viên diễn đàn"


# --------------------------------------------------------------------------- #
#  CÂY NỘI DUNG
# --------------------------------------------------------------------------- #
TREE = {
    "title": ROOT_TITLE,
    "icon": "users",
    "summary": "Mạng xã hội nội bộ của tập đoàn: đăng bài, chuyên mục, cảm xúc, bình luận",
    "content": f"""<h2>Diễn đàn nội bộ là gì?</h2>
<p>Diễn đàn là <strong>mạng xã hội nội bộ</strong> của tập đoàn, nằm ngay trong hệ thống ERP: nơi đăng thông báo, vinh danh khen thưởng, trao đổi công việc, chia sẻ đời sống và kết nối đồng nghiệp giữa các công ty, phòng ban. Mọi tài khoản ERP đều dùng được, không cần cấp thêm quyền.</p>
<h3>Năm khu vực chính</h3>
<ul>
<li><strong>Diễn đàn</strong> — trang mặc định: các chuyên mục xếp theo nhóm chủ đề (Thông báo &amp; Chính sách, Công việc, Văn hóa &amp; Sự kiện, Đời sống). Xem {ref(CHUYEN_MUC, "danh sách chuyên mục")}.</li>
<li><strong>Bảng tin</strong> — dòng thời gian kiểu mạng xã hội: bài mới của đồng nghiệp trong phạm vi bạn được xem, cuộn tới đâu tải tới đó.</li>
<li><strong>Thông báo</strong> — mọi bài đang được quản trị viên ghim (nghỉ lễ, quy định mới...), nhìn một trang là nắm hết thông báo còn hiệu lực.</li>
<li><strong>Trang của tôi</strong> — toàn bộ bài bạn đã đăng. Xem {ref(TRANG_TOI, "Trang của tôi")}.</li>
<li><strong>Quản trị</strong> — chỉ hiện với người được gán quyền quản trị diễn đàn. Xem {ref(QUAN_TRI, "bài dành cho quản trị viên")}.</li>
</ul>
<h3>Đọc theo tác vụ</h3>
<p>Bộ hướng dẫn chia theo việc bạn muốn làm: {ref(LAM_QUEN, "làm quen")} · {ref(DANG_BAI, "đăng bài")} · {ref(TUONG_TAC, "tương tác")} · {ref(TIM_KIEM, "tìm kiếm")}.</p>""",
    "children": [
        {
            "title": LAM_QUEN,
            "icon": "rocket",
            "summary": "Bố cục các tab, cách đọc bài, xem ảnh phóng to và xem video",
            "content": f"""<h2>Làm quen với Diễn đàn nội bộ</h2>
<p>Từ màn chọn phân hệ của ERP, bấm thẻ <strong>Diễn đàn</strong>. Giao diện là một trang riêng không có menu trái của ERP — thanh trên cùng có các tab <strong>Diễn đàn · Bảng tin · Thông báo · Trang của tôi</strong> (và <strong>Quản trị</strong> nếu bạn có quyền), kèm ô tìm bài viết.</p>
<h3>Tab Diễn đàn (mặc định)</h3>
<ul>
<li>Các chuyên mục xếp theo <strong>nhóm chủ đề</strong>; mỗi chuyên mục hiện mô tả, số chủ đề và bài mới nhất — bấm vào để xem danh sách chủ đề bên trong.</li>
<li>Cột phải (màn hình rộng) có ba khung: <strong>Nổi bật</strong> (bài được ghim), <strong>Đang sôi nổi</strong> (5 chủ đề được bàn tán nhiều nhất 7 ngày qua) và <strong>Mới nhất</strong>. Trên điện thoại, khung Nổi bật dồn lên đầu trang.</li>
</ul>
<h3>Tab Bảng tin</h3>
<ul>
<li>Dòng thời gian kiểu mạng xã hội: bài mới nhất trên cùng, cuộn xuống tự tải tiếp.</li>
<li>Đang đọc mà có bài mới, đầu trang hiện nút <strong>«Có bài viết mới»</strong> — bấm để cập nhật.</li>
<li>Bài dài được thu gọn, bấm <strong>«Xem thêm»</strong> để đọc trọn.</li>
</ul>
<h3>Đọc một bài viết</h3>
<ul>
<li>Bấm vào bài trên Bảng tin sẽ mở <strong>cửa sổ chi tiết</strong> ngay tại chỗ — đóng lại là về đúng vị trí đang cuộn. Trang chi tiết chữ to hơn, không thu gọn, đọc bài dài thoải mái.</li>
<li><strong>Bấm vào bất kỳ ảnh nào</strong> (ảnh đính kèm lẫn ảnh nằm trong nội dung bài) để phóng to: có nút chuyển ảnh, dải ảnh thu nhỏ, tải xuống và sao chép liên kết; bấm dấu X, phím Esc hoặc nền tối để đóng.</li>
<li>Video trong bài phát trực tiếp ngay trên trang.</li>
</ul>
<p>Sẵn sàng rồi thì sang bài {ref(DANG_BAI, "Đăng bài viết mới")}.</p>""",
        },
        {
            "title": DANG_BAI,
            "icon": "file-text",
            "summary": "Soạn bài có định dạng, chèn ảnh/video, chọn đối tượng xem, đăng vào chuyên mục",
            "content": f"""<h2>Đăng bài viết mới</h2>
<h3>Mở khung đăng bài</h3>
<ul>
<li><strong>Đăng lên Bảng tin:</strong> vào tab Bảng tin, bấm ô <strong>«Bạn đang nghĩ gì?»</strong> trên đầu trang.</li>
<li><strong>Đăng vào chuyên mục:</strong> mở chuyên mục muốn đăng rồi bấm nút tạo chủ đề — bài sẽ nằm trong chuyên mục đó và vẫn xuất hiện trên Bảng tin.</li>
</ul>
<h3>Soạn nội dung</h3>
<ul>
<li>Khung soạn hỗ trợ <strong>định dạng phong phú</strong>: tiêu đề, chữ đậm/nghiêng, danh sách, bảng... như soạn văn bản.</li>
<li><strong>Chèn ảnh/video:</strong> kéo thả vào khung, dán từ bộ nhớ tạm, hoặc bấm nút đính kèm. Tối đa <strong>10 tệp mỗi bài, 50MB mỗi tệp</strong>; video nhận định dạng mp4/webm.</li>
<li><strong>Dán bài từ trang web</strong> (bài báo, tài liệu...) giữ nguyên định dạng, ảnh và chú thích ảnh.</li>
<li>Bấm nút mặt cười để chèn <strong>emoji</strong> vào bài.</li>
</ul>
<h3>Chọn đối tượng xem</h3>
<ul>
<li>Bài đăng lên Bảng tin chọn được một trong ba phạm vi: <strong>Phòng ban</strong> (chỉ người cùng phòng thấy) · <strong>Công ty</strong> (người cùng pháp nhân) · <strong>Toàn tập đoàn</strong>. Hệ thống nhớ lựa chọn lần trước của bạn.</li>
<li>Bài đăng vào <strong>chuyên mục</strong> luôn hiển thị toàn tập đoàn — không phải chọn.</li>
</ul>
<h3>Bài trong chuyên mục có thêm gì?</h3>
<ul>
<li><strong>Tiêu đề</strong> là bắt buộc — người khác lướt danh sách chủ đề bằng tiêu đề.</li>
<li>Chọn thêm <strong>nhãn đầu bài</strong> (không bắt buộc): Thảo luận · Thắc mắc · Kiến thức · Khoe · Đánh giá — giúp người đọc biết ngay bài thuộc dạng gì.</li>
</ul>
<h3>Lưu ý</h3>
<ul>
<li>Hiện <strong>chưa có sửa bài sau khi đăng</strong> — cần sửa thì xóa bài rồi đăng lại (xem {ref(TRANG_TOI, "cách xóa bài")}).</li>
<li>Nội dung đang gõ dở không mất khi lỡ đóng khung đăng — mở lại là còn.</li>
</ul>""",
        },
        {
            "title": CHUYEN_MUC,
            "icon": "tags",
            "summary": "4 nhóm chủ đề, đăng bài gì vào đâu",
            "content": f"""<h2>Các chuyên mục trên diễn đàn</h2>
<p>Chuyên mục xếp theo 4 nhóm chủ đề. Chọn đúng chỗ để người quan tâm dễ thấy bài của bạn:</p>
<h3>Thông báo &amp; Chính sách</h3>
<ul>
<li><strong>Thông báo công ty</strong> — thông báo chính thức từ Ban lãnh đạo, HR và các phòng ban.</li>
<li><strong>Nội quy &amp; chính sách</strong> — nội quy, quy định, chính sách và quy trình áp dụng toàn tập đoàn.</li>
<li><strong>Khen thưởng &amp; vinh danh</strong> — vinh danh cá nhân, tập thể xuất sắc; thông báo khen thưởng.</li>
</ul>
<h3>Công việc</h3>
<ul>
<li><strong>Trao đổi nghiệp vụ</strong> — bàn việc chung giữa các phòng ban: thu mua, kho, tài chính, sản xuất.</li>
<li><strong>Hỏi đáp nghiệp vụ</strong> — thắc mắc về quy trình, chứng từ, phân quyền.</li>
<li><strong>Góp ý &amp; sáng kiến</strong> — đề xuất cải tiến quy trình, công cụ làm việc, sản phẩm.</li>
<li><strong>Mẹo dùng hệ thống ERP</strong> — hướng dẫn, thủ thuật khi dùng ERP nội bộ.</li>
</ul>
<h3>Văn hóa &amp; Sự kiện</h3>
<ul>
<li><strong>Sự kiện &amp; hoạt động</strong> — sự kiện công ty, team building, hình ảnh hoạt động.</li>
<li><strong>Chúc mừng &amp; sinh nhật</strong> — sinh nhật, tin vui, thành viên mới, cột mốc của đồng nghiệp.</li>
<li><strong>Thể thao &amp; giải trí</strong> — kèo thể thao, game, giải trí sau giờ làm.</li>
</ul>
<h3>Đời sống</h3>
<ul>
<li><strong>Góc chia sẻ</strong> — chuyện trò tự do: cà phê, du lịch, ảnh đẹp, chuyện đời thường.</li>
<li><strong>Mua bán trao đổi</strong> — chợ nội bộ: mua bán, cho tặng, trao đổi đồ dùng.</li>
</ul>
<p>Bộ chuyên mục do quản trị viên quản lý — muốn mở thêm chuyên mục, đề xuất với quản trị viên diễn đàn (xem {ref(QUAN_TRI, "bài quản trị")}). Cách đăng bài vào chuyên mục xem ở {ref(DANG_BAI, "Đăng bài viết mới")}.</p>""",
        },
        {
            "title": TUONG_TAC,
            "icon": "bell",
            "summary": "6 loại cảm xúc, bình luận hai tầng, nhắc tên bằng @, chuông thông báo",
            "content": """<h2>Thả cảm xúc, bình luận và nhắc tên</h2>
<h3>Thả cảm xúc</h3>
<ul>
<li>Bấm nút <strong>Thích</strong> dưới bài để thích nhanh. <strong>Di chuột lên nút</strong> (hoặc giữ nút trên điện thoại) để mở khay 6 cảm xúc: <strong>Thích · Yêu thích · Haha · Tuyệt vời · Buồn · Phẫn nộ</strong>.</li>
<li>Bấm lại cảm xúc đang chọn để bỏ; chọn cảm xúc khác để đổi.</li>
<li>Bấm vào <strong>số đếm cảm xúc</strong> để xem ai đã thả gì — lọc được theo từng loại.</li>
</ul>
<h3>Bình luận</h3>
<ul>
<li>Bình luận có <strong>hai tầng</strong>: bình luận và phản hồi bên dưới, hiển thị dạng bong bóng.</li>
<li>Đính kèm được <strong>ảnh</strong> vào bình luận; bấm ảnh trong bình luận cũng phóng to được.</li>
<li>Gõ <strong>@</strong> rồi chọn tên để <strong>nhắc đồng nghiệp</strong> — người được nhắc nhận thông báo riêng.</li>
<li>Bài nhiều bình luận có nút «Xem các bình luận trước» để tải dần.</li>
</ul>
<h3>Thông báo chuông</h3>
<ul>
<li>Bài của bạn có bình luận mới: bạn nhận <strong>một chuông</strong>; người từng bình luận trong bài cũng được báo.</li>
<li>Bạn <strong>được nhắc tên</strong>: nhận chuông «Bạn được nhắc tên» riêng.</li>
<li>Thả cảm xúc <strong>không</strong> sinh chuông — thoải mái thả không sợ làm phiền.</li>
<li>Bấm chuông là nhảy thẳng tới đúng bài viết.</li>
</ul>""",
        },
        {
            "title": TIM_KIEM,
            "icon": "book-open",
            "summary": "Gợi ý nhanh khi gõ, trang tìm đầy đủ và bộ lọc nâng cao",
            "content": """<h2>Tìm kiếm bài viết</h2>
<h3>Gợi ý nhanh từ ô tìm</h3>
<ul>
<li>Gõ từ <strong>2 ký tự</strong> vào ô tìm trên thanh đầu trang — hệ thống sổ ngay <strong>5 bài khớp nhất</strong> (theo tiêu đề và nội dung), kèm người đăng và chuyên mục.</li>
<li>Bấm thẳng vào gợi ý để mở bài; hoặc dùng phím mũi tên lên/xuống rồi Enter.</li>
</ul>
<h3>Trang tìm kiếm đầy đủ</h3>
<ul>
<li>Bấm <strong>«Xem tất cả N kết quả»</strong> dưới khay gợi ý, hoặc nhấn Enter khi chưa trỏ vào gợi ý nào, để mở trang tìm kiếm với toàn bộ kết quả.</li>
<li>Bấm <strong>«Bộ lọc nâng cao»</strong> để lọc thêm theo <strong>người đăng, công ty, phòng ban</strong>.</li>
</ul>
<h3>Lưu ý về phạm vi</h3>
<p>Kết quả tìm kiếm tôn trọng đối tượng xem của từng bài: bài giới hạn trong phòng ban hoặc công ty khác sẽ không hiện với bạn.</p>""",
        },
        {
            "title": TRANG_TOI,
            "icon": "clipboard-list",
            "summary": "Xem bài của mình, xóa bài, bài đổi ảnh đại diện",
            "content": """<h2>Trang của tôi và quản lý bài đã đăng</h2>
<h3>Trang của tôi</h3>
<ul>
<li>Tab <strong>Trang của tôi</strong> liệt kê toàn bộ bài bạn đã đăng, mới nhất trên cùng.</li>
<li>Bấm <strong>tên hoặc ảnh đại diện</strong> của đồng nghiệp ở bất kỳ đâu để xem trang cá nhân và các bài của người đó (trong phạm vi bạn được xem).</li>
</ul>
<h3>Xóa bài của mình</h3>
<ul>
<li>Mở menu <strong>ba chấm</strong> góc phải bài viết, chọn <strong>Xóa bài</strong> và xác nhận.</li>
<li>Xóa bài sẽ xóa kèm toàn bộ bình luận, cảm xúc và tệp đính kèm — <strong>không hoàn tác được</strong>.</li>
<li>Hiện chưa có chức năng sửa bài — cần chỉnh nội dung thì xóa rồi đăng lại.</li>
</ul>
<h3>Bài đổi ảnh đại diện</h3>
<p>Khi bạn đổi ảnh đại diện (ở Trang cá nhân hoặc menu tài khoản), hệ thống hỏi <strong>«Đăng lên diễn đàn?»</strong> — đồng ý thì diễn đàn có một bài «đã cập nhật ảnh đại diện» để đồng nghiệp vào chúc mừng; chọn «Để sau» thì chỉ đổi ảnh, không đăng gì.</p>""",
        },
        {
            "title": QUAN_TRI,
            "icon": "shield-check",
            "summary": "Kiểm duyệt bài viết, quản lý chuyên mục, bài ghim và nhật ký",
            "content": """<h2>Dành cho Quản trị viên diễn đàn</h2>
<p>Người được gán vai trò <strong>quản trị diễn đàn</strong> thấy thêm tab <strong>Quản trị</strong> và các nút kiểm duyệt trên từng bài. Quản trị viên xem được mọi bài bất kể đối tượng xem.</p>
<h3>Kiểm duyệt bài viết</h3>
<ul>
<li>Mở menu <strong>ba chấm</strong> trên bài: <strong>Ẩn bài</strong> (chỉ tác giả và quản trị viên còn thấy, khôi phục được) · <strong>Gỡ bài</strong> (khuất hẳn với mọi người) · <strong>Khôi phục</strong> bài đang ẩn.</li>
<li>Ẩn và gỡ đều <strong>bắt buộc nhập lý do</strong>; tác giả tự động nhận thông báo kèm lý do — không có chuyện bài biến mất mà không ai hay.</li>
<li>Bài bị ẩn hiện băng rôn «đã bị quản trị viên ẩn» kèm lý do cho tác giả.</li>
</ul>
<h3>Tab Quản trị — ba mục</h3>
<ul>
<li><strong>Chuyên mục:</strong> thêm/sửa nhóm và chuyên mục, đặt mô tả, chọn biểu tượng, đổi thứ tự, ẩn chuyên mục không dùng nữa (bài cũ vẫn giữ). Có ô lọc nhanh theo tên.</li>
<li><strong>Bài ghim:</strong> danh sách bài đang ghim — bài ghim xuất hiện ở tab <strong>Thông báo</strong> và khung <strong>Nổi bật</strong>; bỏ ghim ngay tại đây. Ghim bài mới bằng menu ba chấm trên bài.</li>
<li><strong>Nhật ký kiểm duyệt:</strong> ai ẩn/gỡ/khôi phục bài nào, lúc nào, lý do gì — lọc được theo hành động và từ khóa.</li>
</ul>
<h3>Cấp quyền quản trị</h3>
<p>Vai trò quản trị diễn đàn do quản trị hệ thống gán trong màn Phân quyền của ERP — liên hệ bộ phận IT khi cần thêm hoặc thu hồi.</p>""",
        },
    ],
}


# --------------------------------------------------------------------------- #
#  DỰNG CÂY (khuôn y hệt seed_help_van_thu.py)
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
    #  Xóa RAW theo thứ tự sâu-trước: FK tự tham chiếu parent_id KHÔNG cascade.
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
        print(f"Đã dựng cây Diễn đàn: {total} bài (gốc id={root_id}, sort_order={next_order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
