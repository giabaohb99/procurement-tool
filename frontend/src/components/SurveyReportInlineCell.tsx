import { useEffect, useRef, useState } from 'react'
import { toast } from './toast'

/**
 * duoc-CR-612 (v1): ô chữ SỬA NGAY TRÊN DÒNG của dạng «Bảng» trong khối Báo cáo thực hiện.
 * Kiểu bảng tính: bấm vào là sửa, Enter / rời ô là lưu, Esc là bỏ. Chép hành vi từ
 * `frontend-v2/.../survey-report-inline-cells.tsx`.
 *
 * Ở trạng thái XEM là một nút phẳng chứ không phải ô nhập luôn mở: bảng 20–50 dòng × 4 ô chữ mà
 * ô nào cũng là <input> thì nặng, và giá trị đổi từ ngoài (hoàn tác, người khác sửa) phải hiện
 * ngay — bản nháp chỉ sống trong lúc đang sửa nên không phải đồng bộ ngược.
 */
type Props = {
  value: string
  /** Chỉ gọi khi giá trị THẬT SỰ đổi. Trả Promise bị từ chối (lưu hỏng) thì ô mở lại với chữ đã gõ. */
  onCommit: (next: string) => unknown
  /** Tên ô cho trình đọc màn hình. */
  label: string
  /** Khớp `max_length` ở backend — vượt là 422. */
  maxLength: number
  /** Ô nhiều dòng: Enter lưu, Shift+Enter xuống dòng. */
  multiline?: boolean
  /** Rỗng thì không lưu, giữ giá trị cũ (tên hồ sơ). */
  required?: boolean
  placeholder?: string
  readOnly?: boolean
  className?: string
}

export default function SurveyReportInlineCell({
  value, onCommit, label, maxLength, multiline = false, required = false, placeholder = '—', readOnly = false, className = '',
}: Props) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  //  Enter lưu xong thì ô nhập bị gỡ, trình duyệt có thể bắn thêm một `blur` —
  //  cờ này giữ cho một lượt sửa chỉ lưu đúng MỘT lần.
  const settled = useRef(false)
  //  Enter / Esc xong thì trả con trỏ về ô vừa sửa (gỡ ô nhập thì focus rơi về <body>).
  const viewButton = useRef<HTMLButtonElement>(null)
  const refocus = useRef(false)
  useEffect(() => {
    if (!editing && refocus.current) {
      refocus.current = false
      viewButton.current?.focus()
    }
  }, [editing])

  if (readOnly) {
    return (
      <span title={value || undefined} className={`srp-cell-text${multiline ? ' clamp' : ''}${value ? '' : ' empty'} ${className}`}>
        {value || '—'}
      </span>
    )
  }

  function startEdit() {
    settled.current = false
    setDraft(value)
    setEditing(true)
  }

  function finish(save: boolean, fromKeyboard = false) {
    if (settled.current) return
    settled.current = true
    refocus.current = fromKeyboard
    setEditing(false)
    if (!save) return
    const next = draft.trim()
    if (required && !next) {
      toast.error('Ô này không được để trống — đã giữ giá trị cũ')
      return
    }
    //  So với giá trị cũ ĐÃ CẮT khoảng trắng: dữ liệu cũ có dấu cách thừa thì bấm vào rồi bấm ra
    //  cũng không được thành một lần lưu + một dòng lịch sử.
    if (next === value.trim()) return
    const result = onCommit(next)
    if (result instanceof Promise) {
      result.catch(() => {
        //  Lưu hỏng: lỗi đã có toast của client.ts — mở lại ô với chữ vừa gõ để khỏi gõ lại.
        settled.current = false
        setDraft(next)
        setEditing(true)
      })
    }
  }

  if (editing) {
    const shared = {
      autoFocus: true,
      value: draft,
      maxLength,
      'aria-label': label,
      className: 'srp-cell-input',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setDraft(e.target.value),
      onBlur: () => finish(true),
      onKeyDown: (e: React.KeyboardEvent) => {
        //  Bộ gõ tiếng Việt chốt chữ bằng chính phím Enter: lúc đó `isComposing` bật, lưu ngay là mất chữ cuối.
        if (e.nativeEvent.isComposing) return
        if (e.key === 'Escape') {
          e.preventDefault()
          e.stopPropagation()
          finish(false, true)
        } else if (e.key === 'Enter' && !(multiline && e.shiftKey)) {
          e.preventDefault()
          finish(true, true)
        }
      },
    }
    return multiline ? <textarea {...shared} rows={3} /> : <input type="text" {...shared} />
  }

  return (
    <button
      ref={viewButton}
      type="button"
      className={`srp-cell-btn${value ? '' : ' empty'}`}
      aria-label={`Sửa ${label}: ${value || 'đang trống'}`}
      title={value || 'Bấm để nhập'}
      onClick={startEdit}
    >
      <span className={`srp-cell-text${multiline ? ' clamp' : ''} ${className}`}>{value || placeholder}</span>
    </button>
  )
}
