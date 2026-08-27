import { EditorContent, useEditor, type Editor } from '@tiptap/react'
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type CSSProperties,
} from 'react'
import { PaginationPlus } from 'tiptap-pagination-plus'

import { cn } from '@/shared/utils/cn'
import { contentExtensions } from './content-extensions'
import { EditorContextMenu } from './editor-context-menu'
import { applyImportedContent, hasEditorContent, type DocumentImportMode } from './editor-import'
import { EditorOutlinePanel } from './editor-outline-panel'
import { EditorRuler, type PageMargins } from './editor-ruler'
import { EditorToolbar } from './editor-toolbar'
import { EditorVerticalRuler } from './editor-vertical-ruler'
import { ImportTrace } from './import-trace-extension'
import {
  A4_HEIGHT_PX,
  A4_WIDTH_PX,
  MARGIN_LEFT_MM,
  MARGIN_RIGHT_MM,
  MARGIN_TOP_MM,
  mmToPx,
} from './page-format'
import { useFillViewportHeight } from './use-fill-viewport-height'

/** Khổ giấy và lề — số gốc ở `page-format.ts`, dùng chung với bản in. */
const A4_WIDTH = A4_WIDTH_PX
const A4_HEIGHT = A4_HEIGHT_PX
const PAGE_MARGIN = mmToPx(MARGIN_TOP_MM)

/** Lề ngang mặc định (px) khi trang cha không truyền lề của bản ghi xuống. */
const DEFAULT_MARGINS: PageMargins = {
  left: mmToPx(MARGIN_LEFT_MM),
  right: mmToPx(MARGIN_RIGHT_MM),
}

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
  /**
   * Lề ngang (px) của bản ghi. Bỏ trống thì dùng lề Nghị định 30 và giữ trong
   * phiên soạn; truyền vào thì trang cha là nơi lưu, xem `onMarginsChange`.
   */
  defaultMargins?: PageMargins
  /**
   * Đánh số mục tự động cho tiêu đề (I · 1 · a). Bỏ trống `onAutoNumberChange`
   * thì thanh công cụ không hiện nút bật/tắt — dùng cho chỗ không có nơi lưu cờ.
   */
  autoNumber?: boolean
  onAutoNumberChange?: (bat: boolean) => void
  /**
   * Đầu trang / chân trang vẽ trên MỌI tờ giấy. Trang cha đã thay sẵn các thẻ
   * mà nó biết (số hiệu, tên, ngày); thẻ số trang thì trang cha để lại nhãn
   * ngắn vì lúc soạn chưa biết tờ nào là tờ thứ mấy của bản in.
   */
  pageFrame?: {
    headerLeft: string
    headerRight: string
    footerLeft: string
    footerRight: string
  }
  /**
   * Người dùng BUÔNG TAY khỏi thước — trang cha ghi xuống bản ghi.
   *
   * Chỉ bắn một lần cho mỗi cú chỉnh, không bắn theo từng khung hình lúc rê
   * chuột, nên trang cha ghi thẳng chứ không phải hẹn giờ gom nhịp.
   */
  onMarginsChange?: (margins: PageMargins) => void
  className?: string
}

export interface RichTextEditorHandle {
  /** Trình soạn thảo đang có nội dung thật, không tính đoạn rỗng mặc định. */
  hasContent: () => boolean
  /** Chèn tại con trỏ hoặc ghi đè toàn bộ theo chế độ nhập đã chọn. */
  insertContent: (html: string, mode?: DocumentImportMode) => Promise<boolean>
  /** Nhảy tới node đầu tiên được dựng từ một trang PDF trong báo cáo import. */
  focusImportedPage: (importId: string, page: number) => boolean
}

/** Chờ trình duyệt vẽ xong ít nhất một khung hình trước khi làm việc nặng. */
function afterPaint() {
  return new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()))
  })
}

/**
 * Gõ ngừng bao lâu (ms) thì mới chốt nội dung ra HTML.
 *
 * `getHTML()` duyệt lại TOÀN BỘ cây tài liệu; với văn bản nhập từ tệp Word dài,
 * làm việc đó ở mỗi phím gõ là đủ để chữ hiện ra chậm hơn tay. Mốc này ngắn hơn
 * nhiều so với nhịp tự động lưu (1,5 giây) nên không làm chậm việc lưu.
 */
const SERIALIZE_DELAY = 250

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
    {
      defaultContent,
      onChange,
      editable = true,
      showOutline = false,
      defaultMargins,
      onMarginsChange,
      autoNumber,
      onAutoNumberChange,
      pageFrame,
      className,
    },
    ref,
  ) {
    const [zoom, setZoom] = useState(1)
    //  Lề ngang do thước kẻ chỉnh. Giữ ở đây và BÁO RA cho trang cha ghi xuống
    //  bản ghi — như `defaultContent`, chỉ nhận giá trị ban đầu một lần: bám
    //  theo prop thì mỗi lần lưu xong lề lại đổ ngược vào giữa lúc đang kéo.
    const [margins, setMargins] = useState<PageMargins>(defaultMargins ?? DEFAULT_MARGINS)

    //  Rê chuột: chỉ vẽ lại trang giấy. Buông tay: mới ghi xuống bản ghi.
    function commitMargins(next: PageMargins) {
      setMargins(next)
      onMarginsChange?.(next)
    }
    // Cột mục lục: đóng/mở và bề ngang do người dùng chỉnh, giữ trong phiên soạn.
    const [outlineOpen, setOutlineOpen] = useState(true)
    const [outlineWidth, setOutlineWidth] = useState(224)

    //  Khung giấy cao hết phần màn hình còn lại — đo thật, xem hook.
    const pageFrameRef = useRef<HTMLDivElement>(null)
    const pageHeight = useFillViewportHeight(pageFrameRef)
    // Khi nhập file lớn, transaction chèn sẽ phát `onUpdate`. Không serialize
    // ở đó vì phía dưới còn bật lại pagination; chốt HTML đúng một lần sau khi
    // chèn xong để tránh duyệt cả cây tài liệu hai lần liên tiếp.
    const importingRef = useRef(false)

    // Giữ hàm báo thay đổi trong ref: `onUpdate` của Tiptap đóng băng closure
    // từ lần dựng đầu, còn hàm này thì trang cha có thể dựng lại.
    const changeRef = useRef(onChange)
    changeRef.current = onChange
    const serializeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

    function cancelSerialize() {
      if (serializeTimer.current === null) return false
      clearTimeout(serializeTimer.current)
      serializeTimer.current = null
      return true
    }

    /** Hẹn chốt HTML sau khi người dùng ngừng gõ — xem `SERIALIZE_DELAY`. */
    function scheduleChange(instance: Editor) {
      cancelSerialize()
      serializeTimer.current = setTimeout(() => {
        serializeTimer.current = null
        if (!instance.isDestroyed) changeRef.current(instance.getHTML())
      }, SERIALIZE_DELAY)
    }

    /** Chốt ngay lượt đang chờ: bấm ra ngoài (kể cả bấm nút Lưu) hoặc rời trang. */
    function flushChange(instance: Editor) {
      if (cancelSerialize() && !instance.isDestroyed) changeRef.current(instance.getHTML())
    }

    const editor = useEditor({
      extensions: [
        //  Lược đồ nội dung dùng chung với ô rich text trong hộp thoại — xem
        //  `content-extensions.ts`. Ở đây chỉ thêm phần dàn TRANG GIẤY.
        ...contentExtensions(),
        // Vết tích nguồn nhập (trang PDF nào ra node nào) — chỉ trang soạn thảo
        // toàn màn hình mới có luồng nhập tệp nên không đưa vào lược đồ chung.
        ImportTrace,
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
          //  Lề ngang chỉ khai lúc dựng: sau đó thước kẻ đổi lề bằng biến CSS
          //  (`--doc-margin-left/right`), plugin đo chiều cao trên DOM thật nên
          //  vẫn chia trang đúng.
          marginLeft: (defaultMargins ?? DEFAULT_MARGINS).left,
          marginRight: (defaultMargins ?? DEFAULT_MARGINS).right,
          // Lề trên/dưới đã khai ở `marginTop/Bottom`; để thêm ở đây là cộng dồn
          // thành lề dày hơn quy định.
          contentMarginTop: 0,
          contentMarginBottom: 0,
          pageGap: PAGE_GAP,
          pageGapBorderSize: 0,
          // Đúng màu nền xám của vùng đặt giấy (`--muted`), để khe giữa hai
          // trang nhìn xuyên xuống nền chứ không thành một vạch trắng.
          pageBreakBackground: '#f6f8fb',
          //  Đầu/chân trang: thư viện tự vẽ trên mọi tờ. Khai lúc dựng rồi cập
          //  nhật bằng lệnh khi trang cha đổi (xem effect bên dưới).
          headerLeft: pageFrame?.headerLeft ?? '',
          headerRight: pageFrame?.headerRight ?? '',
          footerLeft: pageFrame?.footerLeft ?? '',
          footerRight: pageFrame?.footerRight ?? '',
        }),
      ],
      content: defaultContent,
      editable,
      onCreate: ({ editor: instance }) => {
        // PaginationPlus chia trang bằng cách ĐO CHIỀU CAO DOM thật. Lúc editor
        // vừa dựng xong, phông của trang giấy ("Times New Roman" 14pt, khai ở
        // `index.css`) thường chưa tải xong nên nó đo trên phông dự phòng: chữ
        // thấp hơn thực tế, cả bài lọt vào MỘT trang. Sau đó không gì bắt nó đo
        // lại, nên trang chỉ "vỡ" ra đúng số tờ khi người dùng bấm chuột hay gõ
        // phím đầu tiên — nhìn như trang tự hỏng dưới tay.
        //
        // Chờ phông sẵn sàng rồi phát một transaction RỖNG: không đổi nội dung,
        // không vào lịch sử hoàn tác, không kích `onUpdate` (Tiptap chỉ gọi khi
        // `docChanged`), nhưng đủ để plugin đo lại trên phông thật.
        void document.fonts.ready.then(() => {
          if (instance.isDestroyed) return
          instance.view.dispatch(instance.state.tr.setMeta('addToHistory', false))
        })
      },
      onUpdate: ({ editor: instance }) => {
        if (!importingRef.current) scheduleChange(instance)
      },
      // Bấm ra khỏi trang giấy (nút Lưu, một tab khác, ô nhập khác) là chốt
      // ngay: `blur` bắn trước `click`, nên nút Lưu luôn nhận đúng nội dung vừa
      // gõ dù lượt hẹn ở trên chưa tới hạn.
      onBlur: ({ editor: instance }) => flushChange(instance),
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
        hasContent: () => Boolean(editor && !editor.isDestroyed && hasEditorContent(editor)),
        insertContent: async (html, mode = 'insert') => {
          if (!editor || editor.isDestroyed) return false

          const paginationEnabled = editor.storage.PaginationPlus.enabled
          importingRef.current = true
          try {
            // PaginationPlus đo DOM và dựng page-break ngay trong mỗi
            // transaction. Tắt nó trước khi chèn để phần parse + insert chỉ là
            // MỘT transaction nhẹ, sau đó mới đo trang một lần trên tài liệu đã
            // ổn định. Hai lần `afterPaint` giữ spinner/UI thật sự chuyển động.
            if (paginationEnabled) {
              editor.commands.disablePagination()
              await afterPaint()
            }

            // Người dùng có thể bấm Quay lại trong lúc file đang được API xử
            // lý; editor đã hủy thì dừng êm thay vì gọi command vào view cũ.
            if (editor.isDestroyed) return false

            const inserted = applyImportedContent(editor, html, mode)
            if (!inserted) return false

            await afterPaint()
            if (editor.isDestroyed) return false
            // Lượt hẹn của phím gõ trước đó (nếu có) coi như xong: nội dung
            // dưới đây đã bao gồm cả phần vừa chèn.
            cancelSerialize()
            changeRef.current(editor.getHTML())

            if (paginationEnabled) {
              await afterPaint()
              editor.commands.enablePagination()
              await afterPaint()
            }
            editor.view.focus()
            return true
          } finally {
            importingRef.current = false
            // Kể cả parser/transaction lỗi cũng không để editor mắc kẹt ở chế
            // độ không phân trang.
            if (
              paginationEnabled &&
              !editor.isDestroyed &&
              !editor.storage.PaginationPlus.enabled
            ) {
              editor.commands.enablePagination()
            }
          }
        },
        focusImportedPage: (importId, page) => {
          if (!editor || editor.isDestroyed) return false
          const matches: { pos: number; isTextblock: boolean }[] = []
          editor.state.doc.descendants((node, pos) => {
            if (node.attrs.importId === importId && Number(node.attrs.sourcePage) === page) {
              matches.push({ pos, isTextblock: node.isTextblock })
              return false
            }
            return true
          })
          const match = matches[0]
          if (!match) return false
          const chain = editor.chain().focus()
          if (match.isTextblock) chain.setTextSelection(match.pos + 1)
          else chain.setNodeSelection(match.pos)
          return chain.scrollIntoView().run()
        },
      }),
      [editor],
    )

    //  Trang cha lưu xong đầu/chân trang thì vẽ lại ngay, không phải dựng lại
    //  cả trình soạn thảo (dựng lại là mất lịch sử hoàn tác của người đang gõ).
    useEffect(() => {
      if (!editor || editor.isDestroyed || !pageFrame) return
      editor.commands.updateHeaderContent(pageFrame.headerLeft, pageFrame.headerRight)
      editor.commands.updateFooterContent(pageFrame.footerLeft, pageFrame.footerRight)
    }, [
      editor,
      pageFrame?.headerLeft,
      pageFrame?.headerRight,
      pageFrame?.footerLeft,
      pageFrame?.footerRight,
      pageFrame,
    ])

    // Rời trang bằng bàn phím hay điều hướng trong mã thì không có `blur` —
    // chốt nốt lượt đang chờ trước khi trình soạn thảo bị gỡ.
    useEffect(() => {
      if (!editor) return
      return () => {
        if (serializeTimer.current === null) return
        clearTimeout(serializeTimer.current)
        serializeTimer.current = null
        if (!editor.isDestroyed) changeRef.current(editor.getHTML())
      }
    }, [editor])

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
            autoNumber={onAutoNumberChange ? Boolean(autoNumber) : undefined}
            onToggleAutoNumber={
              onAutoNumberChange ? () => onAutoNumberChange(!autoNumber) : undefined
            }
          />
        )}

        {/* Thước ngang nằm ngoài vùng cuộn và kéo hết bề ngang — kể cả qua cột
          mục lục — nên nó dính liền dưới thanh công cụ thành một khối lệnh. */}
        {editable && (
          <EditorRuler
            pageWidth={A4_WIDTH}
            defaultMargins={DEFAULT_MARGINS}
            margins={margins}
            onChange={setMargins}
            onCommit={commitMargins}
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
              //  Dùng CHUNG số đo với khung giấy: hai cột đứng cạnh nhau mà cao
              //  khác nhau thì chừa ra một dải có mục lục nhưng không có giấy.
              maxHeight={pageHeight}
            />
          )}

          {/* Nền xám để tờ giấy trắng nổi lên — nhìn ra ngay đâu là mép trang.

            Chiều cao ĐO THẬT từ vị trí của chính khối này tới đáy cửa sổ (xem
            `useFillViewportHeight`), không trừ một hằng số. Trang chi tiết có
            tới bốn dải cảnh báo hiện/ẩn tùy lúc, và bản chỉ đọc thì không có
            thanh công cụ — mọi hằng số đều sai ở đa số trường hợp. */}
          <div
            ref={pageFrameRef}
            style={{ height: pageHeight }}
            className="min-h-80 min-w-0 flex-1 overflow-x-auto overflow-y-auto bg-muted px-6 py-5"
          >
            {/* Phóng bằng `zoom` chứ không phải `transform: scale`: `zoom` co
              giãn luôn cả hộp bố cục nên thanh cuộn vẫn đúng tầm và con trỏ
              chuột vẫn trỏ trúng chữ, còn `scale` thì phải tự bù chiều cao.

              Hai biến lề đặt ở đây để thước kẻ và trang giấy cùng đọc một số —
              trang giấy nhận qua `.doc-page` trong `index.css`. */}
            <div
              //  Class bật đánh số mục nằm ở thẻ BỌC NGOÀI trang giấy, không
              //  phải trên chính `.doc-page`: đổi class của trang giấy phải đi
              //  qua `editorProps` và dựng lại trình soạn thảo.
              className={cn(autoNumber && 'doc-auto-number')}
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
