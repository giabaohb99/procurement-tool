# -*- coding: utf-8 -*-
"""Seed bài Trung tâm trợ giúp: LẬP BỘ TÀI KHOẢN THU MUA BẰNG TRỢ LÝ AI (bao-CR-441).

Bài này là BÀI CON của bài «Trợ lý AI» (nằm trong nhóm «Các chức năng khác»). Không dựng
thẻ phân hệ mới ngoài trang chủ, không đụng nội dung bài cha.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_tro_ly_ai_lap_bo_tai_khoan.py

Idempotent: đã có bài cùng tiêu đề dưới cùng bài cha thì xóa bài đó (kèm con, nếu có)
rồi chèn lại. Không thấy bài cha «Trợ lý AI» thì DỪNG, không tự tạo bài gốc.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md`
mục 3 (phần «Làm nhanh Bước 3 và 4 bằng Trợ lý AI») và với tool T49
`propose_account_setup` (`app/modules/assistant/tools/account_setup_tool.py`, bao-CR-435).
Đổi hành vi tool thì sửa cả ba chỗ.
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
ARTICLE_TITLE = "Lập bộ tài khoản thu mua bằng Trợ lý AI"


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


SUMMARY = "HD nhờ Trợ lý AI gán vai trò và loại trừ phòng ban cho một tài khoản: đọc thẻ đề xuất rồi bấm Xác nhận"

CONTENT = f"""<h2>I. Giới thiệu</h2>
<p>Lập một tài khoản thu mua có bốn bước: tạo hồ sơ nhân sự, tạo tài khoản đăng nhập, gán vai trò, khai phạm vi. Hai bước đầu vẫn làm tay. <strong>Hai bước sau</strong> (gán vai trò + khai ô <em>Loại trừ phòng ban</em>) có thể nhờ {ref(PARENT_TITLE, "Trợ lý AI")} làm thay: bạn gõ một câu, trợ lý dò tình trạng hiện có rồi hiện <strong>thẻ đề xuất</strong>; hệ thống chỉ ghi khi <strong>chính bạn bấm Xác nhận</strong>.</p>
<p>Dùng bài này khi lập bộ tài khoản cho <strong>phòng tự mua hàng</strong> (ví dụ nhà máy Dego Organic) hoặc bộ <strong>Thu mua chung trừ phòng đó</strong>, và cả khi chỉ cần chỉnh vai trò của một người đã có tài khoản.</p>

<h2>II. Điều kiện trước khi hỏi</h2>
<table><thead><tr><th>Cần có</th><th>Kiểm ở đâu</th></tr></thead><tbody>
<tr><td>Người đó <strong>đã có hồ sơ nhân sự</strong> đúng phòng ban</td><td>Menu <strong>Nhân sự › Nhân sự</strong> — xem bài {ref("Nhân sự", "Nhân sự")}</td></tr>
<tr><td>Người đó <strong>đã có tài khoản đăng nhập</strong></td><td>Mở hồ sơ, tab <strong>Tài khoản</strong>. Chưa có thì bấm <strong>Tạo tài khoản đăng nhập</strong> và đặt mật khẩu bằng tay — trợ lý không làm bước này</td></tr>
<tr><td>Bạn có quyền <strong>sửa Người dùng</strong>, <strong>đọc Vai trò</strong> và <strong>đọc Nhân sự</strong></td><td>Tài khoản <em>Quản trị hệ thống</em> là đủ. Thiếu quyền nào trợ lý nói rõ thiếu quyền đó</td></tr>
<tr><td>Vai trò cần gán <strong>có sẵn</strong> trong danh sách vai trò</td><td><strong>Quản trị › Phân quyền tài khoản › Vai trò &amp; quyền</strong> — xem bài {ref("Vai trò", "Vai trò")}</td></tr>
</tbody></table>
<p>⚠️ Không lập cho <strong>chính tài khoản đang đăng nhập</strong>: đây là chốt hai người của phân quyền, trợ lý sẽ từ chối y như màn Phân quyền. Nhờ một quản trị khác.</p>

<h2>III. Các bước thao tác</h2>
<h3>Bước 1 — Mở trợ lý</h3>
<ul>
<li>Bấm <strong>bong bóng trợ lý AI</strong> ở góc dưới bên phải, hoặc chọn phân hệ <strong>Trợ lý AI</strong> từ màn chọn phân hệ.</li>
</ul>

<h3>Bước 2 — Gõ yêu cầu</h3>
<p>Nói rõ <strong>ai</strong> (tên, hoặc tốt nhất là <strong>mã nhân viên</strong>), <strong>vai trò nào</strong> và <strong>loại trừ phòng nào</strong> (nếu có).</p>
<table><thead><tr><th>Muốn gì</th><th>Gõ ví dụ</th></tr></thead><tbody>
<tr><td>Bộ <strong>Thu mua chung trừ nhà máy</strong></td><td>"Lập bộ tài khoản nhân viên thu mua cho Nguyễn Văn A, loại trừ phòng Dego Organic"</td></tr>
<tr><td>Bộ <strong>Nhà máy</strong> (phòng tự mua)</td><td>"Gán vai trò Quản lý thu mua phòng cho NM_MUA" — không cần loại trừ gì, giới hạn nằm sẵn trong bậc của vai trò</td></tr>
<tr><td>Chỉ giữ đúng một vai trò, bỏ vai trò thừa</td><td>"Cho Trần Thị B chỉ còn vai trò Nhân viên thu mua"</td></tr>
<tr><td>Thêm phòng loại trừ cho người đã có bộ</td><td>"Thêm loại trừ phòng Nhà máy Cần Thơ cho các vai trò thu mua của TM_QL"</td></tr>
<tr><td>Gỡ ô <em>Chỉ trong công ty</em> đang khai</td><td>"... và gỡ luôn Chỉ trong công ty"</td></tr>
</tbody></table>
<p>Trợ lý chỉ nhận <strong>sáu vai trò trong bộ mẫu</strong> (mục V). Cần vai trò khác thì gán tay ở màn Phân quyền.</p>

<h3>Bước 3 — Đọc thẻ đề xuất</h3>
<p>Trợ lý dò trước: hồ sơ có không, tài khoản có chưa, đang giữ vai trò gì, phạm vi đang khai gì. Rồi hiện thẻ gồm:</p>
<ul>
<li><strong>Từng dòng thêm / bỏ / không đổi</strong> cho vai trò và cho phạm vi — chỉ dòng <em>thêm</em> và <em>bỏ</em> mới làm thay đổi hệ thống.</li>
<li><strong>Cảnh báo vàng</strong> (nếu có): ví dụ vai trò thu mua đang khai <em>Chỉ trong công ty</em> — bộ thu mua thường không nên nhốt theo pháp nhân. Trợ lý <strong>không tự gỡ</strong>; muốn gỡ thì nói rõ (Bước 2). Hoặc tài khoản đang <strong>khóa</strong>: gán xong vẫn chưa đăng nhập được, mở khóa ở màn Người dùng.</li>
<li>Nút <strong>Xác nhận</strong> và <strong>Bỏ qua</strong>. Thẻ báo <em>"đã đúng bộ"</em> (mọi dòng không đổi) thì chỉ có nút Đóng, không có gì để ghi.</li>
</ul>
<p>⚠️ Thẻ có hạn <strong>15 phút</strong>. Quá hạn thì hỏi lại trợ lý để có thẻ mới; đừng tưởng bấm Xác nhận là đã ghi.</p>

<h3>Bước 4 — Xác nhận</h3>
<ul>
<li>Đúng ý thì bấm <strong>Xác nhận</strong>. Tới lúc này hệ thống mới gán vai trò và ghi phạm vi, đi qua đúng hai đường ghi của màn Phân quyền và <strong>kiểm lại quyền của bạn một lần nữa</strong> ngay lúc bấm.</li>
<li>Muốn chắc, mở <strong>Quản trị › Phân quyền tài khoản › Người dùng</strong>, tìm theo mã nhân viên: thẻ <em>Vai trò &amp; phạm vi</em> phải hiện đúng như thẻ đề xuất.</li>
<li>Hỏi lại cùng câu thì mọi dòng ra <em>không đổi</em> — đó là cách kiểm nhanh nhất.</li>
</ul>

<h2>IV. Trợ lý KHÔNG làm gì</h2>
<table><thead><tr><th>Việc</th><th>Làm ở đâu thay thế</th></tr></thead><tbody>
<tr><td>Tạo hồ sơ nhân sự</td><td><strong>Nhân sự › Nhân sự › Thêm mới</strong> (Bước 1 của hướng dẫn bộ tài khoản)</td></tr>
<tr><td>Tạo tài khoản đăng nhập, đặt hay đổi mật khẩu</td><td>Hồ sơ nhân sự, tab <strong>Tài khoản</strong> (Bước 2). Người chưa có tài khoản thì trợ lý chỉ đường sang đó và dừng</td></tr>
<tr><td>Tạo vai trò mới, tick thêm quyền vào vai trò</td><td><strong>Quản trị › Phân quyền tài khoản › Vai trò &amp; quyền</strong></td></tr>
<tr><td>Khai <em>Xem thêm phòng ban</em>, <em>Chỉ trong công ty</em> hay các ô ngoại lệ khác</td><td>Nút <strong>Phạm vi</strong> cạnh vai trò ở màn Người dùng. Trợ lý chỉ <strong>thêm loại trừ</strong> và, khi được bảo, <strong>gỡ Chỉ trong công ty</strong></td></tr>
<tr><td>Sửa quyền của chính bạn, hay của người ngoài phạm vi bạn được sửa</td><td>Nhờ quản trị khác</td></tr>
</tbody></table>

<h2>V. Sáu vai trò trong bộ mẫu</h2>
<table><thead><tr><th>Vai trò</th><th>Dùng cho</th></tr></thead><tbody>
<tr><td><strong>Nhân sự</strong></td><td>người chỉ lập Yêu cầu mua hàng cho phòng mình; tài khoản mới tự có vai trò này</td></tr>
<tr><td><strong>Trưởng phòng (duyệt PYC)</strong></td><td>duyệt phiếu của phòng mình</td></tr>
<tr><td><strong>Nhân viên thu mua</strong></td><td>xử lý các dòng được giao</td></tr>
<tr><td><strong>Quản lý thu mua</strong></td><td>Thu mua chung: thấy và điều phối mọi phiếu đã duyệt, thường kèm <em>Loại trừ phòng ban</em> = các phòng tự mua</td></tr>
<tr><td><strong>Quản lý thu mua phòng</strong></td><td>phòng tự mua hàng: chỉ phiếu đã duyệt của phòng mình và phiếu phòng khác nhờ phòng mình xử lý</td></tr>
<tr><td><strong>Admin thu mua</strong></td><td>như Quản lý thu mua nhưng không duyệt</td></tr>
</tbody></table>
<p>Bộ Nhà máy <strong>không khai</strong> <em>Chỉ trong công ty</em>: nhà máy mua cho nhiều pháp nhân, pháp nhân trên hồ sơ nhân sự không thu hẹp phiếu được thấy.</p>

<h2>VI. Trợ lý trả lời thế này thì làm gì</h2>
<table><thead><tr><th>Trợ lý nói</th><th>Bạn làm</th></tr></thead><tbody>
<tr><td>"... chưa có tài khoản đăng nhập"</td><td>Làm Bước 2 của hướng dẫn bộ tài khoản (tab Tài khoản trong hồ sơ), rồi hỏi lại</td></tr>
<tr><td>"Nhiều hồ sơ khớp"</td><td>Nói lại bằng <strong>mã nhân viên</strong> thay vì tên</td></tr>
<tr><td>Không tìm thấy hồ sơ</td><td>Kiểm hồ sơ có thật và nằm trong phạm vi nhân sự bạn được xem; ngoài phạm vi thì với trợ lý cũng như không có</td></tr>
<tr><td>Không tìm thấy phòng cần loại trừ</td><td>Gõ đúng tên phòng trong danh mục <strong>Nhân sự › Phòng ban</strong>; hai phòng trùng tên ở hai công ty sẽ bị trừ cả hai</td></tr>
<tr><td>"Không tự đổi quyền của chính mình được"</td><td>Nhờ quản trị khác</td></tr>
<tr><td>Thẻ báo <em>"đã đúng bộ"</em></td><td>Không cần làm gì, tài khoản đã đúng như yêu cầu</td></tr>
</tbody></table>

<h2>VII. Kiểm tra sau khi làm</h2>
<ul>
<li>Người vừa được gán <strong>phải đăng xuất rồi đăng nhập lại</strong>; máy chủ còn nhớ bản quyền cũ tối đa một phút.</li>
<li>Kiểm bằng cửa sổ ẩn danh: người của bộ Thu mua chung <strong>không</strong> thấy phiếu của phòng bị loại trừ (gõ thẳng id lên đường dẫn phải ra <em>Không tìm thấy</em>), nhưng vẫn thấy phiếu phòng đó <em>nhờ</em> Thu mua chung xử lý.</li>
<li>Mọi lần Xác nhận đều có dấu vết ở lịch sử thao tác của tài khoản, giống như bấm tay trên màn Phân quyền.</li>
</ul>
<p>💡 <strong>Mở thêm một phòng tự mua khác?</strong> Nhớ nhờ trợ lý <strong>thêm phòng mới vào loại trừ</strong> cho <em>từng</em> tài khoản Thu mua chung. Quên bước này thì Thu mua chung vẫn thấy phiếu phòng mới mà không ai báo lỗi.</p>

<h2>VIII. Điều hướng</h2>
<ul>
<li><strong>Thuộc thư mục:</strong> Các chức năng khác › {ref(PARENT_TITLE, "Trợ lý AI")}</li>
<li><strong>Bài liên quan:</strong> {ref("Lập bộ tài khoản phòng tự mua hàng", "Lập bộ tài khoản phòng tự mua hàng")} (bốn bước làm tay) · {ref("Vai trò", "Vai trò")} · {ref("Nhân sự", "Nhân sự")}</li>
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
