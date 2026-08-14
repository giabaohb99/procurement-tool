import { ArrowLeft, Filter, Loader2, Save } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appRoutes } from '@/shared/constants/app-routes'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { UserScopeDialog } from '../components/user-scope-dialog'
import { useRoles } from '../hooks/use-roles'
import { useAssignRoles, useUserAccount } from '../hooks/use-user-accounts'

/**
 * Gán vai trò và phạm vi dữ liệu cho MỘT tài khoản.
 *
 * Phải LƯU vai trò trước rồi mới đặt được phạm vi: phạm vi lưu theo cặp
 * (tài khoản × vai trò), vai trò chưa tồn tại trong DB thì chưa có chỗ gắn.
 */
export function UserPermissionDetailPage() {
  // Tham số route là `:userId` (xem `appRoutes.hr.userPermissionDetail`), đọc
  // nhầm tên khác sẽ ra NaN -> query bị tắt -> màn hình báo "không tìm thấy".
  const { userId: userIdParam } = useParams()
  const navigate = useNavigate()
  const userId = Number(userIdParam)

  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>([])
  const [scopeRoleId, setScopeRoleId] = useState<number | null>(null)

  const { data: account, isLoading, isError } = useUserAccount(userId)
  const { data: roles } = useRoles()
  const assignRoles = useAssignRoles(userId)

  // Tài khoản vừa tải về / vừa lưu xong -> đồng bộ lại các vai trò đang tick.
  if (useHasChanged(account)) setSelectedRoleIds(account?.role_ids ?? [])

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-5 h-20 w-full" />
        <Skeleton className="h-80 w-full" />
      </PageContainer>
    )
  }

  if (isError || !account) {
    return (
      <ErrorState
        title="Không tìm thấy tài khoản"
        description="Tài khoản có thể đã bị xóa, hoặc bạn không có quyền xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.hr.permissions)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const toggleRole = (roleId: number) =>
    setSelectedRoleIds((current) =>
      current.includes(roleId)
        ? current.filter((x) => x !== roleId)
        : [...current, roleId],
    )

  const scopeRoleName = roles?.find((role) => role.id === scopeRoleId)?.name ?? ''

  return (
    <PageContainer>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to={appRoutes.hr.permissions}>
            <ArrowLeft />
            Phân quyền tài khoản
          </Link>
        </Button>

        <PermissionGate entity="user" action="write">
          <Button
            onClick={() => assignRoles.mutate(selectedRoleIds)}
            disabled={assignRoles.isPending}
          >
            {assignRoles.isPending ? <Loader2 className="animate-spin" /> : <Save />}
            Lưu vai trò
          </Button>
        </PermissionGate>
      </div>

      <div className="mb-5">
        <h1 className="text-lg font-semibold text-navy">{account.full_name}</h1>
        <p className="text-sm text-muted-foreground">
          {account.email || '(chưa có email)'} ·{' '}
          {account.department_name || 'Chưa có phòng ban'}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Vai trò &amp; phạm vi</CardTitle>
          <p className="text-sm text-muted-foreground">
            Tick vai trò để gán. Với vai trò ĐÃ LƯU, bấm "Phạm vi" để giới hạn công ty /
            phòng ban / nhân sự riêng cho tài khoản này.
          </p>
        </CardHeader>

        <CardContent className="space-y-2">
          {(roles ?? []).map((role) => {
            const checked = selectedRoleIds.includes(role.id)
            const persisted = account.role_ids.includes(role.id)

            return (
              // `h-12` cho MỌI dòng: dòng có nút "Phạm vi" và dòng không có phải
              // cao bằng nhau, nếu không danh sách nhấp nhô mỗi khi tick.
              <div
                key={role.id}
                className={cn(
                  'flex h-12 items-center gap-3 rounded-lg border px-3',
                  checked && 'border-primary/40 bg-primary/5',
                )}
              >
                <label className="flex h-full min-w-0 flex-1 cursor-pointer items-center gap-3">
                  <Checkbox checked={checked} onCheckedChange={() => toggleRole(role.id)} />
                  <span className="truncate font-medium text-navy">{role.name}</span>
                  <span className="shrink-0 font-mono text-xs text-muted-foreground">
                    {role.code}
                  </span>
                </label>

                {persisted ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="shrink-0"
                    onClick={() => setScopeRoleId(role.id)}
                  >
                    <Filter />
                    Phạm vi
                  </Button>
                ) : (
                  checked && (
                    <span className="shrink-0 text-xs text-muted-foreground">
                      Lưu vai trò trước để đặt phạm vi
                    </span>
                  )
                )}
              </div>
            )
          })}
        </CardContent>
      </Card>

      <UserScopeDialog
        userId={userId}
        roleId={scopeRoleId}
        roleName={scopeRoleName}
        onClose={() => setScopeRoleId(null)}
      />
    </PageContainer>
  )
}
