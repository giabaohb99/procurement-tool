/**
 * duoc-CR-784 — luật thuần của BẢN IN Lịch sử mua hàng: bộ lọc <-> chuỗi truy vấn của trang in, câu mô tả bộ lọc, trần số dòng.
 *
 * Bảng trên màn hình phân trang tại máy chủ nên in màn hình chỉ ra một trang. Bản in là một trang riêng nhận ĐÚNG bộ lọc
 * (không kèm `page`) qua URL, rồi tự nạp đủ mọi dòng. URL là dữ liệu từ ngoài vào (gõ tay, dán link) nên mọi trường đều
 * được kiểm ở đây: chế độ lạ về `code`, ngày sai khuôn bị bỏ, khóa xếp ngoài danh sách bị bỏ, mã cắt ở trần của máy chủ.
 */
import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'

import type {
  PackagingHistoryParams,
  PackagingLastPricesSupplier,
} from '../types/packaging-cost-types'
import { PACKAGING_HISTORY_MAX_CODES } from './packaging-history'

/** Cỡ một lượt nạp của bản in — bằng trần `MAX_PAGE_SIZE` của máy chủ để ít vòng nhất. */
export const HISTORY_PRINT_PAGE_SIZE = 500
/** Trần số dòng của một bản in: quá thì cắt và báo rõ trên giấy (in cả chục nghìn dòng là treo trình duyệt). */
export const HISTORY_PRINT_ROW_CAP = 5000
/** Trần độ dài ô từ khóa — khớp `max_length=100` của máy chủ (dài hơn là 422). */
const MAX_QUERY_LENGTH = 100

/** Khóa xếp máy chủ nhận — khớp `SORT_KEYS` của `packaging_cost/history_service.py` (ba khóa cuối chỉ có ở chế độ sản phẩm). */
export const HISTORY_SORT_KEYS: readonly string[] = [
  'date',
  'code',
  'name',
  'supplier',
  'warehouse',
  'qty',
  'price',
  'amount',
  'vat',
  'source',
  'fg_code',
  'fg_name',
  'role',
]

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

function splitList(raw: string | null): string[] {
  if (!raw) return []
  const seen = new Set<string>()
  for (const part of raw.split(',')) {
    const value = part.trim()
    if (value) seen.add(value)
  }
  return [...seen].slice(0, PACKAGING_HISTORY_MAX_CODES)
}

function validDate(raw: string | null): string | undefined {
  if (!raw || !ISO_DATE.test(raw)) return undefined
  //  `Date.parse` nuốt cả 30/02 (lăn sang tháng sau) nên dựng lại ngày rồi so chuỗi để loại ngày không có trên lịch.
  const time = Date.parse(`${raw}T00:00:00Z`)
  return Number.isNaN(time) || new Date(time).toISOString().slice(0, 10) !== raw ? undefined : raw
}

/**
 * Bộ lọc màn hình -> chuỗi truy vấn của trang in (không kèm `page` / `page_size`). Mã đi một khóa nối bằng dấu phẩy;
 * nhà cung cấp lặp khóa `supplier` (mã nhà cung cấp có thể chứa dấu phẩy nên không nối).
 */
export function buildHistoryPrintSearch(params: PackagingHistoryParams): string {
  const search = new URLSearchParams()
  search.set('mode', params.mode)
  if (params.codes?.length) search.set('codes', params.codes.join(','))
  if (params.fg_codes?.length) search.set('fg_codes', params.fg_codes.join(','))
  if (params.q) search.set('q', params.q)
  for (const supplier of params.supplier ?? []) search.append('supplier', supplier)
  if (params.date_from) search.set('date_from', params.date_from)
  if (params.date_to) search.set('date_to', params.date_to)
  if (params.sort_by) {
    search.set('sort_by', params.sort_by)
    search.set('sort_dir', params.sort_dir ?? 'desc')
  }
  return search.toString()
}

/** Đường dẫn trang in cho một bộ lọc. */
export function packagingHistoryPrintHref(params: PackagingHistoryParams): string {
  return `${appRoutes.procurement.packagingHistoryPrint}?${buildHistoryPrintSearch(params)}`
}

/** Chuỗi truy vấn của trang in -> tham số gửi máy chủ (đã kiểm từng trường, xem đầu tệp). */
export function parseHistoryPrintSearch(search: URLSearchParams): PackagingHistoryParams {
  const mode = search.get('mode') === 'product' ? 'product' : 'code'
  const codes = splitList(search.get('codes'))
  const fg = splitList(search.get('fg_codes'))
  const q = (search.get('q') ?? '').trim().slice(0, MAX_QUERY_LENGTH)
  const suppliers = [
    ...new Set(
      search
        .getAll('supplier')
        .map((value) => value.trim())
        .filter(Boolean),
    ),
  ].slice(0, PACKAGING_HISTORY_MAX_CODES)
  const sortBy = search.get('sort_by')
  const sorted = sortBy !== null && HISTORY_SORT_KEYS.includes(sortBy)
  return {
    mode,
    //  Chỉ giữ mã của chế độ đang bật — giống `buildHistoryParams`, máy chủ không phải đoán mã nào còn hiệu lực.
    codes: mode === 'code' && codes.length ? codes : undefined,
    fg_codes: mode === 'product' && fg.length ? fg : undefined,
    q: q || undefined,
    supplier: suppliers.length ? suppliers : undefined,
    date_from: validDate(search.get('date_from')),
    date_to: validDate(search.get('date_to')),
    ...(sorted ? { sort_by: sortBy, sort_dir: search.get('sort_dir') === 'asc' ? 'asc' : 'desc' } : {}),
  }
}

/** Mô tả khoảng ngày: đủ hai đầu, một đầu, hoặc rỗng. */
function describeDateRange(from?: string, to?: string): string {
  if (from && to) return `${formatDate(from)} – ${formatDate(to)}`
  if (from) return `từ ${formatDate(from)}`
  if (to) return `đến ${formatDate(to)}`
  return ''
}

/**
 * Các mảnh của dòng mô tả bộ lọc trên bản in — CHỈ các điều kiện đang bật ngoài lựa chọn mã (chế độ + mã đã có ô chip riêng
 * ở đầu trang): nhà cung cấp (tra tên trong `suppliers` máy chủ trả kèm, không thấy thì in chính mã), khoảng ngày, từ khóa.
 */
export function describeHistoryFilters(
  params: PackagingHistoryParams,
  suppliers: readonly PackagingLastPricesSupplier[] = [],
): string[] {
  const parts: string[] = []
  if (params.supplier?.length) {
    const names = new Map(suppliers.map((supplier) => [supplier.code, supplier.name || supplier.code]))
    parts.push(`NCC: ${params.supplier.map((code) => names.get(code) ?? code).join(', ')}`)
  }
  const range = describeDateRange(params.date_from, params.date_to)
  if (range) parts.push(`Ngày mua: ${range}`)
  if (params.q) parts.push(`Từ khóa: "${params.q}"`)
  return parts
}

/** Số dòng sẽ in và có bị cắt ở trần không — `total` là tổng của máy chủ cho bộ lọc này. */
export function planHistoryPrintRows(
  total: number,
  cap: number = HISTORY_PRINT_ROW_CAP,
): { rows: number; capped: boolean } {
  const safe = Number.isFinite(total) && total > 0 ? Math.floor(total) : 0
  return { rows: Math.min(safe, cap), capped: safe > cap }
}

/** Câu báo khi bản in bị cắt: nói rõ in bao nhiêu trên tổng bao nhiêu và cách thu hẹp. */
export function describeCappedPrint(total: number, unit = 'lần mua'): string {
  return `Bộ lọc có ${total.toLocaleString('vi-VN')} ${unit} — bản in chỉ gồm ${HISTORY_PRINT_ROW_CAP.toLocaleString('vi-VN')} dòng đầu. Thu hẹp bộ lọc rồi in lại để có đủ.`
}
