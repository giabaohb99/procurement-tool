import { useState } from 'react'

import { Input } from '@/shared/ui/input'
import { maskTime24h, parseTime24h, shiftTime24h } from '@/shared/utils/time-24h'
import { cn } from '@/shared/utils/cn'

interface TimeInput24hProps {
  /** "HH:MM" hoặc `null`/rỗng khi chưa có giờ. */
  value: string | null
  /** Bắn "HH:MM" hợp lệ, hoặc `null` khi người dùng xóa trắng ô. */
  onChange: (next: string | null) => void
  'aria-label': string
  className?: string
  id?: string
}

/** Bước mũi tên lên/xuống, tính bằng phút. */
const ARROW_STEP_MINUTES = 15

/**
 * Ô nhập giờ LUÔN 24h «HH:MM». Dùng thay `<input type="time">` vì ô gốc theo locale của
 * trình duyệt (en-US hiện «08:00 AM»), còn công ty chốt giờ làm việc luôn dạng 24h.
 *
 * Gõ tự do: «8» «830» «8:30» đều được, tự chèn «:». Gõ đủ 4 số hợp lệ là ghi ngay; gõ dở
 * thì chốt khi rời ô (hợp lệ -> chuẩn hóa, sai -> trả về giá trị cũ, không ghi rác). Mũi tên
 * lên/xuống đổi 15 phút, Enter chốt ô mà KHÔNG gửi form cha (gõ dở giờ rồi Enter không được lưu cả mẫu).
 */
export function TimeInput24h({ value, onChange, className, id, ...rest }: TimeInput24hProps) {
  //  `draft` chỉ tồn tại lúc đang gõ; ngoài lúc đó ô luôn hiện đúng `value` của form.
  const [draft, setDraft] = useState<string | null>(null)

  const commitDraft = () => {
    if (draft === null) return
    if (draft.trim() === '') onChange(null)
    else {
      const parsed = parseTime24h(draft)
      if (parsed) onChange(parsed)
    }
    setDraft(null)
  }

  return (
    <Input
      id={id}
      type="text"
      inputMode="numeric"
      autoComplete="off"
      placeholder="--:--"
      maxLength={5}
      aria-label={rest['aria-label']}
      className={cn('w-[4.5rem] text-center tabular-nums', className)}
      value={draft ?? value ?? ''}
      onFocus={(event) => event.target.select()}
      onChange={(event) => {
        const masked = maskTime24h(event.target.value)
        setDraft(masked)
        if (masked === '') onChange(null)
        else if (masked.length === 5) {
          const parsed = parseTime24h(masked)
          if (parsed) onChange(parsed)
        }
      }}
      onBlur={commitDraft}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault()
          commitDraft()
        } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
          event.preventDefault()
          const base = draft !== null ? parseTime24h(draft) : value
          onChange(shiftTime24h(base, event.key === 'ArrowUp' ? ARROW_STEP_MINUTES : -ARROW_STEP_MINUTES))
          setDraft(null)
        }
      }}
      aria-invalid={draft !== null && draft.trim() !== '' && parseTime24h(draft) === null ? true : undefined}
    />
  )
}
