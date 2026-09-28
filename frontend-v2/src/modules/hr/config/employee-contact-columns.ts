import type { PeopleColumn } from '../components/employee-people-editor'
import type { EmployeeContact } from '../types/employee'

/**
 * Cột của bảng «Người báo tin trong trường hợp cần thiết».
 *
 * Dùng chung cho HAI nơi — tab «Liên hệ & Ngân hàng» của hồ sơ nhân sự và thẻ
 * tự sửa ở Trang cá nhân (bao-CR-508). Tách ra đây để hai bảng không trôi khỏi
 * nhau: thêm một cột ở một nơi mà quên nơi kia thì người dùng tự khai xong,
 * phòng Nhân sự mở ra lại thấy thiếu ô.
 */
export const CONTACT_COLUMNS: PeopleColumn<EmployeeContact>[] = [
  { key: 'full_name', label: 'Họ tên', kind: 'text', span: 3 },
  //  Ô CHỌN, không gõ tay (khách chốt 08/09/2026). Quan hệ với NHÂN VIÊN.
  { key: 'relation', label: 'Quan hệ', kind: 'relation', span: 2, placeholder: '— Chọn quan hệ —' },
  { key: 'phone', label: 'Điện thoại', kind: 'phone', span: 2 },
  { key: 'address', label: 'Địa chỉ', kind: 'text', span: 4 },
]

/** Dòng trống để thêm mới. `relation = 0` = chưa khai, xem `RELATION_OPTIONS`. */
export function createEmptyContactRow(): EmployeeContact {
  return { id: 0, full_name: '', relation: 0, address: '', phone: '', sort_order: 0 }
}

/**
 * Bỏ `id` / `sort_order` trước khi gửi — cả bảng ĐẶT LẠI một lượt, thứ tự lấy
 * theo đúng thứ tự dòng; gửi kèm id cũ chỉ làm người đọc tưởng nó được dùng.
 */
export function toContactPayload(rows: EmployeeContact[]) {
  return rows.map(({ full_name, relation, address, phone }) => ({
    full_name,
    relation,
    address,
    phone,
  }))
}
