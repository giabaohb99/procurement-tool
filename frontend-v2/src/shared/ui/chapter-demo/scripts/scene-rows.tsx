import type { ReactNode } from 'react'

import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'

/** Dòng / dòng có ô tick dùng chung cho các cảnh của kịch bản demo (ai-CR-214). */
export function Row({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('flex items-center gap-2 rounded-md border px-2 py-1.5 text-xs', className)}>{children}</div>
}

export function TickRow({ label, checked }: { label: string; checked: boolean }) {
  return (
    <Row className={cn(checked && 'border-primary bg-accent')}>
      <Checkbox checked={checked} aria-label={label} />
      <span>{label}</span>
    </Row>
  )
}
