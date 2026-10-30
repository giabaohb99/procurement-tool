import { useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Badge } from '@/shared/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import type { JobItem, JobRun, JobStatusOption } from '../api/job-run-api'
import { useJobRuns } from '../hooks/use-job-runs'
import { formatDuration, jobRunTone } from '../utils/job-run-format'

interface JobRunHistorySheetProps {
  /** `null` = đóng ngăn. */
  job: JobItem | null
  statuses: JobStatusOption[]
  onClose: () => void
}

/**
 * Ngăn LỊCH SỬ CHẠY của một việc nền (bao-CR-703): mỗi dòng một lần chạy — giờ bắt đầu, thời lượng, kết quả tóm tắt,
 * câu lỗi. Phân trang ở máy chủ, lọc theo trạng thái. Chỉ đọc.
 */
export function JobRunHistorySheet({ job, statuses, onClose }: JobRunHistorySheetProps) {
  return (
    <Sheet open={job !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 sm:max-w-4xl">
        {/*  key theo mã việc: đổi việc là ô lọc + trang quay về mặc định, không mang trang 5 của việc trước sang. */}
        {job && <JobRunHistoryBody key={job.code} job={job} statuses={statuses} />}
      </SheetContent>
    </Sheet>
  )
}

function JobRunHistoryBody({ job, statuses }: { job: JobItem; statuses: JobStatusOption[] }) {
  const [status, setStatus] = useState('')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([status])
  const { data, isLoading, isError, refetch } = useJobRuns(job.code, {
    status: status ? Number(status) : undefined,
    page,
    page_size: pageSize,
  })

  const columns: DataTableColumn<JobRun>[] = [
    {
      key: 'started_at',
      header: 'Bắt đầu',
      width: 150,
      hideable: false,
      cell: (r) => <span className="tabular-nums">{formatDateTime(r.started_at) || '—'}</span>,
    },
    {
      key: 'duration_ms',
      header: 'Thời lượng',
      width: 120,
      align: 'right',
      cell: (r) => <span className="tabular-nums">{formatDuration(r.duration_ms)}</span>,
    },
    {
      key: 'status',
      header: 'Kết quả',
      width: 120,
      cell: (r) => <Badge className={cn(TONE_CLASS[jobRunTone(r.status)])}>{r.status_label}</Badge>,
    },
    {
      key: 'summary',
      header: 'Tóm tắt',
      width: 280,
      cell: (r) => (
        <span className="truncate" title={r.summary || undefined}>
          {r.summary || <span>—</span>}
        </span>
      ),
    },
    {
      key: 'error',
      header: 'Lỗi',
      width: 320,
      cell: (r) =>
        r.error ? (
          //  Câu lỗi dài (traceback) chỉ hiện dòng đầu; rê chuột đọc đủ.
          <span className="truncate text-destructive" title={r.error}>
            {r.error}
          </span>
        ) : null,
    },
  ]

  return (
    <>
      <SheetHeader className="border-b">
        <SheetTitle>{job.name}</SheetTitle>
        <SheetDescription className="space-y-1">
          <span className="block">{job.purpose}</span>
          <span className="block text-xs">
            {job.group_label} · {job.schedule_label}
            {!job.enabled && ' · đang tắt'}
            <span className="ml-2 font-mono">{job.code}</span>
          </span>
        </SheetDescription>
      </SheetHeader>
      <div className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          emptyMessage={
            status ? 'Không có lần chạy nào khớp trạng thái đang lọc.' : 'Việc này chưa có lần chạy nào được ghi sổ.'
          }
          storageKey="system.job_runs"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'lần chạy',
          }}
          toolbar={
            <Select value={status || 'all'} onValueChange={(v) => setStatus(v === 'all' ? '' : v)}>
              <SelectTrigger size="sm" className="w-44" aria-label="Lọc trạng thái lần chạy">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Mọi kết quả</SelectItem>
                {statuses.map((opt) => (
                  <SelectItem key={opt.code} value={String(opt.code)}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          }
        />
      </div>
    </>
  )
}
