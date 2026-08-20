import { useEffect, useRef, useState, type CSSProperties } from 'react'

import { A4_HEIGHT_PX, A4_WIDTH_PX, MARGIN_TOP_MM, mmToPx } from '@/shared/ui/rich-text-editor'
import { cn } from '@/shared/utils/cn'
import {
  fillPageMarkers,
  hasPageMarkerContent,
  type PageMarkerValues,
} from '../helpers/page-marker'
import {
  oversizedCount,
  splitBlocksIntoPages,
  type PrintBlock,
} from '../helpers/split-blocks-into-pages'

interface DocumentPrintSheetProps {
  /** Thân văn bản (HTML do trình soạn thảo sinh ra). */
  html: string
  marginLeftMm: number
  marginRightMm: number
  /** Chữ chìm cảnh báo, vd "BẢN NHÁP" — bỏ trống thì không vẽ. */
  watermark?: string
  /** Đánh số mục tự động cho tiêu đề — bản in phải giống hệt màn soạn thảo. */
  autoNumber?: boolean
  /**
   * Đầu trang / chân trang, còn nguyên thẻ. Bản in là nơi DUY NHẤT thay được
   * `{{trang}}` và `{{tong_trang}}` bằng số thật, vì chỉ ở đây mới biết bài
   * chia ra mấy tờ.
   */
  pageFrame?: {
    header_left: string
    header_right: string
    footer_left: string
    footer_right: string
  }
  /** Giá trị cho các thẻ còn lại (số hiệu, tên văn bản, ngày in). */
  markers?: PageMarkerValues
  /** Báo ra số tờ và số khối sẽ tràn, để trang cha nói với người dùng. */
  onLayout?: (info: { pages: number; oversized: number }) => void
}

/**
 * Dựng THÂN VĂN BẢN thành từng tờ A4 rời để in.
 *
 * Đo trên DOM thật rồi mới chia: chiều cao một đoạn phụ thuộc phông, cỡ chữ,
 * giãn dòng và bề ngang còn lại sau khi trừ lề — không có công thức nào tính
 * trước được. Đo xong mới biết cắt ở đâu, và mỗi tờ là một thẻ riêng nên đánh
 * được số trang (xem `split-blocks-into-pages.ts`).
 */
export function DocumentPrintSheet({
  html,
  marginLeftMm,
  marginRightMm,
  watermark,
  autoNumber = false,
  pageFrame,
  markers,
  onLayout,
}: DocumentPrintSheetProps) {
  const measureRef = useRef<HTMLDivElement>(null)
  const [pages, setPages] = useState<PrintBlock[][] | null>(null)

  const contentWidth = A4_WIDTH_PX - mmToPx(marginLeftMm) - mmToPx(marginRightMm)
  const contentHeight = A4_HEIGHT_PX - 2 * mmToPx(MARGIN_TOP_MM)

  //  Giữ hàm báo trong ref: trang cha thường truyền hàm dựng mới mỗi lần render,
  //  để nó vào mảng phụ thuộc là đo lại vô tận. Gán trong effect chứ không gán
  //  thẳng lúc render — đụng ref lúc render là hành vi không đoán trước được
  //  khi React dựng lại giữa chừng.
  const layoutRef = useRef(onLayout)
  useEffect(() => {
    layoutRef.current = onLayout
  })

  useEffect(() => {
    let huy = false

    //  Chờ phông thật tải xong rồi mới đo: Times New Roman chưa sẵn sàng thì
    //  trình duyệt đo trên phông dự phòng, chữ thấp hơn thực tế và cả bài lọt
    //  vào ít trang hơn — in ra mới thấy dòng cuối bị đẩy sang tờ sau.
    //  `document.fonts` có thể không tồn tại (jsdom lúc chạy test, trình duyệt
    //  cũ) — thiếu nó thì đo luôn chứ không được đứng im không vẽ gì.
    const sanSang = document.fonts?.ready ?? Promise.resolve()

    void sanSang.then(() => {
      const host = measureRef.current
      if (huy || !host) return

      const blocks: PrintBlock[] = Array.from(host.children).map((node) => {
        const element = node as HTMLElement
        const style = window.getComputedStyle(element)
        return {
          html: element.outerHTML,
          height: element.getBoundingClientRect().height,
          spaceBefore: Number.parseFloat(style.marginTop) || 0,
        }
      })

      const chia = splitBlocksIntoPages(blocks, contentHeight)
      setPages(chia)
      layoutRef.current?.({
        pages: Math.max(chia.length, 1),
        oversized: oversizedCount(blocks, contentHeight),
      })
    })

    return () => {
      huy = true
    }
  }, [html, contentHeight, contentWidth])

  const soTo = pages?.length ?? 0

  /** Nội dung đầu/chân trang của tờ thứ `index` (0-based), đã thay hết thẻ. */
  function khungTrang(index: number) {
    if (!pageFrame) return null
    const giaTri: PageMarkerValues = { ...markers, trang: index + 1, tongTrang: soTo }
    return {
      headerLeft: fillPageMarkers(pageFrame.header_left, giaTri),
      headerRight: fillPageMarkers(pageFrame.header_right, giaTri),
      footerLeft: fillPageMarkers(pageFrame.footer_left, giaTri),
      footerRight: fillPageMarkers(pageFrame.footer_right, giaTri),
    }
  }

  return (
    <>
      {/* Bản đo: cùng bề ngang, cùng kiểu chữ với tờ thật, nhưng nằm ngoài tầm
          mắt và ngoài luồng bố cục. `visibility: hidden` chứ không phải
          `display: none` — thẻ ẩn hẳn thì mọi chiều cao đo được đều bằng 0. */}
      <div
        aria-hidden
        ref={measureRef}
        //  Bản đo phải mang CÙNG class với tờ thật: thiếu `doc-auto-number` thì
        //  đo hụt phần số mục và chia trang lệch.
        className={cn('doc-page doc-print-body', autoNumber && 'doc-auto-number-body')}
        style={{
          position: 'absolute',
          top: 0,
          left: -99999,
          width: contentWidth,
          visibility: 'hidden',
          pointerEvents: 'none',
        }}
        dangerouslySetInnerHTML={{ __html: html }}
      />

      {(pages ?? []).map((blocks, index) => (
        <section
          key={index}
          className="doc-print-sheet"
          style={
            {
              paddingLeft: `${marginLeftMm}mm`,
              paddingRight: `${marginRightMm}mm`,
              //  Dải đầu/chân trang canh theo đúng lề của trang, không phải lề
              //  cố định — lề trái 30mm mà dải bắt đầu ở 20mm thì lệch thấy rõ.
              '--doc-print-pad-left': `${marginLeftMm}mm`,
              '--doc-print-pad-right': `${marginRightMm}mm`,
            } as CSSProperties
          }
        >
          {watermark && <span className="doc-print-watermark">{watermark}</span>}

          {/* Đầu trang / chân trang lặp trên MỌI tờ, số trang thay bằng số thật
              của chính tờ này. Ô rỗng thì không vẽ dải nào cả — tờ giấy trống
              trên đầu vẫn hơn một dải kẻ trống trơn. */}
          {khungTrang(index) && (
            <>
              {hasPageMarkerContent(pageFrame?.header_left, pageFrame?.header_right) && (
                <div className="doc-print-frame doc-print-frame--top">
                  <span>{khungTrang(index)?.headerLeft}</span>
                  <span>{khungTrang(index)?.headerRight}</span>
                </div>
              )}
              {hasPageMarkerContent(pageFrame?.footer_left, pageFrame?.footer_right) && (
                <div className="doc-print-frame doc-print-frame--bottom">
                  <span>{khungTrang(index)?.footerLeft}</span>
                  <span>{khungTrang(index)?.footerRight}</span>
                </div>
              )}
            </>
          )}

          {/* Nghị định 30 điều 8: số trang đặt canh giữa ở LỀ TRÊN, KHÔNG hiện
              ở trang đầu. */}
          {index > 0 && <span className="doc-print-page-number">{index + 1}</span>}

          <div
            className={cn('doc-page doc-print-body', autoNumber && 'doc-auto-number-body')}
            dangerouslySetInnerHTML={{ __html: blocks.map((block) => block.html).join('') }}
          />
        </section>
      ))}
    </>
  )
}
