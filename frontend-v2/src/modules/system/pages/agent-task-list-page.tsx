import { Bot, CircleDollarSign, ListChecks, RotateCw } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { StatCard } from '@/shared/ui/stat-card'
import { formatDateTime } from '@/shared/utils/format-date'

import type { AgentTaskItem } from '../api/agent-hub-api'
import { AgentTaskStatusBadge } from '../components/agent-task-status-badge'
import { useAgentStats, useAgentTasks } from '../hooks/use-agent-tasks'
import { AGENT_TASK_STATUS, formatDurationMs, formatUsd } from '../utils/agent-task-format'

const ALL = 'all'
const STATS_DAYS = 30
const OPEN_STATUSES: number[] = [
  AGENT_TASK_STATUS.SCANNING, AGENT_TASK_STATUS.TRIAGE, AGENT_TASK_STATUS.PLAN,
  AGENT_TASK_STATUS.NEEDS_INPUT, AGENT_TASK_STATUS.CODE, AGENT_TASK_STATUS.REVIEW,
  AGENT_TASK_STATUS.DEPLOYING, AGENT_TASK_STATUS.PROD,
]

/**
 * VIỆC CỦA BOT Đậu Đậu (ai-CR-036, AN-006) — `/system/agent-tasks`.
 *
 * Chỉ ĐỌC: bot đã nhận việc gì, đang ở bước nào, tốn bao nhiêu. Duyệt, gộp, thu hồi, bỏ…
 * vẫn nhắn trên Telegram — nơi có luật hỏi-trước và dấu vết hội thoại.
 */
export function AgentTaskListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<string>(ALL)
  const [search, setSearch] = useState('')
  const q = useDebouncedValue(search, 300)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([status, q])

  const { data, isLoading, isError, refetch } = useAgentTasks({
    page,
    page_size: pageSize,
    status: status === ALL ? 0 : Number(status),
    q: q.trim(),
  })
  const stats = useAgentStats(STATS_DAYS)
  const openCount = (stats.data?.by_status ?? [])
    .filter((s) => OPEN_STATUSES.includes(s.status))
    .reduce((sum, s) => sum + s.count, 0)

  const columns: DataTableColumn<AgentTaskItem>[] = [
    {
      key: 'code',
      header: 'Mã việc',
      width: 100,
      cell: (r) => <span className="font-mono text-xs font-medium">{r.code}</span>,
    },
    {
      key: 'title',
      header: 'Việc',
      width: 360,
      cell: (r) => <span className="truncate" title={r.title}>{r.title}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 170,
      cell: (r) => <AgentTaskStatusBadge status={r.status} label={r.status_label} />,
    },
    { key: 'source', header: 'Nguồn', width: 140, cell: (r) => r.source_label },
    { key: 'risk', header: 'Rủi ro', width: 80, cell: (r) => r.risk_label },
    { key: 'created_at', header: 'Nhận lúc', width: 140, cell: (r) => formatDateTime(r.created_at) || '—' },
    {
      key: 'bot_ms',
      header: 'Bot chạy',
      width: 100,
      cell: (r) => formatDurationMs(r.bot_ms),
    },
    {
      key: 'cost_usd',
      header: 'Chi phí ước',
      width: 100,
      cell: (r) => <span title="Ước theo bảng giá model; Claude Code chạy gói thuê bao">{formatUsd(r.cost_usd)}</span>,
    },
    {
      key: 'branch_name',
      header: 'Nhánh',
      width: 240,
      defaultHidden: true,
      cell: (r) => <span className="font-mono text-xs">{r.branch_name || '—'}</span>,
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Việc của bot Telegram"
        description="Đậu Đậu đã nhận việc gì, đang ở bước nào, tốn bao nhiêu — thao tác trên việc vẫn nhắn qua Telegram"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Làm mới danh sách">
            <RotateCw className="size-4 mr-1.5" /> Làm mới
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <StatCard icon={ListChecks} label="Việc đang mở" value={openCount} loading={stats.isLoading} />
        <StatCard
          icon={CircleDollarSign}
          label={`Chi phí model ${STATS_DAYS} ngày`}
          value={formatUsd(stats.data?.total_cost_usd)}
          hint="Ước theo bảng giá; Claude Code chạy gói thuê bao"
          loading={stats.isLoading}
        />
        <StatCard
          icon={Bot}
          label={`Lượt gọi ${STATS_DAYS} ngày`}
          value={stats.data?.run_count ?? 0}
          loading={stats.isLoading}
          className="max-md:col-span-2"
        />
      </div>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => String(r.id)}
          onRowClick={(r) => navigate(appRoutes.system.agentTask(r.id))}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          emptyMessage={status !== ALL || q ? 'Không có việc nào khớp bộ lọc.' : 'Bot chưa nhận việc nào.'}
          storageKey="system.agent_tasks"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'việc',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-3">
              <SearchField
                value={search}
                onChange={setSearch}
                placeholder="Tìm mã hoặc tên việc…"
                className="w-72"
              />
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="h-9 w-48 text-xs">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
                  {(data?.statuses ?? []).map((s) => (
                    <SelectItem key={s.value} value={String(s.value)}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          }
        />
      </Card>
    </PageContainer>
  )
}
