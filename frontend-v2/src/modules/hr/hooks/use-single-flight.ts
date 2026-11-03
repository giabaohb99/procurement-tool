import { useCallback, useRef } from 'react'

/**
 * CHẶN BẤM ĐÚP cho các nút duyệt / từ chối / hủy / xóa / gửi: chỉ cho MỘT thao tác chạy tại một thời điểm.
 *
 * ⚠️ `disabled={mutation.isPending}` KHÔNG đủ — `isPending` chỉ đổi sau lần render kế tiếp, hai cú bấm trong
 * cùng một tick đều thấy `false` và cùng bắn request. Cờ nằm ở `useRef` nên đổi NGAY trong tick.
 *
 * `run(start)` gọi `start(release)`; thao tác phải gọi `release()` khi xong (thành công hay lỗi — dùng `onSettled`).
 * Lượt bấm tới khi đang chạy bị bỏ, `run` trả `false`.
 */
export function useSingleFlight() {
  const busy = useRef(false)
  return useCallback((start: (release: () => void) => void): boolean => {
    if (busy.current) return false
    busy.current = true
    try {
      start(() => {
        busy.current = false
      })
    } catch (error) {
      busy.current = false
      throw error
    }
    return true
  }, [])
}
