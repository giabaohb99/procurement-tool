import { useQueryClient } from '@tanstack/react-query'
import { FileDown, FilePlus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { downloadFile } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'
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
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeId = Number(searchParams.get('c')) || 0

  const providersQuery = useProviders()
  const conversationsQuery = useConversations()
  const conversationQuery = useConversation(activeId)
  const sendMessage = useSendMessage()
  const deleteConversation = useDeleteConversation()

  const [pending, setPending] = useState<string | null>(null)
  const [provider, setProvider] = useState<string>('')
  //  Mốc id chốt LÚC BẤM GỬI — tin trợ lý mới hơn mốc này được chạy hiệu ứng
  //  gõ máy. Chốt trước khi gửi (không phải sau khi nhận) để tin mới mount là
  //  gõ ngay; xem chú thích `typingAfterId` trong `message-thread.tsx`.
  const [typingAfterId, setTypingAfterId] = useState<number | null>(null)
  //  Bản nháp trợ lý vừa soạn (tool `draft_survey_request` = YCBG, `draft_purchase_request`
  //  = YCMH, `draft_leave_request` = đơn nghỉ phép) — chỉ sống trong lượt trả lời hiện tại,
  //  backend không lưu. Bấm nút mới mở form; phiếu KHÔNG tự tạo.
  const [draftOffer, setDraftOffer] = useState<{
    conversationId: number
    args: Record<string, unknown>
    target: 'survey' | 'purchase' | 'leave'
  } | null>(null)
  //  File báo cáo trợ lý vừa xuất (tool `export_report_file`) — cũng chỉ sống trong lượt
  //  trả lời hiện tại. Tải qua downloadFile (kèm Bearer), không gắn href thẳng.
  const [fileOffer, setFileOffer] = useState<{
    conversationId: number
    filename: string
    downloadUrl: string
  } | null>(null)

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
    setTypingAfterId(null) //  đổi hội thoại thì thôi gõ dở câu của hội thoại trước
    setDraftOffer(null)
    setFileOffer(null)
    if (id > 0) setSearchParams({ c: String(id) })
    else setSearchParams({})
  }

  const handleSend = async (message: string) => {
    setPending(message)
    //  Chốt mốc gõ máy TRƯỚC khi gửi: mọi tin đang có đều cũ, tin nào server
    //  trả thêm về (id lớn hơn) là câu vừa nhận -> được gõ. Đặt sau khi nhận
    //  thì thua race với render từ cache — xem `message-thread.tsx`.
    const currentMessages = conversationQuery.data?.messages ?? []
    setTypingAfterId(currentMessages.reduce((max, m) => Math.max(max, m.id), 0))
    try {
      const reply = await sendMessage.mutateAsync({
        message,
        provider: selectedProvider || undefined,
        conversation_id: activeId > 0 ? activeId : undefined,
      })
      // Nạp XONG chi tiết hội thoại trước khi bỏ tin đang chờ, để câu vừa gửi
      // không biến mất một nhịp rồi mới hiện lại từ luồng tin của server.
      await queryClient.fetchQuery({
        queryKey: queryKeys.assistant.conversation(reply.conversation_id),
        queryFn: () => assistantApi.conversation(reply.conversation_id),
      })

      //  Trợ lý vừa soạn xong bản nháp YCBG/YCMH (rows != null nghĩa là tool chạy thành
      //  công, không bị từ chối quyền) -> chào nút mở form. Lượt sau không soạn thì gỡ nút.
      const draftTargets: Record<string, 'survey' | 'purchase' | 'leave'> = {
        draft_survey_request: 'survey',
        draft_purchase_request: 'purchase',
        draft_leave_request: 'leave',
      }
      const draftCall = (reply.tool_calls ?? [])
        .filter((call) => draftTargets[call.name] != null && call.rows != null && call.rows > 0)
        .at(-1)
      setDraftOffer(
        draftCall
          ? //  Ưu tiên bản draft ĐÃ CHUẨN HÓA từ kết quả tool (ĐVT khớp chính tả danh mục
            //  "cái" -> "Cái", mã hàng khớp danh mục); args thô của model chỉ là dự phòng.
            {
              conversationId: reply.conversation_id,
              args: draftCall.draft ?? draftCall.args,
              target: draftTargets[draftCall.name],
            }
          : null,
      )

      //  Trợ lý vừa xuất file báo cáo -> chào nút tải. Lượt sau không xuất thì gỡ nút.
      const fileCall = (reply.tool_calls ?? [])
        .filter((call) => call.name === 'export_report_file' && call.file != null)
        .at(-1)
      setFileOffer(
        fileCall?.file
          ? {
              conversationId: reply.conversation_id,
              filename: fileCall.file.filename,
              downloadUrl: fileCall.file.download_url,
            }
          : null,
      )
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
                <ChatEmptyState onPick={isSending ? undefined : (question) => void handleSend(question).catch(() => {})} />
              ) : (
                <MessageThread
                  messages={messages}
                  pending={pending}
                  isSending={isSending}
                  typingAfterId={typingAfterId}
                />
              )}

              {/*  Bản nháp YCBG/YCMH/đơn nghỉ phép trợ lý vừa soạn — bấm mới mở form ĐÃ
                   ĐIỀN SẴN, người dùng rà lại rồi tự bấm Tạo trong form; ở đây chưa có
                   phiếu nào được tạo. */}
              {draftOffer && draftOffer.conversationId === activeId && !isSending ? (
                <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
                  <p className="text-xs text-muted-foreground">
                    Trợ lý đã soạn sẵn nội dung phiếu. Mở form để kiểm tra rồi bấm Tạo.
                  </p>
                  <Button
                    size="sm"
                    onClick={() =>
                      navigate(
                        {
                          survey: appRoutes.procurement.surveyRequestNew,
                          purchase: appRoutes.procurement.purchaseRequestNew,
                          leave: appRoutes.document.documentNew,
                        }[draftOffer.target],
                        { state: { assistantDraft: draftOffer.args } },
                      )
                    }
                  >
                    <FilePlus />
                    {
                      {
                        survey: 'Tạo yêu cầu báo giá',
                        purchase: 'Tạo yêu cầu mua hàng',
                        leave: 'Tạo đơn nghỉ phép',
                      }[draftOffer.target]
                    }
                  </Button>
                </div>
              ) : null}

              {/*  File báo cáo trợ lý vừa xuất — file ĐÃ nằm trên máy chủ, nút chỉ tải về. */}
              {fileOffer && fileOffer.conversationId === activeId && !isSending ? (
                <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5">
                  <p className="min-w-0 truncate text-xs text-muted-foreground">
                    Trợ lý đã tạo file báo cáo: {fileOffer.filename}
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      void downloadFile(fileOffer.downloadUrl, fileOffer.filename).catch(() => {})
                    }
                  >
                    <FileDown />
                    Tải báo cáo
                  </Button>
                </div>
              ) : null}

              <ChatComposer disabled={noProvider} busy={isSending} onSend={handleSend} />
            </>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
