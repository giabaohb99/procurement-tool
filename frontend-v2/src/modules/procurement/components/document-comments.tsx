import {
  ChevronDown,
  ChevronUp,
  File,
  MessageCircle,
  Paperclip,
  Send,
  ThumbsUp,
  Trash2,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import {
  MentionInput,
  type MentionInputHandle,
  type MentionPerson,
} from '@/shared/ui/mention-input'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'
import {
  purchaseRequestSupportApi,
  type CommentMention,
  type PurchaseRequestComment,
} from '../api/purchase-request-support-api'
import {
  useCreateDocumentComment,
  useDocumentCommentActions,
  useDocumentComments,
} from '../hooks/use-purchase-request-support'

interface DocumentCommentsProps {
  /** `purchase_request` hoặc `purchase_order`. */
  entity: string
  entityId: number
}

/** Luồng trao đổi của một chứng từ — dùng chung cho YCMH và ĐMH. */
export function DocumentComments({ entity, entityId }: DocumentCommentsProps) {
  const { user } = useAuth()
  const { data, isLoading, isError } = useDocumentComments(entity, entityId)
  const createComment = useCreateDocumentComment(entity, entityId)
  const { toggleLike, remove } = useDocumentCommentActions(entity, entityId)
  const [files, setFiles] = useState<File[]>([])
  const [olderRoots, setOlderRoots] = useState<PurchaseRequestComment[]>([])
  const [olderCount, setOlderCount] = useState(0)

  useEffect(() => {
    setOlderCount(data?.older_count ?? 0)
  }, [data?.older_count])

  const searchMentionable = useCallback(
    (query: string) => purchaseRequestSupportApi.listMentionable(entity, entityId, query),
    [entity, entityId],
  )

  async function sendRoot(body: string) {
    if (!body && !files.length) return
    await createComment.mutateAsync({ body, files })
    setFiles([])
  }

  async function loadOlder() {
    const beforeId = olderRoots[0]?.id ?? data?.oldest_id ?? 0
    if (!beforeId) return
    const page = await purchaseRequestSupportApi.listComments(entity, entityId, beforeId)
    setOlderRoots((current) => [...page.items, ...current])
    setOlderCount(page.older_count)
  }

  const roots = [...olderRoots, ...(data?.items ?? [])]

  return (
    <Card className="gap-4 py-4">
      {/* Xem ghi chú về `pb-3!` ở `purchase-request-attachments-card.tsx`. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
          <MessageCircle className="size-4 text-primary" />
          Trao đổi
          {!!data?.total && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {data.total}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 px-4">
        {isLoading && <Skeleton className="h-28 w-full" />}
        {isError && <p className="text-sm text-destructive">Không tải được nội dung trao đổi.</p>}

        {olderCount > 0 && (
          <Button variant="outline" size="sm" onClick={() => void loadOlder()}>
            Xem thêm {Math.min(olderCount, 10)} bình luận trước
          </Button>
        )}

        {!isLoading && !isError && roots.length === 0 && (
          <p className="text-sm leading-6 text-muted-foreground">
            Chưa có trao đổi nào. Ghi chú và câu hỏi liên quan đến phiếu được lưu tại đây.
          </p>
        )}

        {!!roots.length && (
          <div className="space-y-3">
            {roots.map((comment) => (
              <CommentThreadItem
                key={comment.id}
                comment={comment}
                currentUserName={user?.full_name ?? ''}
                searchMentionable={searchMentionable}
                onLike={() => toggleLike.mutate(comment.id)}
                onDelete={() => void remove.mutateAsync(comment.id)}
                onReply={async (text, replyFiles) => {
                  await createComment.mutateAsync({
                    body: text,
                    parentId: comment.id,
                    files: replyFiles,
                  })
                }}
              />
            ))}
          </div>
        )}

        <CommentComposer
          files={files}
          pending={createComment.isPending}
          placeholder="Viết bình luận… gõ @ để nhắc tên"
          searchMentionable={searchMentionable}
          onFilesChange={setFiles}
          onSend={(body) => void sendRoot(body)}
        />
      </CardContent>
    </Card>
  )
}

function CommentThreadItem({
  comment,
  currentUserName,
  searchMentionable,
  onLike,
  onDelete,
  onReply,
}: {
  comment: PurchaseRequestComment
  currentUserName: string
  searchMentionable: (query: string) => Promise<MentionPerson[]>
  onLike: () => void
  onDelete: () => void
  onReply: (body: string, files: File[]) => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const [replying, setReplying] = useState(false)
  const [replies, setReplies] = useState<PurchaseRequestComment[]>([])
  const [loadingReplies, setLoadingReplies] = useState(false)
  const [replyFiles, setReplyFiles] = useState<File[]>([])

  async function toggleReplies() {
    if (open) {
      setOpen(false)
      return
    }
    if (!replies.length) {
      setLoadingReplies(true)
      try {
        setReplies(await purchaseRequestSupportApi.listReplies(comment.id))
      } finally {
        setLoadingReplies(false)
      }
    }
    setOpen(true)
  }

  async function sendReply(body: string) {
    if (!body && !replyFiles.length) return
    await onReply(body, replyFiles)
    setReplies(await purchaseRequestSupportApi.listReplies(comment.id))
    setReplyFiles([])
    setReplying(false)
    setOpen(true)
  }

  async function likeReply(replyId: number) {
    const result = await purchaseRequestSupportApi.toggleLike(replyId)
    setReplies((current) =>
      current.map((reply) =>
        reply.id === replyId
          ? { ...reply, liked: result.liked, like_count: result.count }
          : reply,
      ),
    )
  }

  async function deleteReply(replyId: number) {
    await purchaseRequestSupportApi.deleteComment(replyId)
    setReplies((current) => current.filter((reply) => reply.id !== replyId))
  }

  return (
    <article className="rounded-lg border bg-muted/35 p-4">
      <CommentRow
        comment={comment}
        onLike={onLike}
        onDelete={onDelete}
        onReply={() => setReplying(true)}
      />

      {!!comment.reply_count && (
        <Button variant="ghost" size="sm" className="ml-10 mt-2" onClick={() => void toggleReplies()}>
          {open ? <ChevronUp /> : <ChevronDown />}
          {comment.reply_count} phản hồi
        </Button>
      )}

      {(open || replying) && (
        <div className="ml-5 mt-3 space-y-3 border-l-2 pl-4">
          {loadingReplies && <Skeleton className="h-16 w-full" />}
          {open && replies.map((reply) => (
            <CommentRow
              key={reply.id}
              comment={reply}
              compact
              onLike={() => void likeReply(reply.id)}
              onDelete={() => void deleteReply(reply.id)}
              onReply={() => setReplying(true)}
            />
          ))}
          {replying && (
            <CommentComposer
              files={replyFiles}
              pending={false}
              placeholder={`Phản hồi với tư cách ${currentUserName || 'người dùng'}…`}
              compact
              searchMentionable={searchMentionable}
              onFilesChange={setReplyFiles}
              onSend={(body) => void sendReply(body)}
              onCancel={() => setReplying(false)}
            />
          )}
        </div>
      )}
    </article>
  )
}

function CommentRow({
  comment,
  compact,
  onLike,
  onDelete,
  onReply,
}: {
  comment: PurchaseRequestComment
  compact?: boolean
  onLike: () => void
  onDelete: () => void
  onReply: () => void
}) {
  return (
    <div className="flex gap-3">
      <Avatar size={compact ? 'sm' : 'default'}>
        <AvatarImage src={comment.author_avatar} alt={comment.author_name} />
        <AvatarFallback>{initials(comment.author_name)}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <b className="text-sm text-navy dark:text-foreground">{comment.author_name || 'Không rõ'}</b>
          {!!comment.author_code && <span className="text-xs text-muted-foreground">{comment.author_code}</span>}
          <span className="text-xs text-muted-foreground">{formatDateTime(comment.created_at)}</span>
        </div>
        <p className="mt-1 whitespace-pre-wrap break-words text-sm leading-6">
          {renderCommentBody(comment.body, comment.mentions)}
        </p>
        <CommentFiles files={comment.files} />
        <div className="mt-2 flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className={comment.liked ? 'text-primary' : 'text-muted-foreground'}
            onClick={onLike}
          >
            <ThumbsUp />
            {comment.like_count || 'Thích'}
          </Button>
          <Button variant="ghost" size="sm" onClick={onReply}>
            Phản hồi
          </Button>
          {comment.can_delete && (
            <ConfirmIconButton
              icon={Trash2}
              title="Xóa bình luận"
              confirmTitle="Xóa bình luận này?"
              confirmDescription={
                comment.reply_count
                  ? `Bình luận và ${comment.reply_count} phản hồi sẽ bị xóa.`
                  : 'Nội dung đã xóa không thể khôi phục.'
              }
              confirmLabel="Xóa"
              destructive
              onConfirm={onDelete}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function CommentComposer({
  files,
  pending,
  placeholder,
  compact,
  searchMentionable,
  onFilesChange,
  onSend,
  onCancel,
}: {
  files: File[]
  pending: boolean
  placeholder: string
  compact?: boolean
  searchMentionable: (query: string) => Promise<MentionPerson[]>
  onFilesChange: (files: File[]) => void
  /** Nội dung lấy từ ô soạn thảo, đã kèm thẻ `@[id]` của người được nhắc. */
  onSend: (body: string) => void
  onCancel?: () => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const editorRef = useRef<MentionInputHandle>(null)
  // Ô soạn thảo chạy uncontrolled (xem `MentionInput`), nên chỉ theo dõi RỖNG /
  // KHÔNG RỖNG để bật tắt nút Gửi — không giữ cả nội dung trong state.
  const [empty, setEmpty] = useState(true)
  const disabled = pending || (empty && !files.length)

  function send() {
    const body = editorRef.current?.getValue() ?? ''
    if (!body && !files.length) return
    onSend(body)
    editorRef.current?.clear()
  }

  return (
    <div className="space-y-2 border-t pt-4">
      <MentionInput
        ref={editorRef}
        placeholder={placeholder}
        search={searchMentionable}
        className={compact ? 'min-h-12' : undefined}
        onEmptyChange={setEmpty}
        onSubmit={send}
        onCancel={onCancel}
      />
      {!!files.length && (
        <div className="flex flex-wrap gap-2">
          {files.map((file, index) => (
            <span key={`${file.name}-${index}`} className="inline-flex max-w-64 items-center gap-1 rounded-md bg-muted px-2 py-1 text-xs">
              <File className="size-3.5 shrink-0" />
              <span className="truncate">{file.name}</span>
              <button
                type="button"
                className="text-muted-foreground hover:text-foreground"
                aria-label={`Bỏ tệp ${file.name}`}
                onClick={() => onFilesChange(files.filter((_, fileIndex) => fileIndex !== index))}
              >
                <X className="size-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          className="hidden"
          type="file"
          multiple
          onChange={(event) => {
            const selected = Array.from(event.target.files ?? [])
            onFilesChange([...files, ...selected].slice(0, 5))
            event.target.value = ''
          }}
        />
        <Button variant="ghost" size="sm" onClick={() => inputRef.current?.click()}>
          <Paperclip />
          Đính kèm
        </Button>
        <div className="ml-auto flex gap-2">
          {onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Hủy
            </Button>
          )}
          <Button size="sm" disabled={disabled} onClick={send}>
            <Send />
            {pending ? 'Đang gửi' : 'Gửi'}
          </Button>
        </div>
      </div>
    </div>
  )
}

function CommentFiles({ files }: { files: PurchaseRequestComment['files'] }) {
  if (!files?.length) return null
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {files.map((file) =>
        file.is_image ? (
          <a key={file.link_id} href={file.url} target="_blank" rel="noreferrer">
            <img
              className="size-20 rounded-md border object-cover"
              src={file.url}
              alt={file.filename}
            />
          </a>
        ) : (
          <a
            key={file.link_id}
            className="inline-flex max-w-72 items-center gap-2 rounded-md border bg-background px-2 py-1 text-xs font-medium hover:text-primary"
            href={file.url}
            target="_blank"
            rel="noreferrer"
          >
            <Paperclip className="size-3.5 shrink-0" />
            <span className="truncate">{file.filename}</span>
          </a>
        ),
      )}
    </div>
  )
}

function renderCommentBody(body: string, mentions: CommentMention[]) {
  if (!body.includes('@[')) return body
  const names = new Map(mentions.map((mention) => [mention.user_id, mention.name]))
  const output: Array<string | React.ReactNode> = []
  const pattern = /@\[(\d+)\]/g
  let cursor = 0
  let match: RegExpExecArray | null
  while ((match = pattern.exec(body))) {
    if (match.index > cursor) output.push(body.slice(cursor, match.index))
    output.push(
      <span key={match.index} className="rounded bg-primary/10 px-1.5 py-0.5 font-medium text-primary">
        @{names.get(Number(match[1])) || 'không rõ'}
      </span>,
    )
    cursor = match.index + match[0].length
  }
  output.push(body.slice(cursor))
  return output
}

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || '?'
}
