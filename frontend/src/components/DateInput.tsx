import { useEffect, useRef, useState, CSSProperties } from 'react'

// Ô nhập ngày hiển thị dd/mm/yyyy (đồng nhất mọi trình duyệt/máy), lưu giá trị ISO 'YYYY-MM-DD'.
// Thay cho <input type="date"> native (vốn render theo ngôn ngữ trình duyệt → hay ra MM/DD/YYYY).

function isoToVi(iso?: string): string {
  if (!iso) return ''
  const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/)
  return m ? `${m[3]}/${m[2]}/${m[1]}` : ''
}
function viToIso(vi: string): string | null {
  const m = vi.trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/)
  if (!m) return null
  const d = +m[1], mo = +m[2], y = +m[3]
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return null
  const dd = String(d).padStart(2, '0'), mm = String(mo).padStart(2, '0')
  const dt = new Date(`${y}-${mm}-${dd}T00:00:00`)
  if (isNaN(dt.getTime()) || dt.getMonth() + 1 !== mo || dt.getDate() !== d) return null
  return `${y}-${mm}-${dd}`
}
// Tự chèn '/' khi gõ: dd -> dd/mm -> dd/mm/yyyy
function autoFmt(raw: string): string {
  const s = raw.replace(/[^\d]/g, '').slice(0, 8)
  if (s.length >= 5) return `${s.slice(0, 2)}/${s.slice(2, 4)}/${s.slice(4)}`
  if (s.length >= 3) return `${s.slice(0, 2)}/${s.slice(2)}`
  return s
}

type Props = {
  value?: string
  onChange: (iso: string) => void
  disabled?: boolean
  className?: string
  style?: CSSProperties
  placeholder?: string
  onFocus?: () => void
  /** Gọi SAU khi giá trị đã chốt (rời ô hoặc chọn từ lịch) — dùng cho ô tự lưu */
  onBlur?: () => void
}

export default function DateInput({ value, onChange, disabled, className, style, placeholder, onFocus, onBlur }: Props) {
  const [text, setText] = useState(() => isoToVi(value))
  const hiddenRef = useRef<HTMLInputElement>(null)
  useEffect(() => { setText(isoToVi(value)) }, [value])

  // Tách các thuộc tính bố cục ra thẻ bọc, phần còn lại (font, màu…) áp cho ô nhập
  const { width, minWidth, maxWidth, flex, margin, marginTop, marginLeft, marginRight, marginBottom, ...restStyle } = (style || {}) as any
  const wrapStyle: CSSProperties = { width: width ?? '100%', minWidth, maxWidth: maxWidth ?? '100%', flex, margin, marginTop, marginLeft, marginRight, marginBottom }

  // Báo cho cha SAU khi state đã cập nhật (ô tự lưu cần đọc giá trị mới)
  const fireBlur = () => { if (onBlur) setTimeout(onBlur, 0) }

  function commit(t: string) {
    const s = t.trim()
    if (!s) { onChange('') }
    else {
      const iso = viToIso(s)
      if (iso) onChange(iso)
      else setText(isoToVi(value))   // gõ sai định dạng → khôi phục giá trị cũ
    }
    fireBlur()
  }

  function openPicker() {
    const el = hiddenRef.current
    if (!el) return
    if (typeof (el as any).showPicker === 'function') (el as any).showPicker()
    else el.focus()
  }

  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', ...wrapStyle }}>
      <input
        type="text"
        inputMode="numeric"
        className={className}
        placeholder={placeholder || 'dd/mm/yyyy'}
        value={text}
        disabled={disabled}
        onFocus={onFocus}
        onChange={(e) => setText(autoFmt(e.target.value))}
        onBlur={(e) => commit(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') commit((e.target as HTMLInputElement).value) }}
        style={{ ...restStyle, width: '100%', paddingRight: 30 }}
      />
      <button
        type="button"
        tabIndex={-1}
        disabled={disabled}
        onClick={() => { if (onFocus) onFocus(); openPicker() }}
        title="Chọn ngày"
        style={{ position: 'absolute', right: 8, background: 'none', border: 0, padding: 0, height: '100%',
          display: 'inline-flex', alignItems: 'center', cursor: disabled ? 'default' : 'pointer', color: 'var(--muted)' }}
      >
        <i className="ti ti-calendar" style={{ fontSize: 15 }} />
      </button>
      {/* Ô date native ẩn — chỉ dùng để mở lịch chọn ngày */}
      <input
        ref={hiddenRef}
        type="date"
        value={value || ''}
        disabled={disabled}
        onChange={(e) => { onChange(e.target.value); fireBlur() }}
        tabIndex={-1}
        aria-hidden
        style={{ position: 'absolute', right: 4, bottom: 0, width: 1, height: 1, minWidth: 0, padding: 0, margin: 0, border: 0, opacity: 0, pointerEvents: 'none' }}
      />
    </span>
  )
}
