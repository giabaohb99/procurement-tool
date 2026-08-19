import { AlertTriangle, Bell } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { toAppPath } from './notification-link'
import type { AppNotification, SystemAlert } from './notification-types'
import { useNotificationActions, useNotifications, useSystemAlerts } from './use-notifications'

/**
 * CHUÔNG THÔNG BÁO trên thanh trên — bản dựng lại của `NotificationBell` ở app
 * cũ (`frontend/src/components/NotificationBell.tsx`), dùng chung API.
 *
 * Số trên chuông = thông báo chưa đọc + cảnh báo mức nguy hiểm: cả hai đều là
 * "việc phải xử lý", đếm riêng thì người dùng phải cộng nhẩm.
 */
export function NotificationBell() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<'all' | 'unread'>('all')

  const { data: notifications } = useNotifications(tab === 'unread')
  const { data: alerts } = useSystemAlerts()
  const { markRead, readAll, clearRead } = useNotificationActions()

  const unread = notifications?.unread ?? 0
  const items = notifications?.items ?? []
  const alertItems = alerts?.items ?? []
  const badge = unread + (alerts?.danger ?? 0)

  function openNotification(item: AppNotification) {
    setOpen(false)
    if (!item.is_read) markRead.mutate(item.id)
    // Màn hình chưa có bên v2 thì đứng yên, không quăng người dùng vào trang 404.
    const path = toAppPath(item.link)
    if (path) navigate(path)
  }

  function openAlert(alert: SystemAlert) {
    setOpen(false)
    const path = toAppPath(alert.link)
    if (path) navigate(path)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          title="Thông báo"
          aria-label={badge > 0 ? `Thông báo (${badge} chưa xử lý)` : 'Thông báo'}
          className="relative text-muted-foreground hover:text-foreground"
        >
          <Bell className="size-4.5" />
          {badge > 0 && (
            <span className="absolute top-0.5 right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] leading-none font-bold text-white">
              {badge > 99 ? '99+' : badge}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent align="end" className="w-95 p-0">
        <div className="flex items-center justify-between gap-2 border-b px-3 py-2.5">
          <span className="text-sm font-semibold text-navy">
            Thông báo{unread > 0 && ` (${unread})`}
          </span>
          <Tabs value={tab} onValueChange={(value) => setTab(value as 'all' | 'unread')}>
            <TabsList>
              <TabsTrigger value="all">Tất cả</TabsTrigger>
              <TabsTrigger value="unread">Chưa đọc</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="max-h-[58vh] overflow-y-auto">
          {items.length === 0 && alertItems.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-muted-foreground">
              {tab === 'unread' ? 'Không có thông báo chưa đọc.' : 'Không có thông báo nào.'}
            </p>
          )}

          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => openNotification(item)}
              className={cn(
                'flex w-full gap-2.5 border-b px-3 py-2.5 text-left hover:bg-accent',
                !item.is_read && 'bg-primary/5',
              )}
            >
              <Bell
                className={cn(
                  'mt-0.5 size-4 shrink-0',
                  item.is_read ? 'text-muted-foreground' : 'text-primary',
                )}
              />
              <span className="min-w-0 flex-1">
                <span
                  className={cn(
                    'block text-sm text-navy',
                    item.is_read ? 'font-medium' : 'font-semibold',
                  )}
                >
                  {item.title}
                </span>
                <span className="mt-0.5 block text-xs text-muted-foreground">{item.body}</span>
                <span className="mt-0.5 block text-[11px] text-muted-foreground">
                  {formatDateTime(item.at)}
                </span>
              </span>
            </button>
          ))}

          {/* Cảnh báo hệ thống: không ai gửi, backend tính từ dữ liệu đang có. */}
          {alertItems.length > 0 && (
            <p className="bg-muted px-3 py-1.5 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
              Cảnh báo · việc cần làm
            </p>
          )}
          {alertItems.map((alert, index) => (
            <button
              key={`${alert.type}-${index}`}
              type="button"
              onClick={() => openAlert(alert)}
              className="flex w-full gap-2.5 border-b px-3 py-2 text-left hover:bg-accent"
            >
              <AlertTriangle
                className={cn(
                  'mt-0.5 size-4 shrink-0',
                  alert.level === 'danger' ? 'text-destructive' : 'text-amber-600',
                )}
              />
              <span className="min-w-0 flex-1 text-xs text-foreground">{alert.title}</span>
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between gap-2 border-t bg-muted/40 px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={unread === 0 || readAll.isPending}
            onClick={() => readAll.mutate()}
          >
            Đánh dấu đã đọc
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            disabled={clearRead.isPending}
            onClick={() => clearRead.mutate()}
          >
            Xóa đã đọc
          </Button>
        </div>

        {/* Chuông chỉ giữ 20 cái mới nhất — lối ra trang đầy đủ (tìm kiếm, phân
            trang, xóa từng cái) phải nằm ngay đây, không bắt người dùng tự mò URL. */}
        <Link
          to={appRoutes.notifications}
          onClick={() => setOpen(false)}
          className="block border-t px-3 py-2 text-center text-[13px] font-medium text-primary hover:bg-accent"
        >
          Xem tất cả thông báo
        </Link>
      </PopoverContent>
    </Popover>
  )
}
