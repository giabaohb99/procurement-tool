import { Sparkles } from 'lucide-react'

/**
 * Dấu nhận của trợ lý, đứng cạnh mỗi câu trả lời.
 *
 * Có nó vì câu trả lời KHÔNG nằm trong bong bóng (xem `chat-message.tsx`): thiếu
 * bong bóng thì cần một mốc thị giác khác để mắt biết đoạn này là của máy, nhất
 * là khi trả lời dài và người dùng cuộn giữa chừng.
 */
export function AssistantAvatar() {
  return (
    <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md border border-primary/20 bg-primary/10">
      <Sparkles className="size-3.5 text-primary" />
    </div>
  )
}
