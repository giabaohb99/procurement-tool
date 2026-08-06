import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { toast } from 'sonner'

import EmbedCodeDialog, { type EmbedDraft } from '@/components/embed-code-dialog'
import HelpEditorExtras from '@/components/help-editor-extras'
import { uploadHelpImage } from '@/components/help-article-slides'
import { Textarea } from '@/components/ui/textarea'
import { registerHtmlEmbed } from '@/lib/quill-html-embed'
import {
  attachTableColumnResize, attachTableWidthMatcher,
} from '@/lib/quill-table-column-resize'
import { applyQuillVietnameseLabels } from '@/lib/quill-vietnamese-labels'
import {
  hasTableSupport, insertTable, registerTableModule, runTableAction,
  TABLE_KEYBOARD_BINDINGS, TABLE_MODULE_OPTIONS, type TableCommand,
} from '@/lib/quill-table-actions'

// Trình soạn thảo dùng chung cho bài viết (/admin/:id) và câu trả lời FAQ (/admin/faq/:id):
// Quill + 3 nút riêng (Bảng · Nhúng mã · Mã HTML). Trước đây mỗi trang tự dựng Quill nên
// thêm tính năng phải sửa hai chỗ.
//
// Ba nút riêng được PORTAL thẳng vào thanh công cụ do Quill dựng, để tất cả nằm trên MỘT hàng.
// Không tự dựng lại toàn bộ thanh công cụ (Quill hỗ trợ truyền container tự viết) vì như vậy
// phải chép lại toàn bộ markup picker của Quill và dễ lệch khi nâng cấp.

registerHtmlEmbed()
registerTableModule()

/** Thanh công cụ đầy đủ (bài viết) và rút gọn (câu hỏi thường gặp). */
const FULL_TOOLBAR = [
  [{ header: [1, 2, 3, 4, 5, 6, false] }],
  ['bold', 'italic', 'underline', 'strike'],
  [{ color: [] }, { background: [] }],
  [{ list: 'ordered' }, { list: 'bullet' }],
  [{ align: [] }],
  ['link', 'image', 'video'],
  ['clean'],
]

const COMPACT_TOOLBAR = [
  [{ header: [2, 3, false] }],
  ['bold', 'italic', 'underline'],
  [{ list: 'ordered' }, { list: 'bullet' }],
  ['link'],
  ['clean'],
]

export interface HelpRichEditorProps {
  value: string
  /** `fromUser` = false khi Quill tự chuẩn hóa HTML lúc nạp bài (không tính là đã sửa). */
  onChange: (html: string, fromUser: boolean) => void
  /** Thanh công cụ rút gọn, không có ảnh/video — dùng cho câu hỏi thường gặp. */
  compact?: boolean
}

export default function HelpRichEditor({ value, onChange, compact = false }: HelpRichEditorProps) {
  const quillRef = useRef<ReactQuill>(null)
  const [htmlMode, setHtmlMode] = useState(false)
  const [embedOpen, setEmbedOpen] = useState(false)
  const [tableEnabled, setTableEnabled] = useState(false)
  const [extrasHost, setExtrasHost] = useState<HTMLElement | null>(null)

  const editor = () => quillRef.current?.getEditor()

  // Ở chế độ mã HTML, Quill vẫn được GIỮ NGUYÊN trong DOM (chỉ ẩn khung soạn) và nhận một giá trị
  // đông cứng. Nếu đẩy từng ký tự đang gõ vào Quill, nó sẽ chuẩn hóa lại và nuốt mất thẻ lạ ngay
  // trong lúc gõ. Rời chế độ này, giá trị mới mới được đẩy vào để Quill dựng lại.
  const frozen = useRef(value)
  if (!htmlMode) frozen.current = value
  const quillValue = htmlMode ? frozen.current : value

  // Chèn ảnh — thay handler mặc định của Quill (mặc định nhét base64 làm phình DB)
  const imageHandler = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) return
      try {
        const url = await uploadHelpImage(file)
        const quill = editor()
        if (!quill) return
        const range = quill.getSelection(true)
        quill.insertEmbed(range.index, 'image', url)
        quill.setSelection(range.index + 1, 0)
      } catch {
        // interceptor đã toast lỗi
      }
    }
    input.click()
  }

  const modules = useMemo(() => ({
    toolbar: {
      container: compact ? COMPACT_TOOLBAR : FULL_TOOLBAR,
      handlers: { image: imageHandler },
    },
    table: TABLE_MODULE_OPTIONS,
    keyboard: { bindings: TABLE_KEYBOARD_BINDINGS },
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [compact])

  // onChange đổi tham chiếu mỗi lần render, còn effect dưới chỉ chạy một lần -> giữ qua ref
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  // Quill dựng thanh công cụ trong componentDidMount -> effect này (chạy sau) đã có DOM để bám vào.
  // Cũng là thời điểm sớm nhất gắn được matcher độ rộng cột: phải sau matcher của module bảng,
  // và vẫn kịp trước khi bài viết tải xong (lúc mount `value` còn rỗng).
  useEffect(() => {
    const quill = editor()
    const container = (quill?.getModule('toolbar') as { container?: HTMLElement } | undefined)
      ?.container
    if (!quill || !container) return

    const host = document.createElement('span')
    host.className = 'hc-editor-extras'
    container.appendChild(host)
    setExtrasHost(host)
    setTableEnabled(hasTableSupport(quill))
    applyQuillVietnameseLabels()

    attachTableWidthMatcher(quill)
    const detachResize = attachTableColumnResize(quill, () => {
      onChangeRef.current(quill.root.innerHTML, true)
    })

    return () => {
      host.remove()
      detachResize()
    }
  }, [])

  const handleInsertTable = (rows: number, columns: number) => {
    if (!insertTable(editor(), rows, columns)) {
      toast.error('Không chèn được bảng ở vị trí này')
    }
  }

  const handleTableAction = (command: TableCommand) => {
    if (!runTableAction(editor(), command)) {
      toast.error('Đặt con trỏ vào một ô trong bảng rồi thử lại')
    }
  }

  const handleInsertEmbed = ({ parsed, height }: EmbedDraft) => {
    const quill = editor()
    if (!quill) return
    quill.focus()
    const range = quill.getSelection(true)
    // Chỉ 1 iframe và không ép chiều cao -> dùng embed "video" sẵn có của Quill cho nhẹ;
    // còn lại phải bọc iframe srcdoc (blot htmlEmbed) thì script của nhà cung cấp mới chạy.
    if (parsed.kind === 'iframe' && !height) {
      quill.insertEmbed(range.index, 'video', parsed.src, 'user')
    } else {
      const code = parsed.kind === 'iframe'
        ? `<iframe src="${parsed.src}" allowfullscreen></iframe>`
        : parsed.code
      quill.insertEmbed(range.index, 'htmlEmbed', { code, height }, 'user')
    }
    quill.setSelection(range.index + 1, 0)
  }

  return (
    <div className={`hc-editor${compact ? ' hc-editor-sm' : ''}${htmlMode ? ' hc-editor--html' : ''}`}>
      <ReactQuill
        ref={quillRef}
        theme="snow"
        value={quillValue}
        onChange={(html, _delta, source) => {
          if (htmlMode) return
          onChange(html, source === 'user')
        }}
        modules={modules}
      />

      {extrasHost && createPortal(
        <HelpEditorExtras
          htmlMode={htmlMode}
          onToggleHtml={() => setHtmlMode((m) => !m)}
          tableEnabled={tableEnabled}
          onInsertTable={handleInsertTable}
          onTableAction={handleTableAction}
          onOpenEmbed={() => setEmbedOpen(true)}
        />,
        extrasHost,
      )}

      {htmlMode && (
        <div className="space-y-2">
          <Textarea
            autoFocus
            value={value}
            onChange={(e) => onChange(e.target.value, true)}
            spellCheck={false}
            className="hc-editor-html h-[26rem] rounded-t-none font-mono text-xs leading-relaxed"
          />
          <p className="text-xs text-muted-foreground">
            Lưu ngay ở chế độ này thì HTML được giữ nguyên. Bấm <b>Soạn trực quan</b> thì Quill
            chuẩn hóa lại và <b>bỏ những thẻ nó không hiểu</b> — muốn nhúng mã phức tạp hãy dùng
            nút <b>Nhúng mã</b>.
          </p>
        </div>
      )}

      <EmbedCodeDialog open={embedOpen} onOpenChange={setEmbedOpen} onInsert={handleInsertEmbed} />
    </div>
  )
}
