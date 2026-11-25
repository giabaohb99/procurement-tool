/**
 * duoc-CR-784 — luật thuần của tab Lịch sử mua hàng: đường dẫn sâu (`?codes=` / `?hh=`), bộ lọc → tham số máy chủ, dữ
 * liệu + trục của biểu đồ đơn giá. Các thẻ số liệu ở `packaging-history-summary-items.ts`.
 *
 * Mã được cất trong URL (không chỉ trong state) để màn khác dẫn thẳng vào được — bấm mã ở Bảng giá / Giá mua gần nhất /
 * Tác động giá là mở đúng lịch sử của mã đó — và để gửi link cho người khác.
 */
import { appRoutes } from '@/shared/constants/app-routes'
import { PACKAGING_ROLE } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'

import type {
  PackagingHistoryMode,
  PackagingHistoryParams,
  PackagingHistoryPoint,
} from '../types/packaging-cost-types'

const ROLE_LABEL = new Map(PACKAGING_ROLE.map((role) => [Number(role.value), role.label]))

/** "Chai" / "Nắp"... — thành phần của dòng trong định mức sản phẩm (chế độ sản phẩm); chế độ mã không có vai trò thì rỗng. */
export function historyRoleText(row: { role: number | null }): string {
  return row.role === null ? '' : (ROLE_LABEL.get(row.role) ?? String(row.role))
}

/** Khóa dòng của bảng: chế độ sản phẩm một dòng sổ giá hiện ở nhiều sản phẩm nên `id` một mình không duy nhất. */
export function historyRowKey(row: { id: number; hh_code: string }): string {
  return row.hh_code ? `${row.hh_code}:${row.id}` : String(row.id)
}

/** Trần số mã một lượt — khớp `MAX_CODES` của máy chủ (`history_service.py`). */
export const PACKAGING_HISTORY_MAX_CODES = 200

export interface PackagingHistoryFilters {
  q: string
  /** Mã nhà cung cấp đã chọn; rỗng = không lọc. */
  suppliers: string[]
  from: string
  to: string
}

export interface PackagingHistorySelection {
  mode: PackagingHistoryMode
  /** Mã VTBB (chế độ `code`). */
  codes: string[]
  /** Mã sản phẩm (chế độ `product`). */
  hh: string[]
}

export const EMPTY_HISTORY_FILTERS: PackagingHistoryFilters = {
  q: '',
  suppliers: [],
  from: '',
  to: '',
}

function splitCodes(raw: string | null): string[] {
  if (!raw) return []
  const seen = new Set<string>()
  for (const part of raw.split(',')) {
    const code = part.trim()
    if (code) seen.add(code)
  }
  return [...seen].slice(0, PACKAGING_HISTORY_MAX_CODES)
}

/**
 * Đọc lựa chọn từ URL. `mode` nói rõ thì theo `mode`; không nói thì đường dẫn sâu chỉ có `hh` là chế độ sản phẩm, còn lại là
 * chế độ mã. Mã lặp / rỗng bị bỏ, cắt ở trần.
 */
export function parseHistorySearch(search: URLSearchParams): PackagingHistorySelection {
  const hh = splitCodes(search.get('hh'))
  const codes = splitCodes(search.get('codes'))
  const explicit = search.get('mode')
  const mode: PackagingHistoryMode =
    explicit === 'product' || explicit === 'code'
      ? explicit
      : hh.length > 0 && codes.length === 0
        ? 'product'
        : 'code'
  return { mode, codes, hh }
}

/**
 * Ghi lựa chọn ra chuỗi truy vấn của URL. Giữ CẢ HAI danh sách để đổi chế độ qua lại không mất lựa chọn bên kia; `mode`
 * chỉ ghi khi cần để đọc lại ra đúng chế độ (chế độ mã mà không có mã sản phẩm nào là mặc định nên không ghi).
 */
export function buildHistorySearch(selection: PackagingHistorySelection): Record<string, string> {
  const out: Record<string, string> = {}
  if (selection.mode === 'product' || selection.hh.length > 0) out.mode = selection.mode
  if (selection.codes.length) out.codes = selection.codes.join(',')
  if (selection.hh.length) out.hh = selection.hh.join(',')
  return out
}

/** Đường dẫn tới Lịch sử mua hàng của MỘT mã VTBB — dùng cho ô mã ở các bảng khác. */
export function packagingHistoryHref(code: string): string {
  return `${appRoutes.procurement.packagingHistory}?${new URLSearchParams({ codes: code }).toString()}`
}

/** Đường dẫn tới Lịch sử mua hàng của MỘT sản phẩm (chế độ "Theo mã sản phẩm": mọi mã thành phần của định mức). */
export function packagingHistoryProductHref(hhCode: string): string {
  return `${appRoutes.procurement.packagingHistory}?${new URLSearchParams({ hh: hhCode }).toString()}`
}

/**
 * Lựa chọn + bộ lọc màn hình → tham số gửi máy chủ (danh sách VÀ Xuất Excel dùng chung nên ra cùng thứ tự). Chỉ gửi mã
 * của chế độ đang bật. `sort.by` rỗng = để máy chủ xếp mặc định (ngày mới nhất trước).
 */
export function buildHistoryParams(
  selection: PackagingHistorySelection,
  filters: PackagingHistoryFilters,
  search: string,
  sort: { by: string; dir: 'asc' | 'desc' },
): PackagingHistoryParams {
  const isProduct = selection.mode === 'product'
  return {
    mode: selection.mode,
    codes: !isProduct && selection.codes.length ? selection.codes : undefined,
    hh_codes: isProduct && selection.hh.length ? selection.hh : undefined,
    q: search.trim() || undefined,
    supplier: filters.suppliers.length ? filters.suppliers : undefined,
    date_from: filters.from || undefined,
    date_to: filters.to || undefined,
    ...(sort.by ? { sort_by: sort.by, sort_dir: sort.dir } : {}),
  }
}

/** Điểm biểu đồ: nhãn ngày ngắn cho trục + giá + thông tin hiện ở ô rê chuột. */
export interface HistoryChartPoint extends PackagingHistoryPoint {
  label: string
}

export function buildChartPoints(series: readonly PackagingHistoryPoint[]): HistoryChartPoint[] {
  return series.map((point) => ({ ...point, label: formatDate(point.date) }))
}

/**
 * Trục giá nới ra hai đầu một đoạn (10% biên độ, tối thiểu 2% giá) — đường giá không dính sát khung, và giá đi ngang
 * (min = max) vẫn có khoảng để vẽ. Trục KHÔNG bắt đầu từ 0: biến động vài phần trăm sẽ dẹp lì nếu kéo về 0.
 */
export function priceAxisDomain(prices: readonly number[]): [number, number] {
  if (prices.length === 0) return [0, 1]
  const low = Math.min(...prices)
  const high = Math.max(...prices)
  const pad = Math.max((high - low) * 0.1, high * 0.02, 1)
  return [Math.max(0, Math.floor(low - pad)), Math.ceil(high + pad)]
}
