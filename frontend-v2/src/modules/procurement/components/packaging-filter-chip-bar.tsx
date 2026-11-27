/**
 * duoc-CR-784 — THANH LỌC DẠNG CHIP của hai màn Tác động giá bao bì và Tổng hợp theo sản phẩm (thay hộp "Lọc nâng cao",
 * người chủ chốt 26/11/2026: "cái bộ lọc khó xài quá"). Một hàng: ô tìm + nút "Thêm điều kiện" (menu các trường chưa bật) +
 * phần riêng của màn (`children`: chip xu hướng kèm số đếm / dòng "Đang lọc"). Hàng thứ hai chỉ hiện khi có điều kiện:
 * mỗi điều kiện đang bật là một chip ghi câu tóm tắt; bấm chip = sửa ngay tại chỗ, nút x = bỏ.
 *
 * Lọc NGAY (không có nút Áp dụng); khoảng số đợi 400 ms sau phím cuối (xem `packaging-filter-condition-editor.tsx`). Trạng thái
 * vẫn là `ImpactAdvancedFilters` nên thân `POST /impact`, tham số `GET /product-overview` và bản in không đổi.
 *
 * Đặt làm `toolbar` của `DataTable`: hàng một dùng `order-1`, hàng chip `order-4 basis-full`; màn phải truyền
 * `toolbarActionsClassName="order-2"` để nhóm nút Tải lại / Cột đứng cùng hàng một thay vì tụt xuống dưới hàng chip.
 *
 * Khổ điện thoại (< 768px, bảng thành thẻ): hàng một chỉ còn ô tìm (giãn hết chỗ) + nút "Thêm điều kiện" dạng biểu tượng,
 * để cụm Xếp theo / Tải lại đứng CÙNG hàng; phần riêng của màn (`children`) xuống hàng riêng `order-3` — người chủ chê
 * dải trống khi cụm nút đứng một mình một hàng (26/11/2026).
 */
import { ChevronDown, ListFilter, Plus, X } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

import {
  ADVANCED_FILTER_PROFILES,
  WARNINGS_ONLY_HINT,
  clearCondition,
  conditionLabel,
  isConditionActive,
  summarizeCondition,
  type AdvancedFilterVariant,
  type FilterConditionKey,
  type ImpactAdvancedFilters,
} from '../utils/packaging-impact-filters'
import { PackagingFilterConditionEditor } from './packaging-filter-condition-editor'
import { PackagingKeywordSuggestInput } from './packaging-keyword-suggest-input'

interface PackagingFilterChipBarProps {
  variant: AdvancedFilterVariant
  /** Bộ lọc đang áp. */
  value: ImpactAdvancedFilters
  onChange: (next: ImpactAdvancedFilters) => void
  keyword: string
  onKeywordChange: (value: string) => void
  /** Phần riêng của màn, đứng sau nút "Thêm điều kiện" trên hàng một. */
  children?: ReactNode
}

export function PackagingFilterChipBar({
  variant,
  value,
  onChange,
  keyword,
  onKeywordChange,
  children,
}: PackagingFilterChipBarProps) {
  //  Điều kiện vừa thêm / đang sửa. Chưa nhập gì thì vẫn hiện chip (để hộp sửa neo vào), đóng hộp mà còn trống thì chip biến mất.
  const [editing, setEditing] = useState<FilterConditionKey | null>(null)
  const isMobile = useIsMobile()
  const order = ADVANCED_FILTER_PROFILES[variant].conditionOrder
  const chips = order.filter((key) => isConditionActive(value, key) || key === editing)
  const addable = order.filter((key) => !chips.includes(key))

  const addCondition = (key: FilterConditionKey) => {
    //  Cờ bật/tắt không cần chỗ nhập: thêm là lọc luôn.
    if (key === 'warningsOnly') onChange({ ...value, warningsOnly: true })
    else setEditing(key)
  }
  const removeCondition = (key: FilterConditionKey) => {
    if (editing === key) setEditing(null)
    onChange(clearCondition(value, key))
  }

  return (
    <>
      {/*  `flex-[1_1_24rem]`: hàng này chiếm phần còn lại để Tải lại / Cột đứng CÙNG hàng bên phải; hẹp hơn 24rem thì cả
           cụm xuống dòng thay vì bóp ô tìm. */}
      <div
        className={cn(
          'order-1 flex min-w-0 items-center gap-2',
          isMobile ? 'flex-[1_1_10rem]' : 'flex-[1_1_24rem] flex-wrap',
        )}
      >
        {/*  Ô tìm có gợi ý sản phẩm / mã thành phần (27/11/2026). */}
        <PackagingKeywordSuggestInput
          value={keyword}
          onChange={onKeywordChange}
          className={isMobile ? 'min-w-0 flex-1' : 'w-72 max-w-full'}
        />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            {isMobile ? (
              <Button
                type="button"
                variant="outline"
                size="icon"
                aria-label="Thêm điều kiện"
                title="Thêm điều kiện"
                disabled={addable.length === 0}
              >
                <ListFilter />
              </Button>
            ) : (
              <Button type="button" variant="outline" disabled={addable.length === 0}>
                <Plus />
                Thêm điều kiện
                <ChevronDown />
              </Button>
            )}
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="start"
            //  Trả tiêu điểm về nút sẽ giật hộp sửa vừa mở của chip mới → để hộp sửa tự nhận tiêu điểm.
            onCloseAutoFocus={(event) => event.preventDefault()}
          >
            {addable.map((key) => (
              <DropdownMenuItem key={key} onSelect={() => addCondition(key)}>
                <span className="flex flex-col">
                  {conditionLabel(key, variant)}
                  {key === 'warningsOnly' && (
                    <span className="max-w-64 text-xs whitespace-normal text-muted-foreground">
                      {WARNINGS_ONLY_HINT}
                    </span>
                  )}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        {!isMobile && children}
      </div>

      {isMobile && children && (
        <div className="order-3 flex basis-full flex-wrap items-center gap-2">{children}</div>
      )}

      {chips.length > 0 && (
        <div
          className="order-4 flex basis-full flex-wrap items-center gap-2"
          role="group"
          aria-label="Điều kiện lọc đang bật"
        >
          {chips.map((key) => (
            <ConditionChip
              key={key}
              conditionKey={key}
              variant={variant}
              value={value}
              open={editing === key}
              onOpenChange={(open) => setEditing(open ? key : null)}
              onChange={onChange}
              onRemove={() => removeCondition(key)}
            />
          ))}
        </div>
      )}
    </>
  )
}

interface ConditionChipProps {
  conditionKey: FilterConditionKey
  variant: AdvancedFilterVariant
  value: ImpactAdvancedFilters
  open: boolean
  onOpenChange: (open: boolean) => void
  onChange: (next: ImpactAdvancedFilters) => void
  onRemove: () => void
}

const CHIP_SHELL = 'inline-flex h-8 items-center rounded-full border border-primary/40 bg-primary/10 text-sm'
const CHIP_BODY = 'h-full rounded-l-full pr-1 pl-3 hover:bg-primary/15'

function ConditionChip({
  conditionKey,
  variant,
  value,
  open,
  onOpenChange,
  onChange,
  onRemove,
}: ConditionChipProps) {
  const label = conditionLabel(conditionKey, variant)
  const text = summarizeCondition(value, conditionKey)
  const removeButton = (
    <button
      type="button"
      aria-label={`Bỏ điều kiện ${label}`}
      title="Bỏ điều kiện"
      onClick={onRemove}
      className="h-full rounded-r-full pr-2 pl-1 text-muted-foreground hover:text-destructive"
    >
      <X className="size-3.5" />
    </button>
  )

  //  Cờ cảnh báo không có gì để sửa: chip chỉ là nhãn + nút bỏ.
  if (conditionKey === 'warningsOnly') {
    return (
      <span className={CHIP_SHELL} title={WARNINGS_ONLY_HINT}>
        <span className="pr-1 pl-3">{text}</span>
        {removeButton}
      </span>
    )
  }

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <span className={cn(CHIP_SHELL, open && 'border-primary')}>
        <PopoverTrigger asChild>
          <button type="button" aria-label={`Sửa điều kiện: ${text}`} className={CHIP_BODY}>
            {text}
          </button>
        </PopoverTrigger>
        {removeButton}
      </span>
      <PopoverContent align="start" collisionPadding={8} className="w-80 max-w-[calc(100vw-2rem)]">
        <PackagingFilterConditionEditor
          conditionKey={conditionKey}
          variant={variant}
          value={value}
          onChange={onChange}
          onClose={() => onOpenChange(false)}
        />
      </PopoverContent>
    </Popover>
  )
}
