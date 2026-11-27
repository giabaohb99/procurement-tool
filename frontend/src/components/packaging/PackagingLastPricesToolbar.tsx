import DateRangePicker from '../DateRangePicker'
import MultiCheckSelect from '../MultiCheckSelect'
import NumberInput from '../NumberInput'
import type { LastPricesTrend, PackagingLastPricesResult } from '../../api/packaging-cost-types'
import { LAST_PRICE_N_OPTIONS, RECENT_CODES_LIMIT, type LastPricesFilters } from '../../utils/packaging-query'
import './packaging.css'

const TRENDS: [LastPricesTrend, string][] = [['up', 'Tăng'], ['down', 'Giảm'], ['flat', 'Không đổi']]
/** Dòng "Tất cả" đứng đầu ô Nhóm sản phẩm — không phải tên nhóm thật, chỉ là cờ `all` của bộ lọc. */
const ALL_GROUPS = '__all_groups'

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
 * Hàng 1: ô tìm + ô chọn nhiều NHÓM SẢN PHẨM (tick nhiều nhóm = HOẶC, không tick nhóm nào = mọi nhóm; số mã là chữ phụ), dòng
 * đầu danh sách là Tất cả — ô chọn thay hàng chip từ 27/11/2026 vì prod có khoảng 42 nhóm, chip chiếm bốn hàng. Hàng 2: số lần hiển thị, phạm vi mã, nhà cung cấp, khoảng ngày mua, biến động,
 * ngưỡng %. Hàng 3: các công tắc. Lọc nhà cung cấp GIỮ DÒNG có nhà cung cấp đó trong n lần đang hiện (không cắt bớt lần mua).
 */
export default function PackagingLastPricesToolbar({
  filters, onChange, groups, suppliers, recentMode = false,
}: {
  filters: LastPricesFilters
  onChange: (next: LastPricesFilters) => void
  groups: PackagingLastPricesResult['groups']
  suppliers: PackagingLastPricesResult['suppliers']
  /** Đang ở chế độ gần nhất (chưa chọn nhóm / "Tất cả" / bộ lọc nào) — hiện chú thích 20 mã thay cho tổng số. */
  recentMode?: boolean
}) {
  const patch = (next: Partial<LastPricesFilters>) => onChange({ ...filters, ...next })
  //  Mỗi nhóm một dòng tick, số mã là chữ phụ. Nhóm đã chọn mà số đếm về 0 (bộ lọc khác loại hết mã của nó) vẫn có dòng để bỏ tick.
  const groupOptions = [
    { value: ALL_GROUPS, label: 'Tất cả' },
    ...groups.map((g) => ({ value: g.group, label: g.group, hint: String(g.count) })),
    ...filters.groups.filter((name) => !groups.some((g) => g.group === name)).map((name) => ({ value: name, label: name, hint: '0' })),
  ]
  //  "Tất cả" = bỏ mọi nhóm đang chọn và nạp hết mọi mã; chỉ được tick SAU KHI chọn (người chủ chốt 26/11/2026), mới mở thì không
  //  tick, màn ở chế độ gần nhất. Đang Tất cả mà tick thêm một nhóm = chuyển sang lọc theo nhóm đó (bỏ tick Tất cả).
  const changeGroups = (v: string[]) => {
    if (v.includes(ALL_GROUPS) && !filters.all) patch({ groups: [], all: true })
    else patch({ groups: v.filter((g) => g !== ALL_GROUPS), all: false })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '14px 0 10px' }}>
      <div className="pkg-row">
        <div className="pkg-search">
          <input aria-label="Tìm mã vật tư" placeholder="Tìm mã, tên, nhóm, nhà cung cấp…" value={filters.q} onChange={(e) => patch({ q: e.target.value })} />
        </div>
        <div style={{ width: 230 }}>
          <MultiCheckSelect value={filters.all ? [ALL_GROUPS] : filters.groups} placeholder="Nhóm sản phẩm" options={groupOptions}
            onChange={changeGroups} />
        </div>
        {recentMode && <span className="pkg-hint">{RECENT_CODES_LIMIT} mã mua gần nhất · chọn Tất cả ở ô Nhóm sản phẩm để xem hết</span>}
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
            options={suppliers.map((s) => ({ value: s.code, label: s.name, hint: s.code }))}
            onChange={(v) => patch({ suppliers: v })} />
        </div>
        <div style={{ width: 250 }}>
          <DateRangePicker block value={{ from: filters.from, to: filters.to }} placeholder="Khoảng ngày mua"
            onChange={(v) => patch({ from: v.from, to: v.to })} />
        </div>
        <Field label="Biến động lần 1 so lần 2">
          <div className="pkg-seg" role="group" aria-label="Biến động lần 1 so lần 2">
            {/*  "Tất cả" = bỏ lọc biến động; sáng sau khi bấm (cờ `trendAllLit`), mới mở thì chưa sáng. */}
            <button type="button" className={filters.trend === 'all' && filters.trendAllLit ? 'on' : ''}
              aria-pressed={filters.trend === 'all' && filters.trendAllLit}
              onClick={() => patch({ trend: 'all', trendAllLit: true })}>Tất cả</button>
            {TRENDS.map(([v, label]) => (
              //  Bấm lại nút đang bật = tắt (về "không lọc"); `all` là giá trị nội bộ cho "chưa chọn".
              <button key={v} className={filters.trend === v ? 'on' : ''} aria-pressed={filters.trend === v}
                onClick={() => patch({ trend: filters.trend === v ? 'all' : v, trendAllLit: false })}>{label}</button>
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
        <span className="pkg-hint">Xanh = đắt hơn lần mua trước đó, đỏ = rẻ hơn. VNĐ, chưa VAT.</span>
      </div>
    </div>
  )
}
