import { COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import { formatMoney, formatPercent, formatQuantity } from '@/shared/utils/format-money'
import type { HrCostItem } from '../types/hr-cost'

const M = COST_CALC_METHOD_CODE

/** Chữ thay cho số tiền khi người xem không được xem lương của pháp nhân. */
export const HIDDEN_MONEY_TEXT = '(ẩn số tiền)'

interface DescribeCostItemOptions {
  showMoney: boolean
  /** Danh mục chức vụ — đọc tên vị trí khi khoản chỉ áp cho vài vị trí. */
  positions?: readonly { id: number; name: string }[]
}

const formatMonths = (months: readonly number[]) =>
  [...months]
    .sort((a, b) => a - b)
    .map((m) => `T${m}`)
    .join(', ')

/** Tên các vị trí đã chọn: tối đa 2 tên, còn lại gom «và n vị trí khác». */
function describePositions(item: HrCostItem, positions: DescribeCostItemOptions['positions']): string {
  if (item.applies_to !== COST_APPLIES_TO_CODE.SELECTED_POSITIONS) return ''
  const names = (positions ?? []).filter((p) => item.position_ids.includes(p.id)).map((p) => p.name)
  if (names.length === 0) return `chỉ ${item.position_ids.length} vị trí đã chọn`
  const rest = item.position_ids.length - 2
  return `chỉ vị trí: ${names.slice(0, 2).join(', ')}${rest > 0 ? ` và ${rest} vị trí khác` : ''}`
}

/** «(Lương + Phụ cấp)» — tên các khoản trong «Tính trên khoản»; khoản đã xóa thì hiện mã. */
function describeBases(item: HrCostItem, all: readonly HrCostItem[]): string {
  if (item.base_codes.length === 0) return '(chưa chọn khoản)'
  const names = item.base_codes.map((c) => {
    const found = all.find((i) => i.code === c)
    return found?.name.trim() || c
  })
  return names.length > 1 ? `(${names.join(' + ')})` : names[0]
}

/**
 * MÔ TẢ MỘT DÒNG cho khoản chi phí, đọc ra đúng cách hệ thống sẽ tính — thay cho bảng nhiều cột
 * (Tỷ lệ / Trần / Số tiền / Khoản gốc / Tháng) mà người dùng không hiểu. Ví dụ:
 * «23,5% × (Lương + Phụ cấp), tối đa 50.600.000 đ/người» · «1 tháng × Lương, chi vào T12» ·
 * «500.000 đ/người, chi vào T3». Không xem được tiền: số tiền thành «(ẩn số tiền)», tỷ lệ vẫn hiện.
 */
export function describeCostItem(
  item: HrCostItem,
  all: readonly HrCostItem[],
  { showMoney, positions }: DescribeCostItemOptions,
): string {
  const money = (v: number | null) => (showMoney ? `${formatMoney(v ?? 0)} đ` : HIDDEN_MONEY_TEXT)
  const months = item.months.length ? `chi vào ${formatMonths(item.months)}` : ''
  const parts: string[] = []
  switch (item.calc_method) {
    case M.PER_HEAD_MONTH:
      //  Mức chung (`amount`) áp cho mọi vị trí; vị trí nào nhập riêng ở bảng Số người thì số riêng thắng.
      //  Che tiền thì `amount` về null — không biết có mức chung hay không, nên nói cả hai khả năng.
      if (!showMoney) parts.push(`${HIDDEN_MONEY_TEXT} · nhập theo từng vị trí`, months)
      else if (Number(item.amount) > 0) parts.push(`${money(item.amount)}/người/tháng · vị trí nhập riêng nếu khác`, months)
      else parts.push('Nhập số tiền theo từng vị trí', months)
      break
    case M.PERCENT_OF:
      parts.push(`${formatPercent(item.rate ?? 0)} × ${describeBases(item, all)}`)
      //  Che tiền thì `cap_amount` về null — không biết có trần hay không, nên im lặng thay vì đoán.
      if (showMoney && Number(item.cap_amount) > 0) parts.push(`tối đa ${money(item.cap_amount)}/người`)
      parts.push(months)
      break
    case M.MONTHS_OF:
      parts.push(`${formatQuantity(item.factor ?? 0)} tháng × ${describeBases(item, all)}`, months || 'chưa chọn tháng chi')
      break
    case M.PER_HEAD_ONCE:
      parts.push(`${money(item.amount)}/người`, months || 'chưa chọn tháng chi')
      break
    case M.LUMP_SUM:
      parts.push(`${money(item.amount)} cả phòng`, months || 'chia đều các tháng')
      break
    default:
      return 'Cách tính chưa hỗ trợ'
  }
  parts.push(describePositions(item, positions))
  return parts.filter(Boolean).join(', ')
}
