import { ShieldAlert } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

import type { LoginHistoryItem, LoginHistoryResult } from '../api/login-session-api'

/** Tối đa bao nhiêu dòng lịch sử vẽ ra trước khi bấm «Xem thêm». */
export const HISTORY_PREVIEW_ROWS = 10

interface LoginHistoryListProps {
  data: LoginHistoryResult | undefined
  isLoading: boolean
  /** Số ngày đang xem — cho câu rỗng lúc `data` chưa về. */
  days: number
  /** Dòng tiêu đề «Lịch sử N ngày · x lần đăng nhập · y lần thất bại».
   *  Tắt khi thẻ bọc ngoài đã có tiêu đề riêng (tab ở Trang cá nhân). */
  heading?: boolean
  className?: string
}

/**
 * Danh sách LỊCH SỬ ĐĂNG NHẬP — dùng chung cho hai chỗ (bao-CR-400):
 * thẻ «Phiên đăng nhập» ở hồ sơ nhân sự (dữ liệu từ cửa quản trị) và tab
 * «Lịch sử đăng nhập» ở Trang cá nhân (dữ liệu từ cửa tự thân). Hai cửa trả cùng
 * một hình `LoginHistoryResult`, nên phần vẽ chỉ có một bản: dòng thành công
 * bày máy + IP + kết cục của phiên, dòng thất bại bày câu lỗi backend ghi.
 */
export function LoginHistoryList({
  data,
  isLoading,
  days,
  heading = true,
  className,
}: LoginHistoryListProps) {
  const [showAll, setShowAll] = useState(false)
  const rows = data?.items ?? []
  const visible = showAll ? rows : rows.slice(0, HISTORY_PREVIEW_ROWS)
  const failedCount = data?.failed_count ?? 0

  return (
    <section className={cn('space-y-2', className)}>
      {heading && (
        <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
          <ShieldAlert
            className={cn('size-4', failedCount > 0 ? 'text-amber-600' : 'text-muted-foreground')}
          />
          Lịch sử {days} ngày
          <span className="text-xs font-normal text-muted-foreground">
            {data ? `${data.login_count} lần đăng nhập · ${failedCount} lần thất bại` : ''}
          </span>
        </div>
      )}
      {isLoading && <Skeleton className="h-16 w-full" />}
      {!isLoading && rows.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Chưa ghi nhận lần đăng nhập nào trong {days} ngày qua.
        </p>
      )}
      {visible.length > 0 && (
        <ul className="divide-y rounded-md border text-sm">
          {visible.map((row) => (
            <LoginHistoryRow key={`${row.kind}-${row.session_id}-${row.at}`} row={row} />
          ))}
        </ul>
      )}
      {rows.length > HISTORY_PREVIEW_ROWS && (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0"
          onClick={() => setShowAll((v) => !v)}
        >
          {showAll ? 'Thu gọn' : `Xem cả ${rows.length} dòng`}
        </Button>
      )}
    </section>
  )
}

function LoginHistoryRow({ row }: { row: LoginHistoryItem }) {
  return (
    <li className="flex items-center gap-3 px-3 py-2">
      <Badge
        variant="outline"
        className={cn(
          'w-20 shrink-0 justify-center',
          row.ok
            ? 'border-emerald-500 text-emerald-600'
            : 'border-rose-500 text-rose-600 bg-rose-50 dark:bg-rose-950/40',
        )}
      >
        {row.ok ? 'Thành công' : 'Thất bại'}
      </Badge>
      <span className="w-32 shrink-0 text-xs text-muted-foreground">{formatDateTime(row.at)}</span>
      <span className="min-w-0 flex-1 truncate" title={row.message || undefined}>
        {row.ok ? row.device_label || row.login_method_label || '—' : row.message || 'Sai mật khẩu'}
      </span>
      <span className="font-mono text-xs text-muted-foreground">{row.ip || '—'}</span>
      {row.ok && row.ending && (
        <span className="hidden w-36 shrink-0 truncate text-right text-xs text-muted-foreground sm:inline">
          {row.ending}
        </span>
      )}
    </li>
  )
}
