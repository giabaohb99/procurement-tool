import { FileText, Paperclip, X } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { HelpHint } from '@/shared/ui/help-hint'
import {
  WORK_HISTORY_FILE_ACCEPT,
  WORK_HISTORY_FILE_MAX_SIZE_MB,
} from './employee-work-history-files-dialog'

interface EmployeeConcurrentFileFieldProps {
  /** Đang SỬA (có dòng) thì mở hộp quản lý tệp; tạo mới (`null`) thì xếp hàng tệp, tải lên sau khi lưu. */
  editingRow: { file_count: number } | null
  /** `false` = thiếu quyền xem nhạy cảm: không có điều khiển nào gọi tới cửa đính kèm, chỉ báo số tệp. */
  canOpenFiles: boolean
  queuedFiles: readonly File[]
  onQueueFiles: (files: File[]) => void
  onRemoveQueued: (index: number) => void
  onOpenFilesDialog: () => void
}

/**
 * Ô **Tệp QĐ** GỌN MỘT DÒNG của hộp kiêm nhiệm (người chủ chốt 13/11/2026): nhãn + nút *Chọn tệp*, giới hạn dung lượng
 * nằm trong (i); tệp đã chọn hiện thành dòng nhỏ bỏ được, kèm chữ nhỏ "tải lên sau khi lưu" — thay vùng kéo-thả cao
 * ~120px dùng chung với hộp quá trình công tác (giữ nguyên ở đó).
 * Cùng luật quyền với `EmployeeWorkHistoryFileField`.
 */
export function EmployeeConcurrentFileField({
  editingRow,
  canOpenFiles,
  queuedFiles,
  onQueueFiles,
  onRemoveQueued,
  onOpenFilesDialog,
}: EmployeeConcurrentFileFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  if (!canOpenFiles) {
    if (!editingRow || editingRow.file_count === 0) return null
    return (
      <p className="text-sm text-muted-foreground sm:col-span-2">
        Có {editingRow.file_count} tệp QĐ — cần quyền xem thông tin nhạy cảm để quản lý.
      </p>
    )
  }

  if (editingRow) {
    return (
      <div className="flex flex-wrap items-center gap-2 sm:col-span-2">
        <span className="text-sm font-medium">Tệp QĐ</span>
        <Button type="button" variant="outline" size="sm" onClick={onOpenFilesDialog}>
          <Paperclip className="size-4" />
          Quản lý tệp ({editingRow.file_count})
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1.5 sm:col-span-2">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="text-sm font-medium">Tệp QĐ</span>
        <Button type="button" variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
          <Paperclip className="size-4" />
          Chọn tệp
        </Button>
        <HelpHint label="Giới hạn tệp QĐ">
          {`Tối đa ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB mỗi tệp. Tệp được tải lên sau khi lưu dòng kiêm nhiệm.`}
        </HelpHint>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          accept={WORK_HISTORY_FILE_ACCEPT}
          aria-label="Chọn tệp QĐ"
          onChange={(event) => {
            const picked = Array.from(event.target.files ?? [])
            //  Xóa giá trị để chọn lại đúng tệp vừa bỏ vẫn kích hoạt `change`.
            event.target.value = ''
            if (picked.length > 0) onQueueFiles(picked)
          }}
        />
      </div>
      {queuedFiles.length > 0 && (
        <ul className="space-y-1" aria-label="Tệp QĐ đã chọn">
          {queuedFiles.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center gap-2 rounded-md border px-2 py-1 text-xs"
            >
              <FileText className="size-3.5 shrink-0 text-muted-foreground" />
              <span className="min-w-0 flex-1 truncate" title={file.name}>
                {file.name}
              </span>
              <button
                type="button"
                aria-label={`Bỏ tệp ${file.name}`}
                className="shrink-0 rounded-sm text-muted-foreground hover:text-foreground"
                onClick={() => onRemoveQueued(index)}
              >
                <X className="size-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
      {queuedFiles.length > 0 && <p className="text-xs text-muted-foreground">Tải lên sau khi lưu</p>}
    </div>
  )
}
