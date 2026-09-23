# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp: TRA CỨU GIÁ HẢI QUAN (bao-CR-470, A-04 của doc/erp/hai-quan/01).

Dựng MỘT bài dưới nhóm có sẵn «Dành cho Nhân viên Mua hàng» (không đẻ nhóm mới):
«Tra cứu giá hải quan» — kể đủ: dữ liệu là gì (dòng hàng, không phải tờ khai), năm thẻ của
màn hình, bốn luật đọc biểu đồ, cảnh báo pháp lý, nạp dữ liệu và hoàn tác, hỏi trợ lý AI.

Chạy trong container api (LOCAL / dev — KHÔNG chạy ở prod khi đại ca chưa bảo):
    docker compose exec -T api python scripts/seed_help_customs_prices.py

Idempotent: đã có bài cùng tiêu đề dưới đúng nhóm thì xóa bài đó (kèm bài con, nếu có) rồi
chèn lại ở nguyên chỗ cũ. Thiếu nhóm cha thì DỪNG, không tự tạo bài gốc.

Nội dung phải KHỚP với doc/erp/hai-quan/04-giao-dien.md và màn /customs-prices. Không nêu
tên doanh nghiệp có trong dữ liệu.
"""
import sys

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

STAFF_PARENT_TITLE = "Dành cho Nhân viên Mua hàng"
ARTICLE_TITLE = "Tra cứu giá hải quan"

SUMMARY = (
    "Xem giá và lượng nhập khẩu của thị trường theo tờ khai hải quan: lọc theo tên hàng, hoạt "
    "chất, mã HS; biểu đồ giá theo tháng, quý, năm; ai đang nhập; cảnh báo pháp lý và biểu thuế"
)

CONTENT = """<h2>I. Màn này dùng để làm gì</h2>
<p>Trước khi mua một mặt hàng, người thu mua cần biết <strong>thị trường đang nhập mặt hàng đó về Việt Nam với giá bao nhiêu, lượng bao nhiêu, và tháng nào giá tốt</strong>. Màn <strong>Tra cứu giá hải quan</strong> (menu <em>Mua hàng</em>) trả lời câu đó bằng dữ liệu tờ khai hải quan nhập khẩu do người được giao nạp vào từ tệp Excel.</p>
<p>Màn này <strong>độc lập</strong>: không nối với danh mục vật tư, tồn kho hay lịch sử mua hàng của công ty. Tìm theo chữ, không theo mã sản phẩm nội bộ.</p>
<p>Cần quyền <strong>Tra cứu giá hải quan</strong> (xem). Nạp dữ liệu, hoàn tác, xuất Excel là các quyền riêng — không có quyền thì không thấy nút.</p>

<h2>II. Một dòng là gì</h2>
<p>Mỗi dòng trên màn là <strong>một dòng hàng</strong> trên tờ khai, không phải một tờ khai. Một tờ khai có thể gồm nhiều dòng hàng, và tệp dữ liệu không có số tờ khai, nên mọi con số trên màn đều đếm theo <strong>dòng hàng</strong>.</p>
<p>Bảng hiện <strong>đủ 32 cột đúng thứ tự và tiêu đề như tệp Excel</strong> hải quan, cả <em>Đơn giá khai báo</em> lẫn <em>Đơn giá điều chỉnh</em>. Biểu đồ và các con số thống kê dùng giá điều chỉnh nếu có, không thì giá khai báo (đổi được ở nút <em>Giá</em> trên thẻ Biểu đồ). Cột nào không cần thì ẩn ở nút <strong>Cột</strong>.</p>
<p>Hai cột cuối <strong>Hoạt chất (suy ra)</strong> và <strong>Hàm lượng / dạng (suy ra)</strong> do hệ thống <strong>suy ra</strong> từ tên hàng (tên hàng là chữ tự do). Khoảng một nửa số dòng nhận ra được hoạt chất; phần còn lại phần lớn là hóa chất khử trùng, tẩy rửa. Dòng không nhận ra vẫn tìm được bằng tên hàng.</p>

<h2>III. Đầu trang: dữ liệu đang phủ tới đâu</h2>
<p>Dải ô tháng ngay dưới tiêu đề cho biết tháng nào đã có dữ liệu (xanh), tháng nào <strong>trống</strong> (đỏ) và tháng nào chưa tới (mờ). Một tháng đã qua mà trống gần như luôn là do <strong>quên nạp một tệp</strong> — báo cho người phụ trách nạp dữ liệu.</p>

<h2>IV. Tìm và lọc</h2>
<ul>
<li><strong>Tên hàng / hoạt chất</strong>: gõ rồi Enter, ví dụ <em>ATRAZINE</em>, <em>mancozeb</em>. Khớp cả tên hàng lẫn hoạt chất đã suy ra.</li>
<li><strong>Mã HS · Xuất xứ · Đơn vị tính · Hàm lượng / dạng · Từ tháng · Đến tháng</strong>: chọn xong bấm <em>Tìm</em>.</li>
<li>Muốn xem riêng một doanh nghiệp: sang thẻ <em>Nhà nhập khẩu</em>, bấm vào dòng của doanh nghiệp đó. Thẻ nhỏ «Doanh nghiệp: ...» hiện dưới thanh lọc, bấm dấu x để bỏ.</li>
</ul>
<p>Bảng trống có hai câu khác nhau: «Chưa có dữ liệu hải quan» nghĩa là chưa ai nạp gì; «Không có dòng hàng nào khớp bộ lọc» nghĩa là bộ lọc quá hẹp hoặc gõ sai chữ.</p>

<h2>V. Năm thẻ</h2>
<table>
<thead><tr><th>Thẻ</th><th>Cho biết gì</th></tr></thead>
<tbody>
<tr><td><strong>Danh sách</strong></td><td>Các dòng hàng khớp bộ lọc, mới nhất lên đầu. Bấm một dòng để xem đủ 32 trường. Nút <em>Xuất Excel</em> xuất đúng các dòng đang lọc (tối đa 50.000 dòng).</td></tr>
<tr><td><strong>Biểu đồ</strong></td><td>Giá thấp nhất, bình quân, cao nhất và lượng nhập theo <strong>tháng / quý / năm</strong>. Chỉ hiện khi đã nhập từ khóa hoặc chọn mã HS.</td></tr>
<tr><td><strong>Nhà nhập khẩu</strong></td><td>20 doanh nghiệp nhập nhiều nhất mặt hàng đang lọc: số dòng, tổng lượng, thị phần, giá bình quân, lần nhập gần nhất. Gộp theo mã số thuế.</td></tr>
<tr><td><strong>So sánh</strong></td><td>Đặt 2–5 mặt hàng hoặc hoạt chất cạnh nhau trên cùng một biểu đồ, cùng một đơn vị tính.</td></tr>
<tr><td><strong>Pháp lý &amp; thuế</strong></td><td>Tra hóa chất trong các danh mục pháp lý theo tên, số CAS hoặc công thức (ví dụ H2SO4); tra thuế suất nhập khẩu, VAT và thuế theo hiệp định thương mại theo mã HS.</td></tr>
</tbody>
</table>

<h2>VI. Đọc biểu đồ cho đúng — bốn điều</h2>
<ol>
<li><strong>Mỗi lần chỉ vẽ một đơn vị tính.</strong> Cùng một hoạt chất có dòng tính bằng kg, có dòng tính bằng lít — cộng chung là ra con số vô nghĩa. Hàng nút đơn vị phía trên biểu đồ cho chọn đơn vị, mặc định là đơn vị nhiều dòng nhất.</li>
<li><strong>Kỳ không có dòng nào thì để trống</strong>, đường giá đứt ở đó. Trống không có nghĩa là giá bằng 0.</li>
<li><strong>Kỳ có dưới 5 dòng vẽ điểm rỗng</strong> và không bao giờ được chọn làm «kỳ giá tốt nhất» (điểm xanh lá). Một tháng trông rẻ nhất mà chỉ dựa trên 3 dòng thì chưa đủ để tin.</li>
<li><strong>Dải tô nhạt là khoảng thấp – cao.</strong> Dải rộng thường do cùng một từ khóa đang trộn thuốc kỹ thuật với thành phẩm. Lọc thêm <em>Hàm lượng / dạng</em> (ví dụ 97%) để tách ra.</li>
</ol>
<p>Dòng chữ vàng trên biểu đồ nói biểu đồ đang dựa trên bao nhiêu dòng, bao nhiêu tháng, bao nhiêu năm. Khi mới có <strong>một năm</strong> dữ liệu, biểu đồ chỉ cho thấy xu hướng trong năm đó, <strong>chưa đủ để kết luận theo mùa vụ</strong>.</p>

<h2>VII. Cảnh báo pháp lý</h2>
<p>Gõ từ khóa trùng một hóa chất trong danh sách <strong>hoạt chất cấm</strong>, danh sách <strong>có ngưỡng khối lượng</strong> hoặc danh sách <strong>phải công bố theo lô</strong> thì một dải cảnh báo đỏ hiện ngay dưới thanh lọc, nói rõ văn bản và việc cần lưu ý. Đây là tra cứu tham khảo; trước khi quyết định vẫn phải đối chiếu văn bản gốc.</p>
<p>Các danh sách đó nằm ở <em>Danh mục → Hóa chất theo văn bản</em> (quyền riêng). Khi văn bản thay đổi, người có quyền sửa trực tiếp ở đó.</p>

<h2>VIII. Nạp dữ liệu (người có quyền nạp)</h2>
<ol>
<li>Bấm <strong>Nạp dữ liệu</strong>, chọn một hoặc nhiều tệp <em>.xls / .xlsx</em> kết xuất từ hệ thống hải quan (mẫu GTT02, đủ 32 cột), bấm <strong>Chạy thử</strong>.</li>
<li>Xem bảng chạy thử: số dòng, khoảng ngày, số ngày đã tự sửa, và <strong>số dòng cũ sẽ bị thay</strong>. Lúc này chưa có gì được ghi.</li>
<li>Bấm <strong>Áp dụng</strong>. Hệ thống báo khi ghi xong.</li>
</ol>
<ul>
<li>Tệp hải quan không có mã dòng để đối chiếu, nên nạp một tệp có khoảng ngày trùng dữ liệu đã có thì <strong>các dòng cũ trong khoảng ngày đó được thay</strong> bằng tệp mới — nạp lại không làm nhân đôi.</li>
<li>Cột ngày đăng ký trong tệp xuất đôi khi bị Excel đảo ngày và tháng; hệ thống tự nhận ra và đọc lại. Ô ngày có dấu lịch màu cam là dòng đã được sửa.</li>
<li><strong>Lịch sử nạp</strong> liệt kê mọi lần nạp, ai nạp, lúc nào, kèm nhật ký cảnh báo. Lần nạp <strong>chưa thay dòng cũ</strong> thì hoàn tác được; lần nạp đã thay dòng cũ thì không — muốn sửa thì nạp lại tệp đúng.</li>
</ul>

<h2>IX. Hỏi trợ lý AI</h2>
<p>Trợ lý AI (cả trên web lẫn bot Telegram) đọc được cùng dữ liệu này nếu người hỏi có quyền xem. Có thể hỏi: <em>«Giá atrazine nhập về theo tháng bao nhiêu?»</em>, <em>«Nên mua mancozeb vào tháng nào?»</em>. Trợ lý luôn nói kèm <strong>độ tin cậy</strong> và số dòng dữ liệu, chỉ gợi ý tháng có đủ dữ liệu, và nhắc cảnh báo pháp lý nếu có. Câu trả lời để tham khảo, không thay cho quyết định mua.</p>

<h2>X. Câu hỏi thường gặp</h2>
<p><strong>Thẻ Biểu đồ chỉ hiện một câu nhắc, không có hình?</strong> Chưa nhập từ khóa hoặc mã HS. Biểu đồ của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng nên không vẽ.</p>
<p><strong>Tổng lượng trên biểu đồ ít hơn ở Danh sách?</strong> Biểu đồ chỉ tính đơn vị đang chọn; bấm sang đơn vị khác để xem phần còn lại.</p>
<p><strong>Doanh nghiệp tôi tìm có hai cách viết tên?</strong> Hệ thống gộp doanh nghiệp theo mã số thuế, nên hai cách viết vẫn là một doanh nghiệp ở thẻ Nhà nhập khẩu.</p>
"""

ARTICLES = [
    (STAFF_PARENT_TITLE, ARTICLE_TITLE, SUMMARY, CONTENT, 7),
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
