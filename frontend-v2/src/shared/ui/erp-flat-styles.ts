import { cn } from '@/shared/utils/cn'

/**
 * Bộ lớp «mặt phẳng kiểu ERPNext» dùng chung (duoc-CR-708, gom về đây ở duoc-CR-716): đặt lên KHỐI CHA của một vùng
 * nội dung để mọi thẻ con mất viền / bóng / nền và mọi ô nhập thành ô nền xám không viền — đúng form ERPNext.
 * Dùng ở màn hồ sơ nhân sự và trang chi tiết CRUD bố cục `flat`. Không đặt vào primitive (`card.tsx`, `input.tsx`)
 * vì các màn khác vẫn dùng kiểu thẻ.
 */

/** Thẻ con thành khối phẳng: bỏ viền, bóng, nền, lề trong. */
export const ERP_FLATTEN_CARDS = cn(
  '[&_[data-slot=card]]:gap-4 [&_[data-slot=card]]:rounded-none [&_[data-slot=card]]:border-0',
  '[&_[data-slot=card]]:bg-transparent [&_[data-slot=card]]:p-0 [&_[data-slot=card]]:shadow-none',
  '[&_[data-slot=card-content]]:px-0 [&_[data-slot=card-header]]:px-0',
)

/**
 * Ô nhập NỀN XÁM, không viền: ô thường, ô chữ dài, ô chọn, nút mở lịch / hộp chọn trong ô biểu mẫu. Ô bị khóa vẫn
 * mờ như cũ. Trừ checkbox / switch của Radix (cũng là `<button>`, tô xám bỏ viền là biến mất).
 */
export const ERP_FILLED_FIELDS = cn(
  '[&_button[data-slot=form-control]:not([role=checkbox]):not([role=switch])]:border-transparent [&_button[data-slot=form-control]:not([role=checkbox]):not([role=switch])]:bg-muted [&_button[data-slot=form-control]:not([role=checkbox]):not([role=switch])]:shadow-none',
  //  Ô nằm trong `FormControl` mang `data-slot="form-control"` (Slot đè `data-slot="input"`), nên bắt thêm theo thẻ.
  '[&_input[data-slot=form-control]:not([type=checkbox])]:border-transparent [&_input[data-slot=form-control]:not([type=checkbox])]:bg-muted [&_input[data-slot=form-control]:not([type=checkbox])]:shadow-none',
  '[&_textarea[data-slot=form-control]]:border-transparent [&_textarea[data-slot=form-control]]:bg-muted [&_textarea[data-slot=form-control]]:shadow-none',
  '[&_[data-slot=input]]:border-transparent [&_[data-slot=input]]:bg-muted [&_[data-slot=input]]:shadow-none',
  '[&_[data-slot=textarea]]:border-transparent [&_[data-slot=textarea]]:bg-muted [&_[data-slot=textarea]]:shadow-none',
  '[&_[data-slot=select-trigger]]:border-transparent [&_[data-slot=select-trigger]]:bg-muted [&_[data-slot=select-trigger]]:shadow-none',
  '[&_[data-slot=form-item]_button[aria-haspopup=dialog]]:border-transparent [&_[data-slot=form-item]_button[aria-haspopup=dialog]]:bg-muted [&_[data-slot=form-item]_button[aria-haspopup=dialog]]:shadow-none',
)
