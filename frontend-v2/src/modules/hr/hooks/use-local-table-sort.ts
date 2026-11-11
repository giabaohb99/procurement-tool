// duoc-CR-748 — trạng thái sắp xếp CỤC BỘ (state, không lên URL) cho các bảng con của phân hệ Nhân sự: bảng nằm
// trong trang chi tiết (nhân sự thuộc phòng, người đang giữ chức vụ, lịch đặt của phòng, đơn nghỉ của một dòng quỹ),
// tab hồ sơ, hộp thoại... Những chỗ đó đã có tham số URL của riêng trang (`tab`, `whView`, `mode`/`date`), mà một
// trang có thể bày HAI bảng cùng lúc — ghi `sort_by` lên URL thì hai bảng tranh nhau một cặp tham số.
//
// Hai cách dùng, cùng một trạng thái:
// - bảng phân trang / cắt dòng ở MÁY CHỦ: trải `params` vào lời gọi API để backend xếp trên CẢ tập, đừng xếp lại
//   một trang ở trình duyệt (luật §8 của `chung-dat-ten-va-quy-uoc.md`);
// - bảng nạp ĐỦ mọi dòng: đưa `sortBy` / `sortDir` vào `sortRowsByCell` / `sortRowsBy` trước khi cắt trang.
//
// Nhịp thứ ba của tiêu đề cột trả khóa RỖNG = thôi sắp xếp: `params` rỗng (backend về thứ tự mặc định của nó),
// bảng trình duyệt về thứ tự gốc. Bản sinh đôi ở Tra cứu thị trường: `procurement/hooks/use-local-server-sort.ts`.
import { useCallback, useMemo, useState } from 'react'

import type { SortDir } from '@/shared/utils/compare-sort-values'

export interface LocalTableSort {
  sortBy: string
  sortDir: SortDir
  /** Cắm thẳng vào `onSortChange` của `DataTable`. */
  onSortChange: (sortBy: string, sortDir: SortDir) => void
  /** `{ sort_by, sort_dir }` khi đang xếp, rỗng khi chưa bấm cột nào — trải thẳng vào tham số API. */
  params: { sort_by?: string; sort_dir?: SortDir }
}

export function useLocalTableSort(): LocalTableSort {
  const [state, setState] = useState<{ by: string; dir: SortDir }>({ by: '', dir: 'asc' })
  const onSortChange = useCallback((by: string, dir: SortDir) => {
    setState({ by, dir: by ? dir : 'asc' })
  }, [])
  const params = useMemo(
    () => (state.by ? { sort_by: state.by, sort_dir: state.dir } : {}),
    [state],
  )
  return { sortBy: state.by, sortDir: state.dir, onSortChange, params }
}
