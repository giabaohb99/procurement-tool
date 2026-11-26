/**
 * duoc-CR-784 — THẺ điện thoại của một BÁO GIÁ VTBB (`PACKAGING_QUOTE_CRUD_CONFIG.mobileCard`).
 *
 * Bấm cả thẻ = mở hộp sửa (như bấm dòng), nên thẻ nằm trong `<button>` và KHÔNG chứa link: "Nguồn" chỉ là chữ (mở đợt
 * nhập Excel thì qua bảng ở màn rộng). Số chính là đơn giá, đứng bên phải tiêu đề.
 */
import { formatDate } from '@/shared/utils/format-date'

import type { PackagingQuote } from '../types/packaging-cost-types'
import { packagingQuoteSourceText } from '../utils/packaging-quote-source'
import { PackagingCardFields, PackagingCardTitle } from './packaging-mobile-card-parts'
import { EmptyDash, PriceText } from './packaging-price-cells'

export function PackagingQuoteCard({ row }: { row: PackagingQuote }) {
  const supplier = [row.supplier_name, row.supplier_code].filter(Boolean).join(' · ')
  return (
    <div className="space-y-2">
      <PackagingCardTitle
        code={row.product_code}
        name={row.product_name}
        chevron
        aside={
          <>
            <span className="text-xs text-muted-foreground">Đơn giá</span>
            <span className="text-base">
              <PriceText value={Number(row.price)} className="font-semibold" />
            </span>
          </>
        }
      />
      <PackagingCardFields
        items={[
          { label: 'Nhà cung cấp', value: supplier || <EmptyDash />, wide: true },
          { label: 'Ngày hiệu lực', value: formatDate(row.valid_from) },
          { label: 'VAT %', value: Number(row.vat) },
          {
            label: 'Nguồn',
            value: packagingQuoteSourceText(row.source_type, row.source_id) || <EmptyDash />,
          },
          ...(row.note ? [{ label: 'Ghi chú', value: row.note, wide: true }] : []),
        ]}
      />
    </div>
  )
}
