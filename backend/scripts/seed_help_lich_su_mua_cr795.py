# -*- coding: utf-8 -*-
"""Vá bài HDSD *Lịch sử mua hàng & Tham chiếu giá* (dựng TAY) theo luật ghi lịch sử mới (bao-CR-795, 27/11/2026).

Bài còn ghi luật cũ: lần mua chỉ vào lịch sử khi dòng Hoàn thành, số liệu giữ nguyên mãi. Từ bao-CR-790 lịch sử có bản
ghi ngay khi dòng của đơn đã duyệt NHẬN HÀNG; bản ghi đang mở đi theo đơn (đổi giá / số lượng thì đổi theo; dòng hủy,
đơn hủy, bỏ duyệt, xóa thì gỡ), tới khi dòng Hoàn thành thì chốt, không đổi nữa. bao-CR-794 thêm nút **Sửa giá** trên đơn
đã duyệt cho người có quyền duyệt; giá mới đi vào lịch sử của lần mua đó. Nguồn sự thật:
`app/modules/purchase_history/service.py`, `app/modules/purchase_order/price_adjust_service.py`; tài liệu chức năng
`doc/erp/thu-mua/chuc-nang/18-lich-su-mua-hang.md` mục 6 và `13-don-mua-hang.md` mục *Sửa giá sau duyệt*.

Cùng khuôn `seed_help_thu_mua_doi_ten_nut_cr741.py`: tìm bài theo TIÊU ĐỀ dưới thẻ cha tìm theo TIÊU ĐỀ (id local, dev,
prod khác nhau), thay đúng các cặp chữ cũ → mới ở `EDITS`; cặp không có trong bài thì báo *không khớp* và bỏ qua (sửa tay
trên giao diện); chạy lại vô hại; nạp lại kho vector cho bài vừa đổi. Câu cũ đã đối chiếu với bài id 34 trên dev ngày
27/11/2026.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_lich_su_mua_cr795.py --dry-run   # in bài nào đổi gì
    docker compose exec -T api python scripts/seed_help_lich_su_mua_cr795.py
"""
import argparse

from help_seed_common import HelpArticle, SessionLocal, reindex_articles
from seed_help_thu_mua_doi_ten_nut_cr741 import apply_edits

STAFF = "Dành cho Nhân viên Mua hàng"
TITLE = "Lịch sử mua hàng & Tham chiếu giá"

#  Mục 1: luật ghi vào lịch sử.
WHEN_RECORDED = (
    "<li>Một lần mua chỉ vào lịch sử khi mặt hàng đó trong đơn đã <strong>Hoàn thành</strong> — tức là đã nhận đủ hàng và "
    "kết thúc.</li>",
    "<li>Một lần mua vào lịch sử ngay khi dòng hàng của đơn <strong>đã duyệt</strong> bắt đầu <strong>nhận hàng</strong> "
    "(đã nhận một phần cũng tính), không phải đợi tới lúc Hoàn thành.</li>")
NOT_COUNTED = (
    "<li>Đơn còn Nháp, đang Chờ duyệt, đang xử lý hoặc đã Hủy thì <strong>chưa được tính</strong>. Đây là lịch sử của "
    "những gì đã mua xong.</li>",
    "<li>Đơn còn Nháp, đang Chờ duyệt, đã duyệt mà chưa nhận hàng, hoặc đã Hủy thì <strong>chưa được tính</strong>. Đây là "
    "lịch sử của những gì hàng đã về.</li>")
FROZEN = (
    "<li>Số liệu đã ghi thì <strong>giữ nguyên mãi mãi</strong>. Sau này giá trong danh mục có đổi, tên nhà cung cấp có "
    "sửa, con số của lần mua cũ vẫn y như lúc đó.</li>",
    "<li>Khi dòng hàng <strong>chưa Hoàn thành</strong>, lần mua trong lịch sử <strong>đi theo đơn</strong>: đơn được sửa "
    "đơn giá, số lượng hay VAT thì lịch sử đổi theo; dòng bị hủy, đơn bị hủy, bị Hủy duyệt hoặc bị xóa thì lần mua đó rút "
    "khỏi lịch sử.</li>\n"
    "  <li>Khi dòng hàng <strong>Hoàn thành</strong>, số liệu được <strong>chốt và giữ nguyên mãi mãi</strong>. Sau này giá "
    "trong danh mục có đổi, tên nhà cung cấp có sửa, con số của lần mua đó vẫn y như lúc chốt.</li>\n"
    "  <li>Đơn đã duyệt cần đổi đơn giá (kể cả khi hàng đã về): người có quyền duyệt bấm <strong>Sửa giá</strong> trên "
    "chi tiết đơn mua hàng (dòng đã Hoàn thành thì không sửa giá được). Giá mới đi vào lịch sử của lần mua đó.</li>")
#  Mục 6: câu báo trống.
EMPTY_NOTE = (
    "mặt hàng hoặc nhà cung cấp này chưa có lần mua nào hoàn tất. Đơn đang chạy dở chưa được tính vào đây.",
    "mặt hàng hoặc nhà cung cấp này chưa có lần mua nào đã nhận hàng. Đơn chưa duyệt, hoặc đã duyệt mà hàng chưa về, "
    "chưa được tính vào đây.")

#  (thẻ cha, tiêu đề bài, [cặp cũ → mới], [đoạn nối cuối bài])
EDITS = [
    (STAFF, TITLE, [WHEN_RECORDED, NOT_COUNTED, FROZEN, EMPTY_NOTE], []),
]


def main() -> None:
    p = argparse.ArgumentParser(description="Vá bài HDSD Lịch sử mua hàng theo luật ghi từ lúc nhận hàng (bao-CR-795)")
    p.add_argument("--dry-run", action="store_true", help="chỉ in bài nào đổi gì, không ghi")
    args = p.parse_args()
    db = SessionLocal()
    touched = []
    try:
        for parent_title, title, pairs, appends in EDITS:
            parent = (db.query(HelpArticle)
                      .filter(HelpArticle.parent_id.is_(None), HelpArticle.title == parent_title).first())
            row = parent and (db.query(HelpArticle)
                              .filter(HelpArticle.parent_id == parent.id, HelpArticle.title == title).first())
            if not row:
                print(f"BỎ QUA '{title}': không thấy bài dưới thẻ '{parent_title}' trên hệ này")
                continue
            content, notes = apply_edits(row.content or "", pairs, appends)
            changed = content != (row.content or "")
            print(f"{'ĐỔI' if changed else 'giữ'} #{row.id} '{title}' (dưới '{parent_title}')")
            for note in notes:
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
