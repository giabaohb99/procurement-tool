/**
 * duoc-CR-784 — thanh lọc của tab Giá mua gần nhất. Mọi tùy chọn gửi máy chủ (và theo Xuất Excel), trừ "Hiện số lượng"
 * chỉ đổi cột hiện (Excel thêm cột theo cờ `show_qty` cùng giá trị).
 *
 * Bố cục ba hàng (27/11/2026). Hàng 1: bốn ô chọn — ô chọn nhiều MÃ (như màn Tác động, rộng gấp đôi), ô chọn nhiều NHÓM SẢN PHẨM (tick nhiều nhóm = HOẶC, không
 * tick nhóm nào = mọi nhóm, mỗi nhóm kèm số mã, dòng đầu là Tất cả; thay hàng chip vì prod có khoảng 42 nhóm), nhà cung cấp,
 * khoảng ngày mua. Hàng 2: số lần hiển thị, phạm vi mã, biến động, ngưỡng % rồi ba công tắc. Hàng 3: chú thích chữ nhỏ.
 * Lọc nhà cung cấp GIỮ DÒNG có nhà cung cấp đó trong n lần đang hiện (không cắt bớt lần mua).
 */
import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'

import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { NumberInput } from '@/shared/ui/number-input'
import { Switch } from '@/shared/ui/switch'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'
import { cn } from '@/shared/utils/cn'

import type {
  LastPricesTrend,
  PackagingCodeOption,
  PackagingLastPricesGroup,
  PackagingLastPricesSupplier,
} from '../types/packaging-cost-types'
import { LAST_PRICE_DEFAULT_N, LAST_PRICE_N_OPTIONS, RECENT_CODES_LIMIT } from '../utils/packaging-last-prices'
import { PackagingCodePicker } from './packaging-code-picker'

export interface LastPricesFilters {
  /** Mã VTBB chọn ở ô chọn mã (thay ô tìm chữ từ 27/11/2026); rỗng = mọi mã. */
  codes: string[]
  /** Tên các nhóm đang chọn; rỗng = mọi nhóm. */
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
  /** Đã bấm chip "Tất cả" (sáng): nạp mọi mã có phân trang. Không bật + không lọc gì = chế độ gần nhất (20 mã mua gần nhất). */
  all: boolean
  /** Cờ riêng của giao diện: nút "Tất cả" ở hàng Biến động sáng sau khi bấm (trend nội bộ vẫn là `all`). */
  trendAllLit: boolean
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
  /** Danh sách mã cho ô chọn mã (đã xếp, cùng nguồn màn Tác động). */
  codeOptions?: PackagingCodeOption[]
  codeOptionsLoading?: boolean
  onChange: (filters: LastPricesFilters) => void
  /** Đang ở chế độ gần nhất (chưa chọn nhóm / "Tất cả" / bộ lọc nào) — hiện chú thích 20 mã thay cho tổng số. */
  recentMode?: boolean
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

const ALL_TREND = '__all'
/** Dòng "Tất cả" đứng đầu ô Nhóm sản phẩm — không phải tên nhóm thật, chỉ là cờ `all` của bộ lọc. */
const ALL_GROUPS = '__all_groups'

export function PackagingLastPricesToolbar({
  filters,
  groups,
  suppliers,
  codeOptions = [],
  codeOptionsLoading = false,
  onChange,
  recentMode = false,
}: PackagingLastPricesToolbarProps) {
  const patch = (next: Partial<LastPricesFilters>) => onChange({ ...filters, ...next })
  //  Khổ điện thoại: hàng 2–3 (mười tùy chọn) cao gần trọn màn, đẩy danh sách xuống dưới nếp gấp — gập lại sau nút
  //  "Lọc thêm". Màn rộng luôn mở như cũ.
  const isMobile = useIsMobile()
  const [expanded, setExpanded] = useState(false)
  const showExtra = !isMobile || expanded
  const extraCount = countExtraOptions(filters)
  //  Mỗi nhóm một dòng tick, số mã nằm ở chữ phụ bên phải. Nhóm đã chọn mà số đếm về 0 (bộ lọc khác loại hết mã của nó)
  //  vẫn có dòng để bỏ tick được.
  const groupOptions = [
    { id: ALL_GROUPS, label: 'Tất cả' },
    ...groups.map((item) => ({ id: item.group, label: item.group, hint: String(item.count) })),
    ...filters.groups
      .filter((name) => !groups.some((item) => item.group === name))
      .map((name) => ({ id: name, label: name, hint: '0' })),
  ]
  //  "Tất cả" = bỏ mọi nhóm đang chọn và nạp hết mọi mã; chỉ được tick SAU KHI chọn (người chủ chốt 26/11/2026), mới mở thì
  //  không tick, màn ở chế độ gần nhất. Đang Tất cả mà tick thêm một nhóm = chuyển sang lọc theo nhóm đó (bỏ tick Tất cả).
  const changeGroups = (ids: string[]) => {
    if (ids.includes(ALL_GROUPS) && !filters.all) patch({ groups: [], all: true })
    else patch({ groups: ids.filter((id) => id !== ALL_GROUPS), all: false })
  }

  return (
    <div className="flex w-full flex-col gap-3">
      {/*  Hàng 1 (27/11/2026): bốn ô chọn đều nhau — tìm, nhóm, nhà cung cấp, khoảng ngày. Khổ điện thoại chỉ còn hai ô đầu,
          hai ô sau nằm trong phần "Lọc thêm". */}
      <div className="grid grid-cols-1 items-start gap-2 sm:grid-cols-2 xl:grid-cols-[2fr_1fr_1fr_1fr]">
        <PackagingCodePicker
          options={codeOptions}
          value={filters.codes}
          onChange={(codes) => patch({ codes })}
          loading={codeOptionsLoading}
          emptyPlaceholder="Tìm mã VTBB — gõ mã, tên hoặc tên nhóm, chọn được nhiều mã"
          compact
        />
        <div>
          <MultiPicker<string>
            value={filters.all ? [ALL_GROUPS] : filters.groups}
            onChange={changeGroups}
            options={groupOptions}
            placeholder="Nhóm sản phẩm"
            searchPlaceholder="Tìm nhóm…"
            emptyMessage="Không có nhóm nào."
            summaryInTrigger
            clearInTrigger
            //  Không có hàng "Chọn tất cả" của ô chọn: dòng "Tất cả" đầu danh sách đã làm việc đó (bỏ chọn nhóm, nạp hết mọi mã).
            hideSelectAll
          />
        </div>
        {showExtra && (
          <>
            <div title="Giữ các mã có nhà cung cấp này trong các lần mua đang hiện">
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
              className="w-full"
              onChange={(from, to) => patch({ from, to })}
            />
          </>
        )}
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
          {/*  Hàng 2: nhóm nút chọn một rồi các công tắc, chung một dòng chảy để màn vừa (khoảng 1100px) lấp đủ hai dòng thay vì
              ba dòng lửng. */}
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
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
            <Field label="Biến động lần 1 so lần 2">
              <ToggleGroup
                type="single"
                variant="outline"
                size="sm"
                //  Bấm lại nút đang bật = tắt (về "không lọc"); `all` là giá trị nội bộ cho "chưa chọn".
                value={filters.trend !== 'all' ? filters.trend : filters.trendAllLit ? ALL_TREND : ''}
                onValueChange={(value) =>
                  patch({
                    trend: (!value || value === ALL_TREND ? 'all' : value) as LastPricesTrend,
                    trendAllLit: value === ALL_TREND,
                  })
                }
                aria-label="Biến động lần 1 so lần 2"
              >
                {/*  "Tất cả" = bỏ lọc biến động; sáng sau khi bấm (cờ `trendAllLit`), mới mở thì chưa sáng. */}
                <ToggleGroupItem value={ALL_TREND}>Tất cả</ToggleGroupItem>
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
          </div>

          {/*  Hàng 3: một dòng chữ nhỏ căn trái — chú thích màu, và câu nhắc khi đang ở chế độ gần nhất. */}
          <p className="text-xs text-muted-foreground">
            Đỏ = đắt hơn lần mua trước đó, xanh = rẻ hơn. VNĐ, chưa VAT.
            {recentMode && (
              <> · {RECENT_CODES_LIMIT} mã mua gần nhất, chọn Tất cả ở ô Nhóm sản phẩm để xem hết.</>
            )}
          </p>
        </>
      )}
      {!showExtra && recentMode && (
        <span className="text-xs text-muted-foreground">
          {RECENT_CODES_LIMIT} mã mua gần nhất · chọn Tất cả ở ô Nhóm sản phẩm để xem hết
        </span>
      )}
    </div>
  )
}
