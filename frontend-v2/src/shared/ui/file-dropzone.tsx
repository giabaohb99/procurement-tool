import { Loader2, UploadCloud } from 'lucide-react'
import { useRef, useState, type ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface FileDropzoneProps {
  /** Nhận danh sách tệp người dùng thả vào hoặc chọn từ hộp thoại. */
  onFiles: (files: File[]) => void
  /** Dòng chữ chính giữa vùng thả. */
  hint?: string
  /**
   * Khối phụ nằm dưới dòng gợi ý (ví dụ ô chọn mục lưu tệp).
   *
   * Bọc sẵn trong một lớp `data-dropzone-ignore` nên bấm vào đây KHÔNG bật hộp
   * chọn tệp — không thì mở ô chọn mục cái là hộp chọn tệp nhảy ra đè lên.
   */
  children?: ReactNode
  disabled?: boolean
  /** Đang tải lên — khóa vùng thả và hiện vòng quay. */
  busy?: boolean
  /** Lọc loại tệp cho hộp chọn (thuộc tính `accept` của input), vd ".xlsx,.csv". */
  accept?: string
  className?: string
}

/**
 * Vùng kéo-thả tệp.
 *
 * Cả vùng là MỘT phần tử bấm được (`role="button"`) chứ không lồng thêm nút bên
 * trong: lồng nút vào vùng bấm được thì một cú bấm chạy hai lần, và ô chọn đặt
 * trong đó cũng thành nút lồng nút — HTML không hợp lệ, trình đọc màn hình đọc
 * sai.
 */
export function FileDropzone({
  onFiles,
  hint = 'Kéo thả tệp vào đây hoặc bấm để chọn tệp',
  children,
  disabled = false,
  busy = false,
  accept,
  className,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const locked = disabled || busy

  function emit(list: FileList | null) {
    const files = Array.from(list ?? [])
    if (files.length) onFiles(files)
    // Chọn lại đúng tệp vừa xóa thì `change` không bắn nếu không dọn giá trị cũ.
    if (inputRef.current) inputRef.current.value = ''
  }

  function openPicker() {
    if (!locked) inputRef.current?.click()
  }

  return (
    <div
      role="button"
      tabIndex={locked ? -1 : 0}
      aria-disabled={locked}
      aria-label={hint}
      className={cn(
        'flex flex-col items-center gap-2 rounded-lg border border-dashed bg-muted/20 px-4 py-5 text-center transition-colors',
        !locked && 'cursor-pointer hover:border-primary/60 hover:bg-primary/5',
        dragging && 'border-primary bg-primary/10',
        locked && 'cursor-default opacity-70',
        className,
      )}
      onClick={(event) => {
        if ((event.target as HTMLElement).closest('[data-dropzone-ignore]')) return
        openPicker()
      }}
      onKeyDown={(event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return
        event.preventDefault()
        openPicker()
      }}
      onDragOver={(event) => {
        if (locked) return
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        if (locked) return
        event.preventDefault()
        setDragging(false)
        emit(event.dataTransfer.files)
      }}
    >
      <input
        ref={inputRef}
        className="hidden"
        type="file"
        multiple
        accept={accept}
        disabled={locked}
        onChange={(event) => emit(event.target.files)}
      />

      {busy ? (
        <Loader2 className="size-6 animate-spin text-primary" />
      ) : (
        <UploadCloud className="size-6 text-primary" />
      )}
      <p className="text-sm text-muted-foreground">{busy ? 'Đang tải tệp lên…' : hint}</p>

      {children && (
        <div
          data-dropzone-ignore
          className="flex flex-wrap items-center justify-center gap-2"
          // Bấm vào ô chọn thì dừng ở đây, không nổi bọt lên vùng thả.
          onClick={(event) => event.stopPropagation()}
          onKeyDown={(event) => event.stopPropagation()}
        >
          {children}
        </div>
      )}
    </div>
  )
}
