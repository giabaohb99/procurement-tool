/**
 * duoc-CR-784 — khóa TanStack Query của cụm Giá bao bì, dạng `[procurement, <thực thể>, <tham số>]`.
 *
 * why: luật `naming.md` muốn mọi khóa ở `shared/constants/query-keys.ts`, nhưng tệp đó đang có sửa dở
 * CHƯA commit của phiên khác (20/11/2026) — thêm vào bây giờ là trộn hai việc vào một tệp. Khóa ở đây
 * cùng gốc `procurement` nên `invalidateQueries(['procurement'])` vẫn quét được. Dời vào `query-keys.ts`
 * khi tệp đó sạch.
 */
import type {
  PackagingImpactRequest,
  PackagingLastPricesParams,
  PackagingPriceListParams,
} from '../types/packaging-cost-types'

const ROOT = 'procurement'

export const packagingCostKeys = {
  /** Gốc chung — dọn sau khi ghi báo giá / ngưỡng / định mức (giá cũ-mới đổi theo). */
  all: [ROOT, 'packagingCost'] as const,
  codeOptions: () => [ROOT, 'packagingCost', 'codeOptions'] as const,
  impact: (body: PackagingImpactRequest) => [ROOT, 'packagingCost', 'impact', body] as const,
  priceList: (params: PackagingPriceListParams) =>
    [ROOT, 'packagingCost', 'priceList', params] as const,
  lastPrices: (params: PackagingLastPricesParams) =>
    [ROOT, 'packagingCost', 'lastPrices', params] as const,
  limit: (code: string) => [ROOT, 'packagingCost', 'limit', code] as const,
}
