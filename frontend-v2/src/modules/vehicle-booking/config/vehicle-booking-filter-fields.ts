import type { FilterFieldDefinition, OperatorType } from '@/shared/conditional-filter'
import {
  fetchCompanyOptions,
  fetchDepartmentOptions,
  fetchEmployeeOptions,
} from '@/shared/filters/ref-filter-options'
import { BOOKING_STATUS_LABELS, REQUEST_TYPE_LABELS } from '../types/vehicle-booking'

/**
 * Trường của BỘ LỌC NÂNG CAO (nút "Bộ lọc") cho danh sách Yêu cầu đặt xe. Chỉ khai
 * những trường backend LỌC ĐƯỢC (`service.FILTERABLE`): công ty / bộ phận / người
 * yêu cầu / loại / trạng thái. Mã & mục đích để ô Tìm kiếm nhanh lo; ngày tạo dùng
 * ô chọn khoảng ngày riêng (map sang `created_at_from/to`).
 */
const STATUS_OPERATORS = ['is', 'is_not', 'in', 'not_in'] as const
const REF_OPERATORS: OperatorType[] = ['is', 'is_not']

const toOptions = (labels: Record<number, string>) =>
  Object.entries(labels).map(([value, label]) => ({ value, label }))

export const VEHICLE_BOOKING_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'company_id', label: 'Công ty', type: 'combobox', operators: REF_OPERATORS, fetchOptions: fetchCompanyOptions },
  { name: 'department_id', label: 'Bộ phận', type: 'combobox', operators: REF_OPERATORS, fetchOptions: fetchDepartmentOptions },
  { name: 'requester_id', label: 'Người yêu cầu', type: 'combobox', operators: REF_OPERATORS, fetchOptions: fetchEmployeeOptions },
  {
    name: 'request_type',
    label: 'Loại yêu cầu',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: toOptions(REQUEST_TYPE_LABELS),
  },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: toOptions(BOOKING_STATUS_LABELS),
  },
]
