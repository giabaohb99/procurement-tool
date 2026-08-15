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
  structural_nodes: number
}

interface DocumentImportButtonProps {
  /** Trả false nếu editor chưa sẵn sàng để nhận nội dung. */
  onInsert: (html: string) => Promise<boolean>
}

type ImportPhase = 'idle' | 'uploading' | 'inserting'

/** Đợi React commit nhãn tiến trình và trình duyệt vẽ nó lên màn hình. */
function afterPaint() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
  })
}

/** Hành động đầu trang: tải tài liệu, chuyển đổi rồi chèn tại vị trí con trỏ. */
export function DocumentImportButton({ onInsert }: DocumentImportButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [phase, setPhase] = useState<ImportPhase>('idle')
  const loading = phase !== 'idle'

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
    let converted = false
    setPhase('uploading')
    try {
      const imported = await apiPost<ImportedDocument>('/api/documents/import/parse', form)
      converted = true
      if (!imported.content_html.trim()) {
        toast.error('Không tìm thấy nội dung có thể chèn trong tệp')
        return
      }
      setPhase('inserting')
      await afterPaint()
      if (!(await onInsert(imported.content_html))) {
        toast.error('Trình soạn thảo chưa sẵn sàng, vui lòng thử lại')
        return
      }
      toast.success(`Đã chèn nội dung từ ${imported.filename}`)
    } catch {
      // Lỗi API đã được interceptor hiển thị. Lỗi sau khi API chuyển đổi xong
      // là lỗi phía editor, cần báo riêng thay vì nuốt im lặng.
      if (converted) toast.error('Không thể chèn nội dung vào trình soạn thảo')
    } finally {
      setPhase('idle')
    }
  }

  return (
    <>
      <Button
        type="button"
        variant="outline"
        title="Nhận Word (.doc, .docx), Markdown và HTML"
        aria-busy={loading}
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? <Loader2 className="size-4 animate-spin" /> : <FileUp className="size-4" />}
        {phase === 'uploading' ? 'Đang tải…' : phase === 'inserting' ? 'Đang chèn…' : 'Nhập tệp'}
      </Button>
      <input
        ref={inputRef}
        hidden
        type="file"
        accept={ACCEPT}
        disabled={loading}
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
