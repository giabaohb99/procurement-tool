// duoc-CR-490 — bảng 5 cột của dải cảnh báo pháp lý theo từ khóa dòng hàng đang tra (thẻ «Pháp lý»,
// và trước đây thẻ «Pháp lý & thuế»). Bảng DUYỆT cả danh mục (`CustomsRegulationBrowse.tsx`) có
// thêm cột «Thuốc BVTV chứa» nên KHÔNG dùng chung tệp này.
import {
  formatBannedLabel, formatThresholdKg, regulationBadgeClass, sortRegulationsBySeverity,
} from '../../utils/customs-regulation'

export default function CustomsRegulationAlertTable({ items }: { items: any[] }) {
  const rows = sortRegulationsBySeverity(items)
  return (
    <div className="table-scroll"><table>
      <thead><tr><th>Danh mục</th><th>Tên</th><th>Số CAS</th><th>Ngưỡng / Mức cấm</th><th>Lưu ý</th></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}>
            <td style={{ whiteSpace: 'nowrap' }}>
              <span className={`badge ${regulationBadgeClass(r.list_code)}`}>{r.list_label}</span>
            </td>
            <td>{r.name}{r.name_vi && r.name_vi !== r.name ? <div style={{ fontSize: 12, color: 'var(--muted)' }}>{r.name_vi}</div> : null}</td>
            <td>{r.cas_no || '—'}</td>
            <td style={{ whiteSpace: 'nowrap' }}>
              {r.list_code === 10
                ? <span className="badge err" style={{ fontWeight: 700 }}>{formatBannedLabel(r.banned_year)}</span>
                : formatThresholdKg(r.threshold_kg)
                  ? <span style={{ fontSize: 15, fontWeight: 700, color: '#c2410c', fontVariantNumeric: 'tabular-nums' }}>{formatThresholdKg(r.threshold_kg)}</span>
                  : null}
            </td>
            <td style={{ fontSize: 13 }}>{r.obligation}</td>
          </tr>
        ))}
      </tbody>
    </table></div>
  )
}
