# -*- coding: utf-8 -*-
"""Vá chữ tên nút trong các bài HDSD Thu mua DỰNG TAY cho khớp màn sau duoc-CR-741 (09/11/2026).

Thu mua v2 đổi nhãn nút / hộp xác nhận về đúng chữ bản v1 (nguồn: mục *Bảng nhãn đã đổi* của
`doc/erp/thu-mua/plans/261109-dong-bo-ten-nut-v1-v2-duoc-cr-741/plan.md`). Cây trợ giúp Thu mua được
dựng TAY trên giao diện, không có script sở hữu, nên script này KHÔNG xóa / dựng lại cây. Nó chỉ:
  1. tìm bài theo TIÊU ĐỀ dưới thẻ cha (thẻ gốc) theo TIÊU ĐỀ — id ở local, dev, prod khác nhau;
  2. thay đúng các cụm chữ cũ → mới khai ở `EDITS`; cụm nào không có trong bài thì báo *không khớp* và bỏ qua;
  3. cặp mà chữ mới CHỨA chữ cũ (chèn thêm câu sau một câu có sẵn) chỉ áp khi chữ mới chưa nằm trong bài,
     nên chạy lại bao nhiêu lần cũng vô hại;
  4. nạp lại kho vector cho đúng các bài vừa đổi (như `seed_help_thu_mua_cap_nhat.py`).
Bài người dùng tự viết hay đoạn không nằm trong danh sách cặp không bao giờ bị đụng.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_thu_mua_doi_ten_nut_cr741.py --dry-run   # in bài nào đổi gì
    docker compose exec -T api python scripts/seed_help_thu_mua_doi_ten_nut_cr741.py

Nội dung phải khớp tài liệu chức năng `doc/erp/thu-mua/chuc-nang/10..13` và cẩm nang trợ lý
`app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md`.
"""
import argparse

from help_seed_common import HelpArticle, SessionLocal, reindex_articles

REQUESTER = "Dành cho Người yêu cầu"
APPROVER = "Dành cho TBP phê duyệt yêu cầu"
STAFF = "Dành cho Nhân viên Mua hàng"

# ── Cặp dùng chung ────────────────────────────────────────────────────────────────────────────────
#  Nút xóa trên chi tiết YCMH / YCBG / Phiếu khảo sát nay ghi *Xóa phiếu* (bản v1).
DELETE_DOC = ("<strong>Xóa</strong>", "<strong>Xóa phiếu</strong>")
ADD_ON_LIST = ("<strong>+ Thêm mới</strong>", "<strong>+ Thêm</strong>")

EXPORT_LI = ("<li>Ô tìm này áp cho cả nút <strong>Xuất Excel</strong> — lọc xong rồi bấm Xuất thì file chỉ có "
             "đúng những phiếu đang thấy.</li>")
EXPORT_TICKED = (EXPORT_LI, EXPORT_LI + "<li>Chỉ cần vài phiếu thì tick ô đầu dòng: nút đổi thành <strong>Xuất "
                 "Excel (n)</strong> và file chỉ có đúng n phiếu đã tick. Đổi trang hay lọc lại thì các ô tick tự bỏ.</li>")

CLONE_FROM_LIST = (
    "chọn phiếu đó rồi nhấn <strong>Nhân bản</strong> — hệ thống tạo bản sao ở trạng thái Nháp.",
    "bấm <strong>Nhân bản</strong> ở đầu danh sách để hiện cột <em>Thao tác</em>, bấm <strong>Nhân bản</strong> trên "
    "dòng phiếu đó rồi đồng ý ở hộp <em>Nhân bản phiếu</em> — hệ thống tạo bản sao ở trạng thái Nháp. Bấm "
    "<strong>Xong</strong> để ẩn cột.")

PR_LINE_TOOLS = (
    "<h3>Bước 3 — Lưu và gửi duyệt</h3>",
    "<p><strong>Thao tác trên bảng dòng hàng</strong> (khi phiếu đang sửa): nút <strong>Thêm nhiều dòng</strong> dưới "
    "bảng thêm một lượt nhiều dòng trống; cuối mỗi dòng có ba biểu tượng <em>Chi tiết</em> (mở popup chi tiết dòng), "
    "<em>Nhân đôi</em> (chèn bản sao ngay dưới dòng đó) và <em>Xóa</em>. Trong popup chi tiết dòng, "
    "khi cả khối <em>Hình ảnh SP (gốc)</em> lẫn khối <em>File đính kèm (đối chiếu)</em> đều có ảnh thì có thêm nút "
    "<strong>So sánh</strong> để xem hai ảnh cạnh nhau.</p><h3>Bước 3 — Lưu và gửi duyệt</h3>")

NEED_STILL = ("<li><strong>Nếu vẫn cần mua:</strong> dùng <strong>Nhân bản</strong> để tạo phiếu Nháp mới rồi gửi "
              "duyệt lại.</li>")
PR_TO_SURVEY = (NEED_STILL, NEED_STILL + "<li><strong>Cần khảo sát lại giá:</strong> bấm <strong>Tạo yêu cầu báo "
                "giá</strong> ở đầu trang (cần quyền tạo Yêu cầu báo giá). Form Yêu cầu báo giá mới mở ra, điền sẵn các "
                "dòng của phiếu này; kiểm lại rồi Lưu. Phiếu <em>Bị trả lại</em> cũng có nút này.</li>")

DISPATCH_PAIRS = [
    ("Quản lý Thu mua cần bấm <strong>Duyệt điều phối</strong> để phân bổ",
     "Quản lý Thu mua cần bấm <strong>Duyệt</strong> (hộp <em>Duyệt điều phối</em>) để phân bổ"),
    ("Quản lý Thu mua đã bấm Duyệt điều phối,", "Quản lý Thu mua đã bấm <strong>Duyệt</strong> để điều phối,"),
    ("(bấm Duyệt điều phối)", "(bấm <strong>Duyệt</strong>, hộp <em>Duyệt điều phối</em>)"),
    ("thực hiện <strong>Duyệt điều phối</strong>", "bấm <strong>Duyệt</strong> để điều phối"),
]

PO_DOC_STATUS = (
    "<li><strong>Trạng thái hồ sơ chứng từ:</strong> Chọn từ danh sách (Chưa có chứng từ / Đã có thông tin chứng từ / "
    "Đã đủ chứng từ). Kế toán dùng để theo dõi hồ sơ vật lý.</li>",
    "<li><strong>Trạng thái hồ sơ chứng từ:</strong> không nằm ở phần thông tin chung. Chọn ở tiêu đề thẻ chứng từ "
    "của đơn: bấm vào chữ <em>Hồ sơ chứng từ:</em> để mở menu (Chưa có chứng từ / Đã có thông tin chứng từ / Đã đủ "
    "chứng từ), chọn xong là ghi ngay. Kế toán dùng để theo dõi hồ sơ vật lý.</li>")

PO_BUTTONS_HTML = """<h3>Các nút trên đơn mua hàng</h3>
<ul>
<li>Đơn mới: bấm <strong>Tạo</strong> để lưu đơn lần đầu. Đơn đã có: <strong>Lưu</strong> giữ nháp, <strong>Gửi duyệt</strong> lưu rồi gửi luôn.</li>
<li>Ngày dự kiến có hàng của dòng lệch với Yêu cầu mua hàng nguồn thì lúc lưu hiện hộp <em>Lệch ngày dự kiến có hàng</em>: <strong>Vẫn lưu</strong> hoặc <strong>Quay lại sửa</strong>. Yêu cầu mua hàng không tự đổi theo.</li>
<li>Thẻ dòng hàng có nút <strong>Thêm nhiều</strong>: nhập số dòng (mặc định 3) để thêm một lượt dòng trống. Trong popup chi tiết dòng có các nút <strong>Tạm ngưng</strong>, <strong>Tiếp tục</strong>, <strong>Hủy</strong> cho riêng dòng đó.</li>
<li><strong>Hủy</strong> hủy cả đơn, bắt nhập lý do (nút trong hộp ghi <strong>Hủy đơn</strong>). Đơn đã có dòng <em>Hoàn thành</em> thì không còn nút này.</li>
<li><strong>Xóa đơn</strong> xóa hẳn đơn còn <em>Nháp</em> hoặc <em>Bị trả lại</em>. <strong>Hoàn thành</strong> và <strong>Mở lại</strong> luôn hỏi lại trước khi làm.</li>
<li>Thẻ chứng từ: nút <strong>Chuỗi chứng từ (PYC/PKS)</strong> mở tệp của cả chuỗi phiếu liên quan; mỗi mục có nút <strong>Upload thêm file cho mục này</strong>.</li>
</ul>"""

SURVEY_PROCESS_HTML = """<h3>4. Xử lý khảo sát trên Yêu cầu báo giá</h3>
<ul>
<li>Ở màn <strong>Xử lý khảo sát</strong>, kho báo giá đã duyệt cho tick nhiều dòng một lúc: tick xong bấm <strong>Thêm n dòng đã chọn làm option</strong> để gắn cả nhóm làm phương án cho dòng đang xử lý.</li>
<li>Gỡ một phương án đã gắn: bấm biểu tượng <strong>Xóa option</strong>, hộp hỏi lại trước khi xóa. Người yêu cầu đang chọn phương án đó thì xóa sẽ bỏ luôn lựa chọn của họ.</li>
<li><strong>Chốt hoàn thành khảo sát</strong> luôn hỏi lại. Còn dòng chưa có phương án nào thì hộp <em>Chốt rỗng sản phẩm chưa có phương án</em> mở ra: tick các dòng chốt rỗng rồi bấm <strong>Chốt (n chốt rỗng)</strong>.</li>
<li>Nút <strong>Quay lại</strong> ở đầu màn đưa về đúng phiếu Yêu cầu báo giá đang mở.</li>
</ul>"""

SURVEY_APPROVE = (
    "Quản lý sẽ so sánh và nhấn nút <strong>Duyệt</strong> trên giao diện",
    "Quản lý sẽ so sánh và nhấn nút <strong>Duyệt</strong> (hộp hỏi lại, bấm <strong>Duyệt phiếu</strong>) trên giao diện")

# ── Nhân bản cả phiếu chỉ còn ở màn DANH SÁCH (bỏ khỏi trang chi tiết từ duoc-CR-737) ────────────────
#  Các cặp này chạy SAU `DELETE_DOC` nên khớp theo chữ đã đổi (*Xóa phiếu*).
CLONE_NOT_ON_DETAIL = (" · <strong>Xóa phiếu</strong> · <strong>Nhân bản</strong>.", " · <strong>Xóa phiếu</strong>.")
CLONE_SENTENCE = ("<strong>Nhân bản</strong> để tạo phiếu", "<strong>Nhân bản</strong> ở màn danh sách để tạo phiếu")
CLONE_STATUS_CELL = ("Nhân bản tạo phiếu mới</", "Nhân bản ở màn danh sách tạo phiếu mới</")
_CLONE_WHERE = ("Bấm ở màn danh sách (nút <strong>Nhân bản</strong> ở đầu trang bật cột <em>Thao tác</em>), trang chi tiết "
                "không có nút này. ")
CLONE_ROW_PR = ("Tạo phiếu Nháp mới sao chép nội dung.", _CLONE_WHERE + "Tạo phiếu Nháp mới sao chép nội dung.")
CLONE_ROW_SR = ("Tạo một phiếu Nháp mới sao chép nội dung phiếu hiện tại.",
                _CLONE_WHERE + "Tạo một phiếu Nháp mới sao chép nội dung phiếu đã chọn.")

#  (thẻ cha, tiêu đề bài, [cặp cũ → mới], [(dấu nhận đã có, đoạn HTML nối cuối bài)])
EDITS = [
    (REQUESTER, "Yêu cầu mua hàng", [DELETE_DOC, PR_LINE_TOOLS, CLONE_ROW_PR], []),
    (APPROVER, "Yêu cầu mua hàng (TBP)", [DELETE_DOC, PR_LINE_TOOLS, CLONE_ROW_PR], []),
    (REQUESTER, "Xử lý yêu cầu mua hàng",
     [DELETE_DOC, CLONE_NOT_ON_DETAIL, PR_TO_SURVEY, CLONE_SENTENCE, *DISPATCH_PAIRS], []),
    (APPROVER, "Xử lý yêu cầu mua hàng (TBP)",
     [DELETE_DOC, CLONE_NOT_ON_DETAIL, PR_TO_SURVEY, CLONE_SENTENCE, *DISPATCH_PAIRS], []),
    (REQUESTER, "Trạng thái yêu cầu mua hàng", [*DISPATCH_PAIRS, EXPORT_TICKED], []),
    (APPROVER, "Trạng thái yêu cầu mua hàng (TBP)", [*DISPATCH_PAIRS, EXPORT_TICKED], []),
    (REQUESTER, "Yêu cầu báo giá", [DELETE_DOC, CLONE_FROM_LIST, CLONE_ROW_SR], []),
    (APPROVER, "Yêu cầu báo giá (TBP)", [DELETE_DOC, CLONE_FROM_LIST, CLONE_ROW_SR], []),
    (REQUESTER, "Xử lý yêu cầu báo giá", [DELETE_DOC, CLONE_NOT_ON_DETAIL, CLONE_SENTENCE], []),
    (APPROVER, "Xử lý yêu cầu báo giá (TBP)", [DELETE_DOC, CLONE_NOT_ON_DETAIL, CLONE_SENTENCE], []),
    (REQUESTER, "Trạng thái yêu cầu báo giá", [EXPORT_TICKED, CLONE_SENTENCE, CLONE_STATUS_CELL], []),
    (APPROVER, "Trạng thái yêu cầu báo giá (TBP)", [EXPORT_TICKED, CLONE_SENTENCE, CLONE_STATUS_CELL], []),
    (STAFF, "Khảo sát & Phiếu khảo sát", [ADD_ON_LIST, SURVEY_APPROVE],
     [("Xử lý khảo sát trên Yêu cầu báo giá", SURVEY_PROCESS_HTML)]),
    (STAFF, "Đơn mua hàng (PO)", [ADD_ON_LIST, PO_DOC_STATUS], [("Các nút trên đơn mua hàng", PO_BUTTONS_HTML)]),
]


def apply_edits(content: str, pairs, appends) -> tuple[str, list[str]]:
    """Trả nội dung mới + từng dòng nhật ký cho bản in (đổi / đã có / không khớp)."""
    notes = []
    for old, new in pairs:
        short = old if len(old) <= 70 else old[:67] + "..."
        #  Cặp CHÈN (chữ mới chứa chữ cũ): phần chèn thêm đã nằm trong bài thì coi như đã áp — kể cả khi
        #  một cặp sau đã sửa tiếp câu gốc làm `new` không còn nguyên văn.
        added = [part for part in new.split(old, 1) if part] if old in new else []
        if (old in new and new in content) or (added and all(part in content for part in added)):
            notes.append(f"đã có: {short}")
        elif old not in content:
            notes.append(f"đã có: {short}" if new in content else f"không khớp: {short}")
        else:
            notes.append(f"đổi {content.count(old)} chỗ: {short}")
            content = content.replace(old, new)
    for marker, html in appends:
        if marker in content:
            notes.append(f"đã có đoạn: {marker}")
        else:
            notes.append(f"nối đoạn: {marker}")
            content = content.rstrip() + "\n" + html
    return content, notes


def main() -> None:
    p = argparse.ArgumentParser(description="Vá tên nút Thu mua trong bài HDSD dựng tay (duoc-CR-741)")
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
