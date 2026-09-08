import { Smile } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

// why: luật `icons.md` cấm emoji literal trong mã nguồn — bảng chọn dựng từ
// CODE POINT, ký tự emoji chỉ tồn tại lúc chạy. Bộ ~40 emoji chọn tay theo
// mức hay dùng trên mạng xã hội (sếp chốt 03/09: có emoji là đủ, KHÔNG sticker).
const EMOJI_CODE_POINTS: number[][] = [
  // mặt cười / cảm xúc
  [0x1f600], [0x1f602], [0x1f923], [0x1f60a], [0x1f609], [0x1f60d], [0x1f970],
  [0x1f618], [0x1f61c], [0x1f914], [0x1f60e], [0x1f642], [0x1f643], [0x1f644],
  [0x1f62e], [0x1f634], [0x1f622], [0x1f62d], [0x1f621], [0x1f631],
  // cử chỉ
  [0x1f44d], [0x1f44e], [0x1f44f], [0x1f64f], [0x1f4aa], [0x1f91d], [0x1f44c],
  [0x1f44b], [0x270c, 0xfe0f],
  // tim / đồ vật hay dùng
  [0x2764, 0xfe0f], [0x1f494], [0x1f525], [0x1f389], [0x1f38a], [0x2b50],
  [0x1f3c6], [0x1f4af], [0x1f680], [0x2615], [0x1f382], [0x1f4a1],
]
const EMOJIS = EMOJI_CODE_POINTS.map((points) => String.fromCodePoint(...points))

interface EmojiPickerButtonProps {
  /** Nhận ký tự emoji vừa chọn — nơi gọi tự lo chèn vào đúng vị trí con trỏ. */
  onPick: (emoji: string) => void
  className?: string
}

/**
 * Nút mở bảng chọn emoji cho composer + ô bình luận (F13c). Chọn xong ĐÓNG
 * bảng ngay và trả chữ về nơi gọi — không tự đụng vào ô nhập nào, nên cùng
 * một nút cắm được vào cả `<Textarea>` (controlled) lẫn `MentionInput`
 * (contenteditable, uncontrolled).
 */
export function EmojiPickerButton({ onPick, className }: EmojiPickerButtonProps) {
  const [open, setOpen] = useState(false)
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-label="Chèn emoji"
          className={cn('text-muted-foreground', className)}
        >
          <Smile className="size-4 text-amber-500" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-2" align="start">
        <div className="grid grid-cols-8 gap-0.5">
          {EMOJIS.map((emoji) => (
            <button
              key={emoji}
              type="button"
              aria-label={`Chèn ${emoji}`}
              className="rounded-md p-1 text-lg leading-none transition-colors hover:bg-accent"
              onClick={() => {
                onPick(emoji)
                setOpen(false)
              }}
            >
              {emoji}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
