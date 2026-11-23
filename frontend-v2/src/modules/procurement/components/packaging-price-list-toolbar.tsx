/**
 * duoc-CR-784 — thanh lọc của Bảng giá VTBB: ô tìm (gõ tên nhóm hoặc mã / tên), chip nhóm, phạm vi mã
 * (chỉ mã trong định mức hay mọi mã có trong sổ giá) và công tắc "chỉ mã ngoài ngưỡng".
 */
import { Search } from 'lucide-react'

import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Switch } from '@/shared/ui/switch'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'
import { cn } from '@/shared/utils/cn'
import { PACKAGING_LIMITS_ENABLED } from '../config/packaging-feature-flags'

export interface PriceListFilters {
  q: string
  /** Rỗng = mọi nhóm. */
  group: string
  scope: 'bom' | 'all'
  breachOnly: boolean
}

interface PackagingPriceListToolbarProps {
  filters: PriceListFilters
  groups: string[]
  onChange: (filters: PriceListFilters) => void
}

export function PackagingPriceListToolbar({
  filters,
  groups,
  onChange,
}: PackagingPriceListToolbarProps) {
  const patch = (next: Partial<PriceListFilters>) => onChange({ ...filters, ...next })

  return (
    //  `flex-1` (không `w-full`): khối lọc chiếm phần còn lại của hàng để nút Tải lại / Cột của bảng đứng CÙNG hàng bên phải;
    //  `w-full` từng đẩy hai nút đó xuống một hàng riêng, chừa dải trống giữa thanh lọc và bảng (người chủ báo 23/11/2026).
    <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
      <div className="relative w-full max-w-xs">
        <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          aria-label="Tìm mã vật tư"
          placeholder="Tìm mã, tên vật tư…"
          value={filters.q}
          onChange={(event) => patch({ q: event.target.value })}
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

      {PACKAGING_LIMITS_ENABLED && (
        <div className="flex items-center gap-2">
          <Switch
            id="price-breach-only"
            checked={filters.breachOnly}
            onCheckedChange={(breachOnly) => patch({ breachOnly })}
          />
          <Label htmlFor="price-breach-only" className="text-sm font-normal">
            Chỉ mã ngoài ngưỡng
          </Label>
        </div>
      )}
    </div>
  )
}
