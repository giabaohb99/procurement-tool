import { useState } from 'react'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { AttachmentPreviewDialog } from '@/shared/attachments/attachment-preview-dialog'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { workHistoryFileDownloadUrl } from '../api/employee-work-history-api'
import {
  useConcurrentFiles,
  useDeleteConcurrentFile,
  useUploadConcurrentFiles,
} from '../hooks/use-employee-concurrent-files'
import type { WorkHistoryFile } from '../types/employee-work-history'
import {
  WORK_HISTORY_FILE_ACCEPT,
  WORK_HISTORY_FILE_MAX_SIZE_MB,
} from './employee-work-history-files-dialog'
import { EmployeeWorkHistoryFilesDialogList } from './employee-work-history-files-dialog-list'

interface EmployeeConcurrentFilesDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  concurrentId: number
  /** Hồ sơ CHỦ của dòng — để dọn cache bảng ngoài (cột Tệp đọc `file_count`). */
  employeeId: number
  /** `false` → chỉ xem / tải; ẩn vùng thả và nút gỡ. */
  editable: boolean
}

/**
 * Hộp TỆP QĐ của một dòng kiêm nhiệm (entity riêng tư `employee_concurrent`). Cùng chính sách tệp với quá trình công tác
 * (`FILE_POLICY`: nhóm `_DOC`, 50MB) nên dùng lại hằng số và danh sách tệp của hộp đó; xem / tải đi đường
 * `/api/attachments/{id}/view|download` có kiểm quyền.
 *
 * Hộp nằm trong `<form>` của trang hồ sơ — chặn lan `submit` ở đây như hộp tệp quá trình công tác.
 */
export function EmployeeConcurrentFilesDialog({
  open,
  onOpenChange,
  concurrentId,
  employeeId,
  editable,
}: EmployeeConcurrentFilesDialogProps) {
  const { data: files, isLoading } = useConcurrentFiles(concurrentId, open)
  const uploadMutation = useUploadConcurrentFiles(concurrentId, employeeId)
  const deleteMutation = useDeleteConcurrentFile(concurrentId, employeeId)
  const [previewing, setPreviewing] = useState<WorkHistoryFile | null>(null)

  function handleFiles(picked: File[]) {
    const limit = WORK_HISTORY_FILE_MAX_SIZE_MB * 1024 * 1024
    const tooBig = picked.filter((f) => f.size > limit)
    if (tooBig.length > 0) {
      toast.error(`Vượt quá ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`)
    }
    const ok = picked.filter((f) => f.size <= limit)
    if (ok.length > 0) uploadMutation.mutate(ok)
  }

  async function handleDownload(file: WorkHistoryFile) {
    try {
      await downloadFile(workHistoryFileDownloadUrl(file.id), file.filename)
    } catch {
      toast.error(`Không tải được tệp "${file.filename}".`)
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-lg">
          <div className="contents" onSubmit={(event) => event.stopPropagation()}>
            <DialogHeader>
              <DialogTitle>Tệp quyết định kiêm nhiệm</DialogTitle>
            </DialogHeader>

            {editable && (
              <FileDropzone
                onFiles={handleFiles}
                busy={uploadMutation.isPending}
                accept={WORK_HISTORY_FILE_ACCEPT}
                hint="Kéo tệp vào đây hoặc bấm để chọn"
                description={`Ảnh, PDF, Word, Excel · tối đa ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB mỗi tệp`}
              />
            )}

            <EmployeeWorkHistoryFilesDialogList
              files={files}
              isLoading={isLoading}
              editable={editable}
              deleting={deleteMutation.isPending}
              onPreview={setPreviewing}
              onDownload={(file) => void handleDownload(file)}
              onDelete={(fileId) => deleteMutation.mutate(fileId)}
              ownerPhrase="dòng kiêm nhiệm này"
            />
          </div>
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
