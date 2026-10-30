import { RotateCw } from 'lucide-react'
import { useState } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import { JOB_NEVER_RAN, type JobItem } from '../api/job-run-api'
import { JobRunHistorySheet } from '../components/job-run-history-sheet'
import { useJobs } from '../hooks/use-job-runs'
import { formatDuration, jobRunTone, runsText } from '../utils/job-run-format'

/**
 * VIỆC CHẠY NGẦM — `/system/background-jobs` (bao-CR-703).
 *
 * Trả lời bốn câu cho quản trị: việc nền nào chạy LÚC NÀO, chạy BAO LÂU, lần gần nhất THÀNH CÔNG hay LỖI, và việc đó
 * ĐỂ LÀM GÌ. Mỗi dòng một việc theo lịch của Celery beat; bấm một dòng mở lịch sử các lần chạy. Chỉ đọc — đợt này không
 * có nút chạy tay.
 *
 * Ba tham số trên URL (`group` · `status` · `job`) để gửi link được kiểu "việc sao lưu tối qua lỗi, xem đây".
 */
export function BackgroundJobListPage() {
  const [group, setGroup] = useUrlParamState('group', '')
  const [status, setStatus] = useUrlParamState('status', '')
  const [openedCode, setOpenedCode] = useUrlParamState('job', '')
  const [keyword, setKeyword] = useState('')
  const keywordQuery = useDebouncedValue(keyword).trim()

  const { data, isLoading, isError, refetch } = useJobs({
    group: group || undefined,
    //  `status` là CHUỖI trên URL nên '0' (chưa chạy lần nào) vẫn là giá trị thật, không rơi về "tất cả".
    status: status ? Number(status) : undefined,
    q: keywordQuery || undefined,
  })
  const items = data?.items ?? []
  const opened = items.find((j) => j.code === openedCode) ?? null
  const hasFilter = Boolean(group || status || keywordQuery)

  const columns: DataTableColumn<JobItem>[] = [
    {
      key: 'name',
      header: 'Việc',
      width: 320,
      hideable: false,
      cell: (r) => (
        <div className="min-w-0">
          <p className="truncate font-medium">{r.name}</p>
          <p className="truncate text-xs text-muted-foreground" title={r.purpose}>
            {r.purpose}
          </p>
        </div>
      ),
    },
    { key: 'group_label', header: 'Nhóm', width: 140, cell: (r) => r.group_label || <span>—</span> },
    {
      key: 'schedule_label',
      header: 'Lịch',
      width: 170,
      cell: (r) =>
        r.enabled ? (
          r.schedule_label || <span>—</span>
        ) : (
          <span className="flex items-center gap-1.5">
            <Badge className={cn(TONE_CLASS.neutral)}>Đang tắt</Badge>
            <span className="truncate text-muted-foreground">{r.schedule_label}</span>
          </span>
        ),
    },
    {
      key: 'last_run',
      header: 'Lần gần nhất',
      width: 230,
      cell: (r) =>
        r.last_run ? (
          <span className="flex min-w-0 items-center gap-2" title={r.last_run.error || r.last_run.summary || undefined}>
            <Badge className={cn('shrink-0', TONE_CLASS[jobRunTone(r.last_run.status)])}>{r.last_run.status_label}</Badge>
            <span className="truncate tabular-nums">{formatDateTime(r.last_run.started_at)}</span>
          </span>
        ) : (
          <Badge className={cn(TONE_CLASS.neutral)}>Chưa chạy</Badge>
        ),
    },
    {
      key: 'duration',
      header: 'Thời lượng',
      width: 120,
      align: 'right',
      cell: (r) => <span className="tabular-nums">{formatDuration(r.last_run?.duration_ms)}</span>,
    },
    {
      key: 'next_run_at',
      header: 'Lần kế tiếp',
      width: 150,
      cell: (r) =>
        r.enabled && r.next_run_at ? (
          <span className="tabular-nums">{formatDateTime(r.next_run_at)}</span>
        ) : (
          <span>—</span>
        ),
    },
    {
      key: 'avg_duration_ms_7d',
      header: 'Trung bình 7 ngày',
      width: 140,
      align: 'right',
      cell: (r) => <span className="tabular-nums">{formatDuration(r.avg_duration_ms_7d)}</span>,
    },
    {
      key: 'runs_7d',
      header: 'Số lần 7 ngày',
      width: 140,
      cell: (r) => (
        <span className={cn('tabular-nums', r.failed_7d > 0 && 'text-destructive')}>{runsText(r.runs_7d, r.failed_7d)}</span>
      ),
    },
    {
      key: 'code',
      header: 'Mã việc',
      width: 220,
      defaultHidden: true,
      cell: (r) => <span className="truncate font-mono text-xs">{r.code}</span>,
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Việc chạy ngầm"
        description="Các việc hệ thống tự chạy theo lịch: chạy lúc nào, bao lâu, thành công hay lỗi, và để làm gì"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Nạp lại ngay">
            <RotateCw className="mr-1.5 size-4" /> Làm mới
          </Button>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.code}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          onRowClick={(r) => setOpenedCode(r.code)}
          emptyMessage={hasFilter ? 'Không có việc nào khớp bộ lọc.' : 'Chưa có việc chạy ngầm nào được khai báo.'}
          storageKey="system.background_jobs"
          toolbar={
            <div className="flex flex-wrap items-center gap-3">
              <Select value={group || 'all'} onValueChange={(v) => setGroup(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-48" aria-label="Lọc theo nhóm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi nhóm</SelectItem>
                  {(data?.groups ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={opt.code}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={status || 'all'} onValueChange={(v) => setStatus(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-52" aria-label="Lọc theo trạng thái lần gần nhất">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi trạng thái gần nhất</SelectItem>
                  {(data?.statuses ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={String(opt.code)}>
                      {opt.label}
                    </SelectItem>
                  ))}
                  <SelectItem value={String(JOB_NEVER_RAN)}>Chưa chạy lần nào</SelectItem>
                </SelectContent>
              </Select>
              <Input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Tìm theo tên / mã việc…"
                aria-label="Tìm việc"
                className="h-8 w-56"
              />
            </div>
          }
        />
      </Card>

      <JobRunHistorySheet job={opened} statuses={data?.statuses ?? []} onClose={() => setOpenedCode('')} />
    </PageContainer>
  )
}
