// bao-CR-470 — hàm thuần của màn Tra cứu giá hải quan (bản v2): dựng tham số gửi API,
// cổng "đã đủ bộ lọc để vẽ biểu đồ", câu bảng rỗng, trạng thái lô nạp, dải tháng đã phủ.
//
// Tách khỏi component để kiểm được bằng test thuần — đây là những chỗ sai âm thầm:
// gửi nhầm tham số rỗng, vẽ biểu đồ khi chưa lọc, hay nói "chưa có dữ liệu" trong khi
// thật ra là bộ lọc loại hết.
import { formatMoney, formatUnitPrice } from '@/shared/utils/format-money'

import {
  CUSTOMS_BATCH_MODE,
  CUSTOMS_BATCH_STATUS,
  type CustomsCompare,
  type CustomsFilters,
  type CustomsImportBatch,
  type CustomsPeriod,
  type CustomsSeriesPoint,
} from '../types/customs'

export const EMPTY_CUSTOMS_FILTERS: CustomsFilters = {
  q: '',
  hs_code: '',
  origin: '',
  unit: '',
  formulation: '',
  importer_id: '',
  partner_id: '',
  date_from: '',
  date_to: '',
  currency: '',
  incoterm: '',
  batch_id: '',
  price_min: '',
  price_max: '',
  qty_min: '',
  qty_max: '',
  rate_min: '',
  rate_max: '',
}

/** Câu chặn của thẻ Biểu đồ / Nhà nhập khẩu — khớp `NEED_FILTER_MSG` của backend. */
export const CUSTOMS_NEED_FILTER_MESSAGE =
  'Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.'

export const CUSTOMS_PERIOD_OPTIONS: { value: CustomsPeriod; label: string }[] = [
  { value: 'month', label: 'Tháng' },
  { value: 'quarter', label: 'Quý' },
  { value: 'year', label: 'Năm' },
]

/** Số mặt hàng tối thiểu / tối đa của thẻ So sánh — khớp `compare_terms` của backend. */
export const COMPARE_MIN_TERMS = 2
export const COMPARE_MAX_TERMS = 5

/**
 * Danh sách pháp lý của danh mục hóa chất — khớp `RegulationList` +
 * `REGULATION_LIST_LABELS` ở `backend/app/modules/customs/constants.py`.
 */
export const REGULATION_LIST_OPTIONS = [
  { value: 1, label: 'NĐ 24/2026 · Phụ lục I' },
  { value: 2, label: 'NĐ 24/2026 · Phụ lục II' },
  { value: 3, label: 'NĐ 24/2026 · Phụ lục III (tiền chất)' },
  { value: 4, label: 'NĐ 24/2026 · Phụ lục IV (ngưỡng khối lượng)' },
  { value: 10, label: 'TT 75/2025 · Hoạt chất cấm' },
  { value: 11, label: 'TT 01/2026 · Phải công bố theo lô' },
] as const

/**
 * bao-CR-477 — độ NGHIÊM TRỌNG của từng danh sách, số nhỏ = nặng hơn. Dùng để xếp kết quả
 * tra (dòng nặng nhất lên đầu) và chọn màu nhãn. Thứ tự: hoạt chất CẤM · tiền chất vũ khí hóa
 * học (PL III) · có NGƯỠNG khối lượng (PL IV) · phải công bố theo lô · có trong danh mục
 * (PL I, II). Mã lạ xếp cuối nhưng vẫn hiện — đừng giấu thứ mình chưa hiểu.
 */
const REGULATION_SEVERITY: Record<number, number> = { 10: 0, 3: 1, 4: 2, 11: 3, 1: 4, 2: 4 }

export function regulationSeverity(listCode: number): number {
  return REGULATION_SEVERITY[listCode] ?? 9
}

/** Tối thiểu cần để xếp — cả kết quả tra lẫn cảnh báo đều có đủ ba ô này. */
interface RegulationSortable {
  list_code: number
  threshold_kg: number | null
  name: string
}

/**
 * Xếp nặng nhất lên đầu; cùng danh sách thì NGƯỠNG THẤP lên trước (0,15 kg nguy hiểm hơn
 * 1.000 kg), rồi tới tên. Trả mảng MỚI — không đảo thứ tự dữ liệu của truy vấn.
 */
export function sortRegulationsBySeverity<T extends RegulationSortable>(items: readonly T[]): T[] {
  return [...items].sort(
    (a, b) =>
      regulationSeverity(a.list_code) - regulationSeverity(b.list_code) ||
      (a.threshold_kg ?? Number.POSITIVE_INFINITY) - (b.threshold_kg ?? Number.POSITIVE_INFINITY) ||
      a.name.localeCompare(b.name, 'vi'),
  )
}

/**
 * Ngưỡng khối lượng → chữ: «100 kg», «1.000 kg», «0,15 kg». Giữ tới 3 chữ số lẻ vì có ngưỡng
 * dưới 1 kg (Methyl isocyanate 0,15 kg) — làm tròn về số nguyên là in ra «0 kg», tức nói điều
 * ngược hẳn với luật. Rỗng / âm / không phải số thì trả chuỗi rỗng.
 */
export function formatThresholdKg(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value) || value < 0) return ''
  return `${value.toLocaleString('vi-VN', { maximumFractionDigits: 3 })} kg`
}

/** Nhãn cột «Ngưỡng / Mức cấm»: hoạt chất cấm → «CẤM từ 2026» (không rõ năm → «CẤM»). */
export function formatBannedLabel(bannedYear: number | null | undefined): string {
  return bannedYear ? `CẤM từ ${bannedYear}` : 'CẤM'
}

/** Mã danh sách → nhãn. Mã lạ thì hiện nguyên mã, đừng giấu. */
export function formatRegulationListLabel(code: number | string | null | undefined): string {
  if (code === null || code === undefined || code === '') return ''
  const found = REGULATION_LIST_OPTIONS.find((item) => String(item.value) === String(code))
  return found ? found.label : `Danh sách ${code}`
}

/**
 * Mã đơn vị tính trên tờ khai (chuẩn UN/ECE) → chữ đọc được. CHỈ khai mã chắc nghĩa; mã hệ
 * thống hải quan tự đặt (UNK, UNA, UNL, UNIT, TAM…) chưa rõ nghĩa thì hiện nguyên mã.
 */
const UNIT_LABELS: Record<string, string> = {
  KGM: 'kg', LTR: 'lít', TNE: 'tấn', GRM: 'gam', MTQ: 'm³', PCE: 'cái / chiếc', SET: 'bộ',
  PKG: 'gói / kiện', BAG: 'bao', BBL: 'thùng phuy', ROL: 'cuộn', PAIL: 'xô / thùng nhỏ',
}

export function formatCustomsUnit(code: string | null | undefined): string {
  if (!code) return ''
  return UNIT_LABELS[code] ?? code
}

/** Nhãn nút chọn đơn vị: «lít (LTR)»; mã chưa rõ nghĩa thì chỉ mã. */
export function formatCustomsUnitChip(code: string): string {
  return UNIT_LABELS[code] ? `${UNIT_LABELS[code]} (${code})` : code
}

/**
 * Giá USD: giữ đủ 4 số lẻ (KHÔNG làm tròn về đồng như `formatMoney` — giá hải quan
 * 2,817 USD/kg mà làm tròn thành 3 là mất hết ý nghĩa). Trống hiện gạch ngang.
 */
export function formatUsd(value: number | string | null | undefined): string {
  return formatUnitPrice(value) || '—'
}

/** Cột VND (bao-CR-493): tiền đồng, không lẻ. */
export function formatVnd(value: number | string | null | undefined): string {
  return formatMoney(value) || '—'
}

/**
 * bao-CR-493 — doanh nghiệp / đối tác chọn NHIỀU nhưng vẫn đi bằng hai tham số URL: `…_id`
 * là id nối dấu phẩy («12,34»), `…_name` là tên nối dấu «|» cùng thứ tự (tên chỉ để in chip,
 * không lọc). Hai hàm dưới giữ hai chuỗi này luôn song song với nhau.
 */
export interface NamedId {
  id: string
  name: string
}

export function splitNamedIds(ids: string, names: string): NamedId[] {
  const idList = ids.split(',').map((v) => v.trim()).filter(Boolean)
  const nameList = names.split('|')
  return idList.map((id, index) => ({ id, name: (nameList[index] ?? '').trim() }))
}

export function joinNamedIds(items: NamedId[]): { ids: string; names: string } {
  return { ids: items.map((item) => item.id).join(','), names: items.map((item) => item.name).join('|') }
}

/** Thêm một đối tượng vào bộ lọc; đã có rồi thì giữ nguyên (không nhân đôi chip). */
export function addNamedId(ids: string, names: string, id: number | string, name: string): { ids: string; names: string } {
  const key = String(id)
  const items = splitNamedIds(ids, names)
  if (items.some((item) => item.id === key)) return joinNamedIds(items)
  return joinNamedIds([...items, { id: key, name: name.replace(/[|,]/g, ' ').trim() }])
}

export function removeNamedId(ids: string, names: string, id: string): { ids: string; names: string } {
  return joinNamedIds(splitNamedIds(ids, names).filter((item) => item.id !== id))
}

/**
 * Bộ lọc → tham số gửi API: bỏ ô rỗng (gửi `hs_code=` là backend lọc theo chuỗi rỗng),
 * cắt khoảng trắng hai đầu từ khóa.
 */
export function buildCustomsParams(filters: CustomsFilters): Record<string, string> {
  const params: Record<string, string> = {}
  for (const [key, raw] of Object.entries(filters)) {
    const value = (raw ?? '').trim()
    if (value) params[key] = value
  }
  return params
}

/**
 * Đã đủ bộ lọc để vẽ biểu đồ chưa — có từ khóa hoặc mã HS (đại ca chốt 23/09/2026).
 * Biểu đồ của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng, kg lẫn lít — vô nghĩa. Xuất
 * xứ, doanh nghiệp, khoảng ngày chỉ thu hẹp thêm, một mình chúng chưa đủ.
 */
export function hasChartFilter(filters: Pick<CustomsFilters, 'q' | 'hs_code'>): boolean {
  return Boolean(filters.q.trim() || filters.hs_code.trim())
}

/**
 * Câu hiện khi bảng dòng hàng rỗng. Phải phân biệt «chưa có dữ liệu» với «bộ lọc loại
 * hết» — một câu chung cho cả hai thì người gõ nhầm một chữ đọc ra "chưa có dữ liệu" và
 * tin là vậy. `coverageTotal` chưa về (undefined) thì coi là đang có dữ liệu.
 */
export function resolveLinesEmptyMessage(
  coverageTotal: number | undefined,
  canImport: boolean,
): string {
  if (coverageTotal === 0) {
    return canImport
      ? 'Chưa có dữ liệu hải quan. Bấm «Nạp dữ liệu» để tải tệp GTT02.'
      : 'Chưa có dữ liệu hải quan. Liên hệ người phụ trách nạp dữ liệu.'
  }
  return 'Không có dòng hàng nào khớp bộ lọc — thử bỏ bớt điều kiện hoặc đổi từ khóa.'
}

/** Lô còn đang chờ / đang chạy — còn phải hỏi lại trạng thái. */
export function isBatchRunning(batch: Pick<CustomsImportBatch, 'status'>): boolean {
  return batch.status === CUSTOMS_BATCH_STATUS.queued || batch.status === CUSTOMS_BATCH_STATUS.running
}

/** Lô chạy thử đã xong và có dòng để ghi — chỉ những lô này mới đem đi Áp dụng. */
export function isBatchUsable(batch: Pick<CustomsImportBatch, 'status' | 'created_count'>): boolean {
  return batch.status === CUSTOMS_BATCH_STATUS.done && batch.created_count > 0
}

/** Tổng số dòng cũ SẼ BỊ THAY nếu áp dụng các lô dùng được. */
export function sumReplacedLines(batches: CustomsImportBatch[]): number {
  return batches.filter(isBatchUsable).reduce((sum, batch) => sum + (batch.deleted_count || 0), 0)
}

/**
 * Hoàn tác được không. Chỉ lô GHI THẬT đã xong mới có gì để hoàn tác; lô đã THAY dòng
 * cũ thì không — dòng cũ đã xóa lúc ghi, hoàn tác chỉ xóa được dòng mới và để lại một
 * khoảng ngày trống.
 */
export function resolveRevertState(
  batch: Pick<CustomsImportBatch, 'mode' | 'status' | 'deleted_count'>,
): 'hidden' | 'blocked' | 'allowed' {
  if (batch.mode !== CUSTOMS_BATCH_MODE.apply || batch.status !== CUSTOMS_BATCH_STATUS.done) {
    return 'hidden'
  }
  return batch.deleted_count > 0 ? 'blocked' : 'allowed'
}

/** Nhãn trạng thái lô. */
export function formatBatchStatus(batch: Pick<CustomsImportBatch, 'mode' | 'status'>): string {
  if (batch.status === CUSTOMS_BATCH_STATUS.reverted) return 'Đã hoàn tác'
  if (batch.status === CUSTOMS_BATCH_STATUS.failed) return 'Lỗi'
  if (batch.status === CUSTOMS_BATCH_STATUS.done) {
    return batch.mode === CUSTOMS_BATCH_MODE.dryRun ? 'Chạy thử xong' : 'Đã ghi'
  }
  return 'Đang chạy'
}

/**
 * Tham số của thẻ So sánh: từ khóa đã cắt khoảng trắng, bỏ ô trống, tối đa 5; bộ lọc
 * khác áp chung (trừ `q` — mỗi mặt hàng là một `q`). Mảng `terms` được `httpClient` gửi
 * thành `terms=a&terms=b` đúng dạng backend đọc.
 */
export function buildCompareParams(
  terms: string[],
  filters: CustomsFilters,
  period: CustomsPeriod,
  chartUnit: string,
): Record<string, string | string[]> {
  const params: Record<string, string | string[]> = {
    ...buildCustomsParams({ ...filters, q: '' }),
    period,
    terms: cleanCompareTerms(terms),
  }
  if (chartUnit) params.chart_unit = chartUnit
  return params
}

/** Từ khóa so sánh sau khi dọn: bỏ trống, bỏ trùng (không phân biệt hoa thường), tối đa 5. */
export function cleanCompareTerms(terms: string[]): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const raw of terms) {
    const term = raw.trim()
    const key = term.toLowerCase()
    if (!term || seen.has(key)) continue
    seen.add(key)
    out.push(term)
  }
  return out.slice(0, COMPARE_MAX_TERMS)
}

/** Một hàng của bảng/biểu đồ so sánh: kỳ + giá của từng mặt hàng theo chỉ số. */
export interface CompareRow {
  period: string
  label: string
  values: (number | null)[]
  counts: number[]
  lowData: boolean[]
}

/**
 * Gộp chuỗi theo kỳ của các mặt hàng thành một trục chung, xếp theo kỳ. Kỳ mà một mặt
 * hàng không có thì giá `null` — biểu đồ ĐỨT đoạn ở đó chứ không nối qua.
 */
export function mergeCompareSeries(data: Pick<CustomsCompare, 'terms'>): CompareRow[] {
  const rows = new Map<string, CompareRow>()
  const size = data.terms.length
  data.terms.forEach((term, index) => {
    for (const point of term.series) {
      let row = rows.get(point.period)
      if (!row) {
        row = {
          period: point.period,
          label: point.label,
          values: Array<number | null>(size).fill(null),
          counts: Array<number>(size).fill(0),
          lowData: Array<boolean>(size).fill(false),
        }
        rows.set(point.period, row)
      }
      row.values[index] = point.wavg
      row.counts[index] = point.count
      row.lowData[index] = point.low_data
    }
  })
  return [...rows.values()].sort((a, b) => a.period.localeCompare(b.period))
}

/**
 * Ô tháng của dải độ phủ: có dữ liệu · trống (quên nạp tệp) · chưa tới. `today` truyền
 * từ ngoài để test không phụ thuộc hôm nay.
 */
export function classifyCoverageMonth(
  year: number,
  monthIndex: number,
  count: number,
  today: Date,
): 'future' | 'filled' | 'empty' {
  const currentYear = today.getFullYear()
  const currentMonth = today.getMonth()
  if (year > currentYear || (year === currentYear && monthIndex > currentMonth)) return 'future'
  return count > 0 ? 'filled' : 'empty'
}

/** Mã HS phải có ít nhất 4 chữ số mới tra biểu thuế — khớp `lookup_tariff`. */
export function isValidHsLookup(code: string): boolean {
  return code.replace(/\D/g, '').length >= 4
}

/** Tra pháp lý cần ít nhất 2 ký tự — khớp `lookup_regulations`. */
export function isValidRegulationLookup(term: string): boolean {
  return term.trim().length >= 2
}

/**
 * Rút gọn số LƯỢNG cho nhãn trục biểu đồ cột: 2.000.000 -> "2 tr", 500.000 -> "500 N",
 * 1.500.000.000 -> "1,5 tỷ". Nhãn đầy đủ ("2.000.000") dài quá bề ngang trục nên bị xén
 * mất chữ số đầu. Chỉ dùng cho nhãn trục — bảng và ô rê chuột luôn ghi đủ chữ số.
 */
export function formatCompactQuantity(value: number): string {
  const num = Number(value)
  if (!Number.isFinite(num)) return ''
  const abs = Math.abs(num)
  const short = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 1 })
  if (abs >= 1e9) return `${short(num / 1e9)} tỷ`
  if (abs >= 1e6) return `${short(num / 1e6)} tr`
  if (abs >= 1e3) return `${short(num / 1e3)} N`
  return short(num)
}

/** Bước chia trục "tròn": 1 · 2 · 2,5 · 5 · 10 × 10^n, không nhỏ hơn `raw`. */
function roundUpStep(raw: number): number {
  const exponent = Math.floor(Math.log10(raw))
  const base = 10 ** exponent
  for (const factor of [1, 2, 2.5, 5, 10]) {
    if (factor * base >= raw) return factor * base
  }
  return 10 * base
}

/** Làm tròn khử sai số dấu phẩy động (0.1 + 0.2) trước khi đưa vào nhãn trục. */
function stripFloatNoise(value: number): number {
  return Number(value.toPrecision(12))
}

export interface PriceAxis {
  domain: [number, number]
  ticks: number[]
}

/**
 * Trục giá của biểu đồ: từ min(p25, bình quân) tới max(p75, bình quân) của mọi kỳ, nới
 * thêm một khoảng rồi làm tròn ra các mốc chẵn. KHÔNG dùng thấp nhất / cao nhất: một
 * dòng giá lạ (250 USD/lít giữa đám 2–4 USD/lít) kéo trục lên trần và ép đường bình quân
 * dẹp sát đáy — lỗi thật ở bản v1. Thấp / cao vẫn hiện trong bảng và ô rê chuột.
 *
 * Trả `null` khi không kỳ nào có giá (không có gì để vẽ).
 */
export function buildPriceAxis(
  series: Pick<CustomsSeriesPoint, 'p25' | 'p75' | 'wavg'>[],
  tickCount = 5,
): PriceAxis | null {
  const lows: number[] = []
  const highs: number[] = []
  for (const point of series) {
    for (const value of [point.p25, point.wavg]) {
      if (typeof value === 'number' && Number.isFinite(value)) lows.push(value)
    }
    for (const value of [point.p75, point.wavg]) {
      if (typeof value === 'number' && Number.isFinite(value)) highs.push(value)
    }
  }
  if (!lows.length || !highs.length) return null

  let low = Math.min(...lows)
  let high = Math.max(...highs)
  //  Mọi kỳ cùng một giá → nới 10% hai phía (hoặc 1 đơn vị khi giá bằng 0) cho có trục.
  const span = high - low
  const pad = span > 0 ? span * 0.08 : Math.abs(high) * 0.1 || 1
  low = Math.max(0, low - pad)
  high += pad

  const step = roundUpStep((high - low) / Math.max(1, tickCount - 1))
  const start = stripFloatNoise(Math.floor(low / step) * step)
  const end = stripFloatNoise(Math.ceil(high / step) * step)
  const ticks: number[] = []
  for (let index = 0; start + index * step <= end + step / 2; index += 1) {
    ticks.push(stripFloatNoise(start + index * step))
  }
  return { domain: [start, end], ticks }
}
