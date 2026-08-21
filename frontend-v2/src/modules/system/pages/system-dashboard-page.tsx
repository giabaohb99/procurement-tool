import { Database, FileUp, History, ShieldCheck, SlidersHorizontal } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent } from '@/shared/ui/card'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'

/**
 * Trang Tổng quan phân hệ Quản trị hệ thống.
 *
 * Cung cấp lối tắt truy cập nhanh các tính năng Quản trị: Cấu hình hệ thống,
 * Sao lưu CSDL, Nhật ký thao tác hệ thống và Lối tắt Phân quyền tài khoản.
 */
export function SystemDashboardPage() {
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
          // Phân quyền nằm ở phân hệ Nhân sự (dữ liệu gốc là nhân sự + tài khoản),
          // nhưng tạo lối tắt ở đây giúp Quản trị viên dễ truy cập.
          label: 'Phân quyền tài khoản',
          description: 'Vai trò, ma trận chức năng và phạm vi dữ liệu của từng tài khoản.',
          path: appRoutes.hr.permissions,
          icon: ShieldCheck,
        },
      ]}
      stats={
        <Card>
          <CardContent className="flex flex-col gap-2 py-4 text-sm text-muted-foreground">
            <p className="font-semibold text-foreground">Tính năng đang hoãn / phát triển tiếp theo:</p>
            <p className="flex items-center gap-2">
              <FileUp className="size-4 text-blue-600 dark:text-blue-400" />
              <span>
                <strong>Quản lý Import (MC-6)</strong> — công cụ nạp dữ liệu hàng loạt từ tệp Excel và theo dõi kết quả xử lý.
              </span>
            </p>
          </CardContent>
        </Card>
      }
    />
  )
}
