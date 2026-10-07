import { FileText, TriangleAlert, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { formatFileSize } from '@/shared/utils/format-file-size'

interface FilePickerProps {
  file: File | null
  /** Lỗi kiểm tại chỗ (đuôi, dung lượng). */
  fileError: string | null
  /** Câu lỗi backend trả về sau khi gửi. */
  serverError: string | null
  /** Biến lạ backend liệt kê trong lỗi 422. */
  unknown: string[]
  busy: boolean
  onFiles: (files: File[]) => void
  onClear: () => void
}

/**
 * Vùng chọn tệp .docx của hộp tải mẫu, kèm chỗ hiện lỗi.
 *
 * Biến lạ liệt kê NGAY trong hộp (không chỉ toast): toast biến mất sau vài giây,
 * còn người soạn mẫu cần danh sách đó mở sẵn để vừa đọc vừa sửa trong Word.
 */
export function LaborContractTemplateFilePicker({
  file,
  fileError,
  serverError,
  unknown,
  busy,
  onFiles,
  onClear,
}: FilePickerProps) {
  return (
    <div className="space-y-2">
      <FileDropzone
        accept=".docx"
        onFiles={onFiles}
        busy={busy}
        hint="Kéo thả tệp .docx vào đây hoặc bấm để chọn"
        description="Chỉ nhận .docx, tối đa 10 MB"
      />
      {file && (
        <p className="flex items-center gap-2 text-sm">
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="truncate">{file.name}</span>
          <span className="text-muted-foreground">({formatFileSize(file.size)})</span>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="ml-auto size-6"
            aria-label="Bỏ tệp đã chọn"
            onClick={onClear}
          >
            <X className="size-3.5" />
          </Button>
        </p>
      )}
      {fileError && (
        <p role="alert" className="text-sm text-destructive">
          {fileError}
        </p>
      )}
      {serverError && (
        <div
          role="alert"
          className="space-y-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm"
        >
          <p className="flex items-start gap-2 font-medium text-destructive">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            {serverError}
          </p>
          {unknown.length > 0 && (
            <>
              <ul aria-label="Biến lạ trong mẫu" className="flex flex-wrap gap-1.5">
                {unknown.map((key) => (
                  <li key={key} className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                    {`{{ ${key} }}`}
                  </li>
                ))}
              </ul>
              <p className="text-muted-foreground">
                Mẹo: Word hay tách biến thành nhiều đoạn khi bạn định dạng giữa chừng. Hãy xóa rồi
                gõ lại biến liền một lần, không đổi chữ đậm/nghiêng/màu ở giữa, rồi tải lại.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
