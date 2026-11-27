# -*- coding: utf-8 -*-
"""Chèn mục *Sửa giá trong bảng* vào bài HDSD Thu mua DỰNG TAY (bao-CR-802, 27/11/2026).

Đơn mua hàng đã duyệt có HAI cách sửa giá song song:
  - hộp **Sửa giá** (bao-CR-794, `price_adjust_service.py`, cả hai giao diện): chỉ đơn giá, bắt buộc lý do, chặn theo cả
    đơn; bài HDSD đã có mục *Sửa giá sau duyệt* do `seed_help_sua_gia_dmh_cr794.py` chèn;
  - nút **Sửa giá trong bảng** (duoc-CR-797, `reprice_service.py`, chỉ giao diện ERP mới): SL đặt, đơn giá, VAT ngay
    trong bảng dòng, không hỏi lý do, chặn theo TỪNG dòng kèm lý do, YCTT Nháp trỏ vào công nợ của dòng tự nạp lại; lưu
    xong lịch sử mua hàng và sổ giá đi theo (bao-CR-799).
Nhãn lấy từ `frontend-v2/src/modules/procurement`: `pages/purchase-order-detail-page.tsx` (nút),
`components/purchase-order-reprice-bar.tsx` (thanh đáy *Thôi* / *Lưu giá mới*), `components/purchase-order-items-table.tsx`
(tiêu đề cột, *Dưới SL đã nhận*), `hooks/use-purchase-order-reprice.ts` (hộp *Bỏ phần sửa giá?*); lý do khóa dòng ở
`reprice_service._lock_reason`.

Cùng khuôn `seed_help_sua_gia_dmh_cr794.py`: tìm bài theo TIÊU ĐỀ dưới thẻ cha tìm theo TIÊU ĐỀ (id local, dev, prod khác
nhau); với mỗi bài:
  1. thay các cặp chữ cũ → mới ở `REPLACES` (câu mở đầu mục Sửa giá sau duyệt còn ghi *đổi số lượng, VAT phải Hủy
     duyệt*). Cặp không có trong bài thì báo *không khớp* và bỏ qua; chữ mới đã có thì coi như đã áp;
  2. chèn đoạn HTML ngay SAU câu neo. Câu neo không có hoặc có nhiều hơn một chỗ thì báo *không khớp* và bỏ qua (không
     đoán chỗ chèn); bài đã có dấu nhận của đoạn thì coi như đã áp.
Chạy lại bao nhiêu lần cũng vô hại; nạp lại kho vector cho đúng các bài vừa đổi. Câu neo là đoạn cuối mà script cr794 đã
chèn, nên script cr794 phải chạy TRƯỚC script này trên mỗi hệ. Đã đối chiếu với bài #10 và #14 trên dev ngày 27/11/2026.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_sua_gia_trong_bang_cr802.py --dry-run   # in bài nào đổi gì
    docker compose exec -T api python scripts/seed_help_sua_gia_trong_bang_cr802.py

Nội dung phải khớp tài liệu chức năng `doc/erp/thu-mua/chuc-nang/13-don-mua-hang.md` mục *Sửa giá trong bảng* và cẩm nang
trợ lý `app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
import argparse

from help_seed_common import HelpArticle, SessionLocal, reindex_articles

STAFF = "Dành cho Nhân viên Mua hàng"
ACCOUNTING = "Dành cho Kho & Kế toán"

#  --- Bài Đơn mua hàng (PO) ---
PO_INTRO = (
    "<p>Đơn đã duyệt thì nội dung bị khóa. Cần đổi mã hàng, số lượng hay VAT thì người có quyền duyệt bấm "
    "<strong>Hủy duyệt</strong> và nhập lý do: đơn về <em>Nháp</em>, sửa xong phải gửi duyệt lại. Đơn đã nhận hàng thì "
    "không còn nút Hủy duyệt. Riêng <strong>đơn giá</strong> có đường sửa riêng, dùng được cả khi hàng đã về:</p>",
    "<p>Đơn đã duyệt thì nội dung bị khóa. Cần đổi mã hàng, thêm hay bỏ dòng thì người có quyền duyệt bấm "
    "<strong>Hủy duyệt</strong> và nhập lý do: đơn về <em>Nháp</em>, sửa xong phải gửi duyệt lại. Đơn đã nhận hàng thì "
    "không còn nút Hủy duyệt. Riêng phần giá có hai cách sửa mà đơn vẫn giữ nguyên trạng thái, dùng được cả khi hàng đã "
    "về: hộp <strong>Sửa giá</strong> (mục này, chỉ đổi đơn giá) và <strong>Sửa giá trong bảng</strong> (mục dưới, đổi "
    "cả SL đặt và VAT). Hộp Sửa giá:</p>")
PO_BOX_ONLY_PRICE = (
    "Chỉ đơn giá đổi; mã hàng, số lượng, VAT vẫn khóa.",
    "Hộp này chỉ đổi đơn giá; cần đổi SL đặt hay VAT thì dùng <strong>Sửa giá trong bảng</strong> ở mục dưới.")

PO_MARKER = "<h3>Sửa giá trong bảng</h3>"
#  Cuối mục *Sửa giá sau duyệt* do script cr794 chèn.
PO_ANCHOR = "Hệ thống nhắc mã phiếu để bạn kiểm lại số tiền trên phiếu trước khi gửi duyệt.</li>\n</ul>"
PO_HTML = """
<h3>Sửa giá trong bảng</h3>
<p>Cách thứ hai, chỉ có ở giao diện ERP mới: sửa <strong>SL đặt</strong>, <strong>Đơn giá</strong> và <strong>VAT</strong> ngay trên bảng dòng hàng của đơn đã duyệt, không phải nhập lý do.</p>
<ul>
<li><strong>Ai dùng được:</strong> người có quyền <strong>Duyệt</strong> đơn mua hàng. Đơn ở <em>Đã duyệt</em>, <em>Đã nhận một phần</em> hoặc <em>Đã nhận đủ</em>, kể cả khi hàng đã về.</li>
<li><strong>Cách làm:</strong> mở chi tiết đơn, bấm <strong>Sửa giá trong bảng</strong> trên thanh nút (đang mở popup chi tiết dòng thì bấm nút <strong>Sửa giá</strong> ở đầu popup). Các ô <em>SL đặt</em>, <em>Đơn giá</em>, <em>VAT%</em>, <em>Đơn giá (Sau VAT)</em> của dòng sửa được mở ra để gõ (đơn nhập khẩu không có hai cột VAT). Ô vừa đổi tô vàng, bên dưới có số đang lưu gạch ngang. Thanh nổi ở đáy màn hiện số dòng đã sửa và tổng đơn cũ → mới.</li>
<li><strong>Lưu hoặc bỏ:</strong> bấm <strong>Lưu giá mới</strong> trên thanh đáy để ghi mọi dòng đã sửa trong một lần. Bấm <strong>Thôi</strong> để bỏ; đã sửa mà chưa lưu thì hệ thống hỏi lại (<em>Bỏ phần sửa giá?</em>).</li>
<li><strong>SL đặt không được nhỏ hơn SL đã nhận:</strong> gõ nhỏ hơn thì dưới ô báo đỏ <em>Dưới SL đã nhận</em> và không lưu được.</li>
<li><strong>Dòng không sửa được:</strong> ô của dòng mờ đi, rê chuột vào thấy lý do. Chặn theo <strong>từng dòng</strong>, các dòng khác của đơn vẫn sửa được. Dòng bị chặn khi: đã <em>Hoàn thành</em> hoặc đã hủy; công nợ của dòng đã có tiền trả; dòng đã nằm trên yêu cầu thanh toán đang chờ duyệt, đã duyệt hoặc đã chi (trả phiếu đó về trước).</li>
<li><strong>Sau khi lưu:</strong> đơn giữ nguyên trạng thái. Thành tiền, tồn kho, công nợ hàng và tiến độ yêu cầu mua hàng tính lại theo số mới; lịch sử mua hàng và các màn Giá nguyên vật liệu sản xuất đi theo. Yêu cầu thanh toán còn <strong>Nháp</strong> có công nợ của dòng vừa sửa được <strong>tự nạp lại</strong> theo số mới, câu báo kèm mã phiếu. Nhật ký của đơn ghi từng ô cũ → mới.</li>
</ul>
<p><strong>Chọn cách nào:</strong></p>
<table>
<thead><tr><th></th><th>Hộp Sửa giá</th><th>Sửa giá trong bảng</th></tr></thead>
<tbody>
<tr><td>Ô sửa được</td><td>Chỉ đơn giá</td><td>SL đặt, đơn giá, VAT</td></tr>
<tr><td>Lý do</td><td>Bắt buộc nhập</td><td>Không hỏi; nhật ký ghi từng ô cũ → mới</td></tr>
<tr><td>Bị chặn</td><td>Cả đơn, khi đơn có yêu cầu thanh toán đã gửi duyệt / đã duyệt / đã chi, hoặc công nợ hàng của đơn đã trả tiền</td><td>Từng dòng, kèm lý do trên ô</td></tr>
<tr><td>Yêu cầu thanh toán Nháp</td><td>Nhắc mã phiếu để bạn kiểm lại số tiền</td><td>Tự nạp lại theo số mới</td></tr>
<tr><td>Giao diện</td><td>Cả hai giao diện</td><td>Chỉ giao diện ERP mới</td></tr>
</tbody>
</table>"""

#  --- Bài Công nợ & Yêu cầu thanh toán ---
PAYABLE_MARKER = "Sửa giá trong bảng"
#  Cuối đoạn *Khoản nợ đổi số sau khi đã ghi* do script cr794 chèn.
PAYABLE_ANCHOR = "có đơn này thì kiểm lại số tiền trên phiếu trước khi gửi duyệt.</p>"
PAYABLE_HTML = (
    "<p>Cách thứ hai là nút <strong>Sửa giá trong bảng</strong> trên đơn đã duyệt (giao diện ERP mới): đổi được SL đặt, "
    "đơn giá và VAT của dòng; công nợ hàng tính lại theo số mới, không hỏi lý do (nhật ký đơn ghi từng ô cũ → mới). Dòng "
    "có công nợ đã trả tiền, hoặc đã nằm trên yêu cầu thanh toán đang chờ duyệt, đã duyệt hay đã chi thì không sửa được. "
    "Yêu cầu thanh toán còn <strong>Nháp</strong> có công nợ của dòng vừa sửa thì <strong>tự nạp lại</strong> theo số "
    "mới, không phải sửa tay.</p>")

#  (thẻ cha, tiêu đề bài, [cặp cũ → mới], dấu nhận, câu neo, đoạn chèn ngay sau câu neo)
EDITS = [
    (STAFF, "Đơn mua hàng (PO)", [PO_INTRO, PO_BOX_ONLY_PRICE], PO_MARKER, PO_ANCHOR, PO_HTML),
    (ACCOUNTING, "Công nợ & Yêu cầu thanh toán", [], PAYABLE_MARKER, PAYABLE_ANCHOR, PAYABLE_HTML),
]


def short(text: str) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= 70 else flat[:67] + "..."


def apply_replaces(content: str, pairs: list[tuple[str, str]]) -> tuple[str, list[str]]:
    notes = []
    for old, new in pairs:
        if new in content:
            notes.append(f"đã có chữ mới: {short(new)}")
        elif content.count(old) == 1:
            content = content.replace(old, new)
            notes.append(f"thay: {short(old)}")
        else:
            notes.append(f"không khớp (chữ cũ có {content.count(old)} chỗ, cần đúng 1): {short(old)} — sửa tay trên giao diện")
    return content, notes


def insert_after_anchor(content: str, marker: str, anchor: str, html: str) -> tuple[str, str]:
    if marker in content:
        return content, f"đã có đoạn: {marker}"
    found = content.count(anchor)
    if found != 1:
        return content, f"không khớp (câu neo có {found} chỗ, cần đúng 1): {short(anchor)} — chèn tay trên giao diện"
    return content.replace(anchor, anchor + html), f"chèn đoạn: {marker}"


def main() -> None:
    p = argparse.ArgumentParser(description="Chèn mục Sửa giá trong bảng vào bài HDSD Thu mua dựng tay (bao-CR-802)")
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
                print(f"    {line}")
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
