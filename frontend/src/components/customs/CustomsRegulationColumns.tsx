// duoc-CR-598 (07/10/2026) — các cột DÙNG CHUNG của bảng hóa chất theo văn bản ở bản cũ, khớp đúng
// thứ tự bản v2 (`frontend-v2/.../config/customs-regulation-columns.tsx`):
//   STT · Phụ lục / Văn bản · Tên khoa học · Tên chất · Mã số CAS · Công thức hóa học · Ngưỡng / Mức cấm
// Bảng duyệt (`CustomsRegulationBrowse`) thêm «Thuốc BVTV chứa» rồi «Lưu ý»; bảng cảnh báo theo từ khóa
// (`CustomsRegulationAlertTable`) thêm «Lưu ý». Gom về một chỗ vì hai bảng từng lệch nhau (bảng cảnh
// báo còn 5 cột cũ trong khi bảng duyệt đã đổi) — đại ca bắt được ngày 07/10/2026.
// duoc-CR-609 (07/10/2026): khai thành MẢNG CỘT có khóa (`TableColumn`) để bảng duyệt ẩn / hiện được
// từng cột qua nút «Cột»; hai component Headers / Cells bên dưới vẫn dựng từ chính mảng này.
import type { TableColumn } from '../../hooks/useTableColumns'
import {
  describeMissingLimit, formatBannedLabel, formatMixtureLimit, formatThresholdKg, regulationBadgeClass,
} from '../../utils/customs-regulation'

/** Bảy cột chung — khóa cột là khóa lưu ẩn / hiện trong localStorage, đổi là mất lựa chọn đã lưu. */
export const REGULATION_COMMON_COLUMNS: TableColumn[] = [
  {
    key: 'seq_no', label: 'STT', align: 'center',
    th: { width: 56 }, td: { fontVariantNumeric: 'tabular-nums' },
    cell: (r) => r.seq_no,
  },
  {
    key: 'list_label', label: 'Phụ lục / Văn bản', td: { whiteSpace: 'nowrap' },
    cell: (r) => <span className={`badge ${regulationBadgeClass(r.list_code)}`}>{r.list_label}</span>,
  },
  { key: 'name', label: 'Tên khoa học', cell: (r) => r.name },
  { key: 'name_vi', label: 'Tên chất', cell: (r) => r.name_vi },
  { key: 'cas_no', label: 'Mã số CAS', td: { whiteSpace: 'nowrap' }, cell: (r) => r.cas_no || '—' },
  { key: 'formula', label: 'Công thức hóa học', cell: (r) => r.formula },
  { key: 'limit', label: 'Ngưỡng / Mức cấm', td: { minWidth: 150 }, cell: (r) => <LimitCell r={r} /> },
]

/** Số cột của phần dùng chung — để bảng tính `colSpan` dòng rỗng. */
export const REGULATION_COMMON_COLUMN_COUNT = REGULATION_COMMON_COLUMNS.length

/** Dựng `<th>` cho một danh sách cột (dùng cho cả phần chung lẫn cột riêng của từng bảng). */
export function RegulationHeaderCells({ columns }: { columns: TableColumn[] }) {
  return (
    <>
      {columns.map((c) => (
        <th key={c.key} style={{ textAlign: c.align, ...c.th }}>{c.label}</th>
      ))}
    </>
  )
}

/** Dựng `<td>` của một dòng theo danh sách cột. */
export function RegulationRowCells({ columns, r, index = 0 }: { columns: TableColumn[]; r: any; index?: number }) {
  return (
    <>
      {columns.map((c) => (
        <td key={c.key} style={{ textAlign: c.align, ...c.td }}>{c.cell?.(r, index)}</td>
      ))}
    </>
  )
}

export function RegulationCommonHeaders() {
  return <RegulationHeaderCells columns={REGULATION_COMMON_COLUMNS} />
}

export function RegulationCommonCells({ r }: { r: any }) {
  return <RegulationRowCells columns={REGULATION_COMMON_COLUMNS} r={r} />
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
