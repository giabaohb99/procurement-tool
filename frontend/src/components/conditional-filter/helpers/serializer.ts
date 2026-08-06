import { DEFAULT_OPERATORS } from '../constants'
import { newRowId } from './new-row-id'
import { operatorFromSuffix } from './operators'
import { buildQueryFromState } from './query-builder'
import type {
  FilterFieldDefinition, FilterRow, FilterState, FilterValue, OperatorType, RestQueryParams,
} from '../types'

export const CONJUNCTION_PARAM = 'conjunction'

/** Trạng thái bộ lọc → cặp (key, value) để ghi lên URL */
export function serializeFiltersToPairs(state: FilterState): [string, string][] {
  const pairs: [string, string][] = []
  Object.entries(buildQueryFromState(state)).forEach(([key, value]) => {
    if (Array.isArray(value)) value.forEach((v) => pairs.push([key, v]))
    else pairs.push([key, value])
  })
  return pairs
}

/** Param này có do bộ lọc điều kiện quản lý không (để xóa sạch trước khi ghi bộ mới)?
 *  Chỉ nhận param `<field>__<op>` với field nằm trong cấu hình → không đụng page/sort/filter cũ. */
export function isFilterParam(key: string, fields: FilterFieldDefinition[]): boolean {
  if (key === CONJUNCTION_PARAM) return true
  const at = key.lastIndexOf('__')
  if (at <= 0) return false
  const name = key.slice(0, at)
  const suffix = key.slice(at + 2)
  // rawValue='' chỉ ảnh hưởng việc phân biệt is_empty/is_not_empty — ở đây chỉ cần biết hợp lệ
  return operatorFromSuffix(suffix, '') !== null && fields.some((f) => f.name === name)
}

function parseValue(operator: OperatorType, raw: string): FilterValue {
  if (operator === 'between') {
    const [from = '', to = ''] = raw.split(',')
    return [from, to]
  }
  if (operator === 'in' || operator === 'not_in') return raw.split(',').filter(Boolean)
  if (operator === 'is_empty' || operator === 'is_not_empty') return null
  return raw
}

/** URL → trạng thái bộ lọc. Param lạ / field ngoài cấu hình bị bỏ qua (người dùng sửa tay URL). */
export function deserializeParamsToState(
  params: URLSearchParams, fields: FilterFieldDefinition[],
): FilterState {
  const rows: FilterRow[] = []

  params.forEach((raw, key) => {
    if (key === CONJUNCTION_PARAM) return
    const at = key.lastIndexOf('__')
    if (at <= 0) return

    const field = fields.find((f) => f.name === key.slice(0, at))
    if (!field) return

    const operator = operatorFromSuffix(key.slice(at + 2), raw)
    if (!operator) return

    // Operator phải nằm trong danh sách cho phép của field (vd cột select thì không có "lớn hơn").
    // Chặn ở đây để URL sửa tay không tạo ra dòng lọc hiện mã thô, sửa không được.
    const allowed = field.operators || DEFAULT_OPERATORS[field.type] || []
    if (!allowed.includes(operator)) return

    rows.push({ id: newRowId(), field, operator, value: parseValue(operator, raw) })
  })

  return { rows, conjunction: params.get(CONJUNCTION_PARAM) === 'or' ? 'or' : 'and' }
}

/** URL → query param gửi API. Dùng cho lần nạp ĐẦU TIÊN của trang danh sách (mở link chia sẻ,
 *  F5 giữa chừng), khi provider chưa kịp bắn onChange. */
export function readParamsFromUrl(
  params: URLSearchParams, fields: FilterFieldDefinition[],
): RestQueryParams {
  return buildQueryFromState(deserializeParamsToState(params, fields))
}
