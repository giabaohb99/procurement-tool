# -*- coding: utf-8 -*-
"""Seed Trung tâm trợ giúp: bài "Chi tiết YC mua hàng — soát dòng chưa mua, tiến độ từng dòng, xuất Excel" (bao-CR-691, 29/10/2026).

Phiếu TK28102602 (Dego Organic) cần một bảng liệt kê MỌI dòng hàng của mọi YCMH, kể cả dòng chưa tạo đơn, kèm tiến độ phía
đơn mua hàng, để đếm số dòng theo trạng thái và kéo Excel. Màn Chi tiết YC mua hàng đã làm việc đó từ bao-CR-691; trước đó
Trung tâm trợ giúp CHƯA có bài nào cho màn này. Bài đặt dưới nhóm "Dành cho Nhân viên Mua hàng", ngay sau bài "Tiến độ
đơn mua hàng" (sort_order 4) để hai màn tiến độ đứng cạnh nhau như trên menu.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_chi_tiet_yc_mua_hang.py --dry-run
    docker compose exec -T api python scripts/seed_help_chi_tiet_yc_mua_hang.py

Idempotent: có bài cùng tiêu đề dưới đúng nhóm thì ghi đè nội dung, giữ chỗ. Thêm mới thì chen vào sort_order 5 và đẩy các
bài 5..49 của nhóm xuống một bậc (bài sort 50+ là cố ý nằm cuối, không đụng). Nội dung phải KHỚP
`doc/tai-lieu-chuc-nang/08-he-thong-bao-cao.md` mục "Màn Chi tiết YC mua hàng" và hành vi thật của
`frontend-v2/src/modules/procurement/components/report-pr-lines-tab.tsx` (v2) / `frontend/src/components/PrLinesReport.tsx` (thumua).
"""
from help_seed_common import HelpArticle, SessionLocal, ref, reindex_articles

PARENT_TITLE = "Dành cho Nhân viên Mua hàng"
TITLE = "Chi tiết YC mua hàng: soát dòng chưa mua, tiến độ từng dòng, xuất Excel"
AFTER_TITLE = "Tiến độ đơn mua hàng"
INSERT_ORDER = 5

SUMMARY = ("Bảng liệt kê mọi dòng hàng của mọi yêu cầu mua hàng, kể cả dòng chưa tạo đơn; lọc nhiều tiến độ dòng, "
           "cột đơn mua hàng ghép sẵn, xuất Excel theo bộ lọc")

CONTENT = f"""<h2>Màn này để làm gì</h2>
<p><strong>Chi tiết YC mua hàng</strong> liệt kê <strong>từng dòng hàng</strong> của <strong>mọi</strong> yêu cầu mua hàng trong phạm vi bạn
được xem. Khác với {ref(AFTER_TITLE, "Tiến độ đơn mua hàng")} (chỉ bắt đầu từ lúc đã có đơn), màn này có cả những dòng <strong>chưa tạo đơn</strong>
và <strong>chưa đặt hàng</strong> — nên dùng nó khi cần trả lời: <em>phiếu này còn dòng nào chưa mua? cả tháng còn bao nhiêu dòng chưa ai đặt?</em></p>
<p>Vào menu <strong>Thu mua</strong>, mục <strong>Chi tiết YC mua hàng</strong> đứng ngay dưới <em>Tiến độ đơn mua hàng</em>. Cùng bảng này còn nằm trong
<em>Báo cáo mua hàng</em>, tab <em>Chi tiết YC mua hàng</em>. Cần quyền xem yêu cầu mua hàng; phạm vi dòng theo đúng phạm vi phiếu bạn được xem.</p>

<h2>Đọc một dòng</h2>
<p>Mỗi hàng là <strong>một dòng hàng</strong> của một phiếu. Hai cột trạng thái đứng cạnh nhau, đừng nhầm:</p>
<table>
<thead><tr><th>Cột</th><th>Nghĩa</th></tr></thead>
<tbody>
<tr><td><strong>Tiến độ dòng</strong></td><td>Dòng này đã mua tới đâu: <em>Chưa tạo đơn mua hàng</em> → <em>Chưa đặt hàng</em> → <em>Đã đặt hàng</em> → <em>Đã nhận hàng</em> → <em>Hoàn thành</em>; dòng bị <em>Hủy đơn</em> hiện riêng. Tự cập nhật theo đơn mua hàng, không sửa tay.</td></tr>
<tr><td><strong>Trạng thái phiếu</strong></td><td>Trạng thái của cả yêu cầu mua hàng (nháp, chờ duyệt, đã duyệt, đang mua…). Phiếu đã duyệt vẫn có thể còn dòng <em>Chưa tạo đơn</em>.</td></tr>
</tbody>
</table>
<p>Ba cột tiến độ hiện sẵn: <strong>SL đã đặt</strong>, <strong>SL đã nhận</strong> và <strong>Mã ĐMH</strong>. Ô Mã ĐMH liệt kê mọi đơn đã lên cho dòng đó theo ngày tạo;
bấm một mã là mở danh sách Đơn mua hàng đã lọc sẵn theo mã ấy (không có quyền xem đơn thì chỉ hiện chữ). Dòng chưa có đơn thì ba ô này trống.</p>

<h2>Cột ẩn, bật khi cần</h2>
<p>Bảng có thêm 16 cột <strong>ẩn mặc định</strong>, bật ở menu <strong>Cột</strong> trên thanh công cụ (bảng nhớ lựa chọn của bạn):</p>
<ul>
<li><strong>Thông tin phiếu:</strong> Pháp nhân · Mục đích · Gấp · Ngày cần (phiếu) · Trưởng bộ phận · Người duyệt · Phòng xử lý.</li>
<li><strong>Thông tin dòng:</strong> ĐVT · Ngày cần (dòng) · Chi tiết tiến độ · Ghi chú dòng · NCC đề xuất.</li>
<li><strong>Phía đơn mua hàng:</strong> Số đơn · NCC đơn gần nhất · Hẹn giao gần nhất · Số lần nhận hàng.</li>
</ul>
<p>Hai cột nhà cung cấp chỉ có với người được xem nhà cung cấp; người khác không thấy chúng cả trong menu Cột. Ô máy chủ không có dữ liệu in dấu gạch ngang.</p>
<p>Trên <em>thumua.degoholding.vn</em> (bản cũ) chỉ hiện ba cột tiến độ; các cột còn lại lấy qua Xuất Excel.</p>

<h2>Lọc và đếm theo trạng thái</h2>
<ol>
<li>Ô <strong>Tiến độ dòng</strong> tick được <strong>nhiều</strong> giá trị cùng lúc; không tick gì là tất cả. Lựa chọn <em>Chưa được đặt hàng (gộp)</em> = <em>Chưa tạo đơn</em> + <em>Chưa đặt hàng</em>, dùng để soi sót nhanh.</li>
<li>Kết hợp ô <strong>Công ty</strong>, <strong>Năm</strong> (đầu trang) với <strong>Trạng thái phiếu</strong>, <strong>NSTM</strong> và ô tìm <em>Mã hàng / tên SP / mã PYC</em>. Gõ mã phiếu vào ô tìm để xem riêng một phiếu — ví dụ một phiếu 23 dòng sẽ thấy ngay dòng nào còn <em>Chưa tạo đơn</em>.</li>
<li>Số dòng của bộ lọc hiện ở chân bảng. Muốn số theo tháng, bộ phận, nhóm hàng, NSTM thì mở bản <strong>biểu đồ</strong> ở phân hệ Báo cáo, mục <em>Chi tiết YC mua hàng</em>.</li>
</ol>

<h2>Xuất Excel</h2>
<p>Nút <strong>Xuất Excel</strong> trên thanh công cụ tải đúng các dòng đang lọc, <strong>không</strong> theo trang, có đủ mọi cột kể cả cột đang ẩn. Cần quyền xuất báo cáo.
Tối đa 5.000 dòng một lần — quá thì màn báo, hãy thu hẹp bộ lọc (chọn năm, công ty hoặc tiến độ dòng) rồi xuất lại. Tệp <code>chi-tiet-yc-mua-hang-theo-dong-&lt;ngày&gt;.xlsx</code>, cột xếp theo thứ tự phiếu → dòng → đơn, tiến độ ghi bằng nhãn tiếng Việt.</p>

<h2>Lưu ý</h2>
<ul>
<li>Đơn mua hàng không ghi dòng yêu cầu nguồn; bảng ghép đơn theo <strong>mã phiếu + mã hàng</strong>. Một phiếu có hai dòng cùng một mã hàng thì cả hai dòng cùng hiện chung tập đơn — tự tách theo số lượng.</li>
<li>Đơn đã hủy, đã xóa và dòng đơn bị hủy không được tính vào SL đã đặt, số đơn hay NCC.</li>
<li>Số liệu lấy thẳng từ dữ liệu hiện tại, không chụp lại: vừa tạo đơn xong tải lại là thấy ngay.</li>
</ul>"""


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Seed bài HDSD Chi tiết YC mua hàng (bao-CR-691)")
    p.add_argument("--dry-run", action="store_true", help="chỉ in sẽ làm gì, không ghi")
    args = p.parse_args()
    db = SessionLocal()
    try:
        parent = db.query(HelpArticle).filter(HelpArticle.parent_id.is_(None), HelpArticle.title == PARENT_TITLE).first()
        if parent is None:
            print(f"BỎ QUA: không có thẻ cha '{PARENT_TITLE}' trên hệ này")
            return
        row = db.query(HelpArticle).filter(HelpArticle.parent_id == parent.id, HelpArticle.title == TITLE).first()
        print(f"  {'cập nhật' if row else f'thêm ở sort_order {INSERT_ORDER}'}: '{TITLE}' (dưới '{PARENT_TITLE}')")
        if args.dry_run:
            print("Thử xong, chưa ghi gì.")
            return
        if row is None:
            siblings = db.query(HelpArticle).filter(HelpArticle.parent_id == parent.id).all()
            for s in siblings:
                if INSERT_ORDER <= (s.sort_order or 0) < 50:
                    s.sort_order = (s.sort_order or 0) + 1
            row = HelpArticle(parent_id=parent.id, title=TITLE, sort_order=INSERT_ORDER)
            db.add(row)
        row.summary, row.content = SUMMARY, CONTENT
        db.flush()
        article_id = row.id
        db.commit()
    finally:
        db.close()
    reindex_articles([article_id])
    print("Xong.")


if __name__ == "__main__":
    main()
