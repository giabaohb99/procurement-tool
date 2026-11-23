/**
 * duoc-CR-784 — nút + hộp thoại nhỏ LỌC NÂNG CAO của bảng sản phẩm bị ảnh hưởng (màn Tác động giá).
 *
 * Không dùng bộ lọc điều kiện chung (`@/shared/conditional-filter`): bộ đó đẩy `field__op=value` lên URL cho các màn danh
 * sách GET, còn bảng này lọc bằng THÂN `POST /impact` với vài điều kiện cố định (xu hướng, vai trò của mã đã chọn, bốn khoảng
 * số, cảnh báo) — một biểu mẫu nhỏ dễ dùng hơn nhiều so với "chọn trường → chọn phép → nhập giá trị".
 *
 * Người dùng sửa trên BẢN NHÁP, bấm Áp dụng mới gửi máy chủ (gõ tới đâu gọi tới đó thì mỗi phím một lượt tính lại). Nút hiện
 * huy hiệu số nhóm điều kiện đang bật.
 */
import { Filter } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

import {
  EMPTY_IMPACT_FILTERS,
  IMPACT_FILTER_ROLES,
  IMPACT_RANGE_FIELDS,
  countImpactFilters,
  invalidImpactRanges,
  type ImpactAdvancedFilters,
  type ImpactRangeKey,
} from '../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS } from '../utils/packaging-product-overview'
import { packagingRoleLabel } from '../utils/packaging-warning-text'

interface PackagingImpactAdvancedFilterProps {
  /** Bộ lọc đang áp. */
  value: ImpactAdvancedFilters
  onApply: (next: ImpactAdvancedFilters) => void
}

const CHIP = 'h-8 rounded-full border px-3 text-sm hover:bg-accent'
const CHIP_ON = 'border-primary bg-primary text-primary-foreground hover:bg-primary/90'

export function PackagingImpactAdvancedFilter({ value, onApply }: PackagingImpactAdvancedFilterProps) {
  const [open, setOpen] = useState(false)
  const count = countImpactFilters(value)
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" aria-label="Lọc nâng cao">
          <Filter />
          Lọc nâng cao
          {count > 0 && (
            <span className="ml-1 inline-flex min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-semibold text-primary-foreground">
              {count}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        collisionPadding={8}
        //  Cao hơn chỗ trống của màn thì cuộn trong hộp, không bị cắt mép trên.
        className="max-h-(--radix-popover-content-available-height) w-[30rem] max-w-[calc(100vw-2rem)] space-y-4 overflow-y-auto"
      >
        {/*  Nội dung chỉ dựng khi mở → bản nháp luôn khởi tạo lại từ bộ lọc đang áp. */}
        <FilterForm
          initial={value}
          onApply={(next) => {
            onApply(next)
            setOpen(false)
          }}
        />
      </PopoverContent>
    </Popover>
  )
}

function FilterForm({
  initial,
  onApply,
}: {
  initial: ImpactAdvancedFilters
  onApply: (next: ImpactAdvancedFilters) => void
}) {
  const [draft, setDraft] = useState<ImpactAdvancedFilters>(initial)
  const bad = invalidImpactRanges(draft)

  const toggleRole = (role: number) =>
    setDraft((prev) => ({
      ...prev,
      roles: prev.roles.includes(role) ? prev.roles.filter((r) => r !== role) : [...prev.roles, role],
    }))
  const setRange = (key: ImpactRangeKey, side: 'min' | 'max', text: string) =>
    setDraft((prev) => ({ ...prev, [key]: { ...prev[key], [side]: text } }))

  return (
    <>
      <section className="space-y-1.5">
        <Label>Xu hướng chi phí</Label>
        <div className="flex flex-wrap gap-1" role="group" aria-label="Xu hướng chi phí">
          {OVERVIEW_TREND_CHIPS.map((chip) => (
            <button
              key={chip.value}
              type="button"
              title={chip.title}
              aria-pressed={draft.trend === chip.value}
              onClick={() => setDraft((prev) => ({ ...prev, trend: chip.value }))}
              className={cn(CHIP, draft.trend === chip.value && CHIP_ON)}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-1.5">
        <Label>Có mã đã chọn ở vai trò</Label>
        <div className="flex flex-wrap gap-1" role="group" aria-label="Vai trò của mã đã chọn">
          {IMPACT_FILTER_ROLES.map((role) => (
            <button
              key={role}
              type="button"
              aria-pressed={draft.roles.includes(role)}
              onClick={() => toggleRole(role)}
              className={cn(CHIP, draft.roles.includes(role) && CHIP_ON)}
            >
              {packagingRoleLabel(role)}
            </button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Chọn nhiều vai trò = sản phẩm có mã đã chọn ở một trong các vai trò đó.
        </p>
      </section>

      <section className="space-y-2">
        {IMPACT_RANGE_FIELDS.map(({ key, label, unit }) => (
          <div key={key} className="grid grid-cols-[11rem_1fr_1fr] items-center gap-2">
            <Label className="text-sm leading-tight">
              {label}{' '}
              {unit && <span className="text-xs font-normal text-muted-foreground">({unit})</span>}
            </Label>
            {(['min', 'max'] as const).map((side) => (
              <Input
                key={side}
                inputMode="decimal"
                className="h-8 text-right"
                aria-label={`${label} ${side === 'min' ? 'từ' : 'đến'}`}
                aria-invalid={bad.includes(key)}
                placeholder={side === 'min' ? 'Từ' : 'Đến'}
                value={draft[key][side]}
                onChange={(event) => setRange(key, side, event.target.value)}
              />
            ))}
            {bad.includes(key) && (
              <p role="alert" className="col-span-3 text-xs text-destructive">
                &quot;Từ&quot; không được lớn hơn &quot;Đến&quot; — điều kiện này chưa được áp dụng.
              </p>
            )}
          </div>
        ))}
      </section>

      <label className="flex cursor-pointer items-start gap-2 text-sm">
        <Checkbox
          className="mt-0.5"
          checked={draft.warningsOnly}
          onCheckedChange={(checked) => setDraft((prev) => ({ ...prev, warningsOnly: checked === true }))}
        />
        <span>
          Chỉ sản phẩm có cảnh báo
          <span className="block text-xs text-muted-foreground">
            Thiếu giá / mã thành phần, thiếu quy cách thùng, lệch ĐVT, dưới sàn hoặc vượt trần.
          </span>
        </span>
      </label>

      <div className="flex items-center justify-between gap-2 border-t pt-3">
        <Button type="button" variant="ghost" onClick={() => setDraft(EMPTY_IMPACT_FILTERS)}>
          Xóa lọc
        </Button>
        <Button type="button" onClick={() => onApply(draft)}>
          Áp dụng
        </Button>
      </div>
    </>
  )
}
