import { useEffect, useState, type RefObject } from 'react'

/**
 * Khung CUỘN gần nhất bao lấy `element` — `window` nếu không có khung nào.
 *
 * ⚠️ Phải dò từ DOM chứ không đoán được: trang trong phân hệ nằm trong một khối
 * `overflow-auto` của bố cục (không phải `window`), nhưng trang chi tiết mở
 * trong hộp thoại lại cuộn ở một khối khác. Gắn cứng một trong hai là cái kia
 * không bao giờ bắn sự kiện, mà lỗi đó im lặng — không có gì đỏ lên, chỉ là hiệu
 * ứng không bao giờ chạy.
 */
function findScrollParent(element: HTMLElement | null): HTMLElement | Window {
  let node = element?.parentElement ?? null
  while (node) {
    const overflowY = getComputedStyle(node).overflowY
    if (overflowY === 'auto' || overflowY === 'scroll') return node
    node = node.parentElement
  }
  return window
}

/**
 * Khung chứa `ref` đã bị cuộn khỏi đỉnh chưa.
 *
 * Dùng để dải ghim đầu trang (`position: sticky`) chỉ đổ bóng KHI có nội dung
 * chạy bên dưới nó. Đổ bóng sẵn từ lúc chưa cuộn thì dải trông như đang nổi lên
 * giữa một trang đứng yên — bóng là để nói "có thứ đang trôi phía dưới", nói
 * điều đó lúc chưa có gì trôi là nói sai.
 *
 * ⚠️ `threshold` khác 0: cuộn đàn hồi trên iOS trả về `scrollTop` âm rồi nhích
 * qua 0 vài lần trong một cú vuốt, để mốc 0 thì bóng nhấp nháy theo.
 */
export function useScrolled(ref: RefObject<HTMLElement | null>, threshold = 4): boolean {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const target = findScrollParent(ref.current)

    const read = () => {
      const top = target instanceof Window ? window.scrollY : target.scrollTop
      setScrolled(top > threshold)
    }

    //  Đọc một lần ngay lúc gắn: quay lại trang bằng nút Back thì trình duyệt
    //  khôi phục vị trí cuộn TRƯỚC khi có sự kiện nào bắn ra.
    read()
    target.addEventListener('scroll', read, { passive: true })
    return () => target.removeEventListener('scroll', read)
  }, [ref, threshold])

  return scrolled
}
