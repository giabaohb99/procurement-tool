// Kiểu dữ liệu cho BỘ LỌC ĐIỀU KIỆN — port logic từ thư viện FilterCN, bỏ lớp UI shadcn/Tailwind
// (dự án dùng plain CSS). Xem README ở `index.ts` để biết các điểm khác biệt so với bản gốc.

/** Loại field → quyết định danh sách operator mặc định và ô nhập giá trị nào được render */
export type FieldType = 'text' | 'number' | 'select' | 'multiselect' | 'date' | 'boolean'

/** Operator — TRÙNG TÊN với hậu tố param backend đọc (app/core/filter_operators.py),
 *  trừ is_empty/is_not_empty vốn cùng dồn về `__isnull=true|false`. */
export type OperatorType =
  | 'eq'            // bằng
  | 'ne'            // khác
  | 'contains'      // chứa
  | 'not_contains'  // không chứa
  | 'gt'            // >
  | 'gte'           // >=
  | 'lt'            // <
  | 'lte'           // <=
  | 'between'       // trong khoảng [từ, đến]
  | 'in'            // thuộc danh sách
  | 'not_in'        // không thuộc danh sách
  | 'is_empty'      // đang trống (NULL hoặc chuỗi rỗng)
  | 'is_not_empty'  // có giá trị

export type SelectOption = { value: string; label: string }

export type FilterFieldDefinition = {
  /** Tên cột — cũng là tên query param. PHẢI nằm trong whitelist FILTERABLE của controller. */
  name: string
  label: string
  type: FieldType
  /** Giới hạn operator cho field này; bỏ trống → lấy mặc định theo `type` */
  operators?: OperatorType[]
  /** Options tĩnh cho select/multiselect */
  options?: SelectOption[]
  /** Nguồn options động từ API — cùng dạng với `FilterField.source` của FilterBar cũ */
  source?: { url: string; value?: string; label?: string }
}

/** Giá trị 1 dòng lọc. Mảng dùng cho between (2 phần tử) và in/not_in (n phần tử). */
export type FilterValue = string | string[] | null

export type FilterRow = {
  id: string
  field: FilterFieldDefinition | null
  operator: OperatorType | null
  value: FilterValue
}

export type Conjunction = 'and' | 'or'

export type FilterState = {
  rows: FilterRow[]
  conjunction: Conjunction
}

/** Query param gửi lên API, dạng `{ 'total__gte': '1000', conjunction: 'or' }`.
 *  Giá trị mảng = cùng 1 cột có nhiều điều kiện → axios lặp key (xem api/client.ts). */
export type RestQueryParams = Record<string, string | string[]>

export type FilterConfig = {
  fields: FilterFieldDefinition[]
  /** Cho phép đổi AND/OR. Mặc định: false (luôn AND) */
  allowConjunctionToggle?: boolean
  /** Số dòng lọc tối đa. Mặc định: 8 */
  maxRows?: number
}
