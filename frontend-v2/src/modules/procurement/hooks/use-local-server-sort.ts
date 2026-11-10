// duoc-CR-744 — trạng thái sắp xếp CỤC BỘ của một bảng phân trang phía server trong Tra cứu thị trường.
//
// Dùng cho bảng không có bộ lọc trên URL (lô nạp, nhật ký lô, kết quả từng dòng, các danh mục ở mục Cấu hình):
// giữ `{ by, dir }` trong state, đưa `params` (`sort_by`/`sort_dir`) vào lời gọi API để backend xếp trên CẢ tập
// chứ không riêng trang đang xem. Nhịp thứ ba của tiêu đề cột trả khóa RỖNG = thôi sắp xếp (về thứ tự mặc định
// của backend). Đổi thứ tự thì gọi `onChange` để trang kéo về 1 — đứng ở trang 5 của thứ tự cũ rồi nhảy sang
// thứ tự mới là lạc.
import { useCallback, useMemo, useState } from 'react'

export interface LocalServerSort {
  sortBy: string
  sortDir: 'asc' | 'desc'
  /** Cắm thẳng vào `onSortChange` của `DataTable`. */
  onSortChange: (sortBy: string, sortDir: 'asc' | 'desc') => void
  /** Rỗng khi chưa bấm cột nào — trải thẳng vào tham số API. */
  params: Record<string, string>
}

export function useLocalServerSort(onChange?: () => void): LocalServerSort {
  const [state, setState] = useState<{ by: string; dir: 'asc' | 'desc' }>({ by: '', dir: 'asc' })
  const onSortChange = useCallback(
    (by: string, dir: 'asc' | 'desc') => {
      setState({ by, dir: by ? dir : 'asc' })
      onChange?.()
    },
    [onChange],
  )
  const params = useMemo<Record<string, string>>(() => {
    const next: Record<string, string> = {}
    if (state.by) {
      next.sort_by = state.by
      next.sort_dir = state.dir
    }
    return next
  }, [state])
  return { sortBy: state.by, sortDir: state.dir, onSortChange, params }
}
