import { Download, FileText, Loader2 } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Button } from '@/shared/ui/button'
import { SearchField } from '@/shared/ui/search-field'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatTime } from '@/shared/utils/format-date'

import { chatGroupApi, type ChatGroupMessage } from '../api/chat-group-api'
import { useChatGroupMessages } from '../hooks/use-chat-groups'
import { buildGroupThread, formatFileSize, getAvatarTone, getInitials } from '../utils/chat-group-format'

interface GroupChatThreadProps {
  groupId: number
}

/**
 * Tin nhắn của một nhóm, dựng theo khung hội thoại của Trợ lý AI (ai-CR-123, đại ca 08/10: «giao diện tin nhắn xấu
 * quá, tận dụng giao diện tin nhắn của Trợ lý AI»): cột đọc giữa màn, bong bóng bo tròn, cũ trên mới dưới, vạch ngày,
 * gộp tin liên tiếp của cùng một người, tệp là chip bấm để tải.
 *
 * Mở ra thì cuộn xuống tin mới nhất; bấm «Xem tin cũ hơn» thì GIỮ chỗ đang đọc (không giật về đáy).
 */
export function GroupChatThread({ groupId }: GroupChatThreadProps) {
  const [search, setSearch] = useState('')
  const q = useDebouncedValue(search, 300).trim()
  const query = useChatGroupMessages(groupId, { q: q || undefined })
  const messages = useMemo(() => (query.data?.pages ?? []).flatMap((p) => p.items), [query.data])
  const items = useMemo(() => buildGroupThread(messages), [messages])

  const scrollRef = useRef<HTMLDivElement>(null)
  //  Chiều cao khung trước khi nạp tin cũ — để bù lại scrollTop, người đọc không bị đẩy đi.
  const heightBeforeOlder = useRef<number | null>(null)
  const newestId = messages[0]?.id ?? 0

  useEffect(() => {
    const frame = scrollRef.current
    if (!frame) return
    if (heightBeforeOlder.current != null) {
      frame.scrollTop += frame.scrollHeight - heightBeforeOlder.current
      heightBeforeOlder.current = null
      return
    }
    frame.scrollTop = frame.scrollHeight
  }, [items.length, newestId])

  const loadOlder = () => {
    heightBeforeOlder.current = scrollRef.current?.scrollHeight ?? null
    void query.fetchNextPage()
  }

  return (
    <div className="flex h-[calc(100dvh-20rem)] min-h-96 flex-col rounded-xl border bg-card">
      <div className="flex items-center gap-3 border-b px-4 py-2.5">
        <SearchField value={search} onChange={setSearch} placeholder="Tìm trong tin nhắn…" className="w-72" />
        {query.isFetching && !query.isLoading && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
      </div>

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-1 px-4 py-4">
          {query.hasNextPage && (
            <div className="mb-2 flex justify-center">
              <Button variant="outline" size="sm" disabled={query.isFetchingNextPage} onClick={loadOlder}>
                Xem tin cũ hơn
              </Button>
            </div>
          )}
          {query.isLoading && <Skeleton className="h-40 w-full" />}
          {query.isError && <p className="text-sm text-destructive">Không tải được tin nhắn.</p>}
          {!query.isLoading && !query.isError && items.length === 0 && (
            <p className="py-10 text-center text-sm text-muted-foreground">
              {q ? 'Không có tin nào khớp.' : 'Nhóm chưa có tin nào kể từ lúc bot vào nhóm.'}
            </p>
          )}
          {items.map((item) =>
            item.kind === 'day' ? (
              <div key={item.key} className="my-3 flex justify-center">
                <span className="rounded-full bg-muted px-3 py-1 text-xs text-muted-foreground">{item.label}</span>
              </div>
            ) : (
              <GroupMessageRow
                key={item.key}
                groupId={groupId}
                message={item.message}
                showHeader={item.showHeader}
              />
            ),
          )}
        </div>
      </div>
    </div>
  )
}

interface GroupMessageRowProps {
  groupId: number
  message: ChatGroupMessage
  showHeader: boolean
}

function GroupMessageRow({ groupId, message, showHeader }: GroupMessageRowProps) {
  const name = message.from_name || 'Ẩn danh'
  return (
    <div className={cn('flex gap-3', showHeader && 'mt-2')}>
      <div className="w-8 shrink-0">
        {showHeader && (
          <span
            className={cn(
              'flex size-8 items-center justify-center rounded-full text-xs font-semibold',
              getAvatarTone(name),
            )}
            aria-hidden
          >
            {getInitials(name)}
          </span>
        )}
      </div>
      <div className="flex min-w-0 max-w-[85%] flex-col items-start gap-1">
        {showHeader && (
          <div className="flex items-baseline gap-2 text-xs">
            <span className="font-medium text-foreground">{name}</span>
            <span className="text-muted-foreground">{formatTime(message.sent_at)}</span>
          </div>
        )}
        {message.text && (
          <div
            className="rounded-2xl rounded-tl-md bg-muted px-4 py-2.5 text-sm break-words whitespace-pre-wrap text-foreground"
            title={formatTime(message.sent_at)}
          >
            {message.text}
          </div>
        )}
        {message.file && <FileChip groupId={groupId} messageId={message.id} file={message.file} />}
      </div>
    </div>
  )
}

interface FileChipProps {
  groupId: number
  messageId: number
  file: NonNullable<ChatGroupMessage['file']>
}

/** Chip tệp — cùng dáng chip tệp trong bong bóng của Trợ lý AI; bấm là tải (bot tải hộ từ Telegram / Zalo). */
function FileChip({ groupId, messageId, file }: FileChipProps) {
  //  Chặn bấm đúp bằng ref (đổi ngay trong tick) — `disabled` theo state chỉ có hiệu lực ở lần render sau.
  const busy = useRef(false)
  const [downloading, setDownloading] = useState(false)
  const size = formatFileSize(file.size)

  const download = async () => {
    if (busy.current) return
    busy.current = true
    setDownloading(true)
    try {
      await chatGroupApi.downloadFile(groupId, messageId, file.name || 'tep')
    } catch (e) {
      toast.error(extractErrorMessage(e))
    } finally {
      busy.current = false
      setDownloading(false)
    }
  }

  return (
    <button
      type="button"
      onClick={() => void download()}
      disabled={downloading}
      title={`Tải tệp ${file.name}`}
      className={cn(
        'inline-flex max-w-72 items-center gap-2 rounded-xl border bg-background px-3 py-2 text-sm',
        'hover:bg-accent disabled:opacity-60',
      )}
    >
      <FileText className="size-4 shrink-0 text-muted-foreground" />
      <span className="truncate">{file.name}</span>
      {size && <span className="shrink-0 text-xs text-muted-foreground">{size}</span>}
      {downloading ? (
        <Loader2 className="size-4 shrink-0 animate-spin" />
      ) : (
        <Download className="size-4 shrink-0 text-muted-foreground" />
      )}
    </button>
  )
}
