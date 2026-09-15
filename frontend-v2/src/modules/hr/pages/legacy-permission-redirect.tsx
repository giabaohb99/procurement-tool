import { Navigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Đá đường CŨ `/hr/permissions/users/:userId` sang `/system/permissions/users/:userId`.
 *
 * Màn Phân quyền tài khoản đã dời sang phân hệ Quản trị (duoc-CR-396), nhưng
 * `/hr/permissions` sống hơn một năm: người dùng lưu dấu trang, và địa chỉ đó
 * còn nằm trong mấy chục thư thông báo đã gửi đi.
 *
 * ⚠️ Phải là một COMPONENT chứ không dùng thẳng `<Navigate>` được: `to` của
 * `Navigate` là chuỗi tĩnh, không nội suy được `:userId` của route. Quăng hết về
 * trang danh sách thì liên kết trong thư "đã cấp quyền cho bạn" — vốn trỏ thẳng
 * vào MỘT tài khoản — biến thành lời mời đi tìm lại từ đầu.
 *
 * `replace`: đường cũ không được nằm lại trong lịch sử, kẻo bấm Back là rơi vào
 * vòng chuyển hướng.
 */
export function LegacyUserPermissionRedirect() {
  const { userId } = useParams()
  if (!userId) return <Navigate to={appRoutes.system.permissions} replace />
  return <Navigate to={appRoutes.system.userPermissionDetail(userId)} replace />
}
