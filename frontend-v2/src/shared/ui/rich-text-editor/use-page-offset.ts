import { useLayoutEffect, useState, type RefObject } from 'react'

export interface PageOffset {
  left: number
  top: number
  height: number
  /** Chiều cao khung nhìn của cây thước — để chỉ vẽ phần trang đang thấy. */
  viewport: number
}

/**
 * Vị trí và chiều cao của TỜ GIẤY so với khung của cây thước.
 *
 * Hai cây thước nằm ngoài vùng cuộn (một dính dưới thanh công cụ, một sát mục
 * lục) nên không tự trôi theo trang giấy. Thay vì cộng trừ tay từng thứ chen
 * giữa — bề ngang mục lục, phần đệm của vùng cuộn, chỗ căn giữa trang, mức
 * phóng — cứ ĐO thẳng khoảng cách giữa hai thẻ: đo một lần là đúng mọi bố cục,
 * kể cả khi mục lục bị ẩn ở màn hẹp.
 *
 * Nghe `scroll` ở PHA CAPTURE trên `window` chứ không gắn vào đúng thẻ vùng
 * cuộn: thước được vẽ trước thẻ đó trong cây, lúc effect này chạy thì `ref` của
 * nó vẫn còn rỗng nên gắn vào là gắn hụt, cuộn không thấy thước nhúc nhích.
 * `scroll` không nổi bọt lên, nhưng pha capture thì vẫn nghe được.
 */
export function usePageOffset(
  page: HTMLElement | null,
  containerRef: RefObject<HTMLElement | null>,
  /** Đổi giá trị này là đo lại (mức phóng, lề…). */
  watch: unknown,
  /**
   * Trục mà người gọi thật sự dùng: thước ngang chỉ đọc `left`, thước dọc chỉ
   * đọc `top/height`. Lọc theo trục để cuộn DỌC không kéo theo thước ngang vẽ
   * lại — với tài liệu vài chục trang, mỗi lần vẽ thừa là một khung hình rớt.
   */
  axis: 'x' | 'y' = 'y',
) {
  const [box, setBox] = useState<PageOffset>({ left: 0, top: 0, height: 0, viewport: 0 })

  useLayoutEffect(() => {
    const container = containerRef.current
    if (!page || !container) return

    const measure = () => {
      const pageBox = page.getBoundingClientRect()
      const containerBox = container.getBoundingClientRect()
      const next = {
        left: pageBox.left - containerBox.left,
        top: pageBox.top - containerBox.top,
        height: pageBox.height,
        viewport: containerBox.height,
      }
      // So sánh trước khi set: hàm này chạy theo từng khung hình lúc cuộn.
      setBox((current) =>
        (
          axis === 'x'
            ? current.left === next.left
            : current.top === next.top &&
              current.height === next.height &&
              current.viewport === next.viewport
        )
          ? current
          : next,
      )
    }

    // Một cú lăn chuột bắn ra nhiều sự kiện `scroll` trong CÙNG một khung hình,
    // mà mỗi lần đo là một lần bắt trình duyệt tính lại bố cục của cả tài liệu
    // (`getBoundingClientRect`). Gom về đúng một lần đo mỗi khung hình.
    let frame = 0
    const schedule = () => {
      if (frame) return
      frame = requestAnimationFrame(() => {
        frame = 0
        measure()
      })
    }

    measure()
    window.addEventListener('scroll', schedule, { capture: true, passive: true })
    const observer = new ResizeObserver(schedule)
    observer.observe(container)
    observer.observe(page)

    return () => {
      if (frame) cancelAnimationFrame(frame)
      window.removeEventListener('scroll', schedule, { capture: true })
      observer.disconnect()
    }
  }, [page, containerRef, watch, axis])

  return box
}
