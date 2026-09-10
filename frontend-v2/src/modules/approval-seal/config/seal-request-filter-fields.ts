import type { FilterFieldDefinition, OperatorType } from '@/shared/conditional-filter'
import {
  fetchCompanyOptions,
  fetchDepartmentOptions,
  fetchEmployeeOptions,
} from '@/shared/filters/ref-filter-options'
import { SEAL_STATUS_LABELS } from '../types/seal-request'

/**
 * Trường của BỘ LỌC NÂNG CAO cho danh sách Yêu cầu đóng dấu — chỉ khai trường
 * backend lọc được (`service.FILTERABLE`): công ty / bộ phận / người yêu cầu /
 * trạng thái. Mã & mục đích để ô Tìm kiếm nhanh; ngày tạo dùng ô khoảng ngày riêng.
 */
const STATUS_OPERATORS = ['is', 'is_not', 'in', 'not_in'] as const
const REF_OPERATORS: OperatorType[] = ['is', 'is_not']

const toOptions = (labels: Record<number, string>) =>
  Object.entries(labels).map(([value, label]) => ({ value, label }))

export const SEAL_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'company_id', label: 'Công ty', type: 'combobox', operators: REF_OPERATORS, fetchOptions: fetchCompanyOptions },
  { name: 'department_id', label: 'Bộ phận', type: 'combobox', operators: REF_OPERATORS, fetchOptions: fetchDepartmentOptions },
  { name: 'requester_id', label: 'Người yêu cầu', type: 'combobox', operators: REF_OPERATORS, fetchOptions: fetchEmployeeOptions },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: toOptions(SEAL_STATUS_LABELS),
  },
]
