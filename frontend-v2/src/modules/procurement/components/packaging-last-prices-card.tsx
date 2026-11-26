/**
 * duoc-CR-784 — THẺ điện thoại của một mã ở tab GIÁ MUA GẦN NHẤT (`usePackagingLastPricesColumns`).
 *
 * Bảng trải n cụm cột "Lần 1 … Lần n" theo chiều ngang (~3400px ở n = 10); thẻ gập chúng thành DANH SÁCH DỌC n dòng
 * "Lần k · ngày · nhà cung cấp · (số lượng) · đơn giá", đơn giá tô xanh / đỏ so với lần cũ hơn kế bên đúng như bảng
 * (`purchaseTrendTone`). Số chính ở trên: biến động lần 1 so lần 2 / lần n và giá trung bình.
 */
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import type { PackagingLastPricesRow } from '../types/packaging-cost-types'
import { purchaseTrendTone } from '../utils/packaging-last-prices'
import { formatPackagingPrice } from '../utils/packaging-price-format'
import { PackagingCodeLink } from './packaging-code-link'
import { PackagingCardStats, PackagingCardTitle } from './packaging-mobile-card-parts'
import { EmptyDash, PercentText, PriceText } from './packaging-price-cells'

interface PackagingLastPricesCardProps {
  row: PackagingLastPricesRow
  /** Số lần đang hiện (3 / 5 / 10) — nhãn "Lần 1 so lần n", "Giá TB n lần". */
  n: number
  /** Công tắc "Hiện số lượng" của thanh lọc. */
  showQty: boolean
}

export function PackagingLastPricesCard({ row, n, showQty }: PackagingLastPricesCardProps) {
  const purchases = row.purchases.slice(0, n)
  return (
    <div className="space-y-2.5">
      <PackagingCardTitle
        code={<PackagingCodeLink code={row.code} />}
        name={row.name}
        aside={
          <>
            {row.group && <Badge variant="secondary">{row.group}</Badge>}
            <span className="text-xs whitespace-nowrap text-muted-foreground">
              {row.purchase_count.toLocaleString('vi-VN')} lần có giá
              {row.unit && ` · ${row.unit}`}
            </span>
          </>
        }
      />

      <PackagingCardStats
        columns={3}
        items={[
          { label: 'Lần 1 so lần 2', value: <PercentText value={row.v12} /> },
          { label: `Lần 1 so lần ${n}`, value: <PercentText value={row.v1n} /> },
          { label: `Giá TB ${n} lần`, value: <PriceText value={row.avg} /> },
        ]}
      />

      {purchases.length === 0 ? (
        <p className="text-xs text-muted-foreground">Chưa có lần mua nào có giá.</p>
      ) : (
        <ol className="space-y-1" aria-label="Các lần mua gần nhất">
          {purchases.map((purchase, index) => {
            const qty = formatPackagingPrice(purchase.qty)
            return (
              <li key={index} className="flex items-baseline gap-2 text-xs">
                <span className="w-9 shrink-0 text-muted-foreground">Lần {index + 1}</span>
                <span className="shrink-0 tabular-nums">
                  {purchase.date ? formatDate(purchase.date) : <EmptyDash />}
                </span>
                <span className="min-w-0 flex-1 truncate" title={purchase.supplier}>
                  {purchase.supplier || <EmptyDash />}
                </span>
                {showQty && qty && (
                  <span className="shrink-0 text-muted-foreground tabular-nums">SL {qty}</span>
                )}
                <span className="shrink-0 text-right">
                  <PriceText
                    value={purchase.price}
                    className={cn('font-semibold', purchaseTrendTone(row, index))}
                  />
                </span>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
