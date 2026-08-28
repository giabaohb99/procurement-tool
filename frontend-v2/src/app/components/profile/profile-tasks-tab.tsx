import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Banknote,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Eye,
  EyeOff,
  FileSignature,
  FileText,
  ListFilter,
  RotateCcw,
  ScrollText,
  Search,
  ShoppingCart,
  Truck,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { apiGet, apiPost } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

/**
 * Tab VIỆC CẦN LÀM của Trang cá nhân.
 *
 * CR-215: "Đánh dấu làm xong" lưu SERVER theo tài khoản (`/api/dashboard/tasks/dismiss`)
 * chứ không còn localStorage — nhờ vậy chuông cảnh báo và khối cảnh báo dashboard
 * cùng ẩn theo, và đổi máy vẫn giữ. Khóa việc (`item.key`) do backend sinh.
 */

interface DashboardTaskItem {
  /** Khóa ổn định backend sinh — dùng cho đánh dấu xong/khôi phục. */
  key: string
  type: 'sign' | 'pr' | 'sr' | 'po' | 'late' | 'payable' | 'contract' | string
  label: string
  code: string
  title: string
  subtitle: string
  date: string
  link: string
  /** Tài khoản này đã đánh dấu xong việc này. */
  dismissed: boolean
}

interface DashboardTasksData {
  total: number
  by_type: Record<string, number>
  dismissed_total: number
  page: number
  page_size: number
  items: DashboardTaskItem[]
}

const TASK_META: Record<
  string,
  { label: string; short: string; colorClass: string; icon: typeof FileText }
> = {
  sign: {
    label: 'Chờ tôi duyệt',
    short: 'Chờ duyệt',
    colorClass: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400',
    icon: FileSignature,
  },
  pr: {
    label: 'YCMH chờ duyệt',
    short: 'YCMH',
    colorClass: 'bg-blue-500/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400',
    icon: FileText,
  },
  sr: {
    label: 'Khảo sát chờ duyệt',
    short: 'Khảo sát',
    colorClass: 'bg-cyan-500/10 text-cyan-600 dark:bg-cyan-500/20 dark:text-cyan-400',
    icon: ClipboardCheck,
  },
  po: {
    label: 'ĐMH chờ duyệt',
    short: 'ĐMH',
    colorClass: 'bg-purple-500/10 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400',
    icon: ShoppingCart,
  },
  late: {
    label: 'Giao hàng trễ',
    short: 'Giao hàng',
    colorClass: 'bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400',
    icon: Truck,
  },
  payable: {
    label: 'Công nợ quá hạn',
    short: 'Công nợ',
    colorClass: 'bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400',
    icon: Banknote,
  },
  contract: {
    label: 'Hợp đồng hết hạn',
    short: 'Hợp đồng',
    colorClass: 'bg-orange-500/10 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400',
    icon: ScrollText,
  },
}

function normalizeTaskLink(link: string): string {
  if (!link) return '#'
  if (link.startsWith('/purchase-requests')) {
    return link.replace('/purchase-requests', '/procurement/purchase-requests')
  }
  if (link.startsWith('/survey-requests')) {
    return link.replace('/survey-requests', '/procurement/survey-requests')
  }
  if (link.startsWith('/purchase-orders')) {
    return link.replace('/purchase-orders', '/procurement/purchase-orders')
  }
  if (link.startsWith('/payables')) {
    return link.replace('/payables', '/finance/payables')
  }
  if (link.startsWith('/contracts')) {
    return link.replace('/contracts', '/production/contracts')
  }
  return link
}

export function ProfileTasksTab({ onCountChange }: { onCountChange?: (count: number) => void }) {
  const [selectedType, setSelectedType] = useState<string>('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [showHidden, setShowHidden] = useState(false)
  const pageSize = 15

  const queryClient = useQueryClient()

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: queryKeys.notification.tasks({ type: selectedType, q: q.trim() }),
    queryFn: async () => {
      return await apiGet<DashboardTasksData>('/api/dashboard/tasks', {
        params: {
          page: 1,
          // Nạp cả danh sách rồi phân trang tại chỗ. 500 = đúng trần backend —
          // xin thấp hơn tổng việc thì by_type đếm ra số mà danh sách không có.
          page_size: 500,
          include_dismissed: 1, // Việc đã ẩn vẫn về (kèm cờ) cho nút "Hiện đã làm"
          type: selectedType || undefined,
          q: q.trim() || undefined,
        },
      })
    },
  })

  // Đánh dấu xong / khôi phục ghi server rồi vô hiệu cả nhóm `notification`
  // (tab này + chuông cảnh báo) và số liệu dashboard — ba nơi cùng khớp.
  function refreshAfterMutation() {
    void queryClient.invalidateQueries({ queryKey: queryKeys.notification.all })
    void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.dashboard() })
  }

  const dismiss = useMutation({
    mutationFn: (body: { keys?: string[]; all?: boolean }) =>
      apiPost<{ added: number }>('/api/dashboard/tasks/dismiss', body),
    onSuccess: refreshAfterMutation,
  })

  const restore = useMutation({
    mutationFn: (body: { keys?: string[]; all?: boolean }) =>
      apiPost<{ removed: number }>('/api/dashboard/tasks/restore', body),
    onSuccess: refreshAfterMutation,
  })

  const items = useMemo(() => data?.items ?? [], [data?.items])
  const byTypeCounts = data?.by_type ?? {}
  const dismissedTotal = data?.dismissed_total ?? 0
  // Tổng việc CHƯA ẨN mọi loại — by_type do server đếm trước khi lọc q/type.
  const activeCount = Object.values(byTypeCounts).reduce((sum, n) => sum + n, 0)

  const visibleItems = useMemo(
    () => (showHidden ? items : items.filter((item) => !item.dismissed)),
    [items, showHidden],
  )

  // Cập nhật số việc chưa làm lên badge của tab
  useEffect(() => {
    if (onCountChange) {
      onCountChange(activeCount)
    }
  }, [activeCount, onCountChange])

  // Đánh dấu 1 việc cụ thể đã xong / mở lại
  function toggleDismissTask(e: React.MouseEvent, item: DashboardTaskItem) {
    e.preventDefault()
    e.stopPropagation()
    if (item.dismissed) {
      restore.mutate(
        { keys: [item.key] },
        { onSuccess: () => toast.info(`Đã mở lại việc: ${item.code}`) },
      )
    } else {
      dismiss.mutate(
        { keys: [item.key] },
        { onSuccess: () => toast.success(`Đã đánh dấu hoàn thành: ${item.code}`) },
      )
    }
  }

  // Đánh dấu TẤT CẢ việc đang hiện đã làm hết
  function handleDismissAll() {
    // Không lọc gì thì để SERVER tự gom key (`all: true`) — gửi key theo danh
    // sách đã nạp là sót việc nằm ngoài trang khi tổng vượt trần page_size.
    if (!q.trim() && !selectedType) {
      if (activeCount === 0) return
      dismiss.mutate(
        { all: true },
        { onSuccess: () => toast.success(`Đã đánh dấu làm hết ${activeCount} công việc!`) },
      )
      return
    }
    const keys = items.filter((item) => !item.dismissed).map((item) => item.key)
    if (keys.length === 0) return
    dismiss.mutate(
      { keys },
      { onSuccess: () => toast.success(`Đã đánh dấu làm hết ${keys.length} công việc!`) },
    )
  }

  // Khôi phục tất cả việc đã ẩn của tài khoản
  function handleResetAll() {
    restore.mutate(
      { all: true },
      { onSuccess: () => toast.info('Đã khôi phục lại danh sách việc cần làm') },
    )
  }

  // Danh sách loại SINH TỪ `TASK_META` — thêm loại việc mới chỉ khai một chỗ ở
  // trên, ô lọc tự có. Trước đây là một hàng nút chip: mỗi loại một nút, càng
  // thêm loại càng tràn dòng nên đổi thành dropdown (CR-215).
  const filterOptions = [
    { key: 'all', label: 'Tất cả', count: activeCount },
    ...Object.entries(TASK_META).map(([key, meta]) => ({
      key,
      label: meta.short,
      count: byTypeCounts[key] || 0,
    })),
  ]

  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize
    return visibleItems.slice(start, start + pageSize)
  }, [visibleItems, page, pageSize])

  const totalPages = Math.max(1, Math.ceil(visibleItems.length / pageSize))

  return (
    <div className="space-y-4">
      {/* Một hàng duy nhất: ô lọc loại + ô tìm + các nút, cùng chiều cao h-9. */}
      <Card className="flex flex-row flex-wrap items-center gap-2 p-3">
        <Select
          value={selectedType || 'all'}
          onValueChange={(value) => {
            setSelectedType(value === 'all' ? '' : value)
            setPage(1)
          }}
        >
          <SelectTrigger className="w-48 text-xs" aria-label="Lọc theo loại việc">
            <ListFilter className="size-3.5 shrink-0 text-muted-foreground" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {filterOptions.map((opt) => (
              <SelectItem key={opt.key} value={opt.key} className="text-xs">
                {opt.label}
                {opt.count > 0 ? ` (${opt.count})` : ''}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-full sm:w-56">
            <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
            <Input
              value={q}
              placeholder="Tìm mã / tên / nội dung..."
              className="h-9 pl-8 text-xs"
              onChange={(e) => {
                setQ(e.target.value)
                setPage(1)
              }}
            />
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-9 gap-1.5 text-xs text-success hover:bg-success/10 hover:text-success"
            title="Đánh dấu tất cả việc hiện tại đã làm xong"
            disabled={dismiss.isPending}
            onClick={handleDismissAll}
          >
            <CheckCheck className="size-4" />
            <span className="hidden sm:inline">Đánh dấu</span> làm hết
          </Button>

          {dismissedTotal > 0 && (
            <Button
              type="button"
              variant={showHidden ? 'secondary' : 'ghost'}
              size="sm"
              className="h-9 gap-1 px-2.5 text-xs text-muted-foreground"
              title={showHidden ? 'Ẩn các việc đã đánh dấu xong' : 'Hiện các việc đã đánh dấu xong'}
              onClick={() => setShowHidden(!showHidden)}
            >
              {showHidden ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
              <span>{showHidden ? 'Ẩn đã làm' : 'Hiện đã làm'}</span>
            </Button>
          )}

          {dismissedTotal > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="h-9 w-9 text-muted-foreground hover:text-foreground"
              title="Khôi phục lại toàn bộ danh sách"
              disabled={restore.isPending}
              onClick={handleResetAll}
            >
              <RotateCcw className="size-3.5" />
            </Button>
          )}
        </div>
      </Card>

      <Card className="divide-y overflow-hidden">
        {isPending && (
          <div className="space-y-3 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="size-9 rounded-md" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="py-12 text-center">
            <p className="text-sm text-destructive">Không tải được danh sách việc cần làm.</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => void refetch()}>
              Thử lại
            </Button>
          </div>
        )}

        {!isPending && !isError && paginatedItems.length === 0 && (
          <div className="py-12 text-center">
            <CheckCircle2 className="mx-auto size-12 text-emerald-500" />
            <p className="mt-3 text-base font-semibold text-foreground">
              {q || selectedType
                ? 'Không có việc nào khớp bộ lọc'
                : dismissedTotal > 0 && !showHidden
                  ? 'Tuyệt vời! Bạn đã đánh dấu làm hết tất cả các việc.'
                  : 'Không có việc nào cần xử lý'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {q || selectedType
                ? 'Thử thay đổi từ khóa tìm kiếm hoặc chọn bộ lọc "Tất cả".'
                : dismissedTotal > 0 && !showHidden
                  ? 'Bấm "Hiện đã làm" nếu bạn muốn xem lại các việc vừa ẩn.'
                  : 'Tất cả các công việc cần bạn duyệt hoặc xử lý sẽ hiển thị tại đây.'}
            </p>
          </div>
        )}

        {!isPending &&
          !isError &&
          paginatedItems.map((item) => {
            const meta = TASK_META[item.type] || {
              label: item.label,
              short: item.type,
              colorClass: 'bg-muted text-muted-foreground',
              icon: FileText,
            }
            const Icon = meta.icon
            const targetUrl = normalizeTaskLink(item.link)
            const isDismissed = item.dismissed

            return (
              <div
                key={item.key}
                className={cn(
                  'group flex items-center justify-between gap-4 p-3.5 transition-colors',
                  isDismissed ? 'bg-muted/40 opacity-60' : 'hover:bg-accent/50',
                )}
              >
                <Link to={targetUrl} className="flex min-w-0 flex-1 items-center gap-3.5">
                  <div
                    className={cn(
                      'flex size-9 shrink-0 items-center justify-center rounded-lg',
                      meta.colorClass,
                    )}
                  >
                    <Icon className="size-4" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'text-xs font-semibold',
                          isDismissed
                            ? 'text-muted-foreground line-through'
                            : 'text-navy dark:text-foreground',
                        )}
                      >
                        {item.code}
                      </span>
                      {/* Nhãn theo TỪNG DÒNG backend gửi — một loại giờ có hai mức
                          (vd "Công nợ quá hạn" / "Công nợ sắp đến hạn"). */}
                      <Badge variant="outline" className="text-[10px]">
                        {item.label || meta.label}
                      </Badge>
                      {isDismissed && (
                        <Badge
                          variant="secondary"
                          className="bg-emerald-500/10 text-[10px] text-emerald-600"
                        >
                          Đã xong
                        </Badge>
                      )}
                    </div>
                    <p
                      className={cn(
                        'truncate text-sm font-medium',
                        isDismissed
                          ? 'text-muted-foreground line-through'
                          : 'text-foreground group-hover:text-primary',
                      )}
                    >
                      {item.title}
                    </p>
                    {item.subtitle && (
                      <p className="truncate text-xs text-muted-foreground">{item.subtitle}</p>
                    )}
                  </div>
                </Link>

                <div className="flex shrink-0 items-center gap-2">
                  {item.date && (
                    <span className="text-xs text-muted-foreground">{formatDate(item.date)}</span>
                  )}

                  <Button
                    type="button"
                    variant={isDismissed ? 'secondary' : 'ghost'}
                    size="icon-sm"
                    className={cn(
                      'h-8 w-8 transition-opacity',
                      isDismissed
                        ? 'text-emerald-600'
                        : 'opacity-70 hover:bg-emerald-50 hover:text-emerald-600 group-hover:opacity-100',
                    )}
                    title={isDismissed ? 'Khôi phục lại việc này' : 'Đánh dấu đã hoàn thành'}
                    disabled={dismiss.isPending || restore.isPending}
                    onClick={(e) => toggleDismissTask(e, item)}
                  >
                    <Check className="size-4" />
                  </Button>

                  <Link to={targetUrl} className="text-muted-foreground hover:text-foreground">
                    <ChevronRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                  </Link>
                </div>
              </div>
            )
          })}
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Hiển thị {(page - 1) * pageSize + 1} -{' '}
            {Math.min(page * pageSize, visibleItems.length)} / {visibleItems.length} việc
          </span>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Trang trước
            </Button>
            <span className="px-2 font-medium">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Trang sau
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
