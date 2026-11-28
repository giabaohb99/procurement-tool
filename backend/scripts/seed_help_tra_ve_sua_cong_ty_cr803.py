# -*- coding: utf-8 -*-
"""Chèn mục *Trả về sửa Công ty nhận hóa đơn* vào bài HDSD Thu mua DỰNG TAY (duoc-CR-803, 28/11/2026).

Yêu cầu mua hàng đang **Đang mua hàng** mà chọn nhầm Công ty nhận hóa đơn: quản lý (quyền Hủy) hoặc người duyệt trong
phạm vi bấm nút **Trả về** có sẵn. Chỉ trả về được khi mọi dòng ĐMH liên quan (cùng mã PYC, chưa hủy) chưa nhận hàng và
ĐMH chưa có YCTT (chưa hủy) / công nợ. Phiếu sang Bị trả lại nhưng giữ NSTM và trạng thái dòng; người yêu cầu chỉ sửa
được Công ty nhận hóa đơn rồi Gửi duyệt; các ĐMH liên quan khóa mọi thao tác ghi (chỉ xem, in). Trưởng bộ phận Duyệt →
công ty chép xuống mọi ĐMH, mở khóa, phiếu tự về Đang mua hàng (không điều phối lại), NSTM nhận chuông *Đổi công ty
nhận hóa đơn*. Trong lúc trả về phiếu KHÔNG hủy / Từ chối phiếu được (nút ẩn); Duyệt chỉ được khi phiếu đã gửi lại và
chưa phát sinh YCTT / công nợ mới gắn mã ĐMH. Áp cho CẢ HAI giao diện (thumua cũ và ERP mới).
Câu lỗi lấy từ `purchase_request/invoice_company_return_service.py` (`find_invoice_company_return_blocker`,
`PO_LOCKED_MESSAGE`, `apply_invoice_company_approval`), `lifecycle_service.cancel_pr` và
`purchase_request/controller.approve_pr`; tiêu đề chuông ở `purchase_request/controller._approve_invoice_company_change`. Dòng báo đầu phiếu /
đầu đơn chỉ tả ý, không chép chữ (màn đang làm song song lúc viết bài).

Cùng khuôn `seed_help_sua_gia_trong_bang_cr802.py` (dùng lại ba hàm của script đó): tìm bài theo TIÊU ĐỀ dưới thẻ cha
tìm theo TIÊU ĐỀ (id local, dev, prod khác nhau); với mỗi bài:
  1. thay các cặp chữ cũ → mới ở `REPLACES` (câu *Lưu ý* của trả về thường, câu mở đầu bài Phê duyệt). Cặp không có
     trong bài thì báo *không khớp* và bỏ qua; chữ mới đã có thì coi như đã áp;
  2. chèn đoạn HTML ngay SAU câu neo. Câu neo không có hoặc có nhiều hơn một chỗ thì báo *không khớp* và bỏ qua (không
     đoán chỗ chèn); bài đã có dấu nhận của đoạn thì coi như đã áp.
Câu neo của hai bài *Xử lý yêu cầu mua hàng* là chữ MỚI của bước 1, nên bước 1 không khớp thì bước 2 cũng bỏ qua.
Bài *Đơn mua hàng (PO)* neo cùng chỗ với script cr794 (cuối danh sách *Các nút trên đơn mua hàng*), chạy trước hay sau
script đó đều được. Chạy lại bao nhiêu lần cũng vô hại; nạp lại kho vector cho đúng các bài vừa đổi. Đã đối chiếu với
bài #10, #40, #49, #51 trên local ngày 28/11/2026.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_tra_ve_sua_cong_ty_cr803.py --dry-run   # in bài nào đổi gì
    docker compose exec -T api python scripts/seed_help_tra_ve_sua_cong_ty_cr803.py

Nội dung phải khớp tài liệu chức năng `doc/erp/thu-mua/chuc-nang/12-yeu-cau-mua-hang.md` mục *Trả về phiếu Đang mua
hàng để sửa Công ty nhận hóa đơn*, `13-don-mua-hang.md` mục *Đơn tạm khóa* và cẩm nang trợ lý
`app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
import argparse

from help_seed_common import HelpArticle, SessionLocal, reindex_articles
from seed_help_sua_gia_trong_bang_cr802 import apply_replaces, insert_after_anchor, short

REQUESTER = "Dành cho Người yêu cầu"
APPROVER = "Dành cho TBP phê duyệt yêu cầu"
STAFF = "Dành cho Nhân viên Mua hàng"

#  Câu chặn chép đúng chữ máy chủ (`find_invoice_company_return_blocker`); dấu ... thay cho mã phiếu.
BLOCKERS_HTML = (
    "<em>Đơn mua hàng ... đã có dòng nhận hàng — không trả về được phiếu này</em>, "
    "<em>Đơn mua hàng đã có yêu cầu thanh toán ... — không trả về được phiếu này</em>, "
    "<em>Đơn mua hàng đã phát sinh công nợ — không trả về được phiếu này</em>")
CONDITIONS_HTML = (
    "phiếu đang <em>Đang mua hàng</em>; mọi dòng của các đơn mua hàng lập từ phiếu (trừ đơn đã hủy) <strong>chưa nhận "
    "hàng</strong>; các đơn đó <strong>chưa có yêu cầu thanh toán</strong> (trừ phiếu đã hủy) và <strong>chưa phát sinh "
    "công nợ</strong>. Thiếu một điều kiện thì hệ thống báo lý do, ví dụ " + BLOCKERS_HTML + ". Phiếu <em>Đang xử "
    "lý</em>, <em>Đã mua hàng</em>, <em>Hoàn thành</em> không trả về kiểu này được")

#  --- Hai bài *Xử lý yêu cầu mua hàng* (người yêu cầu và bản TBP, cùng nội dung mục 3) ---
PROCESS_NOTE = (
    "Sau khi duyệt lại, việc điều phối sẽ chạy lại từ đầu.</li>",
    "Sau khi duyệt lại, việc điều phối sẽ chạy lại từ đầu. Riêng phiếu trả về từ <em>Đang mua hàng</em> để sửa Công ty "
    "nhận hóa đơn thì khác, xem mục 3a.</li>")
PROCESS_MARKER = "<h3>3a. Bị trả lại chỉ để sửa Công ty nhận hóa đơn</h3>"
PROCESS_HTML = f"""
<h3>3a. Bị trả lại chỉ để sửa Công ty nhận hóa đơn</h3>
<p>Phiếu đã ở <em>Đang mua hàng</em> mà chọn nhầm <strong>Công ty nhận hóa đơn</strong> thì vẫn trả về được, nhưng chỉ để sửa đúng ô đó. Giao diện cũ và giao diện ERP mới làm giống nhau.</p>
<ul>
<li><strong>Ai bấm:</strong> quản lý thu mua có quyền Hủy phiếu, hoặc người duyệt phiếu (trưởng bộ phận trong phạm vi duyệt), bấm <strong>Trả về</strong> trên phiếu và nhập lý do. Người yêu cầu nhờ một trong hai người này.</li>
<li><strong>Khi nào trả về được:</strong> {CONDITIONS_HTML}.</li>
<li><strong>Sửa phiếu:</strong> phiếu sang <strong>Bị trả lại</strong>, đầu phiếu có dòng báo phiếu được trả về chỉ để sửa Công ty nhận hóa đơn. Chọn lại <strong>Công ty nhận hóa đơn</strong> (giao diện ERP mới bấm <strong>Sửa</strong> trước), rồi bấm <strong>Gửi duyệt</strong>. Mọi ô khác (dòng hàng, số lượng, giá, ngày...) chỉ xem; có gửi lên thì hệ thống cũng bỏ qua, chỉ lưu Công ty nhận hóa đơn.</li>
<li><strong>Trong lúc chờ duyệt lại:</strong> phiếu giữ nguyên nhân sự thu mua phụ trách và trạng thái từng dòng (không bị kéo về <em>Chưa tạo đơn mua hàng</em> như trả về thường). Không xóa, không hủy hay từ chối phiếu, không bật tắt <strong>Đơn gấp</strong>, không phân bổ lại người phụ trách, không cập nhật trạng thái dòng, không lập thêm đơn mua hàng từ phiếu được. Các đơn mua hàng liên quan bị tạm khóa: chỉ xem và in.</li>
<li><strong>Sau khi duyệt lại:</strong> trưởng bộ phận bấm <strong>Duyệt</strong> như thường, sau khi bạn đã bấm Gửi duyệt (phiếu còn <em>Bị trả lại</em> thì Duyệt bị chặn, câu báo <em>Phiếu đang chờ người yêu cầu sửa công ty nhận hóa đơn — chưa duyệt được</em>). Hệ thống chép công ty mới xuống mọi đơn mua hàng liên quan, mở khóa các đơn, phiếu tự về lại <em>Đang mua hàng</em> mà không phải điều phối lại. Nhân sự thu mua phụ trách nhận chuông báo <em>Đổi công ty nhận hóa đơn</em>.</li>
<li><strong>Duyệt bị chặn vì chứng từ mới:</strong> trong lúc khóa mà có yêu cầu thanh toán mới gắn mã đơn mua hàng (hoặc phát sinh công nợ) thì Duyệt báo lý do kèm câu <em>Xử lý chứng từ đó trước rồi duyệt lại</em>.</li>
<li><strong>Bị trả về tiếp:</strong> trưởng bộ phận bấm <strong>Trả về</strong> lần nữa thì phiếu vẫn chỉ sửa được Công ty nhận hóa đơn, các đơn vẫn khóa.</li>
<li><strong>Muốn bỏ đợt sửa:</strong> phiếu không hủy được, nút <strong>Từ chối phiếu</strong> ẩn trong lúc này. Chọn lại công ty cũ, bấm Gửi duyệt và để trưởng bộ phận duyệt; các đơn mở khóa, giữ nguyên công ty.</li>
</ul>"""
#  Câu neo = chữ MỚI của cặp PROCESS_NOTE; bài người yêu cầu viết liền, bài TBP xuống dòng giữa </li> và </ul>.
REQUESTER_ANCHOR = "xem mục 3a.</li></ul>"
APPROVER_PROCESS_ANCHOR = "xem mục 3a.</li>\n</ul>"

#  --- Bài *Phê duyệt yêu cầu mua hàng* (TBP) ---
APPROVE_INTRO = (
    "Chờ duyệt</span>.</p>",
    "Chờ duyệt</span>. Riêng nút <strong>Trả về</strong> còn hiện ở phiếu <em>Đang mua hàng</em>, xem mục <em>Trả về "
    "phiếu Đang mua hàng để sửa Công ty nhận hóa đơn</em> cuối bài.</p>")
APPROVE_MARKER = "<h3>Trả về phiếu Đang mua hàng để sửa Công ty nhận hóa đơn</h3>"
APPROVE_ANCHOR = "đây là cách nhanh nhất phát hiện mặt hàng chưa có người lo.</p>"
APPROVE_HTML = f"""
<h3>Trả về phiếu Đang mua hàng để sửa Công ty nhận hóa đơn</h3>
<p>Người yêu cầu chọn nhầm <strong>Công ty nhận hóa đơn</strong> mà phiếu đã ở <em>Đang mua hàng</em> thì bạn (người duyệt trong phạm vi), hoặc quản lý thu mua có quyền Hủy phiếu, bấm <strong>Trả về</strong> và nhập lý do. Giao diện cũ và giao diện ERP mới làm giống nhau.</p>
<ul>
<li><strong>Điều kiện:</strong> {CONDITIONS_HTML}.</li>
<li><strong>Sau khi trả về:</strong> phiếu sang <strong>Bị trả lại</strong> nhưng giữ nguyên nhân sự thu mua phụ trách và trạng thái dòng. Người yêu cầu chỉ sửa được Công ty nhận hóa đơn. Các đơn mua hàng liên quan tạm khóa, chỉ xem và in.</li>
<li><strong>Duyệt lại:</strong> phiếu gửi lại hiện ở <em>Chờ duyệt</em> như thường. Phiếu còn <em>Bị trả lại</em> (người yêu cầu chưa gửi lại) thì chưa duyệt được: <em>Phiếu đang chờ người yêu cầu sửa công ty nhận hóa đơn — chưa duyệt được</em>. Bấm <strong>Duyệt</strong>: công ty mới chép xuống mọi đơn mua hàng liên quan, các đơn mở khóa, phiếu tự về <em>Đang mua hàng</em>, không qua bước Duyệt điều phối. Nhân sự thu mua phụ trách nhận chuông báo <em>Đổi công ty nhận hóa đơn</em>.</li>
<li><strong>Duyệt bị chặn vì chứng từ mới:</strong> trong lúc khóa mà có yêu cầu thanh toán mới gắn mã đơn mua hàng (hoặc phát sinh công nợ) thì Duyệt báo lý do kèm câu <em>Xử lý chứng từ đó trước rồi duyệt lại</em>.</li>
<li><strong>Trả về lần nữa</strong> thì phiếu vẫn ở chế độ chỉ sửa công ty, các đơn vẫn khóa. Trong lúc này phiếu <strong>không hủy, không Từ chối phiếu được</strong> (nút ẩn). Muốn bỏ đợt sửa thì trả về để người yêu cầu chọn lại công ty cũ, gửi duyệt, rồi bạn duyệt.</li>
</ul>"""

#  --- Bài *Đơn mua hàng (PO)* ---
PO_MARKER = "<h3>Đơn tạm khóa khi yêu cầu mua hàng được trả về sửa công ty</h3>"
#  Cuối danh sách *Các nút trên đơn mua hàng* (script cr741 dựng); script cr794 cũng neo ở đây.
PO_ANCHOR = "mỗi mục có nút <strong>Upload thêm file cho mục này</strong>.</li>\n</ul>"
PO_HTML = """
<h3>Đơn tạm khóa khi yêu cầu mua hàng được trả về sửa công ty</h3>
<p>Yêu cầu mua hàng nguồn (cùng mã PYC) đang <em>Đang mua hàng</em> mà được trả về để sửa <strong>Công ty nhận hóa đơn</strong> thì mọi đơn mua hàng lập từ phiếu đó (trừ đơn đã hủy) bị tạm khóa tới khi trưởng bộ phận duyệt lại phiếu. Giao diện cũ và giao diện ERP mới giống nhau:</p>
<ul>
<li>Đầu đơn hiện dòng báo đơn đang tạm khóa, kèm mã yêu cầu mua hàng được trả về.</li>
<li><strong>Chỉ xem và in.</strong> Mọi thao tác ghi bị chặn: sửa đơn, gửi duyệt, duyệt, hủy duyệt, sửa giá, tiến độ, nhận hàng, chi phí thu mua, tải lên hay xóa tệp đính kèm, hủy, xóa đơn. Tiến độ tự động của dòng cũng đứng yên. Làm thao tác ghi thì hệ thống báo <em>Đơn mua hàng đang bị khóa: yêu cầu mua hàng liên quan đã trả về để sửa công ty nhận hóa đơn, chờ duyệt lại</em>.</li>
<li><strong>Duyệt lại xong:</strong> Công ty nhận hóa đơn của đơn tự đổi theo phiếu, đơn mở khóa và làm tiếp bình thường. Nhân sự thu mua phụ trách nhận chuông báo <em>Đổi công ty nhận hóa đơn</em>. Phiếu không hủy được trong lúc này, nên đơn chỉ mở khóa khi phiếu được duyệt lại (bỏ đợt sửa thì người yêu cầu chọn lại công ty cũ).</li>
<li>Trong lúc khóa mà có yêu cầu thanh toán mới gắn mã đơn thì trưởng bộ phận chưa duyệt lại được phiếu; xử lý yêu cầu thanh toán đó trước.</li>
<li>Phiếu chỉ trả về kiểu này được khi mọi đơn liên quan chưa dòng nào nhận hàng, chưa có yêu cầu thanh toán và chưa phát sinh công nợ.</li>
</ul>"""

#  (thẻ cha, tiêu đề bài, [cặp cũ → mới], dấu nhận, câu neo, đoạn chèn ngay sau câu neo)
EDITS = [
    (REQUESTER, "Xử lý yêu cầu mua hàng", [PROCESS_NOTE], PROCESS_MARKER, REQUESTER_ANCHOR, PROCESS_HTML),
    (APPROVER, "Xử lý yêu cầu mua hàng (TBP)", [PROCESS_NOTE], PROCESS_MARKER, APPROVER_PROCESS_ANCHOR, PROCESS_HTML),
    (APPROVER, "Phê duyệt yêu cầu mua hàng", [APPROVE_INTRO], APPROVE_MARKER, APPROVE_ANCHOR, APPROVE_HTML),
    (STAFF, "Đơn mua hàng (PO)", [], PO_MARKER, PO_ANCHOR, PO_HTML),
]


def main() -> None:
    p = argparse.ArgumentParser(description="Chèn mục Trả về sửa Công ty nhận hóa đơn vào bài HDSD Thu mua (duoc-CR-803)")
    p.add_argument("--dry-run", action="store_true", help="chỉ in bài nào đổi gì, không ghi")
    args = p.parse_args()
    db = SessionLocal()
    touched = []
    try:
        for parent_title, title, pairs, marker, anchor, html in EDITS:
            parent = (db.query(HelpArticle)
                      .filter(HelpArticle.parent_id.is_(None), HelpArticle.title == parent_title).first())
            row = parent and (db.query(HelpArticle)
                              .filter(HelpArticle.parent_id == parent.id, HelpArticle.title == title).first())
            if not row:
                print(f"BỎ QUA '{title}': không thấy bài dưới thẻ '{parent_title}' trên hệ này")
                continue
            content, notes = apply_replaces(row.content or "", pairs)
            content, note = insert_after_anchor(content, marker, anchor, html)
            changed = content != (row.content or "")
            print(f"{'ĐỔI' if changed else 'giữ'} #{row.id} '{title}' (dưới '{parent_title}')")
            for line in notes + [note]:
                print(f"    {short(line) if len(line) > 160 else line}")
            if changed and not args.dry_run:
                row.content = content
                touched.append(row.id)
        if args.dry_run:
            print("Thử xong, chưa ghi gì.")
            return
        db.commit()
    finally:
        db.close()
    print(f"Đã ghi {len(touched)} bài.")
    reindex_articles(touched)
    print("Xong.")


if __name__ == "__main__":
    main()
