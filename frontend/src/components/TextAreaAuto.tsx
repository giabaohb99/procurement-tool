import { useLayoutEffect, useRef, CSSProperties } from 'react'

type Props = {
  value?: string
  onChange?: (v: string) => void
  disabled?: boolean
  readOnly?: boolean
  className?: string
  style?: CSSProperties
  placeholder?: string
  title?: string
  onBlur?: () => void
}

/**
 * Ô nhập chữ tự XUỐNG DÒNG và tự giãn chiều cao theo nội dung.
 * Dùng thay <input> cho các trường dài (tên hàng, tên trên hóa đơn, quy cách…)
 * để người đọc thấy đủ thông tin, không bị cắt cụt bằng dấu "…".
 * Enter không xuống dòng (giữ hành vi như ô 1 dòng), chỉ tự wrap khi tràn.
 */
export default function TextAreaAuto({
  value, onChange, disabled, readOnly, className, style, placeholder, title, onBlur,
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null)

  // Đặt lại chiều cao = chiều cao thật của nội dung
  const fit = () => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  }

  useLayoutEffect(fit, [value])

  return (
    <textarea
      ref={ref}
      className={className}
      disabled={disabled}
      readOnly={readOnly}
      placeholder={placeholder}
      title={title}
      rows={1}
      value={value ?? ''}
      onChange={(e) => { onChange?.(e.target.value); fit() }}
      onBlur={onBlur}
      onKeyDown={(e) => { if (e.key === 'Enter') e.preventDefault() }}
      style={{
        resize: 'none',
        overflow: 'hidden',
        whiteSpace: 'pre-wrap',
        overflowWrap: 'anywhere',
        lineHeight: 1.45,
        ...style,
      }}
    />
  )
}
