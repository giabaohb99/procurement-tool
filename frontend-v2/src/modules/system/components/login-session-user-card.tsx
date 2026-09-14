import { Lock, LogOut, ShieldCheck, UserX } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { useEmployeeAccount, useSetUserActive } from '@/modules/hr/hooks/use-user-accounts'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import type { LoginSessionItem } from '../api/login-session-api'
import {
  LOGIN_HISTORY_DAYS,
  useLoginHistory,
  useLoginSessions,
  useLogoutAllSessions,
  useRevokeLoginSession,
} from '../hooks/use-login-sessions'
import { LoginHistoryList } from './login-history-list'
import { LoginSessionDevice } from './login-session-device'

interface LoginSessionUserCardProps {
  /** Hồ sơ nhân sự — để tra tình trạng khóa của tài khoản (`user.read`). */
  employeeId: number
  /** Tài khoản đăng nhập của nhân sự — `0` = chưa có tài khoản, thẻ tự ẩn. */
  userId: number
  userName: string
  className?: string
}

/**
 * Thẻ PHIÊN ĐĂNG NHẬP của một nhân sự (bao-CR-395) — đặt ở tab «Tài khoản»
 * của hồ sơ nhân sự. Gác bằng `login_session.read`; nút cắt phiên đòi
 * `login_session.delete`; nút «Khóa tài khoản + đăng xuất mọi thiết bị» đi
 * qua `PUT /api/users/{id}/active` nên đòi `user.write` (backend tự thu hồi
 * phiên với lý do ACCOUNT_LOCKED khi khóa).
 *
 * ⚠️ Thẻ mượn dữ liệu của phân hệ Quản trị: mọi hook đều truyền `enabled`,
 * thiếu quyền thì không gọi — mount là gọi thì người dùng ăn toast 403.
 */
export function LoginSessionUserCard({
  employeeId,
  userId,
  userName,
  className,
}: LoginSessionUserCardProps) {
  const { can } = usePermission()
  const canRead = can('login_session', 'read')
  const canRevoke = can('login_session', 'delete')
  const canLock = can('user', 'write')
  const canReadUser = can('user', 'read')

  const enabled = canRead && userId > 0
  const sessions = useLoginSessions(
    { user_id: userId, active_only: true, page: 1, page_size: 50 },
    { enabled },
  )
  const history = useLoginHistory(userId, LOGIN_HISTORY_DAYS, { enabled })
  const revoke = useRevokeLoginSession()
  const logoutAll = useLogoutAllSessions()
  const setActive = useSetUserActive()
  // Chỉ để biết tài khoản đã khóa chưa; thiếu `user.read` thì coi như đang mở.
  const { data: account } = useEmployeeAccount(employeeId, canRead && canReadUser && userId > 0)
  const isActive = account?.is_active !== false

  if (!canRead || userId <= 0) return null

  const openSessions = sessions.data?.items ?? []

  async function handleRevoke(row: LoginSessionItem) {
    const ok = await confirm({
      title: 'Đá phiên khỏi thiết bị',
      message: `Đá phiên trên ${row.device_label || 'thiết bị này'} (IP ${row.ip || '?'})? Token cũ còn dùng được tối đa 1 phút.`,
      confirmLabel: 'Đá phiên',
    })
    if (ok) revoke.mutate(row.id)
  }

  async function handleLogoutAll() {
    const ok = await confirm({
      title: 'Bắt đăng nhập lại',
      message: `Đăng xuất ${userName} khỏi MỌI thiết bị ngay lập tức?`,
      confirmLabel: 'Đăng xuất mọi thiết bị',
    })
    if (ok) logoutAll.mutate(userId)
  }

  async function handleLock() {
    const ok = await confirm({
      title: 'Khóa tài khoản',
      message: `Khóa tài khoản của ${userName} và đăng xuất mọi thiết bị? Người này không đăng nhập được cho tới khi được mở khóa.`,
      confirmLabel: 'Khóa + đăng xuất',
    })
    if (ok) setActive.mutate({ userId, isActive: false })
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <SectionHeading>Phiên đăng nhập</SectionHeading>
          <div className="flex flex-wrap items-center gap-2">
            {canRevoke && openSessions.length > 0 && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void handleLogoutAll()}
                disabled={logoutAll.isPending}
                title="Mọi phiên của người này bị cắt ngay, phải đăng nhập lại"
              >
                <UserX className="size-4 mr-1.5" /> Bắt đăng nhập lại
              </Button>
            )}
            {canLock && isActive && (
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => void handleLock()}
                disabled={setActive.isPending}
                title="Khóa tài khoản — backend tự thu hồi mọi phiên"
              >
                <Lock className="size-4 mr-1.5" /> Khóa tài khoản + đăng xuất mọi thiết bị
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <section className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="size-4 text-muted-foreground" />
            Thiết bị đang đăng nhập
            <Badge variant="secondary">{openSessions.length}</Badge>
          </div>
          {sessions.isLoading && <Skeleton className="h-12 w-full" />}
          {!sessions.isLoading && openSessions.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Không có phiên nào còn hiệu lực.
            </p>
          )}
          {openSessions.length > 0 && (
            <ul className="divide-y rounded-md border">
              {openSessions.map((row) => (
                <li key={row.id} className="flex items-center gap-3 px-3 py-2 text-sm">
                  <LoginSessionDevice session={row} className="flex-1" />
                  <span className="font-mono text-xs text-muted-foreground">{row.ip || '—'}</span>
                  <span
                    className="w-28 shrink-0 text-right text-xs text-muted-foreground"
                    title={formatDateTime(row.last_seen_at)}
                  >
                    {formatRelativeTime(row.last_seen_at) || '—'}
                  </span>
                  {canRevoke && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-8 px-2"
                      onClick={() => void handleRevoke(row)}
                      disabled={revoke.isPending}
                      title="Đá phiên này (trễ tối đa 1 phút)"
                    >
                      <LogOut className="size-4" />
                      <span className="sr-only">Đá phiên</span>
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* bao-CR-400 — cùng một bản vẽ với tab «Lịch sử đăng nhập» ở /me. */}
        <LoginHistoryList
          data={history.data}
          isLoading={history.isLoading}
          days={LOGIN_HISTORY_DAYS}
        />
      </CardContent>
    </Card>
  )
}
