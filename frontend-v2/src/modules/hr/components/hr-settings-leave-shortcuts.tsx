import { CalendarDays, CalendarOff, ChevronRight, ListChecks } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Lối tắt tới các danh mục của Nghỉ phép (duoc-CR-713) — chúng đã có màn quản lý riêng ở «Nghỉ phép ▸ Thiết lập», trang
 * Cài đặt chỉ dẫn đường cho người tìm «cấu hình nghỉ phép» ở một chỗ. Mỗi lối tắt chỉ hiện khi có quyền SỬA danh mục
 * đó (cùng luật `manage: true` của mục menu «Thiết lập»), kẻo bấm vào là màn 403.
 */
export function HrSettingsLeaveShortcuts() {
  const { can } = usePermission()
  const links = [
    {
      to: appRoutes.hr.leaveTypes,
      icon: ListChecks,
      label: 'Loại nghỉ & bậc thâm niên',
      hint: 'Số ngày phép năm, cách cộng thâm niên, loại nghỉ có lương / không lương.',
      allowed: can('leave_type', 'write'),
    },
    {
      to: appRoutes.hr.holidays,
      icon: CalendarDays,
      label: 'Lịch ngày lễ',
      hint: 'Ngày lễ không tính vào số ngày nghỉ.',
      allowed: can('holiday', 'write'),
    },
    {
      to: appRoutes.hr.leaveBlocks,
      icon: CalendarOff,
      label: 'Ngày cấm nghỉ',
      hint: 'Khoảng ngày không muốn ai nghỉ: cảnh báo lúc lập đơn, chặn ở lượt duyệt cuối.',
      allowed: can('leave_type', 'write'),
    },
  ].filter((link) => link.allowed)
  if (links.length === 0) return null

  return (
    <section className="space-y-2">
      <h2 className="text-sm font-medium text-muted-foreground">Danh mục nghỉ phép</h2>
      <div className="divide-y rounded-lg border">
        {links.map(({ to, icon: Icon, label, hint }) => (
          <Link key={to} to={to} className="flex items-center gap-3 p-4 hover:bg-muted/50">
            <Icon className="size-4 shrink-0 text-muted-foreground" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium">{label}</span>
              <span className="block text-sm text-muted-foreground">{hint}</span>
            </span>
            <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
          </Link>
        ))}
      </div>
    </section>
  )
}
