import type { HrCostItem } from '../types/hr-cost'

/**
 * CHÉP khoản của mẫu vào kế hoạch theo kỳ — bản giao diện của `plan_save_service.copy_template_items`
 * (backend), để bảng khoản và bản xem trước khớp đúng thứ backend sẽ chép khi tạo kế hoạch:
 *
 * 1. Bỏ các tháng rơi ngoài kỳ. Khoản có khai tháng mà MỌI tháng đều ngoài kỳ (thưởng T12 trong kế
 *    hoạch Q1) không còn gì để tính → bỏ cả khoản.
 * 2. Khoản trỏ vào khoản đã bỏ: % thì bớt gốc (hết gốc → bỏ), «số tháng» mất gốc → bỏ. Lặp tới khi
 *    không còn gì đổi (bỏ khoản này có thể kéo theo khoản trỏ vào nó).
 *
 * Trả bộ khoản còn lại + tên các khoản đã bỏ (theo đúng thứ tự bỏ, để báo trên form).
 */
export function copyTemplateItemsForPeriod(
  templateItems: readonly HrCostItem[],
  periodMonths: readonly number[],
): { items: HrCostItem[]; skipped: string[] } {
  const inPeriod = new Set(periodMonths)
  const kept = new Map<string, HrCostItem>()
  const skipped: string[] = []
  for (const src of templateItems) {
    const months = src.months.filter((m) => inPeriod.has(m))
    if (src.months.length > 0 && months.length === 0) {
      skipped.push(src.name)
      continue
    }
    kept.set(src.code, { ...src, id: undefined, months, base_codes: [...src.base_codes], position_ids: [...src.position_ids] })
  }
  let changed = true
  while (changed) {
    changed = false
    for (const [code, item] of [...kept]) {
      if (item.base_codes.length === 0) continue
      const present = item.base_codes.filter((b) => kept.has(b))
      if (present.length === item.base_codes.length) continue
      changed = true
      if (present.length === 0) {
        skipped.push(item.name)
        kept.delete(code)
      } else {
        kept.set(code, { ...item, base_codes: present })
      }
    }
  }
  return { items: [...kept.values()], skipped }
}
