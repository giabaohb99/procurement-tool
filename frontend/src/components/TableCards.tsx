import type { MouseEvent, ReactNode } from 'react'
import type { CardSlot, TableColumn } from '../hooks/useTableColumns'
import './table-cards.css'

/** Một lựa chọn trong thanh sắp xếp của màn thẻ (`key` = khóa `sort_by` máy chủ nhận). */
export type CardSortOption = { key: string; label: ReactNode }

/**
 * Thanh sắp xếp của màn thẻ: trên điện thoại không có tiêu đề cột để bấm, nên chọn cột ở ô chọn + nút đảo chiều.
 * Dùng chung cho `TableCards` và thẻ tự dựng (Giá mua gần nhất). `onSort(key)` giữ đúng ngữ nghĩa bấm tiêu đề của bảng:
 * cùng cột thì đảo chiều, cột mới thì chiều đầu theo kiểu cột — nên nút đảo chiều gọi lại đúng cột đang xếp.
 */
export function CardSortBar({ options, sortBy, sortDir, onSort }: {
  options: CardSortOption[]
  sortBy?: string | null
  sortDir?: 'asc' | 'desc'
  onSort?: (key: string) => void
}) {
  if (!onSort || options.length === 0) return null
  const active = options.some((o) => o.key === sortBy) ? sortBy! : ''
  return (
    <div className="tcards-sort">
      <label>
        <span>Xếp theo</span>
        <select aria-label="Xếp theo cột" value={active} onChange={(e) => { if (e.target.value && e.target.value !== sortBy) onSort(e.target.value) }}>
          <option value="">— Mặc định —</option>
          {options.map((o) => <option key={o.key} value={o.key}>{typeof o.label === 'string' ? o.label : o.key}</option>)}
        </select>
      </label>
      <button type="button" className="btn ghost sm" disabled={!active} onClick={() => active && onSort(active)}
        title={sortDir === 'desc' ? 'Đang giảm dần — bấm để tăng dần' : 'Đang tăng dần — bấm để giảm dần'}>
        <i className={'ti ' + (active ? (sortDir === 'desc' ? 'ti-sort-descending' : 'ti-sort-ascending') : 'ti-arrows-sort')} />
        {active ? (sortDir === 'desc' ? 'Giảm dần' : 'Tăng dần') : 'Chiều'}
      </button>
    </div>
  )
}

/** Ô rỗng ("", null, false) hiện gạch mờ thay vì để trống — thẻ không có ô để biết "chưa có" hay "lỗi hiển thị". */
function filled(node: ReactNode): ReactNode {
  return node === '' || node === null || node === undefined || node === false ? <span className="pkg-muted">—</span> : node
}

function pick<T>(columns: TableColumn<T>[], slot: CardSlot) {
  return columns.filter((c) => (c.card ?? 'field') === slot)
}

/**
 * Bảng hiện dạng THẺ trên màn hẹp (≤ 820px, chọn bằng `useNarrowScreen`): mỗi dòng một thẻ dọc. Dựng từ CHÍNH danh sách cột
 * của bảng (`table.columns` — đã áp ẩn / hiện cột) nên nhãn, ô, màu tăng xanh giảm đỏ y hệt bảng; chỗ đặt mỗi cột do
 * `column.card` quyết định (xem `CardSlot`). Phân trang / chip lọc / thanh công cụ vẫn là của trang, đứng ngoài thẻ.
 */
export default function TableCards<T>({
  columns, rows, rowKey, empty, sortBy, sortDir, onSort, onRowClick, onRowAuxClick, rowClassName,
}: {
  columns: TableColumn<T>[]
  rows: T[]
  rowKey: (row: T, index: number) => string | number
  /** Nội dung khi không có dòng (cùng câu với ô rỗng của bảng). */
  empty: ReactNode
  sortBy?: string | null
  sortDir?: 'asc' | 'desc'
  onSort?: (key: string) => void
  onRowClick?: (e: MouseEvent, row: T) => void
  onRowAuxClick?: (e: MouseEvent, row: T) => void
  rowClassName?: (row: T) => string | undefined
}) {
  const sortOptions = columns.filter((c) => c.sort).map((c) => ({ key: c.sort!, label: c.label }))
  const titles = pick(columns, 'title')
  const subtitles = pick(columns, 'subtitle')
  const heroes = pick(columns, 'hero')
  const fields = pick(columns, 'field')
  const fulls = pick(columns, 'full')
  const parts = pick(columns, 'part')
  const corners = pick(columns, 'corner')
  const actions = pick(columns, 'action')
  const labelOf = (c: TableColumn<T>) => (typeof c.label === 'string' ? c.label : c.key)

  return (
    <div className="tcards-wrap">
      <CardSortBar options={sortOptions} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
      {rows.length === 0 && <div className="tcards-empty">{empty}</div>}
      <ul className="tcards">
        {rows.map((row, i) => (
          <li key={rowKey(row, i)}
            className={'tcard' + (onRowClick ? ' clickable' : '') + (rowClassName?.(row) ? ` ${rowClassName(row)}` : '')}
            onClick={onRowClick ? (e) => onRowClick(e, row) : undefined}
            onAuxClick={onRowAuxClick ? (e) => onRowAuxClick(e, row) : undefined}>
            {(titles.length > 0 || corners.length > 0) && (
              <div className="tcard-head">
                <div className="tcard-title">{titles.map((c) => <span key={c.key}>{filled(c.cell?.(row, i) ?? (row as any)[c.key])}</span>)}</div>
                {corners.map((c) => <div key={c.key} className="tcard-corner">{c.cell?.(row, i)}</div>)}
              </div>
            )}
            {subtitles.map((c) => <div key={c.key} className="tcard-sub">{filled(c.cell?.(row, i) ?? (row as any)[c.key])}</div>)}
            {heroes.length > 0 && (
              <div className="tcard-heroes" style={{ gridTemplateColumns: `repeat(${heroes.length === 1 ? 1 : heroes.length === 3 ? 3 : 2}, minmax(0, 1fr))` }}>
                {heroes.map((c) => (
                  <div key={c.key} className="tcard-hero">
                    <span className="tcard-k">{labelOf(c)}</span>
                    <span className="tcard-v">{filled(c.cell?.(row, i) ?? (row as any)[c.key])}</span>
                  </div>
                ))}
              </div>
            )}
            {fields.length > 0 && (
              <dl className="tcard-grid">
                {fields.map((c) => (
                  <div key={c.key} className="tcard-f">
                    <dt>{labelOf(c)}</dt>
                    <dd>{filled(c.cell?.(row, i) ?? (row as any)[c.key])}</dd>
                  </div>
                ))}
              </dl>
            )}
            {fulls.map((c) => {
              //  Ô `full` (ghi chú, ô nhập) rỗng thì ẩn cả nhãn — không có gì để đọc, khác ô lưới cần gạch "—" giữ chỗ.
              const content = c.cell ? c.cell(row, i) : (row as any)[c.key]
              if (content === '' || content === null || content === undefined || content === false) return null
              return (
                <div key={c.key} className="tcard-full">
                  <span className="tcard-k">{labelOf(c)}</span>
                  <div>{content}</div>
                </div>
              )
            })}
            {parts.length > 0 && (
              <div className="tcard-parts">
                {parts.map((c) => (
                  <div key={c.key} className="tcard-part">
                    <span className="tcard-k">{labelOf(c)}</span>
                    <div>{filled(c.cell?.(row, i) ?? (row as any)[c.key])}</div>
                  </div>
                ))}
              </div>
            )}
            {actions.length > 0 && (
              <div className="tcard-actions">{actions.map((c) => <span key={c.key}>{c.cell?.(row, i)}</span>)}</div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
