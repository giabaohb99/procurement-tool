import { Database, FileUp, History, ShieldCheck, SlidersHorizontal } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

/**
 * Trang Tổng quan phân hệ Quản trị hệ thống.
 *
 * Cung cấp lối tắt truy cập nhanh các tính năng Quản trị: Cấu hình hệ thống,
 * Sao lưu CSDL, Nhật ký thao tác hệ thống và Lối tắt Phân quyền tài khoản.
 */
export function SystemDashboardPage() {
  const { can } = usePermission()
  const canSetting = can('setting', 'write') || can('setting', 'create') || can('setting', 'delete')
  const canBackup = can('backup', 'read') || can('backup', 'write')

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
      description="Cấu hình hệ thống chạy nóng, quản lý sao lưu dữ liệu, lịch sử thao tác và phân quyền."
      shortcuts={[
        {
          label: 'Cấu hình hệ thống',
          description: 'Quy trình duyệt, email gửi đi, kho lưu trữ tệp.',
          path: appRoutes.system.settings,
          icon: SlidersHorizontal,
        },
        {
          label: 'Sao lưu CSDL',
          description: 'Quản lý, tạo mới và tải bản sao lưu dữ liệu hệ thống.',
          path: appRoutes.system.backups,
          icon: Database,
        },
        {
          label: 'Nhật ký hệ thống',
          description: 'Lịch sử ghi nhận toàn bộ thao tác (thêm, sửa, xóa, duyệt...) của người dùng.',
          path: appRoutes.system.auditLogs,
          icon: History,
        },
        {
          label: 'Quản lý Import',
          description: 'Nạp dữ liệu hàng loạt từ tệp Excel, chạy thử, theo dõi kết quả và hoàn tác.',
          path: appRoutes.system.imports,
          icon: FileUp,
        },
        {
          // Phân quyền nằm ở phân hệ Nhân sự (dữ liệu gốc là nhân sự + tài khoản),
          // nhưng tạo lối tắt ở đây giúp Quản trị viên dễ truy cập.
          label: 'Phân quyền tài khoản',
          description: 'Vai trò, ma trận chức năng và phạm vi dữ liệu của từng tài khoản.',
          path: appRoutes.hr.permissions,
          icon: ShieldCheck,
        },
      ]}
    />
  )
}
