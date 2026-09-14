import { KeyRound, MonitorSmartphone, RotateCw, ShieldAlert } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { LoginHistoryList } from '@/modules/system/components/login-history-list'
import {
  LOGIN_HISTORY_DAYS,
  useMyLoginHistory,
  useMySessions,
} from '@/modules/system/hooks/use-login-sessions'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { cn } from '@/shared/utils/cn'

/** Ba khoảng xem — khớp trần `HISTORY_DAYS_MAX = 365` của backend. */
const DAY_RANGES = [
  { days: 30, label: '30 ngày' },
  { days: LOGIN_HISTORY_DAYS, label: `${LOGIN_HISTORY_DAYS} ngày` },
  { days: 365, label: '1 năm' },
] as const

/**
 * Tab «Lịch sử đăng nhập» ở Trang cá nhân (bao-CR-400).
 *
 * Trả lời ba câu người dùng hay hỏi về tài khoản của CHÍNH MÌNH: đang có bao
 * nhiêu máy giữ phiên, gần đây đăng nhập từ máy nào, và có ai gõ sai mật khẩu
 * vào tài khoản mình không. Đọc hai cửa tự thân `/api/auth/sessions` (số phiên
 * đang mở) và `/api/auth/sessions/history` (lịch sử) — chỉ đòi đăng nhập, không
 * cần khóa `login_session`, và backend khóa cứng vào `user.id` nên không có
 * cách nào xem của người khác từ đây.
 */
export function ProfileLoginHistoryTab() {
  const [days, setDays] = useState<number>(LOGIN_HISTORY_DAYS)
  const history = useMyLoginHistory(days)
  //  Cùng cache với tab «Thiết bị của tôi» — mở tab nào trước cũng chỉ gọi một lần.
  const sessions = useMySessions(true)

  const aliveCount = sessions.data?.alive_count ?? 0
  const failedCount = history.data?.failed_count ?? 0

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <SectionHeading>Lịch sử đăng nhập</SectionHeading>
          <div className="flex flex-wrap items-center gap-2">
            <div
              role="group"
              aria-label="Khoảng thời gian"
              className="flex items-center rounded-md border p-0.5"
            >
              {DAY_RANGES.map((range) => (
                <Button
                  key={range.days}
                  type="button"
                  size="sm"
                  variant={days === range.days ? 'secondary' : 'ghost'}
                  aria-pressed={days === range.days}
                  className="h-7 px-2.5"
                  onClick={() => setDays(range.days)}
                >
                  {range.label}
                </Button>
              ))}
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                void history.refetch()
                void sessions.refetch()
              }}
              title="Làm mới"
            >
              <RotateCw className="size-4" />
              <span className="sr-only">Làm mới</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <SummaryTile
            icon={MonitorSmartphone}
            label="Phiên đang mở"
            value={sessions.isLoading ? '…' : aliveCount}
            hint={
              <Link to="/me?tab=devices" className="text-primary hover:underline">
                Xem thiết bị
              </Link>
            }
          />
          <SummaryTile
            icon={KeyRound}
            label={`Lần đăng nhập · ${days} ngày`}
            value={history.isLoading ? '…' : (history.data?.login_count ?? 0)}
          />
          <SummaryTile
            icon={ShieldAlert}
            label={`Lần thất bại · ${days} ngày`}
            value={history.isLoading ? '…' : failedCount}
            tone={failedCount > 0 ? 'warning' : undefined}
            hint={
              failedCount > 0
                ? 'Có người gõ sai mật khẩu vào tài khoản này. Không phải bạn thì hãy đổi mật khẩu.'
                : undefined
            }
          />
        </div>

        <LoginHistoryList
          data={history.data}
          isLoading={history.isLoading}
          days={days}
          heading={false}
        />
      </CardContent>
    </Card>
  )
}

interface SummaryTileProps {
  icon: LucideIcon
  label: string
  value: number | string
  hint?: React.ReactNode
  tone?: 'warning'
}

/** Ô số nhỏ nằm TRONG thẻ — không dùng `StatCard` vì đó là một `Card` riêng,
 *  lồng vào đây thành thẻ trong thẻ (cùng lý do với `AuditTimeline`). */
function SummaryTile({ icon: Icon, label, value, hint, tone }: SummaryTileProps) {
  return (
    <div className="flex items-start gap-3 rounded-md border p-3">
      <span
        className={cn(
          'grid size-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground',
          tone === 'warning' && 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400',
        )}
      >
        <Icon className="size-4" />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-semibold">{value}</p>
        {hint && (
          <p className={cn('text-[11px] leading-snug text-muted-foreground', tone === 'warning' && 'text-warning')}>
            {hint}
          </p>
        )}
      </div>
    </div>
  )
}
