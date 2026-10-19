import type { UsageDailyRow, UsageProfileDetail, UsageSnapshot } from '../types/usage-profile'

/** Mức đậm 0..4 theo tỉ lệ với ô lớn nhất; ô 0 luôn nhạt nhất. */
export function heatLevel(value: number, max: number): number {
  if (!(value > 0) || !(max > 0)) return 0
  return Math.min(4, Math.max(1, Math.ceil((value / max) * 4)))
}

export type DayKind = 'worked' | 'leave' | 'holiday' | 'absent' | 'off'

/** Phân loại một ngày: nghỉ phép / lễ / ngày nghỉ xếp TRƯỚC «không vào» để không bị đọc nhầm là vắng. */
export function classifyDay(day: UsageDailyRow): DayKind {
  if (day.active) return 'worked' // có vào thì là đi làm, kể cả ngày lễ / cuối tuần
  if (day.is_holiday) return 'holiday'
  if (!day.is_workday) return 'off'
  if ((day.leave_days ?? 0) > 0) return 'leave'
  return 'absent'
}

/** Tổng thời gian ở lại theo phân hệ (ms) từ danh sách màn — dùng cho vòng «% thời gian theo phân hệ». */
export function sumDwellByModule(
  screens: { route: string; dwell_ms: number }[],
  moduleOf: (route: string) => string,
): { label: string; value: number }[] {
  const totals = new Map<string, number>()
  for (const s of screens) {
    if (!(s.dwell_ms > 0)) continue
    const name = moduleOf(s.route) || 'Giao diện cũ'
    totals.set(name, (totals.get(name) ?? 0) + s.dwell_ms)
  }
  return [...totals.entries()].map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value)
}

const SECURITY_KEYS = [
  'new_ip_logins',
  'new_device_logins',
  'max_parallel_ips',
  'export_rows_spike',
  'max_deletes_10min',
  'active_after_resign',
  'http_403',
]

/** Khóa nào được coi là «bất thường»: có giá trị > 0 (riêng số IP chỉ khi ≥ 2 nơi cùng lúc). */
export function findSecurityFlags(snapshot: UsageSnapshot): string[] {
  return SECURITY_KEYS.filter((key) => {
    const v = snapshot.metrics[key]?.v
    if (v == null || snapshot.unmeasured?.[key] !== undefined) return false
    return key === 'max_parallel_ips' ? v >= 2 : v > 0
  })
}

export const USAGE_WEEK_OPTIONS = [4, 8, 12] as const

/** Dòng «đang so với …» — nói rõ nhóm so sánh, và LÝ DO khi phải lùi về pháp nhân / toàn công ty. */
export function describeCohort(cohort: NonNullable<UsageProfileDetail['latest']>['cohort']): string {
  if (!cohort) return 'Chưa có nhóm so sánh.'
  if (cohort.kind === 1) return `Đang so với: vai trò ${cohort.name} (${cohort.size} người).`
  const scope = cohort.kind === 2 ? `pháp nhân ${cohort.name}` : 'toàn công ty'
  return `Đang so với: ${scope} (${cohort.size} người) vì chưa có vai trò nào đủ 5 người để so sánh.`
}
