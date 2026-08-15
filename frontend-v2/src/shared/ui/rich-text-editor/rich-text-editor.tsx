import { Image } from '@tiptap/extension-image'
import { Subscript } from '@tiptap/extension-subscript'
import { Superscript } from '@tiptap/extension-superscript'
import { TableKit } from '@tiptap/extension-table'
import { TextAlign } from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { forwardRef, useImperativeHandle, useState, type CSSProperties } from 'react'
import { PaginationPlus } from 'tiptap-pagination-plus'

import { cn } from '@/shared/utils/cn'
import { EditorContextMenu } from './editor-context-menu'
import { EditorOutlinePanel } from './editor-outline-panel'
import { EditorRuler, type PageMargins } from './editor-ruler'
import { EditorToolbar } from './editor-toolbar'
import { EditorVerticalRuler } from './editor-vertical-ruler'
import { ParagraphFormat } from './paragraph-format-extension'
import {
  TableCellWithBackground,
  TableHeaderWithBackground,
} from './table-cell-background-extension'
import { TableWithColumnResizing } from './table-column-resizing-extension'
import { TableRowWithHeight } from './table-row-resizing-extension'

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

export interface RichTextEditorHandle {
  /** Chèn HTML tại vị trí con trỏ hiện tại; trả false khi editor chưa sẵn sàng. */
  insertContent: (html: string) => boolean
}

/**
 * Trình soạn thảo văn bản kiểu Word: thanh công cụ trên, TRANG GIẤY TRẮNG ở
 * giữa nền xám — soạn thẳng trên hệ thống thay vì làm ở Word rồi tải tệp lên.
 *
 * Dựng trên Tiptap (ProseMirror) vì đây là thứ duy nhất trong hệ sinh thái
 * React vừa headless (tự áp Tailwind) vừa có sẵn bảng biểu, canh lề, cỡ chữ —
 * những thứ văn bản hành chính bắt buộc phải có.
 */
export const RichTextEditor = forwardRef<RichTextEditorHandle, RichTextEditorProps>(
  function RichTextEditor(
    { defaultContent, onChange, editable = true, showOutline = false, className },
    ref,
  ) {
    const [zoom, setZoom] = useState(1)
    // Lề ngang do thước kẻ chỉnh. Giữ ở đây (chưa lưu xuống bản ghi): đổi lề là
    // việc căn chỉnh lúc soạn, mở lại văn bản thì về đúng lề quy định.
    const [margins, setMargins] = useState<PageMargins>({
      left: PAGE_MARGIN,
      right: PAGE_MARGIN,
    })
    // Cột mục lục: đóng/mở và bề ngang do người dùng chỉnh, giữ trong phiên soạn.
    const [outlineOpen, setOutlineOpen] = useState(true)
    const [outlineWidth, setOutlineWidth] = useState(224)

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
        // Tắt ô / ô tiêu đề / hàng mặc định để thay bằng bản có thêm MÀU NỀN
        // (`table-cell-background-extension.ts`) và KÉO CAO HÀNG
        // (`table-row-resizing-extension.ts`).
        // Tắt luôn cả bảng mặc định: phần kéo cột dựng sẵn làm bảng phình quá
        // khổ giấy, thay bằng bản kéo cột kiểu Word ở
        // `table-column-resizing-extension.ts`.
        TableKit.configure({
          table: false,
          tableCell: false,
          tableHeader: false,
          tableRow: false,
        }),
        // `resizable: false` để tắt phần kéo cột dựng sẵn, nhưng vẫn giữ nguyên
        // phần còn lại của bảng (vùng chọn ô, `<colgroup>` giữ bề rộng cột).
        TableWithColumnResizing.configure({ resizable: false }),
        TableCellWithBackground,
        TableHeaderWithBackground,
        TableRowWithHeight,
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

    useImperativeHandle(
      ref,
      () => ({
        insertContent: (html) =>
          editor ? editor.chain().focus().insertContent(html).scrollIntoView().run() : false,
      }),
      [editor],
    )

    if (!editor) return null

    return (
      <div className={cn('overflow-hidden rounded-lg border bg-card', className)}>
        {editable && (
          <EditorToolbar
            editor={editor}
            zoom={zoom}
            onZoomChange={setZoom}
            outlineOpen={showOutline ? outlineOpen : undefined}
            onToggleOutline={() => setOutlineOpen((open) => !open)}
          />
        )}

        {/* Thước ngang nằm ngoài vùng cuộn và kéo hết bề ngang — kể cả qua cột
          mục lục — nên nó dính liền dưới thanh công cụ thành một khối lệnh. */}
        {editable && (
          <EditorRuler
            pageWidth={A4_WIDTH}
            defaultMargin={PAGE_MARGIN}
            margins={margins}
            onChange={setMargins}
            zoom={zoom}
            page={editor.view.dom}
          />
        )}

        {/* Mục lục và trang giấy cuộn RIÊNG nhau: cuộn xuống cuối bài mà mục lục
          cũng trôi theo thì mất luôn chỗ để nhảy ngược lên. */}
        <div className="flex">
          {/* Thước dọc nằm ở MÉP TRÁI khung soạn thảo, ngoài cả cột mục lục —
            giống Google Docs: hai cây thước gặp nhau ở góc trên bên trái nên
            đọc ra ngay đây là gốc tọa độ của tờ giấy. */}
          {editable && (
            <EditorVerticalRuler
              pageHeight={A4_HEIGHT}
              pageGap={PAGE_GAP}
              margin={PAGE_MARGIN}
              zoom={zoom}
              page={editor.view.dom}
            />
          )}

          {showOutline && outlineOpen && (
            <EditorOutlinePanel
              editor={editor}
              width={outlineWidth}
              onWidthChange={setOutlineWidth}
            />
          )}

          {/* Nền xám để tờ giấy trắng nổi lên — nhìn ra ngay đâu là mép trang.
            Cao theo màn hình chứ không cố định: màn 13" thì vẫn thấy được cả
            thanh công cụ lẫn cuối trang, màn lớn thì soạn được nhiều dòng. */}
          <div className="max-h-[calc(100vh-16rem)] min-h-100 min-w-0 flex-1 overflow-x-auto overflow-y-auto bg-muted px-6 py-5">
            {/* Phóng bằng `zoom` chứ không phải `transform: scale`: `zoom` co
              giãn luôn cả hộp bố cục nên thanh cuộn vẫn đúng tầm và con trỏ
              chuột vẫn trỏ trúng chữ, còn `scale` thì phải tự bù chiều cao.

              Hai biến lề đặt ở đây để thước kẻ và trang giấy cùng đọc một số —
              trang giấy nhận qua `.doc-page` trong `index.css`. */}
            <div
              style={
                {
                  zoom,
                  '--doc-margin-left': `${margins.left}px`,
                  '--doc-margin-right': `${margins.right}px`,
                } as CSSProperties
              }
            >
              {/* Chỉ bọc menu chuột phải khi CÒN SỬA ĐƯỢC: trang chỉ để xem thì
                menu toàn lệnh sửa là bày ra cho có, mà lại chặn mất menu gốc
                của trình duyệt (dịch, tìm kiếm chữ đang chọn…). */}
              {editable ? (
                <EditorContextMenu editor={editor}>
                  <div>
                    <EditorContent editor={editor} />
                  </div>
                </EditorContextMenu>
              ) : (
                <EditorContent editor={editor} />
              )}
            </div>
          </div>
        </div>
      </div>
    )
  },
)
