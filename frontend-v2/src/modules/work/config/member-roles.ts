import { WORK_ROLE } from '../types/work'

/**
 * Ba vai trò GÁN ĐƯỢC cho thành viên dự án, kèm câu nói rõ mỗi vai làm được gì.
 *
 * Không có *Chủ sở hữu*: chủ chỉ đổi bằng thao tác chuyển quyền, gán thẳng thì
 * backend chặn (`list_service.add_member`). Để nó trong ô chọn là mời người ta
 * bấm vào một thứ chắc chắn báo lỗi.
 *
 * Ở tệp riêng chứ không nằm cạnh `MemberRoleSelect`: tệp vừa xuất hằng vừa xuất
 * component thì `react-refresh/only-export-components` kêu, và mỗi lần sửa hằng
 * là cả cây component nạp lại thay vì thay nóng.
 */
export const ASSIGNABLE_ROLES = [
  { value: WORK_ROLE.ADMIN, label: 'Quản trị', hint: 'Mời và gỡ người, sửa thông tin dự án' },
  { value: WORK_ROLE.MEMBER, label: 'Thành viên', hint: 'Tạo và sửa công việc' },
  { value: WORK_ROLE.VIEWER, label: 'Khách xem', hint: 'Chỉ xem, không sửa được gì' },
] as const
