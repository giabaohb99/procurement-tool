// bao-CR-470 — phần dùng chung của màn Tra cứu giá hải quan (bản cũ).
// Thiết kế: doc/erp/hai-quan/04-giao-dien.md.
import { useLayoutEffect, useRef, useState } from 'react'
import { fmtPrice, fmtVND } from '../../utils/money'

export type CustomsFilters = {
  q: string
  hs_code: string
  origin: string
  unit: string
  formulation: string
  importer_id: string     // bao-CR-493: nhiều id nối dấu phẩy («12,34»), backend tự tách, nhiều là HOẶC
  importer_name: string   // chỉ để hiện chip "đang lọc theo doanh nghiệp", không gửi lên API; nhiều tên nối «|»
  partner_id: string      // bao-CR-493: đối tác nước ngoài, cùng luật «nhiều id nối dấu phẩy»
  partner_name: string    // chỉ để in chip, không gửi lên API
  date_from: string
  date_to: string
  // bao-CR-493 — sáu ô «Lọc thêm» theo sheet 4 yêu cầu phòng Thu mua. Rỗng = không lọc.
  currency: string
  incoterm: string
  batch_id: string
  price_min: string
  price_max: string
  qty_min: string
  qty_max: string
  rate_min: string
  rate_max: string
  // bao-CR-494 — nhãn tự gắn: '1' Thành phẩm · '2' Nguyên liệu (khớp `ProductKind` backend). Rỗng = cả hai.
  product_kind: string
}

export const EMPTY_FILTERS: CustomsFilters = {
  q: '', hs_code: '', origin: '', unit: '', formulation: '', importer_id: '', importer_name: '',
  partner_id: '', partner_name: '', date_from: '', date_to: '',
  currency: '', incoterm: '', batch_id: '', price_min: '', price_max: '', qty_min: '', qty_max: '',
  rate_min: '', rate_max: '', product_kind: '',
}

/** bao-CR-494 — khớp `ProductKind` backend. */
export const PRODUCT_KIND_OPTIONS = [
  { value: '1', label: 'Thành phẩm' },
  { value: '2', label: 'Nguyên liệu' },
]

// bao-CR-496 — bộ lọc đã lưu dùng CHUNG kho với bản v2: `params` là chuỗi tham số URL, đúng tên và
// đúng thứ tự `FILTER_PARAMS` của trang v2. Chỉ những khóa này được ghi / đọc.
export const SAVED_FILTER_KEYS: (keyof CustomsFilters)[] = [
  'q', 'hs_code', 'origin', 'unit', 'formulation', 'importer_id', 'importer_name', 'partner_id',
  'partner_name', 'date_from', 'date_to', 'currency', 'incoterm', 'batch_id', 'price_min', 'price_max',
  'qty_min', 'qty_max', 'rate_min', 'rate_max', 'product_kind',
]

/** Bộ lọc đang áp → chuỗi ổn định (bỏ ô trống) để lưu. */
export function toSavedParams(f: CustomsFilters): string {
  const out = new URLSearchParams()
  for (const k of SAVED_FILTER_KEYS) if (f[k]) out.append(k, String(f[k]))
  return out.toString()
}

/** Chuỗi đã lưu → bộ lọc ĐẦY ĐỦ (ô không có trong chuỗi về rỗng) — chọn là về đúng trạng thái đó. */
export function fromSavedParams(params: string): CustomsFilters {
  const saved = new URLSearchParams(params)
  const out: CustomsFilters = { ...EMPTY_FILTERS }
  for (const k of SAVED_FILTER_KEYS) {
    const values = saved.getAll(k).filter((v) => v !== '')
    if (values.length) out[k] = values.join(',')
  }
  return out
}

export const sameSavedParams = (a: string, b: string) =>
  toSavedParams(fromSavedParams(a)) === toSavedParams(fromSavedParams(b))


/** Sáu ô của hàng «Lọc thêm» — có giá trị thì hàng tự mở. */
export const EXTRA_FILTER_KEYS: (keyof CustomsFilters)[] = [
  'currency', 'incoterm', 'batch_id', 'price_min', 'price_max', 'qty_min', 'qty_max', 'rate_min', 'rate_max',
]

// bao-CR-493 — doanh nghiệp chọn NHIỀU: `importer_id` là id nối dấu phẩy, `importer_name` là tên nối «|»
// cùng thứ tự (tên chỉ để in chip). Ba hàm dưới giữ hai chuỗi luôn song song.
export type NamedId = { id: string; name: string }
export function splitNamedIds(ids: string, names: string): NamedId[] {
  const idList = ids.split(',').map((v) => v.trim()).filter(Boolean)
  const nameList = names.split('|')
  return idList.map((id, i) => ({ id, name: (nameList[i] ?? '').trim() }))
}
export function joinNamedIds(items: NamedId[]): { ids: string; names: string } {
  return { ids: items.map((x) => x.id).join(','), names: items.map((x) => x.name).join('|') }
}
export function addNamedId(ids: string, names: string, id: number | string, name: string) {
  const key = String(id)
  const items = splitNamedIds(ids, names)
  if (items.some((x) => x.id === key)) return joinNamedIds(items)
  return joinNamedIds([...items, { id: key, name: (name || '').replace(/[|,]/g, ' ').trim() }])
}
export function removeNamedId(ids: string, names: string, id: string) {
  return joinNamedIds(splitNamedIds(ids, names).filter((x) => x.id !== id))
}

export const PERIODS = [
  { value: 'month', label: 'Tháng' },
  { value: 'quarter', label: 'Quý' },
  { value: 'year', label: 'Năm' },
]

// Mã đơn vị tính trên tờ khai (chuẩn UN/ECE) → chữ đọc được. CHỈ khai mã chắc nghĩa; mã hệ
// thống hải quan tự đặt (UNK, UNA, UNL, UNIT, TAM…) chưa rõ nghĩa thì hiện nguyên mã, đừng đoán.
export const UNIT_LABELS: Record<string, string> = {
  KGM: 'kg', LTR: 'lít', TNE: 'tấn', GRM: 'gam', MTQ: 'm³', PCE: 'cái / chiếc', SET: 'bộ',
  PKG: 'gói / kiện', BAG: 'bao', BBL: 'thùng phuy', ROL: 'cuộn', PAIL: 'xô / thùng nhỏ',
}
export const unitLabel = (u?: string) => (u ? UNIT_LABELS[u] || u : '')
// Nhãn nút chọn đơn vị: «lít (LTR)»; mã chưa rõ nghĩa thì chỉ mã.
export const unitChip = (u: string) => (UNIT_LABELS[u] ? `${UNIT_LABELS[u]} (${u})` : u)

export function toParams(f: CustomsFilters): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(f)) {
    if (k === 'importer_name' || k === 'partner_name') continue
    if (v !== '' && v != null) out[k] = String(v)
  }
  return out
}

// Cột VND (bao-CR-493): tiền đồng, không lẻ.
export const fmtVnd = (v: any) => (v == null || v === '' ? '—' : fmtVND(v))

// Tải một tệp từ API (responseType blob). Câu lỗi của backend cũng về dạng blob nên đọc lại
// thành JSON mới báo đúng lý do — dùng chung cho Xuất Excel và Tải tệp gốc (bao-CR-493).
export async function downloadBlob(api: any, url: string, fallbackName: string, params?: Record<string, string>) {
  const r = await api.get(url, { params, responseType: 'blob' })
  const cd = String(r.headers['content-disposition'] || '')
  const name = /filename="?([^";]+)"?/.exec(cd)?.[1] || fallbackName
  const href = window.URL.createObjectURL(new Blob([r.data]))
  const a = document.createElement('a')
  a.href = href
  a.setAttribute('download', name)
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(href)
}
export async function blobErrorMessage(e: any, fallback: string): Promise<string> {
  try { return JSON.parse(await e?.response?.data?.text())?.error?.message || fallback } catch { return fallback }
}

// Biểu đồ / xếp hạng / so sánh chỉ chạy khi đã có từ khóa hoặc mã HS (đại ca chốt 23/09/2026):
// biểu đồ của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng, kg lẫn lít — con số vô nghĩa.
export const hasChartFilter = (f: CustomsFilters) => !!(f.q.trim() || f.hs_code.trim())
export const NEED_FILTER_MSG = 'Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.'

// Giá USD giữ đủ 4 số lẻ — KHÔNG dùng fmtVND (làm tròn về đồng, cắt mất phần lẻ).
export const fmtUsd = (v: any) => (v == null || v === '' ? '—' : fmtPrice(v))
export const fmtQty = (v: any, unit?: string) =>
  v == null ? '—' : `${fmtVND(v)}${unit ? ' ' + unitLabel(unit) : ''}`
export const fmtDate = (iso?: string | null) => {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

// ── Thang chia trục ─────────────────────────────────────────────────────────
// Bước tròn 1 · 2 · 2,5 · 5 × 10^k — trục ra 0,5 · 1 · 1,5 thay vì 225,38 · 76,13.
export function niceStep(raw: number) {
  const p = Math.pow(10, Math.floor(Math.log10(raw)))
  const m = raw / p
  return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p
}

export function niceScale(lo: number, hi: number, count = 5) {
  if (hi <= lo) hi = lo + (lo || 1) * 0.1
  const step = niceStep((hi - lo) / count)
  const start = Math.floor(lo / step) * step
  const end = Math.ceil(hi / step) * step
  const ticks: number[] = []
  for (let v = start; v <= end + step / 2; v += step) ticks.push(Number(v.toFixed(10)))
  return { min: start, max: end, ticks }
}

export const fmtTick = (v: number) => v.toLocaleString('vi-VN', { maximumFractionDigits: 2 })

// Số lượng gọn cho trục: 2.000.000 → «2 tr», 500.000 → «500 N».
export function fmtCompact(v: number) {
  if (v >= 1e9) return `${fmtTick(v / 1e9)} tỷ`
  if (v >= 1e6) return `${fmtTick(v / 1e6)} tr`
  if (v >= 1e3) return `${fmtTick(v / 1e3)} N`
  return fmtTick(v)
}

// Đo bề rộng thật của khung để vẽ SVG đúng pixel.
export function useWidth() {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    setWidth(el.clientWidth)
    const ro = new ResizeObserver(() => setWidth(el.clientWidth))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return { ref, width }
}
