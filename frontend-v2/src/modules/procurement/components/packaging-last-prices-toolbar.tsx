/**
 * duoc-CR-784 — thanh lọc của tab Giá mua gần nhất. Mọi tùy chọn gửi máy chủ (và theo Xuất Excel), trừ "Hiện số lượng"
 * chỉ đổi cột hiện (Excel thêm cột theo cờ `show_qty` cùng giá trị).
 *
 * Hàng 1: ô tìm + chip nhóm (kèm số mã; bấm bật / tắt, bật nhiều nhóm cùng lúc = HOẶC, không chip nào bật = mọi nhóm).
 * Hàng 2: số lần hiển thị, phạm vi mã, nhà cung cấp, khoảng ngày mua, biến động,
 * ngưỡng %, và các công tắc. Lọc nhà cung cấp GIỮ DÒNG có nhà cung cấp đó trong n lần đang hiện (không cắt bớt lần mua).
 */
import { ChevronDown, Search } from 'lucide-react'
import { useState } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'

import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { NumberInput } from '@/shared/ui/number-input'
import { Switch } from '@/shared/ui/switch'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'
import { cn } from '@/shared/utils/cn'

import type {
  LastPricesTrend,
  PackagingLastPricesGroup,
  PackagingLastPricesSupplier,
} from '../types/packaging-cost-types'
import { LAST_PRICE_DEFAULT_N, LAST_PRICE_N_OPTIONS } from '../utils/packaging-last-prices'

export interface LastPricesFilters {
  q: string
  /** Tên các nhóm đang bật (chip); rỗng = mọi nhóm. */
  groups: string[]
  n: number
  scope: 'bom' | 'all'
  /** Mã nhà cung cấp đã chọn; rỗng = không lọc. */
  suppliers: string[]
  from: string
  to: string
  trend: LastPricesTrend
  /** |biến động lần 1 so lần 2| tối thiểu (%); 0 = không lọc. */
  minPct: number
  onlyPriced: boolean
  bomOnly: boolean
  showQty: boolean
}

/** Số tùy chọn hàng 2–3 đang khác mặc định — hiện trên nút "Lọc thêm" khi đã gập ở khổ điện thoại. */
function countExtraOptions(filters: LastPricesFilters): number {
  return [
    filters.n !== LAST_PRICE_DEFAULT_N,
    filters.scope !== 'all',
    filters.suppliers.length > 0,
    Boolean(filters.from || filters.to),
    filters.trend !== 'all',
    filters.minPct > 0,
    filters.onlyPriced,
    filters.bomOnly,
    filters.showQty,
  ].filter(Boolean).length
}

const TREND_LABELS: [LastPricesTrend, string][] = [
  ['up', 'Tăng'],
  ['down', 'Giảm'],
  ['flat', 'Không đổi'],
]

interface PackagingLastPricesToolbarProps {
  filters: LastPricesFilters
  groups: PackagingLastPricesGroup[]
  suppliers: PackagingLastPricesSupplier[]
  onChange: (filters: LastPricesFilters) => void
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    //  `flex-wrap`: ở khổ điện thoại nhãn dài ("Biến động lần 1 so lần 2") + bốn nút không vừa một hàng — nhóm nút xuống
    //  dưới nhãn chứ không tràn ngang cả trang.
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-sm whitespace-nowrap text-muted-foreground">{label}</span>
      {children}
    </div>
  )
}

function Toggle({
  id,
  label,
  checked,
  onChange,
  title,
}: {
  id: string
  label: string
  checked: boolean
  onChange: (value: boolean) => void
  title?: string
}) {
  return (
    <div className="flex items-center gap-2" title={title}>
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
      <Label htmlFor={id} className="text-sm font-normal">
        {label}
      </Label>
    </div>
  )
}

export function PackagingLastPricesToolbar({
  filters,
  groups,
  suppliers,
  onChange,
}: PackagingLastPricesToolbarProps) {
  const patch = (next: Partial<LastPricesFilters>) => onChange({ ...filters, ...next })
  //  Khổ điện thoại: hàng 2–3 (mười tùy chọn) cao gần trọn màn, đẩy danh sách xuống dưới nếp gấp — gập lại sau nút
  //  "Lọc thêm". Màn rộng luôn mở như cũ.
  const isMobile = useIsMobile()
  const [expanded, setExpanded] = useState(false)
  const showExtra = !isMobile || expanded
  const extraCount = countExtraOptions(filters)
  //  Chip bật / tắt từng nhóm (không có chip "Tất cả"): tên nhóm đã bật mà không còn chip nào (số đếm về 0) vẫn hiện để tắt được.
  const chips = [
    ...groups.map((item) => ({ group: item.group, label: `${item.group} (${item.count})` })),
    ...filters.groups
      .filter((name) => !groups.some((item) => item.group === name))
      .map((name) => ({ group: name, label: `${name} (0)` })),
  ]
  const toggleGroup = (name: string) =>
    patch({
      groups: filters.groups.includes(name)
        ? filters.groups.filter((item) => item !== name)
        : [...filters.groups, name],
    })

  return (
    <div className="flex w-full flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative w-full max-w-xs">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            aria-label="Tìm mã vật tư"
            placeholder="Tìm mã, tên, nhóm, nhà cung cấp…"
            value={filters.q}
            onChange={(event) => patch({ q: event.target.value })}
          />
        </div>
        <div className="flex flex-wrap gap-1" role="group" aria-label="Lọc theo nhóm">
          {chips.map((chip) => (
            <button
              key={chip.group}
              type="button"
              aria-pressed={filters.groups.includes(chip.group)}
              onClick={() => toggleGroup(chip.group)}
              className={cn(
                'h-8 rounded-full border px-3 text-sm hover:bg-accent',
                filters.groups.includes(chip.group) &&
                  'border-primary bg-primary text-primary-foreground hover:bg-primary/90',
              )}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {isMobile && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="w-fit"
          aria-expanded={expanded}
          onClick={() => setExpanded((open) => !open)}
        >
          {expanded ? 'Thu gọn bộ lọc' : 'Lọc thêm'}
          {!expanded && extraCount > 0 && ` (${extraCount})`}
          <ChevronDown className={cn('transition-transform', expanded && 'rotate-180')} />
        </Button>
      )}

      {showExtra && (
        <>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <Field label="Số lần hiển thị">
              <ToggleGroup
                type="single"
                variant="outline"
                size="sm"
                value={String(filters.n)}
                onValueChange={(value) => value && patch({ n: Number(value) })}
                aria-label="Số lần hiển thị"
              >
                {LAST_PRICE_N_OPTIONS.map((option) => (
                  <ToggleGroupItem key={option} value={String(option)}>
                    {option} lần
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </Field>
            <Field label="Phạm vi mã">
              <ToggleGroup
                type="single"
                variant="outline"
                size="sm"
                value={filters.scope}
                onValueChange={(value) => value && patch({ scope: value as 'bom' | 'all' })}
                aria-label="Phạm vi mã"
              >
                <ToggleGroupItem value="bom">Định mức + báo giá</ToggleGroupItem>
                <ToggleGroupItem value="all">Mọi mã</ToggleGroupItem>
              </ToggleGroup>
            </Field>
            <div className="w-56" title="Giữ các mã có nhà cung cấp này trong các lần mua đang hiện">
              <MultiPicker<string>
                value={filters.suppliers}
                onChange={(ids) => patch({ suppliers: ids })}
                options={suppliers.map((s) => ({ id: s.code, label: s.name, hint: s.code }))}
                placeholder="Nhà cung cấp"
                searchPlaceholder="Tìm nhà cung cấp…"
                emptyMessage="Không có nhà cung cấp nào."
                summaryInTrigger
                clearInTrigger
              />
            </div>
            <DateRangePicker
              from={filters.from}
              to={filters.to}
              placeholder="Khoảng ngày mua"
              onChange={(from, to) => patch({ from, to })}
            />
            <Field label="Biến động lần 1 so lần 2">
              <ToggleGroup
                type="single"
                variant="outline"
                size="sm"
                //  Bấm lại nút đang bật = tắt (về "không lọc"); `all` là giá trị nội bộ cho "chưa chọn".
                value={filters.trend === 'all' ? '' : filters.trend}
                onValueChange={(value) => patch({ trend: (value || 'all') as LastPricesTrend })}
                aria-label="Biến động lần 1 so lần 2"
              >
                {TREND_LABELS.map(([value, label]) => (
                  <ToggleGroupItem key={value} value={value}>
                    {label}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </Field>
            <Field label="Biến động từ (%)">
              <NumberInput
                aria-label="Ngưỡng biến động lần 1 so lần 2 (%)"
                title="Chỉ lấy mã có |biến động lần 1 so lần 2| từ ngưỡng này trở lên; 0 = không lọc"
                className="h-8 w-20"
                value={filters.minPct}
                maxDecimals={2}
                onChange={(minPct) => patch({ minPct })}
              />
            </Field>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <Toggle
              id="last-prices-only-priced"
              label="Chỉ mã đã có giá"
              checked={filters.onlyPriced}
              onChange={(onlyPriced) => patch({ onlyPriced })}
            />
            <Toggle
              id="last-prices-bom-only"
              label="Chỉ mã đang dùng trong định mức"
              checked={filters.bomOnly}
              onChange={(bomOnly) => patch({ bomOnly })}
            />
            <Toggle
              id="last-prices-show-qty"
              label="Hiện số lượng"
              checked={filters.showQty}
              onChange={(showQty) => patch({ showQty })}
            />
            <span className="text-xs text-muted-foreground">
              Xanh = đắt hơn lần mua trước đó, đỏ = rẻ hơn. VNĐ, chưa VAT.
            </span>
          </div>
        </>
      )}
    </div>
  )
}
