// bao-CR-608 — biểu mẫu SỬA một dòng hàng, hiện ngay trong hộp chi tiết dòng (bản v1 của
// `customs-line-edit-form.tsx` + `utils/customs-line-form.ts` bản v2 — giữ hai bản cùng một luật).
//
// Chỉ gửi ô ĐÃ ĐỔI (PATCH `/api/customs/lines/{id}`). Bốn ô suy ra / tự tính (hoạt chất, hàm
// lượng, hai giá VND): ô TRỐNG = để hệ thống suy ra / tính; gõ vào = giá trị do người nhập.
// Chặn bấm đúp bằng `useRef`; Enter trong ô không lưu.
import { KeyboardEvent, useMemo, useRef, useState } from 'react'
import { api } from '../../api/client'
import DateInput from '../DateInput'
import { toast } from '../toast'

type Kind = 'text' | 'integer' | 'decimal' | 'date' | 'transport'
type Field = { key: string; label: string; kind: Kind; max?: number; required?: boolean; derived?: boolean }

const t = (key: string, label: string, max: number, extra: Partial<Field> = {}): Field =>
  ({ key, label, kind: 'text', max, ...extra })
const d = (key: string, label: string, extra: Partial<Field> = {}): Field => ({ key, label, kind: 'decimal', ...extra })

// Trần độ dài khớp `String(n)` của `tab_customs_line` / `tab_customs_party` (schema `CustomsLineUpdate`).
const GROUPS: { title: string; fields: Field[] }[] = [
  { title: 'Tờ khai', fields: [
    { key: 'reg_date', label: 'Ngày đăng ký', kind: 'date', required: true }, t('office_code', 'Nơi mở tờ khai', 10),
    { key: 'line_no', label: 'Số thứ tự hàng', kind: 'integer' }, t('import_country', 'Nước nhận hàng', 2),
  ] },
  { title: 'Doanh nghiệp', fields: [
    t('importer_tax_code', 'Mã số thuế doanh nghiệp', 14), t('importer_name', 'Doanh nghiệp', 255),
    t('partner_name', 'Đối tác (bên bán)', 255), t('origin_country', 'Nước xuất xứ', 2),
  ] },
  { title: 'Hàng hóa', fields: [
    t('product_name', 'Tên hàng', 255, { required: true }), t('hs_code', 'Mã HS', 8),
    t('active_ingredient', 'Hoạt chất', 255, { derived: true }), t('formulation', 'Hàm lượng / dạng', 40, { derived: true }),
    d('quantity', 'Lượng'), t('unit_code', 'Đơn vị tính', 4),
  ] },
  { title: 'Giá', fields: [
    d('price_usd', 'Đơn giá khai báo (USD)'), d('adj_price_usd', 'Đơn giá điều chỉnh (USD)'),
    d('price_nt', 'Đơn giá nguyên tệ khai báo'), d('adj_price_nt', 'Đơn giá nguyên tệ điều chỉnh'),
    t('currency', 'Nguyên tệ', 3), d('fx_rate', 'Tỷ giá nguyên tệ'), d('usd_rate', 'Tỷ giá USD'),
    d('price_vnd_flat', 'Giá VND (thuế NK 7%)', { derived: true }),
    d('price_vnd_line_tax', 'Giá VND (thuế suất dòng)', { derived: true }),
  ] },
  { title: 'Hợp đồng & vận chuyển', fields: [
    t('contract_no', 'Số hợp đồng', 40), { key: 'contract_date', label: 'Ngày hợp đồng', kind: 'date' },
    t('incoterm', 'Điều kiện giao hàng', 3), { key: 'transport_mode', label: 'Phương tiện vận chuyển', kind: 'transport' },
  ] },
  { title: 'Thuế', fields: [
    d('rate_import', 'Thuế suất XNK (%)'), d('tax_import', 'Thuế XNK'), d('rate_vat', 'Thuế suất VAT (%)'),
    d('tax_vat', 'Thuế VAT'), d('rate_excise', 'Thuế suất TTĐB (%)'), d('tax_excise', 'Thuế TTĐB'),
    d('rate_safeguard', 'Thuế suất tự vệ (%)'), d('tax_safeguard', 'Thuế tự vệ'), d('tax_environment', 'Thuế môi trường'),
  ] },
]
const FIELDS = GROUPS.flatMap((g) => g.fields)

// Khớp `TransportMode` + `TRANSPORT_LABELS` ở backend (mã VNACCS).
const TRANSPORT = [['1', 'Đường không'], ['2', 'Đường biển (container)'], ['3', 'Đường biển (hàng rời, lỏng...)'],
  ['4', 'Đường bộ (xe tải)'], ['9', 'Khác']]

const FROM_USER: Record<string, string> = {
  active_ingredient: 'active_ingredient_from_file', formulation: 'formulation_from_file',
  price_vnd_flat: 'price_vnd_flat_from_file', price_vnd_line_tax: 'price_vnd_line_tax_from_file',
}
const isUserValue = (row: any, key: string) => !FROM_USER[key] || Boolean(row[FROM_USER[key]])
const show = (v: any) => (v == null ? '' : String(v))

function toForm(row: any): Record<string, string> {
  const form: Record<string, string> = {}
  for (const f of FIELDS) form[f.key] = f.derived && !isUserValue(row, f.key) ? '' : show(row[f.key])
  return form
}

/** Dấu chấm hoặc phẩy làm dấu thập phân, không nhận dấu ngăn nghìn. Rỗng → null; sai → NaN. */
function parseNumber(value: string): number | null {
  const raw = value.replace(/\s/g, '')
  if (!raw) return null
  const s = raw.includes(',') && !raw.includes('.') ? raw.replace(',', '.') : raw
  return /^\d+(\.\d+)?$/.test(s) ? Number(s) : NaN
}

function buildPatch(initial: Record<string, string>, form: Record<string, string>): { patch: any; error: string | null } {
  const patch: Record<string, any> = {}
  for (const f of FIELDS) {
    const v = form[f.key].trim()
    if (f.required && !v) return { patch: {}, error: `Chưa nhập «${f.label}»` }
    if (v === initial[f.key].trim()) continue
    if (f.kind === 'text') patch[f.key] = v
    else if (f.kind === 'date') patch[f.key] = v || null
    else if (f.kind === 'transport') patch[f.key] = v ? Number(v) : null
    else {
      const n = parseNumber(v)
      if (Number.isNaN(n)) return { patch: {}, error: `«${f.label}» phải là số không âm` }
      if (f.kind === 'integer' && n !== null && !Number.isInteger(n)) return { patch: {}, error: `«${f.label}» phải là số nguyên` }
      patch[f.key] = n
    }
  }
  return { patch, error: null }
}

const blockEnter = (e: KeyboardEvent<HTMLInputElement>) => { if (e.key === 'Enter') e.preventDefault() }

export default function CustomsLineEditForm({ row, onCancel, onSaved }: {
  row: any
  onCancel: () => void
  onSaved: (fresh: any) => void
}) {
  const initial = useMemo(() => toForm(row), [row])
  const [form, setForm] = useState(initial)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const busy = useRef(false)
  const set = (key: string, value: string) => setForm((cur) => ({ ...cur, [key]: value }))

  async function save() {
    if (busy.current) return
    const { patch, error: problem } = buildPatch(initial, form)
    setError(problem)
    if (problem) return
    if (!Object.keys(patch).length) { toast.info('Chưa có ô nào thay đổi'); onCancel(); return }
    busy.current = true
    setSaving(true)
    try {
      const r = await api.patch(`/api/customs/lines/${row.id}`, patch)
      toast.success('Đã lưu dòng hàng')
      onSaved(r.data.data)
    } catch { /* interceptor đã báo lỗi — giữ biểu mẫu để sửa tiếp */ } finally {
      busy.current = false
      setSaving(false)
    }
  }

  function input(f: Field) {
    if (f.kind === 'date') return <DateInput value={form[f.key]} onChange={(v) => set(f.key, v || '')} />
    if (f.kind === 'transport') {
      return (
        <select value={form[f.key]} onChange={(e) => set(f.key, e.target.value)}>
          <option value="">Không khai</option>
          {TRANSPORT.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
        </select>
      )
    }
    const auto = f.derived && !isUserValue(row, f.key) ? `Tự động${row[f.key] != null && row[f.key] !== '' ? `: ${row[f.key]}` : ''}` : undefined
    return (
      <input value={form[f.key]} maxLength={f.max} inputMode={f.kind === 'text' ? undefined : 'decimal'} placeholder={auto}
        onKeyDown={blockEnter} onChange={(e) => set(f.key, e.target.value)} />
    )
  }

  return (
    <>
      <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
        Ô <b>Hoạt chất</b>, <b>Hàm lượng / dạng</b> và hai ô <b>giá VND</b> để trống thì hệ thống tự suy ra / tự tính (giá trị
        hiện ở chữ mờ); gõ vào thì giữ đúng giá trị đó. Số dùng dấu chấm hoặc phẩy cho phần thập phân, không gõ dấu ngăn
        nghìn. Bản trước khi sửa được lưu lại trong nhật ký.
      </div>
      {error && <div style={{ color: '#b91c1c', fontSize: 13, marginBottom: 8 }}>{error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
        {GROUPS.map((g) => (
          <div key={g.title} className="card" style={{ padding: '10px 14px' }}>
            <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--navy)' }}>{g.title}</div>
            {g.fields.map((f) => (
              <div key={f.key} className="form-row" style={{ marginBottom: 6 }}>
                <label>{f.label}{f.required ? ' *' : ''}</label>
                {input(f)}
              </div>
            ))}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 14 }}>
        <button className="btn ghost" type="button" disabled={saving} onClick={onCancel}>Hủy</button>
        <button className="btn" type="button" disabled={saving} onClick={save}>
          <i className="ti ti-device-floppy" />{saving ? 'Đang lưu…' : 'Lưu'}
        </button>
      </div>
    </>
  )
}
