/**
 * duoc-CR-784 — luật thuần của tab Tổng hợp theo sản phẩm: chip xu hướng kèm số đếm, bộ lọc → tham số máy chủ.
 *
 * Chip dùng mã CHỮ của URL (`up` / `down` / `flat` / `missing`) — khác mã SỐ `CostTrend` của từng dòng; nhãn của hai thứ
 * này trùng nhau nên chip lấy nhãn từ bộ mã sinh TS, không gõ lại.
 */
import { PACKAGING_COST_TREND_CODE } from '@/shared/constants/statuses'

import type {
  PackagingOverviewCounts,
  PackagingOverviewParams,
  PackagingOverviewTrend,
} from '../types/packaging-cost-types'
import { overviewFiltersToParams, type ImpactAdvancedFilters } from './packaging-impact-filters'
import { costTrendLabel } from './packaging-warning-text'

export const OVERVIEW_TREND_CHIPS: readonly {
  value: PackagingOverviewTrend
  label: string
  title: string
}[] = [
  { value: 'all', label: 'Tất cả', title: 'Mọi sản phẩm có định mức bao bì' },
  {
    value: 'up',
    label: costTrendLabel(PACKAGING_COST_TREND_CODE.UP),
    title: 'Chi phí bao bì tăng — cần xem lại giá bán',
  },
  {
    value: 'down',
    label: costTrendLabel(PACKAGING_COST_TREND_CODE.DOWN),
    title: 'Chi phí bao bì giảm',
  },
  {
    value: 'flat',
    label: costTrendLabel(PACKAGING_COST_TREND_CODE.SAME),
    title: 'Chi phí bao bì không đổi',
  },
  {
    value: 'missing',
    label: costTrendLabel(PACKAGING_COST_TREND_CODE.NO_PRICE),
    title: 'Thiếu giá chai nên chưa tính được chi phí',
  },
]

/** "Tăng (263)"; chưa có số đếm (đang tải lần đầu) thì chỉ nhãn. */
export function overviewChipLabel(
  chip: { value: PackagingOverviewTrend; label: string },
  counts: PackagingOverviewCounts | undefined,
): string {
  const count = counts?.[chip.value]
  return count == null ? chip.label : `${chip.label} (${count.toLocaleString('vi-VN')})`
}

/** Bộ lọc (kể cả lọc nâng cao) + thứ tự màn hình → tham số gửi máy chủ (danh sách VÀ Xuất Excel dùng chung nên ra cùng thứ tự). */
export function buildOverviewParams(
  trend: PackagingOverviewTrend,
  search: string,
  sort: { by: string; dir: 'asc' | 'desc' },
  advanced?: ImpactAdvancedFilters,
): PackagingOverviewParams {
  return {
    ...(advanced ? overviewFiltersToParams(advanced) : {}),
    q: search.trim() || undefined,
    trend: trend === 'all' ? undefined : trend,
    //  Chưa chọn cột xếp thì KHÔNG gửi — máy chủ xếp mặc định theo mã HH.
    ...(sort.by ? { sort_by: sort.by, sort_dir: sort.dir } : {}),
  }
}
