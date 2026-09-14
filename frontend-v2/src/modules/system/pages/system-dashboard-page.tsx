import { canManageEntity } from '@/app/router/module-visibility'
import { usePermission } from '@/core/authorization/use-permission'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SYSTEM_DASHBOARD_SHORTCUTS } from '../config/dashboard-shortcuts'

/**
 * Trang Tổng quan phân hệ Quản trị hệ thống — lối tắt vào từng màn của phân hệ.
 *
 * Danh sách lối tắt nằm ở `config/dashboard-shortcuts.ts` (có test so với menu
 * trái để không sót màn nào).
 */
export function SystemDashboardPage() {
  const { can } = usePermission()
  const canSetting = canManageEntity('setting', can)
  const canBackup = can('backup', 'read') || can('backup', 'write')

  //  ⚠️ Lọc theo ĐÚNG luật của mục menu tương ứng (`canManageEntity` cho mục
  //  khai `manage`, `read` cho mục còn lại) — cùng hàm mà `ModuleSidebar` dùng.
  //  Trước 14/09/2026 trang này bày đủ 5 thẻ cho mọi người: ai không có quyền
  //  `backup` vẫn thấy thẻ *Sao lưu CSDL*, bấm vào ăn 403. Thẻ mời gọi một việc
  //  không làm được thì tệ hơn là không có thẻ.
  const shortcuts = SYSTEM_DASHBOARD_SHORTCUTS.filter((item) =>
    item.manage ? canManageEntity(item.entity, can) : can(item.entity, 'read'),
  )

  if (!canSetting && !canBackup) {
    return (
      <PageContainer>
        <PageHeader title="Quản trị hệ thống" description="Cấu hình hệ thống và sao lưu dữ liệu." />
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          Bạn không có quyền truy cập Phân hệ Quản trị hệ thống.
        </div>
      </PageContainer>
    )
  }

  return (
    <ModuleDashboard
      title="Quản trị hệ thống"
      description="Cấu hình hệ thống chạy nóng, sao lưu dữ liệu, nhật ký thao tác, phiên đăng nhập và phân quyền."
      shortcuts={shortcuts}
    />
  )
}
