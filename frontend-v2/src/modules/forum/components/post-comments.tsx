import { ChevronDown, ChevronUp, Paperclip, Send, Trash2, X } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ImageLightbox, useImageLightbox } from '@/shared/ui/image-lightbox'
import {
  MentionInput,
  type MentionInputHandle,
} from '@/shared/ui/mention-input'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import {
  fetchCommentReplies,
  fetchPostComments,
  searchMentionablePeople,
  toggleCommentLike,
  deletePostComment,
  type ForumComment,
  type ForumCommentMention,
} from '../api/forum-comment-api'
import {
  useCreateForumComment,
  useForumCommentActions,
  useForumComments,
} from '../hooks/use-forum-comments'
import { authorInitials } from '../utils/author-initials'

interface PostCommentsProps {
  postId: number
  /** Nằm trong popup chi tiết: bỏ viền/bóng của thẻ — khung dialog đã có sẵn. */
  flat?: boolean
}

/**
 * Khối bình luận dưới một bài viết (F4) — chạy trên bộ máy bình luận dùng chung
 * `/api/comments` (entity `forum_post`), cùng luật với luồng trao đổi chứng từ:
 * 2 tầng gốc–phản hồi, `@` nhắc tên, thích, tệp đính kèm, xóa của mình.
 * Khác `DocumentComments` của thu mua ở lớp áo: bong bóng kiểu mạng xã hội,
 * không bọc Card chứng từ.
 */
export function PostComments({ postId, flat = false }: PostCommentsProps) {
  const { user } = useAuth()
  const { data, isLoading, isError } = useForumComments(postId)
  const createComment = useCreateForumComment(postId)
  const { toggleLike, remove } = useForumCommentActions(postId)
  const [files, setFiles] = useState<File[]>([])
  const [olderRoots, setOlderRoots] = useState<ForumComment[]>([])
  const [olderCount, setOlderCount] = useState(0)

  if (useHasChanged(data?.older_count)) setOlderCount(data?.older_count ?? 0)

  const searchMentionable = useCallback(
    (query: string) => searchMentionablePeople(postId, query),
    [postId],
  )

  async function sendRoot(body: string) {
    if (!body && !files.length) return
    await createComment.mutateAsync({ body, files })
    setFiles([])
  }

  async function loadOlder() {
    const beforeId = olderRoots[0]?.id ?? data?.oldest_id ?? 0
    if (!beforeId) return
    const page = await fetchPostComments(postId, beforeId)
    setOlderRoots((current) => [...page.items, ...current])
    setOlderCount(page.older_count)
  }

  const roots = [...olderRoots, ...(data?.items ?? [])]

  return (
    <section
      aria-label="Bình luận"
      className={cn(
        'bg-card px-4 py-3',
        flat
          ? 'border-t border-border/70'
          : 'mt-3 border-y border-border shadow-sm sm:rounded-xl sm:border',
      )}
    >
      {isLoading && <Skeleton className="h-24 w-full" />}
      {isError && <p className="text-sm text-destructive">Không tải được bình luận.</p>}

      {olderCount > 0 && (
        <button
          type="button"
          className="mb-3 text-sm font-medium text-muted-foreground hover:text-foreground hover:underline"
          onClick={() => void loadOlder()}
        >
          Xem {Math.min(olderCount, 10)} bình luận trước
        </button>
      )}

      {!isLoading && !isError && roots.length === 0 && (
        <p className="pb-1 text-sm text-muted-foreground">
          Chưa có bình luận nào. Hãy là người đầu tiên.
        </p>
      )}

      {!!roots.length && (
        <div className="space-y-3">
          {roots.map((comment) => (
            <CommentThread
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
    </section>
  )
}

function CommentThread({
  comment,
  currentUserName,
  searchMentionable,
  onLike,
  onDelete,
  onReply,
}: {
  comment: ForumComment
  currentUserName: string
  searchMentionable: (query: string) => ReturnType<typeof searchMentionablePeople>
  onLike: () => void
  onDelete: () => void
  onReply: (body: string, files: File[]) => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const [replying, setReplying] = useState(false)
  const [replies, setReplies] = useState<ForumComment[]>([])
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
        setReplies(await fetchCommentReplies(comment.id))
      } finally {
        setLoadingReplies(false)
      }
    }
    setOpen(true)
  }

  async function sendReply(body: string) {
    if (!body && !replyFiles.length) return
    await onReply(body, replyFiles)
    setReplies(await fetchCommentReplies(comment.id))
    setReplyFiles([])
    setReplying(false)
    setOpen(true)
  }

  async function likeReply(replyId: number) {
    const result = await toggleCommentLike(replyId)
    setReplies((current) =>
      current.map((reply) =>
        reply.id === replyId
          ? { ...reply, liked: result.liked, like_count: result.count }
          : reply,
      ),
    )
  }

  async function deleteReply(replyId: number) {
    await deletePostComment(replyId)
    setReplies((current) => current.filter((reply) => reply.id !== replyId))
  }

  return (
    <div>
      <CommentRow
        comment={comment}
        onLike={onLike}
        onDelete={onDelete}
        onReply={() => setReplying(true)}
      />

      {!!comment.reply_count && (
        <button
          type="button"
          className="ml-11 mt-1 flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground hover:underline"
          onClick={() => void toggleReplies()}
        >
          {open ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
          {comment.reply_count} phản hồi
        </button>
      )}

      {(open || replying) && (
        <div className="ml-11 mt-2 space-y-2 border-l-2 border-border/60 pl-3">
          {loadingReplies && <Skeleton className="h-14 w-full" />}
          {open &&
            replies.map((reply) => (
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
    </div>
  )
}

function CommentRow({
  comment,
  compact,
  onLike,
  onDelete,
  onReply,
}: {
  comment: ForumComment
  compact?: boolean
  onLike: () => void
  onDelete: () => void
  onReply: () => void
}) {
  return (
    <div className="flex gap-2.5">
      <Avatar className={compact ? 'size-7' : 'size-9'}>
        <AvatarImage
          className="object-cover"
          src={comment.author_avatar}
          alt={comment.author_name}
        />
        <AvatarFallback className="bg-navy-solid text-xs font-semibold text-white">
          {authorInitials(comment.author_name)}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <div className="inline-block max-w-full rounded-2xl bg-muted px-3 py-2">
          <b className="block text-[13px] leading-4 text-navy dark:text-foreground">
            {comment.author_name || 'Không rõ'}
            {!!comment.author_code && (
              <span className="ml-1.5 font-normal text-muted-foreground">
                {comment.author_code}
              </span>
            )}
          </b>
          {!!comment.body && (
            <p className="mt-0.5 whitespace-pre-wrap break-words text-sm leading-5">
              {renderCommentBody(comment.body, comment.mentions)}
            </p>
          )}
        </div>
        <CommentFiles files={comment.files} />
        <div className="mt-0.5 flex items-center gap-3 pl-3 text-xs text-muted-foreground">
          <button
            type="button"
            className={cn(
              'font-semibold hover:underline',
              comment.liked && 'text-primary',
            )}
            onClick={onLike}
          >
            Thích
          </button>
          {!!comment.like_count && <span>{comment.like_count} lượt thích</span>}
          <button type="button" className="font-semibold hover:underline" onClick={onReply}>
            Phản hồi
          </button>
          <span title={formatDateTime(comment.created_at)}>
            {formatRelativeTime(comment.created_at)}
          </span>
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
  searchMentionable: (query: string) => ReturnType<typeof searchMentionablePeople>
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
    <div className={cn('space-y-2', compact ? 'pt-1' : 'mt-3 border-t pt-3')}>
      <MentionInput
        ref={editorRef}
        placeholder={placeholder}
        search={searchMentionable}
        className={compact ? 'min-h-12' : 'min-h-14'}
        onEmptyChange={setEmpty}
        onSubmit={send}
        onCancel={onCancel}
      />
      {!!files.length && (
        <div className="flex flex-wrap gap-2">
          {files.map((file, index) => (
            <span
              key={`${file.name}-${index}`}
              className="inline-flex max-w-64 items-center gap-1 rounded-md bg-muted px-2 py-1 text-xs"
            >
              <Paperclip className="size-3.5 shrink-0" />
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

function CommentFiles({ files }: { files: ForumComment['files'] }) {
  const imageFiles = (files ?? []).filter((file) => file.is_image)
  const lightbox = useImageLightbox()
  if (!files?.length) return null
  return (
    <div className="mt-1.5 flex flex-wrap gap-2">
      {files.map((file) =>
        file.is_image ? (
          <button
            key={file.link_id}
            type="button"
            title={file.filename}
            onClick={() => lightbox.openAt(imageFiles.indexOf(file))}
            className="block leading-none"
          >
            <img
              className="size-20 rounded-md border object-cover"
              src={file.url}
              alt={file.filename}
            />
          </button>
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
      {imageFiles.length > 0 && (
        <ImageLightbox
          images={imageFiles.map((f) => ({ url: f.url, name: f.filename }))}
          {...lightbox.bind}
        />
      )}
    </div>
  )
}

function renderCommentBody(body: string, mentions: ForumCommentMention[]) {
  if (!body.includes('@[')) return body
  const names = new Map(mentions.map((mention) => [mention.user_id, mention.name]))
  const output: Array<string | React.ReactNode> = []
  const pattern = /@\[(\d+)\]/g
  let cursor = 0
  let match: RegExpExecArray | null
  while ((match = pattern.exec(body))) {
    if (match.index > cursor) output.push(body.slice(cursor, match.index))
    output.push(
      <span
        key={match.index}
        className="rounded bg-primary/10 px-1.5 py-0.5 font-medium text-primary"
      >
        @{names.get(Number(match[1])) || 'không rõ'}
      </span>,
    )
    cursor = match.index + match[0].length
  }
  output.push(body.slice(cursor))
  return output
}
