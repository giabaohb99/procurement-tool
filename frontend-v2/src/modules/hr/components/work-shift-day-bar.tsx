import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'
import { formatHourLabel, formatHourRanges, HOURS_PER_DAY, mergeRanges } from '../utils/work-shift-hours'

/** Mốc vạch dưới thanh: màn rộng "06:00", điện thoại "06" cho khỏi dính chữ. */
const TICKS = [0, 6, 12, 18, 24]

const pct = (hour: number) => `${(hour / HOURS_PER_DAY) * 100}%`
const pad2 = (hour: number) => String(hour).padStart(2, '0')

interface WorkShiftDayBarProps {
  /**
   * Các khung theo ĐÚNG thứ tự dòng đang hiện — số trong khối khớp số tròn ở đầu dòng. `invalid` (dòng đang báo lỗi,
   * vd trùng giờ) tô đỏ trong suốt nên phần chồng nhau đậm lên và số của cả hai khối vẫn đọc được.
   */
  segments: readonly { start: number; end: number; invalid?: boolean }[]
}

/**
 * THANH NGÀY 00:00–24:00 của hộp xếp ca (duoc-CR-761, bản làm lại 16/11/2026): rãnh thấp nền mờ, mỗi khung là một
 * khối màu ca phủ kín chiều cao rãnh, ghi SỐ khung (chữ trắng) chứ không ghi giờ; rê chuột / Tab vào khối hiện
 * "08:00 – 12:00". Vạch mốc dính mép dưới rãnh, nhãn ngay dưới vạch (mốc đầu căn trái, mốc cuối căn phải cho khỏi tràn).
 * Vị trí khối tính theo dữ liệu nên dùng `style` (luật styling cho phép).
 */
export function WorkShiftDayBar({ segments }: WorkShiftDayBarProps) {
  const merged = mergeRanges(segments.map((s) => [s.start, s.end]))
  const label = merged.length === 0 ? 'Nghỉ cả ngày' : formatHourRanges(merged)
  return (
    <div role="group" aria-label={`Khung giờ trong ngày: ${label}`}>
      <div className="relative h-6 overflow-hidden rounded-md bg-muted">
        {segments.map((seg, i) => {
          if (seg.end <= seg.start) return null
          //  Hai khung chạm nhau (08–10 và 10–12) vẫn là hai khối: vạch nền mảnh ở mép trái khối sau.
          const touches = segments.some((other, j) => j !== i && other.end === seg.start)
          const range = `${formatHourLabel(seg.start)} – ${formatHourLabel(seg.end)}`
          return (
            <IconTooltip key={i} label={range}>
              <span
                tabIndex={0}
                aria-label={`Khung ${i + 1}: ${range}`}
                style={{ left: pct(seg.start), width: pct(seg.end - seg.start) }}
                className={cn(
                  'absolute inset-y-0 flex items-center justify-center overflow-hidden bg-shift text-[11px] font-semibold text-shift-foreground tabular-nums outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset',
                  touches && 'border-l-2 border-background',
                  seg.invalid && 'bg-destructive/70',
                )}
              >
                {i + 1}
              </span>
            </IconTooltip>
          )
        })}
        {merged.length === 0 && (
          <span aria-hidden className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
            Nghỉ cả ngày
          </span>
        )}
      </div>
      <div aria-hidden className="relative h-5 text-[11px] leading-none text-muted-foreground tabular-nums">
        {TICKS.map((hour) => (
          <span
            key={hour}
            style={{ left: pct(hour) }}
            className={cn(
              'absolute top-0 flex flex-col gap-0.5',
              hour === 0 ? 'items-start' : hour === HOURS_PER_DAY ? '-translate-x-full items-end' : '-translate-x-1/2 items-center',
            )}
          >
            <span className="h-1.5 w-px bg-border" />
            <span className="max-md:hidden">{formatHourLabel(hour)}</span>
            <span className="md:hidden">{pad2(hour)}</span>
          </span>
        ))}
      </div>
    </div>
  )
}
