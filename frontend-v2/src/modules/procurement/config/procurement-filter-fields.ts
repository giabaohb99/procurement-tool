import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import {
  DOCUMENT_STATUSES,
  PO_STATUS_LABELS,
  PR_STATUS_LABELS,
  SR_STATUS_LABELS,
  SURVEY_STATUS_LABELS,
  statusOptions,
} from '../types/purchase-document'

/**
 * Trường của BỘ LỌC NÂNG CAO cho các bảng chứng từ mua hàng.
 *
 * ⚠️ `name` PHẢI nằm trong `service.FILTERABLE` của controller tương ứng, nếu
 * không backend bỏ qua điều kiện và người dùng tưởng bộ lọc hỏng. Những tham số
 * lọc QUA BẢNG CON (company_id, item_group, assignee, invoice_no, product_code)
 * không đi qua `apply_filters` nên KHÔNG khai ở đây — chúng nằm ở thanh công cụ.
 */

const STATUS_OPERATORS = ['is', 'is_not', 'in', 'not_in'] as const

export const PURCHASE_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã PYC', type: 'text' },
  { name: 'requester', label: 'Người yêu cầu', type: 'text' },
  { name: 'department', label: 'Bộ phận yêu cầu', type: 'text' },
  { name: 'request_date', label: 'Ngày tạo', type: 'date' },
  { name: 'need_date', label: 'Ngày cần hàng', type: 'date' },
  { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean', operators: ['is'] },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(PR_STATUS_LABELS),
  },
]

export const SURVEY_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã phiếu', type: 'text' },
  { name: 'requester', label: 'Người yêu cầu', type: 'text' },
  { name: 'department', label: 'Bộ phận', type: 'text' },
  { name: 'request_date', label: 'Ngày tạo', type: 'date' },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(SR_STATUS_LABELS),
  },
]

export const PURCHASE_ORDER_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã ĐMH', type: 'text' },
  { name: 'misa_code', label: 'Mã MISA', type: 'text' },
  { name: 'pr_code', label: 'Mã PYC', type: 'text' },
  { name: 'supplier_code', label: 'Mã nhà cung cấp', type: 'text' },
  { name: 'nspt', label: 'NSPT phụ trách', type: 'text' },
  { name: 'department', label: 'Bộ phận', type: 'text' },
  { name: 'order_date', label: 'Ngày đặt', type: 'date' },
  { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean', operators: ['is'] },
  {
    name: 'document_status',
    label: 'Hồ sơ chứng từ',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: DOCUMENT_STATUSES.map((value) => ({ value, label: value })),
  },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(PO_STATUS_LABELS),
  },
]

export const SURVEY_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã phiếu', type: 'text' },
  { name: 'sr_code', label: 'Mã YCBG', type: 'text' },
  { name: 'pr_code', label: 'Mã PYC', type: 'text' },
  { name: 'main_content', label: 'Nội dung chính', type: 'text' },
  { name: 'item_code', label: 'Mã hàng', type: 'text' },
  { name: 'nspt', label: 'NSPT', type: 'text' },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(SURVEY_STATUS_LABELS),
  },
]
