import { Monitor, Smartphone, Tablet, HelpCircle } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { DEVICE_TYPE, type LoginSessionItem } from '../api/login-session-api'

const DEVICE_ICONS = {
  [DEVICE_TYPE.DESKTOP]: Monitor,
  [DEVICE_TYPE.MOBILE]: Smartphone,
  [DEVICE_TYPE.TABLET]: Tablet,
} as const

interface LoginSessionDeviceProps {
  session: Pick<
    LoginSessionItem,
    'device_type' | 'device_label' | 'browser' | 'os' | 'is_current' | 'user_agent'
  >
  className?: string
}

/**
 * Ô «Thiết bị» dùng chung cho ba màn phiên đăng nhập: biểu tượng theo loại
 * máy + nhãn "Chrome trên Windows" + huy hiệu «Thiết bị này» khi là phiên đang
 * bấm. `title` mang nguyên `User-Agent` để người tra lỗi rê chuột đọc được.
 */
export function LoginSessionDevice({ session, className }: LoginSessionDeviceProps) {
  const Icon = DEVICE_ICONS[session.device_type as keyof typeof DEVICE_ICONS] ?? HelpCircle
  const label =
    session.device_label ||
    [session.browser, session.os].filter(Boolean).join(' trên ') ||
    'Không rõ thiết bị'

  return (
    <div className={cn('flex items-center gap-2 min-w-0', className)} title={session.user_agent}>
      <Icon className="size-4 shrink-0 text-muted-foreground" />
      <span className="truncate font-medium text-foreground">{label}</span>
      {session.is_current && (
        <Badge variant="outline" className="shrink-0 border-emerald-500 text-emerald-600">
          Thiết bị này
        </Badge>
      )}
    </div>
  )
}

/** Huy hiệu tình trạng phiên: xanh khi còn hiệu lực, xám khi đã kết thúc. */
export function LoginSessionEnding({ session }: { session: Pick<LoginSessionItem, 'is_alive' | 'ending'> }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        session.is_alive
          ? 'border-emerald-500 text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40'
          : 'border-slate-400 text-slate-600 bg-slate-100 dark:bg-slate-800',
      )}
    >
      {session.ending || (session.is_alive ? 'Còn hiệu lực' : 'Đã kết thúc')}
    </Badge>
  )
}
