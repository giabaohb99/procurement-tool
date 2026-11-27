# -*- coding: utf-8 -*-
"""Chèn đoạn *Sửa giá sau duyệt* vào các bài HDSD Thu mua DỰNG TAY (bao-CR-794, 27/11/2026).

Chi tiết Đơn mua hàng có thêm nút **Sửa giá** (cạnh Hủy duyệt) mở hộp *Sửa giá sau duyệt*: người có quyền Duyệt đổi ĐƠN
GIÁ của dòng trên đơn đã duyệt, kể cả đơn đã nhận hàng; đơn giữ nguyên trạng thái. Nguồn sự thật:
`app/modules/purchase_order/price_adjust_service.py`, nhãn ở `frontend/src/components/PoPriceAdjustModal.tsx` (giao diện
mới dùng cùng nhãn).

Cây trợ giúp Thu mua được dựng TAY trên giao diện, không có script sở hữu, nên script này KHÔNG xóa / dựng lại cây
(cùng khuôn `seed_help_thu_mua_doi_ten_nut_cr741.py`). Nó chỉ:
  1. tìm bài theo TIÊU ĐỀ dưới thẻ cha tìm theo TIÊU ĐỀ (id ở local, dev, prod khác nhau);
  2. chèn đoạn HTML ngay SAU câu neo khai ở `EDITS`. Câu neo không có trong bài, hoặc có nhiều hơn một chỗ, thì báo
     *không khớp* và bỏ qua bài đó (không đoán chỗ chèn) — khi ấy chèn tay trên giao diện;
  3. bài đã có dấu nhận của đoạn thì coi như đã áp, nên chạy lại bao nhiêu lần cũng vô hại;
  4. nạp lại kho vector cho đúng các bài vừa đổi.
Câu neo đã đối chiếu với nội dung bài trên dev và prod ngày 27/11/2026 (hai hệ giống nhau từng ký tự): bài Đơn mua hàng
neo vào cuối khối *Các nút trên đơn mua hàng* do script cr741 nối; bài Công nợ neo vào cuối mục 1.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_sua_gia_dmh_cr794.py --dry-run   # in bài nào đổi gì
    docker compose exec -T api python scripts/seed_help_sua_gia_dmh_cr794.py

Nội dung phải khớp tài liệu chức năng `doc/erp/thu-mua/chuc-nang/13-don-mua-hang.md` mục *Sửa giá sau duyệt* và cẩm nang
trợ lý `app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
import argparse

from help_seed_common import HelpArticle, SessionLocal, reindex_articles

STAFF = "Dành cho Nhân viên Mua hàng"
ACCOUNTING = "Dành cho Kho & Kế toán"

#  Dấu nhận: có chuỗi này trong bài là đoạn đã được chèn (hoặc đã có người viết tay) — không chèn lần hai.
PO_MARKER = "<h3>Sửa giá sau duyệt</h3>"
PAYABLE_MARKER = "Sửa giá sau duyệt"

#  Cuối khối *Các nút trên đơn mua hàng* (script cr741 nối vào cuối bài).
PO_ANCHOR = "mỗi mục có nút <strong>Upload thêm file cho mục này</strong>.</li>\n</ul>"

PO_PRICE_ADJUST_HTML = """
<h3>Sửa giá sau duyệt</h3>
<p>Đơn đã duyệt thì nội dung bị khóa. Cần đổi mã hàng, số lượng hay VAT thì người có quyền duyệt bấm <strong>Hủy duyệt</strong> và nhập lý do: đơn về <em>Nháp</em>, sửa xong phải gửi duyệt lại. Đơn đã nhận hàng thì không còn nút Hủy duyệt. Riêng <strong>đơn giá</strong> có đường sửa riêng, dùng được cả khi hàng đã về:</p>
<ul>
<li><strong>Ai dùng được:</strong> người có quyền <strong>Duyệt</strong> đơn mua hàng (cùng người bấm được Hủy duyệt). Đơn phải ở trạng thái <em>Đã duyệt</em>, <em>Đã nhận một phần</em> hoặc <em>Đã nhận đủ</em>.</li>
<li><strong>Cách làm:</strong> mở chi tiết đơn, bấm <strong>Sửa giá</strong> trên thanh nút (cạnh Hủy duyệt). Trong hộp <em>Sửa giá sau duyệt</em>, gõ giá vào cột <em>Đơn giá mới</em> của dòng cần đổi (cột <em>Đơn giá hiện tại</em> để so), nhập <strong>Lý do sửa giá</strong> (bắt buộc) rồi bấm <strong>Lưu giá mới</strong>. Cột <em>Chênh lệch (chưa VAT)</em> cho biết tiền hàng đã nhận tăng hay giảm bao nhiêu; dòng chưa nhận hàng thì hiện dấu —.</li>
<li><strong>Đơn giữ nguyên trạng thái:</strong> không về Nháp, không phải duyệt lại. Chỉ đơn giá đổi; mã hàng, số lượng, VAT vẫn khóa.</li>
<li><strong>Sau khi lưu:</strong> thành tiền dòng và công nợ hàng tính lại theo số lượng đã nhận. Lịch sử mua hàng và các màn Giá nguyên vật liệu sản xuất (Bảng giá VTBB, Giá mua gần nhất, Lịch sử mua hàng) đi theo giá mới. Nhật ký của đơn ghi giá cũ → giá mới kèm lý do.</li>
<li><strong>Không sửa được khi:</strong> đơn đã có yêu cầu thanh toán đã gửi duyệt, đã duyệt hoặc đã chi (hủy phiếu thanh toán trước rồi mới sửa giá); công nợ hàng của đơn đã trả tiền; dòng đã <em>Hoàn thành</em> hoặc đã <em>Hủy</em>; đơn đã Hoàn thành hoặc đã Hủy. Đơn chưa duyệt thì sửa thẳng trên đơn.</li>
<li><strong>Yêu cầu thanh toán còn Nháp có đơn này:</strong> vẫn sửa giá được. Hệ thống nhắc mã phiếu để bạn kiểm lại số tiền trên phiếu trước khi gửi duyệt.</li>
</ul>"""

#  Cuối mục *1. Khoản công nợ sinh ra khi nào* của bài Công nợ & Yêu cầu thanh toán.
PAYABLE_ANCHOR = "Mỗi lần giao là một khoản nợ riêng, kèm hạn trả tính theo điều khoản thanh toán của nhà cung cấp.</p>"

PAYABLE_PRICE_ADJUST_HTML = (
    "<p><strong>Khoản nợ đổi số sau khi đã ghi:</strong> người có quyền duyệt đơn mua hàng có thể bấm <strong>Sửa "
    "giá</strong> trên đơn đã duyệt (hộp <em>Sửa giá sau duyệt</em>), kể cả khi hàng đã về. Khi đó công nợ hàng của đơn "
    "được tính lại theo đơn giá mới và số lượng đã nhận; nhật ký của đơn ghi giá cũ, giá mới và lý do. Đơn đã có yêu cầu "
    "thanh toán đã gửi duyệt, đã duyệt hoặc đã chi, hay công nợ hàng đã trả tiền thì không sửa giá được. Yêu cầu thanh "
    "toán còn <strong>Nháp</strong> có đơn này thì kiểm lại số tiền trên phiếu trước khi gửi duyệt.</p>")

#  (thẻ cha, tiêu đề bài, dấu nhận đã có, câu neo, đoạn HTML chèn ngay sau câu neo)
EDITS = [
    (STAFF, "Đơn mua hàng (PO)", PO_MARKER, PO_ANCHOR, PO_PRICE_ADJUST_HTML),
    (ACCOUNTING, "Công nợ & Yêu cầu thanh toán", PAYABLE_MARKER, PAYABLE_ANCHOR, PAYABLE_PRICE_ADJUST_HTML),
]


def insert_after_anchor(content: str, marker: str, anchor: str, html: str) -> tuple[str, str]:
    """Trả nội dung mới + một dòng nhật ký cho bản in (chèn / đã có / không khớp)."""
    if marker in content:
        return content, f"đã có đoạn: {marker}"
    found = content.count(anchor)
    if found != 1:
        flat = " ".join(anchor.split())
        short = flat if len(flat) <= 70 else flat[:67] + "..."
        return content, f"không khớp (câu neo có {found} chỗ, cần đúng 1): {short} — chèn tay trên giao diện"
    return content.replace(anchor, anchor + html), f"chèn đoạn: {marker}"


def main() -> None:
    p = argparse.ArgumentParser(description="Chèn đoạn Sửa giá sau duyệt vào bài HDSD Thu mua dựng tay (bao-CR-794)")
    p.add_argument("--dry-run", action="store_true", help="chỉ in bài nào đổi gì, không ghi")
    args = p.parse_args()
    db = SessionLocal()
    touched = []
    try:
        for parent_title, title, marker, anchor, html in EDITS:
            parent = (db.query(HelpArticle)
                      .filter(HelpArticle.parent_id.is_(None), HelpArticle.title == parent_title).first())
            row = parent and (db.query(HelpArticle)
                              .filter(HelpArticle.parent_id == parent.id, HelpArticle.title == title).first())
            if not row:
                print(f"BỎ QUA '{title}': không thấy bài dưới thẻ '{parent_title}' trên hệ này")
                continue
            content, note = insert_after_anchor(row.content or "", marker, anchor, html)
            changed = content != (row.content or "")
            print(f"{'ĐỔI' if changed else 'giữ'} #{row.id} '{title}' (dưới '{parent_title}')")
            print(f"    {note}")
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
