import { useQuery } from '@tanstack/react-query'
import {
  Banknote,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Eye,
  EyeOff,
  FileText,
  RotateCcw,
  Search,
  ShoppingCart,
  Truck,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { apiGet } from '@/core/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'

const DISMISSED_STORAGE_KEY = 'erp.profile.dismissed_tasks'

interface DashboardTaskItem {
  type: 'pr' | 'sr' | 'po' | 'late' | 'payable' | string
  label: string
  code: string
  title: string
  subtitle: string
  date: string
  link: string
}

interface DashboardTasksData {
  total: number
  by_type: Record<string, number>
  page: number
  page_size: number
  items: DashboardTaskItem[]
}

const TASK_META: Record<
  string,
  { label: string; short: string; colorClass: string; icon: typeof FileText }
> = {
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
    short: 'Giao trễ',
    colorClass: 'bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400',
    icon: Truck,
  },
  payable: {
    label: 'Công nợ quá hạn',
    short: 'Quá hạn',
    colorClass: 'bg-rose-500/10 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400',
    icon: Banknote,
  },
}

function taskKey(item: DashboardTaskItem): string {
  return `${item.type}:${item.code}:${item.link}`
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
  return link
}

export function ProfileTasksTab({ onCountChange }: { onCountChange?: (count: number) => void }) {
  const [selectedType, setSelectedType] = useState<string>('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [showHidden, setShowHidden] = useState(false)
  const pageSize = 15

  // Khôi phục các việc đã đánh dấu hoàn thành từ localStorage
  const [dismissedKeys, setDismissedKeys] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(DISMISSED_STORAGE_KEY)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  // Lưu các việc đã ẩn vào localStorage
  useEffect(() => {
    try {
      localStorage.setItem(DISMISSED_STORAGE_KEY, JSON.stringify(dismissedKeys))
    } catch {
      // Bỏ qua nếu localStorage bị đầy/khóa
    }
  }, [dismissedKeys])

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['dashboard-tasks', page, pageSize, selectedType, q],
    queryFn: async () => {
      return await apiGet<DashboardTasksData>('/api/dashboard/tasks', {
        params: {
          page: 1,
          page_size: 300, // Nạp danh sách để đếm chính xác số việc chưa ẩn
          type: selectedType || undefined,
          q: q.trim() || undefined,
        },
      })
    },
  })

  // Lọc bỏ hoặc giữ lại các việc đã đánh dấu xong
  const { visibleItems, activeCount, byTypeCounts } = useMemo(() => {
    const rawItems = data?.items || []
    const dismissedSet = new Set(dismissedKeys)

    const filtered = rawItems.filter((item) => {
      const isDismissed = dismissedSet.has(taskKey(item))
      if (!showHidden && isDismissed) return false
      return true
    })

    const counts: Record<string, number> = { pr: 0, sr: 0, po: 0, late: 0, payable: 0 }
    let remainingTotal = 0

    rawItems.forEach((item) => {
      if (!dismissedSet.has(taskKey(item))) {
        remainingTotal += 1
        const t = item.type
        counts[t] = (counts[t] || 0) + 1
      }
    })

    return {
      visibleItems: filtered,
      activeCount: remainingTotal,
      byTypeCounts: counts,
    }
  }, [data?.items, dismissedKeys, showHidden])

  // Cập nhật số công việc chưa làm lên badge của tab
  useEffect(() => {
    if (onCountChange) {
      onCountChange(activeCount)
    }
  }, [activeCount, onCountChange])

  // Đánh dấu 1 việc cụ thể đã xong
  function toggleDismissTask(e: React.MouseEvent, item: DashboardTaskItem) {
    e.preventDefault()
    e.stopPropagation()
    const key = taskKey(item)
    if (dismissedKeys.includes(key)) {
      setDismissedKeys((prev) => prev.filter((k) => k !== key))
      toast.info(`Đã mở lại việc: ${item.code}`)
    } else {
      setDismissedKeys((prev) => [...prev, key])
      toast.success(`Đã đánh dấu hoàn thành: ${item.code}`)
    }
  }

  // Đánh dấu TẤT CẢ việc hiện tại đã làm hết
  function handleDismissAll() {
    const allCurrentKeys = (data?.items || []).map(taskKey)
    const newDismissed = Array.from(new Set([...dismissedKeys, ...allCurrentKeys]))
    setDismissedKeys(newDismissed)
    toast.success(`Đã đánh dấu làm hết ${data?.items?.length || 0} công việc!`)
  }

  // Khôi phục tất cả
  function handleResetAll() {
    setDismissedKeys([])
    toast.info('Đã khôi phục lại danh sách việc cần làm')
  }

  const filterOptions = [
    { key: '', label: 'Tất cả', count: activeCount },
    { key: 'pr', label: 'YCMH', count: byTypeCounts.pr || 0 },
    { key: 'sr', label: 'Khảo sát', count: byTypeCounts.sr || 0 },
    { key: 'po', label: 'ĐMH', count: byTypeCounts.po || 0 },
    { key: 'late', label: 'Giao trễ', count: byTypeCounts.late || 0 },
    { key: 'payable', label: 'Quá hạn', count: byTypeCounts.payable || 0 },
  ]

  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize
    return visibleItems.slice(start, start + pageSize)
  }, [visibleItems, page, pageSize])

  const totalPages = Math.max(1, Math.ceil(visibleItems.length / pageSize))

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3 p-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {filterOptions.map((opt) => (
            <Button
              key={opt.key}
              type="button"
              variant={selectedType === opt.key ? 'default' : 'ghost'}
              size="sm"
              className="h-8 gap-1.5 px-3 text-xs"
              onClick={() => {
                setSelectedType(opt.key)
                setPage(1)
              }}
            >
              <span>{opt.label}</span>
              {opt.count > 0 && (
                <Badge
                  variant={selectedType === opt.key ? 'secondary' : 'outline'}
                  className="h-4 px-1 text-[10px]"
                >
                  {opt.count}
                </Badge>
              )}
            </Button>
          ))}
        </div>

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
            className="h-9 gap-1.5 text-xs text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/30"
            title="Đánh dấu tất cả việc hiện tại đã làm xong"
            onClick={handleDismissAll}
          >
            <CheckCheck className="size-4" />
            <span className="hidden sm:inline">Đánh dấu</span> làm hết
          </Button>

          {dismissedKeys.length > 0 && (
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

          {dismissedKeys.length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="h-9 w-9 text-muted-foreground hover:text-foreground"
              title="Khôi phục lại toàn bộ danh sách"
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
                : dismissedKeys.length > 0 && !showHidden
                  ? 'Tuyệt vời! Bạn đã đánh dấu làm hết tất cả các việc.'
                  : 'Không có việc nào cần xử lý'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {q || selectedType
                ? 'Thử thay đổi từ khóa tìm kiếm hoặc chọn bộ lọc "Tất cả".'
                : dismissedKeys.length > 0 && !showHidden
                  ? 'Bấm "Hiện đã làm" nếu bạn muốn xem lại các việc vừa ẩn.'
                  : 'Tất cả các công việc cần bạn duyệt hoặc xử lý sẽ hiển thị tại đây.'}
            </p>
          </div>
        )}

        {!isPending &&
          !isError &&
          paginatedItems.map((item, idx) => {
            const meta = TASK_META[item.type] || {
              label: item.label,
              short: item.type,
              colorClass: 'bg-muted text-muted-foreground',
              icon: FileText,
            }
            const Icon = meta.icon
            const targetUrl = normalizeTaskLink(item.link)
            const isDismissed = dismissedKeys.includes(taskKey(item))

            return (
              <div
                key={idx}
                className={`group flex items-center justify-between gap-4 p-3.5 transition-colors ${
                  isDismissed ? 'bg-muted/40 opacity-60' : 'hover:bg-accent/50'
                }`}
              >
                <Link
                  to={targetUrl}
                  className="flex items-center gap-3.5 min-w-0 flex-1"
                >
                  <div
                    className={`flex size-9 shrink-0 items-center justify-center rounded-lg ${meta.colorClass}`}
                  >
                    <Icon className="size-4" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-semibold text-xs ${
                          isDismissed ? 'line-through text-muted-foreground' : 'text-navy dark:text-foreground'
                        }`}
                      >
                        {item.code}
                      </span>
                      <Badge variant="outline" className="text-[10px]">
                        {meta.label}
                      </Badge>
                      {isDismissed && (
                        <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600 text-[10px]">
                          Đã xong
                        </Badge>
                      )}
                    </div>
                    <p
                      className={`truncate text-sm font-medium ${
                        isDismissed
                          ? 'line-through text-muted-foreground'
                          : 'text-foreground group-hover:text-primary'
                      }`}
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
                    className={`h-8 w-8 transition-opacity ${
                      isDismissed
                        ? 'text-emerald-600'
                        : 'opacity-70 group-hover:opacity-100 hover:bg-emerald-50 hover:text-emerald-600'
                    }`}
                    title={isDismissed ? 'Khôi phục lại việc này' : 'Đánh dấu đã hoàn thành'}
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
            Hiển thị {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, visibleItems.length)} / {visibleItems.length} việc
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
