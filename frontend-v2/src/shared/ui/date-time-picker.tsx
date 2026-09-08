import { CalendarIcon, X } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'

/**
 * Ô NGÀY-GIỜ hiện `DD/MM/YYYY HH:MM` (24h) trong **một khung** nhưng chia thành các
 * CỤM gõ độc lập (kiểu ô ngày-giờ gốc): bấm vào cụm nào thì bôi xanh 2 số của cụm đó,
 * gõ số chỉ đổi CỤM ĐANG SỬA, đủ số thì tự nhảy cụm kế. Cạnh bên là nút mở lịch + giờ.
 *
 * Thay `<input type="datetime-local">` (vẽ theo locale máy — Windows ra mm/dd/yyyy +
 * AM/PM). **Cảnh báo** khi quá hạng mức (ngày>31, tháng>12, giờ>23, phút>59, ngày
 * không thật) và khi sớm hơn `min` (chặn quá khứ / giao trước lấy hàng).
 *
 * Giá trị vào/ra là chuỗi GIỜ TƯỜNG MINH `yyyy-MM-ddTHH:mm` (giờ Hà Nội GMT+7). Chưa
 * đủ / không hợp lệ → trả `''`.
 */
interface DateTimePickerProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  className?: string
  /** Mốc tối thiểu `yyyy-MM-ddTHH:mm` — khoá ngày quá khứ trên lịch + cảnh báo khi sớm hơn. */
  min?: string
  /** Câu cảnh báo khi sớm hơn `min` (mặc định "Không được ở quá khứ"). */
  minLabel?: string
}

interface Seg {
  da: string
  mo: string
  y: string
  h: string
  mi: string
}

const HOURS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const MINUTES = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))
const pad2 = (s: string) => (s.length === 1 ? `0${s}` : s)

function split(value: string): Seg {
  const [datePart = '', timePart = ''] = value.split('T')
  const [y = '', mo = '', da = ''] = datePart.split('-')
  const [h = '', mi = ''] = timePart.split(':')
  return { da, mo, y, h, mi }
}

function nowLocal(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

/** Ngày (y-mo-da) có thật không — chặn 31/02, 30/02… */
function isRealDate(y: number, mo: number, da: number): boolean {
  const d = new Date(y, mo - 1, da)
  return d.getFullYear() === y && d.getMonth() === mo - 1 && d.getDate() === da
}

interface Warn {
  bad: boolean
  msg: string
}

function rangeWarnings(s: Seg): Warn {
  const num = (x: string) => (x === '' ? null : Number(x))
  const da = num(s.da)
  const mo = num(s.mo)
  const h = num(s.h)
  const mi = num(s.mi)
  const daBad = da !== null && (da < 1 || da > 31)
  const moBad = mo !== null && (mo < 1 || mo > 12)
  const hBad = h !== null && h > 23
  const miBad = mi !== null && mi > 59
  const realBad =
    !daBad && !moBad && s.y.length === 4 && s.da !== '' && s.mo !== '' &&
    !isRealDate(Number(s.y), Number(s.mo), Number(s.da))
  const msgs: string[] = []
  if (daBad) msgs.push('Ngày 1–31')
  if (moBad) msgs.push('Tháng 1–12')
  if (hBad) msgs.push('Giờ 0–23')
  if (miBad) msgs.push('Phút 0–59')
  if (realBad) msgs.push('Ngày không có thật')
  return { bad: daBad || moBad || hBad || miBad || realBad, msg: msgs.join(' · ') }
}

/** Ghép segment → `yyyy-MM-ddTHH:mm`. Thiếu/không hợp lệ → `''`. */
function combine(s: Seg): string {
  if (s.y.length !== 4 || s.da === '' || s.mo === '' || s.h === '' || s.mi === '') return ''
  const da = Number(s.da)
  const mo = Number(s.mo)
  const h = Number(s.h)
  const mi = Number(s.mi)
  if (da < 1 || da > 31 || mo < 1 || mo > 12 || h > 23 || mi > 59) return ''
  if (!isRealDate(Number(s.y), mo, da)) return ''
  return `${s.y}-${pad2(s.mo)}-${pad2(s.da)}T${pad2(s.h)}:${pad2(s.mi)}`
}

/** Ngày `yyyy-MM-dd` cho lịch (bỏ giờ). Thiếu/không hợp lệ → `''`. */
function dateOnly(s: Seg): string {
  if (s.y.length !== 4 || s.da === '' || s.mo === '') return ''
  const da = Number(s.da)
  const mo = Number(s.mo)
  if (da < 1 || da > 31 || mo < 1 || mo > 12 || !isRealDate(Number(s.y), mo, da)) return ''
  return `${s.y}-${pad2(s.mo)}-${pad2(s.da)}`
}

const LEN: Record<keyof Seg, number> = { da: 2, mo: 2, y: 4, h: 2, mi: 2 }

export function DateTimePicker({
  value,
  onChange,
  disabled,
  className,
  min,
  minLabel = 'Không được ở quá khứ',
}: DateTimePickerProps) {
  const [seg, setSeg] = useState<Seg>(() => split(value))
  const [open, setOpen] = useState(false)
  //  THÁNG đang xem của lịch — điều khiển được để "Hôm nay" / mở popover kéo lịch về
  //  đúng tháng (không thì lịch đứng yên ở tháng cũ, chấm "hôm nay" nằm ngoài tầm nhìn).
  const [viewMonth, setViewMonth] = useState<Date>(() => parseLocalDate(dateOnly(split(value))) ?? new Date())

  const iso = combine(seg)
  //  Đồng bộ khi `value` đổi TỪ NGOÀI (nạp phiếu). Bỏ qua lần value quay lại do chính
  //  ô này phát ra (so `iso`) để không xoá cụm đang gõ dở.
  if (useHasChanged(value) && value !== '' && value !== iso) {
    setSeg(split(value))
  }

  const range = rangeWarnings(seg)
  const belowMin = Boolean(min && iso && iso < min)
  const warn = {
    bad: range.bad || belowMin,
    msg: [range.msg, belowMin ? minLabel : ''].filter(Boolean).join(' · '),
  }
  const minDate = min ? parseLocalDate(min.slice(0, 10)) : undefined

  function push(next: Seg) {
    setSeg(next)
    onChange(combine(next))
  }

  function setField(key: keyof Seg, raw: string) {
    push({ ...seg, [key]: raw.replace(/\D/g, '').slice(0, LEN[key]) })
  }

  function pickDate(dateStr: string) {
    const [y = '', mo = '', da = ''] = dateStr.split('-')
    //  KHÔNG đóng popover khi chọn ngày — để người dùng chọn tiếp giờ; chỉ X / bấm ra
    //  ngoài mới đóng.
    push({ ...seg, y, mo, da, h: seg.h || '08', mi: seg.mi || '00' })
  }

  const selected = parseLocalDate(dateOnly(seg))

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      <div className="flex items-center gap-2">
        {/*  KHUNG gộp: viền bọc tất cả cụm, sáng viền khi con trỏ vào cụm bất kỳ. */}
        <div
          className={cn(
            'flex h-9 flex-1 items-center rounded-md border bg-transparent px-2 text-sm shadow-xs',
            'focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50',
            disabled && 'cursor-not-allowed opacity-50',
            warn.bad && 'border-destructive text-destructive focus-within:border-destructive focus-within:ring-destructive/30',
          )}
        >
          <SegBox segKey="da" value={seg.da} placeholder="NN" ariaLabel="Ngày" disabled={disabled} onChange={setField} />
          <Sep>/</Sep>
          <SegBox segKey="mo" value={seg.mo} placeholder="TT" ariaLabel="Tháng" disabled={disabled} onChange={setField} />
          <Sep>/</Sep>
          <SegBox segKey="y" value={seg.y} placeholder="NNNN" ariaLabel="Năm" disabled={disabled} onChange={setField} />
          <Sep className="px-1.5">·</Sep>
          <SegBox segKey="h" value={seg.h} placeholder="GG" ariaLabel="Giờ" disabled={disabled} onChange={setField} />
          <Sep>:</Sep>
          <SegBox segKey="mi" value={seg.mi} placeholder="PP" ariaLabel="Phút" disabled={disabled} onChange={setField} />
        </div>
        <Popover
          open={open}
          onOpenChange={(next) => {
            setOpen(next)
            //  Mở popover → kéo lịch về đúng tháng của ngày đang chọn (nếu có).
            if (next && selected) setViewMonth(selected)
          }}
        >
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="size-9 shrink-0"
              disabled={disabled}
              aria-label="Chọn lịch và giờ"
            >
              <CalendarIcon className="size-4 opacity-60" />
            </Button>
          </PopoverTrigger>
          <PopoverContent
            className="w-auto p-0"
            align="start"
            //  Chọn GIỜ/PHÚT mở một popper Select riêng (portal NGOÀI popover) — bấm vào
            //  đó KHÔNG được coi là "bấm ra ngoài" để đóng. Chỉ X hoặc bấm ra vùng trống mới đóng.
            onInteractOutside={(event) => {
              const target = event.target as HTMLElement | null
              if (target?.closest('[data-radix-popper-content-wrapper],[data-radix-select-viewport],[role="listbox"]')) {
                event.preventDefault()
              }
            }}
          >
            <div className="flex items-center justify-between border-b px-3 py-2">
              <span className="text-sm font-medium">Chọn ngày &amp; giờ</span>
              <button
                type="button"
                aria-label="Đóng"
                className="rounded-sm text-muted-foreground hover:text-foreground"
                onClick={() => setOpen(false)}
              >
                <X className="size-4" />
              </button>
            </div>
            <Calendar
              mode="single"
              autoFocus
              selected={selected}
              month={viewMonth}
              onMonthChange={setViewMonth}
              disabled={minDate ? { before: minDate } : undefined}
              onSelect={(d) => d && pickDate(toDateInputValue(d))}
            />
            <div className="flex items-center gap-2 border-t p-3">
              <span className="text-sm font-medium text-muted-foreground">Giờ</span>
              <TimeSelect value={seg.h} options={HOURS} placeholder="GG" onChange={(v) => push({ ...seg, h: v })} />
              <span className="text-muted-foreground">:</span>
              <TimeSelect value={seg.mi} options={MINUTES} placeholder="PP" onChange={(v) => push({ ...seg, mi: v })} />
              {/*  Hôm nay: đặt về hiện tại + KÉO LỊCH về tháng này (chấm hôm nay hiện rõ);
                  KHÔNG đóng popover (chỉ X / bấm ra ngoài mới đóng). */}
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="ml-auto"
                onClick={() => {
                  setViewMonth(new Date())
                  push(split(nowLocal()))
                }}
              >
                Hôm nay
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      </div>
      {warn.msg && <p className="text-xs font-medium text-destructive">{warn.msg}</p>}
    </div>
  )
}

function SegBox({
  segKey,
  value,
  placeholder,
  ariaLabel,
  disabled,
  onChange,
}: {
  segKey: keyof Seg
  value: string
  placeholder: string
  ariaLabel: string
  disabled?: boolean
  onChange: (key: keyof Seg, raw: string) => void
}) {
  const len = LEN[segKey]
  return (
    <input
      type="text"
      inputMode="numeric"
      disabled={disabled}
      value={value}
      placeholder={placeholder}
      aria-label={ariaLabel}
      maxLength={len}
      //  Bấm/hội tụ vào cụm → bôi xanh 2 số để gõ đè ngay (chỉ đổi cụm này).
      onFocus={(e) => e.currentTarget.select()}
      onChange={(e) => {
        onChange(segKey, e.target.value)
        //  Gõ đủ số → tự nhảy sang CỤM KẾ (ô kế cách một dấu phân tách).
        const digits = e.target.value.replace(/\D/g, '').slice(0, len)
        const next = e.currentTarget.nextElementSibling?.nextElementSibling
        if (digits.length >= len && next instanceof HTMLInputElement) next.focus()
      }}
      className={cn(
        'min-w-0 bg-transparent text-center tabular-nums outline-none placeholder:text-muted-foreground',
        len === 4 ? 'w-9' : 'w-6',
      )}
    />
  )
}

function TimeSelect({
  value,
  options,
  placeholder,
  onChange,
}: {
  value: string
  options: string[]
  placeholder: string
  onChange: (value: string) => void
}) {
  return (
    <Select value={value || undefined} onValueChange={onChange}>
      <SelectTrigger className="h-8 w-[64px]" aria-label={placeholder}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent className="max-h-60">
        {options.map((o) => (
          <SelectItem key={o} value={o}>
            {o}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function Sep({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn('text-sm text-muted-foreground', className)}>{children}</span>
}
