import { useEffect, type RefObject } from 'react'

/** Không có nhịp lăn nào trong bấy nhiêu ms thì coi như cử chỉ đã xong, mở khóa. */
const GESTURE_GAP_MS = 150

/** Một "dòng" của `deltaMode = DOM_DELTA_LINE` quy ra pixel — chuột lăn cổ điển. */
const LINE_HEIGHT = 16

export type WheelAxis = 'x' | 'y'

/**
 * KHÓA TRỤC cho mỗi cử chỉ lăn trên một khung cuộn.
 *
 * Trackpad không sinh ra cử chỉ "thuần ngang": vuốt hai ngón sang bên luôn kèm
 * một ít `deltaY`, nên ở một bảng cuộn được CẢ HAI CHIỀU (đúng như trục thời
 * gian của Gantt) người dùng định kéo sang tháng sau thì bảng vừa chạy ngang vừa
 * trôi dọc — khách báo *"tôi scroll ngang mà vô tình scroll dọc luôn"*. Đây là
 * bệnh của thiết bị chứ không sửa được bằng bố cục.
 *
 * Cách chữa: nhịp lăn ĐẦU của một cử chỉ quyết định trục (bên nào lớn hơn thì
 * thắng), rồi **giữ nguyên trục ấy** cho tới khi ngừng tay `GESTURE_GAP_MS`.
 * Trục kia bị nuốt hẳn. Latch theo cử chỉ chứ không xét lại từng nhịp: giữa một
 * cú vuốt ngang vẫn có những nhịp `|deltaY| > |deltaX|`, xét lại từng nhịp là
 * bảng giật qua giật lại đúng cái nó phải chặn.
 *
 * ⚠️ Phải tự `addEventListener(..., { passive: false })` chứ KHÔNG dùng
 * `onWheel` của React: React gắn `wheel` ở gốc cây theo lối **passive**, nên
 * `preventDefault()` trong `onWheel` bị bỏ qua không một lời cảnh báo — trục
 * thừa vẫn chạy y như cũ.
 *
 * `apply` phải ỔN ĐỊNH (bọc `useCallback`), không thì mỗi lần vẽ lại là gỡ và
 * gắn lại listener, mà gỡ giữa cử chỉ thì mất luôn trục đang khóa.
 */
export function useWheelAxisLock(
  ref: RefObject<HTMLElement | null>,
  apply: (axis: WheelAxis, deltaPx: number) => void,
) {
  useEffect(() => {
    if (!ref.current) return
    //  Gán ra một biến ĐÃ khai kiểu: bên trong `handleWheel` là một closure nên
    //  TypeScript không giữ được phép thu hẹp kiểu của `ref.current`.
    const el: HTMLElement = ref.current

    let axis: WheelAxis | null = null
    let lastAt = 0

    function handleWheel(event: WheelEvent) {
      //  Ctrl + lăn = cử chỉ PHÓNG TO của trackpad/trình duyệt, không phải cuộn.
      //  Nuốt nó ở đây là người dùng mất luôn phím tắt phóng to trang.
      if (event.ctrlKey) return
      if (event.deltaX === 0 && event.deltaY === 0) return

      if (axis === null || event.timeStamp - lastAt > GESTURE_GAP_MS) {
        axis = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? 'x' : 'y'
      }
      lastAt = event.timeStamp

      //  Chặn cuộn mặc định trong MỌI trường hợp, kể cả khi nhịp này không có
      //  gì trên trục đang khóa: để lọt là trình duyệt tự cuộn trục kia.
      event.preventDefault()

      const raw = axis === 'x' ? event.deltaX : event.deltaY
      if (raw !== 0) apply(axis, toPixels(raw, event.deltaMode, el))
    }

    el.addEventListener('wheel', handleWheel, { passive: false })
    return () => el.removeEventListener('wheel', handleWheel)
  }, [ref, apply])
}

function toPixels(delta: number, mode: number, el: HTMLElement): number {
  if (mode === WheelEvent.DOM_DELTA_LINE) return delta * LINE_HEIGHT
  if (mode === WheelEvent.DOM_DELTA_PAGE) return delta * el.clientHeight
  return delta
}
