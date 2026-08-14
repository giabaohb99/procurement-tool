import { useLayoutEffect, useState, type RefObject } from 'react'

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
) {
  const [box, setBox] = useState({ left: 0, top: 0, height: 0 })

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
      }
      // So sánh trước khi set: hàm này chạy theo từng khung hình lúc cuộn.
      setBox((current) =>
        current.left === next.left &&
        current.top === next.top &&
        current.height === next.height
          ? current
          : next,
      )
    }

    measure()
    window.addEventListener('scroll', measure, { capture: true, passive: true })
    const observer = new ResizeObserver(measure)
    observer.observe(container)
    observer.observe(page)

    return () => {
      window.removeEventListener('scroll', measure, { capture: true })
      observer.disconnect()
    }
  }, [page, containerRef, watch])

  return box
}
