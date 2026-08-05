// Bộ lọc điều kiện — port logic từ FilterCN (https://filtercn.vercel.app), bỏ lớp UI
// shadcn/ui + Tailwind vì frontend này dùng plain CSS + react-router (không phải Next.js).
//
// Giữ nguyên từ bản gốc: mô hình dòng lọc (field × operator × value), toggle AND/OR,
// tách helpers (query-builder / serializer / validators), hook state, provider + context.
//
// Đã đổi có chủ ý:
//  1. Operator "bằng" sinh param `field__eq` thay vì param trần `field` — vì param trần ở dự án
//     này đã mang nghĩa LIKE %val% và hàng chục màn hình đang dựa vào đó.
//  2. Đồng bộ URL viết lại cho react-router (bản gốc dùng next/navigation).
//  3. Bỏ paramStyle "bracket"/"custom", bỏ ô tìm kiếm toàn cục — chưa có nhu cầu (YAGNI).
//  4. Ô nhập dùng lại DateInput / NumberInput / SearchSelect sẵn có để không lệch giao diện.
//
// Backend đọc param này ở app/core/filter_operators.py.

export { ConditionalFilter, ConditionalFilterButton } from './conditional-filter-bar'
export { FilterProvider } from './provider/filter-provider'
export { useFilterContext } from './provider/filter-context'
export { buildRestQuery, buildQueryFromState } from './helpers/query-builder'
export {
  deserializeParamsToState, isFilterParam, readParamsFromUrl, serializeFiltersToPairs,
} from './helpers/serializer'
export { getValidFilterRows, isValidFilterRow } from './helpers/validators'
export { DEFAULT_OPERATORS, OPERATOR_LABELS, operatorLabel } from './constants'
export type {
  Conjunction, FieldType, FilterConfig, FilterFieldDefinition, FilterRow,
  FilterState, FilterValue, OperatorType, RestQueryParams, SelectOption,
} from './types'
