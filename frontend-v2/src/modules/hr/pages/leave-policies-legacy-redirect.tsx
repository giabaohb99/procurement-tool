import { Navigate, useLocation } from 'react-router-dom'

import { buildLeavePolicyHubHref } from '../utils/leave-policy-hub-tabs'

/**
 * Đường CŨ `/hr/leave-policies` (danh sách gói, duoc-CR-717) → tab Chính sách của màn Chính sách nghỉ phép
 * (duoc-CR-750). Giữ để dấu trang, liên kết trong HDSD và tin đã gửi không chết.
 *
 * Mang theo chuỗi truy vấn cũ (`?is_active=true`, `?q=…`) vì cùng bảng, cùng tên tham số. `replace` để bấm Back
 * không quay về đường cũ rồi bị đẩy đi lần nữa. `/new` và `/:id` vẫn là route thật, không qua đây.
 */
export function LeavePoliciesLegacyRedirect() {
  const { search } = useLocation()
  return <Navigate to={buildLeavePolicyHubHref('policies', new URLSearchParams(search))} replace />
}
