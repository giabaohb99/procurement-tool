import { Download, Eye, FileImage, FileText, File as FileIcon, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatFileSize } from '@/shared/utils/format-file-size'
import type { WorkHistoryFile } from '../types/employee-work-history'

function fileIcon(file: WorkHistoryFile) {
  const type = (file.content_type || '').toLowerCase()
  if (type.startsWith('image/')) return FileImage
  if (type.includes('pdf')) return FileText
  return FileIcon
}

interface EmployeeWorkHistoryFilesDialogListProps {
  files: WorkHistoryFile[] | undefined
  isLoading: boolean
  /** Sửa được hay chỉ xem — xem docstring đầy đủ ở `employee-work-history-files-dialog.tsx`. */
  editable: boolean
  deleting: boolean
  onPreview: (file: WorkHistoryFile) => void
  onDownload: (file: WorkHistoryFile) => void
  onDelete: (fileId: number) => void
}

/**
 * Danh sách tệp (hoặc chữ thay thế lúc đang tải/rỗng) của hộp «Tệp quyết
 * định» — tách khỏi `employee-work-history-files-dialog.tsx` để tệp đó giữ
 * dưới ~200 dòng (CLAUDE.md §"File Size Management"). Thuần trình bày, không
 * tự gọi mutation nào — nhận sẵn hàm xử lý từ nơi gọi.
 */
export function EmployeeWorkHistoryFilesDialogList({
  files,
  isLoading,
  editable,
  deleting,
  onPreview,
  onDownload,
  onDelete,
}: EmployeeWorkHistoryFilesDialogListProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-12 w-full" />
      </div>
    )
  }

  if (!files || files.length === 0) {
    return (
      <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
        {editable ? 'Chưa có tệp nào. Kéo tệp vào vùng trên để tải lên.' : 'Dòng này không kèm tệp nào.'}
      </p>
    )
  }

  return (
    <ul className="space-y-2">
      {files.map((file) => {
        const Icon = fileIcon(file)
        return (
          <li key={file.id} className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2">
            <Icon className="size-5 shrink-0 text-muted-foreground" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={file.filename}>
                {file.filename}
              </p>
              <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
            </div>

            <div className="flex shrink-0 items-center gap-1">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-8"
                title="Xem trước"
                aria-label={`Xem trước ${file.filename}`}
                onClick={() => onPreview(file)}
              >
                <Eye className="size-4" />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-8"
                title="Tải về"
                aria-label={`Tải về ${file.filename}`}
                onClick={() => onDownload(file)}
              >
                <Download className="size-4" />
              </Button>
              {editable && (
                <ConfirmIconButton
                  icon={Trash2}
                  title="Gỡ tệp"
                  confirmTitle="Gỡ tệp đính kèm?"
                  confirmDescription={`Gỡ «${file.filename}» khỏi dòng quá trình công tác này?`}
                  destructive
                  disabled={deleting}
                  onConfirm={() => onDelete(file.id)}
                />
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
