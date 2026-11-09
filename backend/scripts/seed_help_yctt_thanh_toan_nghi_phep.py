# -*- coding: utf-8 -*-
"""Nạp bài HDSD cho kế toán: Yêu cầu thanh toán sinh từ phiếu thanh toán nghỉ phép (duoc-CR-719).

Cây "Dành cho Kho & Kế toán" (có bài "Công nợ & Yêu cầu thanh toán") được dựng TAY trên giao diện, không script nào
sở hữu, nên script này KHÔNG xóa / dựng lại cây: chỉ thêm hoặc ghi đè đúng bài cùng tiêu đề dưới thẻ cha tìm theo TIÊU
ĐỀ, rồi nạp lại kho vector cho đúng bài đó (RAG tắt thì bỏ qua). Hệ nào không có thẻ cha thì bỏ qua, không đẻ thẻ mới.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_yctt_thanh_toan_nghi_phep.py
    docker compose exec -T api python scripts/seed_help_yctt_thanh_toan_nghi_phep.py --dry-run

⚠️ Phần phía Nhân sự (lập phiếu, duyệt, hủy) nằm ở bài "Thanh toán nghỉ phép" của `seed_help_nghi_phep.py`; tài liệu
chức năng ở `doc/erp/hrm/02-nghi-phep.md` §16 và `doc/erp/thu-mua/chuc-nang/14-yeu-cau-thanh-toan.md`. Ba nơi phải khớp.
Nhãn đối chiếu bằng đọc `finance/components/payment-request-leave-encashment-{view,info-card}.tsx`,
`finance/pages/payment-request-print-page.tsx`, `finance/pages/payment-request-list-page.tsx` và câu báo ở
`payment_request/leave_encashment_payout.py`.
"""
from help_seed_common import ref, run_article_upsert

ACCOUNTING_ROOT = "Dành cho Kho & Kế toán"
LEAVE_ARTICLE = "Thanh toán nghỉ phép"

CONTENT = f"""<h2>Yêu cầu thanh toán nghỉ phép: nhập số tiền và chi</h2>
<p>Khi phòng Nhân sự duyệt một <strong>phiếu thanh toán nghỉ phép</strong> (đổi ngày phép chưa nghỉ ra tiền, cuối năm hoặc khi nghỉ việc), hệ <strong>tự tạo</strong> một <strong>Yêu cầu thanh toán</strong> (YCTT) ở trạng thái <em>Nháp</em>, số tiền 0. Phiếu bên Nhân sự chỉ ghi số ngày; việc của kế toán là nhập số tiền, trình duyệt và chi. Phía Nhân sự đọc ở {ref(LEAVE_ARTICLE, "bài Thanh toán nghỉ phép")}.</p>

<h2>Tìm phiếu ở đâu</h2>
<ul>
<li>Người có quyền duyệt YCTT nhận chuông <em>… — Thanh toán nghỉ phép cần nhập số tiền</em>; bấm chuông là mở thẳng phiếu.</li>
<li>Ở danh sách <strong>Yêu cầu thanh toán</strong>, ô lọc <strong>Loại nợ</strong> chọn <strong>Thanh toán nghỉ phép</strong>.</li>
<li>Trang chi tiết có nhãn <strong>Thanh toán nghỉ phép</strong> cạnh mã phiếu, và thẻ <strong>Thông tin phiếu</strong> ghi <strong>Người nhận</strong> (tên và mã nhân sự), <strong>Phiếu thanh toán nghỉ phép</strong> (mã <code>TTP…</code>), <strong>Nội dung</strong> (số ngày, loại nghỉ, năm, lý do).</li>
</ul>

<h2>Khác YCTT nhà cung cấp ở chỗ nào</h2>
<table>
<thead><tr><th>Việc</th><th>YCTT nghỉ phép</th></tr></thead>
<tbody>
<tr><td>Dòng tiền</td><td>Đúng <strong>một dòng</strong>, nhập ở ô <strong>Số tiền thanh toán</strong>. Không thêm, bớt dòng; không gắn công nợ; không cấn trừ, không trả trước.</td></tr>
<tr><td>Sửa được gì</td><td>Khi còn <em>Nháp</em>: <strong>Số tiền thanh toán</strong>, <strong>Hình thức thanh toán</strong>, <strong>Ghi chú</strong>. Nhớ bấm <strong>Lưu</strong> (hoặc <strong>Gửi duyệt</strong>, hệ lưu rồi gửi).</td></tr>
<tr><td>Gửi duyệt</td><td>Nút <strong>Gửi duyệt</strong> tắt khi số tiền bằng 0 (<em>Nhập số tiền thanh toán trước khi gửi duyệt</em>).</td></tr>
<tr><td>Duyệt, chi</td><td>Như YCTT thường: <strong>Duyệt</strong> hoặc <strong>Từ chối</strong> (bắt ghi lý do) khi đang chờ duyệt; đã duyệt thì bấm <strong>Ghi nhận đã chi</strong>. Ghi nhận đã chi không đụng công nợ nào và không hoàn tác được. Người được thanh toán nhận chuông đã chi.</td></tr>
<tr><td>Xóa, hoàn tiền, cập nhật theo công nợ</td><td><strong>Không có.</strong> YCTT Nháp không bỏ được ở đây; muốn bỏ thì nhờ phòng Nhân sự hủy phiếu thanh toán nghỉ phép (YCTT Nháp tự bị xóa theo).</td></tr>
</tbody>
</table>

<h2>Từ chối thì sao</h2>
<p>Từ chối YCTT thì phiếu thanh toán nghỉ phép bên Nhân sự <strong>vẫn ở Đã duyệt</strong>, hiện băng vàng <strong>Kế toán từ chối chi</strong>; người duyệt và người lập phiếu nhận chuông kèm lý do bạn ghi. Phòng Nhân sự sẽ hủy phiếu để trả ngày về quỹ rồi lập phiếu mới nếu cần, nên ghi lý do rõ ràng (ví dụ sai số ngày). YCTT đã từ chối thì khóa, không mở lại được.</p>
<p>Ngược lại, khi YCTT đang chờ duyệt hoặc đã duyệt, phòng Nhân sự <strong>không hủy được</strong> phiếu thanh toán nghỉ phép; đã chi thì không hủy được nữa.</p>

<h2>Bản in và số tài khoản</h2>
<ul>
<li>Bản in ghi người nhận là <strong>tên (mã) nhân sự</strong> và nội dung <em>Thanh toán tiền nghỉ phép năm … — … ngày</em>.</li>
<li><strong>Chuyển khoản</strong>: dòng <strong>Số TK thụ hưởng</strong> và <strong>Ngân hàng</strong> lấy từ hồ sơ nhân sự <strong>chỉ khi người in được xem thông tin nhạy cảm của nhân sự</strong> (hoặc chính người đó in). Không thì hai dòng in chữ <em>kế toán tự điền</em> để bạn điền tay, không để chấm trống.</li>
<li><strong>Tiền mặt</strong>: hai dòng đó để trống như YCTT thường.</li>
</ul>

<h2>Ai thấy YCTT nghỉ phép</h2>
<p>Số tiền chia cho số ngày ra lương một ngày, nên loại YCTT này <strong>không mở cho mọi người xem YCTT</strong>: phải vừa có quyền <strong>Yêu cầu thanh toán</strong>, vừa có quyền <strong>đọc Thanh toán nghỉ phép</strong> (nhãn <em>Nghỉ phép › Thanh toán nghỉ phép</em>) với phạm vi phủ phiếu nguồn. Nhân viên và quản lý mua hàng không thấy các phiếu này trong danh sách, kể cả khi gõ thẳng đường dẫn.</p>
<p>⚠️ <strong>Không thấy YCTT nghỉ phép nào dù đã có phiếu được duyệt?</strong> Gần như chắc là vai trò Kế toán chưa được tick quyền đó. Quản trị vào <strong>Quản trị ▸ Phân quyền tài khoản</strong>, mở vai trò Kế toán, tick <strong>đọc</strong> ở <em>Nghỉ phép › Thanh toán nghỉ phép</em> với phạm vi <strong>Công ty</strong> (hoặc Tất cả), rồi người dùng đăng xuất và đăng nhập lại. Seed không tự cấp quyền này cho hệ đang chạy.</p>"""

ARTICLES = [
    (ACCOUNTING_ROOT, "Yêu cầu thanh toán nghỉ phép: nhập số tiền và chi",
     "YCTT hệ tự tạo khi phiếu thanh toán nghỉ phép được duyệt: nhập một số tiền, không gửi duyệt được khi bằng 0, "
     "không xóa hay hoàn tiền, khi nào in số tài khoản, ai thấy loại YCTT này",
     CONTENT),
]


if __name__ == "__main__":
    run_article_upsert(ARTICLES, "Nạp bài HDSD YCTT thanh toán nghỉ phép (duoc-CR-719) + kho vector")
