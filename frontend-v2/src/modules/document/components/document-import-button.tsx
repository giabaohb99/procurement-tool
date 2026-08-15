import { FileUp, Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { apiPost } from '@/core/api/api-request'
import { Button } from '@/shared/ui/button'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ACCEPTED_EXTENSIONS = new Set(['doc', 'docx', 'md', 'markdown', 'html', 'htm'])
const ACCEPT = [
  '.doc',
  '.docx',
  '.md',
  '.markdown',
  '.html',
  '.htm',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/markdown',
  'text/html',
].join(',')

interface ImportedDocument {
  filename: string
  content_html: string
}

interface DocumentImportButtonProps {
  /** Trả false nếu editor chưa sẵn sàng để nhận nội dung. */
  onInsert: (html: string) => boolean
}

/** Hành động đầu trang: tải tài liệu, chuyển đổi rồi chèn tại vị trí con trỏ. */
export function DocumentImportButton({ onInsert }: DocumentImportButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)

  async function importFile(file: File) {
    const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!ACCEPTED_EXTENSIONS.has(extension)) {
      toast.error('Chỉ nhận tệp Word, Markdown hoặc HTML')
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      toast.error('Tệp vượt quá 10MB')
      return
    }

    const form = new FormData()
    form.append('file', file)
    setLoading(true)
    try {
      const imported = await apiPost<ImportedDocument>('/api/documents/import/parse', form)
      if (!imported.content_html.trim()) {
        toast.error('Không tìm thấy nội dung có thể chèn trong tệp')
        return
      }
      if (!onInsert(imported.content_html)) {
        toast.error('Trình soạn thảo chưa sẵn sàng, vui lòng thử lại')
        return
      }
      toast.success(`Đã chèn nội dung từ ${imported.filename}`)
    } catch {
      // Interceptor API đã hiển thị đúng thông báo lỗi từ backend.
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Button
        type="button"
        variant="outline"
        title="Nhận Word (.doc, .docx), Markdown và HTML"
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? <Loader2 className="size-4 animate-spin" /> : <FileUp className="size-4" />}
        {loading ? 'Đang nhập…' : 'Nhập tệp'}
      </Button>
      <input
        ref={inputRef}
        hidden
        type="file"
        accept={ACCEPT}
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void importFile(file)
          // Cho phép chọn lại chính tệp vừa nhập.
          event.target.value = ''
        }}
      />
    </>
  )
}
