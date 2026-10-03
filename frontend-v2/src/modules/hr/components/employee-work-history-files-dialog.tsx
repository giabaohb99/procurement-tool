import { Download, Eye, FileImage, FileText, File as FileIcon, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { AttachmentPreviewDialog } from '@/shared/attachments/attachment-preview-dialog'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { workHistoryFileDownloadUrl } from '../api/employee-work-history-api'
import {
  useDeleteWorkHistoryFile,
  useUploadWorkHistoryFiles,
  useWorkHistoryFiles,
} from '../hooks/use-employee-work-history-files'
import type { WorkHistoryFile } from '../types/employee-work-history'

/**
 * Trần dung lượng MỘT tệp — khai ở `FILE_POLICY["employee_work_history"]` của
 * backend. Xuất ra để hộp thêm/sửa (hàng đợi tệp lúc TẠO MỚI) dùng chung, đừng
 * gõ lại — hai nơi lệch nhau là chọn tệp "được" ở nơi này nhưng ăn 413 ở nơi
 * tải thật.
 */
export const WORK_HISTORY_FILE_MAX_SIZE_MB = 50
/** Khớp tập đuôi `_DOC` của `FILE_POLICY` (`backend/app/core/file_registry.py`). */
export const WORK_HISTORY_FILE_ACCEPT =
  '.jpg,.jpeg,.png,.webp,.pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.xml,.msg,.eml,.cdr'

const MAX_SIZE_MB = WORK_HISTORY_FILE_MAX_SIZE_MB
const ACCEPT = WORK_HISTORY_FILE_ACCEPT

function fileIcon(file: WorkHistoryFile) {
  const type = (file.content_type || '').toLowerCase()
  if (type.startsWith('image/')) return FileImage
  if (type.includes('pdf')) return FileText
  return FileIcon
}

interface EmployeeWorkHistoryFilesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  historyId: number
  /**
   * Id hồ sơ CHỦ của dòng lịch sử — để sau khi tải/gỡ tệp dọn đúng cache của
   * bảng ngoài (`employeeWorkHistory(employeeId)`, và `myWorkHistory()` khi
   * đó là hồ sơ của chính người đang đăng nhập). Xem
   * `use-employee-work-history-files.ts::invalidateWorkHistoryLists`.
   */
  employeeId: number
  /**
   * Sửa được hay chỉ xem (Q4 + phase 05).
   *
   * `false` → ẨN vùng thả và nút gỡ tệp; nút xem/tải VẪN hiện — nơi gọi chỉ mở
   * hộp này khi đã biết `can_open_files=true` cho dòng đó, nên ai mở được hộp
   * thì luôn được xem/tải, bất kể có sửa được hay không.
   */
  editable: boolean
}

/**
 * Hộp TỆP QĐ của một dòng quá trình công tác (A6 — entity riêng tư, đi qua cửa
 * đính kèm dùng chung với `entity=employee_work_history`).
 *
 * Dùng LẠI ở hai nơi: cột «Tệp» của tab hồ sơ (`editable` theo `can_edit`) và
 * thẻ ở Trang cá nhân `/me` (luôn `editable=false` — chỉ xem tệp của chính mình).
 *
 * Khuôn giống `leave-attachments-card.tsx`, chỉ khác là một `Dialog` thay vì
 * một `Card` thường trực — hộp tệp của một dòng lịch sử chỉ cần mở khi bấm vào,
 * không cần nằm sẵn trên trang.
 */
export function EmployeeWorkHistoryFilesDialog({
  open,
  onOpenChange,
  historyId,
  employeeId,
  editable,
}: EmployeeWorkHistoryFilesDialogProps) {
  const { data: files, isLoading } = useWorkHistoryFiles(historyId, open)
  const uploadMutation = useUploadWorkHistoryFiles(historyId, employeeId)
  const deleteMutation = useDeleteWorkHistoryFile(historyId, employeeId)
  const [previewing, setPreviewing] = useState<WorkHistoryFile | null>(null)

  function handleFiles(picked: File[]) {
    const limit = MAX_SIZE_MB * 1024 * 1024
    const tooBig = picked.filter((f) => f.size > limit)
    if (tooBig.length > 0) {
      toast.error(`Vượt quá ${MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`)
    }
    const ok = picked.filter((f) => f.size <= limit)
    if (ok.length > 0) uploadMutation.mutate(ok)
  }

  async function handleDownload(file: WorkHistoryFile) {
    try {
      await downloadFile(workHistoryFileDownloadUrl(file.id), file.filename)
    } catch {
      toast.error(`Không tải được tệp «${file.filename}».`)
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Tệp quyết định</DialogTitle>
          </DialogHeader>

          {editable && (
            <FileDropzone
              onFiles={handleFiles}
              busy={uploadMutation.isPending}
              accept={ACCEPT}
              hint="Kéo tệp vào đây hoặc bấm để chọn"
              description={`Ảnh, PDF, Word, Excel · tối đa ${MAX_SIZE_MB}MB mỗi tệp`}
            />
          )}

          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
            </div>
          ) : !files || files.length === 0 ? (
            <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
              {editable ? 'Chưa có tệp nào. Kéo tệp vào vùng trên để tải lên.' : 'Dòng này không kèm tệp nào.'}
            </p>
          ) : (
            <ul className="space-y-2">
              {files.map((file) => {
                const Icon = fileIcon(file)
                return (
                  <li
                    key={file.id}
                    className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2"
                  >
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
                        onClick={() => setPreviewing(file)}
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
                        onClick={() => void handleDownload(file)}
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
                          disabled={deleteMutation.isPending}
                          onConfirm={() => deleteMutation.mutate(file.id)}
                        />
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </DialogContent>
      </Dialog>

      <AttachmentPreviewDialog
        file={previewing}
        open={Boolean(previewing)}
        onOpenChange={(next) => !next && setPreviewing(null)}
      />
    </>
  )
}
