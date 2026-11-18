import { ChevronDown, ChevronUp } from 'lucide-react'
import type { ReactNode } from 'react'

import {
  CardCollapseContext,
  useCardCollapse,
  type CardCollapseState,
} from '@/shared/hooks/use-card-collapse'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

/**
 * Bọc một vùng để mọi thẻ dùng chung bên trong (`FormCard`, khung người báo tin, Lịch sử thao tác) có
 * nút gập / mở ở góc phải tiêu đề (duoc-CR-772, Trang cá nhân). `scope` là tiền tố khóa nhớ trạng thái;
 * `null` = tắt gập cho cả vùng (vd màn lập chứng từ MỚI của Thu mua, duoc-CR-780: ô bắt buộc không được nằm
 * trong thẻ đang gập).
 */
export function CardCollapseScope({ scope, children }: { scope: string | null; children: ReactNode }) {
  return <CardCollapseContext.Provider value={scope}>{children}</CardCollapseContext.Provider>
}

/**
 * Gọi `useCardCollapse` ở BÊN TRONG phạm vi rồi trao trạng thái cho thẻ dựng thẳng trong thân trang
 * (duoc-CR-780). Trang chi tiết tự đặt `CardCollapseScope` nên hook gọi ở chính hàm trang thì đọc phải
 * ngữ cảnh BÊN NGOÀI phạm vi (luôn `null`, không gập được) — tách lượt gọi xuống đây là đủ.
 */
export function WithCardCollapse({
  title,
  children,
}: {
  title: string
  children: (collapse: CardCollapseState) => ReactNode
}) {
  return children(useCardCollapse(title))
}

interface CardCollapseToggleProps {
  title: string
  open: boolean
  onToggle: () => void
  /** Vd `ml-auto` khi tiêu đề thẻ không có cụm nút nào bên phải để đẩy nút sang góc. */
  className?: string
}

/**
 * Nút chevron của thẻ: MỞ thì mũi tên LÊN (bấm để thu gọn), GẬP thì mũi tên XUỐNG.
 *
 * ⚠️ `type="button"`: thẻ có thể nằm trong `<form>` — thiếu `type` thì bấm gập là gửi biểu mẫu
 * (bẫy thứ ba của duoc-CR-317).
 */
export function CardCollapseToggle({ title, open, onToggle, className }: CardCollapseToggleProps) {
  const Icon = open ? ChevronUp : ChevronDown
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className={cn('size-7 shrink-0 text-muted-foreground', className)}
      aria-expanded={open}
      aria-label={open ? `Thu gọn ${title}` : `Mở ${title}`}
      onClick={onToggle}
    >
      <Icon className="size-4" />
    </Button>
  )
}
