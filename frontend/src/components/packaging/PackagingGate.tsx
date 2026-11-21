import type { ReactNode } from 'react'
import { useAuth } from '../../auth/AuthContext'
import NotFound from '../NotFound'

/**
 * Cổng quyền của bốn màn riêng cụm Giá bao bì (menu đã ẩn mục khi thiếu quyền, nhưng gõ thẳng đường dẫn vẫn tới được).
 * Chỉ là tiện ích giao diện — backend `require("packaging_cost", "read")` mới là chốt thật.
 */
export default function PackagingGate({ children }: { children: ReactNode }) {
  const { can } = useAuth()
  if (!can('packaging_cost', 'read')) {
    return <NotFound title="Không có quyền xem" backTo="/" message="Bạn không có quyền xem cụm Giá bao bì." />
  }
  return <>{children}</>
}
