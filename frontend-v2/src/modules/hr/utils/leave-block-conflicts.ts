import { formatDate } from '@/shared/utils/format-date'
import type { LeaveBlockConflict } from '../types/leave'

/** "20/12/2026 – 31/12/2026", hoặc một ngày nếu từ = đến. Ngày dd/mm/yyyy. */
export function formatBlockRange(b: Pick<LeaveBlockConflict, 'from_date' | 'to_date'>): string {
  return b.from_date === b.to_date
    ? formatDate(b.from_date)
    : `${formatDate(b.from_date)} – ${formatDate(b.to_date)}`
}

/** Mỗi khoảng một dòng: "20/12/2026 – 31/12/2026 · Chốt sổ cuối năm". */
export function describeBlockConflicts(conflicts: readonly LeaveBlockConflict[] | undefined | null): string[] {
  return (conflicts ?? []).map((c) => (c.reason ? `${formatBlockRange(c)} · ${c.reason}` : formatBlockRange(c)))
}
