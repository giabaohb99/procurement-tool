import { useEffect, useRef, useState } from 'react'
import { DayPicker, type DateRange } from 'react-day-picker'
import { vi } from 'date-fns/locale'
import 'react-day-picker/style.css'

// Bộ chọn KHOẢNG NGÀY: nút -> popover (nút nhanh + lịch 2 tháng, react-day-picker).
// captionLayout="dropdown" => header lịch có dropdown Tháng + Năm.
// Chọn đủ from+to (hoặc bấm nút nhanh) -> tự đóng + gọi onApply (chạy luôn, đỡ 1 bước).
// Value in/out dạng chuỗi ISO 'YYYY-MM-DD' để khớp state phía dùng (không phụ thuộc timezone).

type Val = { from: string; to: string }

// ISO <-> Date theo giờ local (tránh lệch ngày do UTC)
function toDate(s: string): Date | undefined {
  if (!s) return undefined
  const [y, m, d] = s.split('-').map(Number)
  if (!y || !m || !d) return undefined
  return new Date(y, m - 1, d)
}
function toISO(d?: Date): string {
  if (!d) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const da = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${da}`
}
function fmtVN(s: string): string {
  if (!s) return ''
  const [y, m, d] = s.split('-')
  return `${d}/${m}/${y}`
}

// Danh sách nút nhanh — tính khoảng [from, to] theo hôm nay
function buildPresets(): { label: string; from: Date; to: Date }[] {
  const now = new Date()
  const y = now.getFullYear(), mo = now.getMonth(), d = now.getDate()
  const today = new Date(y, mo, d)
  const daysAgo = (n: number) => new Date(y, mo, d - n)
  const q = Math.floor(mo / 3) * 3   // tháng đầu quý hiện tại
  return [
    { label: 'Hôm nay', from: today, to: today },
    { label: '7 ngày qua', from: daysAgo(6), to: today },
    { label: '30 ngày qua', from: daysAgo(29), to: today },
    { label: 'Tháng này', from: new Date(y, mo, 1), to: today },
    { label: 'Tháng trước', from: new Date(y, mo - 1, 1), to: new Date(y, mo, 0) },
    { label: 'Quý này', from: new Date(y, q, 1), to: today },
  ]
}

export default function DateRangePicker({
  value, onChange, onApply, placeholder = 'Chọn khoảng ngày', startYear = 2020, endYear,
}: {
  value: Val
  onChange: (v: Val) => void
  onApply?: (v: Val) => void   // gọi khi đã chọn đủ khoảng / bấm nút nhanh (để chạy luôn)
  placeholder?: string
  startYear?: number
  endYear?: number
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const endY = endYear ?? new Date().getFullYear() + 1
  const has = !!(value.from || value.to)

  // Đóng khi bấm ra ngoài / nhấn Esc
  useEffect(() => {
    if (!open) return
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDoc)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDoc)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const range: DateRange | undefined = has
    ? { from: toDate(value.from), to: toDate(value.to) }
    : undefined

  function apply(v: Val) {
    onChange(v)
    onApply?.(v)
    setOpen(false)
  }

  // Lịch mặc định hiện tháng trước + tháng hiện tại (dữ liệu gần đây dễ thấy)
  const defaultMonth = toDate(value.from) || new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1)

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button type="button" className="drp-trigger" onClick={() => setOpen((o) => !o)}>
        <i className="ti ti-calendar-event" style={{ color: 'var(--teal)', fontSize: 16 }} />
        <span style={{ color: has ? 'var(--navy)' : 'var(--muted)', fontWeight: has ? 600 : 400 }}>
          {has ? `${fmtVN(value.from) || '…'} → ${fmtVN(value.to) || '…'}` : placeholder}
        </span>
        <i className={`ti ti-chevron-${open ? 'up' : 'down'}`} style={{ color: '#94a3b8', fontSize: 14, marginLeft: 6 }} />
      </button>
      {open && (
        <div className="drp-pop">
          <div className="drp-body">
            {/* Nút nhanh */}
            <div className="drp-presets">
              {buildPresets().map((p) => (
                <button key={p.label} type="button" className="drp-preset"
                  onClick={() => apply({ from: toISO(p.from), to: toISO(p.to) })}>{p.label}</button>
              ))}
            </div>
            {/* Lịch 2 tháng — chọn tay KHÔNG tự đóng, chờ bấm "Áp dụng" */}
            <div>
              <DayPicker
                mode="range"
                numberOfMonths={2}
                selected={range}
                onSelect={(r) => onChange({ from: toISO(r?.from), to: toISO(r?.to) })}
                captionLayout="dropdown"
                startMonth={new Date(startYear, 0)}
                endMonth={new Date(endY, 11)}
                defaultMonth={defaultMonth}
                locale={vi}
                weekStartsOn={1}
                showOutsideDays
              />
              {/* Footer: khoảng đang chọn + Áp dụng / Xóa */}
              <div className="drp-footer">
                <span className="drp-summary">
                  {value.from && value.to
                    ? <><b>{fmtVN(value.from)}</b> → <b>{fmtVN(value.to)}</b></>
                    : value.from
                      ? <>Từ <b>{fmtVN(value.from)}</b> · <span style={{ color: 'var(--teal)' }}>chọn ngày kết thúc</span></>
                      : <span style={{ color: 'var(--muted)' }}>Chọn ngày bắt đầu</span>}
                </span>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button type="button" className="btn ghost" onClick={() => onChange({ from: '', to: '' })}>Xóa</button>
                  <button type="button" className="btn" disabled={!(value.from && value.to)} onClick={() => apply(value)}>Áp dụng</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
