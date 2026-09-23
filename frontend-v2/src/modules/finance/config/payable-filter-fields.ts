import { supplierApi } from '@/modules/production/api/supplier-api'
import type { FilterFieldDefinition, SelectOption } from '@/shared/conditional-filter'
import { PAYABLE_SOURCE_LABELS } from '../types/payable'

/**
 * Trường của BỘ LỌC NÂNG CAO cho màn Công nợ.
 *
 * ⚠️ `name` phải nằm trong `payable/service.FILTERABLE` — ngoài whitelist đó
 * backend im lặng bỏ qua và người dùng tưởng bộ lọc hỏng.
 *
 * Các ô trên thanh công cụ (Công ty · Nhà cung cấp · Trạng thái · Số hóa đơn ·
 * Loại nợ · Tuổi nợ · Năm) KHÔNG khai ở đây: controller tự đọc chúng bằng tay
 * chứ không qua `apply_filters`, nên cú pháp `<field>__<op>` của bộ lọc nâng
 * cao vô tác dụng với chúng.
 *
 * ⚠️ ai-CR-017: Nhà cung cấp / Số hóa đơn / Loại nợ vẫn CỐ Ý giữ ở đây dù đã
 * có bản đơn giản ngoài thanh công cụ — đúng khuôn v1 (`PAYABLE_COND_FILTERS`
 * trong `frontend/src/config/conditional-filters.ts`): ô ngoài lọc BẰNG một
 * giá trị, còn ở đây lọc được bằng "khác/chứa/để trống" và gộp AND/OR với các
 * dòng điều kiện khác. Khoảng tiền (`amount_from`/`amount_to`) KHÔNG đưa vào
 * đây được — đó là hai tham số riêng của `payable/controller._filtered`,
 * ngoài whitelist `operator_filterable`; `payable-list-page.tsx` tự dựng một
 * popover riêng để gộp cặp ô đó với khung này.
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
