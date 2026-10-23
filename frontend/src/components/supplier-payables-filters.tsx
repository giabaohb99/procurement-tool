import SearchSelect from './SearchSelect'
import DateRangePicker from './DateRangePicker'
import FilterPanel, { FilterItem } from './FilterPanel'
import { ConditionalFilterButton } from './conditional-filter'
import { AGING_ORDER, agingLabel, EMPTY_PAYABLE_FILTERS, hasFilter, PayableFilters } from './supplier-payables-stats'

/**
 * Thanh lọc tab "Công nợ" của NCC — chỉ giữ 3 ô đọc báo cáo hay dùng nhất
 * (xem nhanh / tuổi nợ / khoảng ngày phát sinh). Mã PO, số hóa đơn, loại nợ, trạng thái
 * nằm trong BỘ LỌC ĐIỀU KIỆN (nút bên phải) để thanh lọc khỏi dài.
 */

const VIEW_OPTIONS = [
  { value: 'open', label: 'Còn phải trả' },
  { value: 'overdue', label: 'Đang quá hạn' },
  { value: 'credit', label: 'Trả dư / ghi có' },
]

export default function SupplierPayablesFilters({
  value, onChange, shown, loaded,
}: {
  value: PayableFilters
  onChange: (f: PayableFilters) => void
  shown: number     // số khoản sau khi áp "Xem nhanh"
  loaded: number    // số khoản API trả về theo các điều kiện còn lại
}) {
  const set = (k: keyof PayableFilters, v: string) => onChange({ ...value, [k]: v })

  return (
    <FilterPanel canClear={hasFilter(value)} onClear={() => onChange({ ...EMPTY_PAYABLE_FILTERS })}
      extra={<>
        <ConditionalFilterButton />
        <span style={{ fontSize: 12.5, color: 'var(--muted)', alignSelf: 'center' }}>
          Đang xem <b style={{ color: 'var(--navy)' }}>{shown}</b>{shown !== loaded ? `/${loaded}` : ''} khoản
        </span>
      </>}>
      <FilterItem label="Xem nhanh">
        <SearchSelect value={value.view} placeholder="Tất cả khoản nợ" options={VIEW_OPTIONS} onChange={(v) => set('view', v)} />
      </FilterItem>
      <FilterItem label="Tuổi nợ">
        <SearchSelect value={value.aging} placeholder="Tất cả"
          options={AGING_ORDER.map((a) => ({ value: a, label: agingLabel(a) }))}
          onChange={(v) => set('aging', v)} />
      </FilterItem>
      <FilterItem label="Ngày phát sinh" width={250}>
        <DateRangePicker block value={{ from: value.from, to: value.to }}
          onChange={(v) => onChange({ ...value, from: v.from, to: v.to })} />
      </FilterItem>
    </FilterPanel>
  )
}
