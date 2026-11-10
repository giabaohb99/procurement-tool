// duoc-CR-744 — sắp xếp NGAY TRÊN TRÌNH DUYỆT cho các bảng nhỏ của Tra cứu thị trường đã tải đủ mọi dòng
// (xếp hạng doanh nghiệp, bảng kỳ của biểu đồ / so sánh, biểu thuế): không có phân trang nên không cần hỏi server.
//
// Xếp theo giá trị ô ĐANG HIỂN THỊ (người gọi khai `getValue` đúng giá trị đó, không phải giá trị thô): số so theo
// số, chữ so theo tiếng Việt, ô trống luôn xuống CUỐI ở cả hai chiều — cùng luật với các bảng xếp tại server
// (`shared/utils/compare-sort-values.ts`, backend `core/sort_order.py`). Bằng nhau thì giữ thứ tự gốc.
// Nhịp thứ ba của tiêu đề cột (khóa rỗng) = thôi sắp xếp, về thứ tự gốc.
import { useCallback, useMemo, useState } from 'react'

import { sortRowsBy, type SortValue } from '@/shared/utils/compare-sort-values'

export interface ClientTableSort<T> {
  /** Dòng đã xếp (hoặc nguyên thứ tự gốc khi chưa bấm cột nào); `undefined` giữ nguyên `undefined` của đầu vào. */
  rows: T[] | undefined
  sortBy: string
  sortDir: 'asc' | 'desc'
  /** Cắm thẳng vào `onSortChange` của `DataTable`. */
  onSortChange: (sortBy: string, sortDir: 'asc' | 'desc') => void
}

export function useClientTableSort<T>(
  rows: T[] | undefined,
  getValue: (columnKey: string, row: T) => SortValue,
): ClientTableSort<T> {
  const [state, setState] = useState<{ by: string; dir: 'asc' | 'desc' }>({ by: '', dir: 'asc' })
  const onSortChange = useCallback((by: string, dir: 'asc' | 'desc') => {
    setState({ by, dir: by ? dir : 'asc' })
  }, [])
  const sorted = useMemo(() => {
    if (!rows || !state.by) return rows
    return sortRowsBy(rows, (row) => getValue(state.by, row), state.dir)
  }, [rows, state, getValue])
  return { rows: sorted, sortBy: state.by, sortDir: state.dir, onSortChange }
}
