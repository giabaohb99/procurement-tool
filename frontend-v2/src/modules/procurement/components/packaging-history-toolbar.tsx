/**
 * duoc-CR-784 — thanh chọn + lọc của tab Lịch sử mua hàng.
 *
 * Một hàng (27/11/2026): chế độ (theo mã VTBB / theo mã sản phẩm) · ô chọn nhiều mã kiểu gọn (dùng lại `PackagingCodePicker`;
 * để trống = tất cả) · nhà cung cấp · khoảng ngày mua. Ô tìm chữ thứ hai bỏ 27/11/2026 vì ô chọn mã đã tìm theo mã, tên, nhóm và
 * tên NCC. Lựa chọn mã nằm ở URL (do trang giữ), bộ lọc còn lại ở state trang.
 */
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

import type {
  PackagingCodeOption,
  PackagingHistoryMode,
  PackagingLastPricesSupplier,
} from '../types/packaging-cost-types'
import {
  PACKAGING_HISTORY_MAX_CODES,
  type PackagingHistoryFilters,
  type PackagingHistorySelection,
} from '../utils/packaging-history'
import { PackagingCodePicker } from './packaging-code-picker'

interface PackagingHistoryToolbarProps {
  selection: PackagingHistorySelection
  onSelectionChange: (selection: PackagingHistorySelection) => void
  filters: PackagingHistoryFilters
  onFiltersChange: (filters: PackagingHistoryFilters) => void
  /** Mã VTBB cho ô chọn của chế độ mã; sản phẩm (`code` = mã HH) cho chế độ sản phẩm. */
  codeOptions: PackagingCodeOption[]
  productOptions: PackagingCodeOption[]
  optionsLoading: boolean
  suppliers: PackagingLastPricesSupplier[]
}

export function PackagingHistoryToolbar({
  selection,
  onSelectionChange,
  filters,
  onFiltersChange,
  codeOptions,
  productOptions,
  optionsLoading,
  suppliers,
}: PackagingHistoryToolbarProps) {
  const patch = (next: Partial<PackagingHistoryFilters>) => onFiltersChange({ ...filters, ...next })
  const isProduct = selection.mode === 'product'

  return (
    <div className="flex w-full flex-col gap-2">
      {/*  MỘT hàng (27/11/2026, "input hơi mập"): chế độ · ô chọn mã kiểu gọn · nhà cung cấp · khoảng ngày; hẹp thì xuống dòng. */}
      <div className="flex flex-wrap items-center gap-2">
        <ToggleGroup
          type="single"
          variant="outline"
          value={selection.mode}
          onValueChange={(value) =>
            value && onSelectionChange({ ...selection, mode: value as PackagingHistoryMode })
          }
          aria-label="Chế độ chọn"
          className="h-9 shrink-0"
        >
          <ToggleGroupItem value="code">Theo mã VTBB</ToggleGroupItem>
          <ToggleGroupItem value="product">Theo mã sản phẩm</ToggleGroupItem>
        </ToggleGroup>
        <div className="min-w-72 flex-1">
          {isProduct ? (
            <PackagingCodePicker
              kind="product"
              options={productOptions}
              value={selection.fg}
              onChange={(fg) => onSelectionChange({ ...selection, fg })}
              loading={optionsLoading}
              maxCodes={PACKAGING_HISTORY_MAX_CODES}
              emptyPlaceholder="Tất cả sản phẩm có định mức — gõ để chọn sản phẩm cụ thể"
              compact
            />
          ) : (
            <PackagingCodePicker
              options={codeOptions}
              value={selection.codes}
              onChange={(codes) => onSelectionChange({ ...selection, codes })}
              loading={optionsLoading}
              maxCodes={PACKAGING_HISTORY_MAX_CODES}
              emptyPlaceholder="Tất cả mã VTBB — gõ mã, tên, nhóm hoặc NCC để chọn mã cụ thể"
              compact
            />
          )}
        </div>
        <div className="w-56">
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
      </div>
    </div>
  )
}
