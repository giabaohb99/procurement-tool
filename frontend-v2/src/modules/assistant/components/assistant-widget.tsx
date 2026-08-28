import { Loader2, Maximize2, Sparkles, SquarePen, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useQueryClient } from '@tanstack/react-query'

import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { assistantApi } from '../api/assistant-api'
import {
  useConversation,
  useConversations,
  useProviders,
  useSendMessage,
} from '../hooks/use-assistant'
import { ChatComposer } from './chat-composer'
import { ChatEmptyState } from './chat-empty-state'
import { MessageThread } from './message-thread'
import {
  pickDraftOffer,
  pickFileOffer,
  pickUpdateOffer,
  type DraftOffer,
  type FileOffer,
  type UpdateOffer,
} from '../utils/reply-offers'
import type { AssistantAttachment } from '../types/assistant'
import { ReplyOffers } from './reply-offers'

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
  //  Đã chọn xong hội thoại mở đầu (tự nạp cái gần nhất) hay chưa — sau đó thì
  //  tôn trọng lựa chọn của người dùng, kể cả "Trò chuyện mới" (id = 0).
  const [autoPicked, setAutoPicked] = useState(false)
  const [pending, setPending] = useState<string | null>(null)
  //  Tệp gửi kèm câu đang chờ — chỉ để vẽ chip trên bong bóng chờ (CR-204).
  const [pendingFiles, setPendingFiles] = useState<AssistantAttachment[]>([])
  //  Mốc id chốt lúc bấm gửi — tin trợ lý mới hơn mốc này được chạy hiệu ứng gõ
  //  máy (xem chú thích `typingAfterId` trong `message-thread.tsx`).
  const [typingAfterId, setTypingAfterId] = useState<number | null>(null)
  //  Bản nháp phiếu / file báo cáo trợ lý vừa soạn — nút hành động dùng chung với
  //  trang đầy đủ, xem `reply-offers.tsx`.
  const [draftOffer, setDraftOffer] = useState<DraftOffer | null>(null)
  const [fileOffer, setFileOffer] = useState<FileOffer | null>(null)
  //  Đề xuất sửa phiếu (CR-218) — thẻ xác nhận dưới luồng chat, cùng vòng đời hai offer trên.
  const [updateOffer, setUpdateOffer] = useState<UpdateOffer | null>(null)

  const conversationQuery = useConversation(conversationId)

  //  Mở bong bóng thì nạp danh sách hội thoại và TỰ MỞ LẠI hội thoại gần nhất —
  //  người dùng thường quay lại đúng câu đang hỏi dở, không phải màn chào.
  const conversationsQuery = useConversations({ enabled: open && !autoPicked })
  const conversationsChanged = useHasChanged(conversationsQuery.data)
  if (conversationsChanged && conversationsQuery.data && !autoPicked) {
    const latest = conversationsQuery.data[0]
    if (latest && conversationId === 0) setConversationId(latest.id)
    setAutoPicked(true)
  }

  // Trợ lý tắt ở máy chủ (AI_ENABLED) hoặc chưa có khóa -> /providers trả 403.
  // Ẩn hẳn bong bóng thay vì hiện nút bấm vào rồi báo lỗi.
  if (providersQuery.isError) return null

  const configured = providersQuery.data?.providers.filter((p) => p.configured) ?? []
  const selectedProvider = providersQuery.data?.default_provider || configured[0]?.name || ''
  const noProvider = !providersQuery.isLoading && configured.length === 0

  const messages = conversationQuery.data?.messages ?? []
  const isSending = sendMessage.isPending
  //  Đang dò hội thoại gần nhất / đang nạp tin của nó — hiện vòng chờ thay vì
  //  nháy màn chào rồi mới đổ tin cũ vào.
  const historyLoading =
    (!autoPicked && conversationsQuery.isLoading) ||
    (conversationId > 0 && conversationQuery.isLoading)

  const startNew = () => {
    setConversationId(0)
    setAutoPicked(true) //  người dùng chủ động mở trang trắng — đừng tự nạp lại cái cũ
    setPending(null)
    setPendingFiles([])
    setTypingAfterId(null) //  hội thoại mới thì thôi gõ dở câu của hội thoại trước
    setDraftOffer(null)
    setFileOffer(null)
    setUpdateOffer(null)
  }

  const handleSend = async (message: string, attachments?: AssistantAttachment[]) => {
    setPending(message)
    setPendingFiles(attachments ?? [])
    //  Chốt mốc gõ máy TRƯỚC khi gửi — tin nào server trả thêm về (id lớn hơn)
    //  là câu vừa nhận. Đặt sau khi nhận thì thua race với render từ cache,
    //  câu trả lời hiện full rồi gõ lại từ đầu — xem `message-thread.tsx`.
    const currentMessages = conversationQuery.data?.messages ?? []
    setTypingAfterId(currentMessages.reduce((max, m) => Math.max(max, m.id), 0))
    try {
      const reply = await sendMessage.mutateAsync({
        message,
        provider: selectedProvider || undefined,
        conversation_id: conversationId > 0 ? conversationId : undefined,
        attachment_ids: attachments?.length ? attachments.map((a) => a.id) : undefined,
      })
      // Nạp xong chi tiết hội thoại trước khi bỏ tin chờ, để câu vừa gửi không
      // nháy mất một nhịp (giống trang đầy đủ).
      await queryClient.fetchQuery({
        queryKey: queryKeys.assistant.conversation(reply.conversation_id),
        queryFn: () => assistantApi.conversation(reply.conversation_id),
      })
      //  Trợ lý vừa soạn bản nháp / xuất file -> chào nút hành động (trước đây chỉ
      //  trang đầy đủ có nút, chat trong bong bóng bị mời bấm nút không tồn tại).
      setDraftOffer(pickDraftOffer(reply))
      setFileOffer(pickFileOffer(reply))
      setUpdateOffer(pickUpdateOffer(reply))
      void queryClient.invalidateQueries({ queryKey: queryKeys.assistant.conversations() })
      if (reply.conversation_id !== conversationId) setConversationId(reply.conversation_id)
    } catch {
      // Lỗi mạng/backend đã tự hiện toast ở tầng API; chỉ cần gỡ tin chờ.
    } finally {
      setPending(null)
      setPendingFiles([])
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
            //  Khổ lớn (khách chê bản 30rem x 24rem nhỏ quá): cao gần hết màn hình,
            //  rộng 30rem từ sm và 34rem từ lg; máy nhỏ vẫn ăn theo bề rộng màn hình.
            'flex h-[40rem] max-h-[calc(100svh-6.5rem)] w-[calc(100vw-2rem)] sm:w-[30rem] lg:w-[34rem]',
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
              {historyLoading ? (
                <div className="flex flex-1 items-center justify-center text-muted-foreground">
                  <Loader2 className="size-5 animate-spin" />
                </div>
              ) : messages.length === 0 && pending === null ? (
                <ChatEmptyState
                  onPick={isSending ? undefined : (question) => void handleSend(question)}
                />
              ) : (
                <MessageThread
                  messages={messages}
                  pending={pending}
                  pendingAttachments={pendingFiles}
                  isSending={isSending}
                  typingAfterId={typingAfterId}
                />
              )}
              {/*  Nút mở form phiếu đã điền sẵn / tải báo cáo — thu gọn bong bóng khi
                   điều hướng để form không bị che. */}
              <ReplyOffers
                draft={draftOffer}
                file={fileOffer}
                update={updateOffer}
                onDismissUpdate={() => setUpdateOffer(null)}
                conversationId={conversationId}
                busy={isSending}
                onNavigate={() => setOpen(false)}
              />
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
