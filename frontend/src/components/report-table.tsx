// Tiện ích + bảng báo cáo gọn dùng chung cho các tab ma trận (Reports + MatrixPivotTab).

export const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
export const pctv = (n: any) => `${Number(n || 0).toLocaleString('vi-VN')}%`

export type Metric = { key: string; label: string; pct?: boolean }

// Bảng báo cáo: dòng = đối tượng, cột = chỉ số. period='all' đọc r[k]; period='YYYY-MM' đọc r.m[period][k].
export function ReportTable({ rows, metrics, period, warnMetric, nameLabel, nameMinWidth = 160 }:
  { rows: any[]; metrics: Metric[]; period: string; warnMetric?: string; nameLabel: string; nameMinWidth?: number }) {
  const val = (r: any, k: string) => (period === 'all' ? (r[k] ?? 0) : (r.m?.[period]?.[k] ?? 0))
  return (
    <div className="items-scroll">
      <table className="items-table" style={{ minWidth: 480 }}>
        <thead><tr><th style={{ width: 40 }}>#</th><th style={{ textAlign: 'left', minWidth: nameMinWidth }}>{nameLabel}</th>
          {metrics.map((m) => <th key={m.key} style={{ textAlign: 'right' }}>{m.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => {
            const warn = warnMetric ? Number(val(r, warnMetric)) > 30 : false
            return (
              <tr key={i} style={warn ? { background: '#fdecea' } : {}}>
                <td>{i + 1}</td><td style={{ textAlign: 'left', fontWeight: 500 }}>{r.key}</td>
                {metrics.map((m) => (
                  <td key={m.key} style={{ textAlign: 'right', fontWeight: m.key === warnMetric ? 600 : 400, color: (m.key === warnMetric && warn) ? 'var(--red)' : 'inherit' }}>
                    {m.pct ? pctv(val(r, m.key)) : fmt(val(r, m.key))}
                  </td>
                ))}
              </tr>
            )
          })}
          {rows.length === 0 && <tr><td colSpan={2 + metrics.length} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Không có dữ liệu</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
