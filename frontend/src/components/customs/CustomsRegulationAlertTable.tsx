// duoc-CR-490 — bảng cảnh báo pháp lý theo từ khóa dòng hàng đang tra (mục «Tra cứu hóa chất»).
// duoc-CR-598 (07/10/2026): đồng bộ cột với bản v2 — phần chung (STT · Phụ lục · Tên khoa học · Tên chất ·
// CAS · Công thức · Ngưỡng) + «Lưu ý». Trước đây còn 5 cột cũ (Danh mục · Tên · Số CAS · Ngưỡng · Lưu ý),
// thiếu ngưỡng hỗn hợp % của phụ lục II / III.
import { sortRegulationsBySeverity } from '../../utils/customs-regulation'
import { RegulationCommonCells, RegulationCommonHeaders } from './CustomsRegulationColumns'

export default function CustomsRegulationAlertTable({ items }: { items: any[] }) {
  const rows = sortRegulationsBySeverity(items)
  return (
    <div className="table-scroll"><table>
      <thead><tr><RegulationCommonHeaders /><th>Lưu ý</th></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}>
            <RegulationCommonCells r={r} />
            <td style={{ fontSize: 13 }}>{r.obligation}</td>
          </tr>
        ))}
      </tbody>
    </table></div>
  )
}
