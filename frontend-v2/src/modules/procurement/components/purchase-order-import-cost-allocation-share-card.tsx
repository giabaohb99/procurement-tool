import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface PurchaseOrderImportCostAllocationShareCardProps {
  typeLabel: string
  description: string
  /** "Mã — Tên" hoặc rỗng khi khoản chưa gắn NCC. */
  supplier: string
  /** Cách chia (có thể là chữ cảnh báo "thiếu cơ sở" tô màu). */
  method: ReactNode
  ratio: string
  /** Số tiền chia, hoặc ô nhập số cho khoản Nhập tay. */
  amount: ReactNode
  /** Khoản Nhập tay: tô nền như dòng trên bảng để biết đây là chỗ gõ số. */
  manual?: boolean
}

/**
 * Một KHOẢN chia vào dòng hàng (bảng con trong "Chi phí theo dòng hàng") ở khổ
 * điện thoại. Bảng con 6 cột trong khung đã thụt lề còn chừng 260px nên đổi
 * thành khối: loại + diễn giải lên đầu, NCC và cách chia dòng phụ, tỷ lệ và số
 * tiền (hoặc ô nhập) đứng một hàng bên dưới.
 */
export function PurchaseOrderImportCostAllocationShareCard({
  typeLabel,
  description,
  supplier,
  method,
  ratio,
  amount,
  manual = false,
}: PurchaseOrderImportCostAllocationShareCardProps) {
  return (
    <div className={cn('space-y-1 rounded-md px-2 py-1.5 text-xs', manual && 'bg-warning/8')}>
      <p className="text-sm font-medium">
        {typeLabel}
        {description && <span className="font-normal text-muted-foreground"> · {description}</span>}
      </p>
      <p className="text-muted-foreground">
        {supplier && <span>{supplier} · </span>}
        {method}
      </p>
      <div className="flex items-center justify-between gap-3">
        <span className="tabular-nums text-muted-foreground">Tỷ lệ {ratio}</span>
        <span className="min-w-0 text-right font-medium tabular-nums">{amount}</span>
      </div>
    </div>
  )
}
