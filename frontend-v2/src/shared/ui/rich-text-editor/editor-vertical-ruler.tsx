import { useRef } from 'react'

import { cmMarks, PX_PER_CM } from './ruler-metrics'
import { usePageOffset } from './use-page-offset'

interface EditorVerticalRulerProps {
  /** Chiều cao một trang giấy và khe giữa hai trang (px thật, chưa phóng). */
  pageHeight: number
  pageGap: number
  /** Lề trên/dưới của trang — tô xám cho biết chữ bắt đầu từ đâu. */
  margin: number
  zoom: number
  /** Thẻ trang giấy (gồm tất cả các trang) — thước bám theo vị trí của nó. */
  page: HTMLElement | null
}

/**
 * THƯỚC KẺ DỌC, dựng sát cột mục lục.
 *
 * CHỈ ĐỂ ĐỌC, không kéo được như thước ngang: lề trên/dưới là số liệu
 * `PaginationPlus` dùng để tính một trang chứa được bao nhiêu dòng, đổi nóng thì
 * phải dựng lại cả trình soạn thảo — mất sạch lịch sử hoàn tác của người đang
 * gõ. Ở đây nó trả lời đúng một câu hỏi hay gặp: "đoạn này đã xuống tới đâu của
 * tờ giấy rồi?".
 *
 * Vạch đánh lại từ đầu ở MỖI TRANG, y như thước của Word: đang ở trang 3 mà
 * thước chạy tiếp số 65cm thì đọc ra cũng chẳng để làm gì.
 */
export function EditorVerticalRuler({
  pageHeight,
  pageGap,
  margin,
  zoom,
  page,
}: EditorVerticalRulerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const offset = usePageOffset(page, containerRef, zoom)

  // Số trang suy ra từ chiều cao thật của khối trang giấy: `PaginationPlus`
  // xếp các trang cách đều nhau nên chia là ra, khỏi phải hỏi nó.
  const contentHeight = offset.height / zoom
  const pageCount = Math.max(1, Math.round((contentHeight + pageGap) / (pageHeight + pageGap)))
  const marks = cmMarks(pageHeight)
  const at = (value: number) => value * zoom

  return (
    <div
      ref={containerRef}
      aria-hidden
      className="relative w-5 shrink-0 overflow-hidden border-r bg-muted/40 select-none"
    >
      {Array.from({ length: pageCount }, (_, index) => {
        const pageTop = offset.top + at(index * (pageHeight + pageGap))

        return (
          <div
            key={index}
            // Không viền quanh dải thước — xem lý do ở `editor-ruler.tsx`.
            className="absolute inset-x-0.5 rounded-sm bg-card"
            style={{ top: pageTop, height: at(pageHeight) }}
          >
            <div
              className="absolute inset-x-0 top-0 rounded-t-sm bg-muted"
              style={{ height: at(margin) }}
            />
            <div
              className="absolute inset-x-0 bottom-0 rounded-b-sm bg-muted"
              style={{ height: at(margin) }}
            />

            {marks.map((cm) => (
              <span
                key={cm}
                className="absolute left-1/2 text-[9px] leading-none text-muted-foreground [writing-mode:vertical-rl]"
                style={{ top: at(cm * PX_PER_CM), transform: 'translate(-50%, -50%)' }}
              >
                {cm || ''}
              </span>
            ))}

            {marks.slice(0, -1).map((cm) => (
              <span
                key={`half-${cm}`}
                className="absolute left-1/2 h-px w-1 -translate-x-1/2 bg-border"
                style={{ top: at((cm + 0.5) * PX_PER_CM) }}
              />
            ))}
          </div>
        )
      })}
    </div>
  )
}
