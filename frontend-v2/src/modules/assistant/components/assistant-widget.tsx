import { Maximize2, Sparkles, SquarePen, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useQueryClient } from '@tanstack/react-query'

import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { assistantApi } from '../api/assistant-api'
import { useConversation, useProviders, useSendMessage } from '../hooks/use-assistant'
import { ChatComposer } from './chat-composer'
import { ChatEmptyState } from './chat-empty-state'
import { MessageThread } from './message-thread'

/**
 * Bong bóng chat nổi ở góc phải dưới — lối vào nhanh của Trợ lý AI, dùng lại
 * đúng API/hook của trang đầy đủ (Phase 1). Chỉ gắn khi người dùng có quyền
 * `assistant.read` (xem `ModuleLayout`), nên không tự bắn 403.
 *
 * Widget giữ MỘT hội thoại đang mở trong state cục bộ; đóng/mở lại vẫn còn vì
 * nó sống trong khung phân hệ. Muốn xem lịch sử đầy đủ thì bấm "Mở toàn trang".
 */
export function AssistantWidget() {
  const queryClient = useQueryClient()
  const providersQuery = useProviders()
  const sendMessage = useSendMessage()

  const [open, setOpen] = useState(false)
  const [conversationId, setConversationId] = useState(0)
  const [pending, setPending] = useState<string | null>(null)
  //  Id câu trả lời được chạy hiệu ứng gõ máy — chỉ câu VỪA nhận trong phiên này.
  const [idGoDan, setIdGoDan] = useState<number | null>(null)

  const conversationQuery = useConversation(conversationId)

  // Trợ lý tắt ở máy chủ (AI_ENABLED) hoặc chưa có khóa -> /providers trả 403.
  // Ẩn hẳn bong bóng thay vì hiện nút bấm vào rồi báo lỗi.
  if (providersQuery.isError) return null

  const configured = providersQuery.data?.providers.filter((p) => p.configured) ?? []
  const selectedProvider = providersQuery.data?.default_provider || configured[0]?.name || ''
  const noProvider = !providersQuery.isLoading && configured.length === 0

  const messages = conversationQuery.data?.messages ?? []
  const isSending = sendMessage.isPending

  const startNew = () => {
    setConversationId(0)
    setPending(null)
    setIdGoDan(null) //  hội thoại mới thì thôi gõ dở câu của hội thoại trước
  }

  const handleSend = async (message: string) => {
    setPending(message)
    try {
      const reply = await sendMessage.mutateAsync({
        message,
        provider: selectedProvider || undefined,
        conversation_id: conversationId > 0 ? conversationId : undefined,
      })
      // Nạp xong chi tiết hội thoại trước khi bỏ tin chờ, để câu vừa gửi không
      // nháy mất một nhịp (giống trang đầy đủ).
      const chiTiet = await queryClient.fetchQuery({
        queryKey: queryKeys.assistant.conversation(reply.conversation_id),
        queryFn: () => assistantApi.conversation(reply.conversation_id),
      })
      //  Chỉ câu trả lời MỚI NHẤT của trợ lý được chạy hiệu ứng gõ; lấy theo id
      //  cho chắc thay vì tin cuối luồng.
      const traLoiMoi = [...chiTiet.messages]
        .filter((m) => m.role_name === 'assistant')
        .sort((a, b) => a.id - b.id)
        .at(-1)
      setIdGoDan(traLoiMoi?.id ?? null)
      void queryClient.invalidateQueries({ queryKey: queryKeys.assistant.conversations() })
      if (reply.conversation_id !== conversationId) setConversationId(reply.conversation_id)
    } catch {
      // Lỗi mạng/backend đã tự hiện toast ở tầng API; chỉ cần gỡ tin chờ.
    } finally {
      setPending(null)
    }
  }

  // Đường dẫn "Mở toàn trang" giữ nguyên hội thoại đang xem.
  const fullPageHref =
    conversationId > 0
      ? `${appRoutes.assistant.root}?c=${conversationId}`
      : appRoutes.assistant.root

  return (
    <div className="fixed right-4 bottom-4 z-50 flex flex-col items-end gap-3 sm:right-6 sm:bottom-6">
      {open && (
        <div
          className={cn(
            'flex h-[30rem] max-h-[calc(100svh-7rem)] w-[calc(100vw-2rem)] sm:w-96',
            'flex-col overflow-hidden rounded-xl border bg-background shadow-2xl',
          )}
        >
          <div className="flex items-center justify-between border-b px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="flex size-6 items-center justify-center rounded-full bg-accent">
                <Sparkles className="size-3.5 text-primary" />
              </span>
              <span className="text-sm font-medium text-navy">Trợ lý AI</span>
            </div>
            <div className="flex items-center gap-0.5">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-7"
                onClick={startNew}
                title="Trò chuyện mới"
              >
                <SquarePen className="size-4" />
              </Button>
              <Button asChild variant="ghost" size="icon" className="size-7" title="Mở toàn trang">
                <Link to={fullPageHref}>
                  <Maximize2 className="size-4" />
                </Link>
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-7"
                onClick={() => setOpen(false)}
                title="Đóng"
              >
                <X className="size-4" />
              </Button>
            </div>
          </div>

          {noProvider ? (
            <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-muted-foreground">
              Chưa cấu hình khóa API cho nhà cung cấp nào.
            </div>
          ) : (
            <>
              {messages.length === 0 && !pending ? (
                <ChatEmptyState
                  onChon={isSending ? undefined : (cau) => void handleSend(cau)}
                />
              ) : (
                <MessageThread
                  messages={messages}
                  pending={pending}
                  isSending={isSending}
                  idGoDan={idGoDan}
                />
              )}
              <ChatComposer disabled={noProvider} busy={isSending} onSend={handleSend} />
            </>
          )}
        </div>
      )}

      <Button
        type="button"
        size="icon"
        onClick={() => setOpen((v) => !v)}
        className="size-12 rounded-full shadow-lg"
        title={open ? 'Thu gọn Trợ lý AI' : 'Mở Trợ lý AI'}
        aria-label={open ? 'Thu gọn Trợ lý AI' : 'Mở Trợ lý AI'}
      >
        {open ? <X className="size-5" /> : <Sparkles className="size-5" />}
      </Button>
    </div>
  )
}
