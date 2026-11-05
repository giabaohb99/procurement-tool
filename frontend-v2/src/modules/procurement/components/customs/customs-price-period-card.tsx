import { formatQuantity } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'

import type { CustomsSeriesPoint } from '../../types/customs'
import { formatUsd } from '../../utils/customs'

interface CustomsPricePeriodCardProps {
  point: CustomsSeriesPoint & { isBest: boolean }
  /** Nhãn đơn vị của biểu đồ (kg, lít…). */
  unit: string
  /** "p25 – p75" đã định dạng — biểu đồ tự tính, thẻ chỉ bày, để hai nơi không lệch nhau. */
  commonRange: string
  /** Câu ghi chú của kỳ (giá tốt nhất / ít dữ liệu / không có dữ liệu) — cùng câu với cột Ghi chú. */
  note: string
}

/**
 * Một KỲ của bảng số liệu dưới biểu đồ giá, ở khổ điện thoại. Bảng 9 cột (~1.300px) chỉ thấy
 * *Kỳ · Số dòng* trong khung 322px — đúng hai thứ ít ai cần nhất.
 *
 * ⚠️ **Bình quân gia quyền là số to nhất thẻ**, đứng cùng hàng tên kỳ: biểu đồ vẽ chính đường
 * này, người xem thẻ là để đọc lại con số của một điểm trên đường đó. Thấp nhất / khoảng phổ
 * biến / cao nhất xếp lưới NHÃN – SỐ bên dưới, giữ đủ 4 số lẻ như bảng.
 *
 * ⚠️ **Kỳ giá tốt nhất tô viền + chữ xanh** (bảng tô nền cả hàng): ở danh sách thẻ, nền xanh một
 * thẻ giữa hai thẻ trắng đọc ra như thẻ đang được chọn.
 */
export function CustomsPricePeriodCard({ point, unit, commonRange, note }: CustomsPricePeriodCardProps) {
  const priceUnit = unit ? `USD/${unit}` : 'USD'
  const stats = [
    { label: 'Thấp nhất', value: formatUsd(point.min) },
    { label: 'Phổ biến (25–75%)', value: commonRange },
    { label: 'Cao nhất', value: formatUsd(point.max) },
    { label: 'Số dòng', value: String(point.count) },
    { label: `Tổng lượng${unit ? ` (${unit})` : ''}`, value: point.count ? formatQuantity(point.qty) : '—' },
  ]

  return (
    <div className={cn('space-y-1.5', point.isBest && 'rounded-md border border-success/40 p-2')}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-medium text-foreground">{point.label}</span>
        <span className="text-right whitespace-nowrap">
          <span className="text-sm font-semibold tabular-nums">{formatUsd(point.wavg)}</span>{' '}
          <span className="text-xs text-muted-foreground">{priceUnit} BQ</span>
        </span>
      </div>

      <dl className="grid grid-cols-1 gap-y-0.5 text-xs">
        {stats.map((stat) => (
          <div key={stat.label} className="flex justify-between gap-2">
            <dt className="text-muted-foreground">{stat.label}</dt>
            <dd className="text-right tabular-nums">{stat.value}</dd>
          </div>
        ))}
      </dl>

      {note && (
        <p className={cn('text-xs', point.isBest ? 'font-medium text-success' : 'text-muted-foreground')}>
          {note}
        </p>
      )}
    </div>
  )
}
