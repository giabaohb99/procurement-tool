import { useCallback, useMemo, useState } from 'react'

import { sortRowsBy, type SortDir, type SortValue } from '@/shared/utils/compare-sort-values'

interface LinesSortState {
  key: string
  dir: SortDir
  /** Thứ tự khóa dòng CHỐT lúc bấm tiêu đề — xem chú thích của `useLinesTableSort`. */
  order: (string | number)[]
}

interface UseLinesTableSortOptions<T> {
  rows: T[]
  rowKey: (row: T, index: number) => string | number
  getSortValue: (columnKey: string, row: T, index: number) => SortValue
}

/**
 * Sắp xếp bảng DÒNG CHỨNG TỪ ngay trên trình duyệt (duoc-CR-744) — bảng dòng nạp
 * đủ mọi dòng của phiếu nên không cần hỏi server.
 *
 * ⚠️ Thứ tự được CHỐT lúc bấm tiêu đề, không tính lại mỗi lần dữ liệu đổi. Bảng
 * dòng là bảng SỬA ĐƯỢC: tính lại liên tục thì gõ một chữ vào ô đang xếp là dòng
 * nhảy sang chỗ khác ngay dưới tay người gõ. Dòng thêm sau khi chốt nối vào cuối;
 * dòng đã xóa thì tự rơi khỏi danh sách.
 *
 * `displayRows` giữ CHỈ SỐ GỐC của từng dòng: `renderCell`, tick chọn, xóa dòng…
 * ở mọi bảng đều làm việc theo chỉ số trong mảng gốc, đưa chỉ số sau khi xếp vào
 * là sửa nhầm dòng.
 */
export function useLinesTableSort<T>({ rows, rowKey, getSortValue }: UseLinesTableSortOptions<T>) {
  const [sort, setSort] = useState<LinesSortState | null>(null)

  const toggleSort = useCallback(
    (key: string, descFirst = false) => {
      const firstDir: SortDir = descFirst ? 'desc' : 'asc'
      const secondDir: SortDir = descFirst ? 'asc' : 'desc'
      //  Ba nhịp như `DataTable`: nhịp đầu → nhịp hai → THÔI SẮP XẾP.
      let dir: SortDir | null = firstDir
      if (sort?.key === key) dir = sort.dir === firstDir ? secondDir : null
      if (!dir) {
        setSort(null)
        return
      }
      const nextDir = dir
      //  Bằng nhau thì giữ thứ tự gốc (`sortRowsBy` xếp ổn định), kẻo hai dòng cùng giá trị đổi chỗ
      //  qua lại mỗi lần bấm. Xếp trên cặp {khóa dòng, giá trị} rồi chỉ giữ khóa.
      const order = sortRowsBy(
        rows.map((row, index) => ({ key: rowKey(row, index), value: getSortValue(key, row, index) })),
        (item) => item.value,
        nextDir,
      ).map((item) => item.key)
      setSort({ key, dir: nextDir, order })
    },
    [rows, rowKey, getSortValue, sort],
  )

  const displayRows = useMemo(() => {
    const indexed = rows.map((row, index) => ({ row, index }))
    if (!sort) return indexed
    const position = new Map(sort.order.map((key, i) => [key, i]))
    const placed = indexed.filter((item) => position.has(rowKey(item.row, item.index)))
    const added = indexed.filter((item) => !position.has(rowKey(item.row, item.index)))
    placed.sort(
      (a, b) =>
        (position.get(rowKey(a.row, a.index)) ?? 0) - (position.get(rowKey(b.row, b.index)) ?? 0),
    )
    return [...placed, ...added]
  }, [rows, rowKey, sort])

  return { sortKey: sort?.key ?? null, sortDir: sort?.dir ?? null, toggleSort, displayRows }
}
