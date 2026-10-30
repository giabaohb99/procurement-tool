import { FileText, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { SIGNED_FILE_ACCEPT, validateSignedFile } from '../utils/labor-contract-rules'

interface LaborContractSignedFileFieldProps {
  /** Tệp đang chọn (chưa tải lên — hộp thoại tải sau khi lưu hợp đồng xong). */
  file: File | null
  onChange: (file: File | null) => void
  /** Hợp đồng đang sửa đã có bản ký → chọn tệp mới là THAY bản cũ. */
  hasExisting?: boolean
  disabled?: boolean
}

/**
 * Ô chọn bản hợp đồng đã ký / bản scan ngay trong hộp Lập / Sửa hợp đồng (duoc-CR-632).
 *
 * Trước đây chỉ tải lên được bằng nút "Tải lên bản đã ký" trên DÒNG hợp đồng sau khi lập, người dùng
 * nhìn hộp lập tưởng là không có chỗ lưu tệp. Ô này chỉ GIỮ tệp; tải lên đi đúng đường API cũ
 * (`PUT /signed-file`) sau khi lưu xong, nên luật định dạng / dung lượng / trạng thái và việc chép
 * tệp sang bản lưu trữ bên Văn bản (CR-629) giữ nguyên một chỗ.
 */
export function LaborContractSignedFileField({ file, onChange, hasExisting, disabled }: LaborContractSignedFileFieldProps) {
  const [error, setError] = useState<string | null>(null)

  function pick(files: File[]) {
    const picked = files[0]
    if (!picked) return
    const problem = validateSignedFile(picked)
    setError(problem)
    if (!problem) onChange(picked)
  }

  return (
    <div className="space-y-1.5">
      <p className="text-sm font-medium">Tệp hợp đồng (bản ký / scan)</p>
      {file ? (
        <div className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="min-w-0 flex-1 truncate" title={file.name}>{file.name}</span>
          <span className="shrink-0 text-xs text-muted-foreground">{formatFileSize(file.size)}</span>
          <Button type="button" variant="ghost" size="icon" className="size-7" disabled={disabled}
            aria-label={`Bỏ tệp ${file.name}`} onClick={() => onChange(null)}>
            <X className="size-4" />
          </Button>
        </div>
      ) : (
        <FileDropzone
          onFiles={pick}
          accept={SIGNED_FILE_ACCEPT}
          disabled={disabled}
          hint="Kéo thả bản hợp đồng vào đây hoặc bấm để chọn"
          description="PDF, JPG, PNG · tối đa 50 MB · không bắt buộc"
        />
      )}
      {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
      {hasExisting && !file && (
        <p className="text-xs text-muted-foreground">Hợp đồng đã có bản ký — chọn tệp mới sẽ thay bản cũ.</p>
      )}
    </div>
  )
}
