import { companyApi } from '@/modules/hr/api/company-api'
import { departmentApi } from '@/modules/hr/api/department-api'
import { employeeApi } from '@/modules/hr/api/employee-api'
import { supplierApi } from '@/modules/production/api/supplier-api'
import type { SelectOption } from '@/shared/conditional-filter'
import { purchaseRequestSupportApi } from '../api/purchase-request-support-api'

/**
 * Nguồn options cho các ô lọc THAM CHIẾU (công ty / phòng ban / nhân sự) — CR-088.
 */

const PAGE_SIZE = 50

/** Danh mục công ty / pháp nhân. */
export async function fetchCompanyOptions(search: string): Promise<SelectOption[]> {
  const res = await companyApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/** Danh mục phòng ban. Endpoint này tìm bằng `q` (tên phòng hoặc tên trưởng bộ phận). */
export async function fetchDepartmentOptions(search: string): Promise<SelectOption[]> {
  const res = await departmentApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/**
 * Danh mục nhân sự. Kèm MÃ vào nhãn vì đây chính là màn có người trùng tên —
 * không có mã thì hai dòng giống hệt nhau, chọn xong không biết đã chọn ai.
 */
export async function fetchEmployeeOptions(search: string): Promise<SelectOption[]> {
  const res = await employeeApi.list({ full_name: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({
    value: String(item.id),
    label: item.code ? `${item.full_name} (${item.code})` : item.full_name,
  }))
}

/**
 * Danh mục nhân sự trả về MÃ nhân sự thay vì id (bao-CR-443).
 *
 * ⚠️ Không thay được cho `fetchEmployeeOptions`: hai ô lọc khác nhau ở chỗ backend
 * so khớp bằng gì. `requester_id` / `nspt_id` là cột khóa nên phải gửi số; còn
 * `assignee` của YCMH và YCBG lọc trên bảng con, nơi người phụ trách được ghi bằng
 * **mã** nhân sự (`purchase_request/controller.py`). Gửi nhầm loại thì không ai báo
 * lỗi cả — danh sách chỉ lặng lẽ rỗng.
 */
export async function fetchEmployeeCodeOptions(search: string): Promise<SelectOption[]> {
  const res = await employeeApi.list({ full_name: search, is_active: true, page_size: PAGE_SIZE })
  return res.items
    .filter((item) => Boolean(item.code))
    .map((item) => ({ value: item.code, label: `${item.full_name} (${item.code})` }))
}

/**
 * Phân loại VTBB/NL. Giá trị lọc là **TÊN** phân loại chứ không phải id — các bảng
 * dòng hàng (`tab_po_item.item_group`, dòng YCMH/YCBG) chép tên xuống chứ không giữ
 * khóa, nên đó là thứ duy nhất so khớp được.
 *
 * Danh mục này nhỏ (vài chục dòng) và đường API không nhận từ khóa tìm, nên nạp cả
 * rồi lọc ngay tại máy — đỡ phải sửa cửa API chỉ để phục vụ một ô lọc.
 */
export async function fetchItemGroupOptions(search: string): Promise<SelectOption[]> {
  const res = await purchaseRequestSupportApi.listItemGroups()
  const keyword = search.trim().toLowerCase()
  return res.items
    .filter((item) => !keyword || item.name.toLowerCase().includes(keyword))
    .slice(0, PAGE_SIZE)
    .map((item) => ({ value: item.name, label: item.name }))
}

/** Nhà cung cấp — giá trị lọc là MÃ NCC (`supplier_code` trên đơn mua hàng). */
export async function fetchSupplierCodeOptions(search: string): Promise<SelectOption[]> {
  const res = await supplierApi.list({ name: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: item.code, label: `${item.name} (${item.code})` }))
}

/**
 * Kho — giá trị lọc là MÃ kho. Cố ý KHÔNG lọc `is_active`: kho đã ngừng dùng vẫn
 * còn nằm trên các đơn cũ, bỏ đi thì không tra lại được lịch sử giao hàng.
 */
export async function fetchWarehouseCodeOptions(search: string): Promise<SelectOption[]> {
  const res = await purchaseRequestSupportApi.listWarehouses()
  const keyword = search.trim().toLowerCase()
  return res.items
    .filter(
      (item) =>
        !keyword ||
        item.name.toLowerCase().includes(keyword) ||
        item.code.toLowerCase().includes(keyword),
    )
    .slice(0, PAGE_SIZE)
    .map((item) => ({ value: item.code, label: `${item.name} (${item.code})` }))
}
