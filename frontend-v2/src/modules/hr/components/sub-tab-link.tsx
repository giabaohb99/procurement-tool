import { Link } from 'react-router-dom'

import { cn } from '@/shared/utils/cn'

/**
 * Một tab gạch chân dạng LINK — dải tab Thiết lập của Nhân sự (duoc-CR-753) và các thanh chuyển màn khác của phân hệ.
 * Tách khỏi `leave-section-tabs.tsx` khi dải tab con Loại nghỉ / Lịch ngày lễ / Ngày cấm nghỉ gộp vào dải Thiết lập.
 */
export function SubTabLink({
  to,
  children,
  active,
}: {
  to: string
  children: React.ReactNode
  active: boolean
}) {
  return (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={cn(
        //  `-mb-px` để gạch chân của tab đè lên đúng đường viền dưới của thanh,
        //  không nằm cách nó một pixel.
        '-mb-px shrink-0 border-b-2 px-1 pb-2 text-sm font-medium transition-colors',
        active
          ? 'border-primary text-foreground'
          : 'border-transparent text-muted-foreground hover:text-foreground',
      )}
    >
      {children}
    </Link>
  )
}
