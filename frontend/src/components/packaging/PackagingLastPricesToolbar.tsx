import DateRangePicker from '../DateRangePicker'
import MultiCheckSelect from '../MultiCheckSelect'
import NumberInput from '../NumberInput'
import type { LastPricesTrend, PackagingLastPricesResult } from '../../api/packaging-cost-types'
import { LAST_PRICE_N_OPTIONS, type LastPricesFilters } from '../../utils/packaging-query'
import './packaging.css'

const TRENDS: [LastPricesTrend, string][] = [['all', 'Tất cả'], ['up', 'Tăng'], ['down', 'Giảm'], ['flat', 'Không đổi']]

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="pkg-field"><span>{label}</span>{children}</div>
}

function Toggle({ label, checked, onChange, title }: { label: string; checked: boolean; onChange: (v: boolean) => void; title?: string }) {
  return (
    <label className="pkg-switch" title={title}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />{label}
    </label>
  )
}

/**
 * Thanh lọc của màn Giá mua gần nhất. Mọi tùy chọn gửi máy chủ (và theo Xuất Excel), trừ "Hiện số lượng" chỉ đổi cột hiện.
 * Hàng 1: ô tìm + chip nhóm (kèm số mã). Hàng 2: số lần hiển thị, phạm vi mã, nhà cung cấp, khoảng ngày mua, biến động,
 * ngưỡng %. Hàng 3: các công tắc. Lọc nhà cung cấp GIỮ DÒNG có nhà cung cấp đó trong n lần đang hiện (không cắt bớt lần mua).
 */
export default function PackagingLastPricesToolbar({
  filters, onChange, groups, suppliers,
}: {
  filters: LastPricesFilters
  onChange: (next: LastPricesFilters) => void
  groups: PackagingLastPricesResult['groups']
  suppliers: PackagingLastPricesResult['suppliers']
}) {
  const patch = (next: Partial<LastPricesFilters>) => onChange({ ...filters, ...next })
  const total = groups.reduce((s, g) => s + g.count, 0)
  const chips = [{ group: '', label: `Tất cả (${total})` }, ...groups.map((g) => ({ group: g.group, label: `${g.group} (${g.count})` }))]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '14px 0 10px' }}>
      <div className="pkg-row">
        <div className="pkg-search">
          <input aria-label="Tìm mã vật tư" placeholder="Tìm mã, tên, nhóm, nhà cung cấp…" value={filters.q} onChange={(e) => patch({ q: e.target.value })} />
        </div>
        <div className="pkg-pills" role="group" aria-label="Lọc theo nhóm">
          {chips.map((c) => (
            <button key={c.group || 'all'} type="button" className={'pkg-pill' + (filters.group === c.group ? ' on' : '')}
              aria-pressed={filters.group === c.group} onClick={() => patch({ group: c.group })}>{c.label}</button>
          ))}
        </div>
      </div>

      <div className="pkg-row">
        <Field label="Số lần hiển thị">
          <div className="pkg-seg" role="group" aria-label="Số lần hiển thị">
            {LAST_PRICE_N_OPTIONS.map((n) => (
              <button key={n} className={filters.n === n ? 'on' : ''} onClick={() => patch({ n })}>{n} lần</button>
            ))}
          </div>
        </Field>
        <Field label="Phạm vi mã">
          <div className="pkg-seg" role="group" aria-label="Phạm vi mã">
            <button className={filters.scope === 'bom' ? 'on' : ''} onClick={() => patch({ scope: 'bom' })}>Định mức + báo giá</button>
            <button className={filters.scope === 'all' ? 'on' : ''} onClick={() => patch({ scope: 'all' })}>Mọi mã</button>
          </div>
        </Field>
        <div style={{ width: 230 }} title="Giữ các mã có nhà cung cấp này trong các lần mua đang hiện">
          <MultiCheckSelect value={filters.suppliers} placeholder="Nhà cung cấp"
            options={suppliers.map((s) => ({ value: s.code, label: s.name }))}
            onChange={(v) => patch({ suppliers: v })} />
        </div>
        <div style={{ width: 250 }}>
          <DateRangePicker block value={{ from: filters.from, to: filters.to }} placeholder="Khoảng ngày mua"
            onChange={(v) => patch({ from: v.from, to: v.to })} />
        </div>
        <Field label="Biến động lần 1 so lần 2">
          <div className="pkg-seg" role="group" aria-label="Biến động lần 1 so lần 2">
            {TRENDS.map(([v, label]) => (
              <button key={v} className={filters.trend === v ? 'on' : ''} onClick={() => patch({ trend: v })}>{label}</button>
            ))}
          </div>
        </Field>
        <Field label="Biến động từ (%)">
          <NumberInput style={{ width: 80, height: 32, padding: '0 8px' }} value={filters.minPct} maxDecimals={2}
            onChange={(minPct) => patch({ minPct })} />
        </Field>
      </div>

      <div className="pkg-row">
        <Toggle label="Chỉ mã đã có giá" checked={filters.onlyPriced} onChange={(onlyPriced) => patch({ onlyPriced })} />
        <Toggle label="Chỉ mã đang dùng trong định mức" checked={filters.bomOnly} onChange={(bomOnly) => patch({ bomOnly })} />
        <Toggle label="Hiện số lượng" checked={filters.showQty} onChange={(showQty) => patch({ showQty })} />
        <span className="pkg-hint">Đơn giá chưa VAT, đơn vị VND. Xanh = đắt hơn lần mua trước đó, đỏ = rẻ hơn.</span>
      </div>
    </div>
  )
}
