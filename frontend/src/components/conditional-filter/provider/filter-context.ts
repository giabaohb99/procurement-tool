import { createContext, useContext } from 'react'
import type { FilterStateApi } from '../hooks/use-filter-state'
import type { FilterConfig, FilterFieldDefinition, SelectOption } from '../types'

export type FilterContextValue = FilterStateApi & {
  config: FilterConfig
  /** Options dùng được cho 1 field (tĩnh hoặc nạp từ API) */
  optionsOf: (field: FilterFieldDefinition) => SelectOption[]
  /** Ghi state nháp lên URL → danh sách nạp lại */
  apply: () => void
  /** Xóa hết điều kiện VÀ áp dụng luôn */
  clearAll: () => void
  /** Số điều kiện đang thực sự có hiệu lực (đọc từ URL) */
  activeCount: number
  /** State nháp đã khác với cái đang áp dụng chưa → bật/tắt nút "Áp dụng" */
  dirty: boolean
}

export const FilterContext = createContext<FilterContextValue | null>(null)

export function useFilterContext(): FilterContextValue {
  const ctx = useContext(FilterContext)
  if (!ctx) throw new Error('useFilterContext phải nằm trong <FilterProvider>')
  return ctx
}
