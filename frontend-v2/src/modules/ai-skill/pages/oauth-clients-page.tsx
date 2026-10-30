import { Plug, ShieldAlert, Trash2 } from 'lucide-react'
import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { useDeleteOAuthClient, useOAuthClients } from '../hooks/use-ai-usage'
import type { OAuthClient } from '../types/ai-skill'

/**
 * bao-CR-635 — Ứng dụng AI đã kết nối: các ứng dụng (ChatGPT, claude.ai…) tự đăng ký OAuth với cổng MCP khi có người bấm
 * "Cho phép" (ai-CR-225). Tên là do ứng dụng TỰ KHAI nên không tin được — cột "Nơi quay về" (hostname) mới là thứ để
 * nhận ra thật giả; host ngoài danh sách ứng dụng quen thì máy chủ trả `trusted = false` và màn tô cảnh báo.
 * Xóa ứng dụng = cắt mọi kết nối của nó ngay (mã truy cập + mã làm mới chết), người dùng muốn nối lại phải "Cho phép" lần nữa.
 * Xem cần `agent_group.read` (như Cấu hình) — thiếu thì nói rõ, không gọi để ăn 403; xóa theo `can_delete` máy chủ trả.
 */
export function OAuthClientsPage() {
  const { can } = usePermission()
  const allowed = can('agent_group', 'read')
  const { data, isLoading, isError } = useOAuthClients(allowed)
  const remove = useDeleteOAuthClient()
  const canDelete = data?.can_delete ?? false
  const rows = data?.items

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
          rows={rows}
          getRowId={(c) => c.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage='Chưa có ứng dụng nào. Ứng dụng xuất hiện ở đây khi có người bấm "Cho phép" trên màn đồng ý kết nối (ChatGPT, claude.ai…).'
          storageKey="ai-skill.oauth-clients"
          toolbar={
            <>
              <Plug className="hidden size-4 text-muted-foreground md:block" />
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
