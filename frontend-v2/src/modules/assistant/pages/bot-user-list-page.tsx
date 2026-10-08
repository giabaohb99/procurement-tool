import { RotateCw, Unlink } from 'lucide-react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

import type { BotUserLink } from '../api/chat-group-api'
import { useBotUserLinks, useRevokeBotUserLink } from '../hooks/use-chat-groups'
import { getChannelTone } from '../utils/chat-group-format'

/**
 * NGƯỜI DÙNG BOT (ai-CR-131) — `/assistant/bot-users`.
 *
 * Đại ca 08/10: «họ có quyền thì mới hỏi được, nhưng chưa biết làm sao check quyền của họ». Màn này liệt kê mọi chat
 * Telegram / Zalo đang nối với một tài khoản ERP, và tài khoản đó CÒN quyền «Trợ lý AI» không — thiếu quyền thì bot
 * không trả lời dù vẫn nối. Cấp / thu quyền vẫn ở màn Phân quyền tài khoản; ở đây chỉ xem và gỡ liên kết.
 */
export function BotUserListPage() {
  const { can } = usePermission()
  const canManage = can('agent_group', 'write')
  const { data, isLoading, isError, refetch } = useBotUserLinks()
  const revoke = useRevokeBotUserLink()

  const columns: DataTableColumn<BotUserLink>[] = [
    {
      key: 'user',
      header: 'Tài khoản ERP',
      width: 260,
      cell: (r) => (
        <div className="min-w-0">
          <div className="truncate font-medium">{r.user_label}</div>
          {r.user_detail && <div className="truncate text-xs text-muted-foreground">{r.user_detail}</div>}
        </div>
      ),
    },
    {
      key: 'channel',
      header: 'Kênh',
      width: 190,
      cell: (r) => (
        <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', getChannelTone(r.channel))}>
          {r.channel_label}
        </span>
      ),
    },
    { key: 'name', header: 'Tên trên kênh', width: 160, cell: (r) => r.name || '—' },
    {
      key: 'permission',
      header: 'Quyền Trợ lý AI',
      width: 140,
      cell: (r) => (
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-xs font-medium',
            r.has_permission ? TONE_CLASS.done : TONE_CLASS.danger,
          )}
          title={r.has_permission ? undefined : 'Bot không trả lời người này cho tới khi được cấp quyền «Trợ lý AI»'}
        >
          {r.has_permission ? 'Có' : 'Thiếu — bot không trả lời'}
        </span>
      ),
    },
    { key: 'last', header: 'Nhắn gần nhất', width: 150, cell: (r) => formatDateTime(r.last_message_at) || '—' },
    { key: 'linked_at', header: 'Nối lúc', width: 150, cell: (r) => formatDateTime(r.linked_at) || '—' },
    { key: 'expires_at', header: 'Hết hạn', width: 150, cell: (r) => formatDateTime(r.expires_at) || '—' },
    { key: 'chat', header: 'Mã chat', width: 100, defaultHidden: true, cell: (r) => r.chat },
    ...(canManage
      ? [
          {
            key: 'actions',
            header: '',
            width: 60,
            cell: (r: BotUserLink) => (
              <ConfirmIconButton
                icon={Unlink}
                title="Gỡ liên kết"
                confirmTitle="Gỡ liên kết bot"
                confirmDescription={`Chat ${r.channel_label} của ${r.user_label} sẽ thôi dùng bot cho tới khi đăng nhập lại.`}
                confirmLabel="Gỡ"
                destructive
                disabled={revoke.isPending}
                onConfirm={() =>
                  revoke.mutate(r.id, {
                    onSuccess: () => toast.success('Đã gỡ liên kết'),
                    onError: (e) => toast.error(extractErrorMessage(e)),
                  })
                }
              />
            ),
          } satisfies DataTableColumn<BotUserLink>,
        ]
      : []),
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Người dùng bot"
        description="Ai đang nối Telegram / Zalo với tài khoản ERP. Dùng bot cần quyền «Trợ lý AI» — cấp ở màn Phân quyền tài khoản"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Làm mới danh sách">
            <RotateCw className="mr-1.5 size-4" /> Làm mới
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
          emptyMessage="Chưa ai nối bot. Mỗi người lấy mã ở Trang cá nhân rồi nhắn bot «/dangnhap <mã>»."
          storageKey="assistant.bot_users"
        />
      </Card>
    </PageContainer>
  )
}
