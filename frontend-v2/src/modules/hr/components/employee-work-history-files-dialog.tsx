import { useState } from 'react'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { AttachmentPreviewDialog } from '@/shared/attachments/attachment-preview-dialog'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { workHistoryFileDownloadUrl } from '../api/employee-work-history-api'
import {
  useDeleteWorkHistoryFile,
  useUploadWorkHistoryFiles,
  useWorkHistoryFiles,
} from '../hooks/use-employee-work-history-files'
import type { WorkHistoryFile } from '../types/employee-work-history'
import { EmployeeWorkHistoryFilesDialogList } from './employee-work-history-files-dialog-list'

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
          {/*  Hộp này đứng NGANG HÀNG (không lồng trong) `<form>` đã chặn lan của
               hộp Sửa (`employee-work-history-form-dialog.tsx`) nhưng cả hai đều
               sống trong `<form>` của trang hồ sơ — chặn lan `submit` riêng ở
               đây. `contents` giữ nguyên lưới `grid gap-4` của `DialogContent`. */}
          <div className="contents" onSubmit={(event) => event.stopPropagation()}>
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

            <EmployeeWorkHistoryFilesDialogList
              files={files}
              isLoading={isLoading}
              editable={editable}
              deleting={deleteMutation.isPending}
              onPreview={setPreviewing}
              onDownload={(file) => void handleDownload(file)}
              onDelete={(fileId) => deleteMutation.mutate(fileId)}
            />
          </div>
        </DialogContent>
      </Dialog>

      {/*  Portal riêng (Radix) — ranh giới chặn lan của chính nó. */}
      <AttachmentPreviewDialog
        file={previewing}
        open={Boolean(previewing)}
        onOpenChange={(next) => !next && setPreviewing(null)}
      />
    </>
  )
}
