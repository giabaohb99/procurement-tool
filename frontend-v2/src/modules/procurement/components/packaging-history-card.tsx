/**
 * duoc-CR-784 — THẺ điện thoại của một LẦN MUA ở màn Lịch sử mua hàng (`usePackagingHistoryColumns`), cả hai chế độ.
 *
 * Dòng đầu là thứ người ta dò trong lịch sử: ngày mua + lần (bên trái), đơn giá to bên phải. Rồi mã VTBB bấm được + tên;
 * chế độ "Theo mã sản phẩm" thêm dòng sản phẩm + thành phần phía trên. Trường phụ theo đúng tên cột; "So lần trước" tô
 * xanh / đỏ và "Nguồn" (ĐMH bấm được) dùng lại đúng ô của bảng. Dòng đơn giá 0 mờ như ở bảng.
 */
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'

import type { PackagingHistoryRow } from '../types/packaging-cost-types'
import { historyRoleText } from '../utils/packaging-history'
import { PackagingCodeLink } from './packaging-code-link'
import { DiffCell, PriceCell, SourceCell } from './packaging-history-cells'
import { PackagingCardFields } from './packaging-mobile-card-parts'
import { EmptyDash, PriceText } from './packaging-price-cells'

interface PackagingHistoryCardProps {
  row: PackagingHistoryRow
  /** Chế độ "Theo mã sản phẩm": thêm Mã SP · Tên sản phẩm · Thành phần. */
  productMode: boolean
  /** bao-CR-801 — dòng của Lịch sử mua nguyên liệu: mã chữ thường như cột Mã nguyên liệu của bảng. */
  rawMaterial?: boolean
}

export function PackagingHistoryCard({
  row,
  productMode,
  rawMaterial = false,
}: PackagingHistoryCardProps) {
  const qty = formatQuantity(row.qty)
  const role = historyRoleText(row)
  return (
    <div className={cn('space-y-2', row.price === 0 && 'text-muted-foreground')}>
      {productMode && (
        <div className="flex items-baseline gap-2 text-xs">
          <span className="font-semibold text-foreground tabular-nums">{row.fg_code}</span>
          <span className="min-w-0 flex-1 truncate" title={row.fg_name}>
            {row.fg_name || '(chưa có tên)'}
          </span>
          {role && <span className="shrink-0 text-muted-foreground">{role}</span>}
        </div>
      )}

      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <span className="font-semibold tabular-nums">
              {row.date ? formatDate(row.date) : <EmptyDash />}
            </span>
            <span className="text-xs text-muted-foreground tabular-nums">Lần {row.seq}</span>
          </div>
          <div className="flex min-w-0 items-baseline gap-1.5 text-sm">
            {rawMaterial ? (
              <span className="font-semibold tabular-nums">{row.code}</span>
            ) : (
              <PackagingCodeLink code={row.code} />
            )}
            <span className="truncate font-medium" title={row.name}>
              {row.name || '(chưa có tên)'}
            </span>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-xs text-muted-foreground">Đơn giá</div>
          <div className="text-base">
            <PriceCell row={row} />
          </div>
        </div>
      </div>

      <PackagingCardFields
        items={[
          { label: 'Nhà cung cấp', value: row.supplier || <EmptyDash />, wide: true },
          { label: 'Kho', value: row.warehouse || <EmptyDash />, wide: true },
          {
            label: 'Số lượng',
            value: qty ? (
              <span className="tabular-nums">
                {qty}
                {row.unit && <span className="ml-1 text-xs text-muted-foreground">{row.unit}</span>}
              </span>
            ) : (
              <EmptyDash />
            ),
          },
          { label: 'Giá trị mua', value: <PriceText value={row.amount} /> },
          { label: 'So lần trước', value: <DiffCell row={row} /> },
          {
            label: 'Nguồn',
            wide: true,
            //  Cùng điều kiện rỗng với `SourceCell` (dữ liệu cũ không có ĐMH) — ô thẻ trống thì đặt gạch như các trường khác.
            value: row.is_open || row.doc_id > 0 ? <SourceCell row={row} /> : <EmptyDash />,
          },
        ]}
      />
    </div>
  )
}
