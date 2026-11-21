/**
 * duoc-CR-784 — ba ô riêng của bảng Lịch sử mua hàng: đơn giá (dòng giá 0 mờ), chênh so lần trước, nguồn + số ĐMH.
 * Tách khỏi `use-packaging-history-columns.tsx` vì tệp hook chỉ được xuất hook (react-refresh).
 */
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { PRICE_SOURCE_TYPE_CODE } from '@/shared/constants/statuses'
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'

import type { PackagingHistoryRow } from '../types/packaging-cost-types'
import {
  formatPackagingDiff,
  formatPackagingPercent,
  packagingDiffTone,
} from '../utils/packaging-price-format'
import { EmptyDash, PriceText } from './packaging-price-cells'

/** Đơn giá 0 = dòng không có giá: hiện "0" mờ, không làm nhiễu cột (và không tô xanh / đỏ). */
export function PriceCell({ row }: { row: PackagingHistoryRow }) {
  if (row.price === 0)
    return (
      <span
        className="text-muted-foreground tabular-nums"
        title="Đơn giá 0 — không tính vào giá bình quân, thấp nhất, cao nhất"
      >
        0
      </span>
    )
  return <PriceText value={row.price} className="font-semibold" />
}

export function DiffCell({ row }: { row: PackagingHistoryRow }) {
  const diff = formatPackagingDiff(row.diff)
  if (!diff) return <EmptyDash />
  //  Giá không đổi so lần trước: một số 0 mờ, không kèm "(0,0%)" — cột cả trăm dòng toàn "0 (0,0%)" che mất những dòng có đổi.
  if (row.diff === 0) return <span className="text-muted-foreground tabular-nums">0</span>
  const percent = formatPackagingPercent(row.pct)
  return (
    <span className={cn('tabular-nums', packagingDiffTone(row.diff))}>
      {diff}
      {percent && ` (${percent})`}
    </span>
  )
}

/** Nhãn "ĐMH đang mở" (giá còn có thể đổi) + số ĐMH nguồn bấm được; dữ liệu cũ không có ĐMH thì để trống. */
export function SourceCell({ row }: { row: PackagingHistoryRow }) {
  const isOpenPo = row.source_type === PRICE_SOURCE_TYPE_CODE.PO_LINE
  if (!isOpenPo && row.doc_id <= 0) return null
  return (
    <span className="flex items-center gap-2">
      {isOpenPo && (
        <Badge
          variant="outline"
          title="Dòng đơn mua hàng đã duyệt, chưa hoàn thành — giá có thể còn đổi"
        >
          ĐMH đang mở
        </Badge>
      )}
      {row.doc_id > 0 && (
        <Link
          to={appRoutes.procurement.purchaseOrderDetail(row.doc_id)}
          onClick={(event) => event.stopPropagation()}
          className="truncate text-primary tabular-nums hover:underline"
        >
          {row.po_code || `#${row.doc_id}`}
        </Link>
      )}
    </span>
  )
}
