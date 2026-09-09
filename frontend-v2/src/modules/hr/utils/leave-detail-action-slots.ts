/**
 * Hai «chỗ đứng» của nút trên dải tiêu đề màn chi tiết đơn nghỉ phép, ở khổ
 * ĐIỆN THOẠI. Khai một chỗ vì cụm nút do HAI tệp cùng dựng — trang chi tiết
 * (`leave-request-detail-page.tsx`) và `leave-detail-decision-actions.tsx` —
 * nên chép tay hai bản là sớm muộn hai bên xếp lệch nhau.
 *
 * ⚠️ **Bốn nút bằng vai nhau là bốn khối trắng, không phải một cụm hành động**
 * (khách báo 09/09/2026). Bản trước xếp chúng thành lưới 2×2 đều tăm tắp: mắt
 * không biết bấm cái nào, mà cả bốn cùng to nên nút xanh cũng chẳng nổi hơn.
 * Chữa bằng CẤP BẬC chứ không bằng màu: **đúng MỘT nút chính** trải hết hàng
 * trên, mọi nút còn lại co lại chia đều hàng dưới.
 *
 * Cả hai chỉ áp dưới `md`. Từ `md` trở lên cụm nút vẫn là một hàng ngang bám
 * mép phải như cũ — chỗ đó rộng, không cần phân tầng.
 */

/**
 * NÚT CHÍNH — việc mà người mở màn này định làm ("Duyệt đơn", "Gửi duyệt").
 *
 * `order-first` chứ không đổi thứ tự trong mã: thứ tự DOM còn phải đúng cho khổ
 * rộng và cho trình đọc màn hình theo nhóm chức năng. `basis-full` đẩy mọi nút
 * sau nó xuống hàng kế — đó là cách duy nhất bắt một hàng flex ngắt đúng chỗ mà
 * không phải chẻ cụm nút thành hai thẻ bọc.
 */
export const PRIMARY_ACTION_SLOT = 'max-md:order-first max-md:basis-full'

/**
 * NÚT PHỤ — chia đều phần còn lại của hàng.
 *
 * `px-2` dưới `md`: ba nút phụ trên màn 360px chỉ còn ~100px mỗi nút, mà phần
 * đệm mặc định của `Button` là 16px mỗi bên. Bóp phần đệm chứ KHÔNG bóp chiều
 * cao — 36px đã là mức thấp nhất còn bấm trúng bằng ngón tay.
 */
export const SECONDARY_ACTION_SLOT = 'max-md:flex-1 max-md:px-2'
