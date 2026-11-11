# -*- coding: utf-8 -*-
"""Nạp bài HDSD luật sắp xếp cột dùng chung toàn ERP v2 (duoc-CR-744) dưới thẻ "Bắt đầu" — MỘT LỆNH, chạy lại vô hại.

Thẻ "Bắt đầu" dựng TAY trên giao diện (không có script sở hữu) nên chỉ thêm / ghi đè đúng bài cùng tiêu đề,
không xóa hay dựng lại cây — khuôn chung ở `help_seed_common.upsert_articles`, nạp luôn kho vector bài vừa ghi.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_sap_xep_cot_cr744.py --dry-run
    docker compose exec -T api python scripts/seed_help_sap_xep_cot_cr744.py

Nội dung phải khớp mã: chu kỳ bấm ở `frontend-v2/src/shared/data-table/data-table.tsx` (tăng → giảm → thôi; cột
thời gian giảm trước), ô trống xuống cuối + khóa phụ `id` ở `backend/app/core/sort_order.py`, trạng thái theo dòng
đời ở `backend/app/core/code_rank_sql.py`, và luật §8 của `.claude/rules/chung-dat-ten-va-quy-uoc.md`.
"""
from help_seed_common import run_article_upsert

START_ROOT = "Bắt đầu"
TITLE = "Sắp xếp bảng danh sách bằng cách bấm tiêu đề cột"

CONTENT = """<h2>Sắp xếp bảng danh sách bằng cách bấm tiêu đề cột</h2>
<p>Mọi bảng danh sách trong ERP (YCMH, ĐMH, Công nợ, Nghỉ phép, Văn bản, Tồn kho, Đặt phòng họp…) xếp được bằng cách
<strong>bấm vào tên cột</strong> ở hàng tiêu đề. Cột xếp được có biểu tượng mũi tên mờ bên cạnh tên cột.</p>

<h3>1. Bấm mấy lần thì ra gì</h3>
<table>
<thead><tr><th>Lần bấm</th><th>Cột thường</th><th>Cột ngày giờ (Ngày tạo, Ngày cập nhật…)</th></tr></thead>
<tbody>
<tr><td>Lần 1</td><td>Xếp <strong>tăng dần</strong> (A → Z, nhỏ → lớn), mũi tên chỉ lên</td><td>Xếp <strong>mới nhất trước</strong>, mũi tên chỉ xuống</td></tr>
<tr><td>Lần 2</td><td>Xếp <strong>giảm dần</strong>, mũi tên chỉ xuống</td><td>Xếp <strong>cũ nhất trước</strong></td></tr>
<tr><td>Lần 3</td><td colspan="2">Thôi xếp theo cột đó, bảng về thứ tự mặc định của màn</td></tr>
</tbody>
</table>
<p>Bôi đen tên cột để chép thì <strong>không</strong> tính là bấm xếp.</p>

<h3>2. Bảng xếp theo đúng chữ bạn đang thấy</h3>
<ul>
<li><strong>Cột tên</strong> (Nhà cung cấp, Người đặt, Bên ký kết…) xếp theo <strong>tên</strong> hiện trong ô, không theo mã ngầm phía sau.</li>
<li><strong>Cột trạng thái</strong> xếp theo <strong>thứ tự các bước</strong> của phiếu (ví dụ Nháp → Chờ duyệt → Đã duyệt), không theo chữ cái.
Cột Hiệu lực của Hợp đồng xếp <em>Hết hạn → Sắp hết hạn → Còn hiệu lực → Không thời hạn</em>.</li>
<li><strong>Cột số tính ra</strong> (SL nhận, còn lại, thành tiền…) xếp theo đúng con số trong ô. Số <strong>0</strong> là một giá trị như mọi số khác.</li>
</ul>

<h3>3. Ô trống luôn nằm cuối</h3>
<p>Dòng chưa có giá trị ở cột đang xếp (ô hiện trống hoặc dấu gạch) luôn nằm <strong>cuối bảng</strong>, dù bạn xếp tăng hay giảm.
Nhờ vậy dòng có dữ liệu luôn nằm trên cùng, không bị một đám ô trống che mất.</p>

<h3>4. Xếp trên toàn bộ dữ liệu, sang trang không lặp dòng</h3>
<ul>
<li>Bảng có nhiều trang thì máy chủ xếp <strong>toàn bộ</strong> dữ liệu rồi mới chia trang, không chỉ xếp riêng trang đang xem.</li>
<li>Nhiều dòng cùng giá trị (ví dụ cùng một trạng thái) vẫn có thứ tự cố định, nên chuyển trang qua lại
<strong>không có dòng nào lặp lại hay biến mất</strong>.</li>
<li><strong>Xuất Excel</strong> ra file theo đúng thứ tự đang thấy trên bảng.</li>
</ul>

<h3>5. Bảng dòng hàng bên trong một phiếu</h3>
<p>Bảng dòng hàng trong chi tiết YCMH, YCBG, ĐMH, phiếu giao hàng, phiếu khảo sát, chi phí nhập khẩu, YCTT cũng bấm tiêu đề cột để xếp.
Thứ tự <strong>chốt lúc bạn bấm</strong>: đang sửa số trong một ô thì dòng đó không tự nhảy chỗ. Muốn xếp lại theo số vừa sửa thì bấm tiêu đề cột lần nữa.</p>

<h3>6. Khi nào không bấm xếp được</h3>
<table>
<thead><tr><th>Hiện tượng</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Cột không có mũi tên, bấm không đổi gì</td><td>Cột đó không có thứ tự hợp lý (ví dụ cột nút thao tác, cột ghi chú dài)</td><td>Dùng ô tìm hoặc bộ lọc thay cho xếp</td></tr>
<tr><td>Cột bị che (ví dụ Nhà cung cấp, thông tin nhạy cảm của nhân sự) và không xếp được</td><td>Bạn chưa có quyền xem cột đó. Thứ tự dòng cũng đủ để đoán ra giá trị bị che, nên hệ khóa luôn việc xếp</td><td>Cần xem thì xin quản trị cấp quyền</td></tr>
<tr><td>Màn Phiếu đặt phòng họp: phiếu chờ bạn duyệt đứng đầu dù chưa xếp gì</td><td>Đó là thứ tự mặc định: việc đang chờ bạn lên trước</td><td>Bấm một cột bất kỳ thì bảng xếp theo cột đó</td></tr>
<tr><td>Bấm xếp xong mà thứ tự nhìn vẫn sai</td><td>Lỗi của màn đó</td><td>Chụp màn hình kèm tên cột, báo quản trị</td></tr>
</tbody>
</table>"""

ARTICLES = [
    (START_ROOT, TITLE,
     "Bấm tên cột để xếp tăng, giảm, rồi thôi; ô trống luôn nằm cuối, trạng thái xếp theo thứ tự các bước, "
     "sang trang không lặp dòng, Excel xuất cùng thứ tự; cột bị che theo quyền thì không xếp được.",
     CONTENT),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD sắp xếp cột duoc-CR-744 + kho vector")
