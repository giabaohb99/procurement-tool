/**
 * TRƯỜNG THÔNG TIN ĐỘNG — cho phép khai thêm ô nhập cho văn bản mà không phải
 * sửa code: hợp đồng cần "Giá trị hợp đồng", quyết định cần "Ngày hiệu lực"…
 *
 * Giá trị nhập vào lưu trong `DocumentRecord.field_values`, tra theo `code` chứ
 * không theo id — đổi thứ tự hay xóa rồi thêm lại trường khác cũng không làm
 * lệch dữ liệu cũ.
 */
export type DynamicFieldType = 'text' | 'textarea' | 'number' | 'date' | 'select' | 'checkbox'

export const DYNAMIC_FIELD_TYPE_LABELS: Record<DynamicFieldType, string> = {
  text: 'Một dòng chữ',
  textarea: 'Nhiều dòng chữ',
  number: 'Số',
  date: 'Ngày',
  select: 'Chọn từ danh sách',
  checkbox: 'Có / không',
}

export interface DynamicField {
  id: number
  /** Khóa lưu giá trị — không dấu, viết thường, vd `contract_value`. */
  code: string
  label: string
  field_type: DynamicFieldType
  /** Chỉ dùng cho `select`; mỗi dòng một lựa chọn. */
  options: string[]
  is_required: boolean
  /** Rỗng = áp dụng cho MỌI loại văn bản. */
  document_type_ids: number[]
  help_text: string
  /** Nhỏ hiện trước. */
  sort_order: number
  is_active: boolean
}

export const DEFAULT_DYNAMIC_FIELDS: DynamicField[] = [
  {
    id: 1,
    code: 'contract_value',
    label: 'Giá trị hợp đồng',
    field_type: 'number',
    options: [],
    is_required: false,
    document_type_ids: [5],
    help_text: 'Giá trị trước thuế, đơn vị đồng.',
    sort_order: 1,
    is_active: true,
  },
  {
    id: 2,
    code: 'contract_partner_signer',
    label: 'Người ký phía đối tác',
    field_type: 'text',
    options: [],
    is_required: false,
    document_type_ids: [5],
    help_text: '',
    sort_order: 2,
    is_active: true,
  },
  {
    id: 3,
    code: 'scope',
    label: 'Phạm vi áp dụng',
    field_type: 'select',
    options: ['Toàn công ty', 'Một bộ phận', 'Một dự án'],
    is_required: false,
    document_type_ids: [],
    help_text: 'Văn bản này áp dụng cho ai.',
    sort_order: 3,
    is_active: true,
  },
]
