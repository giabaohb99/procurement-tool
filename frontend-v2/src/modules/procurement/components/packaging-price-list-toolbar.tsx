/**
 * duoc-CR-784 — thanh lọc của Bảng giá VTBB: ô chọn mã (27/11/2026 thay ô tìm chữ — gõ mã, tên, tên nhóm hoặc tên NCC, chọn
 * nhiều mã, như màn Tác động), chip nhóm, phạm vi mã (chỉ mã trong định mức hay mọi mã có trong sổ giá).
 */
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'
import { cn } from '@/shared/utils/cn'

import type { PackagingCodeOption } from '../types/packaging-cost-types'
import { PackagingCodePicker } from './packaging-code-picker'

export interface PriceListFilters {
  /** Mã chọn ở ô chọn mã; rỗng = mọi mã theo phạm vi. */
  codes: string[]
  /** Rỗng = mọi nhóm. */
  group: string
  scope: 'bom' | 'all'
}

interface PackagingPriceListToolbarProps {
  filters: PriceListFilters
  groups: string[]
  /** Danh sách mã cho ô chọn mã (mọi mã có trong sổ giá, đã xếp). */
  codeOptions?: PackagingCodeOption[]
  codeOptionsLoading?: boolean
  onChange: (filters: PriceListFilters) => void
}

export function PackagingPriceListToolbar({
  filters,
  groups,
  codeOptions = [],
  codeOptionsLoading = false,
  onChange,
}: PackagingPriceListToolbarProps) {
  const patch = (next: Partial<PriceListFilters>) => onChange({ ...filters, ...next })

  return (
    //  `flex-1` (không `w-full`): khối lọc chiếm phần còn lại của hàng để nút Tải lại / Cột của bảng đứng CÙNG hàng bên phải;
    //  `w-full` từng đẩy hai nút đó xuống một hàng riêng, chừa dải trống giữa thanh lọc và bảng (người chủ báo 23/11/2026).
    //  Khổ điện thoại: khối lọc chiếm TRỌN hàng (`basis-full`) — cụm nút bên phải còn thêm ô "Xếp theo", chia hàng với nó
    //  thì ô tìm co còn một mẩu và chip nhóm dựng thành cột.
    <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2 max-md:basis-full">
      <div className="w-full max-w-md">
        <PackagingCodePicker
          options={codeOptions}
          value={filters.codes}
          onChange={(codes) => patch({ codes })}
          loading={codeOptionsLoading}
          emptyPlaceholder="Tìm mã VTBB — gõ mã, tên, nhóm hoặc NCC, chọn được nhiều mã"
          compact
        />
      </div>

      <div className="flex flex-wrap gap-1" role="group" aria-label="Lọc theo nhóm">
        {['', ...groups].map((group) => (
          <button
            key={group || 'all'}
            type="button"
            aria-pressed={filters.group === group}
            onClick={() => patch({ group })}
            className={cn(
              'h-8 rounded-full border px-3 text-sm hover:bg-accent',
              filters.group === group &&
                'border-primary bg-primary text-primary-foreground hover:bg-primary/90',
            )}
          >
            {group || 'Tất cả'}
          </button>
        ))}
      </div>

      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={filters.scope}
        onValueChange={(value) => value && patch({ scope: value as PriceListFilters['scope'] })}
        aria-label="Phạm vi mã"
      >
        <ToggleGroupItem value="bom">Mã trong định mức</ToggleGroupItem>
        <ToggleGroupItem value="all">Mọi mã có giá</ToggleGroupItem>
      </ToggleGroup>
    </div>
  )
}
