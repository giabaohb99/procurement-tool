import { cn } from '@/shared/utils/cn'

/** Một dòng trong danh sách: nhãn + số đo + màu thanh. */
export interface BarListItem {
  label: string
  value: number
  /**
   * Màu thanh. Truyền TOKEN (`var(--success)`, `CHART_COLORS[0]`…) chứ đừng
   * truyền mã hex thô: hex không đổi theo nền tối và không đi cùng bảng màu
   * chung, chỉnh một chỗ là các trang lệch nhau ngay.
   */
  color?: string
}

interface BarListProps {
  items: BarListItem[]
  /** Định dạng số hiển thị; mặc định là số nguyên theo locale vi-VN. */
  formatValue?: (value: number) => string
  emptyLabel?: string
  className?: string
}

/**
 * Danh sách hạng mục kèm thanh tỉ lệ ngang — dùng khi nhãn DÀI (tên nhà cung
 * cấp, tên phòng ban) và con số cần đọc chính xác chứ không chỉ để so hơn kém.
 *
 * Khác `HorizontalBarChart`: chỗ này không vẽ trục, không tooltip, số ghi thẳng
 * cạnh nhãn — vừa cho thẻ hẹp xếp bốn cột một hàng.
 *
 * Thanh chia tỉ lệ theo GIÁ TRỊ LỚN NHẤT trong danh sách, không theo tổng: các
 * danh sách này đều đã cắt top 5 nên tổng không nói lên điều gì.
 */
export function BarList({
  items,
  formatValue = (value) => value.toLocaleString('vi-VN'),
  emptyLabel = 'Chưa có dữ liệu',
  className,
}: BarListProps) {
  if (items.length === 0) {
    return <p className="py-6 text-center text-xs text-muted-foreground">{emptyLabel}</p>
  }

  const max = Math.max(1, ...items.map((item) => item.value || 0))

  return (
    <ul className={cn('space-y-2.5', className)}>
      {items.map((item) => {
        const pct = Math.min(100, Math.max(0, ((item.value || 0) / max) * 100))

        return (
          <li key={item.label} className="space-y-1">
            <div className="flex items-center justify-between gap-2 text-xs">
              {/* Nhãn là chữ token, KHÔNG tô theo màu thanh: tông nhạt như vàng
                  đọc không nổi trên nền trắng. */}
              <span className="min-w-0 flex-1 truncate font-medium text-foreground" title={item.label}>
                {item.label}
              </span>
              <span className="shrink-0 font-semibold tabular-nums">{formatValue(item.value)}</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-chart-track">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{ width: `${pct}%`, backgroundColor: item.color ?? 'var(--chart-1)' }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
