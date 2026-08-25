import { useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { queryKeys } from '@/shared/constants/query-keys'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { assistantApi } from '../api/assistant-api'
import { ChatComposer } from '../components/chat-composer'
import { ChatEmptyState } from '../components/chat-empty-state'
import { ConversationSidebar } from '../components/conversation-sidebar'
import { MessageThread } from '../components/message-thread'
import {
  useConversation,
  useConversations,
  useDeleteConversation,
  useProviders,
  useSendMessage,
} from '../hooks/use-assistant'

/** Nhãn hiển thị của nhà cung cấp — mã kỹ thuật viết hoa chữ đầu. */
function providerLabel(name: string): string {
  return name.charAt(0).toUpperCase() + name.slice(1)
}

export function AssistantPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeId = Number(searchParams.get('c')) || 0

  const providersQuery = useProviders()
  const conversationsQuery = useConversations()
  const conversationQuery = useConversation(activeId)
  const sendMessage = useSendMessage()
  const deleteConversation = useDeleteConversation()

  const [pending, setPending] = useState<string | null>(null)
  const [provider, setProvider] = useState<string>('')
  //  Id câu trả lời được chạy hiệu ứng gõ máy — chỉ đúng câu VỪA nhận trong
  //  phiên này. Mở lại hội thoại cũ thì mọi tin hiện thẳng, không gõ lại.
  const [idGoDan, setIdGoDan] = useState<number | null>(null)

  /** Chỉ chào nhà đã cấu hình key — chọn nhà chưa có key sẽ bị backend từ chối. */
  const configuredProviders = useMemo(
    () => providersQuery.data?.providers.filter((p) => p.configured) ?? [],
    [providersQuery.data],
  )

  const selectedProvider =
    provider ||
    providersQuery.data?.default_provider ||
    configuredProviders[0]?.name ||
    ''

  const setActive = (id: number) => {
    setPending(null)
    setIdGoDan(null) //  đổi hội thoại thì thôi gõ dở câu của hội thoại trước
    if (id > 0) setSearchParams({ c: String(id) })
    else setSearchParams({})
  }

  const handleSend = async (message: string) => {
    setPending(message)
    try {
      const reply = await sendMessage.mutateAsync({
        message,
        provider: selectedProvider || undefined,
        conversation_id: activeId > 0 ? activeId : undefined,
      })
      // Nạp XONG chi tiết hội thoại trước khi bỏ tin đang chờ, để câu vừa gửi
      // không biến mất một nhịp rồi mới hiện lại từ luồng tin của server.
      const chiTiet = await queryClient.fetchQuery({
        queryKey: queryKeys.assistant.conversation(reply.conversation_id),
        queryFn: () => assistantApi.conversation(reply.conversation_id),
      })

      //  Câu trả lời MỚI NHẤT của trợ lý trong luồng vừa nạp — chỉ mình nó được
      //  chạy hiệu ứng gõ. Lấy theo id thay vì "tin cuối" cho chắc: luồng trả về
      //  đã xếp theo thứ tự nhưng đừng phụ thuộc vào điều đó.
      const traLoiMoi = [...chiTiet.messages]
        .filter((m) => m.role_name === 'assistant')
        .sort((a, b) => a.id - b.id)
        .at(-1)
      setIdGoDan(traLoiMoi?.id ?? null)
      void queryClient.invalidateQueries({ queryKey: queryKeys.assistant.conversations() })
      if (reply.conversation_id !== activeId) {
        setSearchParams({ c: String(reply.conversation_id) })
      }
      //  KHÔNG có `catch`: lỗi phải nổi tiếp lên ô nhập. Lỗi mạng/backend đã tự
      //  hiện toast ở tầng API, nhưng nuốt ở đây thì câu vừa gõ mất trắng —
      //  bong bóng chờ bị gỡ ngay dưới `finally`, còn ô nhập thì đã xóa từ lúc
      //  bấm gửi. `chat-composer` bắt lại và trả nguyên văn vào ô.
    } finally {
      setPending(null)
    }
  }

  const handleDelete = (id: number) => {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (id === activeId) setActive(0)
      },
    })
  }

  // Bật/tắt trợ lý ở backend (AI_ENABLED) trả 403 -> báo rõ thay vì khung rỗng.
  if (providersQuery.isError) {
    return (
      <PageContainer>
        <ErrorState
          title="Trợ lý AI chưa sẵn sàng"
          description="Tính năng chưa được bật hoặc chưa cấu hình khóa API. Liên hệ quản trị hệ thống để bật (AI_ENABLED) và khai khóa trong cấu hình máy chủ."
        />
      </PageContainer>
    )
  }

  const messages = conversationQuery.data?.messages ?? []
  const isSending = sendMessage.isPending
  const noProvider = !providersQuery.isLoading && configuredProviders.length === 0

  return (
    <PageContainer fill>
      <PageHeader
        title="Trợ lý AI"
        description="Hỏi đáp trên nền gói tri thức nội bộ. Câu trả lời chỉ mang tính đề xuất."
        actions={
          configuredProviders.length > 1 ? (
            <Select value={selectedProvider} onValueChange={setProvider}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Nhà cung cấp" />
              </SelectTrigger>
              <SelectContent>
                {configuredProviders.map((p) => (
                  <SelectItem key={p.name} value={p.name}>
                    {providerLabel(p.name)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : undefined
        }
      />

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-xl border bg-background">
        <ConversationSidebar
          items={conversationsQuery.data ?? []}
          activeId={activeId}
          loading={conversationsQuery.isLoading}
          onNew={() => setActive(0)}
          onSelect={setActive}
          onDelete={handleDelete}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          {noProvider ? (
            <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-muted-foreground">
              Chưa cấu hình khóa API cho nhà cung cấp nào. Khai khóa trong cấu hình máy chủ rồi
              thử lại.
            </div>
          ) : (
            <>
              {/*  Hội thoại trống thì lời chào nằm GIỮA khung, ngay trên ô nhập —
                   lúc đó việc duy nhất cần làm là gõ câu hỏi, nên hai thứ đó phải
                   ở gần nhau trong tầm mắt. */}
              {messages.length === 0 && !pending ? (
                <ChatEmptyState onChon={isSending ? undefined : (cau) => void handleSend(cau).catch(() => {})} />
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
      </div>
    </PageContainer>
  )
}
