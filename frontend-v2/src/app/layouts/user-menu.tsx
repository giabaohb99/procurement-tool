import {
  Building2,
  Camera,
  ChevronDown,
  Headphones,
  LoaderCircle,
  LogOut,
  Phone,
  User,
} from 'lucide-react'
import { useRef, useState, type ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { CreateTicketDialog } from '@/app/components/profile/create-ticket-dialog'
import { apiPost } from '@/core/api'
import { useAuth } from '@/core/auth/use-auth'
import { useTranslation } from '@/core/i18n/use-translation'
import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { ThemeSwitch } from '@/shared/ui/theme-switch'
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
  const { user, logout, setUser } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const avatarInputRef = useRef<HTMLInputElement>(null)
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const [ticketDialogOpen, setTicketDialogOpen] = useState(false)

  async function uploadAvatar(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || !user) return

    const formData = new FormData()
    formData.append('file', file)
    setUploadingAvatar(true)
    try {
      const result = await apiPost<{ avatar: string }>('/api/auth/avatar', formData)
      setUser({ ...user, avatar: result.avatar })
      toast.success('Đã cập nhật ảnh đại diện')
    } catch {
      // HTTP client đã hiện thông báo lỗi cho thao tác POST.
    } finally {
      setUploadingAvatar(false)
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-11 gap-2 px-2">
            <Avatar className="size-8">
              <AvatarImage className="object-cover" src={user?.avatar} alt={user?.full_name} />
              <AvatarFallback className="bg-navy-solid text-xs font-semibold text-white">
                {initials(user?.full_name)}
              </AvatarFallback>
            </Avatar>
            <span className="hidden min-w-0 text-left sm:block">
              <span className="block max-w-40 truncate text-[13px] leading-4 font-semibold text-navy dark:text-foreground">
                {user?.full_name}
              </span>
              {(user?.emp_code || user?.position) && (
                <span className="block max-w-40 truncate text-[11px] leading-4 text-muted-foreground">
                  {[user?.emp_code, user?.position].filter(Boolean).join(' · ')}
                </span>
              )}
            </span>
            <ChevronDown className="hidden size-3.5 text-muted-foreground sm:block" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" sideOffset={8} className="w-72 overflow-hidden p-0">
          <DropdownMenuLabel className="flex items-center gap-3 border-b bg-secondary/65 p-4 font-normal">
            <div className="relative shrink-0">
              <Avatar className="size-10 ring-1 ring-border shadow-sm">
                <AvatarImage
                  className="object-cover"
                  src={user?.avatar}
                  alt={user?.full_name}
                />
                <AvatarFallback className="bg-navy-solid text-base font-semibold text-white">
                  {initials(user?.full_name)}
                </AvatarFallback>
              </Avatar>
              <button
                type="button"
                aria-label="Đổi ảnh đại diện"
                title="Đổi ảnh đại diện"
                disabled={uploadingAvatar}
                onClick={() => avatarInputRef.current?.click()}
                className="absolute -right-1 -bottom-1 grid size-5 place-items-center rounded-full bg-[#009ee2] text-white shadow-[0_2px_6px_rgba(0,158,226,0.45)] ring-2 ring-popover outline-none transition-colors hover:bg-[#008cc9] focus-visible:ring-ring disabled:cursor-wait"
              >
                {uploadingAvatar ? (
                  <LoaderCircle className="size-3 animate-spin" />
                ) : (
                  <Camera className="size-3" strokeWidth={2.5} />
                )}
              </button>
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-navy dark:text-foreground">
                {user?.full_name}
              </p>
              <div className="mt-1 flex min-w-0 items-center gap-1.5">
                {user?.emp_code ? (
                  <span className="shrink-0 rounded-full border border-primary/25 bg-primary/10 px-2 py-0.5 text-[11px] leading-4 font-bold tracking-wide text-primary">
                    {user.emp_code}
                  </span>
                ) : (
                  <span className="text-[11px] text-muted-foreground">
                    Chưa gắn hồ sơ nhân sự
                  </span>
                )}
                {(user?.position || user?.role_name) && (
                  <span className="truncate text-xs text-muted-foreground">
                    {user.position || user.role_name}
                  </span>
                )}
              </div>
              <p className="mt-1 truncate text-xs text-muted-foreground">{user?.email}</p>
            </div>
          </DropdownMenuLabel>

          <div className="space-y-0.5 px-4 py-2.5 text-[13px] text-slate-600 dark:text-slate-300">
            <p className="flex min-h-8 items-center gap-2.5">
              <Building2 className="size-4 shrink-0 text-slate-400" />
              <span className="truncate">{user?.department_name || 'Chưa có phòng ban'}</span>
            </p>
            <p className="flex min-h-8 items-center gap-2.5">
              <Phone className="size-4 shrink-0 text-slate-400" />
              <span className="truncate">{user?.phone || 'Chưa cập nhật SĐT'}</span>
            </p>
          </div>

          <DropdownMenuSeparator className="m-0" />

          {/*  Chọn giao diện nằm TRONG popover này chứ không phải một nút riêng
               trên thanh trên: đây là tùy chỉnh CÁ NHÂN, cùng nhóm với hồ sơ và
               đăng xuất, mà thanh trên thì đã chật. */}
          <div className="flex min-h-10 items-center justify-between gap-3 px-4">
            <span className="text-[13px] font-medium text-navy dark:text-foreground">
              Giao diện
            </span>
            <ThemeSwitch />
          </div>

          <DropdownMenuSeparator className="m-0" />

          <div className="p-2">
            <DropdownMenuItem
              className="min-h-10 gap-3 px-2.5 font-medium text-navy dark:text-foreground"
              onSelect={() => setTicketDialogOpen(true)}
            >
              <Headphones className="size-4.5 text-navy dark:text-foreground" />
              Gửi yêu cầu hỗ trợ
            </DropdownMenuItem>
            <DropdownMenuItem
              className="min-h-10 gap-3 px-2.5 font-medium text-navy dark:text-foreground"
              onSelect={() => navigate(appRoutes.me)}
            >
              <User className="size-4.5 text-navy dark:text-foreground" />
              Trang cá nhân
            </DropdownMenuItem>
            <DropdownMenuItem
              variant="destructive"
              className="min-h-10 gap-3 px-2.5 font-medium"
              onSelect={logout}
            >
              <LogOut className="size-4.5" />
              {t('auth.logout')}
            </DropdownMenuItem>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>

      <input
        ref={avatarInputRef}
        type="file"
        hidden
        accept="image/*"
        onChange={uploadAvatar}
        disabled={uploadingAvatar}
      />

      <CreateTicketDialog
        open={ticketDialogOpen}
        onOpenChange={setTicketDialogOpen}
      />
    </>
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
