import { ArrowLeft, Filter, Loader2, Mail, MailX, Save } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
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
import { useRoles } from '@/modules/hr/hooks/use-roles'
import {
  useAssignRoles,
  useSetUserNotifyEmail,
  useUserAccount,
} from '@/modules/hr/hooks/use-user-accounts'

/**
 * Gán vai trò và phạm vi dữ liệu cho MỘT tài khoản.
 *
 * Phải LƯU vai trò trước rồi mới đặt được phạm vi: phạm vi lưu theo cặp
 * (tài khoản × vai trò), vai trò chưa tồn tại trong DB thì chưa có chỗ gắn.
 */
export function UserPermissionDetailPage() {
  // Tham số route là `:userId` (xem `appRoutes.system.userPermissionDetail`), đọc
  // nhầm tên khác sẽ ra NaN -> query bị tắt -> màn hình báo "không tìm thấy".
  const { userId: userIdParam } = useParams()
  const navigate = useNavigate()
  const userId = Number(userIdParam)

  // Bản NHÁP của người dùng. `null` = chưa tick gì, khi đó bản máy chủ là bản
  // đang hiện; tick một cái là nháp sinh ra và thắng cho tới khi lưu xong.
  const [draftRoleIds, setDraftRoleIds] = useState<number[] | null>(null)
  const [scopeRoleId, setScopeRoleId] = useState<number | null>(null)

  const { user: currentUser } = useAuth()
  const { data: account, isLoading, isError } = useUserAccount(userId)
  const { data: roles } = useRoles()
  const assignRoles = useAssignRoles(userId)
  const setNotifyEmail = useSetUserNotifyEmail()

  //  KHÔNG TỰ SỬA QUYỀN CỦA CHÍNH MÌNH — chốt hai người. Backend chặn ở
  //  `core/privilege_escalation.py`; ở đây khóa luôn giao diện để người dùng
  //  thấy LUẬT chứ không tick xong rồi ăn 403 và tưởng hệ hỏng (CR-158).
  const isSelf = !!currentUser && currentUser.id === userId

  // Đổi sang tài khoản khác thì mọi thứ tick dở không còn nghĩa gì. Route param
  // đổi mà component KHÔNG mount lại, nên vẫn cần nhịp này.
  if (useHasChanged(userId)) setDraftRoleIds(null)

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
        <Button variant="outline" onClick={() => navigate(appRoutes.system.permissions)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  //  Bản đang hiện = nháp nếu có, không thì bản máy chủ.
  //
  //  ⚠️ Đây là chốt của HAI lỗi, đừng quay về kiểu chép `account.role_ids` vào
  //  state rồi đồng bộ lại theo từng lượt nạp:
  //
  //  - Chép vào state rồi đồng bộ theo MỌI lượt nạp lại thì một lượt nạp rơi
  //    vào giữa lúc đang tick là các ô vừa chọn lặng lẽ quay về bản đã lưu, và
  //    cú «Lưu vai trò» ngay sau đó ghi xuống đúng bản cũ (khách báo 25/08/2026).
  //    React Query nạp lại bất cứ lúc nào: hết hạn 30 giây, `invalidateQueries`
  //    của một thao tác khác, người khác vừa sửa cùng tài khoản.
  //  - Chép vào state rồi CHỈ đồng bộ khi dữ liệu «đổi» thì hỏng ở lượt mount
  //    có sẵn bộ đệm: vào trang, quay ra, vào lại — lần này `account` có ngay ở
  //    lượt render đầu nên không có gì «đổi» cả, state đứng nguyên ở rỗng và
  //    mọi dấu tick biến mất cho tới khi tải lại trang (đại ca báo 25/09/2026).
  //
  //  Đọc thẳng như dưới đây thì không lượt render nào là lượt đặc biệt.
  const selectedRoleIds = draftRoleIds ?? account.role_ids

  const toggleRole = (roleId: number) =>
    setDraftRoleIds((current) => {
      const base = current ?? account.role_ids
      return base.includes(roleId)
        ? base.filter((x) => x !== roleId)
        : [...base, roleId]
    })

  // Lưu xong thì bản của máy chủ mới là bản chuẩn — bỏ nháp đi để lượt nạp lại
  // ngay sau đó (do `invalidateQueries`) hiện ra.
  const saveRoles = () =>
    assignRoles.mutate(selectedRoleIds, { onSuccess: () => setDraftRoleIds(null) })

  const scopeRoleName = roles?.find((role) => role.id === scopeRoleId)?.name ?? ''
  // `undefined` (hệ chưa chạy migration) = vẫn đang nhận — xem `UserAccount.notify_email`.
  const receivesEmail = account.notify_email !== false

  return (
    <PageContainer>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to={appRoutes.system.permissions}>
            <ArrowLeft />
            Phân quyền tài khoản
          </Link>
        </Button>

        <PermissionGate entity="user" action="write">
          <Button
            onClick={saveRoles}
            disabled={assignRoles.isPending || isSelf}
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

      {isSelf && (
        <p className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Đây là tài khoản của chính bạn nên chỉ xem được. Đổi quyền của mình phải
          nhờ một quản trị khác — chốt hai người của phân quyền, tránh việc một
          người tự nâng mình lên quản trị hệ thống bằng một lần bấm.
        </p>
      )}

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
                  <Checkbox
                    checked={checked}
                    disabled={isSelf}
                    onCheckedChange={() => toggleRole(role.id)}
                  />
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
                    disabled={isSelf}
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

      {/*  bao-CR-349 — công tắc EMAIL, cố ý đặt cùng màn với vai trò.
           Người đi tra câu "sao tài khoản này không nhận được thư duyệt" mở đúng
           trang này, và câu trả lời phải nằm ngay đó chứ không nằm trong .env.
           KHÔNG khóa theo `isSelf`: chốt hai người là luật của PHÂN QUYỀN, còn
           đây là tuỳ chọn nhận thư — tự tắt cho mình không nâng quyền cho ai. */}
      <PermissionGate entity="user" action="write">
        <Card className="mt-5">
          <CardHeader>
            <CardTitle className="text-base">Email thông báo</CardTitle>
            <p className="text-sm text-muted-foreground">
              Thư báo mỗi khi có chứng từ cần duyệt, được duyệt hoặc bị trả lại. Tắt
              email <b>không</b> tắt thông báo: chuông trong app vẫn chạy đủ, và thư đặt
              lại mật khẩu / cấp tài khoản vẫn gửi bình thường.
            </p>
          </CardHeader>

          <CardContent className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm">
              <span
                className={cn(
                  'size-2 shrink-0 rounded-full',
                  receivesEmail ? 'bg-emerald-500' : 'bg-muted-foreground/40',
                )}
              />
              <span className="font-medium text-navy">
                {receivesEmail ? 'Đang nhận email thông báo' : 'Đã tắt email thông báo'}
              </span>
            </div>

            <Button
              variant="outline"
              size="sm"
              disabled={setNotifyEmail.isPending}
              onClick={() =>
                setNotifyEmail.mutate({ userId, notifyEmail: !receivesEmail })
              }
            >
              {setNotifyEmail.isPending ? (
                <Loader2 className="animate-spin" />
              ) : receivesEmail ? (
                <MailX />
              ) : (
                <Mail />
              )}
              {receivesEmail ? 'Tắt email thông báo' : 'Bật email thông báo'}
            </Button>
          </CardContent>
        </Card>
      </PermissionGate>

      <UserScopeDialog
        userId={userId}
        employeeId={account.employee_id}
        roleId={scopeRoleId}
        roleName={scopeRoleName}
        onClose={() => setScopeRoleId(null)}
      />
    </PageContainer>
  )
}
