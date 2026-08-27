import { Check, Copy, FileText, Image as ImageIcon } from 'lucide-react'
import { useEffect, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import type { AssistantAttachment } from '../types/assistant'
import { openChatAttachment } from '../utils/open-chat-attachment'
import { useTypewriter } from '../hooks/use-typewriter'
import { AssistantAvatar } from './assistant-avatar'
import { MarkdownMessage } from './markdown-message'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  /** Tệp người dùng gửi kèm lượt hỏi (CR-204) — vẽ chip trong bong bóng. */
  attachments?: AssistantAttachment[]
  /** Chạy hiệu ứng gõ máy. Chỉ bật cho câu trả lời VỪA nhận, không cho tin cũ. */
  typing?: boolean
}

/**
 * MỘT LƯỢT trong hội thoại.
 *
 * Hai vai hiển thị KHÁC HẲN nhau, và đó là điểm chính của bản dựng lại này:
 *
 *  - **Người dùng**: bong bóng bo tròn, lệch phải, nền chìm. Câu hỏi thường
 *    ngắn nên bong bóng ôm lấy chữ, đọc ra ngay "đây là mình vừa hỏi".
 *  - **Trợ lý**: KHÔNG bong bóng — chữ nằm thẳng trên nền trang, chiếm trọn bề
 *    ngang cột đọc. Câu trả lời hay dài, có danh sách và bảng; nhét vào bong
 *    bóng màu thì vừa bó hẹp bề ngang vừa làm bảng tràn ra ngoài. Bản cũ để
 *    `bg-secondary` cho cả khối trả lời nên nhìn như hai người nhắn tin, trong
 *    khi thứ người dùng cần là ĐỌC một đoạn tài liệu.
 *
 * Nút chép chỉ hiện khi rê chuột vào câu trả lời — số liệu tra xong hay được
 * dán sang chỗ khác, mà bôi đen tay thì dễ hụt đầu/cuối đoạn.
 */
export function ChatMessage({ role, content, attachments, typing = false }: ChatMessageProps) {
  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-accent px-4 py-2.5 text-sm whitespace-pre-wrap text-accent-foreground">
          {attachments && attachments.length > 0 && (
            <div className={cn('flex flex-wrap gap-1.5', content && 'mb-1.5')}>
              {attachments.map((a) => (
                //  Chip bấm được: mở xem lại tệp trong tab mới. `id` luôn là id
                //  thật trên server — metadata chỉ tồn tại sau khi upload xong.
                <button
                  key={a.id}
                  type="button"
                  onClick={() => void openChatAttachment(a.id)}
                  title={`Mở tệp ${a.filename}`}
                  className={cn(
                    'inline-flex max-w-52 items-center gap-1.5 rounded-lg bg-background/60 px-2 py-1 text-xs',
                    'hover:bg-background hover:underline',
                  )}
                >
                  {a.content_type === 'application/pdf' ? (
                    <FileText className="size-3.5 shrink-0" />
                  ) : (
                    <ImageIcon className="size-3.5 shrink-0" />
                  )}
                  <span className="truncate">{a.filename}</span>
                </button>
              ))}
            </div>
          )}
          {content}
        </div>
      </div>
    )
  }

  return <AssistantTurn content={content} typing={typing} />
}

function AssistantTurn({ content, typing }: { content: string; typing: boolean }) {
  const { display, isRunning } = useTypewriter(content, typing)

  return (
    <div className="group flex gap-3">
      <AssistantAvatar />

      <div className="min-w-0 flex-1">
        <MarkdownMessage content={display} className="text-sm text-foreground" />

        {/*  Con trỏ nhấp nháy trong lúc chữ đang chạy ra — dấu hiệu quen thuộc
             cho biết "còn nữa", đừng vội đọc kết luận. */}
        {isRunning && (
          <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary align-text-bottom" />
        )}

        {!isRunning && <CopyButton content={content} />}
      </div>
    </div>
  )
}

/** Chép trọn câu trả lời. Ẩn cho tới khi rê chuột để không làm rối cột đọc. */
function CopyButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!copied) return
    const id = setTimeout(() => setCopied(false), 1500)
    return () => clearTimeout(id)
  }, [copied])

  return (
    <button
      type="button"
      onClick={() => {
        //  Không có `navigator.clipboard` khi mở bằng IP nội bộ qua http (chỉ
        //  ngữ cảnh bảo mật mới có) — im lặng bỏ qua, người dùng bôi đen chép tay.
        void navigator.clipboard?.writeText(content).then(() => setCopied(true))
      }}
      className={cn(
        'mt-2 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground',
        'opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100',
        'hover:bg-muted hover:text-foreground',
      )}
    >
      {copied ? <Check className="size-3.5 text-emerald-600" /> : <Copy className="size-3.5" />}
      {copied ? 'Đã chép' : 'Chép'}
    </button>
  )
}
