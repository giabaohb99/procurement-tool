/**
 * bao-CR-800 — trạng thái lọc / xếp / trang DÙNG CHUNG của hai màn Bảng giá VTBB và Bảng giá nguyên liệu (tách từ trang Bảng
 * giá VTBB để màn nguyên liệu không chép lại): bộ lọc, khoảng ngày, cột xếp, trang, cỡ trang — tất cả sống trên URL.
 *
 * URL đọc MỘT lần lúc mở màn, sau đó state là nguồn và URL đi theo (`replace` — chọn mã liên tục không đẻ ra cả chục mục lịch
 * sử của nút Quay lại). `rawMaterial` = màn nguyên liệu: không có phạm vi định mức (`scope` không gửi đi, không ghi URL) và
 * không có cột Số SP đang dùng (URL mang `sort_by=usage` thì bỏ, tránh bảng xếp theo một cột không hiện).
 */
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'

import type { PriceListFilters } from '../components/packaging-price-list-toolbar'
import type { PackagingPriceListParams } from '../types/packaging-cost-types'
import {
  buildPriceListUrlSearch,
  parsePriceListUrlState,
  type PriceListUrlState,
} from '../utils/packaging-list-url-state'

const EMPTY_FILTERS: PriceListFilters = { codes: [], group: '', scope: 'bom' }
const USAGE_SORT_KEY = 'usage'

function readInitialState(search: URLSearchParams, rawMaterial: boolean): PriceListUrlState {
  const state = parsePriceListUrlState(search)
  if (!rawMaterial) return state
  const sortBy = state.sortBy === USAGE_SORT_KEY ? '' : state.sortBy
  return {
    ...state,
    filters: { ...state.filters, scope: EMPTY_FILTERS.scope },
    sortBy,
    sortDir: sortBy ? state.sortDir : 'asc',
  }
}

export function usePackagingPriceListState({ rawMaterial = false }: { rawMaterial?: boolean } = {}) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [initial] = useState(() => readInitialState(searchParams, rawMaterial))
  const [filters, setFilters] = useState<PriceListFilters>(initial.filters)
  const [range, setRange] = useState({ from: initial.from, to: initial.to })
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [pageSize, setPageSize] = useState(initial.pageSize)

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel (không kèm trang). */
  const filterParams = useMemo<PackagingPriceListParams>(
    () => ({
      code: filters.codes.length ? filters.codes : undefined,
      group: filters.group || undefined,
      //  Đường nguyên liệu không có tham số `scope` — không gửi khóa này đi.
      ...(rawMaterial ? {} : { scope: filters.scope }),
      date_from: range.from || undefined,
      date_to: range.to || undefined,
      //  Nhịp thứ ba của tiêu đề cột trả khóa rỗng = thôi xếp → KHÔNG gửi, để máy chủ xếp mặc định.
      ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir } : {}),
    }),
    [filters.codes, filters.group, filters.scope, range, sortBy, sortDir, rawMaterial],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize], initial.page)

  const urlSearch = buildPriceListUrlSearch({
    filters,
    from: range.from,
    to: range.to,
    sortBy,
    sortDir,
    page,
    pageSize,
  })
  useEffect(() => {
    if (urlSearch !== searchParams.toString()) {
      setSearchParams(new URLSearchParams(urlSearch), { replace: true })
    }
  }, [urlSearch, searchParams, setSearchParams])

  return {
    filters,
    setFilters,
    range,
    setRange,
    sortBy,
    sortDir,
    setSort: (by: string, dir: 'asc' | 'desc') => {
      setSortBy(by)
      setSortDir(dir)
    },
    page,
    setPage,
    pageSize,
    setPageSize,
    filterParams,
    /** Tham số của đường danh sách: bộ lọc + trang. */
    listParams: { ...filterParams, page, page_size: pageSize },
    filtersActive:
      filters.codes.length > 0 ||
      filters.group !== '' ||
      filters.scope !== EMPTY_FILTERS.scope ||
      Boolean(range.from || range.to),
    resetFilters: () => {
      setFilters(EMPTY_FILTERS)
      setRange({ from: '', to: '' })
    },
  }
}
