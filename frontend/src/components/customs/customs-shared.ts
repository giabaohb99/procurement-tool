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
  importer_id: string
  importer_name: string   // chỉ để hiện chip "đang lọc theo doanh nghiệp", không gửi lên API
  date_from: string
  date_to: string
}

export const EMPTY_FILTERS: CustomsFilters = {
  q: '', hs_code: '', origin: '', unit: '', formulation: '', importer_id: '', importer_name: '',
  date_from: '', date_to: '',
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
    if (k === 'importer_name') continue
    if (v !== '' && v != null) out[k] = String(v)
  }
  return out
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
