import { Image } from '@tiptap/extension-image'
import { Subscript } from '@tiptap/extension-subscript'
import { Superscript } from '@tiptap/extension-superscript'
import { TableKit } from '@tiptap/extension-table'
import { TextAlign } from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { useState } from 'react'
import { PaginationPlus } from 'tiptap-pagination-plus'

import { cn } from '@/shared/utils/cn'
import { EditorOutline } from './editor-outline'
import { EditorToolbar } from './editor-toolbar'
import { ParagraphFormat } from './paragraph-format-extension'

/** Khổ A4 ở 96dpi: 210 × 297mm ≈ 794 × 1123px, lề 20mm ≈ 76px. */
const A4_WIDTH = 794
const A4_HEIGHT = 1123
const PAGE_MARGIN = 76

/** Khe giữa hai trang — chỉ là chỗ trống nhìn thấy nền xám, không thuộc trang. */
const PAGE_GAP = 28

interface RichTextEditorProps {
  /**
   * Nội dung HTML ban đầu.
   *
   * Chỉ đọc MỘT LẦN lúc dựng: nếu bám theo prop thì mỗi lần tự động lưu xong,
   * nội dung mới lại đổ ngược vào trình soạn thảo và con trỏ nhảy về đầu bài.
   * Muốn nạp lại bản ghi khác thì đặt `key` khác cho component.
   */
  defaultContent: string
  onChange: (html: string) => void
  editable?: boolean
  /** Hiện khung mục lục bên trái — xem `EditorOutline`. */
  showOutline?: boolean
  className?: string
}

/**
 * Trình soạn thảo văn bản kiểu Word: thanh công cụ trên, TRANG GIẤY TRẮNG ở
 * giữa nền xám — soạn thẳng trên hệ thống thay vì làm ở Word rồi tải tệp lên.
 *
 * Dựng trên Tiptap (ProseMirror) vì đây là thứ duy nhất trong hệ sinh thái
 * React vừa headless (tự áp Tailwind) vừa có sẵn bảng biểu, canh lề, cỡ chữ —
 * những thứ văn bản hành chính bắt buộc phải có.
 */
export function RichTextEditor({
  defaultContent,
  onChange,
  editable = true,
  showOutline = false,
  className,
}: RichTextEditorProps) {
  const [zoom, setZoom] = useState(1)

  const editor = useEditor({
    extensions: [
      // StarterKit v3 đã gồm sẵn Bold/Italic/Underline/Strike, tiêu đề, danh
      // sách, trích dẫn, đường kẻ ngang, LIÊN KẾT và lịch sử hoàn tác.
      StarterKit,
      // Phông, cỡ chữ, màu chữ, màu nền chữ.
      TextStyleKit,
      // Chỉ số trên / dưới — cần cho ký hiệu m², số mũ trong phụ lục.
      Subscript,
      Superscript,
      Image.configure({ inline: false, allowBase64: true }),
      // Giãn dòng + thụt lề đầu dòng, xem `paragraph-format-extension.ts`.
      ParagraphFormat,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      TableKit.configure({ table: { resizable: true } }),
      // Gõ quá một trang thì tự sang TRANG MỚI như Google Docs, thay vì kéo
      // dài mãi một tờ giấy — soạn công văn phải biết nội dung tràn sang trang
      // thứ mấy. Số đo lấy theo A4 ở 96dpi, khớp `.doc-page` trong `index.css`.
      PaginationPlus.configure({
        pageWidth: A4_WIDTH,
        // `pageHeight` là chiều cao CẢ TỜ GIẤY (lề nằm bên trong), nên để đúng
        // 1123 thì tỷ lệ trang mới ra 1:1,414 như A4 thật.
        pageHeight: A4_HEIGHT,
        marginTop: PAGE_MARGIN,
        marginBottom: PAGE_MARGIN,
        marginLeft: PAGE_MARGIN,
        marginRight: PAGE_MARGIN,
        // Lề trên/dưới đã khai ở `marginTop/Bottom`; để thêm ở đây là cộng dồn
        // thành lề dày hơn quy định.
        contentMarginTop: 0,
        contentMarginBottom: 0,
        pageGap: PAGE_GAP,
        pageGapBorderSize: 0,
        // Đúng màu nền xám của vùng đặt giấy (`--muted`), để khe giữa hai
        // trang nhìn xuyên xuống nền chứ không thành một vạch trắng.
        pageBreakBackground: '#f6f8fb',
      }),
    ],
    content: defaultContent,
    editable,
    onUpdate: ({ editor: instance }) => onChange(instance.getHTML()),
    editorProps: {
      attributes: {
        // `doc-page` = khổ A4 và kiểu chữ của thân văn bản, khai ở `index.css`.
        class: 'doc-page',
      },
    },
  })

  if (!editor) return null

  return (
    <div className={cn('overflow-hidden rounded-lg border bg-card', className)}>
      {editable && <EditorToolbar editor={editor} zoom={zoom} onZoomChange={setZoom} />}

      {/* Mục lục và trang giấy cuộn RIÊNG nhau: cuộn xuống cuối bài mà mục lục
          cũng trôi theo thì mất luôn chỗ để nhảy ngược lên. */}
      <div className="flex">
        {showOutline && (
          <EditorOutline
            editor={editor}
            className="hidden max-h-[calc(100vh-16rem)] w-56 shrink-0 overflow-y-auto border-r lg:block"
          />
        )}

        {/* Nền xám để tờ giấy trắng nổi lên — nhìn ra ngay đâu là mép trang.
            Cao theo màn hình chứ không cố định: màn 13" thì vẫn thấy được cả
            thanh công cụ lẫn cuối trang, màn lớn thì soạn được nhiều dòng hơn. */}
        <div className="max-h-[calc(100vh-16rem)] min-h-100 flex-1 overflow-x-auto overflow-y-auto bg-muted px-6 py-5">
          {/* Phóng bằng `zoom` chứ không phải `transform: scale`: `zoom` co giãn
              luôn cả hộp bố cục nên thanh cuộn vẫn đúng tầm và con trỏ chuột
              vẫn trỏ trúng chữ, còn `scale` thì phải tự bù chiều cao. */}
          <div style={{ zoom }}>
            <EditorContent editor={editor} />
          </div>
        </div>
      </div>
    </div>
  )
}
