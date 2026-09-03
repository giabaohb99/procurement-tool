import { useLayoutEffect, useState, type RefObject } from 'react'

/**
 * Bề rộng thật của một phần tử, cập nhật khi nó co giãn.
 *
 * Dùng `ResizeObserver` chứ không nghe `resize` của cửa sổ: khung Gantt còn co
 * giãn vì những lý do chẳng liên quan gì tới cửa sổ — thu/mở menu trái, mở panel
 * chi tiết. Nghe `resize` thì mấy trường hợp đó im lặng bỏ qua.
 *
 * `useLayoutEffect` để số đo có ngay ở nhịp vẽ đầu tiên: trả 0 rồi mới sửa ở
 * nhịp sau là lưới trái nháy một cái từ bề rộng tối thiểu sang bề rộng thật.
 */
export function useElementWidth(ref: RefObject<HTMLElement | null>): number {
  const [width, setWidth] = useState(0)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    setWidth(el.clientWidth)

    const observer = new ResizeObserver(([entry]) => {
      //  `clientWidth` chứ không `contentRect.width`: cái sau là số thực có phần
      //  lẻ, mỗi nhịp lệch 0.5px là một lần đặt lại state vô ích.
      setWidth(entry.target.clientWidth)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [ref])

  return width
}
