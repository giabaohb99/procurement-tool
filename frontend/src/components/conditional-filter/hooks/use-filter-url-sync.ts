import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getValidFilterRows } from '../helpers/validators'
import {
  deserializeParamsToState, isFilterParam, serializeFiltersToPairs,
} from '../helpers/serializer'
import type { FilterFieldDefinition, FilterState } from '../types'

/** Đồng bộ bộ lọc với URL — bản viết lại của hook cùng tên trong FilterCN cho react-router
 *  (bản gốc dùng next/navigation). URL là NGUỒN SỰ THẬT: bấm back/forward, gửi link cho đồng
 *  nghiệp, hay F5 đều ra đúng bộ lọc đó.
 */
export function useFilterUrlSync(fields: FilterFieldDefinition[]) {
  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.toString()

  /** Bộ lọc hiện đang có hiệu lực, đọc ngược từ URL */
  const urlState = useMemo(
    () => deserializeParamsToState(new URLSearchParams(search), fields),
    [search, fields],
  )

  /** Ghi bộ lọc lên URL. Giữ nguyên mọi param KHÔNG thuộc bộ lọc (page, sort, filter cơ bản…). */
  const applyToUrl = useCallback((state: FilterState) => {
    const next = new URLSearchParams()
    new URLSearchParams(search).forEach((value, key) => {
      if (!isFilterParam(key, fields)) next.append(key, value)
    })
    const valid: FilterState = { ...state, rows: getValidFilterRows(state.rows) }
    serializeFiltersToPairs(valid).forEach(([key, value]) => next.append(key, value))
    setSearchParams(next)
  }, [search, fields, setSearchParams])

  return { urlState, applyToUrl }
}
