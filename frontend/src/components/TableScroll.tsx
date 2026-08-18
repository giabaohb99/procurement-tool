import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react'

/**
 * Vùng cuộn ngang của bảng danh sách — thay cho `<div className="table-scroll">`.
 *
 * VẤN ĐỀ: bảng nhiều cột (Tiến độ mua hàng, Công nợ, Tồn kho…) rộng hơn màn hình.
 * Thanh cuộn ngang của trình duyệt nằm ở ĐÁY khối cuộn, mà khối cuộn cao bằng cả
 * 20 dòng dữ liệu, nên nó rơi xuống đáy tài liệu: muốn kéo ngang phải cuộn dọc
 * hết trang mới chạm được tới nó.
 *
 * CÁCH SỬA: giữ nguyên khối cuộn cũ (không đụng gì tới bố cục dọc), thêm một
 * thanh cuộn PHỤ neo đáy màn hình (`position: fixed`) đồng bộ hai chiều với khối
 * thật. Thanh phụ chỉ hiện khi CẢ HAI điều kiện đúng:
 *   1. bảng rộng hơn khung — có gì để kéo ngang;
 *   2. đáy khung đang nằm dưới tầm nhìn — thanh cuộn thật đang ngoài màn hình.
 * Bảng vừa màn hình, hoặc đã cuộn tới đáy bảng, thì không có gì đổi so với trước.
 */
export default function TableScroll({ children }: { children: ReactNode }) {
  const boxRef = useRef<HTMLDivElement>(null)
  const barRef = useRef<HTMLDivElement>(null)
  /* Cờ chống vòng lặp: gán scrollLeft cho bên kia lại kích hoạt onScroll của bên kia. */
  const syncingRef = useRef(false)

  const [bar, setBar] = useState({ show: false, left: 0, width: 0, content: 0 })

  const measure = useCallback(() => {
    const box = boxRef.current
    if (!box) return
    const rect = box.getBoundingClientRect()
    const overflow = box.scrollWidth - box.clientWidth > 1
    /* Đáy khối cuộn nằm dưới mép dưới màn hình => thanh cuộn thật đang khuất. */
    const belowFold = rect.bottom > window.innerHeight
    setBar((prev) => {
      const next = {
        show: overflow && belowFold && rect.width > 0,
        left: Math.round(rect.left),
        width: Math.round(rect.width),
        content: Math.round(box.scrollWidth),
      }
      if (
        prev.show === next.show && prev.left === next.left &&
        prev.width === next.width && prev.content === next.content
      ) return prev
      return next
    })
  }, [])

  useLayoutEffect(() => {
    measure()
    const box = boxRef.current
    if (!box) return
    /* Bảng đổi số dòng / đổi bề rộng cột / mở-đóng bộ lọc đều làm đổi số đo. */
    const ro = new ResizeObserver(measure)
    ro.observe(box)
    if (box.firstElementChild) ro.observe(box.firstElementChild)
    window.addEventListener('scroll', measure, { passive: true })
    window.addEventListener('resize', measure)
    return () => {
      ro.disconnect()
      window.removeEventListener('scroll', measure)
      window.removeEventListener('resize', measure)
    }
  }, [measure])

  /* Thanh phụ vừa hiện thì kéo nó về đúng vị trí ngang hiện tại của bảng. */
  useEffect(() => {
    if (bar.show && barRef.current && boxRef.current) {
      barRef.current.scrollLeft = boxRef.current.scrollLeft
    }
  }, [bar.show])

  const relay = (from: HTMLDivElement | null, to: HTMLDivElement | null) => {
    if (!from || !to || syncingRef.current) return
    syncingRef.current = true
    to.scrollLeft = from.scrollLeft
    /* Nhả cờ ở khung hình sau, khi onScroll dội lại đã chạy xong. */
    requestAnimationFrame(() => { syncingRef.current = false })
  }

  return (
    <>
      <div
        ref={boxRef}
        className="table-scroll"
        onScroll={() => relay(boxRef.current, barRef.current)}
      >
        {children}
      </div>
      {bar.show && (
        <div
          ref={barRef}
          className="table-scroll-proxy"
          style={{ left: bar.left, width: bar.width }}
          onScroll={() => relay(barRef.current, boxRef.current)}
          aria-hidden="true"
        >
          <div style={{ width: bar.content, height: 1 }} />
        </div>
      )}
    </>
  )
}
