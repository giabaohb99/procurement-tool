// duoc-CR-490 — bảng phạm vi sử dụng có thể SỬA, dùng trong hộp thêm/sửa thuốc BVTV
// (`CustomsPesticideForm.tsx`). Thêm/xóa dòng tự do, không giới hạn số dòng trên màn (backend
// chặn ở 500 dòng/thuốc — `MAX_USES_PER_RECORD`).
import { PESTICIDE_USE_FIELD_LIMITS, PesticideUseForm } from '../../utils/customs-pesticide'

const SHORT_COLS: { key: 'crop' | 'pest' | 'dosage' | 'pre_harvest_interval'; label: string; width: number }[] = [
  { key: 'crop', label: 'Cây trồng', width: 150 },
  { key: 'pest', label: 'Dịch hại', width: 170 },
  { key: 'dosage', label: 'Liều lượng', width: 150 },
  { key: 'pre_harvest_interval', label: 'Thời gian cách ly', width: 140 },
]

export default function CustomsPesticideUsesEditor({ rows, onChange }: {
  rows: PesticideUseForm[]
  onChange: (rows: PesticideUseForm[]) => void
}) {
  function set(i: number, patch: Partial<PesticideUseForm>) {
    onChange(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)))
  }
  function add() {
    onChange([...rows, { crop: '', pest: '', dosage: '', pre_harvest_interval: '', usage: '' }])
  }
  function remove(i: number) {
    onChange(rows.filter((_, idx) => idx !== i))
  }
  // Hộp thêm/sửa không nằm trong <form> (CustomsModal dùng <div>) nên Enter không tự nộp gì —
  // vẫn chặn cho chắc, phòng khi khung hộp thoại đổi sang <form> về sau.
  const stopEnter = (e: React.KeyboardEvent) => { if (e.key === 'Enter') e.preventDefault() }

  return (
    <div>
      <div className="table-scroll">
        <table>
          <thead><tr>
            {SHORT_COLS.map((c) => <th key={c.key} style={{ width: c.width }}>{c.label}</th>)}
            <th>Cách dùng</th>
            <th style={{ width: 40 }} />
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {SHORT_COLS.map((c) => (
                  <td key={c.key}>
                    <input value={r[c.key]} maxLength={PESTICIDE_USE_FIELD_LIMITS[c.key]} onKeyDown={stopEnter}
                      onChange={(e) => set(i, { [c.key]: e.target.value } as Partial<PesticideUseForm>)}
                      style={{ width: '100%' }} />
                  </td>
                ))}
                <td>
                  <input value={r.usage} maxLength={20000} onKeyDown={stopEnter}
                    onChange={(e) => set(i, { usage: e.target.value })} style={{ width: '100%' }} />
                </td>
                <td style={{ textAlign: 'center' }}>
                  <button type="button" className="icon-btn" title="Xóa dòng" onClick={() => remove(i)}>
                    <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={SHORT_COLS.length + 2} className="table-empty">Chưa có dòng phạm vi sử dụng nào.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <button type="button" className="btn ghost" style={{ marginTop: 8 }} onClick={add}>
        <i className="ti ti-plus" />Thêm dòng
      </button>
    </div>
  )
}
