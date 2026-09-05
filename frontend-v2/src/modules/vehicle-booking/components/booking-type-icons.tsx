import { forwardRef } from 'react'
import type { LucideProps } from 'lucide-react'

/**
 * Hai dấu hiệu cho hai loại yêu cầu — đều vẽ tay theo hình khách chỉ định (lucide
 * không có đúng dáng này): xe con sedan (viewBox 39×28) và xe tải giao hàng
 * (viewBox 24×24). Nhận `currentColor` để đổi màu theo chữ, kích thước bằng
 * Tailwind ở nơi dùng (`className="size-6"`).
 */
interface IconProps {
  className?: string
}

// Dáng xe sedan: thân + 2 bánh xe + trụ kính (cabin). Hệ toạ độ 0..39 × 0..28 nên
// SVG bọc phải khai đúng `viewBox="0 0 39 28"`, không thì path tràn/bị cắt.
const SEDAN_PATH =
  'M11.7532 22.6961H26.4242M11.7532 22.6961C11.7532 24.7162 10.1111 26.3538 8.08548 26.3538C6.05984 26.3538 4.41774 24.7162 4.41774 22.6961M11.7532 22.6961C11.7532 20.6759 10.1111 19.0384 8.08548 19.0384C6.05984 19.0384 4.41774 20.6759 4.41774 22.6961M26.4242 22.6961C26.4242 24.7162 28.0662 26.3538 30.0919 26.3538C32.1176 26.3538 33.7596 24.7162 33.7596 22.6961M26.4242 22.6961C26.4242 20.6759 28.0662 19.0384 30.0919 19.0384C32.1176 19.0384 33.7596 20.6759 33.7596 22.6961M4.41774 22.6961H3.68419C2.65713 22.6961 2.14359 22.6961 1.75131 22.4967C1.40625 22.3214 1.1257 22.0417 0.949873 21.6975C0.75 21.3063 0.75 20.7943 0.75 19.7699V17.5753C0.75 15.5268 0.75 14.5025 1.14977 13.7201C1.50139 13.0319 2.06248 12.4723 2.75262 12.1217C3.53719 11.723 4.56426 11.723 6.61838 11.723H28.6248C29.9877 11.723 30.6692 11.723 31.2394 11.813C34.3782 12.3088 36.84 14.7639 37.3372 17.8941C37.4274 18.4627 37.4274 19.1423 37.4274 20.5015C37.4274 20.8413 37.4274 21.0112 37.4048 21.1533C37.2805 21.9358 36.665 22.5496 35.8803 22.6736C35.7378 22.6961 35.5675 22.6961 35.2267 22.6961H33.7596M15.421 0.75V11.723M4.41774 11.723L5.0257 8.08526C5.46123 5.47925 5.679 4.17624 6.33101 3.19845C6.90577 2.33652 7.71329 1.65431 8.66032 1.23064C9.73468 0.75 11.0593 0.75 13.7085 0.75H19.8793C21.6016 0.75 22.4628 0.75 23.2446 0.986743C23.9367 1.19635 24.5804 1.53995 25.1392 1.99793C25.7704 2.51525 26.2481 3.22985 27.2036 4.65904L31.9258 11.723'

/** Xe con — đặt xe công tác (chở người). Dáng sedan khách chỉ định, viewBox 0 0 39 28. */
export function CarBookingIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 39 28"
      fill="none"
      stroke="currentColor"
      strokeWidth={3}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={SEDAN_PATH} />
    </svg>
  )
}

/**
 * Icon xe sedan cho THẺ phân hệ ở màn chọn phân hệ (launcher). Cùng dáng
 * `CarBookingIcon` nhưng khai đúng `viewBox` để vừa khít ô `size-8` (không tràn),
 * và `strokeWidth={3.25}` để nét dày BẰNG các thẻ lucide khác: thẻ lucide vẽ
 * sw2 trong viewBox24, ở size-8 ra ~2.67px; sedan viewBox39 cần 3.25 để ra đúng
 * 2.67px. Kiểu hợp `LucideIcon` để cắm thẳng vào `ErpModule.icon`.
 */
export const CarTileIcon = forwardRef<SVGSVGElement, LucideProps>(
  ({ className, ...props }, ref) => (
    <svg
      ref={ref}
      {...props}
      viewBox="0 0 39 28"
      fill="none"
      stroke="currentColor"
      strokeWidth={3.25}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={SEDAN_PATH} />
    </svg>
  ),
)
CarTileIcon.displayName = 'CarTileIcon'

/** Xe tải — đặt xe giao hàng (chở hàng). viewBox 0 0 24 24. */
export function DeliveryBookingIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect x="1" y="3" width="15" height="13" />
      <polygon points="16,8 20,8 23,11 23,16 16,16 16,8" />
      <circle cx="5.5" cy="18.5" r="2.5" />
      <circle cx="18.5" cy="18.5" r="2.5" />
    </svg>
  )
}
