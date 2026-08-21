import { supplierApi } from '@/modules/production/api/supplier-api'
import type { FilterFieldDefinition, SelectOption } from '@/shared/conditional-filter'
import { CONTRACT_TYPE_OPTIONS } from './contract-type-options'

async function fetchSupplierCodeOptions(search: string): Promise<SelectOption[]> {
  const res = await supplierApi.list({ name: search, is_active: true, page_size: 50 })
  return res.items.map((item) => ({
    value: item.code,
    label: `${item.name} (${item.code})`,
  }))
}

export const CONTRACT_FILTER_FIELDS: FilterFieldDefinition[] = [
  {
    name: 'code',
    label: 'Số hợp đồng',
    type: 'text',
  },
  {
    name: 'title',
    label: 'Tên / Trích yếu hợp đồng',
    type: 'text',
  },
  {
    name: 'party_type',
    label: 'Bên ký kết (Loại đối tác)',
    type: 'select',
    options: [
      { value: 'Nhà cung cấp', label: 'Nhà cung cấp' },
      { value: 'Khách hàng', label: 'Khách hàng' },
      { value: 'Khác', label: 'Khác' },
    ],
  },
  {
    name: 'party_code',
    label: 'Nhà cung cấp',
    type: 'combobox',
    operators: ['is', 'is_not'],
    fetchOptions: fetchSupplierCodeOptions,
  },
  {
    name: 'party_name',
    label: 'Tên đối tác',
    type: 'text',
  },
  {
    name: 'contract_type',
    label: 'Loại hợp đồng',
    type: 'select',
    // Lọc theo MÃ đang lưu trong DB (CR-118). Trước đó ô này khai 5 chuỗi tiếng Việt
    // KHÔNG khớp dữ liệu thật ("Hợp đồng mua bán", "Hợp đồng kinh tế"…) nên lọc loại
    // nào cũng ra 0 dòng.
    options: CONTRACT_TYPE_OPTIONS,
  },
  {
    name: 'status',
    label: 'Trạng thái hợp đồng',
    type: 'select',
    options: [
      { value: 'Hiệu lực', label: 'Hiệu lực' },
      { value: 'Hết hạn', label: 'Hết hạn' },
      { value: 'Thanh lý', label: 'Thanh lý' },
      { value: 'Hủy', label: 'Hủy' },
    ],
  },
  {
    name: 'signed',
    label: 'Đã ký kết',
    type: 'boolean',
  },
  {
    name: 'start_date',
    label: 'Ngày ký',
    type: 'date',
  },
  {
    name: 'end_date',
    label: 'Ngày hết hạn',
    type: 'date',
  },
]
