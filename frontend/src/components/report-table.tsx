// Tiện ích + bảng báo cáo gọn dùng chung cho các tab ma trận (Reports + MatrixPivotTab).

export const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
export const pctv = (n: any) => `${Number(n || 0).toLocaleString('vi-VN')}%`

export type Metric = { key: string; label: string; pct?: boolean }
export type SortDir = 'asc' | 'desc'
export const NAME_SORT_KEY = '__name__'   // khoá sort cho cột tên

// Bảng báo cáo: dòng = đối tượng, cột = chỉ số. period='all' đọc r[k]; period='YYYY-MM' đọc r.m[period][k].
// Sort (tuỳ chọn): truyền onSort để bật header bấm được; sort đồng bộ do state nằm ở component cha.
export function ReportTable({ rows, metrics, period, warnMetric, nameLabel, nameMinWidth = 160, sortKey = '', sortDir = 'desc', onSort }:
  { rows: any[]; metrics: Metric[]; period: string; warnMetric?: string; nameLabel: string; nameMinWidth?: number; sortKey?: string; sortDir?: SortDir; onSort?: (key: string) => void }) {
  const val = (r: any, k: string) => (period === 'all' ? (r[k] ?? 0) : (r.m?.[period]?.[k] ?? 0))
  // Cột tên ghim: rộng tối đa nameMinWidth (desktop) NHƯNG chỉ ~45% màn hình trên mobile (chừa chỗ cho cột dữ liệu)
  const nameW = `min(${nameMinWidth}px, 45vw)`

  // Sắp xếp theo cột đang chọn (cột tên = A→Z; chỉ số = theo số)
  let view = rows
  if (sortKey) {
    const mul = sortDir === 'asc' ? 1 : -1
    view = [...rows].sort((a, b) => {
      if (sortKey === NAME_SORT_KEY) return mul * String(a.key).localeCompare(String(b.key), 'vi')
      return mul * (Number(val(a, sortKey)) - Number(val(b, sortKey)))
    })
  }

  // Icon sort: cột nào cũng có icon mờ (báo hiệu bấm được); cột đang sort thì ▲/▼ teal
  const sortIcon = (key: string) => sortKey === key
    ? <i className={`ti ti-arrow-${sortDir === 'asc' ? 'up' : 'down'}`} style={{ fontSize: 13 }} />
    : <i className="ti ti-arrows-sort" style={{ fontSize: 13, opacity: 0.35 }} />
  const thBtn = (key: string, label: string, align: 'left' | 'right') =>
    onSort
      ? <span onClick={() => onSort(key)} title="Bấm để sắp xếp"
          style={{ cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: 3, justifyContent: align === 'right' ? 'flex-end' : 'flex-start', color: sortKey === key ? 'var(--teal)' : 'inherit' }}>{label}{sortIcon(key)}</span>
      : <>{label}</>

  return (
    <div className="items-scroll">
      <table className="items-table" style={{ minWidth: 480 }}>
        <thead><tr>
          <th style={{ width: 40, minWidth: 40, boxSizing: 'border-box', position: 'sticky', left: 0, zIndex: 3, background: '#fff' }}>#</th>
          <th style={{ textAlign: 'left', minWidth: nameW, maxWidth: nameW, width: nameW, boxSizing: 'border-box', position: 'sticky', left: 40, zIndex: 3, background: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{thBtn(NAME_SORT_KEY, nameLabel, 'left')}</th>
          {metrics.map((m) => <th key={m.key} style={{ textAlign: 'right' }}>{thBtn(m.key, m.label, 'right')}</th>)}</tr></thead>
        <tbody>
          {view.map((r, i) => {
            const warn = warnMetric ? Number(val(r, warnMetric)) > 30 : false
            const stickyBg = warn ? '#fdecea' : '#fff'
            return (
              <tr key={i} style={warn ? { background: '#fdecea' } : {}}>
                <td style={{ width: 40, minWidth: 40, boxSizing: 'border-box', position: 'sticky', left: 0, zIndex: 2, background: stickyBg }}>{i + 1}</td>
                <td style={{ textAlign: 'left', fontWeight: 500, minWidth: nameW, maxWidth: nameW, width: nameW, boxSizing: 'border-box', position: 'sticky', left: 40, zIndex: 2, background: stickyBg, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.key}</td>
                {metrics.map((m) => (
                  <td key={m.key} style={{ textAlign: 'right', fontWeight: m.key === warnMetric ? 600 : 400, color: (m.key === warnMetric && warn) ? 'var(--red)' : 'inherit' }}>
                    {m.pct ? pctv(val(r, m.key)) : fmt(val(r, m.key))}
                  </td>
                ))}
              </tr>
            )
          })}
          {view.length === 0 && <tr><td colSpan={2 + metrics.length} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Không có dữ liệu</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
