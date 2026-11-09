import { formatUsd, type CompareRow } from '../../utils/customs'

interface CustomsComparePeriodCardProps {
  row: CompareRow
  /** Tên các mặt hàng đang so, đúng thứ tự `row.values`. */
  terms: string[]
  /** Màu của từng mặt hàng — cùng bộ màu với đường trên biểu đồ ngay phía trên. */
  colors: readonly string[]
  /** Nhãn đơn vị đang so (kg, lít…). */
  unit: string
}

/**
 * Một KỲ của bảng So sánh ở khổ điện thoại. Bảng có 1 + N cột (N = 2–5 mặt hàng, mỗi cột
 * 180px), năm mặt hàng là ~1.000px — khung 322px chỉ thấy kỳ và một mặt hàng.
 *
 * ⚠️ **Mỗi mặt hàng một hàng, có chấm màu của đường biểu đồ**: người so đọc thẻ để tra lại
 * con số của một điểm trên biểu đồ, màu là sợi dây nối hai thứ đó.
 *
 * ⚠️ **Kỳ trống của một mặt hàng ghi gạch ngang**, không bỏ hàng: bỏ đi thì thẻ kỳ này ít hàng
 * hơn thẻ kỳ khác và mắt dò theo vị trí sẽ đọc nhầm sang mặt hàng kế tiếp. Số trong ngoặc là
 * số dòng hàng của kỳ, như ô của bảng.
 */
export function CustomsComparePeriodCard({ row, terms, colors, unit }: CustomsComparePeriodCardProps) {
  const priceUnit = unit ? `USD/${unit}` : 'USD'
  return (
    <div className="space-y-1.5">
      <p className="font-medium text-foreground">{row.label}</p>
      <ul className="space-y-1 text-sm">
        {terms.map((term, index) => {
          const value = row.values[index]
          return (
            <li key={`${index}-${term}`} className="flex items-baseline justify-between gap-3">
              <span className="flex min-w-0 items-center gap-1.5">
                <span
                  aria-hidden
                  className="size-2 shrink-0 rounded-full"
                  style={{ backgroundColor: colors[index] }}
                />
                <span className="min-w-0 break-words">{term}</span>
              </span>
              {value === null || value === undefined ? (
                <span className="text-muted-foreground">—</span>
              ) : (
                <span className="shrink-0 text-right whitespace-nowrap tabular-nums">
                  {formatUsd(value)} {priceUnit}{' '}
                  <span className="text-xs text-muted-foreground">({row.counts[index] ?? 0})</span>
                </span>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
