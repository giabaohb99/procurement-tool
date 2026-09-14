import { LogOut, RotateCw, User, UserX } from 'lucide-react'
import { useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { usePermission } from '@/core/authorization/use-permission'
import { useUserAccounts } from '@/modules/hr/hooks/use-user-accounts'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchSelect } from '@/shared/ui/search-select'
import { Switch } from '@/shared/ui/switch'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import type { LoginSessionItem } from '../api/login-session-api'
import { LoginSessionDevice, LoginSessionEnding } from '../components/login-session-device'
import {
  useLoginSessions,
  useLogoutAllSessions,
  useRevokeLoginSession,
} from '../hooks/use-login-sessions'

/**
 * PHIÊN ĐĂNG NHẬP toàn hệ (bao-CR-395, CR-312 P3b) — `/system/sessions`.
 *
 * Ai đang vào hệ thống, từ máy nào, lần cuối lúc nào; hai nút cắt:
 * - «Đá phiên» — chỉ phiên đó, có trễ tối đa 60 giây (cache hồ sơ quyền);
 * - «Bắt đăng nhập lại» — mọi phiên của người đó, hiệu lực tức thì
 *   (`token_version` tăng).
 * Cả hai đòi `login_session.delete`; phạm vi `own` chỉ thấy phiên của mình.
 */
export function LoginSessionListPage() {
  const { can } = usePermission()
  const canRevoke = can('login_session', 'delete')
  const canPickUser = can('user', 'read')

  const [userId, setUserId] = useState<string>('')
  const [activeOnly, setActiveOnly] = useState(true)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([userId, activeOnly])

  const params = {
    page,
    page_size: pageSize,
    user_id: userId ? Number(userId) : 0,
    active_only: activeOnly,
  }
  const { data, isLoading, isError, refetch } = useLoginSessions(params)

  // Ô lọc theo người — mượn danh bạ tài khoản, tắt khi thiếu `user.read`.
  const { data: accounts } = useUserAccounts({ page_size: 1000 }, { enabled: canPickUser })
  const userOptions = (accounts?.items ?? []).map((acc) => ({
    value: String(acc.id),
    label: acc.code ? `${acc.full_name} (${acc.code})` : acc.full_name || acc.email,
  }))

  const revoke = useRevokeLoginSession()
  const logoutAll = useLogoutAllSessions()

  async function handleRevoke(row: LoginSessionItem) {
    const ok = await confirm({
      title: 'Đá phiên khỏi thiết bị',
      message: `Đá phiên của ${row.user_name || `tài khoản #${row.user_id}`} trên ${row.device_label || 'thiết bị này'}? Token cũ còn dùng được tối đa 1 phút.`,
      confirmLabel: 'Đá phiên',
    })
    if (ok) revoke.mutate(row.id)
  }

  async function handleLogoutAll(row: LoginSessionItem) {
    const ok = await confirm({
      title: 'Bắt đăng nhập lại',
      message: `Đăng xuất ${row.user_name || `tài khoản #${row.user_id}`} khỏi MỌI thiết bị ngay lập tức? Người đó phải đăng nhập lại.`,
      confirmLabel: 'Đăng xuất mọi thiết bị',
    })
    if (ok) logoutAll.mutate(row.user_id)
  }

  const columns: DataTableColumn<LoginSessionItem>[] = [
    {
      key: 'user_name',
      header: 'Người dùng',
      width: 200,
      cell: (r) => (
        <div className="flex items-center gap-1.5 font-medium text-foreground">
          <User className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{r.user_name || `Tài khoản #${r.user_id}`}</span>
        </div>
      ),
    },
    {
      key: 'device',
      header: 'Thiết bị',
      width: 220,
      cell: (r) => <LoginSessionDevice session={r} />,
    },
    {
      key: 'ip',
      header: 'IP',
      width: 130,
      cell: (r) => (
        <span className="font-mono text-xs" title={r.last_seen_ip && r.last_seen_ip !== r.ip ? `Lần cuối: ${r.last_seen_ip}` : undefined}>
          {r.ip || '—'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Đăng nhập lúc',
      width: 150,
      cell: (r) => formatDateTime(r.created_at) || '—',
    },
    {
      key: 'last_seen_at',
      header: 'Hoạt động cuối',
      width: 130,
      cell: (r) => (
        <span title={formatDateTime(r.last_seen_at)}>{formatRelativeTime(r.last_seen_at) || '—'}</span>
      ),
    },
    {
      key: 'login_method',
      header: 'Cách vào',
      width: 100,
      defaultHidden: true,
      cell: (r) => r.login_method_label || '—',
    },
    {
      key: 'ending',
      header: 'Tình trạng',
      width: 170,
      cell: (r) => <LoginSessionEnding session={r} />,
    },
    {
      key: 'actions',
      header: 'Thao tác',
      width: 200,
      hideable: false,
      cell: (r) =>
        canRevoke && r.is_alive ? (
          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 gap-1 px-2"
              title="Đá phiên này (trễ tối đa 1 phút)"
              onClick={(e) => {
                e.stopPropagation()
                void handleRevoke(r)
              }}
            >
              <LogOut className="size-4" /> Đá phiên
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-8 gap-1 px-2 text-destructive"
              title="Đăng xuất mọi thiết bị của người này (tức thì)"
              onClick={(e) => {
                e.stopPropagation()
                void handleLogoutAll(r)
              }}
            >
              <UserX className="size-4" /> Bắt đăng nhập lại
            </Button>
          </div>
        ) : null,
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Phiên đăng nhập"
        description="Ai đang vào hệ thống, từ thiết bị nào — đá phiên lạ hoặc bắt đăng nhập lại khi nghi ngờ lộ tài khoản"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Làm mới danh sách">
            <RotateCw className="size-4 mr-1.5" /> Làm mới
          </Button>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => String(r.id)}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          emptyMessage={
            userId || !activeOnly
              ? 'Không có phiên nào khớp bộ lọc.'
              : 'Chưa có phiên đăng nhập nào còn hiệu lực.'
          }
          storageKey="system.login_sessions"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phiên',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-3">
              {canPickUser && (
                <div className="w-72">
                  <SearchSelect
                    value={userId}
                    onChange={setUserId}
                    options={userOptions}
                    placeholder="Mọi người dùng"
                    searchPlaceholder="Tìm tên / mã nhân sự…"
                    clearable
                    size="sm"
                  />
                </div>
              )}
              <div className="flex items-center gap-2">
                <Switch id="sessions-active-only" checked={activeOnly} onCheckedChange={setActiveOnly} />
                <Label htmlFor="sessions-active-only" className="text-sm">
                  Chỉ phiên còn hiệu lực
                </Label>
              </div>
            </div>
          }
        />
      </Card>
    </PageContainer>
  )
}
