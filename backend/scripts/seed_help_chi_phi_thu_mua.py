# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp: CHI PHÍ THU MUA trên đơn mua hàng (bao-CR-453).

Kho hướng dẫn đang chạy có bài về Đơn mua hàng, Công nợ và Báo cáo mua hàng nhưng chưa
bài nào nói về thẻ «Chi phí thu mua» — thứ vừa đổi từ «Chi phí lô hàng nhập khẩu» (chỉ đơn
nhập khẩu, hai cờ Dự kiến / Thực tế) sang ba giai đoạn Dự toán → Tạm tính → Quyết toán trên
mọi loại đơn, kèm danh mục Loại chi phí thu mua do người dùng tự quản.

Script dựng MỘT bài dưới nhóm có sẵn «Dành cho Nhân viên Mua hàng» (không đẻ nhóm mới):
«Chi phí thu mua trên đơn mua hàng» — kể đủ: khai dòng chi phí, ba giai đoạn và nút chốt,
mở lại, quyết toán riêng một dòng, công nợ sinh từ cột Quyết toán, chặn Hoàn thành, phân bổ
theo giai đoạn, danh mục loại chi phí, báo cáo giá vốn theo giai đoạn.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_chi_phi_thu_mua.py

Idempotent: đã có bài cùng tiêu đề dưới đúng nhóm thì xóa bài đó (kèm bài con, nếu có) rồi
chèn lại ở nguyên chỗ cũ. Thiếu nhóm cha thì DỪNG, không tự tạo bài gốc.

Nội dung phải KHỚP với `doc/tai-lieu-chuc-nang/04-don-mua-hang.md` mục K (K.0 → K.7) và
`08-he-thong-bao-cao.md` tab Giá vốn nhập khẩu. Không nêu mã phiếu mẫu của môi trường thử.
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
ARTICLE_TITLE = "Chi phí thu mua trên đơn mua hàng"

#  Tiêu đề các bài đã có, dùng làm đích liên kết nội bộ.
PO_ARTICLE_TITLE = "Đơn mua hàng (PO)"
PAYABLE_ARTICLE_TITLE = "Công nợ & Yêu cầu thanh toán"
REPORT_ARTICLE_TITLE = "Báo cáo mua hàng"


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
    "Khai các khoản chi ngoài giá hàng (cước, phí cảng, thuế, kiểm định, lưu kho...) trên đơn "
    "mua hàng theo ba giai đoạn Dự toán, Tạm tính, Quyết toán; công nợ chỉ sinh từ số quyết toán"
)

CONTENT = f"""<h2>I. Chi phí thu mua là gì</h2>
<p>Ngoài tiền trả cho nhà cung cấp bán hàng, một đơn mua hàng còn kéo theo nhiều khoản chi khác: cước vận tải, phí tại cảng, thuế nhập khẩu, phí kiểm định, bảo hiểm, lưu kho, vận chuyển nội địa... Mỗi khoản thường do <strong>một nhà cung cấp khác</strong> thu tiền và có hóa đơn riêng. Thẻ <strong>«Chi phí thu mua»</strong> trên màn chi tiết {ref(PO_ARTICLE_TITLE, "Đơn mua hàng")} là nơi khai các khoản đó, ngay dưới bảng Dòng hàng.</p>
<p>Thẻ này dùng cho <strong>mọi loại đơn</strong>, không riêng đơn nhập khẩu. Đơn trong nước chưa có khoản nào thì thẻ thu gọn, chỉ còn nút <em>Thêm chi phí</em>.</p>
<p>Điểm quan trọng nhất: mỗi khoản chi phí có <strong>ba con số</strong> theo ba giai đoạn, và <strong>chỉ con số Quyết toán mới sinh công nợ</strong>. Số dự toán hay tạm tính chỉ để lập kế hoạch và so lệch.</p>

<h2>II. Ba giai đoạn</h2>
<table>
<thead><tr><th>Giai đoạn</th><th>Khi nào</th><th>Ý nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Dự toán</strong></td><td>Lúc lập đơn, chưa có báo giá dịch vụ</td><td>Số ước lượng để biết tổng giá trị lô hàng khoảng bao nhiêu.</td></tr>
<tr><td><strong>Tạm tính</strong></td><td>Đã có báo giá cước, tờ khai dự kiến</td><td>Số gần đúng, dùng để theo dõi và phân bổ tạm.</td></tr>
<tr><td><strong>Quyết toán</strong></td><td>Hóa đơn đã về</td><td>Số thật. Từ số này hệ thống <strong>sinh công nợ</strong> cho từng nhà cung cấp dịch vụ.</td></tr>
</tbody>
</table>
<p>Cả đơn đứng ở <strong>một giai đoạn</strong>, hiện trên dải ba bước đầu thẻ. Trên bảng chi phí, cột của giai đoạn hiện hành <strong>gõ được và tô nền</strong>; cột đã qua bị khóa; cột chưa tới mờ đi. Gõ nhầm vào cột khác thì hệ thống bỏ qua, không báo lỗi.</p>
<p>Cột <strong>Lệch</strong> = số mới nhất trừ số Dự toán, kèm phần trăm. Dòng chưa có Dự toán thì ô Lệch để trống.</p>

<h2>III. Khai một khoản chi phí</h2>
<ol>
<li>Bấm <em>Thêm chi phí</em>, chọn <strong>Loại chi phí</strong> trong danh mục. Chọn xong, hệ thống tự điền nhà cung cấp mặc định, cách phân bổ và VAT của loại đó <strong>nếu ô đang trống</strong> (các khoản thuế mặc định nhà cung cấp là Ngân sách nhà nước).</li>
<li>Gõ <strong>Diễn giải</strong>, chọn <strong>Nhà cung cấp</strong> nhận tiền, chọn <strong>Tiền tệ</strong>. Một khoản dùng một đồng tiền cho cả ba giai đoạn.</li>
<li>Gõ số tiền <strong>trước thuế</strong> vào cột của giai đoạn hiện hành. Mỗi giai đoạn có tỷ giá riêng: cùng đồng tiền với đơn thì lấy tỷ giá của đơn, khác đồng tiền thì tỷ giá bằng 1. Số quy đổi đã gồm VAT hiện ở ô bên cạnh.</li>
<li>Điền <strong>Số hóa đơn</strong>, <strong>Ngày hóa đơn</strong>, <strong>Hạn thanh toán</strong> khi có. Hạn thanh toán gõ ở đây được ưu tiên hơn điều khoản của nhà cung cấp.</li>
<li>Bấm <strong>Lưu</strong> của đơn. Bảng chi phí <strong>vẫn sửa được sau khi đơn đã duyệt</strong>, vì hóa đơn cước và thuế thường về sau ngày duyệt. Đơn Hoàn thành hoặc Hủy thì chỉ xem.</li>
</ol>
<p>Một loại chi phí <strong>được khai nhiều dòng</strong> trong cùng đơn: mỗi dòng là một hóa đơn của một nhà cung cấp. Dòng chưa chọn nhà cung cấp vẫn lưu được nhưng <strong>không sinh công nợ</strong>.</p>
<p>Cây bút ở cột Hành động mở <strong>popup chi tiết</strong> của khoản: mỗi giai đoạn một khối số tiền, tỷ giá, quy đổi và tình trạng. Đầu popup ghi rõ vì sao dòng chưa thành công nợ (chưa quyết toán, chưa Lưu, chưa chọn nhà cung cấp, đơn chưa duyệt, hay loại chi phí không sinh công nợ).</p>

<h2>IV. Chốt giai đoạn</h2>
<ul>
<li><strong>Chốt tạm tính</strong> (Dự toán sang Tạm tính): cần quyền sửa đơn mua hàng. Ô Tạm tính còn trống thì hệ thống chép số Dự toán sang, ô đã có số thì giữ nguyên. Bảng chi phí đang sửa dở được lưu cùng lúc.</li>
<li><strong>Chốt quyết toán</strong> (Tạm tính sang Quyết toán): cần quyền sửa đơn mua hàng. Ô Quyết toán trống thì chép Tạm tính sang, rồi hệ thống <strong>sinh công nợ</strong> cho mọi dòng đủ điều kiện. Hộp xác nhận nêu trước số dòng sẽ thành công nợ và số dòng chưa có nhà cung cấp. Có thể chốt thẳng từ Dự toán lên Quyết toán.</li>
<li><strong>Quyết toán riêng một dòng</strong>: hóa đơn của một khoản về sớm trong khi cả đơn còn ở Dự toán hay Tạm tính, dùng menu <em>Quyết toán dòng này</em> ở cột Hành động. Dòng đó khóa ở cột Quyết toán và sinh công nợ ngay, các dòng khác không đổi.</li>
<li><strong>Mở lại</strong> (lùi về giai đoạn trước, hoặc mở lại một dòng đã quyết toán riêng): cần <strong>quyền duyệt đơn mua hàng</strong> và <strong>lý do tối thiểu 10 ký tự</strong>, lý do ghi vào nhật ký. Số ở cột đã mở không bị xóa, chỉ mở khóa. Dòng đã có tiền chi thì <strong>giữ nguyên quyết toán và giữ công nợ</strong>, dòng chưa chi thì gỡ công nợ.</li>
</ul>
<p>Ngày và người chốt từng giai đoạn hiện trên dải ba bước; đơn cũ không có dòng nhật ký thì ghi «chốt khi nâng cấp».</p>

<h2>V. Công nợ và thanh toán</h2>
<p>Mỗi dòng chi phí đã quyết toán thành <strong>một khoản công nợ</strong> loại «Chi phí thu mua» ở màn {ref(PAYABLE_ARTICLE_TITLE, "Công nợ")}, khi đủ bốn điều kiện: đơn đã duyệt; dòng ở giai đoạn Quyết toán; dòng có nhà cung cấp và số tiền lớn hơn 0; loại chi phí có bật <em>Sinh công nợ</em>. Sửa số Quyết toán, nhà cung cấp hay hóa đơn của dòng thì khoản nợ cập nhật theo; hạ số xuống dưới số đã chi thì hệ thống từ chối.</p>
<p>Dòng <strong>đã có tiền chi thì không xóa được</strong>. Hủy đơn thì gỡ các khoản chưa chi, giữ khoản đã chi.</p>
<p>Tạo Yêu cầu thanh toán cho chi phí có ba đường, đều đưa về màn lập phiếu và hệ thống tự tách mỗi nhà cung cấp một phiếu:</p>
<ul>
<li>Khối <strong>«Thanh toán chi phí theo nhà cung cấp»</strong> dưới bảng: mỗi nhà cung cấp một dòng Phải trả, Đã chi, Còn lại và nút <em>Tạo YCTT</em>. Đây là đường chính.</li>
<li>Tick các dòng trên bảng chi phí rồi bấm <em>Tạo YCTT (n dòng đã tick)</em>.</li>
<li>Popup <em>Tạo yêu cầu thanh toán</em> của đơn, tab <em>Chi phí thu mua</em>.</li>
</ul>
<p>Hai cột <strong>Đã chi</strong> / <strong>Còn lại</strong> trên bảng đọc từ khoản nợ; dòng chưa thành nợ hiện dấu gạch.</p>

<h2>VI. Hoàn thành đơn</h2>
<p>Đơn <strong>có ít nhất một dòng chi phí</strong> thì phải <strong>chốt quyết toán trước</strong> mới bấm Hoàn thành được; hộp xác nhận nhắc trước giai đoạn hiện hành và số dòng chưa quyết toán. Đơn không có dòng chi phí nào thì không bị chặn, hệ thống tự đặt giai đoạn Quyết toán khi Hoàn thành.</p>
<p>Riêng <strong>đơn nhập khẩu</strong> giữ luật chặt hơn: mọi khoản chi phí phải đã <strong>chi đủ</strong> mới Hoàn thành; còn dòng nào chưa trả hết thì hệ thống liệt kê từng dòng và số còn lại.</p>

<h2>VII. Phân bổ về dòng hàng, bản in, giá vốn</h2>
<p>Panel <strong>«Chi phí theo dòng hàng»</strong> dưới thẻ chia từng khoản về các dòng hàng theo cách phân bổ đã chọn (theo giá trị, khối lượng, số lượng, chỉ định một mã, hoặc nhập tay). Panel có <strong>nút chọn giai đoạn</strong> để xem phân bổ theo Dự toán, Tạm tính hay Quyết toán mà không cần tải lại; giai đoạn chưa có số thì nút mờ. Kết quả chỉ để xem, <strong>không lưu và không đẩy vào kho</strong>.</p>
<p>Bản in <em>In Đơn nhập khẩu</em> in số của giai đoạn hiện hành và ghi rõ giai đoạn trên tiêu đề khối, không in ba cột.</p>
<p>Tab <strong>Giá vốn nhập khẩu</strong> trong {ref(REPORT_ARTICLE_TITLE, "Báo cáo mua hàng")} có ô lọc <strong>Giai đoạn</strong> (mặc định Quyết toán) và ô tick <strong>Gồm đơn trong nước</strong>; mỗi đơn hiện thêm chi phí dự toán, chi phí quyết toán và số lệch để so sánh.</p>

<h2>VIII. Danh mục Loại chi phí thu mua</h2>
<p>Bộ loại chi phí nay là <strong>danh mục</strong> ở menu <em>Danh mục → Loại chi phí thu mua</em>, cần quyền <em>Loại chi phí thu mua</em>. Người có quyền tự thêm loại mới (ví dụ một loại phí kiểm định mới) mà không phải chờ sửa hệ thống.</p>
<ul>
<li>Mỗi loại có <strong>mã số</strong> (bỏ trống thì hệ thống tự cấp, không sửa được sau khi tạo), tên, nhóm (Thuế nộp ngân sách / Dịch vụ), nhà cung cấp mặc định, cách phân bổ mặc định, VAT mặc định và thứ tự hiện trong ô chọn.</li>
<li>Ô <strong>Sinh công nợ</strong>: tắt đi thì các dòng mang loại này <strong>không thành công nợ</strong> và không chặn Hoàn thành, nhưng vẫn cộng vào tổng chi phí và phân bổ. Dùng cho khoản đã trả ngoài hệ thống.</li>
<li>Loại đã dùng trên đơn thì <strong>không xóa được</strong>; bỏ tick <em>Đang dùng</em> để ẩn khỏi ô chọn. Dòng cũ đang mang loại đã tắt vẫn lưu được, tên hiện kèm «(đã tắt)».</li>
<li>Loại <strong>«Chi phí khác»</strong> (mã 99) là chỗ rơi của mọi mã lạ: không đổi tên, không tắt, không xóa.</li>
</ul>

<h2>IX. Câu hỏi thường gặp</h2>
<p><strong>Tôi gõ số vào cột Quyết toán mà bấm Lưu xong số biến mất?</strong> Đơn đang ở Dự toán hay Tạm tính nên cột Quyết toán chưa mở; hệ thống bỏ qua số gõ vào cột chưa tới. Chốt giai đoạn trước, hoặc dùng <em>Quyết toán dòng này</em> cho riêng dòng đó.</p>
<p><strong>Đã chốt quyết toán mà không thấy công nợ?</strong> Kiểm bốn điều kiện ở mục V: đơn đã duyệt chưa, dòng đã có nhà cung cấp và số tiền chưa, loại chi phí có bật Sinh công nợ không. Đầu popup chi tiết của dòng ghi đúng lý do.</p>
<p><strong>Chốt nhầm, muốn sửa lại số?</strong> Nhờ người có quyền duyệt đơn mua hàng bấm <em>Mở lại</em> và ghi lý do. Dòng đã có tiền chi thì không lùi được, phải xử lý qua công nợ.</p>
<p><strong>Đơn cũ trước ngày nâng cấp hiện giai đoạn nào?</strong> Đơn đã có dòng chi phí hoặc đã đóng được đặt sẵn ở Quyết toán, số cũ nằm ở cột Quyết toán; công nợ cũ giữ nguyên.</p>
"""

ARTICLES = [
    (STAFF_PARENT_TITLE, ARTICLE_TITLE, SUMMARY, CONTENT, 6),
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
