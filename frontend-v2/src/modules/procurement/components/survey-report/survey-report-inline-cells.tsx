// duoc-CR-612 (09/10/2026) — ô SỬA NGAY TRÊN DÒNG của dạng «Bảng» trong khối Báo cáo thực
// hiện. Ô chữ theo kiểu bảng tính: bấm vào là sửa, Enter / rời ô là lưu, Esc là bỏ. Ô chọn,
// ô ngày, ô tick lưu ngay khi chọn. Mỗi lần lưu chỉ gửi ĐÚNG trường vừa đổi (PATCH từng phần).
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'

interface InlineTextCellProps {
  value: string
  /**
   * Chỉ gọi khi giá trị THẬT SỰ đổi — rời ô mà không gõ gì thì không gửi request.
   * Trả Promise bị từ chối (lưu hỏng) thì ô MỞ LẠI với chữ vừa gõ, không bắt gõ lại.
   */
  onCommit: (next: string) => unknown
  /** Tên ô cho trình đọc màn hình, vd `Tên hồ sơ "C/O form E"`. */
  label: string
  /** Khớp `max_length` của `ReportDocPatch` ở backend — vượt là 422. */
  maxLength: number
  /** Ô nhiều dòng (mô tả, kết quả): Enter lưu, Shift+Enter xuống dòng. */
  multiline?: boolean
  /** Rỗng thì không lưu, trả về giá trị cũ (tên hồ sơ — backend cũng chặn). */
  required?: boolean
  placeholder?: string
  readOnly?: boolean
  disabled?: boolean
  className?: string
}

/**
 * Ô chữ sửa tại chỗ. Ở trạng thái XEM là một nút phẳng (bấm / Tab tới rồi Enter là
 * vào sửa) chứ không phải ô nhập luôn mở: bảng 20–50 dòng × 4 ô chữ mà ô nào cũng là
 * `<input>` thì nặng, và giá trị trong cache đổi (người khác sửa, hoàn tác) phải hiện
 * ngay — bản nháp chỉ sống trong lúc đang sửa nên không phải đồng bộ ngược.
 */
export function InlineTextCell({
  value,
  onCommit,
  label,
  maxLength,
  multiline = false,
  required = false,
  placeholder = '—',
  readOnly = false,
  disabled = false,
  className,
}: InlineTextCellProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)
  //  Enter lưu xong thì ô nhập bị gỡ, trình duyệt có thể bắn thêm một `blur` —
  //  cờ này giữ cho một lượt sửa chỉ lưu đúng MỘT lần.
  const settled = useRef(false)
  //  Enter / Esc xong thì trả con trỏ về ô vừa sửa — gỡ ô nhập mà để con trỏ rơi về
  //  `<body>` thì người dùng bàn phím lạc chỗ giữa bảng 50 hàng.
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
      <span
        title={value || undefined}
        className={cn(
          'block whitespace-pre-line [overflow-wrap:anywhere]',
          multiline && 'line-clamp-3',
          !value && 'text-muted-foreground',
          className,
        )}
      >
        {value || '—'}
      </span>
    )
  }

  const startEdit = () => {
    if (disabled) return
    settled.current = false
    setDraft(value)
    setEditing(true)
  }

  const finish = (save: boolean, fromKeyboard = false) => {
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
    //  So với giá trị cũ ĐÃ CẮT khoảng trắng: dữ liệu cũ có dấu cách / xuống dòng thừa ở
    //  hai đầu thì bấm vào rồi bấm ra cũng không được thành một lần lưu + một dòng lịch sử.
    if (next === value.trim()) return
    const result = onCommit(next)
    if (result instanceof Promise) {
      result.catch(() => {
        //  Lưu hỏng (mất mạng, 422, hết quyền): lỗi đã có toast của lớp API chung — ở
        //  đây chỉ mở lại ô với chữ vừa gõ, mất 4000 ký tự mô tả vì một lần rớt mạng là hết chịu.
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
      onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setDraft(event.target.value),
      onBlur: () => finish(true),
      onKeyDown: (event: React.KeyboardEvent) => {
        //  Bộ gõ tiếng Việt (Telex của macOS, Unikey ở chế độ gõ trước) chốt chữ bằng chính
        //  phím Enter: lúc đó `isComposing` bật, lưu ngay là mất dấu / mất chữ cuối.
        if (event.nativeEvent.isComposing) return
        if (event.key === 'Escape') {
          event.preventDefault()
          //  Esc trong ô không được lan lên hộp thoại / khung cha mà đóng luôn thứ khác.
          event.stopPropagation()
          finish(false, true)
        } else if (event.key === 'Enter' && !(multiline && event.shiftKey)) {
          //  Không để Enter rơi xuống `<form>` nào bọc ngoài (bẫy duoc-CR-317).
          event.preventDefault()
          finish(true, true)
        }
      },
    }
    return multiline ? (
      <Textarea {...shared} rows={3} className="min-h-16 text-xs" />
    ) : (
      <Input {...shared} className="h-8 text-xs" />
    )
  }

  return (
    <button
      ref={viewButton}
      type="button"
      disabled={disabled}
      //  Tên đọc ra phải kèm GIÁ TRỊ — chỉ «Sửa mô tả» thì trình đọc màn hình không bao giờ
      //  đọc được nội dung ô.
      aria-label={`Sửa ${label}: ${value || 'đang trống'}`}
      title={value || 'Bấm để nhập'}
      onClick={startEdit}
      className={cn(
        '-mx-1.5 block w-[calc(100%+0.75rem)] rounded-md px-1.5 py-1 text-left',
        'hover:bg-accent/60 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
        !value && 'text-muted-foreground/60',
        disabled && 'cursor-not-allowed',
      )}
    >
      {/* Cắt dòng đặt ở thẻ TRONG, không đặt lên nút: nút có đệm trên/dưới nên dòng thứ
          tư lấp ló trong phần đệm (thấy trên trình duyệt 09/10, jsdom không bắt được). */}
      <span
        className={cn(
          'block whitespace-pre-line [overflow-wrap:anywhere]',
          multiline && 'line-clamp-3',
          className,
        )}
      >
        {value || placeholder}
      </span>
    </button>
  )
}
