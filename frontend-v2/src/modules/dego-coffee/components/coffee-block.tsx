import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { Card } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'

interface CoffeeBlockProps {
  icon: LucideIcon
  title: ReactNode
  /** Nút/bộ lọc nằm bên phải tiêu đề block. */
  actions?: ReactNode
  /** Màu icon — mặc định amber (màu nhận diện phân hệ Dego Coffee). */
  iconClassName?: string
  className?: string
  children: ReactNode
}

/**
 * Thẻ BLOCK chuẩn của phân hệ Dego Coffee — theo case UI **C-03** (khuôn trang
 * chi tiết Đặt xe/Duyệt dấu): tiêu đề = icon lucide màu theme + nhãn
 * `font-medium`, gạch dưới KÉO HẾT bề ngang thẻ (`-mx-5 px-5 border-b` bù `p-5`
 * của Card), `-mt-1` cho padding tiêu đề 16px. Mọi bảng/khối của phân hệ bọc
 * bằng thẻ này để các màn nhìn cùng một giọng.
 */
export function CoffeeBlock({
  icon: Icon,
  title,
  actions,
  iconClassName = 'text-amber-600 dark:text-amber-400',
  className,
  children,
}: CoffeeBlockProps) {
  return (
    <Card className={cn('gap-0 p-5 pb-4', className)}>
      <div className="-mx-5 -mt-1 mb-4 flex items-center justify-between gap-2 border-b px-5 pb-3">
        <span className="inline-flex items-center gap-2 font-medium">
          <Icon className={cn('size-5', iconClassName)} />
          {title}
        </span>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      {children}
    </Card>
  )
}
