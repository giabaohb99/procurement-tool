/**
 * PHẠM VI ÁP DỤNG của văn bản (F01–F05).
 *
 * Ba quy tắc, giao diện phải nói ra quy tắc thứ ba:
 *  1. các dòng bao gồm cộng dồn;
 *  2. loại trừ luôn thắng;
 *  3. **không có dòng nào = áp cho toàn bộ pháp nhân ban hành** — mọi phòng ban,
 *     mọi nhân sự của chính công ty đứng tên, và chỉ công ty đó.
 */

export const SCOPE_DIM = {
  company: 1,
  department: 2,
  employee: 3,
} as const

export const SCOPE_MODE = {
  include: 1,
  exclude: 2,
} as const

export interface DocumentScope {
  id: number
  document_id: number
  dim: number
  mode: number
  company_id: number | null
  company_name: string
  department_id: number | null
  department_name: string
  employee_id: number | null
  employee_name: string
  /** Chọn Tập đoàn kèm cờ này thì áp cho mọi công ty con hiện tại và tương lai. */
  include_children: boolean
}

export interface DocumentScopeList {
  items: DocumentScope[]
  /** Chưa khai dòng nào — văn bản áp trong đúng pháp nhân ban hành (quy tắc 3). */
  default_to_issuer: boolean
  /** Tên pháp nhân ban hành, để nói thẳng "toàn bộ CÔNG TY A" thay vì nói chung chung. */
  issuer_company_name: string
}

export interface DocumentScopeInput {
  dim: number
  mode: number
  company_id?: number | null
  department_id?: number | null
  employee_id?: number | null
  include_children?: boolean
}

export interface ScopeOption {
  value: number
  label: string
}

/** Nhãn tiếng Việt do backend cấp — giao diện không chép cứng. */
export interface ScopeOptions {
  dims: ScopeOption[]
  modes: ScopeOption[]
}
