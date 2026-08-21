import { Bell, Building, BriefcaseBusiness, IdCard, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { apiPost } from '@/core/api'
import type { AuthUser } from '@/core/auth/auth-types'
import { useAuth } from '@/core/auth/use-auth'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { AvatarUploader } from '@/shared/ui/avatar-uploader'
import { validateImageFile } from '@/shared/utils/image-file'

/** "Trần Minh Được" -> "TĐ". Dùng khi chưa có ảnh đại diện. */
function initials(fullName?: string): string {
  if (!fullName) return '?'
  const words = fullName.trim().split(/\s+/)
  const first = words.at(0)?.[0] ?? ''
  const last = words.length > 1 ? (words.at(-1)?.[0] ?? '') : ''
  return (first + last).toUpperCase()
}

/**
 * Thẻ danh tính đầu Trang cá nhân: ảnh đại diện đổi được ngay tại chỗ, họ tên,
 * và các chip mã NV / chức vụ / phòng ban / vai trò.
 *
 * Đổi ảnh xong phải ghi lại vào `auth-store` chứ không chỉ vào cache của trang:
 * ảnh đại diện còn hiện ở menu tài khoản trên mọi màn hình, không cập nhật thì
 * người dùng thấy ảnh cũ cho tới lần đăng nhập sau.
 */
export function ProfileIdentityCard({ profile }: { profile: AuthUser | null }) {
  const { user, setUser } = useAuth()

  const name = profile?.full_name || user?.full_name || 'Người dùng'
  const avatar = user?.avatar || profile?.avatar || ''

  async function uploadAvatar(file: File) {
    const problem = validateImageFile(file)
    if (problem) {
      toast.error(problem)
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    try {
      const result = await apiPost<{ avatar: string }>('/api/auth/avatar', formData)
      if (user) setUser({ ...user, avatar: result.avatar })
      toast.success('Đã cập nhật ảnh đại diện')
    } catch {
      // HTTP client đã hiện thông báo lỗi cho thao tác POST.
    }
  }

  const chips = [
    { icon: IdCard, text: profile?.emp_code },
    { icon: BriefcaseBusiness, text: profile?.position },
    { icon: Building, text: profile?.department_name },
    { icon: ShieldCheck, text: profile?.role_name },
  ].filter((chip) => !!chip.text)

  return (
    <Card className="flex flex-row flex-wrap items-center gap-4 p-5">
      <AvatarUploader
        src={avatar}
        fallback={initials(name)}
        alt={`Ảnh đại diện của ${name}`}
        onUpload={uploadAvatar}
      />

      <div className="min-w-0 flex-1">
        <p className="truncate text-lg font-semibold text-navy dark:text-foreground">{name}</p>
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
          {chips.length > 0 ? (
            chips.map((chip) => (
              <span
                key={chip.text}
                className="flex items-center gap-1.5 rounded-full border bg-accent px-2.5 py-0.5 text-xs text-accent-foreground"
              >
                <chip.icon className="size-3.5 text-muted-foreground" />
                {chip.text}
              </span>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">
              Tài khoản chưa gắn hồ sơ nhân sự
            </span>
          )}
        </div>
      </div>

      {/*
        Bản cũ có tab "Việc cần làm" ngay trong trang này. v2 đã có màn riêng
        («Chờ tôi duyệt» của phân hệ Văn bản) nên ở đây chỉ để lối đi sang,
        không dựng lại bảng thứ hai.
      */}
      <div className="flex shrink-0 flex-wrap gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link to={appRoutes.notifications}>
            <Bell className="size-4" />
            Thông báo
          </Link>
        </Button>
      </div>
    </Card>
  )
}
