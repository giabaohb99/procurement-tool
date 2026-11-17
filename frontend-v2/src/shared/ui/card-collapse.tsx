import { ChevronDown, ChevronUp } from 'lucide-react'
import type { ReactNode } from 'react'

import { CardCollapseContext } from '@/shared/hooks/use-card-collapse'
import { Button } from '@/shared/ui/button'

/**
 * Bọc một vùng để mọi thẻ dùng chung bên trong (`FormCard`, khung người báo tin, Lịch sử thao tác) có
 * nút gập / mở ở góc phải tiêu đề (duoc-CR-772, Trang cá nhân). `scope` là tiền tố khóa nhớ trạng thái.
 */
export function CardCollapseScope({ scope, children }: { scope: string; children: ReactNode }) {
  return <CardCollapseContext.Provider value={scope}>{children}</CardCollapseContext.Provider>
}

interface CardCollapseToggleProps {
  title: string
  open: boolean
  onToggle: () => void
}

/**
 * Nút chevron của thẻ: MỞ thì mũi tên LÊN (bấm để thu gọn), GẬP thì mũi tên XUỐNG.
 *
 * ⚠️ `type="button"`: thẻ có thể nằm trong `<form>` — thiếu `type` thì bấm gập là gửi biểu mẫu
 * (bẫy thứ ba của duoc-CR-317).
 */
export function CardCollapseToggle({ title, open, onToggle }: CardCollapseToggleProps) {
  const Icon = open ? ChevronUp : ChevronDown
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="size-7 shrink-0 text-muted-foreground"
      aria-expanded={open}
      aria-label={open ? `Thu gọn ${title}` : `Mở ${title}`}
      onClick={onToggle}
    >
      <Icon className="size-4" />
    </Button>
  )
}
