import { Search, ShieldAlert, Trash2 } from 'lucide-react'
import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { useDeleteOAuthClient, useOAuthClients } from '../hooks/use-ai-usage'
import type { OAuthClient } from '../types/ai-skill'
import { filterOAuthClients, OAUTH_CLIENT_STATUS, OAUTH_CLIENT_STATUS_OPTIONS } from '../utils/ai-row-mappers'

/**
 * bao-CR-635 — Ứng dụng AI đã kết nối: các ứng dụng (ChatGPT, claude.ai…) tự đăng ký OAuth với cổng MCP khi có người bấm
 * "Cho phép" (ai-CR-225). Tên là do ứng dụng TỰ KHAI nên không tin được — cột "Nơi quay về" (hostname) mới là thứ để
 * nhận ra thật giả; host ngoài danh sách ứng dụng quen thì máy chủ trả `trusted = false` và màn tô cảnh báo.
 * Xóa ứng dụng = cắt mọi kết nối của nó ngay (mã truy cập + mã làm mới chết), người dùng muốn nối lại phải "Cho phép" lần nữa.
 * Xem cần `agent_group.read` (như Cấu hình) — thiếu thì nói rõ, không gọi để ăn 403; xóa theo `can_delete` máy chủ trả.
 *
 * bao-CR-696: nằm ở menu Cấu hình > Nâng cao (chỉ người quản lý bot AI thấy mục), thêm ô tìm + lọc trạng thái. Lọc
 * NGAY TRÊN MÁY (`filterOAuthClients`) vì máy chủ trả cả danh sách một lần, không phân trang.
 */
export function OAuthClientsPage() {
  const { can } = usePermission()
  const allowed = can('agent_group', 'read')
  const { data, isLoading, isError } = useOAuthClients(allowed)
  const remove = useDeleteOAuthClient()
  const canDelete = data?.can_delete ?? false
  const rows = data?.items
  const { value: keyword, setValue: setKeyword, debouncedValue: q } = useUrlSearchParam('q')
  const [status, setStatus] = useUrlParamState('status', OAUTH_CLIENT_STATUS.all)
  const shownRows = useMemo(() => (rows ? filterOAuthClients(rows, q, status) : undefined), [rows, q, status])
  const filtering = q.trim() !== '' || status !== OAUTH_CLIENT_STATUS.all

  const columns = useMemo<DataTableColumn<OAuthClient>[]>(() => {
    const base: DataTableColumn<OAuthClient>[] = [
      {
        key: 'client_name',
        header: 'Tên tự khai',
        width: 220,
        hideable: false,
        cell: (c) => (
          <span>
            <span className="font-medium text-navy dark:text-foreground">{c.client_name || '(không tên)'}</span>{' '}
            <span className="font-mono text-xs text-muted-foreground">{shortId(c.client_id)}</span>
          </span>
        ),
      },
      {
        key: 'redirect_hosts',
        header: 'Nơi quay về',
        width: 260,
        hideable: false,
        cell: (c) => (
          <span className="flex flex-wrap items-center gap-1">
            <span className={cn(!c.trusted && 'font-medium text-destructive')}>
              {c.redirect_hosts.length > 0 ? c.redirect_hosts.join(', ') : '(không khai)'}
            </span>
            {!c.trusted && (
              <Badge variant="outline" className="border-destructive/40 text-destructive">
                <ShieldAlert className="size-3" />
                Host lạ
              </Badge>
            )}
          </span>
        ),
      },
      {
        key: 'live_grants',
        header: 'Kết nối đang sống',
        width: 140,
        cell: (c) => <span className={cn('tabular-nums', c.live_grants === 0 && 'text-muted-foreground')}>{c.live_grants}</span>,
      },
      {
        //  bao-CR-696: AI đang dùng ứng dụng này — để biết xóa thì cắt của ai. Máy chủ cũ chưa có thì gạch ngang.
        key: 'live_users',
        header: 'Người đang dùng',
        width: 240,
        wrap: true,
        cell: (c) => {
          const names = c.live_user_names ?? []
          if (typeof c.live_users !== 'number' || c.live_users === 0) return <span className="text-muted-foreground">—</span>
          const more = c.live_users - names.length
          return (
            <span className="text-sm">
              {names.join(', ')}
              {more > 0 && <span className="text-muted-foreground">{names.length > 0 ? ` và ${more} người khác` : `${more} người`}</span>}
            </span>
          )
        },
      },
      {
        key: 'last_used_at',
        header: 'Dùng lần cuối',
        width: 150,
        cell: (c) => (
          <span className="whitespace-nowrap text-muted-foreground">{c.last_used_at ? formatDateTime(c.last_used_at) : 'Chưa dùng'}</span>
        ),
      },
      {
        key: 'created_at',
        header: 'Đăng ký',
        width: 150,
        cell: (c) => <span className="whitespace-nowrap">{formatDateTime(c.created_at)}</span>,
      },
      { key: 'ip', header: 'IP đăng ký', width: 140, defaultHidden: true, cell: (c) => <span className="font-mono text-xs">{c.ip || '—'}</span> },
      { key: 'auth_method', header: 'Cách xác thực', width: 150, defaultHidden: true, cell: (c) => c.auth_method || '—' },
    ]
    if (!canDelete) return base
    return [
      ...base,
      {
        key: 'actions',
        header: 'Thao tác',
        width: 110,
        hideable: false,
        cell: (c) => (
          <Button
            variant="ghost"
            size="sm"
            className="text-destructive hover:text-destructive"
            aria-label={`Xóa ứng dụng ${c.client_name || c.client_id}`}
            disabled={remove.isPending}
            onClick={() => void handleDelete(c)}
          >
            <Trash2 className="size-4" />
            Xóa
          </Button>
        ),
      },
    ]
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handleDelete chỉ đóng gói `remove`, đã nằm trong deps
  }, [canDelete, remove.isPending])

  async function handleDelete(c: OAuthClient) {
    const name = c.client_name || c.client_id
    const live = c.live_grants > 0 ? `${c.live_grants} kết nối đang sống sẽ bị cắt ngay, ` : 'Hiện không có kết nối nào đang sống; '
    const ok = await confirm({
      title: 'Xóa ứng dụng AI',
      message:
        `Xóa ứng dụng "${name}" (nơi quay về: ${c.redirect_hosts.join(', ') || 'không khai'})? ` +
        `Xóa là cắt mọi kết nối của ứng dụng này: ${live}người đang dùng phải bấm "Cho phép" lại từ đầu nếu muốn nối tiếp.`,
      confirmLabel: 'Xóa ứng dụng',
    })
    if (!ok) return
    try {
      await remove.mutateAsync(c.id)
    } catch {
      //  Toast lỗi tự động (403 thiếu quyền ghi, 404 ứng dụng đã bị dọn).
    }
  }

  if (!allowed) {
    return (
      <PageContainer>
        <PageHeader title="Ứng dụng AI đã kết nối" description={DESCRIPTION} />
        <ErrorState
          title="Màn này dành cho người quản lý trợ lý AI"
          description="Bạn vẫn dùng được Bộ skill, Kết nối và Nhật ký sử dụng ở menu bên trái."
        />
      </PageContainer>
    )
  }

  const untrusted = (rows ?? []).filter((c) => !c.trusted).length
  const live = (rows ?? []).reduce((sum, c) => sum + c.live_grants, 0)

  return (
    <PageContainer fill>
      <PageHeader title="Ứng dụng AI đã kết nối" description={DESCRIPTION} />
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={shownRows}
          getRowId={(c) => c.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            filtering
              ? 'Không có ứng dụng nào khớp bộ lọc.'
              : 'Chưa có ứng dụng nào. Ứng dụng xuất hiện ở đây khi có người bấm "Cho phép" trên màn đồng ý kết nối (ChatGPT, claude.ai…).'
          }
          storageKey="ai-skill.oauth-clients"
          toolbar={
            <>
              <div className="relative min-w-48 flex-1 md:max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm ứng dụng, người dùng"
                  aria-label="Tìm ứng dụng"
                  value={keyword}
                  maxLength={80}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44" aria-label="Lọc trạng thái">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {OAUTH_CLIENT_STATUS_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {rows && (
                <span className="text-sm text-muted-foreground">
                  {rows.length} ứng dụng · {live} kết nối đang sống
                  {untrusted > 0 && (
                    <>
                      {' · '}
                      <span className="font-medium text-destructive">{untrusted} host lạ</span>
                    </>
                  )}
                </span>
              )}
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}

const DESCRIPTION =
  'Ứng dụng AI tự đăng ký khi có người bấm "Cho phép" (ChatGPT, claude.ai…). Tên là do ứng dụng tự khai, đừng tin — nhìn nơi quay về để biết thật giả.'

/** `client_id` dạng `dego_oc_…` dài và ngẫu nhiên — chỉ hiện 6 ký tự cuối để đối chiếu với nhật ký, tránh bảng tràn. */
function shortId(clientId: string): string {
  if (!clientId) return ''
  return clientId.length > 8 ? `…${clientId.slice(-6)}` : clientId
}
