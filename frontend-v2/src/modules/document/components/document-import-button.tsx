import { FileSearch, FileUp, Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { apiPost } from '@/core/api/api-request'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import type { DocumentImportMode } from '@/shared/ui/rich-text-editor'
import { DocumentImportTraceDialog, type DocumentImportTrace } from './document-import-trace-dialog'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ACCEPTED_EXTENSIONS = new Set(['doc', 'docx', 'pdf', 'md', 'markdown', 'html', 'htm'])
const ACCEPT = [
  '.doc',
  '.docx',
  '.pdf',
  '.md',
  '.markdown',
  '.html',
  '.htm',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/pdf',
  'text/markdown',
  'text/html',
].join(',')

interface ImportedDocument {
  filename: string
  content_html: string
  structural_nodes: number
  import_trace?: DocumentImportTrace
}

interface DocumentImportButtonProps {
  /** Chỉ hỏi chế độ nhập khi editor đã có nội dung thật. */
  hasContent: () => boolean
  /** Trả false nếu editor chưa sẵn sàng để nhận nội dung. */
  onInsert: (html: string, mode: DocumentImportMode) => Promise<boolean>
  /** Nhảy editor tới mốc nguồn khi người dùng bấm một trang trong báo cáo PDF. */
  onNavigateToTrace?: (importId: string, page: number) => boolean
}

type ImportPhase = 'idle' | 'uploading' | 'inserting'

/** Đợi React commit nhãn tiến trình và trình duyệt vẽ nó lên màn hình. */
function afterPaint() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
  })
}

/** Hành động đầu trang: tải tài liệu rồi chèn tại con trỏ hoặc ghi đè toàn bộ. */
export function DocumentImportButton({
  hasContent,
  onInsert,
  onNavigateToTrace,
}: DocumentImportButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [phase, setPhase] = useState<ImportPhase>('idle')
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [mode, setMode] = useState<DocumentImportMode>('insert')
  const [trace, setTrace] = useState<DocumentImportTrace | null>(null)
  const [traceOpen, setTraceOpen] = useState(false)
  const loading = phase !== 'idle'

  function validateFile(file: File) {
    const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
    if (!ACCEPTED_EXTENSIONS.has(extension)) {
      toast.error('Chỉ nhận tệp Word, PDF, Markdown hoặc HTML')
      return false
    }
    if (file.size > MAX_FILE_SIZE) {
      toast.error('Tệp vượt quá 10MB')
      return false
    }
    return true
  }

  function chooseFile(file: File) {
    if (!validateFile(file)) return
    if (hasContent()) {
      // Chèn là mặc định an toàn: mở hộp thoại không bao giờ tự đặt người dùng
      // vào lựa chọn làm mất toàn bộ phần họ đã soạn.
      setMode('insert')
      setPendingFile(file)
      return
    }
    void importFile(file, 'replace')
  }

  async function importFile(file: File, importMode: DocumentImportMode) {
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
      if (!(await onInsert(imported.content_html, importMode))) {
        toast.error('Trình soạn thảo chưa sẵn sàng, vui lòng thử lại')
        return
      }
      setTrace(imported.import_trace ?? null)
      setTraceOpen(Boolean(imported.import_trace))
      toast.success(
        importMode === 'replace'
          ? `Đã thay toàn bộ nội dung bằng ${imported.filename}`
          : `Đã chèn ${imported.filename} tại vị trí con trỏ`,
      )
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
      {trace && (
        <Button
          type="button"
          variant="ghost"
          title="Xem lại các điểm cần đối chiếu với PDF"
          onClick={() => setTraceOpen(true)}
        >
          <FileSearch className="size-4" />
          Báo cáo PDF
        </Button>
      )}
      <Button
        type="button"
        variant="outline"
        title="Nhận Word (.doc, .docx), PDF, Markdown và HTML"
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
          if (file) chooseFile(file)
          // Cho phép chọn lại chính tệp vừa nhập.
          event.target.value = ''
        }}
      />
      <Dialog
        open={Boolean(pendingFile)}
        onOpenChange={(open) => {
          if (!open && !loading) setPendingFile(null)
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Nhập nội dung tệp theo cách nào?</DialogTitle>
            <DialogDescription>
              Văn bản đang có nội dung. Chọn cách áp dụng tệp{' '}
              <span className="font-medium text-foreground">{pendingFile?.name}</span>.
            </DialogDescription>
          </DialogHeader>

          <RadioGroup
            value={mode}
            onValueChange={(value) => setMode(value as DocumentImportMode)}
            className="gap-3"
          >
            <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-4 text-sm has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5">
              <RadioGroupItem value="insert" className="mt-0.5" />
              <span>
                <span className="font-medium">Chèn tại vị trí con trỏ</span>
                <span className="mt-1 block text-muted-foreground">
                  Giữ nguyên phần đã soạn và gắn nội dung tệp vào đúng chỗ con trỏ đang đặt.
                </span>
              </span>
            </label>
            <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-4 text-sm has-[[data-state=checked]]:border-destructive has-[[data-state=checked]]:bg-destructive/5">
              <RadioGroupItem value="replace" className="mt-0.5" />
              <span>
                <span className="font-medium">Ghi đè toàn bộ</span>
                <span className="mt-1 block text-muted-foreground">
                  Xóa nội dung đang có trong trình soạn thảo và thay bằng toàn bộ nội dung tệp.
                </span>
              </span>
            </label>
          </RadioGroup>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setPendingFile(null)}>
              Hủy
            </Button>
            <Button
              type="button"
              variant={mode === 'replace' ? 'destructive' : 'default'}
              onClick={() => {
                if (!pendingFile) return
                const file = pendingFile
                setPendingFile(null)
                void importFile(file, mode)
              }}
            >
              {mode === 'replace' ? 'Ghi đè toàn bộ' : 'Chèn tại con trỏ'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <DocumentImportTraceDialog
        trace={trace}
        open={traceOpen}
        onOpenChange={setTraceOpen}
        onNavigate={onNavigateToTrace}
      />
    </>
  )
}
