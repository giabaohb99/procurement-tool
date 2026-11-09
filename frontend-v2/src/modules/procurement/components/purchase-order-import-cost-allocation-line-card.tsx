import { ChevronDown, ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'

import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import type { ImportCostAllocationLine } from '../types/purchase-order-detail'
import { percentOf } from '../utils/purchase-order-import-cost'

interface PurchaseOrderImportCostAllocationLineCardProps {
  line: ImportCostAllocationLine
  open: boolean
  onToggle: () => void
  /** Phần bung ra: các khoản chia vào dòng (kèm ô gõ số cho khoản Nhập tay). */
  children?: ReactNode
}

/**
 * Một DÒNG HÀNG của bảng "Chi phí theo dòng hàng" ở khổ điện thoại.
 *
 * Bảng gốc bấm cả dòng để bung chi tiết, nên ở đây cả phần tóm tắt là một nút
 * bung/gập (`aria-expanded`). Phần bung ra nằm NGOÀI nút vì nó có ô nhập số tiền
 * cho khoản chia Nhập tay — ô nhập trong nút là HTML sai và chạm vào ô thì gập
 * mất dòng.
 */
export function PurchaseOrderImportCostAllocationLineCard({
  line,
  open,
  onToggle,
  children,
}: PurchaseOrderImportCostAllocationLineCardProps) {
  const Chevron = open ? ChevronDown : ChevronRight
  return (
    <div className="space-y-2 p-3">
      <button
        type="button"
        aria-expanded={open}
        onClick={onToggle}
        className="flex w-full min-w-0 items-start gap-1.5 text-left"
      >
        <Chevron className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <span className="block min-w-0 flex-1 space-y-1">
          <span className="line-clamp-2 block font-medium text-foreground">
            {line.product_name || line.product_code}
          </span>
          <span className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
            <span className="font-medium text-sky-600 dark:text-sky-400">{line.product_code}</span>
            <span className="tabular-nums">
              <span aria-hidden="true">· </span>
              {formatQuantity(line.qty_order)} {line.unit}
            </span>
            {!!line.weight_kg && (
              <span className="tabular-nums">
                <span aria-hidden="true">· </span>
                {formatQuantity(line.weight_kg)} kg
              </span>
            )}
          </span>
          <span className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs">
            <span className="text-muted-foreground">Tiền hàng</span>
            <span className="text-right tabular-nums">{formatMoney(line.goods_base)} đ</span>
            <span className="text-muted-foreground">Chi phí phân bổ</span>
            <span className="text-right font-semibold tabular-nums text-amber-600 dark:text-amber-500">
              {formatMoney(line.cost_base)} đ
            </span>
            <span className="text-muted-foreground">Tổng giá trị</span>
            <span className="text-right font-semibold tabular-nums">
              {formatMoney(line.landed_base)} đ
            </span>
            <span className="text-muted-foreground">Tỷ lệ chi phí</span>
            <span className="text-right tabular-nums">
              {line.goods_base > 0 ? `${percentOf(line.cost_base, line.goods_base).toFixed(1)}%` : '-'}
            </span>
          </span>
        </span>
      </button>

      {open && <div className="rounded-md bg-muted/40 p-2">{children}</div>}
    </div>
  )
}
