import type { PeopleColumn } from '../components/employee-people-editor'
import type { EmployeeFamily } from '../types/employee'
import type { ChangeRequestFamilyRow } from '../types/employee-change-request'

/**
 * Cột của bảng «Thành viên hộ gia đình» (kê khai BHXH).
 *
 * Dùng chung cho tab «Giấy tờ & BHXH» của hồ sơ nhân sự, tab «Hộ gia đình» trong hộp «Đề nghị
 * sửa thông tin» ở Trang cá nhân (duoc-CR-676), bảng so sánh ở màn duyệt và bản in phiếu — cùng
 * lẽ với `employee-contact-columns.ts`: thêm cột một nơi mà quên nơi kia thì nhân viên khai xong,
 * phòng Nhân sự mở ra lại thiếu ô.
 */
export const FAMILY_COLUMNS: PeopleColumn<EmployeeFamily>[] = [
  { key: 'full_name', label: 'Họ tên', kind: 'text', span: 3 },
  //  Cùng bộ mã với bảng người báo tin, nhưng gốc quy chiếu là CHỦ HỘ —
  //  hồ sơ BHXH hỏi vậy, và nhân viên không phải lúc nào cũng là chủ hộ.
  { key: 'relation', label: 'Quan hệ với chủ hộ', kind: 'relation', span: 2, placeholder: '— Chọn quan hệ —' },
  { key: 'gender', label: 'Giới tính', kind: 'gender', span: 2 },
  { key: 'date_of_birth', label: 'Ngày sinh', kind: 'date', span: 2 },
  { key: 'id_number', label: 'Số CCCD', kind: 'text', span: 2 },
]

/** Dòng trống để thêm mới. `relation = 0` / `gender = 0` = chưa khai. */
export function createEmptyFamilyRow(): EmployeeFamily {
  return {
    id: 0,
    full_name: '',
    relation: 0,
    gender: 0,
    date_of_birth: null,
    phone: '',
    id_number: '',
    sort_order: 0,
  }
}

/**
 * Bỏ `id` / `sort_order` trước khi gửi — cả bảng ĐẶT LẠI một lượt, thứ tự lấy theo thứ tự dòng.
 * Ngày rỗng về `null` (cột `DATE NULL`, chuỗi rỗng là 422).
 */
export function toFamilyPayload(rows: readonly ChangeRequestFamilyRow[]): ChangeRequestFamilyRow[] {
  return rows.map(({ full_name, relation, gender, date_of_birth, phone, id_number }) => ({
    full_name,
    relation,
    gender,
    date_of_birth: date_of_birth || null,
    phone,
    id_number,
  }))
}
