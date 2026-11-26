/**
 * duoc-CR-784 — trạng thái của bảng SẢN PHẨM BỊ ẢNH HƯỞNG (tìm / lọc nâng cao / xếp / trang) — nằm ở màn chứ không ở bảng vì
 * chúng là một phần của thân `POST /impact` (máy chủ phân trang, luật §8).
 *
 * Trang tự về 1 khi đổi từ khóa (đã hoãn 250 ms, không theo ô nhập thô), lọc nâng cao, cột xếp, cỡ trang, hoặc các khóa màn truyền
 * vào (`resetKeys`: danh sách mã đã chọn, khoảng ngày). Giá giả định KHÔNG nằm trong đó: gõ giá không làm người xem
 * nhảy khỏi trang đang đọc.
 */
import { useState } from 'react'

import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'

import {
  EMPTY_IMPACT_FILTERS,
  countImpactFilters,
  type ImpactAdvancedFilters,
} from '../utils/packaging-impact-filters'

export const PACKAGING_IMPACT_PAGE_SIZE = 100

export interface PackagingImpactTableState {
  keyword: string
  setKeyword: (value: string) => void
  /** Từ khóa đã hoãn, đã bỏ khoảng trắng hai đầu — thứ thật sự gửi máy chủ. */
  query: string
  /** Lọc nâng cao ĐANG ÁP (dạng biểu mẫu); gửi máy chủ qua `impactFiltersToRequest`. */
  filters: ImpactAdvancedFilters
  setFilters: (filters: ImpactAdvancedFilters) => void
  /** Số nhóm điều kiện lọc nâng cao đang bật. */
  filterCount: number
  /** Xóa cả từ khóa lẫn lọc nâng cao (giữ cột xếp). */
  resetFilters: () => void
  /** Rỗng = chưa chọn cột xếp (máy chủ xếp mặc định theo mã HH). */
  sortBy: string
  sortDir: 'asc' | 'desc'
  setSort: (by: string, dir: 'asc' | 'desc') => void
  pageSize: number
  setPageSize: (size: number) => void
  page: number
  setPage: (page: number) => void
}

/** Trạng thái lúc mở màn — đọc từ URL (`parseImpactUrlState`); thiếu thì bảng mở trống như trước. */
export interface PackagingImpactTableInitial {
  q: string
  filters: ImpactAdvancedFilters
  sortBy: string
  sortDir: 'asc' | 'desc'
  page: number
}

const EMPTY_INITIAL: PackagingImpactTableInitial = {
  q: '',
  filters: EMPTY_IMPACT_FILTERS,
  sortBy: '',
  sortDir: 'asc',
  page: 1,
}

export function usePackagingImpactTableState(
  resetKeys: readonly unknown[],
  initial: PackagingImpactTableInitial = EMPTY_INITIAL,
): PackagingImpactTableState {
  const [keyword, setKeyword] = useState(initial.q)
  const query = useDebouncedValue(keyword, 250).trim()
  const [filters, setFilters] = useState<ImpactAdvancedFilters>(initial.filters)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [pageSize, setPageSize] = useState(PACKAGING_IMPACT_PAGE_SIZE)
  const [page, setPage] = usePageResetOnFilterChange(
    [...resetKeys, query, filters, sortBy, sortDir, pageSize],
    initial.page,
  )

  return {
    keyword,
    setKeyword,
    query,
    filters,
    setFilters,
    filterCount: countImpactFilters(filters),
    resetFilters: () => {
      setKeyword('')
      setFilters(EMPTY_IMPACT_FILTERS)
    },
    sortBy,
    sortDir,
    setSort: (by, dir) => {
      setSortBy(by)
      setSortDir(dir)
    },
    pageSize,
    setPageSize,
    page,
    setPage,
  }
}
