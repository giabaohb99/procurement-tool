import {
  DEFAULT_DOCUMENT_PARTNERS,
  type DocumentPartner,
} from '../types/document-partner'
import { DEFAULT_DYNAMIC_FIELDS, type DynamicField } from '../types/dynamic-field'
import { DEFAULT_SECURITY_LEVELS, type SecurityLevel } from '../types/security-level'
import { createLocalCollection } from './local-collection'

/**
 * Kho tạm của ba danh mục phụ: mức mật/khẩn, đối tác, trường thông tin động.
 * Gom một file vì mỗi cái chỉ là một khai báo — xem `local-collection.ts`.
 */

export const securityLevelCollection = createLocalCollection<SecurityLevel>({
  storageKey: 'erp.document-security-levels',
  seed: DEFAULT_SECURITY_LEVELS,
  labels: {
    code: 'mã',
    name: 'tên',
    kind: 'thang đo',
    rank: 'thứ bậc',
    description: 'mô tả',
    is_active: 'trạng thái',
  },
})

export const documentPartnerCollection = createLocalCollection<DocumentPartner>({
  storageKey: 'erp.document-partners',
  seed: DEFAULT_DOCUMENT_PARTNERS,
  labels: {
    code: 'mã',
    name: 'tên',
    kind: 'nhóm',
    contact_person: 'người liên hệ',
    phone: 'điện thoại',
    email: 'email',
    address: 'địa chỉ',
    is_active: 'trạng thái',
  },
})

export const dynamicFieldCollection = createLocalCollection<DynamicField>({
  storageKey: 'erp.document-dynamic-fields',
  seed: DEFAULT_DYNAMIC_FIELDS,
  labels: {
    code: 'khóa',
    label: 'nhãn',
    field_type: 'kiểu dữ liệu',
    options: 'danh sách lựa chọn',
    is_required: 'bắt buộc',
    document_type_ids: 'loại văn bản áp dụng',
    help_text: 'chú thích',
    sort_order: 'thứ tự',
    is_active: 'trạng thái',
  },
})
