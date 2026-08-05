import { ReactNode, useCallback, useEffect, useMemo, useRef } from 'react'
import { buildQueryFromState } from '../helpers/query-builder'
import { getValidFilterRows } from '../helpers/validators'
import { useFilterOptions } from '../hooks/use-filter-options'
import { useFilterState } from '../hooks/use-filter-state'
import { useFilterUrlSync } from '../hooks/use-filter-url-sync'
import type { FilterConfig, RestQueryParams } from '../types'
import { FilterContext, FilterContextValue } from './filter-context'

/**
 * Nối 3 mảnh lại: state nháp (useFilterState) ⇄ URL (useFilterUrlSync) → query param cho API.
 *
 * Luồng dữ liệu một chiều, URL là nguồn sự thật:
 *   sửa trong bảng lọc → state nháp → bấm "Áp dụng" → ghi URL → onChange(params) → gọi API.
 * Nhờ vậy back/forward của trình duyệt và link chia sẻ đều chạy đúng mà không cần code thêm.
 */
export function FilterProvider({
  config, onChange, children,
}: {
  config: FilterConfig
  /** Gọi mỗi khi bộ lọc có hiệu lực đổi (kể cả do bấm back) — nhận query param để gửi API */
  onChange?: (params: RestQueryParams) => void
  children: ReactNode
}) {
  const { fields } = config
  const { urlState, applyToUrl } = useFilterUrlSync(fields)
  const draft = useFilterState(urlState)
  const optionsOf = useFilterOptions(fields)

  const { overrideState } = draft
  const urlKey = JSON.stringify(
    getValidFilterRows(urlState.rows).map((r) => [r.field!.name, r.operator, r.value]),
  ) + '|' + urlState.conjunction

  // URL đổi (áp dụng, xóa chip, back/forward, đổi màn hình) → nạp lại state nháp cho khớp
  useEffect(() => { overrideState(urlState) }, [urlKey, overrideState])

  // Báo bộ lọc có hiệu lực ra ngoài. Chỉ bắn khi param THỰC SỰ đổi để danh sách không nạp lặp.
  const params = useMemo(() => buildQueryFromState(urlState), [urlKey])
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange
  const firstRun = useRef(true)
  useEffect(() => {
    if (firstRun.current) { firstRun.current = false; return }   // lần đầu do CrudList tự nạp
    onChangeRef.current?.(params)
  }, [params])

  const apply = useCallback(() => applyToUrl(draft.state), [applyToUrl, draft.state])
  const clearAll = useCallback(() => applyToUrl({ rows: [], conjunction: 'and' }), [applyToUrl])

  const draftKey = JSON.stringify(
    getValidFilterRows(draft.state.rows).map((r) => [r.field!.name, r.operator, r.value]),
  ) + '|' + draft.state.conjunction

  const value: FilterContextValue = {
    ...draft,
    config,
    optionsOf,
    apply,
    clearAll,
    activeCount: getValidFilterRows(urlState.rows).length,
    dirty: draftKey !== urlKey,
  }

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>
}
