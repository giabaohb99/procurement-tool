import { CheckCircle2, Clock, MailWarning, RotateCw, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { StatCard } from '@/shared/ui/stat-card'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import { EMAIL_LOG_STATUS, type EmailLogFilters, type EmailLogItem } from '../api/email-log-api'
import { EmailLogDetailSheet } from '../components/email-log-detail-sheet'
import { useEmailLogMeta, useEmailLogStats, useEmailLogs } from '../hooks/use-email-logs'
import { emailStatusTone, shortError } from '../utils/email-log-format'

const STAT_DAYS = 7

/**
 * NHẬT KÝ EMAIL — `/system/email-logs` (bao-CR-721).
 *
 * Trả lời câu "hệ đã gửi thư cho ai chưa, lỗi gì": mỗi dòng một thư, mới nhất trước,
 * bấm dòng mở ngăn đọc nguyên văn câu lỗi. Nút Gửi lại nằm trong ngăn (bao-CR-727).
 *
 * `status` và `id` đi qua URL để thẻ đếm đầu màn liên kết được tới danh sách đã lọc
 * và để chép đường dẫn một thư cho người khác xem. Các ô còn lại là state thường.
 * Sự kiện chọn NHIỀU (chip bỏ được) vì một luồng duyệt gửi 3–4 loại thư và người ta
 * hay tra cả cụm.
 */
export function EmailLogListPage() {
  const [status, setStatus] = useUrlParamState('status', '')
  const [openedId, setOpenedId] = useUrlParamState('id', '')

  const [events, setEvents] = useState<string[]>([])
  const [recipient, setRecipient] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  //  Ô gõ chữ phải hoãn: mỗi ký tự một lượt `LIKE '%…%'`.
  const recipientQuery = useDebouncedValue(recipient)

  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([status, events, recipientQuery, fromDate, toDate])

  const filters: EmailLogFilters = {
    q: recipientQuery || undefined,
    event: events.length ? events : undefined,
    status: status || undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  }
  const { data, isLoading, isError, refetch } = useEmailLogs({ ...filters, page, page_size: pageSize })
  const meta = useEmailLogMeta()
  const stats = useEmailLogStats(STAT_DAYS)

  const hasFilter = Boolean(status || events.length || recipientQuery || fromDate || toDate)
  const eventLabel = useMemo(
    () => new Map((meta.data?.events ?? []).map((e) => [e.code, e.label])),
    [meta.data],
  )

  const addEvent = (code: string) => {
    if (code && !events.includes(code)) setEvents([...events, code])
  }
  const removeEvent = (code: string) => setEvents(events.filter((e) => e !== code))
  const clearFilters = () => {
    setStatus('')
    setEvents([])
    setRecipient('')
    setFromDate('')
    setToDate('')
  }

  const columns: DataTableColumn<EmailLogItem>[] = [
    {
      key: 'created_at',
      header: 'Thời gian',
      width: 150,
      hideable: false,
      cell: (r) => <span className="tabular-nums">{formatDateTime(r.created_at) || <span>—</span>}</span>,
    },
    {
      key: 'to_email',
      header: 'Người nhận',
      width: 230,
      hideable: false,
      cell: (r) => <span className="truncate">{r.to_email || <span>—</span>}</span>,
    },
    {
      key: 'subject',
      header: 'Tiêu đề',
      width: 320,
      cell: (r) => (
        <span className="flex min-w-0 items-center gap-1.5">
          {r.resent_from_id && (
            <Badge variant="secondary" className="shrink-0">
              Gửi lại từ #{r.resent_from_id}
            </Badge>
          )}
          <span className="truncate" title={r.subject}>
            {r.subject || <span>—</span>}
          </span>
        </span>
      ),
    },
    {
      key: 'event_label',
      header: 'Loại thư',
      width: 200,
      cell: (r) => (
        <span className="truncate" title={r.event}>
          {r.event_label || <span>—</span>}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 110,
      cell: (r) => <Badge className={cn(TONE_CLASS[emailStatusTone(r.status)])}>{r.status_label}</Badge>,
    },
    {
      key: 'error',
      header: 'Lỗi',
      width: 280,
      cell: (r) =>
        r.error ? (
          <span className="truncate text-destructive" title={r.error}>
            {shortError(r.error)}
          </span>
        ) : null,
    },
    {
      key: 'from_email',
      header: 'Người gửi',
      width: 200,
      cell: (r) => (
        <span className="truncate">
          {r.from_email || <span className="text-muted-foreground">SMTP dùng chung</span>}
        </span>
      ),
    },
    {
      key: 'sent_at',
      header: 'Gửi xong lúc',
      width: 150,
      defaultHidden: true,
      cell: (r) => <span className="tabular-nums">{formatDateTime(r.sent_at) || <span>—</span>}</span>,
    },
  ]

  const toggleStatusLink = (code: string) => (status === code ? '' : code)

  return (
    <PageContainer fill>
      <PageHeader
        title="Nhật ký email"
        description="Mỗi dòng là một thư hệ thống đã gửi hoặc định gửi — bấm dòng để đọc nguyên văn câu lỗi"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Nạp lại ngay">
            <RotateCw className="size-4 mr-1.5" /> Làm mới
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatCard
          icon={MailWarning}
          label={`Thư lỗi ${STAT_DAYS} ngày qua`}
          value={stats.data?.failed ?? 0}
          tone={(stats.data?.failed ?? 0) > 0 ? 'danger' : undefined}
          hint={status === EMAIL_LOG_STATUS.FAILED ? 'Đang lọc theo thẻ này' : 'Bấm để lọc thư lỗi'}
          loading={stats.isLoading}
          to={`?status=${toggleStatusLink(EMAIL_LOG_STATUS.FAILED)}`}
        />
        <StatCard
          icon={CheckCircle2}
          label={`Đã gửi ${STAT_DAYS} ngày qua`}
          value={stats.data?.sent ?? 0}
          loading={stats.isLoading}
          to={`?status=${toggleStatusLink(EMAIL_LOG_STATUS.SENT)}`}
        />
        <StatCard
          icon={Clock}
          label={`Đang chờ ${STAT_DAYS} ngày qua`}
          value={stats.data?.pending ?? 0}
          tone={(stats.data?.pending ?? 0) > 0 ? 'warning' : undefined}
          loading={stats.isLoading}
          to={`?status=${toggleStatusLink(EMAIL_LOG_STATUS.PENDING)}`}
        />
      </div>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          onRowClick={(r) => setOpenedId(String(r.id))}
          emptyMessage={
            hasFilter ? 'Không có thư nào khớp bộ lọc.' : 'Hệ chưa ghi thư nào.'
          }
          storageKey="system.email_logs"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'thư',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-3">
              <Input
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder="Người nhận chứa…"
                aria-label="Người nhận"
                className="h-8 w-56"
              />

              <Select value={status || 'all'} onValueChange={(v) => setStatus(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-40" aria-label="Trạng thái">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi trạng thái</SelectItem>
                  {(meta.data?.statuses ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={opt.code}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Chọn NHIỀU sự kiện: ô chọn thêm từng cái, mỗi cái thành một chip bỏ được. */}
              <Select value="" onValueChange={addEvent}>
                <SelectTrigger size="sm" className="w-56" aria-label="Thêm loại thư">
                  <SelectValue placeholder="Thêm loại thư…" />
                </SelectTrigger>
                <SelectContent>
                  {(meta.data?.events ?? [])
                    .filter((opt) => !events.includes(opt.code))
                    .map((opt) => (
                      <SelectItem key={opt.code} value={opt.code}>
                        {opt.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>

              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                aria-label="Từ ngày"
                className="h-8 w-40"
              />
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                aria-label="Đến ngày"
                className="h-8 w-40"
              />

              {events.map((code) => (
                <Badge key={code} variant="secondary" className="gap-1">
                  {eventLabel.get(code) ?? code}
                  <button
                    type="button"
                    aria-label={`Bỏ lọc ${eventLabel.get(code) ?? code}`}
                    onClick={() => removeEvent(code)}
                    className="rounded-sm hover:text-destructive"
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}

              {hasFilter && (
                <Button type="button" size="sm" variant="ghost" onClick={clearFilters}>
                  Xóa bộ lọc
                </Button>
              )}
            </div>
          }
        />
      </Card>

      <EmailLogDetailSheet logId={openedId ? Number(openedId) : null} onClose={() => setOpenedId('')} />
    </PageContainer>
  )
}
