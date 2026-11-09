import type { ReactNode } from 'react'

import { formatMoney } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import type { LandedCostType } from '../types/import-landed-cost'

/**
 * Mảnh dựng chung của thẻ giá vốn nhập khẩu (`import-landed-cost-cards.tsx`): lưới
 * nhãn trái - số phải, dòng loại chi phí, khung danh sách, thẻ TỔNG, câu báo rỗng.
 */

export function Figures({ children }: { children: ReactNode }) {
  return <div className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-0.5 text-xs">{children}</div>
}

interface FigureProps {
  label: string
  value: ReactNode
  strong?: boolean
  /** Dòng con (một loại chi phí) thụt vào dưới dòng cha của nó. */
  indent?: boolean
}

export function Figure({ label, value, strong, indent }: FigureProps) {
  return (
    <>
      <span
        className={cn(
          'text-muted-foreground',
          strong && 'font-medium text-foreground',
          indent && 'pl-3',
        )}
      >
        {label}
      </span>
      <span
        className={cn(
          'text-right tabular-nums',
          strong && 'text-sm font-semibold text-navy dark:text-foreground',
        )}
      >
        {value}
      </span>
    </>
  )
}

/** Các loại chi phí KHÁC 0, thụt vào dưới dòng Chi phí nhập khẩu. */
export function CostTypeFigures({
  types,
  byType,
}: {
  types: LandedCostType[]
  byType?: Record<string, number>
}) {
  return types
    .filter((costType) => (byType?.[String(costType.code)] || 0) !== 0)
    .map((costType) => (
      <Figure
        key={costType.code}
        label={`${costType.no}. ${costType.label}`}
        indent
        value={formatMoney(byType?.[String(costType.code)] || 0)}
      />
    ))
}

export function TotalCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5 bg-muted/60 p-3">
      <p className="font-semibold text-foreground">{title}</p>
      {children}
    </div>
  )
}

export function CardList({ children }: { children: ReactNode }) {
  return <div className="divide-y overflow-hidden rounded-lg border">{children}</div>
}

export function EmptyMessage({ message }: { message: string }) {
  return <p className="py-8 text-center text-sm text-muted-foreground">{message}</p>
}
