import { AlertCircle, KeyRound, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { employeeApi } from '../api/employee-api'
import { useRoles } from '../hooks/use-roles'
import { useEmployeeAccount } from '../hooks/use-user-accounts'
import { SetPasswordDialog } from './set-password-dialog'

interface EmployeeAccountCardProps {
  employeeId: number
  /** Email trên hồ sơ — chưa có thì không tạo được tài khoản. */
  email: string
  className?: string
}

/**
 * Thẻ "Tài khoản đăng nhập" trên trang chi tiết Nhân sự.
 *
 * Trả lời sẵn ba câu hỏi mà trước đây phải bấm vào mới biết: nhân sự đã có tài
 * khoản chưa, email nào, đã gán vai trò gì — kèm lối đi tiếp sang màn Phân quyền.
 */
export function EmployeeAccountCard({ employeeId, email, className }: EmployeeAccountCardProps) {
  const { can } = usePermission()
  const canReadUser = can('user', 'read')
  const canSetPassword = can('employee', 'write')

  const [isPasswordOpen, setPasswordOpen] = useState(false)

  const { data: account, isLoading, refetch } = useEmployeeAccount(employeeId, canReadUser)
  // Chỉ để đổi id vai trò thành tên; thiếu quyền đọc vai trò thì bỏ qua, không chặn thẻ.
  const { data: roles } = useRoles()

  // Không có quyền nào liên quan thì thẻ này chẳng nói được gì — ẩn hẳn.
  if (!canReadUser && !canSetPassword) return null

  const roleNames = (account?.role_ids ?? [])
    .map((id) => roles?.find((role) => role.id === id)?.name)
    .filter(Boolean)

  async function handleSetPassword(password: string) {
    const message = await employeeApi.setPassword(employeeId, password)
    toast.success(message || 'Đã đặt lại mật khẩu')
    // Vừa tạo tài khoản thì thẻ phải đổi trạng thái ngay.
    await refetch()
  }

  return (
    <>
      <Card className={className}>
        <CardHeader>
          <SectionHeading>Tài khoản đăng nhập</SectionHeading>
        </CardHeader>

        <CardContent className="space-y-4">
          {isLoading && <Skeleton className="h-14 w-full" />}

          {!isLoading && account && (
            <div className="space-y-3">
              {/*  CHỈ hiện khi tài khoản BỊ KHÓA (26/08/2026).

                   Trước đây hàng này luôn có hai huy hiệu: «Đang hoạt động» và
                   một huy hiệu địa chỉ đăng nhập. Bỏ cả hai vì cùng một lý do —
                   chúng nói thứ người dùng đã biết: gần như mọi tài khoản đều
                   đang hoạt động, còn địa chỉ đăng nhập thì chính là ô Email
                   ngay bên trái cùng trang. Tài khoản nào chưa có địa chỉ thì
                   huy hiệu kia rỗng hoác, thành một viên xám trống cạnh viên
                   xanh (đúng thứ khách chụp lại).

                   Giữ lại đúng vế NGƯỢC: bị khóa là chuyện bất thường và người
                   đó KHÔNG đăng nhập được. Bỏ nốt thì màn hình không còn chỗ
                   nào nói ra, và người quản trị đi tìm mãi không hiểu vì sao. */}
              {!account.is_active && <Badge variant="destructive">Đã khóa</Badge>}

              <div className="flex items-start gap-2 text-sm">
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <div>
                  <p className="text-muted-foreground">Vai trò</p>
                  <p className="text-foreground">
                    {roleNames.length > 0
                      ? roleNames.join(', ')
                      : account.role_ids.length > 0
                        ? `${account.role_ids.length} vai trò`
                        : 'Chưa gán vai trò — tài khoản chưa dùng được'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {!isLoading && !account && (
            <div className="flex items-start gap-2 rounded-md bg-accent p-3 text-sm">
              <AlertCircle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              <p>
                Nhân sự này <b>chưa có tài khoản đăng nhập</b>.{' '}
                {email
                  ? 'Đặt mật khẩu để tạo tài khoản, sau đó gán vai trò ở màn Phân quyền tài khoản.'
                  : 'Hãy nhập Email ở hồ sơ và lưu trước — tài khoản đăng nhập dùng chính email này.'}
              </p>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {canSetPassword && (account || email) && (
              // ⚠️ `type="button"` là BẮT BUỘC: thẻ này nằm TRONG `<form>` của
              // trang chi tiết nhân sự, mà nút không khai `type` thì mặc định là
              // `submit`. Bấm «Đặt lại mật khẩu» vừa mở hộp thoại vừa LƯU luôn
              // hồ sơ — khách thấy bóng «Đã cập nhật nhân sự» hiện lên trong khi
              // họ chưa sửa gì (báo 26/08/2026).
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPasswordOpen(true)}
              >
                <KeyRound />
                {account ? 'Đặt lại mật khẩu' : 'Tạo tài khoản đăng nhập'}
              </Button>
            )}

            {account && canReadUser && (
              <Button variant="outline" size="sm" asChild>
                <Link to={appRoutes.hr.userPermissionDetail(account.id)}>
                  <ShieldCheck />
                  Phân quyền tài khoản
                </Link>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <SetPasswordDialog
        open={isPasswordOpen}
        onOpenChange={setPasswordOpen}
        hasAccount={!!account}
        onSubmit={handleSetPassword}
      />
    </>
  )
}
