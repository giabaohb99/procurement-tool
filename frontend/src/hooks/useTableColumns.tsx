import { useCallback, useMemo, useState } from 'react'
import { useResizableColumns } from './useResizableColumns'

/**
 * Mô tả 1 cột bảng — dùng chung cho mọi bảng danh sách.
 * Khai báo cột 1 lần rồi dựng cả <colgroup>, <thead> và <td> từ đây
 * để ẩn/hiện cột và kéo giãn cột hoạt động đồng bộ.
 */
export type TableColumn<T = any> = {
  key: string                                  // định danh cột (dùng để lưu bề rộng + trạng thái ẩn/hiện)
  label: React.ReactNode                       // nhãn header (thường là chuỗi; cột tick chọn đặt ô checkbox)
  sort?: string                                // tên field để sắp xếp; bỏ trống = cột không sort được
  width?: number | string                      // bề rộng mặc định (bảng table-layout: fixed)
  align?: 'left' | 'center' | 'right'          // canh lề cho cả header và ô dữ liệu
  fixed?: boolean                              // luôn hiện, không cho ẩn (cột chọn / thao tác)
  defaultHidden?: boolean                      // cột phụ: mặc định ẩn, người dùng tự bật khi cần
  hiddenForOlderLayouts?: boolean              // bao-CR-705: cột ẩn sẵn thêm SAU — người đã lưu ẩn/hiện từ trước cũng thấy nó ẩn
  th?: React.CSSProperties                     // style thêm cho <th>
  td?: React.CSSProperties                     // style thêm cho <td>
  cell?: (row: T, index: number) => React.ReactNode   // nội dung ô dữ liệu
}

/** Chưa từng chỉnh (chưa có trong localStorage) → dùng bộ mặc định `defaultHidden` của bảng.
 *
 *  bao-CR-705: đã từng chỉnh thì bản lưu thắng, NHƯNG cột mới thêm sau mà khai `defaultHidden` vẫn
 *  vào ẩn — trước đây nó bật sẵn trước mặt mọi người đã lưu, làm vỡ bảng đang quen. "Mới" = không
 *  có trong `colknown:` (ghi kèm từ CR-705); bản lưu cũ chưa có `colknown:` thì chỉ áp cho cột khai
 *  `hiddenForOlderLayouts`. */
function loadHidden(key: string, knownKey: string, columns: TableColumn<any>[]): string[] {
  try {
    const raw = localStorage.getItem(key)
    if (raw) {
      const arr = JSON.parse(raw)
      if (Array.isArray(arr)) {
        const known = readKnown(knownKey)
        const fresh = columns.filter((c) => c.defaultHidden && !c.fixed && !arr.includes(c.key)
          && (known ? !known.includes(c.key) : !!c.hiddenForOlderLayouts))
        return fresh.length ? [...arr, ...fresh.map((c) => c.key)] : arr
      }
    }
  } catch { /* bỏ qua */ }
  return defaultHidden(columns)
}

function readKnown(knownKey: string): string[] | null {
  try {
    const parsed = JSON.parse(localStorage.getItem(knownKey) || 'null')
    return Array.isArray(parsed) ? parsed : null
  } catch { return null }
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
  const knownKey = `colknown:${storeKey}`
  const resize = useResizableColumns(`colw:${storeKey}`)
  const [hidden, setHidden] = useState<string[]>(() => loadHidden(hideKey, knownKey, columns))

  const save = useCallback((next: string[]) => {
    setHidden(next)
    try {
      localStorage.setItem(hideKey, JSON.stringify(next))
      // bao-CR-705: nhớ mọi cột bảng đang biết (gộp bản cũ) để lần sau nhận ra cột mới thêm
      const known = Array.from(new Set([...(readKnown(knownKey) || []), ...columns.map((c) => c.key)]))
      localStorage.setItem(knownKey, JSON.stringify(known))
    } catch { /* bỏ qua */ }
  }, [hideKey, knownKey, columns])

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
