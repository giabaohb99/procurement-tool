import { useCallback } from 'react'

import { useAuthStore } from '@/core/auth/auth-store'
import type { PermissionAction, PermissionEntity } from './permission-types'

/**
 * `can(entity, action)` — dùng để ẩn menu, khóa nút, ẩn cột.
 * Nhắc lại: đây là tiện ích GIAO DIỆN, không phải hàng rào bảo mật.
 */
export function usePermission() {
  const permissions = useAuthStore((s) => s.user?.permissions)

  const can = useCallback(
    (entity: PermissionEntity, action: PermissionAction) =>
      !!permissions?.[entity]?.[action],
    [permissions],
  )

  /** Có BẤT KỲ quyền nào trên entity không — dùng để quyết định hiện mục menu. */
  const canAccess = useCallback(
    (entity: PermissionEntity) => Object.values(permissions?.[entity] ?? {}).some(Boolean),
    [permissions],
  )

  return { can, canAccess }
}

/**
 * Bối cảnh runtime cho luật hiển thị menu mà quyền tĩnh không nói được — có
 * `isDriver` và `reportKeys` (xem `NavContext` ở `module-visibility.ts`). Tách
 * khỏi `usePermission` để nơi nào cần thì lấy riêng, khỏi kéo cả `can`.
 */
export function useNavContext(): { isDriver?: boolean; reportKeys?: readonly number[] } {
  const isDriver = useAuthStore((s) => s.user?.is_driver)
  //  Đọc THẲNG mảng từ store (không `?? []`) để giữ tham chiếu ổn định giữa các
  //  lượt render — một mảng rỗng mới dựng mỗi lần sẽ làm mọi nơi dùng nó trong
  //  `useMemo`/`useQueries` (vd `useReportOverview`) nghĩ dữ liệu vừa đổi.
  const reportKeys = useAuthStore((s) => s.user?.report_keys)
  return { isDriver, reportKeys }
}
