import { FileText, Paperclip, X } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { formatDateTime } from '@/shared/utils/format-date'
import type { DocumentAttachment } from '../types/document-record'

interface DocumentAttachmentListProps {
  attachments: DocumentAttachment[]
  onChange: (attachments: DocumentAttachment[]) => void
}

/**
 * Tệp đính kèm của văn bản.
 *
 * ⚠️ CHƯA CÓ BACKEND nên chỉ ghi lại TÊN và DUNG LƯỢNG file, không giữ nội dung
 * — bấm vào không tải về được. Khi có endpoint upload thì thay phần chọn file
 * bằng lời gọi API và thêm link tải; phần hiển thị giữ nguyên.
 */
export function DocumentAttachmentList({
  attachments,
  onChange,
}: DocumentAttachmentListProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFiles(files: FileList | null) {
    if (!files?.length) return
    const added: DocumentAttachment[] = Array.from(files).map((file, index) => ({
      // Tên + thời điểm là đủ phân biệt; `crypto.randomUUID` không có trên
      // trình duyệt chạy qua HTTP thường ở mạng nội bộ.
      id: `${Date.now()}-${index}-${file.name}`,
      name: file.name,
      size: file.size,
      at: new Date().toISOString(),
    }))
    onChange([...attachments, ...added])
    // Xóa giá trị input để chọn LẠI ĐÚNG file vừa gỡ vẫn kích hoạt `onChange`.
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <FormCard
      title="Tệp đính kèm"
      actions={
        <>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => inputRef.current?.click()}
          >
            <Paperclip className="size-4" />
            Chọn tệp
          </Button>
          <input
            ref={inputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(event) => handleFiles(event.target.files)}
          />
        </>
      }
    >
      {attachments.length === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa có tệp nào.</p>
      ) : (
        <ul className="divide-y">
          {attachments.map((file) => (
            <li key={file.id} className="flex items-center gap-3 py-2 first:pt-0">
              <FileText className="size-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatSize(file.size)} · {formatDateTime(file.at)}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                title="Gỡ tệp"
                onClick={() => onChange(attachments.filter((item) => item.id !== file.id))}
              >
                <X className="size-4" />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </FormCard>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
