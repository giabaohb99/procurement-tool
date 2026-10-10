# -*- coding: utf-8 -*-
"""Seed bài Trung tâm trợ giúp: TẠO, SỬA, XÓA PHIẾU VÀ XEM QUYỀN BẰNG TRỢ LÝ AI (ai-CR-159).

Bài CON của bài «Trợ lý AI» (nhóm «Các chức năng khác»), cạnh bài «Lập bộ tài khoản thu mua bằng Trợ lý AI». Không
đụng nội dung bài cha.

Chạy trong container api (pipe stdin, không cần rebuild):
    docker compose exec -T api python - < backend/scripts/seed_help_tro_ly_ai_phieu_va_quyen.py

Idempotent: đã có bài cùng tiêu đề dưới cùng bài cha thì xóa bài đó (kèm con) rồi chèn lại, giữ sort_order. Không
thấy bài cha thì DỪNG.

Nội dung phải KHỚP mã: `assistant/tools/update_tool.py` (sửa / xóa, ai-CR-151..153), `agent_hub/draft_create.py` +
`service.py` (phiếu nháp, ai-CR-142/143/156), `agent_hub/user_guide.py` (câu lệnh + quyền của tôi, ai-CR-157). Đổi
hành vi ở đó thì sửa bài này rồi chạy lại trên từng môi trường.
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
ARTICLE_TITLE = "Tạo, sửa, xóa phiếu và xem quyền bằng Trợ lý AI"


# --------------------------------------------------------------------------- #
#  LIÊN KẾT NỘI BỘ — slug sinh y hệt slugify() của help-center (help-slug.tsx).
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


SUMMARY = ("HD nhờ Trợ lý AI (web và Telegram) soạn phiếu nháp, dùng lại phiếu nháp cũ, sửa và xóa phiếu của mình "
           "qua thẻ xác nhận, và xem tài khoản dùng được chức năng nào")

CONTENT = f"""<h2>I. Giới thiệu</h2>
<p>{ref(PARENT_TITLE, "Trợ lý AI")} không chỉ trả lời câu hỏi mà còn làm giúp vài việc với phiếu của chính bạn: soạn phiếu nháp, sửa phiếu còn ở bước Nháp, xóa phiếu nháp không dùng nữa. Mọi việc có ghi dữ liệu đều đi qua <strong>một thẻ để bạn xem trước</strong>; hệ thống chỉ ghi khi <strong>chính bạn xác nhận</strong>, và ghi bằng đúng chức năng của màn hình nên quyền, nhật ký và các luật kiểm tra giữ nguyên như khi bạn làm tay.</p>
<p>Trợ lý dùng được ở hai nơi:</p>
<table><thead><tr><th>Nơi dùng</th><th>Cách mở</th></tr></thead><tbody>
<tr><td><strong>Trên web ERP</strong></td><td>Bấm bong bóng trợ lý ở góc dưới bên phải, hoặc chọn phân hệ <strong>Trợ lý AI</strong></td></tr>
<tr><td><strong>Trên Telegram</strong> (bot Lạc Lạc)</td><td>Lấy mã ở <strong>Trang cá nhân › Telegram</strong>, rồi nhắn bot <code>/dangnhap mã</code> một lần. Từ đó bot làm việc dưới đúng tài khoản ERP của bạn</td></tr>
</tbody></table>

<h2>II. Xem mình dùng được chức năng nào</h2>
<ul>
<li>Trên Telegram, nhắn <code>quyền của tôi</code> (hoặc <em>tôi dùng được gì</em>). Bot trả một bảng theo đúng phân quyền ERP của tài khoản bạn: tạo phiếu nháp, sửa phiếu nháp, xóa phiếu nháp, tra cứu. Chức năng nào <strong>được</strong> thì kèm một câu nhắn mẫu, chạm vào là chép được; chức năng nào <em>chưa được cấp</em> thì ghi rõ.</li>
<li>Bot chỉ tra và sửa trong <strong>phạm vi dữ liệu</strong> quản trị đã đặt cho bạn (chỉ phiếu của mình, phòng mình…). Thiếu quyền nào thì nhờ quản trị cấp ở <strong>Quản trị › Phân quyền tài khoản</strong>.</li>
<li>Nhắn <code>hướng dẫn</code> để xem mọi câu lệnh theo nhóm; <code>hướng dẫn phiếu</code> và <code>hướng dẫn sửa phiếu</code> cho riêng hai phần trong bài này.</li>
<li>Khi bị chặn vì thiếu quyền, trợ lý nói rõ thiếu quyền làm gì và nhắc bạn xem <code>quyền của tôi</code>.</li>
</ul>

<h2>III. Soạn phiếu nháp</h2>
<h3>Bước 1 — Nói việc cần làm</h3>
<table><thead><tr><th>Muốn lập</th><th>Nhắn ví dụ</th></tr></thead><tbody>
<tr><td>Đơn nghỉ phép</td><td>"xin nghỉ thứ 6 cả ngày, lý do đưa con đi khám"</td></tr>
<tr><td>Yêu cầu mua hàng (YCMH)</td><td>"lên phiếu mua 10 ram giấy A4 cho kho Cần Thơ, cần trước 20/10, để in hợp đồng"</td></tr>
<tr><td>Yêu cầu báo giá (YCBG)</td><td>"lên phiếu báo giá máy in màu A3"</td></tr>
<tr><td>Việc ở phân hệ Dự án</td><td>"lên task gọi NCC Hòa Phát cho anh Được, hạn thứ 6"</td></tr>
</tbody></table>
<p>Thiếu ý quan trọng (lý do nghỉ, loại nghỉ, số lượng, ngày cần hàng, kho nhận…) thì trợ lý <strong>hỏi lại một lượt</strong> gồm mọi ý còn thiếu, không tự điền thay bạn. Điều trợ lý <em>tự hiểu</em> (ví dụ nghỉ cả ngày) được ghi riêng trên thẻ nháp dưới dòng <em>Em đang hiểu là</em> để bạn kiểm.</p>

<h3>Bước 2 — Lưu phiếu</h3>
<ul>
<li><strong>Trên Telegram</strong>: bot gửi thẻ <em>Bản nháp</em>. Nhắn <code>tạo</code> để lưu Nháp, <code>tạo và gửi duyệt</code> để lưu và gửi duyệt luôn, <code>thôi</code> để bỏ. Lưu xong bot gửi lại thông tin đọc từ hệ thống kèm link mở phiếu.</li>
<li><strong>Trên web</strong>: trợ lý soạn sẵn và hiện nút mở <strong>màn tạo phiếu đã điền sẵn</strong>; bạn xem lại rồi bấm Lưu trên màn đó.</li>
</ul>

<h3>Bước 3 — Dùng lại phiếu nháp cũ thay vì lập thêm</h3>
<ul>
<li><strong>Đơn nghỉ phép</strong>: đơn mới trùng ngày với một đơn Nháp bạn đang có thì bot <strong>sửa đè đơn nháp cũ</strong>, không lập đơn thứ hai.</li>
<li><strong>YCMH / YCBG</strong>: bạn đang có phiếu Nháp cùng loại thì thẻ nháp liệt kê các phiếu đó (tối đa 5) kèm hai lựa chọn:
<ul>
<li><code>thêm vào 1</code>: thêm các dòng mới vào phiếu nháp số 1. Dòng y hệt (cùng tên, số lượng, đơn vị) đã có thì bỏ qua; phần đầu phiếu giữ nguyên, chỉ điền ô đang trống.</li>
<li><code>ghi đè 1</code>: thay cả phần đầu phiếu lẫn dòng hàng của phiếu số 1 bằng bản mới, <strong>giữ mã phiếu cũ</strong>.</li>
</ul></li>
<li>Xem và dọn phiếu nháp: nhắn <code>đơn nháp của tôi</code> để xem danh sách có đánh số; <code>xóa đơn nháp 2 3</code> hay <code>xóa hết đơn nháp</code> rồi trả lời <code>đúng</code> để xóa, <code>thôi</code> để giữ.</li>
</ul>

<h2>IV. Sửa phiếu đã có</h2>
<h3>Sửa được những gì</h3>
<table><thead><tr><th>Loại phiếu</th><th>Sửa được</th><th>Khi phiếu ở trạng thái</th></tr></thead><tbody>
<tr><td>Đơn nghỉ phép</td><td>Từ ngày, đến ngày, loại nghỉ, lý do</td><td>Nháp hoặc Trả về chỉnh sửa</td></tr>
<tr><td>Yêu cầu mua hàng</td><td>Mục đích, ngày cần hàng, ghi chú; dòng hàng: thêm dòng, bỏ dòng, đổi số lượng</td><td>Nháp hoặc Bị trả lại</td></tr>
<tr><td>Yêu cầu báo giá</td><td>Mục đích, ghi chú; dòng hàng: thêm dòng, bỏ dòng, đổi số lượng</td><td>Nháp hoặc Bị trả lại</td></tr>
<tr><td>Yêu cầu thanh toán</td><td>Ba câu chữ trên bản in (Nội dung, Diễn giải, Nội dung chuyển khoản)</td><td>Nháp, Chờ duyệt hoặc Đã duyệt</td></tr>
</tbody></table>
<p>Trợ lý <strong>không</strong> sửa giá, nhà cung cấp, số tiền, trạng thái, hạn chi. Đơn nghỉ gồm nhiều loại nghỉ thì không đổi loại qua trợ lý (phải chia lại số ngày trên form). Mỗi lần sửa tối đa 20 thao tác dòng và phiếu phải còn ít nhất một dòng.</p>

<h3>Các bước</h3>
<ol>
<li>Nhắn rõ <strong>mã phiếu</strong> và thay đổi, ví dụ: "sửa lý do đơn NP011 thành đi khám nghĩa vụ vòng 1", "thêm 5 hộp kẹp giấy vào YCMH00012", "đổi số lượng dòng 2 của YCMH00012 thành 20". Chưa chắc dòng số mấy thì nhờ trợ lý đọc phiếu trước.</li>
<li>Trợ lý hiện <strong>thẻ đề xuất sửa</strong>: mỗi dòng ghi giá trị cũ gạch ngang và giá trị mới in đậm. Phiếu <strong>chưa</strong> bị sửa.</li>
<li>Bấm <strong>Xác nhận sửa</strong> (hoặc <strong>Không sửa</strong>). Lúc bấm, hệ thống kiểm lại từ đầu: còn quyền, phiếu còn trong phạm vi, còn ở trạng thái sửa được, rồi mới ghi.</li>
</ol>
<p><strong>Lưu ý:</strong> thẻ có hạn <strong>15 phút</strong> và <strong>chỉ dùng được một lần</strong>. Bấm lại thẻ cũ sau khi đã ghi, hoặc phiếu vừa bị người khác sửa xen giữa, hệ thống sẽ báo <em>soạn lại đề xuất mới</em> chứ không ghi trùng. Chỉ sửa lý do nghỉ thì số ngày nghỉ giữ nguyên.</p>

<h2>V. Xóa phiếu</h2>
<p>Trợ lý chỉ xóa khi đủ <strong>cả ba điều kiện</strong>:</p>
<ol>
<li>Phiếu do <strong>chính bạn lập</strong> (việc Dự án: do chính bạn tạo).</li>
<li>Phiếu còn <strong>Nháp hoặc Bị trả lại</strong> (đơn nghỉ: Nháp hoặc Trả về chỉnh sửa; việc Dự án: đang mở).</li>
<li>Tài khoản có <strong>quyền xóa</strong> loại phiếu đó và phiếu nằm trong phạm vi bạn được xóa.</li>
</ol>
<table><thead><tr><th>Loại</th><th>Trợ lý làm gì</th></tr></thead><tbody>
<tr><td>Yêu cầu mua hàng, đơn nghỉ phép, việc Dự án</td><td>Xóa như nút Xóa trên màn hình (việc Dự án vào thùng rác của dự án)</td></tr>
<tr><td>Yêu cầu báo giá</td><td>Xóa hẳn như nút Xóa trên màn hình</td></tr>
<tr><td>Đề nghị thanh toán, phiếu hỗ trợ</td><td><strong>Không xóa</strong> qua trợ lý; trợ lý gửi link để bạn tự mở</td></tr>
<tr><td>Phiếu đã gửi duyệt hoặc của người khác</td><td>Không xóa; trợ lý nói lý do và gửi link để bạn mở hoặc nhờ người có quyền</td></tr>
</tbody></table>
<p>Cách làm: nhắn "xóa phiếu YCMH00012", đọc thẻ <strong>Đề xuất XÓA</strong>, rồi bấm <strong>Xác nhận xóa</strong> hoặc <strong>Không xóa</strong>. Nếu bạn nói mơ hồ kiểu "bỏ" hay "hủy", trợ lý hỏi lại là xóa hẳn phiếu nháp hay hủy phiếu.</p>

<h2>VI. Trợ lý trả lời thế này thì làm gì</h2>
<table><thead><tr><th>Trợ lý nói</th><th>Bạn làm</th></tr></thead><tbody>
<tr><td>"Bạn không có quyền sửa / xóa …"</td><td>Nhắn <code>quyền của tôi</code> để xem, rồi nhờ quản trị cấp thêm</td></tr>
<tr><td>"Phiếu … đang ở trạng thái Chờ duyệt / Đã duyệt"</td><td>Phiếu đã vào luồng duyệt: nhờ người duyệt trả về, hoặc mở phiếu làm theo quy trình trên màn hình</td></tr>
<tr><td>"Không tìm thấy phiếu … trong phạm vi"</td><td>Kiểm lại mã phiếu; phiếu ngoài phạm vi dữ liệu của bạn thì với trợ lý cũng như không có</td></tr>
<tr><td>"Đề xuất đã hết hạn" hoặc "đã dùng rồi"</td><td>Nhắn lại yêu cầu để có thẻ mới</td></tr>
<tr><td>Hỏi lại nhiều ý trước khi soạn</td><td>Trả lời đủ trong một tin; ý nào muốn bỏ qua thì nói rõ "không cần"</td></tr>
</tbody></table>

<h2>VII. Điều hướng</h2>
<ul>
<li><strong>Thuộc thư mục:</strong> Các chức năng khác › {ref(PARENT_TITLE, "Trợ lý AI")}</li>
<li><strong>Bài liên quan:</strong> {ref("Lập bộ tài khoản thu mua bằng Trợ lý AI", "Lập bộ tài khoản thu mua bằng Trợ lý AI")}</li>
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
