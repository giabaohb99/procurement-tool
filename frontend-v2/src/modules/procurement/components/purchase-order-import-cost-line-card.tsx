import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { importCostTypeLabel, type PurchaseOrderImportCost } from '../types/purchase-order-detail'

/** Số của một giai đoạn (Dự toán · Tạm tính · Quyết toán), đã quy đổi VNĐ. */
export interface ImportCostStageFigure {
  label: string
  /** `null` = giai đoạn chưa ai nhập số — khác với "0 đ". */
  amount: number | null
  /** Màu nhãn trùng màu cột trên bảng / khối trong popup (bao-CR-473). */
  labelClassName: string
}

interface PurchaseOrderImportCostLineCardProps {
  cost: PurchaseOrderImportCost
  index: number
  stages: ImportCostStageFigure[]
  /** Quy đổi VNĐ hiệu lực (đã gồm VAT). */
  baseAmount: number
  /** Ô Đã chi / Còn lại dựng bằng `renderCell` của bảng — luật màu nằm một chỗ. */
  paid: ReactNode
  remaining: ReactNode
  /** Dòng đã quyết toán (đã sinh công nợ) — khóa sửa, muốn sửa phải mở lại. */
  finalized: boolean
  /** Ô tick quyết toán / lập YCTT của bảng; `null` = dòng này không tick được. */
  tick?: ReactNode
  /** Xóa · mở lại dòng — anh em của vùng chạm. */
  actions: ReactNode
  onOpenDetail: () => void
}

/**
 * Một KHOẢN CHI PHÍ thu mua ở khổ điện thoại — thay cho bảng 20 cột.
 *
 * Diễn giải lên dòng đầu (rỗng thì lấy tên loại), NCC nhận tiền xuống dòng phụ
 * với mã màu sky: mười khoản "Cước biển" chỉ phân biệt được bằng diễn giải và
 * người nhận tiền. Ba số giai đoạn giữ đúng màu ba cột trên bảng để người đã quen
 * bảng ở máy tính đọc được ngay.
 *
 * Mọi ô sửa đi qua popup *Chi tiết khoản chi phí* VỐN ĐÃ CÓ (cùng đường với nút
 * bút chì trên bảng) — popup đó đủ cả tỷ giá từng giai đoạn mà bảng không có.
 * Ô tick và nút thao tác là anh em của vùng chạm, không nằm trong nó.
 */
export function PurchaseOrderImportCostLineCard({
  cost,
  index,
  stages,
  baseAmount,
  paid,
  remaining,
  finalized,
  tick,
  actions,
  onOpenDetail,
}: PurchaseOrderImportCostLineCardProps) {
  const typeLabel = cost.cost_type_label || importCostTypeLabel(cost.cost_type)
  const title = cost.description || typeLabel
  const dates = [
    cost.invoice_no && `HĐ ${cost.invoice_no}`,
    cost.invoice_date && formatDate(cost.invoice_date),
    cost.payment_due_date && `hạn ${formatDate(cost.payment_due_date)}`,
  ].filter(Boolean)

  return (
    <div className="flex items-start gap-2 p-3">
      <span className="flex shrink-0 flex-col items-center gap-1.5">
        {tick}
        <span className="text-xs leading-5 tabular-nums text-muted-foreground">{index + 1}.</span>
      </span>

      <button
        type="button"
        onClick={onOpenDetail}
        aria-label={`Chi tiết khoản chi phí ${index + 1}: ${title}`}
        className="block min-w-0 flex-1 space-y-1 text-left"
      >
        <span className="line-clamp-2 block font-medium text-foreground">{title}</span>

        <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
          {cost.description && <span>{typeLabel}</span>}
          {cost.supplier_code ? (
            <span>
              {cost.description && <span aria-hidden="true">· </span>}
              <span className="font-medium text-sky-600 dark:text-sky-400">{cost.supplier_code}</span>
              {cost.supplier_name && <span> {cost.supplier_name}</span>}
            </span>
          ) : (
            <span>{cost.description ? '· ' : ''}chưa chọn NCC</span>
          )}
        </span>

        <span className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs">
          {stages.map((stage) => (
            <span key={stage.label} className="whitespace-nowrap">
              <span className={cn('font-medium', stage.labelClassName)}>{stage.label}</span>{' '}
              <span className="tabular-nums text-muted-foreground">
                {stage.amount === null ? '—' : `${formatMoney(stage.amount)} đ`}
              </span>
            </span>
          ))}
        </span>

        <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span>Quy đổi</span>
          <span className="text-sm font-semibold tabular-nums text-navy dark:text-foreground">
            {formatMoney(baseAmount)} đ
          </span>
          {finalized && (
            <Badge variant="secondary" className="border-0 bg-teal-500/10 text-teal-700 dark:text-teal-300">
              Đã quyết toán
            </Badge>
          )}
        </span>

        {/*  Đã chi chỉ có nghĩa khi khoản đã thành công nợ; Còn lại luôn hiện. */}
        <span className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
          {paid && <span>Đã chi {paid}</span>}
          <span>Còn lại {remaining}</span>
        </span>

        {dates.length > 0 && (
          <span className="block text-xs text-muted-foreground">{dates.join(' · ')}</span>
        )}
      </button>

      <div className="flex shrink-0 items-start gap-0.5">{actions}</div>
    </div>
  )
}
