import { LogOut, User } from 'lucide-react'

import { useAuth } from '@/core/auth/use-auth'
import { useTranslation } from '@/core/i18n/use-translation'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'

/** Ảnh đại diện + menu tài khoản. Dùng chung cho cả hai khung: launcher và module. */
export function UserMenu() {
  const { user, logout } = useAuth()
  const { t } = useTranslation()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-10 gap-2 px-2">
          <Avatar className="size-7">
            <AvatarImage src={user?.avatar} alt={user?.full_name} />
            <AvatarFallback className="text-xs">{initials(user?.full_name)}</AvatarFallback>
          </Avatar>
          <span className="hidden text-sm font-medium sm:inline">{user?.full_name}</span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="font-normal">
          <p className="text-sm font-medium">{user?.full_name}</p>
          <p className="text-xs text-muted-foreground">
            {user?.position || user?.role_name || user?.email}
          </p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <User className="size-4" />
          Thông tin cá nhân
        </DropdownMenuItem>
        <DropdownMenuItem variant="destructive" onSelect={logout}>
          <LogOut className="size-4" />
          {t('auth.logout')}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** "Trần Minh Được" -> "TĐ". Dùng khi chưa có ảnh đại diện. */
function initials(fullName?: string): string {
  if (!fullName) return '?'
  const words = fullName.trim().split(/\s+/)
  const first = words.at(0)?.[0] ?? ''
  const last = words.length > 1 ? (words.at(-1)?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}
