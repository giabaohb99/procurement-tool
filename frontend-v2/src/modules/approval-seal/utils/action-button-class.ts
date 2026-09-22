/**
 * Lớp phủ thêm cho MỌI nút viền trên dải nút của màn chi tiết phiếu đóng dấu.
 *
 * Vì sao cần: nút viền của shadcn dùng nền `bg-background`, trùng đúng nền trang,
 * nên thứ duy nhất mắt bắt được là cái viền xám mảnh. Đứng cạnh một nút tô đặc
 * (Duyệt · Gửi duyệt), vùng màu của nút đặc phủ trọn 36px còn nút viền chỉ hiện
 * ra một khung rỗng — hai nút CÙNG cao 36px, cùng padding, cùng cỡ chữ (đo trên
 * trình duyệt) nhưng người dùng đọc ra "nút Duyệt to hơn". Cho nút viền một nền
 * xám nhạt là đủ để hai khối màu cân nhau, không phải đụng vào chiều cao.
 *
 * ⚠️ CỐ Ý chỉ áp cho màn này (đại ca chốt 22/09/2026) — `shared/ui/button.tsx`
 * giữ nguyên bản shadcn. Nghĩa là màn Đặt xe · Nghỉ phép · Thu mua vẫn kiểu cũ;
 * đừng "sửa cho đồng bộ" bằng cách chép hằng này sang module khác, muốn đổi cả
 * app thì đổi ở biến `outline` của `button.tsx` rồi xóa hằng này đi.
 *
 * ⚠️ Áp cho CẢ DẢI, kể cả nút «…» và «Lưu nháp». Chỉ tô vài nút trong hàng thì
 * chính hàng nút đó lại có hai kiểu nền, tức là đổi một chỗ lệch lấy một chỗ
 * lệch khác.
 */
export const SEAL_OUTLINE_BTN = 'bg-muted/40 hover:bg-muted'
