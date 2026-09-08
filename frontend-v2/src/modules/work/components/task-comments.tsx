import { AtSign, ImageIcon, Loader2, MessageSquare, Paperclip, Send, Trash2, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { MentionInput, type MentionInputHandle } from '@/shared/ui/mention-input'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { taskSupportApi } from '../api/task-support-api'
import {
  useCreateTaskComment,
  useDeleteTaskComment,
  useTaskComments,
} from '../hooks/use-task-support'
import type { TaskComment } from '../types/task-support'
import { mergePendingFiles } from '../utils/merge-pending-files'
import { parseCommentBody } from '../utils/parse-comment-body'
import { initials } from '../utils/people'

interface TaskCommentsProps {
  taskId: number
  /** Cần cho việc làm mới huy hiệu số bình luận trên thẻ kanban. */
  listId: number
}

/** Trần tệp mỗi bình luận — backend cũng chặn đúng con số này (`MAX_FILES`). */
const MAX_FILES = 5

/**
 * Khối BÌNH LUẬN của một công việc (E-01), đặt trên «Lịch sử thao tác».
 *
 * Danh sách PHẲNG theo thời gian, không luồng trả lời: panel rộng 576px, thụt
 * thêm một cấp là câu chữ còn hơn nửa bề ngang. Backend vẫn hỗ trợ trả lời 2 cấp
 * (`parent_id`) nếu sau này cần bung ra.
 *
 * Dùng chung `/api/comments` với mọi phân hệ khác — xem `api/task-support-api.ts`.
 */
export function TaskComments({ taskId, listId }: TaskCommentsProps) {
  const { data, isLoading, loadOlder } = useTaskComments(taskId)
  const remove = useDeleteTaskComment(taskId, listId)

  const items = data?.items ?? []
  const olderCount = data?.older_count ?? 0

  return (
    <section className="space-y-2">
      <h3 className="flex items-center gap-2 text-sm font-medium">
        <MessageSquare className="size-4 text-muted-foreground" />
        Bình luận
        {data && data.total > 0 && (
          <span className="text-xs font-normal text-muted-foreground">{data.total}</span>
        )}
      </h3>

      {isLoading && <Skeleton className="h-16 w-full" />}

      {!isLoading && items.length === 0 && (
        <p className="text-xs text-muted-foreground">Chưa có bình luận nào.</p>
      )}

      {olderCount > 0 && (
        <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={loadOlder}>
          Xem {olderCount} bình luận trước
        </Button>
      )}

      <ol className="space-y-3">
        {items.map((comment) => (
          <CommentRow
            key={comment.id}
            comment={comment}
            deleting={remove.isPending && remove.variables === comment.id}
            onDelete={() => remove.mutate(comment.id)}
          />
        ))}
      </ol>
    </section>
  )
}

function CommentRow({
  comment,
  deleting,
  onDelete,
}: {
  comment: TaskComment
  deleting: boolean
  onDelete: () => void
}) {
  return (
    <li className="group/cmt flex gap-2">
      <span
        aria-hidden
        className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full border bg-accent text-[10px] font-medium text-accent-foreground"
      >
        {initials(comment.author_name)}
      </span>

      <div className="min-w-0 flex-1">
        <p className="flex items-baseline gap-2 text-xs">
          <b className="font-medium text-foreground">{comment.author_name}</b>
          <span className="text-muted-foreground" title={formatDateTime(comment.created_at)}>
            {formatRelativeTime(comment.created_at)}
          </span>
          {comment.can_delete && (
            //  Hiện khi rê chuột hoặc khi bàn phím đang ở trong dòng — chỉ dựa
            //  vào `hover` thì người đi bằng phím không bao giờ tới được nút.
            <IconTooltip label="Xóa bình luận">
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Xóa bình luận"
                disabled={deleting}
                onClick={onDelete}
                className="ml-auto opacity-0 transition-opacity group-hover/cmt:opacity-100 focus-visible:opacity-100"
              >
                <Trash2 className="size-3.5 text-destructive" />
              </Button>
            </IconTooltip>
          )}
        </p>

        {/*  `whitespace-pre-wrap` giữ lại xuống dòng người ta gõ; `break-words`
             cho chuỗi dài không dấu cách (đường link dán vào) không phá khung. */}
        <p className="text-sm leading-snug break-words whitespace-pre-wrap">
          {parseCommentBody(comment.body, comment.mentions).map((seg, i) =>
            seg.kind === 'text' ? (
              <span key={i}>{seg.text}</span>
            ) : (
              <span key={i} className="rounded bg-primary/10 px-1 py-0.5 font-medium text-primary">
                @{seg.name}
              </span>
            ),
          )}
        </p>

        {comment.files.length > 0 && (
          <ul className="mt-1 space-y-1">
            {comment.files.map((file) =>
              file.is_image ? (
                /*  Ảnh HIỆN THẲNG, đúng lối Lark: ảnh chụp màn hình là thứ dán
                    vào bình luận nhiều nhất, bắt bấm tải về mới xem được thì
                    mất hẳn nghĩa "nhìn phát là hiểu". Tệp khác vẫn chỉ một dòng
                    tên — xem trước một file .xlsx thì chẳng để làm gì.  */
                <li key={file.link_id}>
                  <img
                    src={file.url}
                    alt={file.filename}
                    loading="lazy"
                    className="max-h-56 w-auto max-w-full rounded border object-contain"
                  />
                </li>
              ) : (
                <li key={file.link_id} className="flex items-center gap-1.5 text-xs">
                  <Paperclip className="size-3 shrink-0 text-muted-foreground" />
                  <span className="min-w-0 truncate" title={file.filename}>
                    {file.filename}
                  </span>
                  <span className="shrink-0 text-muted-foreground">
                    {formatFileSize(file.size)}
                  </span>
                </li>
              ),
            )}
          </ul>
        )}
      </div>
    </li>
  )
}

/**
 * Ô soạn bình luận: `MentionInput` + kẹp tệp + nút Gửi.
 *
 * Ô nhập chạy KHÔNG ĐIỀU KHIỂN (nội dung lấy qua `ref` lúc gửi) — bọc
 * `contenteditable` bằng state là bộ gõ tiếng Việt nhảy dấu, xem `MentionInput`.
 */
export function TaskCommentComposer({ taskId, listId }: { taskId: number; listId: number }) {
  const boxRef = useRef<MentionInputHandle>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const imageRef = useRef<HTMLInputElement>(null)
  const [empty, setEmpty] = useState(true)
  const [files, setFiles] = useState<File[]>([])
  const create = useCreateTaskComment(taskId, listId)

  //  Gửi được khi có CHỮ hoặc có TỆP: "đây, bản báo giá vừa nhận" là một câu
  //  trọn nghĩa dù không gõ chữ nào. Backend cũng nhận đúng luật này.
  const canSend = (!empty || files.length > 0) && !create.isPending

  /** Gom tệp từ MỌI đường vào (chọn tay · dán · kéo thả) qua đúng một cửa. */
  function addFiles(picked: File[]) {
    if (!picked.length) return
    setFiles((prev) => mergePendingFiles(prev, picked, MAX_FILES))
  }

  function send() {
    const body = boxRef.current?.getValue() ?? ''
    if (!body.trim() && files.length === 0) return
    create.mutate(
      { body, files },
      {
        onSuccess: () => {
          boxRef.current?.clear()
          setFiles([])
        },
      },
    )
  }

  return (
    /*  MỘT khung bao cả ô nhập lẫn hàng nút, đúng khuôn Lark: hai khối rời thì
        mắt đọc ra hai thứ khác nhau, mà chúng là một cụm soạn thảo. Viền vẽ ở
        khung NGOÀI và ô nhập bên trong bỏ viền — không thì thành hai nét lồng
        nhau. Sáng lên khi ô nhập có tiêu điểm (`focus-within`).  */
    <div className="rounded-md border bg-background focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50">
      <MentionInput
        ref={boxRef}
        placeholder="Viết bình luận, gõ @ để nhắc tên…"
        className="min-h-9 rounded-none border-0 px-3 py-2 text-sm shadow-none focus-visible:border-0 focus-visible:ring-0"
        //  Dán ảnh chụp màn hình và kéo thả tệp thẳng vào ô — xem `MentionInput`.
        onFiles={addFiles}
        search={(q) =>
          taskSupportApi
            .listMentionable(taskId, q)
            //  `MentionPerson` của ô nhập chỉ cần bốn trường này.
            .then((people) =>
              people.map((p) => ({
                user_id: p.user_id,
                name: p.name,
                code: p.code,
                related: p.related,
              })),
            )
        }
        onEmptyChange={setEmpty}
        onSubmit={send}
      />

      {files.length > 0 && (
        <ul className="flex flex-wrap gap-1 px-3 pb-1.5">
          {files.map((file, i) => (
            <li
              key={`${file.name}-${i}`}
              className="flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-xs"
            >
              <span className="max-w-40 truncate">{file.name}</span>
              <button
                type="button"
                aria-label={`Bỏ tệp: ${file.name}`}
                onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                className="rounded p-0.5 hover:bg-accent"
              >
                <X className="size-3" />
              </button>
            </li>
          ))}
        </ul>
      )}

      {/*  Hàng nút nằm TRONG khung, dồn sang phải — đúng chỗ Lark đặt. */}
      <div className="flex items-center justify-end gap-0.5 px-2 pb-1.5">
        <HiddenFilePicker inputRef={fileRef} onFiles={addFiles} />
        <HiddenFilePicker inputRef={imageRef} onFiles={addFiles} accept="image/*" />

        {/*  Nút `@`: người dùng chuột thuần không đoán được là phải GÕ `@`. */}
        <IconTooltip label="Nhắc tên ai đó">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Nhắc tên ai đó"
            onClick={() => boxRef.current?.insertMentionTrigger()}
          >
            <AtSign className="size-4" />
          </Button>
        </IconTooltip>

        <IconTooltip label="Chèn ảnh">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Chèn ảnh"
            disabled={files.length >= MAX_FILES}
            onClick={() => imageRef.current?.click()}
          >
            <ImageIcon className="size-4" />
          </Button>
        </IconTooltip>

        <IconTooltip label={`Kẹp tệp (tối đa ${MAX_FILES})`}>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Kẹp tệp vào bình luận"
            disabled={files.length >= MAX_FILES}
            onClick={() => fileRef.current?.click()}
          >
            <Paperclip className="size-4" />
          </Button>
        </IconTooltip>

        <span aria-hidden className="mx-1 h-4 w-px bg-border" />

        <IconTooltip label="Gửi (Ctrl + Enter)">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Gửi bình luận"
            disabled={!canSend}
            onClick={send}
            className="text-primary hover:text-primary disabled:text-muted-foreground"
          >
            {create.isPending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </IconTooltip>
      </div>
    </div>
  )
}

/**
 * Ô chọn tệp ẨN — mỗi nút một cái, khác nhau ở bộ lọc `accept`.
 *
 * `aria-hidden` + `tabIndex={-1}`: ô nằm ngoài luồng nhìn thấy, để nó nhận được
 * tiêu điểm là người đi bằng phím lạc vào một ô không thấy gì.
 */
function HiddenFilePicker({
  inputRef,
  onFiles,
  accept,
}: {
  inputRef: React.RefObject<HTMLInputElement | null>
  onFiles: (files: File[]) => void
  accept?: string
}) {
  return (
    <input
      ref={inputRef}
      type="file"
      multiple
      accept={accept}
      className="hidden"
      aria-hidden
      tabIndex={-1}
      onChange={(su) => {
        onFiles(Array.from(su.target.files ?? []))
        //  Dọn để chọn LẠI đúng tệp vừa bỏ ra vẫn kích hoạt `change`.
        su.target.value = ''
      }}
    />
  )
}
