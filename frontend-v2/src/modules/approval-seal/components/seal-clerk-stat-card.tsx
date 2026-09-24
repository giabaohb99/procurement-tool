import type { LucideIcon } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'

/**
 * Bốn tông màu của dải thẻ đếm.
 *
 * ⚠️ **Tông màu là NGHĨA của con số, không phải trang trí** — và nó phải khớp
 * với huy hiệu cùng nghĩa ở trong bảng: xanh lá = Đang hoạt động, hổ phách =
 * Nghỉ phép, chàm = Văn thư tổng. Đổi ở đây thì đổi cả `status-pill.tsx`.
 *
 * ⚠️ **KHÔNG dùng `ring` cho trạng thái ĐANG CHỌN.** Trong hệ này `ring` là
 * ngôn ngữ của TIÊU ĐIỂM BÀN PHÍM (`focus-visible:ring`) — thẻ đang chọn mà
 * cũng đeo vòng sáng thì hai nghĩa chồng lên nhau, và cái vòng mờ quanh thẻ đọc
 * ra như một ô nhập đang được bấm vào chứ không như một bộ lọc đang bật.
 *
 * ⚠️ **Cũng KHÔNG dùng thanh nhấn dọc màu đặc** (đã dựng rồi bỏ, 22/09/2026):
 * một vệt 4px `bg-primary` chạy dọc mép thẻ là mảng màu bão hòa nhất trang, nó
 * cắt ngang góc bo và đọc ra như lỗi hiển thị. Dải thẻ này nằm NGAY DƯỚI tiêu
 * đề trang và phải đứng yên; thứ cần nổi lên là con số, không phải cái khung.
 *
 * Trạng thái chọn nay nói bằng ba chi tiết nhỏ, cộng lại thì rõ mà không chói:
 *   · viền đổi sang màu tông (đậm hơn viền thường một bậc),
 *   · nền tô CỰC nhạt cùng tông,
 *   · ô biểu tượng đậm lên và nhãn đổi từ xám sang màu tông, in đậm.
 */
const TONES = {
  primary: {
    //  Thẻ TỔNG cố ý để số màu chữ thường: nó không phải một trạng thái, chỉ là
    //  cái mốc để ba con số kia so vào. Tô màu nốt thì cả dải bốn màu, không còn
    //  màu nào nổi lên nữa.
    value: 'text-navy dark:text-foreground',
    icon: 'text-primary',
    iconBox: 'bg-primary/10',
    iconBoxActive: 'bg-primary/20',
    activeLabel: 'text-primary',
    hover: 'hover:border-primary/35',
    active: 'border-primary/45 bg-primary/[0.04]',
  },
  indigo: {
    value: 'text-indigo-600 dark:text-indigo-400',
    icon: 'text-indigo-600 dark:text-indigo-400',
    iconBox: 'bg-indigo-500/10',
    iconBoxActive: 'bg-indigo-500/20',
    activeLabel: 'text-indigo-700 dark:text-indigo-300',
    hover: 'hover:border-indigo-500/35',
    active: 'border-indigo-500/45 bg-indigo-500/[0.05]',
  },
  emerald: {
    value: 'text-emerald-600 dark:text-emerald-400',
    icon: 'text-emerald-600 dark:text-emerald-400',
    iconBox: 'bg-emerald-500/10',
    iconBoxActive: 'bg-emerald-500/20',
    activeLabel: 'text-emerald-700 dark:text-emerald-300',
    hover: 'hover:border-emerald-500/35',
    active: 'border-emerald-500/45 bg-emerald-500/[0.05]',
  },
  amber: {
    value: 'text-amber-600 dark:text-amber-400',
    icon: 'text-amber-600 dark:text-amber-400',
    iconBox: 'bg-amber-500/10',
    iconBoxActive: 'bg-amber-500/20',
    activeLabel: 'text-amber-700 dark:text-amber-300',
    hover: 'hover:border-amber-500/35',
    active: 'border-amber-500/45 bg-amber-500/[0.05]',
  },
} as const

export type SealClerkStatTone = keyof typeof TONES

interface SealClerkStatCardProps {
  label: string
  value: number
  /** Chữ đứng sau con số ("nhân sự", "văn thư tổng"…). */
  unit: string
  icon: LucideIcon
  tone: SealClerkStatTone
  active: boolean
  onClick: () => void
}

/**
 * Một thẻ trong dải đếm của màn Phân công văn thư — ĐỒNG THỜI là **bộ lọc**.
 *
 * ⚠️ Dựng bằng `<button>` chứ không phải `<div onClick>` (sửa 22/09/2026): bốn
 * thẻ này là bộ lọc DUY NHẤT của trang sau khi bỏ dải chip trùng chức năng, nên
 * không tới được bằng bàn phím nghĩa là không lọc được bằng bàn phím. `<button>`
 * cho sẵn tiêu điểm, phím Enter/Space và `aria-pressed` để trình đọc màn hình
 * đọc ra thẻ nào đang bật.
 *
 * Tách thành tệp riêng vì bản cũ chép nguyên khối JSX bốn lần trong trang (~80
 * dòng); đổi một chi tiết là phải nhớ sửa đủ bốn chỗ.
 */
export function SealClerkStatCard({
  label,
  value,
  unit,
  icon: Icon,
  tone,
  active,
  onClick,
}: SealClerkStatCardProps) {
  const t = TONES[tone]

  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className="rounded-xl text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      <Card
        className={cn(
          'h-full gap-3 p-4 transition-colors',
          t.hover,
          active ? t.active : 'border-border',
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 flex-col gap-1">
            <span
              className={cn(
                'truncate text-xs font-medium transition-colors',
                active ? cn(t.activeLabel, 'font-semibold') : 'text-muted-foreground',
              )}
            >
              {label}
            </span>

            <div className="flex items-baseline gap-1.5">
              <span className={cn('text-2xl font-bold leading-none tabular-nums', t.value)}>
                {value}
              </span>
              <span className="truncate text-xs text-muted-foreground">{unit}</span>
            </div>
          </div>

          {/*  Biểu tượng nằm trong ô bo tròn tô nhạt cùng tông — giữ nguyên ở cả
              hai trạng thái, chỉ đậm thêm khi thẻ đang chọn. Đây là chỗ MANG MÀU
              của thẻ: có nó rồi thì nền thẻ không cần tô đậm để tỏ ra "đang
              bật", mà nền đậm mới là thứ làm dải thẻ trông thô. */}
          <span
            className={cn(
              'flex size-8 shrink-0 items-center justify-center rounded-lg transition-colors',
              active ? t.iconBoxActive : t.iconBox,
            )}
          >
            <Icon className={cn('size-4', t.icon)} />
          </span>
        </div>
      </Card>
    </button>
  )
}
