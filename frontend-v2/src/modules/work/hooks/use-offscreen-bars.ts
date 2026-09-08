import { useEffect, useState, type RefObject } from 'react'

/** Thanh đang nằm ngoài tầm nhìn ở phía nào. */
export type OffscreenSide = 'left' | 'right'

/**
 * Những việc có thanh đã trôi HẲN ra ngoài khung nhìn theo chiều ngang, kèm
 * hướng phải cuộn để về lại.
 *
 * Dùng để vẽ chip mũi tên ở mép khung, đúng hàng của việc ấy — trục nay dài hai
 * năm (xem `khungToiThieu`) nên kéo vài nhịp là mọi thanh biến mất, còn lại một
 * tấm lưới trống trơn không biết việc nằm bên nào.
 *
 * ⚠️ Dùng `IntersectionObserver` chứ KHÔNG đọc `scrollLeft` trong `onScroll`:
 * đọc theo cuộn thì mỗi nhịp lăn là một lần `setState`, mà mỗi lần vẽ lại
 * `GanttView` là React phải so lại tấm lưới nền — ở mức phóng Ngày với dải hai
 * năm, tấm ấy là hơn 700 nút. `IntersectionObserver` chỉ bắn khi một thanh ĐỔI
 * trạng thái nhìn thấy được, tức vài lần cho cả cú cuộn.
 *
 * Chỉ xét chiều NGANG. Cuộn dọc cũng làm thanh rời khỏi khung, nhưng lúc ấy cả
 * hàng của nó cũng ra khỏi màn hình nên chip vẽ ra chẳng ai thấy — coi như vẫn
 * trong tầm để khỏi bắn ra một loạt cập nhật vô ích mỗi lần cuộn dọc.
 */
export function useOffscreenBars(
  rootRef: RefObject<HTMLElement | null>,
  /** Đổi khi bộ thanh được vẽ lại (dữ liệu hoặc mức phóng đổi) — để gắn lại observer. */
  resetKey: unknown,
): Map<number, OffscreenSide> {
  const [offscreen, setOffscreen] = useState<Map<number, OffscreenSide>>(new Map())

  useEffect(() => {
    const root = rootRef.current
    if (!root) return

    const bars = root.querySelectorAll<HTMLElement>('[data-gantt-bar][data-task-id]')
    if (bars.length === 0) {
      setOffscreen((prev) => (prev.size === 0 ? prev : new Map()))
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        setOffscreen((prev) => {
          const next = new Map(prev)
          for (const entry of entries) {
            const id = Number(entry.target.getAttribute('data-task-id'))
            const khung = entry.rootBounds
            if (!id || !khung) continue

            const hop = entry.boundingClientRect
            if (hop.right <= khung.left) next.set(id, 'left')
            else if (hop.left >= khung.right) next.set(id, 'right')
            else next.delete(id)
          }
          return next
        })
      },
      { root, threshold: 0 },
    )

    bars.forEach((bar) => observer.observe(bar))
    return () => observer.disconnect()
  }, [rootRef, resetKey])

  return offscreen
}
