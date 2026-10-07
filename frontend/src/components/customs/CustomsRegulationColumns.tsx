// duoc-CR-598 (07/10/2026) — các cột DÙNG CHUNG của bảng hóa chất theo văn bản ở bản cũ, khớp đúng
// thứ tự bản v2 (`frontend-v2/.../config/customs-regulation-columns.tsx`):
//   STT · Phụ lục / Văn bản · Tên khoa học · Tên chất · Mã số CAS · Công thức hóa học · Ngưỡng / Mức cấm
// Bảng duyệt (`CustomsRegulationBrowse`) thêm «Thuốc BVTV chứa» rồi «Lưu ý»; bảng cảnh báo theo từ khóa
// (`CustomsRegulationAlertTable`) thêm «Lưu ý». Gom về một chỗ vì hai bảng từng lệch nhau (bảng cảnh
// báo còn 5 cột cũ trong khi bảng duyệt đã đổi) — đại ca bắt được ngày 07/10/2026.
import {
  describeMissingLimit, formatBannedLabel, formatMixtureLimit, formatThresholdKg, regulationBadgeClass,
} from '../../utils/customs-regulation'

/** Số cột của phần dùng chung — để bảng tính `colSpan` dòng rỗng. */
export const REGULATION_COMMON_COLUMN_COUNT = 7

export function RegulationCommonHeaders() {
  return (
    <>
      <th style={{ textAlign: 'center', width: 56 }}>STT</th>
      <th>Phụ lục / Văn bản</th>
      <th>Tên khoa học</th>
      <th>Tên chất</th>
      <th>Mã số CAS</th>
      <th>Công thức hóa học</th>
      <th>Ngưỡng / Mức cấm</th>
    </>
  )
}

/** Ô «Ngưỡng / Mức cấm»: cấm (đỏ) > tồn trữ kg (cam đậm) > hàm lượng hỗn hợp (chữ thường) > không có. */
function LimitCell({ r }: { r: any }) {
  if (r.list_code === 10) {
    return <span className="badge err" style={{ fontWeight: 700 }}>{formatBannedLabel(r.banned_year)}</span>
  }
  const kg = formatThresholdKg(r.threshold_kg)
  if (kg) {
    return <span style={{ fontSize: 15, fontWeight: 700, color: '#c2410c', fontVariantNumeric: 'tabular-nums' }}>{kg}</span>
  }
  const mixture = formatMixtureLimit(r.mixture_pct)
  if (mixture) {
    return (
      <span style={{ fontVariantNumeric: 'tabular-nums' }}
        title="Hỗn hợp chứa chất này với hàm lượng vượt mức này (theo khối lượng) cũng thuộc danh mục">
        {mixture}
      </span>
    )
  }
  const note = describeMissingLimit(r.list_code)
  return note ? <span style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' }}>{note}</span> : null
}

export function RegulationCommonCells({ r }: { r: any }) {
  return (
    <>
      <td style={{ textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>{r.seq_no}</td>
      <td style={{ whiteSpace: 'nowrap' }}>
        <span className={`badge ${regulationBadgeClass(r.list_code)}`}>{r.list_label}</span>
      </td>
      <td>{r.name}</td>
      <td>{r.name_vi}</td>
      <td style={{ whiteSpace: 'nowrap' }}>{r.cas_no || '—'}</td>
      <td>{r.formula}</td>
      <td style={{ minWidth: 150 }}><LimitCell r={r} /></td>
    </>
  )
}
