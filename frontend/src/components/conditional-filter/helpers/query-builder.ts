import { isnullValue, paramKey } from './operators'
import { getValidFilterRows } from './validators'
import type { FilterRow, FilterState, RestQueryParams } from '../types'

/** Chuẩn hóa giá trị 1 dòng lọc thành chuỗi param.
 *  - between → "từ,đến" (hở đầu nào thì để trống đầu đó)
 *  - in/not_in → "a,b,c"
 *  - is_empty/is_not_empty → "true"/"false" */
function paramValue(row: FilterRow): string {
  const op = row.operator!
  if (op === 'is_empty' || op === 'is_not_empty') return isnullValue(op)
  if (op === 'between') {
    const [from = '', to = ''] = Array.isArray(row.value) ? row.value : []
    return `${from ?? ''},${to ?? ''}`
  }
  if (Array.isArray(row.value)) return row.value.filter(Boolean).join(',')
  return String(row.value ?? '')
}

/** Danh sách dòng lọc → query param gửi API.
 *  Hai dòng trùng (field, operator) sẽ được gộp thành MẢNG → axios lặp key (xem api/client.ts). */
export function buildRestQuery(rows: FilterRow[]): RestQueryParams {
  const params: RestQueryParams = {}

  getValidFilterRows(rows).forEach((row) => {
    const key = paramKey(row.field!.name, row.operator!)
    const value = paramValue(row)
    const existing = params[key]
    if (existing === undefined) params[key] = value
    else if (Array.isArray(existing)) existing.push(value)
    else params[key] = [existing, value]
  })

  return params
}

/** Query param đầy đủ của bộ lọc, gồm cả `conjunction` khi người dùng chọn OR. */
export function buildQueryFromState(state: FilterState): RestQueryParams {
  const params = buildRestQuery(state.rows)
  // Chỉ gửi conjunction khi thực sự có từ 2 điều kiện — 1 điều kiện thì AND/OR như nhau
  if (state.conjunction === 'or' && Object.keys(params).length > 0) params.conjunction = 'or'
  return params
}
