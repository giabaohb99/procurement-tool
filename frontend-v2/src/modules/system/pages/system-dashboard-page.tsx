import { DatabaseBackup, FileUp, ShieldCheck, SlidersHorizontal } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent } from '@/shared/ui/card'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'

/**
 * Tổng quan phân hệ Quản trị hệ thống.
 *
 * Chưa có số liệu để đếm nên chỉ có lối tắt. Phần "sắp có" nói thẳng hai màn
 * còn nợ (Sao lưu CSDL, Quản lý Import) để người dùng khỏi đi tìm trong menu.
 */
export function SystemDashboardPage() {
  return (
    <ModuleDashboard
      title="Quản trị hệ thống"
      description="Cấu hình chạy nóng, phân quyền và các tác vụ quản trị."
      shortcuts={[
        {
          label: 'Cấu hình hệ thống',
          description: 'Quy trình duyệt, email gửi đi, kho lưu trữ tệp.',
          path: appRoutes.system.settings,
          icon: SlidersHorizontal,
        },
        {
          // Phân quyền nằm ở phân hệ Nhân sự (dữ liệu gốc là nhân sự + tài
          // khoản), nhưng người đi tìm nó thường vào đây trước.
          label: 'Phân quyền tài khoản',
          description: 'Vai trò, phạm vi dữ liệu của từng tài khoản.',
          path: appRoutes.hr.permissions,
          icon: ShieldCheck,
        },
      ]}
      stats={
        <Card>
          <CardContent className="flex flex-col gap-2 py-4 text-sm text-muted-foreground">
            <p className="font-medium text-navy dark:text-foreground">Sắp có</p>
            <p className="flex items-center gap-2">
              <DatabaseBackup className="size-4" />
              Sao lưu cơ sở dữ liệu — tải bản sao lưu, xem lịch chạy tự động.
            </p>
            <p className="flex items-center gap-2">
              <FileUp className="size-4" />
              Quản lý Import — nạp dữ liệu từ tệp Excel và theo dõi kết quả.
            </p>
          </CardContent>
        </Card>
      }
    />
  )
}
