import { CONTRACT_TYPE_INDEFINITE } from './labor-contract-rules'

/**
 * Nút chọn nhanh thời hạn ở hộp lập/sửa HĐLĐ — bấm là điền sẵn ngày kết thúc từ ngày bắt đầu.
 *
 * Sinh ra sau đợt bấm thử 06/10/2026: lịch chọn ngày chỉ có nút «tháng sau», HĐ 3 năm phải bấm 36
 * lần. Không sửa ô chọn ngày dùng chung của cả app — gói gọn trong form hợp đồng.
 *
 * Cách tính PHẢI khớp backend (`context_builder.describe_duration` + `rules.duration_warnings`):
 * ngày kết thúc = ngày bắt đầu + N tháng − 1 ngày, tháng đích ngắn hơn thì kẹp về cuối tháng
 * (giống `_add_months`). Nhờ vậy «12 tháng» in ra file đúng «12 tháng», và «36 tháng» không tự kích
 * cảnh báo «quá 36 tháng».
 */

export type TermPreset = { label: string; months: number } | { label: string; days: number }

/** Khớp `LaborContractType`: 1 Thử việc · 2 Xác định thời hạn. */
const PROBATION = 1
const FIXED_TERM = 2

const PRESETS_BY_TYPE: Record<number, TermPreset[]> = {
  //  Thử việc tính theo NGÀY (BLLĐ 2019 Điều 25: tối đa 60 ngày với việc cần cao đẳng trở lên,
  //  30 ngày với trung cấp). «2 tháng» có khi ra 61–62 ngày, vượt trần — nên không dùng tháng.
  [PROBATION]: [
    { label: '30 ngày', days: 30 },
    { label: '60 ngày', days: 60 },
  ],
  [FIXED_TERM]: [
    { label: '12 tháng', months: 12 },
    { label: '24 tháng', months: 24 },
    { label: '36 tháng', months: 36 },
  ],
}

/** Khoán việc, cộng tác viên, khác: hợp đồng ngắn hạn. */
const SHORT_TERM_PRESETS: TermPreset[] = [
  { label: '3 tháng', months: 3 },
  { label: '6 tháng', months: 6 },
  { label: '12 tháng', months: 12 },
]

/** Nút cho loại HĐ này; rỗng khi chưa chọn loại hoặc loại không có ngày kết thúc. */
export function termPresetsFor(contractType: number): TermPreset[] {
  if (!contractType || contractType === CONTRACT_TYPE_INDEFINITE) return []
  return PRESETS_BY_TYPE[contractType] ?? SHORT_TERM_PRESETS
}

/** `yyyy-mm-dd` → [năm, tháng 1-12, ngày]; sai dạng hoặc ngày không có thật → `null`. */
function parseIsoDate(value: string): [number, number, number] | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return null
  const [y, m, d] = [Number(match[1]), Number(match[2]), Number(match[3])]
  const probe = new Date(Date.UTC(y, m - 1, d))
  //  Date tự «tràn» 31/02 → 03/03; so lại để loại ngày không tồn tại.
  if (probe.getUTCFullYear() !== y || probe.getUTCMonth() !== m - 1 || probe.getUTCDate() !== d) return null
  return [y, m, d]
}

/** Tính theo UTC từ đầu đến cuối: chỉ có ngày, không có giờ, nên không lệch múi giờ. */
function toIso(date: Date): string {
  return date.toISOString().slice(0, 10)
}

/**
 * Ngày kết thúc của preset tính từ `startDate` (`yyyy-mm-dd`). Ngày bắt đầu trống/sai → `''`.
 * - theo tháng: + N tháng (kẹp cuối tháng) − 1 ngày — 01/11/2026 + 12 tháng → 31/10/2027;
 * - theo ngày: tính CẢ ngày bắt đầu — 01/11/2026 + 30 ngày → 30/11/2026.
 */
export function endDateForPreset(startDate: string, preset: TermPreset): string {
  const parts = parseIsoDate(startDate)
  if (!parts) return ''
  const [y, m, d] = parts
  if ('days' in preset) return toIso(new Date(Date.UTC(y, m - 1, d + preset.days - 1)))
  const totalMonths = m - 1 + preset.months
  const targetYear = y + Math.floor(totalMonths / 12)
  const targetMonth = totalMonths % 12
  //  Ngày 0 của tháng SAU = ngày cuối của tháng đích.
  const lastDayOfTarget = new Date(Date.UTC(targetYear, targetMonth + 1, 0)).getUTCDate()
  const anchor = new Date(Date.UTC(targetYear, targetMonth, Math.min(d, lastDayOfTarget)))
  anchor.setUTCDate(anchor.getUTCDate() - 1)
  return toIso(anchor)
}
