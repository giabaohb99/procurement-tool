import { Paperclip } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { FormLabel } from '@/shared/ui/form'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import {
  WORK_HISTORY_FILE_ACCEPT,
  WORK_HISTORY_FILE_MAX_SIZE_MB,
} from './employee-work-history-files-dialog'

interface EmployeeWorkHistoryFileFieldProps {
  /** Đang SỬA (`true`) hay tạo mới (`false`) — quyết định ô Tệp QĐ hiện dạng nào. */
  editingRow: EmployeeWorkHistory | null
  /** A9 (Q4) — `false` thì ẨN cả vùng thả tệp lẫn nút «Quản lý tệp» (M4). */
  canOpenFiles: boolean
  queuedFileCount: number
  onQueueFiles: (files: File[]) => void
  onOpenFilesDialog: () => void
}

/**
 * Ô «Tệp QĐ» của hộp thêm/sửa «Quá trình công tác» — tách khỏi
 * `employee-work-history-form-dialog-fields.tsx` để tệp đó giữ dưới ~200 dòng
 * (CLAUDE.md §"File Size Management").
 *
 * M4 (Q4) — `can_open_files=false` thì ẨN cả vùng thả tệp lẫn nút «Quản lý
 * tệp»: không hiện điều khiển gọi tới cửa đính kèm khi người sửa không có
 * quyền xem tệp (vd thiếu `employee_sensitive.read` khi sửa hồ sơ NGƯỜI
 * KHÁC). Dòng có tệp sẵn vẫn báo SỐ LƯỢNG (không nội dung), cùng quy ước với
 * cột «Tệp» của bảng.
 */
export function EmployeeWorkHistoryFileField({
  editingRow,
  canOpenFiles,
  queuedFileCount,
  onQueueFiles,
  onOpenFilesDialog,
}: EmployeeWorkHistoryFileFieldProps) {
  if (!canOpenFiles) {
    //  Không có gì để báo (TẠO MỚI, hoặc SỬA dòng chưa có tệp nào) → bỏ hẳn
    //  cả nhãn, đừng để một chữ «Tệp QĐ» trống hoác không có nội dung dưới nó.
    if (!editingRow || editingRow.file_count === 0) return null
    return (
      <div>
        <FormLabel>Tệp QĐ</FormLabel>
        <p className="mt-2 text-sm text-muted-foreground">
          Có {editingRow.file_count} tệp đính kèm — cần quyền xem thông tin nhạy cảm để quản lý.
        </p>
      </div>
    )
  }

  return (
    <div>
      <FormLabel>Tệp QĐ</FormLabel>
      {editingRow ? (
        <div className="mt-2">
          <Button type="button" variant="outline" size="sm" onClick={onOpenFilesDialog}>
            <Paperclip className="size-4" />
            Quản lý tệp ({editingRow.file_count})
          </Button>
        </div>
      ) : (
        <div className="mt-2">
          <FileDropzone
            onFiles={onQueueFiles}
            accept={WORK_HISTORY_FILE_ACCEPT}
            hint="Kéo tệp QĐ vào đây hoặc bấm để chọn"
            description={
              queuedFileCount > 0
                ? `Đã chọn ${queuedFileCount} tệp — tải lên SAU khi tạo xong dòng này.`
                : `Tối đa ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB mỗi tệp · tải lên SAU khi tạo xong dòng này.`
            }
          />
        </div>
      )}
    </div>
  )
}
