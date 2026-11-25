/**
 * duoc-CR-784 — các thẻ số liệu của Lịch sử mua hàng, chép đúng bộ thẻ của bản mẫu HTML (người chủ chốt 23/11/2026):
 *
 * - Đúng MỘT mã: Tổng số lần mua · Tổng số lượng mua · Tổng giá trị mua · Giá thấp nhất – cao nhất · Gần nhất so với lần
 *   đầu · Số nhà cung cấp.
 * - Nhiều mã / mọi mã: Số mã đã chọn (hoặc Số mã hàng) · Tổng số lần mua · Tổng giá trị mua · Số nhà cung cấp — trộn giá
 *   của nhiều vật tư ra một số bình quân / thấp nhất / cao nhất là vô nghĩa nên bỏ.
 * - Theo mã sản phẩm: Số sản phẩm · Mã vật tư liên quan · Số dòng lịch sử · Số nhà cung cấp.
 *
 * Mỗi thẻ có dòng phụ như bản mẫu; số tính trên TOÀN BỘ tập đã lọc, không phải trang đang xem. Màn hình và bản in dùng
 * chung hàm này nên hai nơi không lệch nhau.
 */
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'

import type { PackagingHistoryMode, PackagingHistoryStats } from '../types/packaging-cost-types'
import { formatPackagingPercent, formatPackagingPrice } from './packaging-price-format'

export interface HistorySummaryItem {
  label: string
  value: string
  /** Dòng phụ dưới số (khoảng ngày, ĐVT, số lần có giá...). */
  sub?: string
  /** Chiều giá của thẻ "Gần nhất so với lần đầu": tăng = xanh, giảm = đỏ (luật màu chung của cụm). */
  tone?: 'up' | 'down'
}

export interface HistorySummaryContext {
  /** Tập lọc chỉ còn đúng một mã (máy chủ trả biểu đồ). */
  singleCode: boolean
  mode: PackagingHistoryMode
  /** Số mã VTBB (chế độ mã) hoặc mã sản phẩm (chế độ sản phẩm) người dùng đã chọn; 0 = tất cả. */
  selectedCount: number
}

const DASH = '—'

/** "06/01/2025 → 08/11/2025"; một ngày thì một ngày; chưa có lần mua thì rỗng. */
function formatDateSpan(stats: PackagingHistoryStats): string {
  if (!stats.first_date || !stats.last_date) return ''
  if (stats.first_date === stats.last_date) return formatDate(stats.first_date)
  return `${formatDate(stats.first_date)} → ${formatDate(stats.last_date)}`
}

/** Tỷ lệ giá gần nhất / giá lần đầu − 1; thiếu một đầu hoặc giá đầu bằng 0 thì không có số. */
export function getLatestVsFirstRatio(stats: PackagingHistoryStats): number | null {
  const { first_price: first, last_price: last } = stats
  if (first == null || last == null || first <= 0) return null
  return last / first - 1
}

const countText = (value: number): string => value.toLocaleString('vi-VN')

function buildPurchaseCountItem(stats: PackagingHistoryStats, label: string): HistorySummaryItem {
  return { label, value: countText(stats.purchase_count), sub: formatDateSpan(stats) }
}

function buildAmountItem(stats: PackagingHistoryStats): HistorySummaryItem {
  return {
    label: 'Tổng giá trị mua',
    value: formatMoney(stats.amount_total ?? 0) || '0',
    sub: `${countText(stats.priced_count)}/${countText(stats.purchase_count)} lần có giá`,
  }
}

function buildSupplierItem(stats: PackagingHistoryStats): HistorySummaryItem {
  return { label: 'Số nhà cung cấp', value: countText(stats.supplier_count) }
}

function buildSingleCodeItems(stats: PackagingHistoryStats): HistorySummaryItem[] {
  const ratio = getLatestVsFirstRatio(stats)
  const low = formatPackagingPrice(stats.min)
  const high = formatPackagingPrice(stats.max)
  const average = formatPackagingPrice(stats.weighted_avg)
  return [
    buildPurchaseCountItem(stats, 'Tổng số lần mua'),
    {
      label: 'Tổng số lượng mua',
      value: formatQuantity(stats.qty_total) || '0',
      sub: stats.unit || undefined,
    },
    buildAmountItem(stats),
    {
      label: 'Giá thấp nhất – cao nhất',
      value: low && high ? `${low} – ${high}` : DASH,
      sub: average ? `BQ gia quyền ${average}` : undefined,
    },
    {
      label: 'Gần nhất so với lần đầu',
      value: ratio === null ? DASH : formatPackagingPercent(ratio),
      sub:
        stats.first_price != null && stats.last_price != null
          ? `${formatPackagingPrice(stats.first_price)} → ${formatPackagingPrice(stats.last_price)}`
          : undefined,
      tone: ratio === null || Math.abs(ratio) < 1e-9 ? undefined : ratio > 0 ? 'up' : 'down',
    },
    buildSupplierItem(stats),
  ]
}

function buildManyCodesItems(
  stats: PackagingHistoryStats,
  selectedCount: number,
): HistorySummaryItem[] {
  const codesItem: HistorySummaryItem =
    selectedCount > 0
      ? {
          label: 'Số mã đã chọn',
          value: countText(selectedCount),
          sub: `${countText(stats.code_count ?? 0)} mã có lịch sử mua`,
        }
      : {
          label: 'Số mã hàng',
          value: countText(stats.code_count ?? 0),
          sub: 'tất cả mã có lịch sử mua',
        }
  return [
    codesItem,
    buildPurchaseCountItem(stats, 'Tổng số lần mua'),
    buildAmountItem(stats),
    buildSupplierItem(stats),
  ]
}

function buildProductItems(
  stats: PackagingHistoryStats,
  selectedCount: number,
): HistorySummaryItem[] {
  return [
    //  Số sản phẩm có định mức trong phạm vi chọn (máy chủ đếm); "đã chọn" / "tất cả" như bản mẫu.
    {
      label: 'Số sản phẩm',
      value: countText(stats.product_count ?? selectedCount),
      sub: selectedCount > 0 ? 'đã chọn' : 'tất cả',
    },
    {
      label: 'Mã vật tư liên quan',
      value: countText(stats.code_count ?? 0),
      sub: 'chai, nắp, nhãn, nhãn thùng, thùng',
    },
    buildPurchaseCountItem(stats, 'Số dòng lịch sử'),
    buildSupplierItem(stats),
  ]
}

export function buildHistorySummary(
  stats: PackagingHistoryStats,
  { singleCode, mode, selectedCount }: HistorySummaryContext,
): HistorySummaryItem[] {
  if (singleCode) return buildSingleCodeItems(stats)
  return mode === 'product'
    ? buildProductItems(stats, selectedCount)
    : buildManyCodesItems(stats, selectedCount)
}
