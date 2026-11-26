/**
 * duoc-CR-784 — THẺ điện thoại của một ĐỊNH MỨC BAO BÌ (`PACKAGING_BOM_CRUD_CONFIG.mobileCard`).
 *
 * Bấm cả thẻ = mở hộp sửa, nên thẻ nằm trong `<button>` và không chứa link. Năm thành phần thành năm dòng "nhãn · mã ·
 * tên"; mã chưa có trong danh mục sản phẩm tô đỏ như ô bảng.
 */
import { cn } from '@/shared/utils/cn'

import { PACKAGING_PART_COLUMNS } from '../config/packaging-part-columns'
import type { PackagingBom } from '../types/packaging-cost-types'
import { packagingRoleLabel } from '../utils/packaging-warning-text'
import { PackagingCardPartLine, PackagingCardTitle } from './packaging-mobile-card-parts'

export function PackagingBomCard({ row }: { row: PackagingBom }) {
  return (
    <div className="space-y-2">
      <PackagingCardTitle code={row.fg_code} name={row.fg_name} chevron />
      <ul className="space-y-1">
        <PackagingCardPartLine
          label="Quy cách thùng"
          code={
            row.carton_qty ? (
              row.carton_qty.toLocaleString('vi-VN')
            ) : (
              <span className="text-destructive">chưa có</span>
            )
          }
        />
        {PACKAGING_PART_COLUMNS.map((column) => {
          const code = String(row[column.field] ?? '')
          const part = row.parts?.find((item) => item.role === column.role)
          const missing = Boolean(code) && part ? !part.in_catalog : false
          return (
            <PackagingCardPartLine
              key={column.role}
              label={packagingRoleLabel(column.role)}
              code={<span className={cn(missing && 'text-destructive')}>{code || '—'}</span>}
              detailTitle={missing ? 'Mã chưa có trong danh mục sản phẩm' : (part?.name ?? '')}
              detail={
                code && (
                  <span className={cn('text-muted-foreground', missing && 'text-destructive')}>
                    {missing ? 'chưa có trong danh mục' : part?.name}
                  </span>
                )
              }
            />
          )
        })}
      </ul>
    </div>
  )
}
