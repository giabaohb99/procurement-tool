import { TableColumn } from '../hooks/useTableColumns'
import { ResizeHandle } from '../hooks/useResizableColumns'

type HeadProps = {
  columns: TableColumn[]
  sortBy?: string | null
  sortDir?: 'asc' | 'desc'
  onSort?: (field: string) => void
  startResize: (id: string | number, e: React.MouseEvent) => void
  /** Chỉ truyền cho bảng table-layout auto. Bảng fixed lấy bề rộng từ <TableColGroup>. */
  thStyle?: (id: string | number) => React.CSSProperties | undefined
}

/**
 * <thead> dùng chung: nhãn + mũi tên sắp xếp + tay nắm kéo giãn, style thống nhất mọi bảng.
 */
export default function TableHead({ columns, sortBy, sortDir = 'asc', onSort, startResize, thStyle }: HeadProps) {
  return (
    <thead>
      <tr>
        {columns.map((c) => {
          const sortable = !!c.sort && !!onSort
          const active = sortable && sortBy === c.sort
          const icon = active ? (sortDir === 'asc' ? 'ti-chevron-up' : 'ti-chevron-down') : 'ti-arrows-sort'
          return (
            <th
              key={c.key}
              className={'th-resizable' + (sortable ? ' th-sortable' : '')}
              style={{ textAlign: c.align || 'left', ...(c.th || {}), ...(thStyle?.(c.key) || {}) }}
              onClick={sortable ? () => onSort!(c.sort!) : undefined}
              title={sortable ? 'Bấm để sắp xếp' : undefined}
            >
              <span className="th-inner">
                <span className="th-label">{c.label}</span>
                {sortable && <i className={`ti ${icon} th-sort-ico${active ? ' active' : ''}`} />}
              </span>
              <ResizeHandle onMouseDown={(e) => startResize(c.key, e)} />
            </th>
          )
        })}
      </tr>
    </thead>
  )
}

/** <colgroup> cho bảng table-layout: fixed — khóa bề rộng để sort/đổi trang không làm giật bảng. */
export function TableColGroup({ columns, colW }: {
  columns: TableColumn[]
  colW: (id: string | number, def: number | string) => number | string
}) {
  return (
    <colgroup>
      {columns.map((c) => <col key={c.key} style={{ width: colW(c.key, c.width || 'auto') }} />)}
    </colgroup>
  )
}

/** Các ô dữ liệu của 1 dòng, dựng theo đúng danh sách cột đang hiện. */
export function TableCells<T>({ columns, row, index }: { columns: TableColumn<T>[]; row: T; index: number }) {
  return (
    <>
      {columns.map((c) => (
        <td key={c.key} style={{ textAlign: c.align || 'left', ...(c.td || {}) }}>
          {c.cell ? c.cell(row, index) : (row as any)[c.key] ?? ''}
        </td>
      ))}
    </>
  )
}
