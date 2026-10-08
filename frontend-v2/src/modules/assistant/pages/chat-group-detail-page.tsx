import { Download, FileText, Sparkles } from 'lucide-react'
import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { DetailPageHeader } from '@/shared/ui/detail-page-header'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Switch } from '@/shared/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

import { chatGroupApi, type ChatGroupItem, type ChatGroupMessage } from '../api/chat-group-api'
import { MarkdownMessage } from '../components/markdown-message'
import {
  useChatGroup,
  useChatGroupMessages,
  useChatGroupMeta,
  useChatGroupSummaries,
  useChatGroupViews,
  useSummarizeChatGroup,
  useUpdateChatGroup,
} from '../hooks/use-chat-groups'
import { describeGroupState, formatFileSize, getChannelTone } from '../utils/chat-group-format'

/** Khoảng tóm tắt cho nút «Tóm tắt» — trần là hạn giữ tin (90 ngày). */
const SUMMARY_RANGES = [
  { hours: 24, label: '24 giờ qua' },
  { hours: 72, label: '3 ngày qua' },
  { hours: 168, label: '7 ngày qua' },
  { hours: 720, label: '30 ngày qua' },
]

/**
 * CHI TIẾT MỘT NHÓM CHAT (ai-CR-123) — `/assistant/groups/:id`.
 *
 * Tin + tệp bot đã ghi, các bản tóm tắt đã lưu (từ câu hỏi gửi bot / Trợ lý web, hoặc nút «Tóm tắt» ở đây). Người
 * quản lý bot AI mở nhóm mình không ở thì backend ghi nhật ký — tab «Nhật ký xem» cho thấy ai đã mở.
 */
export function ChatGroupDetailPage() {
  const { id } = useParams()
  const groupId = Number(id) || 0
  const meta = useChatGroupMeta()
  const { data: group, isLoading, isError, refetch } = useChatGroup(groupId)

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-48 w-full" />
      </PageContainer>
    )
  }
  if (isError || !group) {
    return (
      <PageContainer>
        <ErrorState title="Không mở được nhóm này" description="Nhóm không còn, hoặc anh/chị không ở trong nhóm.">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Thử lại
          </Button>
        </ErrorState>
      </PageContainer>
    )
  }

  const state = describeGroupState(group)
  const canViewAll = Boolean(meta.data?.can_view_all)

  return (
    <PageContainer>
      <DetailPageHeader
        backTo={appRoutes.assistant.groups}
        backLabel="Về danh sách nhóm chat"
        title={group.title}
        badges={
          <>
            <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', getChannelTone(group.channel))}>
              {group.channel_label}
            </span>
            <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', state.tone)}>{state.label}</span>
          </>
        }
      />

      <GroupFacts group={group} categories={meta.data?.categories ?? []} />

      <Tabs defaultValue="messages" className="mt-4">
        <TabsList>
          <TabsTrigger value="messages">Tin nhắn</TabsTrigger>
          <TabsTrigger value="files">Tệp ({group.file_count})</TabsTrigger>
          <TabsTrigger value="summaries">Bản tóm tắt</TabsTrigger>
          {canViewAll && <TabsTrigger value="views">Nhật ký xem</TabsTrigger>}
        </TabsList>
        <TabsContent value="messages">
          <MessageList groupId={group.id} />
        </TabsContent>
        <TabsContent value="files">
          <MessageList groupId={group.id} filesOnly />
        </TabsContent>
        <TabsContent value="summaries">
          <SummaryList groupId={group.id} />
        </TabsContent>
        {canViewAll && (
          <TabsContent value="views">
            <ViewList groupId={group.id} />
          </TabsContent>
        )}
      </Tabs>
    </PageContainer>
  )
}

interface GroupFactsProps {
  group: ChatGroupItem
  categories: { value: number; label: string }[]
}

function GroupFacts({ group, categories }: GroupFactsProps) {
  const update = useUpdateChatGroup(group.id)
  const save = (body: { category?: number; paused?: boolean }) =>
    update.mutate(body, {
      onSuccess: () => toast.success('Đã lưu'),
      onError: (e) => toast.error(extractErrorMessage(e)),
    })

  const facts: [string, string][] = [
    ['Người thêm bot', group.owner_label || '—'],
    ['Số tin đang giữ', group.message_count.toLocaleString('vi-VN')],
    ['Tin mới nhất', formatDateTime(group.last_message_at) || '—'],
    ['Thành viên', group.members_count == null ? '—' : String(group.members_count)],
  ]

  return (
    <Card>
      <CardContent className="grid gap-x-6 gap-y-3 pt-6 sm:grid-cols-2 lg:grid-cols-3">
        {facts.map(([label, value]) => (
          <div key={label} className="min-w-0">
            <div className="text-xs text-muted-foreground">{label}</div>
            <div className="truncate text-sm">{value}</div>
          </div>
        ))}
        <div className="min-w-0">
          <div className="text-xs text-muted-foreground">Loại nhóm</div>
          {group.can_edit ? (
            <Select value={String(group.category)} onValueChange={(v) => save({ category: Number(v) })}>
              <SelectTrigger className="mt-1 h-8 w-52 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {categories.map((c) => (
                  <SelectItem key={c.value} value={String(c.value)}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <div className="text-sm">{group.category_label}</div>
          )}
        </div>
        {group.can_pause && (
          <div className="min-w-0">
            <div className="text-xs text-muted-foreground">Ghi tin nhóm này</div>
            <label className="mt-1 flex items-center gap-2 text-sm">
              <Switch
                checked={!group.paused}
                disabled={update.isPending}
                onCheckedChange={(on) => save({ paused: !on })}
                aria-label="Ghi tin nhóm này"
              />
              {group.paused ? 'Đang ngừng ghi' : 'Đang ghi'}
            </label>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface MessageListProps {
  groupId: number
  filesOnly?: boolean
}

function MessageList({ groupId, filesOnly = false }: MessageListProps) {
  const [search, setSearch] = useState('')
  const q = useDebouncedValue(search, 300).trim()
  const query = useChatGroupMessages(groupId, { q: q || undefined, files_only: filesOnly || undefined })
  const rows = (query.data?.pages ?? []).flatMap((p) => p.items)

  return (
    <Card className="mt-3">
      <CardContent className="space-y-3 pt-6">
        {!filesOnly && (
          <SearchField value={search} onChange={setSearch} placeholder="Tìm trong tin nhắn…" className="w-72" />
        )}
        {query.isLoading && <Skeleton className="h-32 w-full" />}
        {query.isError && <p className="text-sm text-destructive">Không tải được tin nhắn.</p>}
        {!query.isLoading && rows.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {q ? 'Không có tin nào khớp.' : filesOnly ? 'Nhóm chưa có tệp nào.' : 'Nhóm chưa có tin nào.'}
          </p>
        )}
        <ul className="divide-y">
          {rows.map((m) => (
            <MessageRow key={m.id} groupId={groupId} message={m} />
          ))}
        </ul>
        {query.hasNextPage && (
          <Button variant="outline" size="sm" disabled={query.isFetchingNextPage} onClick={() => query.fetchNextPage()}>
            Xem tin cũ hơn
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

interface MessageRowProps {
  groupId: number
  message: ChatGroupMessage
}

function MessageRow({ groupId, message }: MessageRowProps) {
  //  Chặn bấm đúp bằng ref (đổi ngay trong tick) — `disabled` theo state chỉ có hiệu lực ở lần render sau.
  const busy = useRef(false)
  const [downloading, setDownloading] = useState(false)
  const file = message.file

  const download = async () => {
    if (!file || busy.current) return
    busy.current = true
    setDownloading(true)
    try {
      await chatGroupApi.downloadFile(groupId, message.id, file.name || 'tep')
    } catch (e) {
      toast.error(extractErrorMessage(e))
    } finally {
      busy.current = false
      setDownloading(false)
    }
  }

  return (
    <li className="py-2">
      <div className="flex flex-wrap items-baseline gap-x-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{message.from_name || 'Ẩn danh'}</span>
        <span>{formatDateTime(message.sent_at)}</span>
      </div>
      {message.text && <p className="text-sm whitespace-pre-wrap">{message.text}</p>}
      {file && (
        <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
          <FileText className="size-4 text-muted-foreground" />
          <span className="truncate">{file.name}</span>
          {formatFileSize(file.size) && <span className="text-xs text-muted-foreground">{formatFileSize(file.size)}</span>}
          <Button variant="ghost" size="sm" disabled={downloading} onClick={download} title="Tải tệp">
            <Download className="size-4" />
          </Button>
        </div>
      )}
    </li>
  )
}

function SummaryList({ groupId }: { groupId: number }) {
  const [hours, setHours] = useState(24)
  const summaries = useChatGroupSummaries(groupId)
  const summarize = useSummarizeChatGroup(groupId)
  const busy = useRef(false)

  const run = () => {
    if (busy.current) return
    busy.current = true
    summarize.mutate(hours, {
      onSuccess: (out) => {
        if (out.empty) toast.info('Nhóm không có tin nào trong khoảng này')
      },
      onError: (e) => toast.error(extractErrorMessage(e)),
      onSettled: () => {
        busy.current = false
      },
    })
  }

  const items = summaries.data?.items ?? []
  return (
    <Card className="mt-3">
      <CardContent className="space-y-4 pt-6">
        <div className="flex flex-wrap items-center gap-2">
          <Select value={String(hours)} onValueChange={(v) => setHours(Number(v))}>
            <SelectTrigger className="h-9 w-40 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SUMMARY_RANGES.map((r) => (
                <SelectItem key={r.hours} value={String(r.hours)}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" disabled={summarize.isPending} onClick={run}>
            <Sparkles className="mr-1.5 size-4" /> {summarize.isPending ? 'Đang tóm tắt…' : 'Tóm tắt'}
          </Button>
        </div>
        {summaries.isLoading && <Skeleton className="h-24 w-full" />}
        {!summaries.isLoading && items.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Chưa có bản tóm tắt nào. Bấm «Tóm tắt», hoặc hỏi bot / Trợ lý AI «nhóm này hôm nay bàn gì» — câu trả lời
            sẽ được lưu ở đây.
          </p>
        )}
        {items.map((s) => (
          <div key={s.id} className="rounded-md border p-3">
            <div className="mb-2 flex flex-wrap gap-x-2 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{s.user_label || '—'}</span>
              <span>{formatDateTime(s.created_at)}</span>
              <span>{s.source === 2 ? 'nút Tóm tắt' : 'hỏi bot / Trợ lý'}</span>
              {s.question && <span className="italic">«{s.question}»</span>}
            </div>
            <MarkdownMessage content={s.text} className="text-sm" />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function ViewList({ groupId }: { groupId: number }) {
  const views = useChatGroupViews(groupId, true)
  const items = views.data?.items ?? []
  return (
    <Card className="mt-3">
      <CardContent className="pt-6">
        {views.isLoading && <Skeleton className="h-16 w-full" />}
        {!views.isLoading && items.length === 0 && (
          <p className="text-sm text-muted-foreground">Chưa có ai ngoài thành viên mở nhóm này.</p>
        )}
        <ul className="divide-y text-sm">
          {items.map((v) => (
            <li key={v.id} className="flex flex-wrap gap-x-3 py-1.5">
              <span className="font-medium">{v.user_label || '—'}</span>
              <span className="text-muted-foreground">{v.what}</span>
              <span className="text-muted-foreground">{formatDateTime(v.at)}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
