import type { FilterFieldDefinition } from '@/shared/conditional-filter'

/**
 * Trường của BỘ LỌC NÂNG CAO màn Tồn kho.
 *
 * ⚠️ `name` phải nằm trong `inventory/service.FILTERABLE`
 * (`warehouse_code · product_code · product_name`) — ngoài whitelist đó backend
 * im lặng bỏ qua, giao diện trông như bộ lọc hỏng.
 *
 * Whitelist chỉ có ba cột, mà hai trong số đó đã có chỗ đứng riêng trên thanh
 * công cụ nên không khai lại ở đây — khai hai lần thì cùng một cột nhận hai
 * điều kiện chỏi nhau, hoặc tệ hơn là điều kiện này ghi đè điều kiện kia lúc
 * dựng query:
 *  - `warehouse_code` -> ô chọn "Kho" (gửi `warehouse_code__eq`, khớp chính xác);
 *  - `product_name`   -> ô tìm kiếm bên trái (gõ trần = LIKE).
 *
 * Ba ô chọn còn lại (`company_id`, `item_group`, `qty_status`) thì backend đọc
 * TAY chứ không qua `apply_filters`, nên cú pháp `<field>__<op>` vô tác dụng với
 * chúng — có khai vào đây cũng không lọc được.
 */
export const INVENTORY_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'product_code', label: 'Mã sản phẩm', type: 'text' },
]
