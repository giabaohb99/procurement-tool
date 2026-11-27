/**
 * duoc-CR-784 — khóa TanStack Query của cụm Giá bao bì, dạng `[procurement, <thực thể>, <tham số>]`.
 *
 * why: luật `naming.md` muốn mọi khóa ở `shared/constants/query-keys.ts`, nhưng tệp đó đang có sửa dở
 * CHƯA commit của phiên khác (20/11/2026) — thêm vào bây giờ là trộn hai việc vào một tệp. Khóa ở đây
 * cùng gốc `procurement` nên `invalidateQueries(['procurement'])` vẫn quét được. Dời vào `query-keys.ts`
 * khi tệp đó sạch.
 */
import type {
  PackagingHistoryParams,
  PackagingImpactRequest,
  PackagingLastPricesParams,
  PackagingOverviewParams,
  PackagingPriceListParams,
} from '../types/packaging-cost-types'

const ROOT = 'procurement'

export const packagingCostKeys = {
  /** Gốc chung — dọn sau khi ghi báo giá / định mức (giá cũ-mới đổi theo). */
  all: [ROOT, 'packagingCost'] as const,
  codeOptions: (scope: 'bom' | 'all' = 'bom') => [ROOT, 'packagingCost', 'codeOptions', scope] as const,
  impact: (body: PackagingImpactRequest) => [ROOT, 'packagingCost', 'impact', body] as const,
  priceList: (params: PackagingPriceListParams) =>
    [ROOT, 'packagingCost', 'priceList', params] as const,
  lastPrices: (params: PackagingLastPricesParams) =>
    [ROOT, 'packagingCost', 'lastPrices', params] as const,
  productOverview: (params: PackagingOverviewParams) =>
    [ROOT, 'packagingCost', 'productOverview', params] as const,
  history: (params: PackagingHistoryParams) => [ROOT, 'packagingCost', 'history', params] as const,
  /** Bản in: nạp ĐỦ mọi dòng của bộ lọc (không có page) nên khóa riêng, không đụng khóa danh sách. */
  historyPrint: (params: PackagingHistoryParams) =>
    [ROOT, 'packagingCost', 'historyPrint', params] as const,
  impactPrint: (body: PackagingImpactRequest) =>
    [ROOT, 'packagingCost', 'impactPrint', body] as const,
  fgOptions: () => [ROOT, 'packagingCost', 'fgOptions'] as const,
}
