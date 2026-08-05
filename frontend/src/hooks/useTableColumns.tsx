import { useCallback, useMemo, useState } from 'react'
import { useResizableColumns } from './useResizableColumns'

/**
 * Mô tả 1 cột bảng — dùng chung cho mọi bảng danh sách.
 * Khai báo cột 1 lần rồi dựng cả <colgroup>, <thead> và <td> từ đây
 * để ẩn/hiện cột và kéo giãn cột hoạt động đồng bộ.
 */
export type TableColumn<T = any> = {
  key: string                                  // định danh cột (dùng để lưu bề rộng + trạng thái ẩn/hiện)
  label: string                                // nhãn hiển thị trên header
  sort?: string                                // tên field để sắp xếp; bỏ trống = cột không sort được
  width?: number | string                      // bề rộng mặc định (bảng table-layout: fixed)
  align?: 'left' | 'center' | 'right'          // canh lề cho cả header và ô dữ liệu
  fixed?: boolean                              // luôn hiện, không cho ẩn (cột chọn / thao tác)
  defaultHidden?: boolean                      // cột phụ: mặc định ẩn, người dùng tự bật khi cần
  th?: React.CSSProperties                     // style thêm cho <th>
  td?: React.CSSProperties                     // style thêm cho <td>
  cell?: (row: T, index: number) => React.ReactNode   // nội dung ô dữ liệu
}

/** Chưa từng chỉnh (chưa có trong localStorage) → dùng bộ mặc định `defaultHidden` của bảng. */
function loadHidden(key: string, columns: TableColumn<any>[]): string[] {
  try {
    const raw = localStorage.getItem(key)
    if (raw) {
      const arr = JSON.parse(raw)
      if (Array.isArray(arr)) return arr
    }
  } catch { /* bỏ qua */ }
  return defaultHidden(columns)
}

function defaultHidden(columns: TableColumn<any>[]): string[] {
  return columns.filter((c) => c.defaultHidden && !c.fixed).map((c) => c.key)
}

/**
 * Quản lý cột của 1 bảng: bề rộng (kéo giãn) + ẩn/hiện, cùng lưu theo `storeKey`.
 *
 *   const t = useTableColumns('inventory', COLS)
 *   <TableToolbar {...t} onRefresh={load} />
 *   <table><TableHead {...t} sortBy=… onSort=… />…</table>
 */
export function useTableColumns<T = any>(storeKey: string, columns: TableColumn<T>[]) {
  const hideKey = `colhide:${storeKey}`
  const resize = useResizableColumns(`colw:${storeKey}`)
  const [hidden, setHidden] = useState<string[]>(() => loadHidden(hideKey, columns))

  const save = useCallback((next: string[]) => {
    setHidden(next)
    try { localStorage.setItem(hideKey, JSON.stringify(next)) } catch { /* bỏ qua */ }
  }, [hideKey])

  const toggleColumn = useCallback((key: string) => {
    save(hidden.includes(key) ? hidden.filter((k) => k !== key) : [...hidden, key])
  }, [hidden, save])

  const showAllColumns = useCallback(() => save([]), [save])

  // Trả bảng về mặc định: bộ cột mặc định + bỏ mọi bề rộng đã kéo
  const resetTable = useCallback(() => {
    save(defaultHidden(columns))
    resize.resetWidths()
  }, [columns, save, resize])

  // Cột `fixed` luôn hiện dù người dùng có bỏ tick (phòng dữ liệu cũ trong localStorage)
  const visibleColumns = useMemo(
    () => columns.filter((c) => c.fixed || !hidden.includes(c.key)),
    [columns, hidden],
  )

  return {
    columns: visibleColumns,
    allColumns: columns,
    hidden,
    toggleColumn,
    showAllColumns,
    resetTable,
    startResize: resize.startResize,
    thStyle: resize.thStyle,
    colW: resize.colW,
  }
}
