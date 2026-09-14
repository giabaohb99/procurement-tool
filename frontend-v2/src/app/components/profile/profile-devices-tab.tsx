import { LogOut, MonitorSmartphone, RotateCw } from 'lucide-react'
import { useState } from 'react'

import { LoginSessionDevice, LoginSessionEnding } from '@/modules/system/components/login-session-device'
import {
  useMySessions,
  useRevokeMyOtherSessions,
  useRevokeMySession,
} from '@/modules/system/hooks/use-login-sessions'
import type { LoginSessionItem } from '@/modules/system/api/login-session-api'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { Switch } from '@/shared/ui/switch'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

/**
 * Tab «Thiết bị của tôi» ở Trang cá nhân (bao-CR-395, CR-312 P3b).
 *
 * Đọc `/api/auth/sessions` — cửa CHỈ đòi đăng nhập, không cần khóa
 * `login_session`, nên mọi tài khoản đều thấy được máy nào đang giữ phiên của
 * mình và tự đá máy lạ. Phiên đang bấm được đánh dấu «Thiết bị này» và không
 * có nút đá (muốn thoát máy này thì bấm Đăng xuất như thường).
 */
export function ProfileDevicesTab() {
  const [activeOnly, setActiveOnly] = useState(true)
  const { data, isLoading, refetch } = useMySessions(activeOnly)
  const revokeOne = useRevokeMySession()
  const revokeOthers = useRevokeMyOtherSessions()

  const rows = data?.items ?? []
  const otherAlive = rows.filter((r) => r.is_alive && !r.is_current)

  async function handleRevoke(row: LoginSessionItem) {
    const ok = await confirm({
      title: 'Đăng xuất thiết bị',
      message: `Đăng xuất ${row.device_label || 'thiết bị này'} (IP ${row.ip || '?'})? Thiết bị đó còn dùng được tối đa 1 phút rồi phải đăng nhập lại.`,
      confirmLabel: 'Đăng xuất thiết bị',
    })
    if (ok) revokeOne.mutate(row.id)
  }

  async function handleRevokeOthers() {
    const ok = await confirm({
      title: 'Đăng xuất mọi thiết bị khác',
      message: `Đăng xuất ${otherAlive.length} thiết bị khác? Thiết bị đang dùng vẫn giữ nguyên.`,
      confirmLabel: 'Đăng xuất mọi thiết bị khác',
    })
    if (ok) revokeOthers.mutate()
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <SectionHeading>Thiết bị đang đăng nhập</SectionHeading>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Switch id="my-sessions-active-only" checked={activeOnly} onCheckedChange={setActiveOnly} />
              <Label htmlFor="my-sessions-active-only" className="text-sm">
                Chỉ còn hiệu lực
              </Label>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={() => refetch()} title="Làm mới">
              <RotateCw className="size-4" />
              <span className="sr-only">Làm mới</span>
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={() => void handleRevokeOthers()}
              disabled={otherAlive.length === 0 || revokeOthers.isPending}
              title="Cắt mọi phiên trừ phiên đang bấm"
            >
              <LogOut className="size-4 mr-1.5" /> Đăng xuất mọi thiết bị khác
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading && <Skeleton className="h-20 w-full" />}
        {!isLoading && rows.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-8 text-sm text-muted-foreground">
            <MonitorSmartphone className="size-8" />
            {activeOnly
              ? 'Không có thiết bị nào khác đang giữ phiên của bạn.'
              : 'Chưa ghi nhận phiên đăng nhập nào.'}
          </div>
        )}
        {rows.length > 0 && (
          <ul className="divide-y rounded-md border text-sm">
            {rows.map((row) => (
              <li key={row.id} className="flex flex-wrap items-center gap-3 px-3 py-2.5">
                <LoginSessionDevice session={row} className="min-w-0 flex-1 basis-56" />
                <span className="font-mono text-xs text-muted-foreground">{row.ip || '—'}</span>
                <span
                  className="w-32 shrink-0 text-xs text-muted-foreground"
                  title={`Đăng nhập ${formatDateTime(row.created_at)}`}
                >
                  {formatRelativeTime(row.last_seen_at) || '—'}
                </span>
                <LoginSessionEnding session={row} />
                {row.is_alive && !row.is_current && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-8 gap-1 px-2"
                    onClick={() => void handleRevoke(row)}
                    disabled={revokeOne.isPending}
                  >
                    <LogOut className="size-4" /> Đăng xuất
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
