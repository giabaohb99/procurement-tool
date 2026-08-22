import type { FilterFieldDefinition, OperatorType } from '@/shared/conditional-filter'
import { PO_DOCUMENT_STATUS } from '@/shared/constants/statuses'
import {
  PO_STATUS_LABELS,
  PR_STATUS_LABELS,
  SR_STATUS_LABELS,
  SURVEY_STATUS_LABELS,
  SURVEY_TYPE_LABELS,
  statusOptions,
} from '../types/purchase-document'
import { fetchCompanyOptions, fetchDepartmentOptions, fetchEmployeeOptions } from './ref-filter-options'

/**
 * Trường của BỘ LỌC NÂNG CAO cho các bảng chứng từ mua hàng.
 */

const STATUS_OPERATORS = ['is', 'is_not', 'in', 'not_in'] as const

/** Ô tham chiếu chỉ để `bằng` / `khác`. */
const REF_OPERATORS: OperatorType[] = ['is', 'is_not']

const COMPANY_FIELD: FilterFieldDefinition = {
  name: 'company_id',
  label: 'Công ty',
  type: 'combobox',
  operators: REF_OPERATORS,
  fetchOptions: fetchCompanyOptions,
}

/** Ô phòng ban dùng chung — mỗi màn chỉ khác cái nhãn ("Bộ phận" / "Bộ phận yêu cầu"). */
const DEPARTMENT_FIELD: Omit<FilterFieldDefinition, 'label'> = {
  name: 'department_id',
  type: 'combobox',
  operators: REF_OPERATORS,
  fetchOptions: fetchDepartmentOptions,
}

/** Ô nhân sự dùng chung — `name` khác nhau theo vai trò (người yêu cầu / NSPT). */
const EMPLOYEE_FIELD: Omit<FilterFieldDefinition, 'label' | 'name'> = {
  type: 'combobox',
  operators: REF_OPERATORS,
  fetchOptions: fetchEmployeeOptions,
}

export const PURCHASE_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã PYC', type: 'text' },
  COMPANY_FIELD,
  { ...EMPLOYEE_FIELD, name: 'requester_id', label: 'Người yêu cầu' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận yêu cầu' },
  { name: 'purpose', label: 'Mục đích', type: 'text' },
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
  COMPANY_FIELD,
  { ...EMPLOYEE_FIELD, name: 'requester_id', label: 'Người yêu cầu' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận yêu cầu' },
  { name: 'purpose', label: 'Mục đích', type: 'text' },
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
  COMPANY_FIELD,
  { name: 'supplier_code', label: 'Mã nhà cung cấp', type: 'text' },
  { ...EMPLOYEE_FIELD, name: 'nspt_id', label: 'NSPT phụ trách' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận' },
  { name: 'order_date', label: 'Ngày đặt', type: 'date' },
  { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean', operators: ['is'] },
  {
    name: 'document_status',
    label: 'Hồ sơ chứng từ',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: PO_DOCUMENT_STATUS.map(({ value, label }) => ({ value, label })),
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
  { name: 'code', label: 'Mã phiếu khảo sát', type: 'text' },
  {
    name: 'survey_type',
    label: 'Loại khảo sát',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: Object.entries(SURVEY_TYPE_LABELS).map(([k, v]) => ({ value: k, label: v })),
  },
  { name: 'sr_code', label: 'Mã YCBG', type: 'text' },
  { name: 'pr_code', label: 'Mã PYC', type: 'text' },
  { name: 'main_content', label: 'Nội dung chính', type: 'text' },
  { name: 'item_code', label: 'Mã hàng', type: 'text' },
  { name: 'item_group', label: 'Nhóm hàng', type: 'text' },
  { name: 'nspt', label: 'NSPT', type: 'text' },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(SURVEY_STATUS_LABELS),
  },
]
