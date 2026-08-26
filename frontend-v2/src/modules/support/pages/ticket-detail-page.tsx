import {
  ArrowLeft,
  CircleCheck,
  CircleDot,
  Loader2,
  Lock,
  LockOpen,
  MessageSquare,
  MessagesSquare,
  Paperclip,
  Send,
  UserMinus,
  UserPlus,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ImageLightbox } from '@/shared/ui/image-lightbox'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { ticketApi, type UploadedFile } from '../api/ticket-api'
import {
  TicketPriorityBadge,
  TicketStatusBadge,
} from '../config/ticket-meta'
import {
  useAssignTicket,
  useReplyTicket,
  useSetTicketStatus,
  useTicket,
  useTicketAttachments,
} from '../hooks/use-tickets'
import type { TicketDetail, TicketFile, TicketMessage } from '../types/ticket'

export function TicketDetailPage() {
  const { id: idParam } = useParams()
  const id = Number(idParam)
  const navigate = useNavigate()
  const { user } = useAuth()
  const { can } = usePermission()

  // FE không giữ scope trong bản đồ quyền → mượn quyền `delete` (chỉ nhóm Hỗ trợ
  // có) làm proxy "người xử lý", đúng như bản v1.
  const isHandler = can('ticket', 'delete')
  // Người gửi thường không vào được màn quản lý → quay về tab phiếu của mình.
  const backTo = isHandler ? appRoutes.support.root : '/me?tab=tickets'

  const { data: ticket, isLoading, isError } = useTicket(id)
  const { data: attachments } = useTicketAttachments(id)

  // Ngoài phạm vi hoặc không tồn tại → báo và trả về danh sách, không để màn trắng.
  useEffect(() => {
    if (isError) {
      toast.error('Không mở được phiếu hỗ trợ (ngoài phạm vi hoặc không tồn tại)')
      navigate(backTo)
    }
  }, [isError, navigate, backTo])

  if (isLoading || !ticket) {
    return (
      <PageContainer>
        <Skeleton className="h-40 w-full" />
        <Skeleton className="mt-4 h-72 w-full" />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <TicketDetailView
        ticket={ticket}
        attachments={attachments ?? []}
        isHandler={isHandler}
        currentUserId={user?.id ?? 0}
        onBack={() => navigate(backTo)}
      />
    </PageContainer>
  )
}

function TicketDetailView({
  ticket,
  attachments,
  isHandler,
  currentUserId,
  onBack,
}: {
  ticket: TicketDetail
  attachments: TicketFile[]
  isHandler: boolean
  currentUserId: number
  onBack: () => void
}) {
  const isClosed = ticket.status === 'closed'

  // Tin nhắn đầu tiên của người gửi CHÍNH là nội dung yêu cầu → tách lên khối
  // thông tin, phần Trao đổi chỉ còn các lượt qua lại thực sự.
  const first = ticket.messages[0]
  const desc = first && !first.is_staff ? first : null
  const thread = desc ? ticket.messages.slice(1) : ticket.messages
  const introFiles = [...attachments, ...(desc?.files ?? [])]

  const info: { label: string; value: ReactNode }[] = [
    { label: 'Mã phiếu', value: ticket.code },
    { label: 'Bộ phận / Nhóm', value: ticket.department || '—' },
    { label: 'Mức ưu tiên', value: <TicketPriorityBadge priority={ticket.priority} /> },
    { label: 'Trạng thái', value: <TicketStatusBadge status={ticket.status} /> },
    { label: 'Người gửi', value: ticket.requester_name || '—' },
    {
      label: 'Người xử lý',
      value: ticket.assignee_name || <span className="text-warning">Chưa ai nhận</span>,
    },
    { label: 'Ngày tạo', value: formatDateTime(ticket.created_at) },
    { label: 'Cập nhật', value: formatDateTime(ticket.updated_at) },
  ]
  if (ticket.closed_at) info.push({ label: 'Đã đóng', value: formatDateTime(ticket.closed_at) })

  return (
    <div className="flex flex-col gap-4">
      {/* Khối 1: thông tin yêu cầu */}
      <Card className="gap-0 overflow-hidden py-0">
        <div className="flex flex-wrap items-start gap-3 border-b p-4">
          <Button variant="outline" size="sm" className="shrink-0" onClick={onBack}>
            <ArrowLeft className="size-4" />
            Danh sách
          </Button>
          <div className="min-w-0 flex-1">
            <h1 className="flex flex-wrap items-center gap-2 text-lg font-semibold text-navy dark:text-foreground">
              <span className="truncate">{ticket.subject}</span>
              <TicketStatusBadge status={ticket.status} />
              <TicketPriorityBadge priority={ticket.priority} />
            </h1>
            <p className="mt-1 text-xs text-muted-foreground">
              {ticket.code} · {ticket.requester_name || 'Người dùng'} gửi lúc{' '}
              {formatDateTime(ticket.created_at)}
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <TicketActions
              ticket={ticket}
              isHandler={isHandler}
              isClosed={isClosed}
              currentUserId={currentUserId}
            />
          </div>
        </div>

        <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
          {info.map((row) => (
            <div key={row.label} className="min-w-0">
              <div className="mb-0.5 text-xs font-medium text-muted-foreground">{row.label}</div>
              <div className="text-sm font-medium text-navy dark:text-foreground">{row.value}</div>
            </div>
          ))}
        </div>

        <div className="px-4 pb-4">
          <div className="mb-1.5 text-xs font-medium text-muted-foreground">Nội dung yêu cầu</div>
          <div className="whitespace-pre-wrap break-words rounded-lg border bg-muted/40 p-3 text-sm leading-6 text-navy dark:text-foreground">
            {desc?.body || (
              <span className="text-muted-foreground">(người gửi không nhập mô tả)</span>
            )}
          </div>
          {introFiles.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-2">
              <TicketFileList files={introFiles} />
            </div>
          )}
        </div>
      </Card>

      {/* Khối 2: trao đổi */}
      <Card className="gap-0 overflow-hidden py-0">
        <CardHeader className="flex min-h-9 flex-row items-center gap-2 border-b p-4">
          <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
            <MessagesSquare className="size-4 text-primary" />
            Trao đổi
            {thread.length > 0 && (
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {thread.length}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <TicketThread thread={thread} isHandler={isHandler} />
          <ReplyComposer ticketId={ticket.id} isHandler={isHandler} isClosed={isClosed} />
        </CardContent>
      </Card>
    </div>
  )
}

/** Nhóm nút hành động — khác nhau giữa người xử lý và người gửi. */
function TicketActions({
  ticket,
  isHandler,
  isClosed,
  currentUserId,
}: {
  ticket: TicketDetail
  isHandler: boolean
  isClosed: boolean
  currentUserId: number
}) {
  const assign = useAssignTicket(ticket.id)
  const setStatus = useSetTicketStatus(ticket.id)
  const [confirmClose, setConfirmClose] = useState(false)
  const busy = assign.isPending || setStatus.isPending

  const closeMessage = isHandler
    ? 'Đóng phiếu hỗ trợ này?'
    : 'Bạn đã được giải quyết và muốn đóng phiếu?'

  const reopenButton = (
    <Button variant="secondary" size="sm" disabled={busy} onClick={() => setStatus.mutate('in_progress')}>
      <LockOpen className="size-4" />
      Mở lại phiếu
    </Button>
  )

  return (
    <>
      {isHandler ? (
        <>
          {!isClosed &&
            (ticket.assignee_id !== currentUserId ? (
              <Button variant="default" size="sm" disabled={busy} onClick={() => assign.mutate(currentUserId)}>
                <UserPlus className="size-4" />
                {ticket.assignee_id ? 'Nhận lại phiếu' : 'Nhận phiếu'}
              </Button>
            ) : (
              <Button variant="outline" size="sm" disabled={busy} onClick={() => assign.mutate(0)}>
                <UserMinus className="size-4" />
                Trả phiếu
              </Button>
            ))}
          {ticket.status !== 'in_progress' && !isClosed && (
            <Button variant="secondary" size="sm" disabled={busy} onClick={() => setStatus.mutate('in_progress')}>
              <CircleDot className="size-4" />
              Đang xử lý
            </Button>
          )}
          {ticket.status !== 'answered' && !isClosed && (
            <Button variant="secondary" size="sm" disabled={busy} onClick={() => setStatus.mutate('answered')}>
              <CircleCheck className="size-4" />
              Đã trả lời
            </Button>
          )}
          {!isClosed ? (
            <Button variant="default" size="sm" disabled={busy} onClick={() => setConfirmClose(true)}>
              <Lock className="size-4" />
              Đóng phiếu
            </Button>
          ) : (
            reopenButton
          )}
        </>
      ) : !isClosed ? (
        <Button variant="default" size="sm" disabled={busy} onClick={() => setConfirmClose(true)}>
          <CircleCheck className="size-4" />
          Đóng phiếu
        </Button>
      ) : (
        reopenButton
      )}

      <AlertDialog open={confirmClose} onOpenChange={setConfirmClose}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Đóng phiếu hỗ trợ</AlertDialogTitle>
            <AlertDialogDescription>{closeMessage}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction onClick={() => setStatus.mutate('closed')}>Đóng phiếu</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

function TicketThread({ thread, isHandler }: { thread: TicketMessage[]; isHandler: boolean }) {
  const scrollRef = useRef<HTMLDivElement | null>(null)

  // Cuộn xuống tin mới nhất mỗi khi có thêm lượt trao đổi.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [thread.length])

  return (
    <div
      ref={scrollRef}
      className="flex max-h-[520px] min-h-40 flex-col gap-4 overflow-y-auto bg-muted/40 p-4"
    >
      {thread.length === 0 ? (
        <div className="m-auto text-center text-sm text-muted-foreground">
          <MessageSquare className="mx-auto mb-1.5 size-7" />
          Chưa có trao đổi nào.{' '}
          {isHandler ? 'Trả lời để bắt đầu hỗ trợ.' : 'Nhóm Hỗ trợ sẽ phản hồi sớm nhất.'}
        </div>
      ) : (
        thread.map((message) => <MessageBubble key={message.id} message={message} />)
      )}
    </div>
  )
}

function MessageBubble({ message }: { message: TicketMessage }) {
  const staff = message.is_staff
  const files = message.files ?? []
  return (
    <div className={cn('flex gap-2.5', staff && 'flex-row-reverse')}>
      <Avatar size="sm" className="mt-0.5 shrink-0">
        <AvatarImage src={message.author_avatar} alt={message.author_name} className="object-cover" />
        <AvatarFallback className={cn(staff ? 'bg-primary text-primary-foreground' : 'bg-navy-solid text-white')}>
          {initials(message.author_name)}
        </AvatarFallback>
      </Avatar>
      <div className={cn('flex max-w-[78%] flex-col gap-1.5', staff ? 'items-end' : 'items-start')}>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <b className="text-navy dark:text-foreground">{message.author_name || 'Người dùng'}</b>
          {staff && (
            <Badge variant="secondary" className="border-0 bg-primary/10 px-1.5 py-0 text-[10px] text-primary">
              Hỗ trợ
            </Badge>
          )}
          <span>{formatDateTime(message.created_at)}</span>
        </div>
        {message.body && (
          <div
            className={cn(
              'whitespace-pre-wrap break-words rounded-xl border px-3.5 py-2.5 text-sm leading-6 text-navy dark:text-foreground',
              staff ? 'bg-info/10 border-info/20' : 'border-border bg-background',
            )}
          >
            {message.body}
          </div>
        )}
        {files.length > 0 && (
          <div className={cn('flex flex-wrap gap-2', staff ? 'justify-end' : 'justify-start')}>
            <TicketFileList files={files} compact />
          </div>
        )}
      </div>
    </div>
  )
}

/** Ô soạn trả lời: gõ chữ + kẹp tệp + dán ảnh + kéo-thả, tất cả trong một khung. */
function ReplyComposer({
  ticketId,
  isHandler,
  isClosed,
}: {
  ticketId: number
  isHandler: boolean
  isClosed: boolean
}) {
  const reply = useReplyTicket(ticketId)
  const [body, setBody] = useState('')
  const [draft, setDraft] = useState<UploadedFile[]>([])
  const [uploading, setUploading] = useState(false)
  const pickRef = useRef<HTMLInputElement | null>(null)

  async function upload(files: File[]) {
    if (!files.length) return
    setUploading(true)
    try {
      const uploaded = await ticketApi.uploadMessageFiles(files)
      setDraft((current) => [...current, ...uploaded])
    } catch {
      toast.error('Không tải được tệp lên. Vui lòng thử lại.')
    } finally {
      setUploading(false)
    }
  }

  async function send() {
    if (!body.trim() && !draft.length) return
    await reply.mutateAsync({ body: body.trim(), fileIds: draft.map((file) => file.file_id) })
    setBody('')
    setDraft([])
  }

  if (isClosed) {
    return (
      <div className="border-t p-3 text-center text-sm text-muted-foreground">
        <Lock className="mr-1 inline size-4 align-text-bottom" />
        Phiếu đã đóng.{' '}
        {isHandler ? 'Mở lại để tiếp tục trao đổi.' : 'Mở lại phiếu nếu bạn vẫn cần hỗ trợ.'}
      </div>
    )
  }

  return (
    <div className="border-t p-3">
      <div
        className="rounded-xl border bg-background p-2"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          void upload(Array.from(e.dataTransfer.files ?? []))
        }}
      >
        {draft.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-0.5 pb-2">
            {draft.map((file) => (
              <span
                key={file.file_id}
                className="inline-flex max-w-60 items-center gap-1.5 rounded-full bg-muted py-1 pl-3 pr-1.5 text-xs"
              >
                <span className="min-w-0 truncate font-medium text-navy dark:text-foreground">
                  {file.filename}
                </span>
                <span className="text-muted-foreground">{formatFileSize(file.size)}</span>
                <button
                  type="button"
                  className="text-muted-foreground hover:text-destructive"
                  aria-label={`Bỏ tệp ${file.filename}`}
                  onClick={() => setDraft((current) => current.filter((f) => f.file_id !== file.file_id))}
                >
                  <X className="size-3.5" />
                </button>
              </span>
            ))}
          </div>
        )}
        <Textarea
          value={body}
          rows={2}
          placeholder="Nhập nội dung trả lời… (kéo thả tệp vào đây hoặc dán ảnh bằng Ctrl/⌘ + V)"
          className="min-h-13 resize-y border-0 bg-transparent px-1.5 shadow-none focus-visible:ring-0 dark:bg-transparent"
          onChange={(e) => setBody(e.target.value)}
          onPaste={(e) => {
            const images = Array.from(e.clipboardData?.files ?? []).filter((f) =>
              f.type.startsWith('image/'),
            )
            if (!images.length) return
            e.preventDefault()
            void upload(images)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              e.preventDefault()
              void send()
            }
          }}
        />
        <div className="flex items-center gap-2 pt-1">
          <input
            ref={pickRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              void upload(Array.from(e.target.files ?? []))
              e.target.value = ''
            }}
          />
          <Button
            variant="ghost"
            size="icon"
            disabled={uploading}
            title="Đính kèm tệp"
            onClick={() => pickRef.current?.click()}
          >
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Paperclip className="size-4" />}
          </Button>
          <span className="flex-1 text-xs text-muted-foreground">
            {uploading ? 'Đang tải tệp lên…' : 'Ctrl/⌘ + Enter để gửi nhanh · tối đa 50MB mỗi tệp'}
          </span>
          <Button
            size="sm"
            disabled={reply.isPending || uploading || (!body.trim() && !draft.length)}
            onClick={() => void send()}
          >
            {reply.isPending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Gửi
          </Button>
        </div>
      </div>
    </div>
  )
}

/**
 * Danh sách tệp của một cụm (mô tả đầu phiếu hoặc một tin nhắn). Ảnh mở bằng
 * lightbox tại chỗ và chuyển qua lại trong CÙNG cụm; tệp khác vẫn mở tab mới.
 */
function TicketFileList({ files, compact }: { files: TicketFile[]; compact?: boolean }) {
  const images = files.filter(isImage)
  const [lightbox, setLightbox] = useState<number | null>(null)

  return (
    <>
      {files.map((file) =>
        isImage(file) ? (
          <button
            key={file.id}
            type="button"
            title={file.filename}
            onClick={() => setLightbox(images.indexOf(file))}
            className="block overflow-hidden rounded-lg border leading-none"
          >
            <img
              src={file.url}
              alt={file.filename}
              className={cn('block max-h-44 object-cover', compact ? 'max-w-50' : 'max-w-60')}
            />
          </button>
        ) : (
          <TicketFileChip key={file.id} file={file} />
        ),
      )}
      {images.length > 0 && (
        <ImageLightbox
          images={images.map((f) => ({ url: f.url, name: f.filename }))}
          index={lightbox ?? 0}
          open={lightbox !== null}
          onOpenChange={(o) => {
            if (!o) setLightbox(null)
          }}
          onIndexChange={setLightbox}
        />
      )}
    </>
  )
}

/** Một tệp KHÔNG phải ảnh: thẻ bấm mở tab mới. */
function TicketFileChip({ file }: { file: TicketFile }) {
  return (
    <a
      href={file.url}
      target="_blank"
      rel="noreferrer"
      title={file.filename}
      className="inline-flex max-w-64 items-center gap-2 rounded-lg border bg-background px-2.5 py-1.5 text-xs font-medium hover:text-primary"
    >
      <Paperclip className="size-3.5 shrink-0" />
      <span className="min-w-0 truncate">{file.filename}</span>
      <span className="shrink-0 text-muted-foreground">{formatFileSize(file.size)}</span>
    </a>
  )
}

function isImage(file: TicketFile): boolean {
  return (
    file.content_type.startsWith('image/') ||
    /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(file.filename)
  )
}

function initials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(-2)
      .map((part) => part[0]?.toUpperCase())
      .join('') || '?'
  )
}
