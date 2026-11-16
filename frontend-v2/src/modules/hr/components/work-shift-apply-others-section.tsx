import { ChevronDown } from 'lucide-react'
import type { ReactNode } from 'react'

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/shared/ui/collapsible'
import { cn } from '@/shared/utils/cn'

interface WorkShiftApplyOthersSectionProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Số ngày / người chọn THÊM (không tính ô đang mở). */
  extraDates: number
  extraEmployees: number
  /** Tổng ô của lượt lưu (người × ngày, gồm ô đang mở). */
  cells: number
  /** Câu chặn lượt áp; bày cả khi phần này đang gập để người dùng biết vì sao nút Lưu tắt. */
  warning: string | null
  children: ReactNode
}

/** "Thêm 3 ngày · 2 người → tổng 8 ô"; không chọn thêm gì → `null`. */
function describeApplySelection(extraDates: number, extraEmployees: number, cells: number): string | null {
  const parts = [extraDates > 0 && `${extraDates} ngày`, extraEmployees > 0 && `${extraEmployees} người`].filter(Boolean)
  if (parts.length === 0) return null
  return `Thêm ${parts.join(' · ')} → tổng ${cells} ô`
}

/**
 * Mục gập "Áp cùng ca cho ngày / người khác (tùy chọn)" trong THÂN hộp xếp ca (duoc-CR-761 — thay nút bật ở chân hộp
 * mà đại ca chê khó hiểu). Mặc định gập; có chọn thêm thì dòng tóm tắt hiện ngay dưới tiêu đề kể cả khi gập, và nút
 * chính ở chân hộp đổi thành "Lưu cho N ô".
 */
export function WorkShiftApplyOthersSection({
  open,
  onOpenChange,
  extraDates,
  extraEmployees,
  cells,
  warning,
  children,
}: WorkShiftApplyOthersSectionProps) {
  const summary = describeApplySelection(extraDates, extraEmployees, cells)
  return (
    <Collapsible open={open} onOpenChange={onOpenChange} className="space-y-2 border-t pt-3">
      <CollapsibleTrigger className="group flex w-full items-center gap-2 rounded-md py-1 text-left text-sm outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50">
        <span className="font-medium">Áp cùng ca cho ngày / người khác</span>
        <span className="text-muted-foreground">(tùy chọn)</span>
        <ChevronDown
          aria-hidden
          className={cn('ml-auto size-4 shrink-0 text-muted-foreground transition-transform', open && 'rotate-180')}
        />
      </CollapsibleTrigger>
      {summary && <p className="text-xs font-medium text-shift tabular-nums dark:text-foreground">{summary}</p>}
      {warning && summary && (
        <p role="alert" className="text-xs text-destructive">
          {warning}
        </p>
      )}
      <CollapsibleContent>{children}</CollapsibleContent>
    </Collapsible>
  )
}
