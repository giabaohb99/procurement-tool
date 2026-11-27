import DateRangePicker from '../DateRangePicker'
import MultiCheckSelect from '../MultiCheckSelect'
import type { PackagingCodeOption, PackagingHistoryMode, PackagingSupplierOption } from '../../api/packaging-cost-types'
import { PACKAGING_HISTORY_MAX_CODES, type HistoryFilters, type HistorySelection } from '../../utils/packaging-query'
import PackagingCodePicker from './PackagingCodePicker'
import './packaging.css'

/**
 * Thanh chọn + lọc của màn Lịch sử mua hàng. Hàng 1: chế độ (theo mã VTBB / theo mã sản phẩm) + ô chọn nhiều mã
 * (để trống = tất cả). Hàng 2: ô tìm, nhà cung cấp, khoảng ngày mua. Lựa chọn mã nằm ở URL (do trang giữ), bộ lọc còn
 * lại ở state trang.
 */
export default function PackagingHistoryToolbar({
  selection, onSelection, filters, onFilters, codeOptions, productOptions, optionsLoading, suppliers,
}: {
  selection: HistorySelection
  onSelection: (s: HistorySelection) => void
  filters: HistoryFilters
  onFilters: (f: HistoryFilters) => void
  /** Mã VTBB cho ô chọn của chế độ mã; sản phẩm (`code` = mã HH) cho chế độ sản phẩm. */
  codeOptions: PackagingCodeOption[]
  productOptions: PackagingCodeOption[]
  optionsLoading: boolean
  suppliers: PackagingSupplierOption[]
}) {
  const patch = (next: Partial<HistoryFilters>) => onFilters({ ...filters, ...next })
  const isProduct = selection.mode === 'product'
  const setMode = (mode: PackagingHistoryMode) => onSelection({ ...selection, mode })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/*  MỘT hàng (27/11/2026, "input hơi mập"): chế độ · ô chọn mã kiểu gọn · nhà cung cấp · khoảng ngày; hẹp thì xuống dòng. */}
      <div className="pkg-row">
        <div className="pkg-seg" role="group" aria-label="Chế độ chọn" style={{ height: 38, alignItems: 'stretch' }}>
          <button className={!isProduct ? 'on' : ''} style={{ height: 'auto' }} onClick={() => setMode('code')}>Theo mã VTBB</button>
          <button className={isProduct ? 'on' : ''} style={{ height: 'auto' }} onClick={() => setMode('product')}>Theo mã sản phẩm</button>
        </div>
        <div style={{ flex: 1, minWidth: 300 }}>
          {isProduct ? (
            <PackagingCodePicker kind="product" options={productOptions} value={selection.fg}
              onChange={(fg) => onSelection({ ...selection, fg })} loading={optionsLoading} maxCodes={PACKAGING_HISTORY_MAX_CODES}
              emptyPlaceholder="Tất cả sản phẩm có định mức — gõ để chọn sản phẩm cụ thể" compact />
          ) : (
            <PackagingCodePicker options={codeOptions} value={selection.codes}
              onChange={(codes) => onSelection({ ...selection, codes })} loading={optionsLoading} maxCodes={PACKAGING_HISTORY_MAX_CODES}
              emptyPlaceholder="Tất cả mã VTBB — gõ mã, tên, nhóm hoặc NCC để chọn mã cụ thể" compact />
          )}
        </div>
        {/*  Ô tìm chữ thứ hai bỏ 27/11/2026: ô chọn mã đã tìm theo mã, tên, nhóm và tên NCC. */}
        <div style={{ width: 230 }}>
          <MultiCheckSelect value={filters.suppliers} placeholder="Nhà cung cấp"
            options={suppliers.map((s) => ({ value: s.code, label: s.name, hint: s.code }))} onChange={(v) => patch({ suppliers: v })} />
        </div>
        <div style={{ width: 250 }}>
          <DateRangePicker block value={{ from: filters.from, to: filters.to }} placeholder="Khoảng ngày mua"
            onChange={(v) => patch({ from: v.from, to: v.to })} />
        </div>
      </div>
    </div>
  )
}
