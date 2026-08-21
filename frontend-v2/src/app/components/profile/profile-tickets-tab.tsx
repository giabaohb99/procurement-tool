import { ChevronRight, Headset, LifeBuoy, Plus, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { TICKET_STATUS_OPTIONS } from '@/modules/support/config/ticket-constants'
import { TicketPriorityBadge, TicketStatusBadge } from '@/modules/support/config/ticket-meta'
import { useTickets } from '@/modules/support/hooks/use-tickets'
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
import { formatDateTime } from '@/shared/utils/format-date'
import { CreateTicketDialog } from './create-ticket-dialog'

export function ProfileTicketsTab({ onCountChange }: { onCountChange?: (count: number) => void }) {
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [dialogOpen, setDialogOpen] = useState(false)
  const pageSize = 10

  const { data, isLoading, isError, refetch } = useTickets({
    mine: 1,
    page,
    page_size: pageSize,
    subject: q.trim() || undefined,
    status: status !== 'all' ? status : undefined,
  })

  useEffect(() => {
    if (data?.total !== undefined && onCountChange) {
      onCountChange(data.total)
    }
  }, [data?.total, onCountChange])

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-center justify-between gap-3 p-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
            <Input
              value={q}
              placeholder="Tìm chủ đề phiếu hỗ trợ..."
              className="h-9 pl-8 text-xs"
              onChange={(e) => {
                setQ(e.target.value)
                setPage(1)
              }}
            />
          </div>

          <Select
            value={status}
            onValueChange={(val) => {
              setStatus(val)
              setPage(1)
            }}
          >
            <SelectTrigger className="h-9 w-40 text-xs">
              <SelectValue placeholder="Trạng thái" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tất cả trạng thái</SelectItem>
              {TICKET_STATUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          type="button"
          size="sm"
          className="gap-1.5 text-xs"
          onClick={() => setDialogOpen(true)}
        >
          <Plus className="size-4" />
          Tạo phiếu hỗ trợ
        </Button>
      </Card>

      <Card className="divide-y overflow-hidden">
        {isLoading && (
          <div className="space-y-3 p-4">
            {Array.from({ length: 4 }).map((_, i) => (
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
            <p className="text-sm text-destructive">Không tải được danh sách phiếu hỗ trợ.</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => void refetch()}>
              Thử lại
            </Button>
          </div>
        )}

        {!isLoading && !isError && (data?.items?.length ?? 0) === 0 && (
          <div className="py-12 text-center">
            <Headset className="mx-auto size-12 text-muted-foreground/60" />
            <p className="mt-3 text-base font-semibold text-foreground">
              {q || status !== 'all'
                ? 'Không có phiếu hỗ trợ nào khớp bộ lọc'
                : 'Bạn chưa tạo phiếu yêu cầu hỗ trợ nào'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Bấm nút "Tạo phiếu hỗ trợ" nếu bạn cần hỗ trợ về mặt kỹ thuật, cấp quyền hoặc báo lỗi.
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-4 gap-1.5"
              onClick={() => setDialogOpen(true)}
            >
              <Plus className="size-4" />
              Tạo phiếu mới ngay
            </Button>
          </div>
        )}

        {!isLoading &&
          !isError &&
          data?.items?.map((ticket) => (
            <Link
              key={ticket.id}
              to={`/support/tickets/${ticket.id}`}
              className="group flex items-center justify-between gap-4 p-3.5 transition-colors hover:bg-accent/50"
            >
              <div className="flex items-center gap-3.5 min-w-0 flex-1">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-teal-500/10 text-teal-600 dark:bg-teal-500/20 dark:text-teal-400">
                  <LifeBuoy className="size-4" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-xs text-navy dark:text-foreground">
                      {ticket.code}
                    </span>
                    <TicketStatusBadge status={ticket.status} />
                    <TicketPriorityBadge priority={ticket.priority} />
                  </div>
                  <p className="mt-0.5 truncate text-sm font-medium text-foreground group-hover:text-primary">
                    {ticket.subject || '(Không có chủ đề)'}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    Bộ phận: {ticket.department || 'Chưa phân loại'}
                    {ticket.assignee_name && ` · Người xử lý: ${ticket.assignee_name}`}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-3">
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(ticket.created_at)}
                </span>
                <ChevronRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          ))}
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Hiển thị {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, data?.total || 0)} / {data?.total} phiếu
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

      <CreateTicketDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={() => void refetch()}
      />
    </div>
  )
}
