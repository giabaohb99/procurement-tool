import { Bot, Loader2, Sparkles } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { cn } from '@/shared/utils/cn'
import type { AssistantMessage } from '../types/assistant'
import { MarkdownMessage } from './markdown-message'

/**
 * Câu hỏi mẫu gợi sẵn để người dùng biết trợ lý tra được gì (khỏi "không biết hỏi gì").
 * Mỗi câu bám đúng một nhóm công cụ loại A ở backend.
 */
const SUGGESTED_QUESTIONS = [
  'Hợp đồng nhà cung cấp nào sắp hết hạn?',
  'Nhà cung cấp nào mua hàng nhiều nhất năm nay?',
  'Đơn mua hàng gần nhất có giá trị bao nhiêu?',
  'Tổng chi tiêu mua hàng theo từng tháng năm nay?',
  'Mặt hàng nào chi tiêu nhiều nhất?',
  'Lần mua hàng gần nhất là gì?',
]

interface MessageThreadProps {
  messages: AssistantMessage[]
  /** Câu vừa gửi đang chờ trả lời — hiện ngay để không thấy trễ. */
  pending: string | null
  isSending: boolean
  /** Bấm một câu hỏi mẫu ở màn trống — gửi luôn câu đó. */
  onPickSuggestion?: (question: string) => void
}

/** Khung cuộn chứa toàn bộ tin của hội thoại đang mở. */
export function MessageThread({
  messages,
  pending,
  isSending,
  onPickSuggestion,
}: MessageThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Luôn dán xuống đáy khi có tin mới / đang gõ — như mọi khung chat.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, pending, isSending])

  const empty = messages.length === 0 && !pending

  if (empty) {
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center px-6 text-center">
        <div className="flex size-12 items-center justify-center rounded-full bg-accent">
          <Sparkles className="size-6 text-primary" />
        </div>
        <h2 className="mt-4 text-lg font-medium text-navy">Trợ lý AI</h2>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          Hỏi về quy trình mua hàng, khảo sát, hợp đồng, giá và lịch sử mua… Trợ lý tra số liệu
          thật theo quyền của bạn và chỉ mang tính đề xuất, không thay quyết định của bạn.
        </p>

        {onPickSuggestion && (
          <div className="mt-6 flex max-w-xl flex-wrap justify-center gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => onPickSuggestion(q)}
                className={cn(
                  'rounded-full border border-input bg-background px-3 py-1.5 text-xs',
                  'text-muted-foreground transition-colors',
                  'hover:border-primary/40 hover:bg-accent hover:text-foreground',
                )}
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-5">
      {messages.map((m) => (
        <MessageBubble key={m.id} role={m.role_name} content={m.content} />
      ))}

      {pending && <MessageBubble role="user" content={pending} />}

      {isSending && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent">
            <Bot className="size-4 text-primary" />
          </div>
          <Loader2 className="size-4 animate-spin" />
          Đang soạn trả lời…
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}

interface MessageBubbleProps {
  role: 'user' | 'assistant'
  content: string
}

function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === 'user'
  return (
    <div className={cn('flex gap-2', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent">
          <Bot className="size-4 text-primary" />
        </div>
      )}
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-3 py-2 text-sm',
          isUser
            ? 'bg-primary whitespace-pre-wrap text-primary-foreground'
            : 'bg-secondary text-foreground',
        )}
      >
        {isUser ? content : <MarkdownMessage content={content} />}
      </div>
    </div>
  )
}
