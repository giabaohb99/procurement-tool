import type { LinesTableColumn } from '@/shared/data-table/types'
import type { HeadcountPlanPeriod } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { listPerPositionItems } from '../utils/hr-cost-item-rules'

/** Tiền tố khóa cột — cột định biên theo chỉ số kỳ con, cột số tiền theo MÃ khoản. */
export const HEADCOUNT_COLUMN_PREFIX = 'hc_'
export const AMOUNT_COLUMN_PREFIX = 'amt_'

/**
 * Cột của khối ĐỊNH BIÊN THEO VỊ TRÍ (tài liệu 06 §2.3): Vị trí · một cột cho MỖI kỳ con · Đang có ·
 * Cần tuyển · một cột cho MỖI khoản «nhập theo vị trí» · Ghi chú · Thao tác.
 *
 * Cột số tiền chỉ mọc khi người xem được xem lương — che bằng cách KHÔNG dựng cột, không phải dựng
 * cột rỗng (một cột toàn ô trống đọc ra «chưa ai nhập lương»).
 */
export function buildHeadcountPlanLineColumns(opts: {
  periods: readonly HeadcountPlanPeriod[]
  items: readonly HrCostItem[]
  showMoney: boolean
  readOnly: boolean
}): LinesTableColumn[] {
  const columns: LinesTableColumn[] = [
    { key: 'position', header: 'Vị trí', width: 220, hideable: false, defaultPinned: true },
    ...opts.periods.map((p, i) => ({
      key: `${HEADCOUNT_COLUMN_PREFIX}${i}`,
      header: `Định biên ${p.label}`,
      width: 110,
      align: 'right' as const,
      hideable: false,
    })),
    { key: 'current', header: 'Đang có', width: 90, align: 'right' },
    { key: 'need', header: 'Cần tuyển', width: 100, align: 'right' },
  ]
  if (opts.showMoney) {
    for (const item of listPerPositionItems(opts.items)) {
      columns.push({
        key: `${AMOUNT_COLUMN_PREFIX}${item.code}`,
        header: `${item.name || item.code} / người / tháng`,
        width: 170,
        align: 'right',
      })
    }
  }
  columns.push({ key: 'note', header: 'Ghi chú', width: 200, compactHidden: true })
  if (!opts.readOnly) columns.push({ key: 'actions', header: 'Thao tác', width: 70, hideable: false })
  return columns
}
