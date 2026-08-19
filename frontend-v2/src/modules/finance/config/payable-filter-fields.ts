import { supplierApi } from '@/modules/production/api/supplier-api'
import type { FilterFieldDefinition, SelectOption } from '@/shared/conditional-filter'
import { PAYABLE_SOURCE_LABELS } from '../types/payable'

/**
 * Trường của BỘ LỌC NÂNG CAO cho màn Công nợ.
 *
 * ⚠️ `name` phải nằm trong `payable/service.FILTERABLE` — ngoài whitelist đó
 * backend im lặng bỏ qua và người dùng tưởng bộ lọc hỏng.
 *
 * Bốn ô trên thanh công cụ (Công ty · Trạng thái · Tuổi nợ · Năm) KHÔNG khai ở
 * đây: controller tự đọc chúng bằng tay chứ không qua `apply_filters`, nên cú
 * pháp `<field>__<op>` của bộ lọc nâng cao vô tác dụng với chúng.
 */

/**
 * Lọc theo MÃ nhà cung cấp — `tab_payable` neo bằng mã, không có cột id NCC.
 *
 * Tìm bằng `name` chứ không phải `q`: `/api/suppliers` chạy qua `apply_filters`
 * với whitelist `code · name · tax_code · supplier_type · is_active`, không có
 * tham số tìm chung. Nhãn kèm mã vì mã mới là thứ gửi lên.
 */
async function fetchSupplierCodeOptions(search: string): Promise<SelectOption[]> {
  const res = await supplierApi.list({ name: search, is_active: true, page_size: 50 })
  return res.items.map((item) => ({ value: item.code, label: `${item.name} (${item.code})` }))
}

export const PAYABLE_FILTER_FIELDS: FilterFieldDefinition[] = [
  {
    name: 'supplier_code',
    label: 'Nhà cung cấp',
    type: 'combobox',
    // Mã NCC là khóa duy nhất nên chỉ cần bằng / khác; `contains` trên mã viết
    // tắt khớp bừa (lọc "DEGO" ra luôn "DEGOHN", "DEGOSG").
    operators: ['is', 'is_not'],
    fetchOptions: fetchSupplierCodeOptions,
  },
  { name: 'po_code', label: 'Mã ĐMH', type: 'text' },
  { name: 'invoice_no', label: 'Số hóa đơn', type: 'text' },
  {
    name: 'source_type',
    label: 'Loại nợ',
    type: 'select',
    operators: ['is', 'is_not'],
    options: Object.entries(PAYABLE_SOURCE_LABELS).map(([value, label]) => ({ value, label })),
  },
]
