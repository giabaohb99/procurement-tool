import { toDateInputValue } from '@/shared/utils/format-date'

import {
  isReportPresetKey,
  resolveLocalPresetRange,
  type ReportPresetKey,
} from '../config/report-period-presets'

/**
 * Bộ lọc của báo cáo «Phúc lợi & sự kiện» (H1, duoc-CR-688, khóa 22) — tên tham số khớp
 * `backend/app/modules/employee/benefit_report_inputs.py`. Mọi giá trị nằm trên URL;
 * NGÀY DỊP = `date_to` của kỳ (backend đọc cuối kỳ), giao diện đặt kỳ «Tùy chọn» một ngày.
 */
export const BENEFIT_PARAM = {
  gender: 'gender',
  ageMin: 'age_min',
  ageMax: 'age_max',
  birthMonth: 'birth_month',
  seniorityYears: 'seniority_years',
  childMaxAge: 'child_max_age',
  includeOnLeave: 'include_on_leave',
  amountStaff: 'amount_staff',
  amountManager: 'amount_manager',
  occasionLabel: 'occasion_label',
} as const

/** Ngừng gõ bao lâu thì mới ghi URL (= gọi lại báo cáo) — gõ «500000» không thành 6 lượt gọi. */
export const BENEFIT_INPUT_DEBOUNCE_MS = 400
/** Trần tuổi — khớp `MAX_AGE` backend. */
export const BENEFIT_MAX_AGE = 120
/** Trần độ dài tên dịp — khớp `MAX_LABEL` backend (tiêu đề tệp ký nhận). */
export const BENEFIT_MAX_LABEL = 100
/**
 * Kỳ khi mở trang lần đầu = «Hôm nay» → ngày dịp mặc định là hôm nay (cuối kỳ «Tháng này»
 * thì ra ngày 31 — đọc như một ngày dịp có thật mà không ai chọn).
 */
export const BENEFIT_DEFAULT_PRESET: ReportPresetKey = 'today'
/** Mã giới tính Nữ (`GENDER_FEMALE` backend, cùng mã hồ sơ nhân sự). */
const GENDER_FEMALE = '2'

export type BenefitOccasionPresetId =
  | 'women_0803'
  | 'women_2010'
  | 'children_0106'
  | 'mid_autumn'
  | 'lunar_new_year'
  | 'birthday_month'
  | 'work_anniversary'

export interface BenefitOccasionPreset {
  id: BenefitOccasionPresetId
  /** Chữ trên nút — ngắn. */
  chip: string
  /** Ngày dương lịch cố định (tháng 1–12, ngày) — có thì bấm nút là đặt luôn ngày dịp. */
  fixedDate?: { month: number; day: number }
  gender?: string
  childMaxAge?: number
  /** Lọc người sinh trong THÁNG của ngày dịp. */
  birthMonthOfOccasion?: boolean
  seniorityYears?: number[]
  /** Dùng bộ lọc ngày sinh / người thân → cần `employee_sensitive.read`, thiếu là 403. */
  needsSensitive: boolean
}

/**
 * Bảy dịp có sẵn (phase 15). Trung thu và Tết theo âm lịch, mỗi năm một ngày dương khác —
 * không tự đặt ngày, người lập chọn ở ô «Ngày dịp».
 */
export const BENEFIT_OCCASION_PRESETS: readonly BenefitOccasionPreset[] = [
  { id: 'women_0803', chip: '8/3', fixedDate: { month: 3, day: 8 }, gender: GENDER_FEMALE, needsSensitive: false },
  { id: 'women_2010', chip: '20/10', fixedDate: { month: 10, day: 20 }, gender: GENDER_FEMALE, needsSensitive: false },
  { id: 'children_0106', chip: '1/6', fixedDate: { month: 6, day: 1 }, childMaxAge: 14, needsSensitive: true },
  { id: 'mid_autumn', chip: 'Trung thu', childMaxAge: 15, needsSensitive: true },
  { id: 'lunar_new_year', chip: 'Tết', needsSensitive: false },
  { id: 'birthday_month', chip: 'Sinh nhật tháng', birthMonthOfOccasion: true, needsSensitive: true },
  { id: 'work_anniversary', chip: 'Kỷ niệm năm làm việc', seniorityYears: [1, 3, 5, 10], needsSensitive: false },
]

/** Tên dịp mà nút điền sẵn vào `occasion_label` — thành tiêu đề «DANH SÁCH NHẬN QUÀ …». */
export function buildOccasionLabel(preset: BenefitOccasionPreset, occasionDate: string): string {
  switch (preset.id) {
    case 'women_0803':
      return 'Quốc tế Phụ nữ 8/3'
    case 'women_2010':
      return 'Ngày Phụ nữ Việt Nam 20/10'
    case 'children_0106':
      return 'Quốc tế Thiếu nhi 1/6'
    case 'mid_autumn':
      return 'Tết Trung thu'
    case 'lunar_new_year':
      return 'Tết Nguyên đán'
    case 'birthday_month':
      return `Sinh nhật tháng ${monthOf(occasionDate)}`
    case 'work_anniversary':
      return 'Kỷ niệm năm làm việc'
  }
}

/** Tháng (1–12) của chuỗi `yyyy-mm-dd`; chuỗi hỏng → tháng hiện tại, không ném lỗi. */
export function monthOf(isoDate: string, today = new Date()): number {
  const m = /^\d{4}-(\d{2})-\d{2}$/.exec(isoDate)
  const month = m ? Number(m[1]) : NaN
  return month >= 1 && month <= 12 ? month : today.getMonth() + 1
}

/**
 * Lần tới của một ngày dương lịch cố định, TÍNH CẢ hôm nay — 27/10 bấm «8/3» ra 08/3 năm sau,
 * đúng ngày 20/10 bấm «20/10» ra chính hôm đó. Lập muộn cho dịp đã qua thì chọn lại ở ô ngày.
 */
export function resolveNextOccurrence(month: number, day: number, today = new Date()): string {
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const thisYear = new Date(today.getFullYear(), month - 1, day)
  return toDateInputValue(thisYear >= start ? thisYear : new Date(today.getFullYear() + 1, month - 1, day))
}

/**
 * Ngày dịp đang xem = cuối kỳ trên URL: kỳ «Tùy chọn» lấy `date_to`; preset khác thì tính
 * cục bộ cuối kỳ của preset đó (chỉ để HIỆN ô ngày — số liệu vẫn theo kỳ backend tính).
 */
export function resolveOccasionDate(
  params: URLSearchParams,
  fallbackPreset: ReportPresetKey = BENEFIT_DEFAULT_PRESET,
  today = new Date(),
): string {
  const preset = params.get('preset')
  const dateTo = params.get('date_to') ?? ''
  if (preset === 'custom' && /^\d{4}-\d{2}-\d{2}$/.test(dateTo)) return dateTo
  const key = isReportPresetKey(preset) && preset !== 'custom' ? preset : fallbackPreset
  return resolveLocalPresetRange(key, today)[1]
}

/** Các tham số đặt kỳ về MỘT ngày dịp — kèm `compare=none` (so «hôm trước» vô nghĩa với danh sách nhận quà). */
function buildSingleDayPeriod(day: string): Record<string, string | null> {
  return { preset: 'custom', date_from: day, date_to: day, compare: 'none', year: null }
}

/**
 * Bấm một dịp có sẵn → MỌI tham số trong MỘT lượt ghi URL. Ghi đè đủ bốn ô do dịp quản
 * (giới tính, tuổi con, tháng sinh, thâm niên) để dịp trước không sót lại — bấm «1/6» sau
 * «8/3» thì không còn lọc riêng nữ. Ô tuổi, mức quà, công tắc người đang nghỉ giữ nguyên.
 */
export function buildOccasionPresetParams(
  preset: BenefitOccasionPreset,
  currentOccasionDate: string,
  today = new Date(),
): Record<string, string | null> {
  const day = preset.fixedDate
    ? resolveNextOccurrence(preset.fixedDate.month, preset.fixedDate.day, today)
    : currentOccasionDate
  return {
    ...(preset.fixedDate ? buildSingleDayPeriod(day) : {}),
    [BENEFIT_PARAM.gender]: preset.gender ?? null,
    [BENEFIT_PARAM.childMaxAge]: preset.childMaxAge != null ? String(preset.childMaxAge) : null,
    [BENEFIT_PARAM.birthMonth]: preset.birthMonthOfOccasion ? String(monthOf(day, today)) : null,
    [BENEFIT_PARAM.seniorityYears]: preset.seniorityYears?.join(',') ?? null,
    [BENEFIT_PARAM.occasionLabel]: buildOccasionLabel(preset, day),
  }
}

/**
 * Đổi ngày dịp → kỳ «Tùy chọn» đúng một ngày. Đang lọc «sinh nhật tháng» theo tháng của
 * ngày dịp cũ thì tháng sinh (và tên dịp tự điền) đi theo ngày mới — cùng lượt ghi.
 */
export function buildOccasionDateParams(
  day: string,
  current: URLSearchParams,
  currentOccasionDate: string,
): Record<string, string | null> {
  const next = buildSingleDayPeriod(day)
  const birthMonth = current.get(BENEFIT_PARAM.birthMonth)
  if (birthMonth !== null && birthMonth === String(monthOf(currentOccasionDate))) {
    next[BENEFIT_PARAM.birthMonth] = String(monthOf(day))
    const label = current.get(BENEFIT_PARAM.occasionLabel)
    if (label === `Sinh nhật tháng ${birthMonth}`) next[BENEFIT_PARAM.occasionLabel] = `Sinh nhật tháng ${monthOf(day)}`
  }
  return next
}

/** Dịp đang bật = tên dịp và bốn ô do dịp quản khớp đúng như lúc bấm nút. */
export function findActiveOccasionPreset(
  params: URLSearchParams,
  occasionDate: string,
): BenefitOccasionPresetId | null {
  for (const preset of BENEFIT_OCCASION_PRESETS) {
    const want = buildOccasionPresetParams(preset, occasionDate)
    const keys = [
      BENEFIT_PARAM.gender,
      BENEFIT_PARAM.childMaxAge,
      BENEFIT_PARAM.birthMonth,
      BENEFIT_PARAM.seniorityYears,
    ] as const
    if (params.get(BENEFIT_PARAM.occasionLabel) !== want[BENEFIT_PARAM.occasionLabel]) continue
    if (keys.every((k) => (params.get(k) ?? null) === want[k])) return preset.id
  }
  return null
}

/** Mọi tham số riêng của H1 về mặc định trong MỘT lượt ghi (nút «Bỏ hết điều kiện»). Kỳ giữ nguyên. */
export function buildClearBenefitParams(): Record<string, null> {
  return Object.fromEntries(Object.values(BENEFIT_PARAM).map((k) => [k, null]))
}
