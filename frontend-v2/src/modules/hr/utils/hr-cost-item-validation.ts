import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { pickDefaultPercentBases } from './hr-cost-item-kind'

const M = COST_CALC_METHOD_CODE

interface ValidateOptions {
  /** Tháng của kỳ kế hoạch; rỗng = không kiểm «ngoài kỳ». */
  periodMonths?: readonly number[]
  /** Người không xem được tiền nhận `null` ở ô tiền — đừng đòi họ nhập số. */
  showMoney?: boolean
}

/**
 * KIỂM MỘT DÒNG của khối «Chi phí khác» (cách tính 2…5) — câu ngắn đọc được, không nói «khoản», «cách
 * tính», «mã». Báo sớm những chỗ backend sẽ chặn 422 (`costing.py`) cộng vài chỗ backend để lọt nhưng
 * chắc chắn là nhập thiếu (tỷ lệ 0%, số tiền 0). Dòng đã TẮT thì không kiểm — nó không được lưu.
 *
 * `others` = mọi khoản KHÁC của bộ (để biết còn lương / phụ cấp cho khoản % tính trên không).
 */
export function listOtherCostProblems(
  item: HrCostItem,
  others: readonly HrCostItem[],
  { periodMonths = [], showMoney = true }: ValidateOptions = {},
): string[] {
  if (item.excluded) return []
  const out: string[] = []
  if (!item.name.trim()) out.push('Chưa đặt tên.')
  const m = item.calc_method
  if (m === M.PERCENT_OF && !(Number(item.rate) > 0)) out.push('Nhập tỷ lệ % lớn hơn 0.')
  if (m === M.MONTHS_OF && !(Number(item.factor) > 0)) out.push('Nhập số tháng lương lớn hơn 0.')
  if ((m === M.PER_HEAD_ONCE || m === M.LUMP_SUM) && showMoney && !(Number(item.amount) > 0)) {
    out.push('Nhập số tiền lớn hơn 0.')
  }
  const active = others.filter((o) => !o.excluded)
  if ((m === M.PERCENT_OF || m === M.MONTHS_OF) && pickDefaultPercentBases(active).length === 0) {
    out.push('Chưa có lương để tính — thêm vị trí và nhập lương ở bảng Người và lương.')
  }
  if ((m === M.MONTHS_OF || m === M.PER_HEAD_ONCE) && item.months.length === 0) out.push('Chọn tháng chi.')
  else if (periodMonths.length && item.months.some((x) => !periodMonths.includes(x))) {
    out.push('Tháng chi nằm ngoài kỳ của kế hoạch — chọn lại tháng.')
  }
  return out
}
