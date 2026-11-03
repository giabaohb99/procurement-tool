import { cn } from '@/shared/utils/cn'

/**
 * Một ô số ngày của ma trận Quỹ phép "Theo nhân sự" (duoc-CR-717).
 *
 * `undefined` (người không có dòng quỹ loại đó) hiện "—" mờ, KHÁC số `0` (có quỹ nhưng đã dùng
 * hết — thứ phải đập vào mắt nên in rõ). Số âm (ứng phép quá quỹ, duoc-CR-715
 * `max_negative_days`) tô đỏ. Làm tròn 2 số lẻ: `8` chứ không `8.00`, `0.83` chứ không `0.8333…`;
 * màu xét SAU khi làm tròn để `-0.001` không ra một chữ "0" màu đỏ.
 */
export function MatrixDayCell({ value, strong = false }: { value: number | undefined; strong?: boolean }) {
  if (value === undefined) {
    return (
      <span className="text-muted-foreground/40" title="Chưa có quỹ loại nghỉ này">
        —
      </span>
    )
  }
  //  `+ 0` gỡ số `-0` (Math.round(-0.001 * 100) ra -0, String(-0) vẫn là "0" nhưng `< 0` thì không).
  const rounded = Math.round(value * 100) / 100 + 0
  return (
    <span className={cn('tabular-nums', strong && 'font-semibold', rounded < 0 && 'text-destructive')}>
      {String(rounded)}
    </span>
  )
}
