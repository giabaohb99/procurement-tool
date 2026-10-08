import { MessagesSquare, RotateCw } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import type { ChatGroupItem } from '../api/chat-group-api'
import { ZaloAccountCard } from '../components/zalo-account-card'
import { useChatGroupMeta, useChatGroups } from '../hooks/use-chat-groups'
import { describeGroupState, getChannelTone } from '../utils/chat-group-format'

//  `-1` chứ không `0`: loại 0 «Chưa phân loại» là một giá trị lọc thật (luật bảng có bộ lọc, duoc-CR-322).
const ALL = '-1'

/**
 * NHÓM CHAT CỦA BOT (ai-CR-123) — `/assistant/groups`.
 *
 * Bot cá nhân đọc nhóm Telegram / Zalo, ghi tin + tệp + bản tóm tắt, nhưng chỉ trả lời riêng. Màn này là chỗ xem lại
 * những gì bot đã ghi: «Nhóm của tôi» = nhóm mình là thành viên; «Tất cả nhóm» chỉ cho người quản lý bot AI.
 */
export function ChatGroupListPage() {
  const navigate = useNavigate()
  const meta = useChatGroupMeta()
  const [scope, setScope] = useState<'mine' | 'all'>('mine')
  const [channel, setChannel] = useState(ALL)
  const [category, setCategory] = useState(ALL)
  const [search, setSearch] = useState('')
  const q = useDebouncedValue(search, 300)
  const canViewAll = Boolean(meta.data?.can_view_all)

  const { data, isLoading, isError, refetch } = useChatGroups({
    scope: canViewAll ? scope : 'mine',
    channel: channel === ALL ? undefined : channel,
    category: category === ALL ? undefined : Number(category),
    q: q.trim() || undefined,
    include_inactive: canViewAll && scope === 'all' ? true : undefined,
  })
  const filtered = channel !== ALL || category !== ALL || q.trim() !== ''

  const columns: DataTableColumn<ChatGroupItem>[] = [
    {
      key: 'title',
      header: 'Nhóm',
      width: 280,
      cell: (r) => (
        <span className="truncate font-medium" title={r.title}>
          {r.title}
        </span>
      ),
    },
    {
      key: 'channel',
      header: 'Kênh / bot',
      width: 190,
      cell: (r) => (
        <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', getChannelTone(r.channel))}>
          {r.channel_label}
        </span>
      ),
    },
    { key: 'category', header: 'Loại', width: 150, cell: (r) => r.category_label },
    { key: 'message_count', header: 'Số tin', width: 90, cell: (r) => r.message_count.toLocaleString('vi-VN') },
    { key: 'file_count', header: 'Tệp', width: 70, cell: (r) => r.file_count.toLocaleString('vi-VN') },
    {
      key: 'last_message_at',
      header: 'Tin mới nhất',
      width: 150,
      cell: (r) => formatDateTime(r.last_message_at) || '—',
    },
    { key: 'owner', header: 'Người thêm bot', width: 200, cell: (r) => r.owner_label || '—' },
    {
      key: 'state',
      header: 'Tình trạng',
      width: 140,
      cell: (r) => {
        const s = describeGroupState(r)
        return <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', s.tone)}>{s.label}</span>
      },
    },
    {
      key: 'members_count',
      header: 'Thành viên',
      width: 100,
      defaultHidden: true,
      cell: (r) => (r.members_count == null ? '—' : r.members_count),
    },
    {
      key: 'is_member',
      header: 'Tôi ở trong nhóm',
      width: 130,
      defaultHidden: true,
      cell: (r) => (r.is_member ? 'Có' : 'Không'),
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Nhóm chat"
        description={`Tin, tệp và bản tóm tắt bot đã ghi ở các nhóm Telegram / Zalo — bot chỉ trả lời riêng, giữ tin ${
          meta.data?.retention_days ?? 90
        } ngày`}
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Làm mới danh sách">
            <RotateCw className="mr-1.5 size-4" /> Làm mới
          </Button>
        }
      />

      {canViewAll && meta.data?.zalo_enabled && (
        <div className="mb-3">
          <ZaloAccountCard canManage={Boolean(meta.data?.can_manage)} />
        </div>
      )}

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => String(r.id)}
          onRowClick={(r) => navigate(appRoutes.assistant.group(r.id))}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          emptyMessage={
            filtered
              ? 'Không có nhóm nào khớp bộ lọc.'
              : scope === 'all'
                ? 'Bot chưa ở nhóm nào.'
                : 'Anh/chị chưa ở nhóm nào có bot. Thêm bot (Telegram) hoặc tài khoản Zalo công ty vào nhóm, rồi nhắn riêng bot «/dangnhap <mã>» một lần.'
          }
          storageKey="assistant.chat_groups"
          toolbar={
            <div className="flex flex-wrap items-center gap-3">
              {canViewAll && (
                <Tabs value={scope} onValueChange={(v) => setScope(v === 'all' ? 'all' : 'mine')}>
                  <TabsList>
                    <TabsTrigger value="mine">Nhóm của tôi</TabsTrigger>
                    <TabsTrigger value="all">Tất cả nhóm</TabsTrigger>
                  </TabsList>
                </Tabs>
              )}
              <SearchField value={search} onChange={setSearch} placeholder="Tìm tên nhóm…" className="w-64" />
              <Select value={channel} onValueChange={setChannel}>
                <SelectTrigger className="h-9 w-52 text-xs">
                  <SelectValue placeholder="Kênh" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi kênh</SelectItem>
                  {(meta.data?.channels ?? []).map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="h-9 w-48 text-xs">
                  <SelectValue placeholder="Loại nhóm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi loại</SelectItem>
                  {(meta.data?.categories ?? []).map((c) => (
                    <SelectItem key={c.value} value={String(c.value)}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <MessagesSquare className="size-4" /> {data?.total ?? 0} nhóm
              </span>
            </div>
          }
        />
      </Card>
    </PageContainer>
  )
}
