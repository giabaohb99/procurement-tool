import { Download, FileText, Loader2, X } from 'lucide-react'
import { useRef } from 'react'

import { downloadFile } from '@/core/api/download-file'
import { logger } from '@/core/telemetry/logger'
import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatFileSize } from '@/shared/utils/format-file-size'
import {
  useDeleteTaskAttachment,
  useTaskAttachments,
  useUploadTaskAttachments,
} from '../hooks/use-task-support'
import type { TaskAttachment } from '../types/task-support'

interface TaskAttachmentsProps {
  taskId: number
  /** Khách xem vẫn TẢI được tệp, chỉ không thêm/gỡ — xem `_ensure_task_member`. */
  canEdit: boolean
}

/**
 * Đính kèm ở cấp CÔNG VIỆC (E-03) — một hàng thuộc tính trong panel chi tiết.
 *
 * Dáng bám Lark: một dòng bấm **«Thêm đính kèm»** đặt ngay dưới «Thêm việc con»,
 * KHÔNG phải một hộp kéo-thả to. Panel này là dải thuộc tính mỗi thứ một dòng;
 * nhét vào giữa một khung nét đứt cao 60px thì nó nuốt hết chỗ của những hàng
 * còn lại, mà phần lớn việc chẳng có tệp nào để mà cần một bãi thả rộng thế.
 *
 * Dùng thẳng `/api/attachments` với `entity = "work_task"`; quyền do backend gác
 * theo tư cách thành viên dự án (`core/attachment_scope._ensure_task_member`),
 * `canEdit` ở đây chỉ là lớp áo cho đỡ bày ra nút bấm không ăn.
 */
export function TaskAttachments({ taskId, canEdit }: TaskAttachmentsProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const { data: files = [], isLoading } = useTaskAttachments(taskId)
  const upload = useUploadTaskAttachments(taskId)
  const remove = useDeleteTaskAttachment(taskId)

  if (isLoading) return <Skeleton className="h-7 w-40" />

  return (
    <div className="w-full space-y-0.5">
      <ul className="space-y-0.5">
        {files.map((file) => (
          <AttachmentRow
            key={file.id}
            file={file}
            canEdit={canEdit}
            removing={remove.isPending && remove.variables === file.id}
            onRemove={() => remove.mutate(file.id)}
          />
        ))}
      </ul>

      {files.length === 0 && !canEdit && (
        <p className="text-sm text-muted-foreground">Chưa có tệp nào.</p>
      )}

      {canEdit && (
        <>
          <input
            ref={fileRef}
            type="file"
            multiple
            className="hidden"
            //  ⚠️ `aria-hidden` + `tabIndex={-1}`: ô này nằm ngoài luồng nhìn
            //  thấy, để nó nhận được tiêu điểm là người đi bằng phím lạc vào một
            //  ô không thấy gì.
            aria-hidden
            tabIndex={-1}
            onChange={(su) => {
              const picked = Array.from(su.target.files ?? [])
              if (picked.length) upload.mutate(picked)
              //  Dọn để chọn LẠI đúng tệp vừa gỡ vẫn kích hoạt `change`.
              su.target.value = ''
            }}
          />
          {/*  MỘT biểu tượng thôi — cái ở máng trái của hàng (`TaskDetailRow`)
               đã nói rõ đây là đính kèm rồi. Đặt thêm một cái kẹp giấy nữa ngay
               trước chữ là hai biểu tượng giống hệt nhau nằm cạnh nhau, mà chữ
               thì thụt vào so với «Thêm việc con» ở hàng trên — hai dòng cùng
               kiểu phải bắt đầu ở cùng một mốc (khách đối chiếu Lark 03/09/2026).
               Lúc đang tải thì mượn chỗ chữ để báo, không mọc thêm vòng quay. */}
          <button
            type="button"
            disabled={upload.isPending}
            onClick={() => fileRef.current?.click()}
            className="flex items-center rounded-md px-1 py-1 text-sm text-muted-foreground hover:text-foreground disabled:opacity-60"
          >
            {upload.isPending ? 'Đang tải lên…' : 'Thêm đính kèm'}
          </button>
        </>
      )}
    </div>
  )
}

function AttachmentRow({
  file,
  canEdit,
  removing,
  onRemove,
}: {
  file: TaskAttachment
  canEdit: boolean
  removing: boolean
  onRemove: () => void
}) {
  /*  Tải qua đường CÓ KIỂM QUYỀN, không dùng `file.url`.

      `url` là đường đọc thẳng kho lưu trữ, không đi qua lớp kiểm nào — ai cầm
      được chuỗi đó đều mở được, kể cả người đã bị gỡ khỏi dự án. Còn đặt thẳng
      `<a href="/api/attachments/…">` thì trình duyệt điều hướng cả trang nên
      không gắn được token, tới nơi ăn 401. Xem `downloadFile`.  */
  function download() {
    downloadFile(`/api/attachments/${file.id}/download`, file.filename).catch((error) =>
      //  Nuốt tại đây: lỗi mạng lúc tải một tệp không được phép thành một
      //  unhandled rejection đỏ console. Toast do tầng `@/core/api` lo.
      logger.warn('Không tải được tệp đính kèm của công việc', error),
    )
  }

  return (
    <li className="group/file flex items-center gap-2 rounded px-1 py-0.5 text-sm hover:bg-accent/60">
      <FileText className="size-3.5 shrink-0 text-muted-foreground" />
      <span className="min-w-0 flex-1 truncate" title={file.filename}>
        {file.filename}
      </span>
      <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
        {formatFileSize(file.size)}
      </span>

      <IconTooltip label="Tải về">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={`Tải về: ${file.filename}`}
          onClick={download}
        >
          <Download className="size-3.5" />
        </Button>
      </IconTooltip>

      {canEdit && (
        <IconTooltip label="Gỡ tệp">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={`Gỡ tệp: ${file.filename}`}
            disabled={removing}
            onClick={onRemove}
          >
            {removing ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <X className="size-3.5 text-destructive" />
            )}
          </Button>
        </IconTooltip>
      )}
    </li>
  )
}
