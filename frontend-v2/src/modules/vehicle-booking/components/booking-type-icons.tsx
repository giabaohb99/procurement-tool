/**
 * Hai dấu hiệu cho hai loại yêu cầu. Xe con theo dáng lucide-car; xe tải giao hàng
 * vẽ tay theo hình khách chỉ định. Cả hai cùng viewBox 0 0 24 24 + strokeWidth 2
 * để đặt cạnh nhau khớp khổ. Nhận `currentColor` để đổi màu theo chữ, kích thước
 * bằng Tailwind ở nơi dùng (`className="size-6"`).
 */
interface IconProps {
  className?: string
}

/** Xe con — đặt xe công tác (chở người). Dùng dáng lucide-car, viewBox 0 0 24 24
 *  đồng bộ với icon giao hàng (cùng khổ, cùng strokeWidth). */
export function CarBookingIcon({ className }: IconProps) {
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
      <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2" />
      <circle cx="7" cy="17" r="2" />
      <path d="M9 17h6" />
      <circle cx="17" cy="17" r="2" />
    </svg>
  )
}

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
