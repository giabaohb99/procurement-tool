/**
 * duoc-CR-784 — lựa chọn của màn TÁC ĐỘNG GIÁ BAO BÌ <-> chuỗi truy vấn URL (người chủ chốt 26/11/2026): F5 hay gửi link
 * cho người khác là mở lại đúng mã đã chọn, giá giả định, khoảng ngày tính min–max, ô tìm + điều kiện lọc + cột xếp + trang
 * của bảng sản phẩm.
 *
 * Không đặt ra định dạng mới: dựng và đọc qua CHÍNH hai hàm của bản in (`buildImpactPrintSearch` / `parseImpactPrintSearch`
 * — đã kiểm mã, trần 500 mã, giá giả định > 0 và chỉ cho mã đang chọn, ngày ISO, khóa xếp máy chủ nhận), thêm `page`. Cùng
 * tên tham số với bản v1: `codes=A,B` · `assumed=A:4500,B:300` · `date_from` / `date_to` · `q` · `sort_by` / `sort_dir` ·
 * `page` · tên trường lọc của máy chủ.
 */
import type { ImpactAdvancedFilters } from './packaging-impact-filters'
import { EMPTY_IMPACT_FILTERS, impactFiltersToRequest } from './packaging-impact-filters'
import { advancedFiltersFromSearch, parsePageParam } from './packaging-filter-url'
import { buildImpactPrintSearch, parseImpactPrintSearch } from './packaging-impact-print'

export interface ImpactUrlState {
  codes: string[]
  /** Giá giả định theo mã (chỉ mã đang chọn, giá > 0). */
  assumed: Record<string, number>
  dateFrom: string
  dateTo: string
  /** Từ khóa ô tìm của bảng sản phẩm (đã bỏ khoảng trắng hai đầu). */
  q: string
  filters: ImpactAdvancedFilters
  /** Rỗng = chưa chọn cột xếp. */
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
}

export const EMPTY_IMPACT_URL_STATE: ImpactUrlState = {
  codes: [],
  assumed: {},
  dateFrom: '',
  dateTo: '',
  q: '',
  filters: EMPTY_IMPACT_FILTERS,
  sortBy: '',
  sortDir: 'asc',
  page: 1,
}

/** URL → trạng thái màn. Mọi trường đã kiểm (URL là dữ liệu từ ngoài vào); thứ hỏng rơi về mặc định. */
export function parseImpactUrlState(search: URLSearchParams): ImpactUrlState {
  const request = parseImpactPrintSearch(search)
  return {
    codes: request.codes,
    assumed: request.assumed_prices ?? {},
    dateFrom: request.date_from ?? '',
    dateTo: request.date_to ?? '',
    q: request.q ?? '',
    filters: advancedFiltersFromSearch(search, 'impact'),
    sortBy: request.sort_by ?? '',
    sortDir: request.sort_dir ?? 'asc',
    page: parsePageParam(search.get('page')),
  }
}

/** Trạng thái màn → chuỗi truy vấn (không kèm `?`). Chưa chọn mã thì không ghi `codes`; trang 1 không ghi `page`. */
export function buildImpactUrlSearch(state: ImpactUrlState): string {
  const picked = new Set(state.codes)
  const assumed = Object.fromEntries(
    Object.entries(state.assumed).filter(([code, price]) => picked.has(code) && price > 0),
  )
  const search = new URLSearchParams(
    buildImpactPrintSearch({
      codes: state.codes,
      assumed_prices: assumed,
      date_from: state.dateFrom || undefined,
      date_to: state.dateTo || undefined,
      q: state.q.trim() || undefined,
      ...impactFiltersToRequest(state.filters),
      ...(state.sortBy ? { sort_by: state.sortBy, sort_dir: state.sortDir } : {}),
    }),
  )
  if (!state.codes.length) search.delete('codes')
  if (state.page > 1) search.set('page', String(state.page))
  return search.toString()
}
