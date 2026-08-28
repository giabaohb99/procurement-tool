import { Bell, BellOff, Check, CheckCheck, Search, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTablePagination } from '@/shared/data-table/data-table-pagination'
import {
  buildNotificationParams,
  type NotificationTab,
} from '@/shared/notifications/notification-filter'
import { toAppPath } from '@/shared/notifications/notification-link'
import type { AppNotification } from '@/shared/notifications/notification-types'
import {
  useNotificationActions,
  useNotificationList,
} from '@/shared/notifications/use-notifications'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { IconInput } from '@/shared/ui/icon-input'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Tab THÔNG BÁO của Trang cá nhân — bản đầy đủ của cái chuông trên thanh tiêu đề.
 *
 * CR-215: trước là trang riêng `/notifications`; hai trang "thông báo" song song
 * làm người dùng rối nên gom về đây, route cũ chuyển hướng về `/me?tab=notifications`.
 *
 * Bộ lọc tất cả/chưa đọc và ô tìm giữ bằng state cục bộ (KHÔNG ghi URL): tham số
 * `?tab=` của URL đã thuộc về dải tab của Trang cá nhân.
 */
export function ProfileNotificationsTab() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // Gõ tới đâu hỏi server tới đó thì phí — chờ ngừng gõ 300ms mới hỏi.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  const params = buildNotificationParams({
    page,
    pageSize,
    tab: tab as NotificationTab,
    search: debouncedSearch,
  })
  const { data, isLoading } = useNotificationList(params)
  const { markRead, readAll, clearRead, remove } = useNotificationActions()

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const unread = data?.unread ?? 0

  // Đổi bộ lọc thì về trang 1 — đang ở trang 4 mà lọc còn 2 trang là màn trắng.
  function changeTab(value: string) {
    setTab(value)
    setPage(1)
  }

  function changeSearch(value: string) {
    setSearch(value)
    setPage(1)
  }

  function open(item: AppNotification) {
    if (!item.is_read) markRead.mutate(item.id)
    // Màn hình v2 chưa có thì đứng yên, thà vậy còn hơn quăng vào trang 404.
    const path = toAppPath(item.link)
    if (path) navigate(path)
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <Tabs value={tab} onValueChange={changeTab}>
          <TabsList>
            <TabsTrigger value="all">Tất cả</TabsTrigger>
            <TabsTrigger value="unread">Chưa đọc</TabsTrigger>
          </TabsList>
        </Tabs>
        <IconInput
          icon={Search}
          value={search}
          onChange={(event) => changeSearch(event.target.value)}
          placeholder="Tìm theo tiêu đề hoặc nội dung…"
          className="h-9 min-w-56 flex-1 rounded-md"
        />
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={unread === 0 || readAll.isPending}
            onClick={() => readAll.mutate()}
          >
            <CheckCheck className="size-4" />
            Đánh dấu đã đọc tất cả
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-destructive hover:text-destructive"
            disabled={clearRead.isPending}
            onClick={() => clearRead.mutate()}
          >
            <Trash2 className="size-4" />
            Xóa đã đọc
          </Button>
        </div>
      </div>

      <Card className="gap-0 overflow-hidden py-0">
        {items.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-16 text-center">
            <BellOff className="size-9 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {isLoading
                ? 'Đang tải…'
                : tab === 'unread'
                  ? 'Không có thông báo chưa đọc.'
                  : 'Không có thông báo nào.'}
            </p>
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className={cn(
                'flex gap-3 border-b px-4 py-3 last:border-b-0',
                !item.is_read && 'bg-primary/5',
              )}
            >
              {/* Cả mảng nội dung là MỘT nút: vùng bấm rộng, khỏi phải nhắm vào
                  đúng dòng tiêu đề. Hai nút thao tác đứng ngoài nút này. */}
              <button
                type="button"
                onClick={() => open(item)}
                className="flex min-w-0 flex-1 gap-3 text-left"
              >
                <Bell
                  className={cn(
                    'mt-0.5 size-4.5 shrink-0',
                    item.is_read ? 'text-muted-foreground' : 'text-primary',
                  )}
                />
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      'block text-sm text-navy dark:text-foreground',
                      item.is_read ? 'font-medium' : 'font-semibold',
                    )}
                  >
                    {item.title}
                  </span>
                  <span className="mt-0.5 block text-[13px] text-muted-foreground">
                    {item.body}
                  </span>
                  <span className="mt-1 block text-[11px] text-muted-foreground">
                    {formatDateTime(item.at)}
                  </span>
                </span>
              </button>

              <div className="flex shrink-0 items-center gap-1">
                {!item.is_read && (
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    title="Đánh dấu đã đọc"
                    aria-label="Đánh dấu đã đọc"
                    disabled={markRead.isPending}
                    onClick={() => markRead.mutate(item.id)}
                  >
                    <Check className="text-primary" />
                  </Button>
                )}
                <ConfirmIconButton
                  icon={Trash2}
                  title="Xóa thông báo"
                  confirmTitle="Xóa thông báo"
                  confirmDescription="Xóa thông báo này khỏi danh sách của bạn?"
                  confirmLabel="Xóa"
                  destructive
                  disabled={remove.isPending}
                  onConfirm={() => remove.mutate(item.id)}
                />
              </div>
            </div>
          ))
        )}
      </Card>

      {total > 0 && (
        <DataTablePagination
          page={page}
          pageSize={pageSize}
          total={total}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          unitLabel="thông báo"
        />
      )}
    </div>
  )
}
